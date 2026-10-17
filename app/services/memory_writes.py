"""Typed memory writes: goals, constraints, decisions, skills, evidence.

Each helper creates the entity, mirrors it into the memory graph and logs
an event, so every write is visible on the Memory and Trace screens.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.db import models
from app.db.models import utcnow
from app.memory.refs import make_ref
from app.memory.service import record_entity
from app.services.events import log_event

LEVELS = {"none", "beginner", "intermediate", "advanced", "expert"}
EVIDENCE_TYPES = {"project", "repo", "cert", "internship", "course", "other"}
CONSTRAINT_KINDS = {"hours", "deadline", "boundary"}


def add_goal(
    db: Session,
    user: models.User,
    *,
    title: str,
    target_role: str | None = None,
    deadline: date | None = None,
    hours_per_day: float | None = None,
    priority_rank: int = 1,
    parent_goal_id: int | None = None,
    source: str = "user",
) -> models.Goal:
    if parent_goal_id is not None:
        parent = db.get(models.Goal, parent_goal_id)
        if parent is None or parent.user_id != user.id or parent.deleted_at is not None:
            raise ValueError(f"Parent goal {parent_goal_id} does not exist.")
    goal = models.Goal(
        user_id=user.id,
        title=title.strip(),
        target_role=target_role,
        deadline=deadline,
        hours_per_day=hours_per_day,
        priority_rank=priority_rank,
        parent_goal_id=parent_goal_id,
    )
    db.add(goal)
    db.flush()
    record_entity(db, goal, source=source)
    log_event(
        db,
        user_id=user.id,
        agent="goal_engine",
        action="goal_added",
        summary=f"Goal recorded: {goal.title} (priority {goal.priority_rank}).",
        refs=[make_ref(goal)],
    )
    return goal


def add_constraint(
    db: Session,
    user: models.User,
    *,
    kind: str,
    value: str,
    valid_from: date | None = None,
    valid_to: date | None = None,
    source: str = "user",
) -> models.Constraint:
    if kind not in CONSTRAINT_KINDS:
        raise ValueError(f"Constraint kind must be one of {sorted(CONSTRAINT_KINDS)}.")
    constraint = models.Constraint(
        user_id=user.id, kind=kind, value=value.strip(), valid_from=valid_from, valid_to=valid_to
    )
    db.add(constraint)
    db.flush()
    record_entity(db, constraint, source=source)
    log_event(
        db,
        user_id=user.id,
        agent="goal_engine",
        action="constraint_added",
        summary=f"Constraint recorded ({kind}): {constraint.value}",
        refs=[make_ref(constraint)],
    )
    return constraint


def add_decision(
    db: Session,
    user: models.User,
    *,
    statement: str,
    reason: str,
    goal_id: int | None = None,
    source: str = "user",
) -> models.Decision:
    if goal_id is not None:
        goal = db.get(models.Goal, goal_id)
        if goal is None or goal.user_id != user.id or goal.deleted_at is not None:
            raise ValueError(f"Goal {goal_id} does not exist.")
    decision = models.Decision(
        user_id=user.id, statement=statement.strip(), reason=reason.strip(), goal_id=goal_id, source=source
    )
    db.add(decision)
    db.flush()
    record_entity(db, decision, source=source, tags=["decision"])
    log_event(
        db,
        user_id=user.id,
        agent="memory",
        action="decision_recorded",
        summary=f"Decision stored with its reason: {decision.statement}",
        refs=[make_ref(decision)] + ([f"goal#{goal_id}"] if goal_id else []),
    )
    return decision


def add_skill(
    db: Session,
    user: models.User,
    *,
    name: str,
    level: str = "beginner",
    confidence: int = 50,
    source: str = "user",
) -> models.Skill:
    if level not in LEVELS:
        raise ValueError(f"Skill level must be one of {sorted(LEVELS)}.")
    confidence = max(0, min(100, int(confidence)))
    skill = models.Skill(user_id=user.id, name=name.strip(), level=level, confidence=confidence, last_updated=utcnow())
    db.add(skill)
    db.flush()
    record_entity(db, skill, source=source)
    log_event(
        db,
        user_id=user.id,
        agent="profile",
        action="skill_added",
        summary=f"Skill recorded: {skill.name} ({skill.level}).",
        refs=[make_ref(skill)],
    )
    return skill


def add_evidence(
    db: Session,
    user: models.User,
    skill: models.Skill,
    *,
    type: str,
    description: str,
    url: str | None = None,
    source: str = "user",
) -> models.Evidence:
    if type not in EVIDENCE_TYPES:
        raise ValueError(f"Evidence type must be one of {sorted(EVIDENCE_TYPES)}.")
    evidence = models.Evidence(
        user_id=user.id, skill_id=skill.id, type=type, description=description.strip(), url=url
    )
    db.add(evidence)
    db.flush()
    record_entity(db, evidence, source=source, tags=[skill.name])
    skill.last_updated = utcnow()
    record_entity(db, skill, source=source)
    log_event(
        db,
        user_id=user.id,
        agent="profile",
        action="evidence_added",
        summary=f"Evidence added for {skill.name}: {evidence.description}",
        refs=[make_ref(evidence), make_ref(skill)],
    )
    return evidence


def update_skill(
    db: Session,
    skill: models.Skill,
    *,
    level: str | None = None,
    confidence: int | None = None,
) -> models.Skill:
    if level is not None:
        if level not in LEVELS:
            raise ValueError(f"Skill level must be one of {sorted(LEVELS)}.")
        skill.level = level
    if confidence is not None:
        skill.confidence = max(0, min(100, int(confidence)))
    skill.last_updated = utcnow()
    db.flush()
    record_entity(db, skill)
    return skill
