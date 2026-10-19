"""Request/response contracts for the backend API (docs/contracts/backend-api.md)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ProfileIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    goal: str | None = None
    targetRole: str | None = None
    dailyMinutes: int | None = Field(default=None, ge=1, le=24 * 60)
    education: str | None = None
    summary: str | None = None
    email: str | None = None
    allowTaskWrites: bool | None = None
    preferences: dict | None = None


class ProfileImportIn(BaseModel):
    """Output of the Profile agent (app/schemas/profile.py UserProfile), accepted leniently."""

    model_config = ConfigDict(extra="ignore")

    education: str | None = None
    goals: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    daily_available_minutes: int | None = Field(default=None, ge=1, le=24 * 60)
    learning_preferences: list[str] = Field(default_factory=list)


class MemoryIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source: str = "user"
    payload: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    visibility: str = "private"
    reason: str | None = None


class MemoryPatch(BaseModel):
    content: str | None = None
    payload: dict | None = None
    tags: list[str] | None = None
    visibility: str | None = None


class GoalIn(BaseModel):
    title: str = Field(min_length=1)
    target_role: str | None = None
    deadline: date | None = None
    hours_per_day: float | None = Field(default=None, ge=0)
    priority_rank: int = Field(default=1, ge=1)
    parent_goal_id: int | None = None


class GoalPatch(BaseModel):
    title: str | None = None
    target_role: str | None = None
    deadline: date | None = None
    hours_per_day: float | None = Field(default=None, ge=0)
    priority_rank: int | None = Field(default=None, ge=1)
    status: str | None = None


class ConstraintIn(BaseModel):
    kind: str = Field(min_length=1)
    value: str = Field(min_length=1)
    valid_from: date | None = None
    valid_to: date | None = None


class DecisionIn(BaseModel):
    statement: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    goal_id: int | None = None
    source: str = "user"


class SkillIn(BaseModel):
    name: str = Field(min_length=1)
    level: str = "beginner"
    confidence: int = Field(default=50, ge=0, le=100)


class SkillPatch(BaseModel):
    level: str | None = None
    confidence: int | None = Field(default=None, ge=0, le=100)


class EvidenceIn(BaseModel):
    type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    url: str | None = None
    skill_id: int | None = None


class OpportunityIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str | None = None
    opportunity_title: str | None = None
    org: str | None = None
    organization: str | None = None
    type: str | None = None
    opportunity_type: str | None = None
    deadline: date | None = None
    url: str | None = None
    summary: str | None = None
    requirements: list[dict | str] | None = None
    required_skills: list[dict] | None = None
    preferred_skills: list[str] | None = None


class OpportunitySearchIn(BaseModel):
    query: str = ""
    limit: int = Field(default=12, ge=1, le=50)


class FitIn(BaseModel):
    judgments: list[dict] | None = None
    ai_assessment: dict | None = None


class GapsIn(BaseModel):
    opportunity_id: int


class TaskIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1)
    minutes: int = Field(gt=0)
    priority: str = "Medium"
    day_number: int | None = Field(default=None, ge=1)
    why: str = ""
    refs: list[str] = Field(default_factory=list)
    role_impact: float = Field(default=0.5, ge=0, le=1)
    goal_id: int | None = None
    deadline: date | None = None


class PlanIn(BaseModel):
    tasks: list[TaskIn] = Field(default_factory=list)
    daily_budget_minutes: int | None = Field(default=None, gt=0)
    goal_id: int | None = None
    rationale: str | None = None
    refs: list[str] = Field(default_factory=list)
    generate_from_opportunity_id: int | None = None


class ReplanIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    available_minutes: int | None = Field(default=None, gt=0)
    reason: str | None = None


class TaskStatusIn(BaseModel):
    status: str


class PracticeStartIn(BaseModel):
    topic: str | None = None
    question: str | None = None


class PracticeEvaluateIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer: str = Field(min_length=1)
    session_id: int | None = None
    question: str | None = None
    topic: str | None = None


class ActionIn(BaseModel):
    action: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)
    refs: list[str] = Field(default_factory=list)
    confirmed: bool = False
