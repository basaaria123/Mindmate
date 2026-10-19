"""Backend <-> AI agent orchestration.

The AI agents (app/agents, owned by the AI developer) are pure functions that
take Pydantic inputs and return schema-validated outputs. This module is the
backend side of that interface:

* builds agent inputs from the database memory (task-scoped, deleted items excluded),
* calls the agent only when live model calls are enabled (``llm_available()``),
* treats every failure (missing key, timeout, invalid JSON after the agent's
  retry) as a soft failure and returns ``None`` so callers use deterministic code,
* logs each call and each fallback as an Event for the Trace screen.

Reference IDs in agent output are validated against the database by the
callers (create_plan / assess_fit), never trusted as-is.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from app.config import get_settings, llm_available
from app.db import models
from app.memory.refs import make_ref
from app.memory.retrieval import active_decisions, active_evidence, active_goals, active_skills, active_weaknesses
from app.memory.service import list_items
from app.services.events import log_event

T = TypeVar("T")


def call_agent(db: Session, user: models.User | None, agent: str, fn: Callable[..., T], **kwargs: Any) -> T | None:
    """Run one agent call with logging; return None when the model is off or fails."""

    if not llm_available():
        return None
    started = time.perf_counter()
    try:
        result = fn(**kwargs)
    except Exception as error:  # noqa: BLE001 - every model failure degrades to deterministic code
        log_event(
            db,
            user_id=user.id if user else None,
            agent=agent,
            action="model_fallback",
            summary=f"{agent} agent unavailable ({type(error).__name__}); deterministic logic used instead.",
            payload={"error": str(error)[:300]},
        )
        return None
    elapsed = round(time.perf_counter() - started, 2)
    log_event(
        db,
        user_id=user.id if user else None,
        agent=agent,
        action="model_call",
        summary=f"{agent} agent answered via Nemotron in {elapsed}s ({get_settings().llm_mode}).",
        payload={"seconds": elapsed},
    )
    return result


def user_profile_input(db: Session, user: models.User, *, daily_minutes: int | None = None):
    """The AI UserProfile schema, filled from structured memory."""

    from app.schemas.profile import UserProfile

    interests: list[str] = []
    preferences: list[str] = []
    for item in list_items(db, user.id, types={"preference"}):
        label, _, value = item.content.partition(":")
        value = value.strip() or item.content
        (interests if label.strip().lower() == "interest" else preferences).append(value)
    return UserProfile(
        education=user.education or "Not specified",
        goals=[goal.title for goal in active_goals(db, user.id)],
        skills=[f"{skill.name} ({skill.level})" for skill in active_skills(db, user.id)],
        interests=interests,
        daily_available_minutes=daily_minutes or user.daily_minutes,
        learning_preferences=preferences,
    )


def opportunity_input(opportunity: models.Opportunity):
    """The AI OpportunitySpec schema, filled from a stored opportunity."""

    from app.schemas.opportunity import OpportunityRequirement, OpportunitySpec

    return OpportunitySpec(
        opportunity_title=opportunity.title,
        organization=opportunity.org,
        opportunity_type=opportunity.type,
        required_skills=[
            OpportunityRequirement(
                skill_name=req.get("name", ""),
                importance=req.get("weight", "Medium"),
                is_mandatory=bool(req.get("mandatory", False)),
                description=req.get("description", "") or "",
            )
            for req in opportunity.requirements
        ],
        preferred_skills=[],
        experience_level="Not specified",
        summary=opportunity.summary or opportunity.title,
    )


def gap_vector_input(opportunity: models.Opportunity, gaps: list[dict]):
    """The AI GapVectorJSON schema from the deterministic gap ranking."""

    from app.schemas.gap import GapVectorJSON, SkillGap

    return GapVectorJSON(
        opportunity_title=opportunity.title,
        gaps=[
            SkillGap(
                skill_name=gap["requirement"],
                career_impact_score=int(gap["impact_score"]),
                gap_type="missing_skill" if gap["coverage"] == "not_shown" else "partial_skill",
                missing_evidence="No supporting evidence in memory" if gap["coverage"] == "not_shown" else "Evidence shows partial coverage",
                rationale=gap["rationale"],
                recommended_focus=gap["recommended_focus"],
                evidence_refs=list(gap["refs"]),
            )
            for gap in gaps
        ],
    )


def planner_memories(db: Session, user: models.User) -> tuple[list[str], list[dict]]:
    """Decisions (as text with refs) and memory records whose IDs the planner may cite."""

    decisions = [f"[{make_ref(d)}] {d.statement} (reason: {d.reason})" for d in active_decisions(db, user.id)]
    memories: list[dict] = []
    for weakness in active_weaknesses(db, user.id):
        memories.append({"memory_id": make_ref(weakness), "memory_type": "weakness", "content": f"{weakness.topic} ({weakness.severity})"})
    for decision in active_decisions(db, user.id):
        memories.append({"memory_id": make_ref(decision), "memory_type": "decision", "content": decision.statement})
    for evidence in active_evidence(db, user.id):
        memories.append({"memory_id": make_ref(evidence), "memory_type": "evidence", "content": evidence.description})
    for goal in active_goals(db, user.id):
        memories.append({"memory_id": make_ref(goal), "memory_type": "goal", "content": goal.title})
    return decisions, memories
