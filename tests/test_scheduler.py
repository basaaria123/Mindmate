"""The time-budget scheduler never exceeds the budget and keeps must-keep tasks."""

import pytest

from app.services.plan_service import TaskCandidate, schedule_within_budget


def _minutes_by_day(scheduled):
    totals = {}
    for item in scheduled:
        totals[item.day_number] = totals.get(item.day_number, 0) + item.minutes
    return totals


def test_schedule_respects_budget_and_orders_by_priority():
    candidates = [
        TaskCandidate("low", 30, preferred_day=1, score=0.2),
        TaskCandidate("high", 30, preferred_day=1, score=0.9),
        TaskCandidate("medium", 30, preferred_day=1, score=0.5),
    ]
    scheduled, deferred = schedule_within_budget(candidates, budget=60, plan_days=14)
    assert not deferred
    assert max(_minutes_by_day(scheduled).values()) <= 60
    day_one = [s.candidate.title for s in scheduled if s.day_number == 1]
    assert day_one == ["high", "medium"]
    assert [s.candidate.title for s in scheduled if s.day_number == 2] == ["low"]


def test_must_keep_goes_first_even_with_low_score():
    candidates = [
        TaskCandidate("other", 30, preferred_day=1, score=0.9),
        TaskCandidate("weak-spot", 30, preferred_day=5, score=0.1, must_keep=True),
    ]
    scheduled, _ = schedule_within_budget(candidates, budget=30, plan_days=14)
    assert scheduled[0].candidate.title == "weak-spot" and scheduled[0].day_number == 1


def test_tasks_longer_than_budget_are_clipped_not_dropped():
    candidates = [TaskCandidate("long", 90, score=0.5)]
    scheduled, deferred = schedule_within_budget(candidates, budget=30, plan_days=14)
    assert not deferred and scheduled[0].minutes == 30
    assert any("Clipped" in note for note in scheduled[0].candidate.notes)


def test_overflow_is_deferred_not_lost():
    candidates = [TaskCandidate(f"t{i}", 30, score=1 - i / 100) for i in range(40)]
    scheduled, deferred = schedule_within_budget(candidates, budget=30, plan_days=14)
    assert len(scheduled) == 14 and len(deferred) == 26
    assert [s.candidate.title for s in scheduled] == [f"t{i}" for i in range(14)]


def test_zero_budget_rejected():
    with pytest.raises(ValueError):
        schedule_within_budget([TaskCandidate("t", 10)], budget=0, plan_days=14)
