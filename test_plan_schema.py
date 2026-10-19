"""Offline schema tests for PlanScheduleJSON."""

import pytest
from pydantic import ValidationError

from app.schemas.plan import PlanScheduleJSON, TaskItem


def _task(**overrides):
    defaults = {
        "task_id": "task-01",
        "day_number": 1,
        "title": "Study transformers",
        "duration_minutes": 30,
        "priority": "High",
        "why_it_matters": "Addresses a high-impact skill gap.",
        "source_refs": [],
    }
    defaults.update(overrides)
    return defaults


def test_valid_plan():
    plan = PlanScheduleJSON(
        goal_id="goal-1",
        daily_budget_minutes=60,
        total_tasks=2,
        schedule=[
            _task(task_id="task-01", day_number=1, duration_minutes=30),
            _task(task_id="task-02", day_number=2, duration_minutes=45),
        ],
    )
    assert plan.total_tasks == 2
    assert len(plan.schedule) == 2


def test_total_tasks_mismatch_raises():
    with pytest.raises(ValidationError, match="total_tasks"):
        PlanScheduleJSON(
            goal_id="goal-1",
            daily_budget_minutes=60,
            total_tasks=5,
            schedule=[_task()],
        )


def test_day_exceeds_budget_raises():
    with pytest.raises(ValidationError, match="exceeds the daily time budget"):
        PlanScheduleJSON(
            goal_id="goal-1",
            daily_budget_minutes=30,
            total_tasks=2,
            schedule=[
                _task(task_id="t1", day_number=1, duration_minutes=20),
                _task(task_id="t2", day_number=1, duration_minutes=20),
            ],
        )


def test_zero_duration_rejected():
    with pytest.raises(ValidationError):
        TaskItem(
            task_id="t1",
            day_number=1,
            title="Bad task",
            duration_minutes=0,
            priority="High",
            why_it_matters="N/A",
        )


def test_day_number_out_of_range():
    with pytest.raises(ValidationError):
        TaskItem(
            task_id="t1",
            day_number=15,
            title="Out of range",
            duration_minutes=30,
            priority="High",
            why_it_matters="N/A",
        )


def test_empty_schedule_with_zero_total_tasks():
    plan = PlanScheduleJSON(
        goal_id="goal-1",
        daily_budget_minutes=60,
        total_tasks=0,
        schedule=[],
    )
    assert plan.schedule == []
