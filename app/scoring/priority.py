"""Replan priority (proposal section 7, "Replan priority").

    priority = 0.40 x role_impact + 0.25 x weakness_boost
             + 0.20 x goal_hierarchy_weight + 0.15 x deadline_urgency
    plan      = highest-priority tasks that fit available_minutes
    must_keep = tasks tied to an active weakness or a hard deadline

Every input is a number in [0, 1]; the breakdown is returned so the
explanation can cite the exact inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.config import PriorityWeights

SEVERITY_BOOST = {"high": 1.0, "medium": 0.7, "low": 0.4}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class PriorityInputs:
    role_impact: float
    weakness_boost: float
    goal_hierarchy_weight: float
    deadline_urgency: float
    weakness_refs: tuple[str, ...] = ()
    hard_deadline: bool = False


@dataclass(frozen=True)
class PriorityBreakdown:
    score: float
    inputs: PriorityInputs
    weights: PriorityWeights
    must_keep: bool

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "must_keep": self.must_keep,
            "inputs": {
                "role_impact": round(self.inputs.role_impact, 3),
                "weakness_boost": round(self.inputs.weakness_boost, 3),
                "goal_hierarchy_weight": round(self.inputs.goal_hierarchy_weight, 3),
                "deadline_urgency": round(self.inputs.deadline_urgency, 3),
                "weakness_refs": list(self.inputs.weakness_refs),
                "hard_deadline": self.inputs.hard_deadline,
            },
            "weights": {
                "role_impact": self.weights.role_impact,
                "weakness_boost": self.weights.weakness_boost,
                "goal_hierarchy": self.weights.goal_hierarchy,
                "deadline_urgency": self.weights.deadline_urgency,
            },
        }


def goal_hierarchy_weight(priority_rank: int | None) -> float:
    """Rank 1 goal -> 1.0, rank 2 -> 0.5, rank 3 -> 0.33...; no goal -> 0.5."""

    if priority_rank is None or priority_rank < 1:
        return 0.5
    return 1.0 / priority_rank


def deadline_urgency(deadline: date | None, today: date, horizon_days: int = 14) -> float:
    """1.0 when due today or overdue, falling linearly to 0 at the horizon."""

    if deadline is None:
        return 0.0
    days_left = (deadline - today).days
    if days_left <= 0:
        return 1.0
    return clamp(1.0 - days_left / horizon_days)


def weakness_boost(task_refs: list[str], active_weaknesses: dict[str, str]) -> tuple[float, tuple[str, ...]]:
    """Boost from the most severe active weakness this task references."""

    hits = [ref for ref in task_refs if ref in active_weaknesses]
    if not hits:
        return 0.0, ()
    boost = max(SEVERITY_BOOST.get(active_weaknesses[ref], 0.7) for ref in hits)
    return boost, tuple(hits)


def compute_priority(
    *,
    role_impact: float,
    task_refs: list[str],
    active_weaknesses: dict[str, str],
    goal_rank: int | None,
    deadline: date | None,
    today: date,
    weights: PriorityWeights,
    hard_deadline_days: int = 3,
) -> PriorityBreakdown:
    boost, hits = weakness_boost(task_refs, active_weaknesses)
    urgency = deadline_urgency(deadline, today)
    hard_deadline = deadline is not None and (deadline - today).days <= hard_deadline_days
    inputs = PriorityInputs(
        role_impact=clamp(role_impact),
        weakness_boost=boost,
        goal_hierarchy_weight=goal_hierarchy_weight(goal_rank),
        deadline_urgency=urgency,
        weakness_refs=hits,
        hard_deadline=hard_deadline,
    )
    score = (
        weights.role_impact * inputs.role_impact
        + weights.weakness_boost * inputs.weakness_boost
        + weights.goal_hierarchy * inputs.goal_hierarchy_weight
        + weights.deadline_urgency * inputs.deadline_urgency
    )
    return PriorityBreakdown(score=score, inputs=inputs, weights=weights, must_keep=bool(hits) or hard_deadline)
