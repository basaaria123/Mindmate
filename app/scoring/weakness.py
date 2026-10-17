"""Weakness thresholds: weaknesses are created by evidence, never by a
single answer (proposal section 7, ``Weakness`` entity).

A topic becomes a weakness when at least ``min_occurrences`` evaluated
sessions score below ``score_threshold``, or when one session scores at or
below ``severe_score``. Severity escalates with the number of occurrences
and the average score.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeaknessDecision:
    should_record: bool
    severity: str
    evidence_count: int
    reason: str


def severity_for(scores: list[int]) -> str:
    average = sum(scores) / len(scores) if scores else 100
    if len(scores) >= 3 or average < 35:
        return "high"
    if average < 50 or len(scores) >= 2:
        return "medium"
    return "low"


def decide_weakness(
    low_scores: list[int],
    *,
    score_threshold: int,
    min_occurrences: int,
    severe_score: int,
) -> WeaknessDecision:
    """``low_scores`` are the scores (including the latest) below the threshold."""

    if not low_scores:
        return WeaknessDecision(False, "none", 0, "The latest answer met the threshold.")

    latest = low_scores[-1]
    if len(low_scores) >= min_occurrences:
        return WeaknessDecision(
            True,
            severity_for(low_scores),
            len(low_scores),
            f"{len(low_scores)} practice answers scored below {score_threshold}.",
        )
    if latest <= severe_score:
        return WeaknessDecision(
            True,
            severity_for(low_scores),
            len(low_scores),
            f"A single answer scored {latest}, at or below the severe threshold {severe_score}.",
        )
    return WeaknessDecision(
        False,
        "none",
        len(low_scores),
        f"Only {len(low_scores)} answer(s) below {score_threshold}; "
        f"{min_occurrences} are needed before recording a weakness.",
    )
