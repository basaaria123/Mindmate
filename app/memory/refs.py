"""Reference IDs: the glue between memory, plans and explanations.

Every claim the system makes must cite a reference such as ``ev#4`` or
``decision#12``. This module parses those strings and checks that they point
at existing, non-deleted rows. Unknown references are rejected, which is how
hallucinated evidence is kept out of the database (proposal section 13).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db import models

REF_PATTERN = re.compile(r"^(?P<prefix>[a-z_]+)#(?P<id>\d+)$")

# prefix -> (model, soft-delete aware)
REF_TYPES: dict[str, type[models.Base]] = {
    "ev": models.Evidence,
    "evidence": models.Evidence,
    "skill": models.Skill,
    "decision": models.Decision,
    "weakness": models.Weakness,
    "goal": models.Goal,
    "constraint": models.Constraint,
    "opp": models.Opportunity,
    "opportunity": models.Opportunity,
    "task": models.Task,
    "plan": models.Plan,
    "practice": models.PracticeSession,
    "session": models.PracticeSession,
    "memory": models.MemoryItem,
    "fit": models.FitAssessment,
}

CANONICAL_PREFIX = {
    models.Evidence: "ev",
    models.Skill: "skill",
    models.Decision: "decision",
    models.Weakness: "weakness",
    models.Goal: "goal",
    models.Constraint: "constraint",
    models.Opportunity: "opp",
    models.Task: "task",
    models.Plan: "plan",
    models.PracticeSession: "practice",
    models.MemoryItem: "memory",
    models.FitAssessment: "fit",
}


@dataclass(frozen=True)
class Ref:
    prefix: str
    id: int

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.prefix}#{self.id}"


class InvalidReference(ValueError):
    """Raised when a reference ID is malformed or does not exist."""


def make_ref(instance: models.Base) -> str:
    prefix = CANONICAL_PREFIX[type(instance)]
    return f"{prefix}#{instance.id}"


def parse_ref(value: str) -> Ref:
    match = REF_PATTERN.match(value.strip())
    if not match or match.group("prefix") not in REF_TYPES:
        raise InvalidReference(f"Malformed reference ID: {value!r}")
    return Ref(prefix=match.group("prefix"), id=int(match.group("id")))


def resolve_ref(db: Session, value: str) -> models.Base:
    """Return the row a reference points to, or raise InvalidReference."""

    ref = parse_ref(value)
    model = REF_TYPES[ref.prefix]
    row = db.get(model, ref.id)
    if row is None:
        raise InvalidReference(f"Unknown reference ID: {value}")
    if getattr(row, "deleted_at", None) is not None:
        raise InvalidReference(f"Reference {value} points to a deleted item")
    return row


def validate_refs(db: Session, refs: list[str]) -> list[str]:
    """Validate every reference; returns the normalised list or raises."""

    normalised: list[str] = []
    for value in refs:
        row = resolve_ref(db, value)
        normalised.append(make_ref(row))
    return normalised


def filter_valid_refs(db: Session, refs: list[str]) -> tuple[list[str], list[str]]:
    """Split references into (valid, invalid) without raising."""

    valid: list[str] = []
    invalid: list[str] = []
    for value in refs:
        try:
            valid.append(make_ref(resolve_ref(db, value)))
        except InvalidReference:
            invalid.append(value)
    return valid, invalid
