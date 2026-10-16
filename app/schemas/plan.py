
from pydantic import BaseModel, Field, model_validator


class TaskItem(BaseModel):
    task_id: str = Field(
        description="Unique identifier for this task."
    )

    day_number: int = Field(
        ge=1,
        le=14,
        description="Scheduled day, from day 1 through day 14."
    )

    title: str = Field(
        description="Short, actionable task title."
    )

    duration_minutes: int = Field(
        gt=0,
        description="Time required to complete the task."
    )

    priority: str = Field(
        description="Task priority: High, Medium, or Low."
    )

    why_it_matters: str = Field(
        description="Why this task contributes to the user's goal."
    )

    source_refs: list[str] = Field(
        default_factory=list,
        description=(
            "Existing weakness, decision, or evidence reference IDs. "
            "Never invent reference IDs."
        )
    )


class PlanScheduleJSON(BaseModel):
    goal_id: str = Field(
        description="Identifier for the goal being pursued."
    )

    daily_budget_minutes: int = Field(
        gt=0,
        description="Maximum time available per day."
    )

    total_tasks: int = Field(
        ge=0,
        description="Number of tasks in the schedule."
    )

    schedule: list[TaskItem] = Field(
        description="Tasks scheduled across the 14-day plan."
    )

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.total_tasks != len(self.schedule):
            raise ValueError(
                "total_tasks must match the number of scheduled tasks."
            )

        minutes_by_day = {}

        for task in self.schedule:
            minutes_by_day[task.day_number] = (
                minutes_by_day.get(task.day_number, 0)
                + task.duration_minutes
            )

        for day, total_minutes in minutes_by_day.items():
            if total_minutes > self.daily_budget_minutes:
                raise ValueError(
                    f"Day {day} exceeds the daily time budget."
                )

        return self
