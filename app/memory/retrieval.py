"""Task-scoped memory retrieval.

Prompts receive only the memory a given agent task needs (proposal, prompt
design rules). ``retrieve_for_task`` maps a task name to the memory kinds it
is allowed to see and never returns deleted items.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.memory.refs import make_ref

TASK_MEMORY_KINDS: dict[str, tuple[str, ...]] = {
    "profile": ("profile", "goals", "skills", "evidence", "preferences"),
    "opportunity": ("goals",),
    "fit": ("skills", "evidence", "goals"),
    "gap": ("skills", "evidence", "weaknesses", "goals"),
    "planner": ("goals", "constraints", "decisions", "weaknesses", "skills", "preferences"),
    "practice": ("skills", "weaknesses", "goals"),
    "memory": ("skills", "evidence", "decisions", "weaknesses", "goals", "constraints", "preferences", "notes"),
    "replan": ("goals", "constraints", "decisions", "weaknesses", "preferences"),
}


@dataclass
class MemoryBundle:
    task: str
    goals: list[dict] = field(default_factory=list)
    constraints: list[dict] = field(default_factory=list)
    skills: list[dict] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    weaknesses: list[dict] = field(default_factory=list)
    preferences: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    profile: dict | None = None

    def all_refs(self) -> set[str]:
        refs: set[str] = set()
        for group in (
            self.goals,
            self.constraints,
            self.skills,
            self.evidence,
            self.decisions,
            self.weaknesses,
        ):
            refs.update(item["ref"] for item in group if item.get("ref"))
        return refs

    def as_dict(self) -> dict:
        return {
            "task": self.task,
            "profile": self.profile,
            "goals": self.goals,
            "constraints": self.constraints,
            "skills": self.skills,
            "evidence": self.evidence,
            "decisions": self.decisions,
            "weaknesses": self.weaknesses,
            "preferences": self.preferences,
            "notes": self.notes,
        }


def _active(query, model):
    return query.where(model.deleted_at.is_(None))


def active_goals(db: Session, user_id: int) -> list[models.Goal]:
    query = _active(select(models.Goal).where(models.Goal.user_id == user_id), models.Goal)
    return list(db.scalars(query.order_by(models.Goal.priority_rank, models.Goal.id)))


def active_constraints(db: Session, user_id: int) -> list[models.Constraint]:
    query = _active(select(models.Constraint).where(models.Constraint.user_id == user_id), models.Constraint)
    return list(db.scalars(query.order_by(models.Constraint.id)))


def active_skills(db: Session, user_id: int) -> list[models.Skill]:
    query = _active(select(models.Skill).where(models.Skill.user_id == user_id), models.Skill)
    return list(db.scalars(query.order_by(models.Skill.name)))


def active_evidence(db: Session, user_id: int) -> list[models.Evidence]:
    query = _active(select(models.Evidence).where(models.Evidence.user_id == user_id), models.Evidence)
    return list(db.scalars(query.order_by(models.Evidence.id)))


def active_decisions(db: Session, user_id: int) -> list[models.Decision]:
    query = _active(select(models.Decision).where(models.Decision.user_id == user_id), models.Decision)
    return list(db.scalars(query.order_by(models.Decision.created_at.desc(), models.Decision.id.desc())))


def active_weaknesses(db: Session, user_id: int) -> list[models.Weakness]:
    query = _active(
        select(models.Weakness).where(models.Weakness.user_id == user_id, models.Weakness.status == "active"),
        models.Weakness,
    )
    return list(db.scalars(query.order_by(models.Weakness.last_seen.desc())))


def _goal_dict(goal: models.Goal) -> dict:
    return {
        "ref": make_ref(goal),
        "id": goal.id,
        "title": goal.title,
        "target_role": goal.target_role,
        "deadline": goal.deadline.isoformat() if goal.deadline else None,
        "hours_per_day": goal.hours_per_day,
        "priority_rank": goal.priority_rank,
        "parent_goal": f"goal#{goal.parent_goal_id}" if goal.parent_goal_id else None,
        "status": goal.status,
    }


def _constraint_dict(constraint: models.Constraint) -> dict:
    return {
        "ref": make_ref(constraint),
        "id": constraint.id,
        "kind": constraint.kind,
        "value": constraint.value,
        "valid_from": constraint.valid_from.isoformat() if constraint.valid_from else None,
        "valid_to": constraint.valid_to.isoformat() if constraint.valid_to else None,
    }


def _skill_dict(skill: models.Skill) -> dict:
    return {
        "ref": make_ref(skill),
        "id": skill.id,
        "name": skill.name,
        "level": skill.level,
        "confidence": skill.confidence,
        "last_updated": skill.last_updated.isoformat() + "Z",
        "evidence_refs": [make_ref(ev) for ev in skill.evidence if ev.deleted_at is None],
    }


def _evidence_dict(evidence: models.Evidence) -> dict:
    return {
        "ref": make_ref(evidence),
        "id": evidence.id,
        "skill_ref": f"skill#{evidence.skill_id}",
        "type": evidence.type,
        "description": evidence.description,
        "url": evidence.url,
    }


def _decision_dict(decision: models.Decision) -> dict:
    return {
        "ref": make_ref(decision),
        "id": decision.id,
        "statement": decision.statement,
        "reason": decision.reason,
        "goal_ref": f"goal#{decision.goal_id}" if decision.goal_id else None,
        "source": decision.source,
        "created_at": decision.created_at.isoformat() + "Z",
    }


def _weakness_dict(weakness: models.Weakness) -> dict:
    return {
        "ref": make_ref(weakness),
        "id": weakness.id,
        "topic": weakness.topic,
        "severity": weakness.severity,
        "evidence_count": weakness.evidence_count,
        "last_seen": weakness.last_seen.isoformat() + "Z",
        "status": weakness.status,
        "refs": list(weakness.refs or []),
    }


def retrieve_for_task(db: Session, user: models.User, task: str) -> MemoryBundle:
    """Return only the memory kinds the named agent task is allowed to see."""

    if task not in TASK_MEMORY_KINDS:
        raise ValueError(f"Unknown memory task: {task}")

    kinds = TASK_MEMORY_KINDS[task]
    bundle = MemoryBundle(task=task)

    if "profile" in kinds:
        bundle.profile = {
            "name": user.name,
            "education": user.education,
            "summary": user.summary,
            "target_role": user.target_role,
            "daily_minutes": user.daily_minutes,
        }
    if "goals" in kinds:
        bundle.goals = [_goal_dict(goal) for goal in active_goals(db, user.id)]
    if "constraints" in kinds:
        bundle.constraints = [_constraint_dict(c) for c in active_constraints(db, user.id)]
    if "skills" in kinds:
        bundle.skills = [_skill_dict(skill) for skill in active_skills(db, user.id)]
    if "evidence" in kinds:
        bundle.evidence = [_evidence_dict(ev) for ev in active_evidence(db, user.id)]
    if "decisions" in kinds:
        bundle.decisions = [_decision_dict(d) for d in active_decisions(db, user.id)]
    if "weaknesses" in kinds:
        bundle.weaknesses = [_weakness_dict(w) for w in active_weaknesses(db, user.id)]
    if "preferences" in kinds or "notes" in kinds:
        from app.memory.service import list_items, serialize_item

        wanted = set()
        if "preferences" in kinds:
            wanted.add("preference")
        if "notes" in kinds:
            wanted.update({"note", "learning_insight"})
        for item in list_items(db, user.id, types=wanted):
            target = bundle.preferences if item.type == "preference" else bundle.notes
            target.append(serialize_item(item))
    return bundle


def prompt_text(bundle: MemoryBundle) -> str:
    """Compact text rendering used when a bundle is handed to a model prompt."""

    lines: list[str] = []
    if bundle.profile:
        lines.append(f"PROFILE: {bundle.profile}")
    for label, group in (
        ("GOALS", bundle.goals),
        ("CONSTRAINTS", bundle.constraints),
        ("SKILLS", bundle.skills),
        ("EVIDENCE", bundle.evidence),
        ("DECISIONS", bundle.decisions),
        ("WEAKNESSES", bundle.weaknesses),
        ("PREFERENCES", bundle.preferences),
        ("NOTES", bundle.notes),
    ):
        if group:
            lines.append(f"{label}:")
            for item in group:
                ref = item.get("ref") or f"memory#{item.get('id')}"
                summary = item.get("content") or item.get("statement") or item.get("topic") or item.get("title") or item.get("name") or item.get("description") or item.get("value")
                lines.append(f"  [{ref}] {summary}")
    return "\n".join(lines)
