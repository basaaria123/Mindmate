"""Relational schema for MindMate's structured memory (proposal section 7).

Every entity that can appear in a prompt carries a ``deleted_at`` column so
that user-purged items are excluded from retrieval while audit history is
kept. ``MemoryItem`` is the unified row behind the Memory Graph screen and
points back at the typed entity through ``ref_id`` (for example ``weakness#3``).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Naive UTC timestamp (stored uniformly across SQLite and PostgreSQL)."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="MindMate learner")
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    education: Mapped[str | None] = mapped_column(String(300), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    goal_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    allow_task_writes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class Goal(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    hours_per_day: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    children: Mapped[list["Goal"]] = relationship(
        "Goal", back_populates="parent", cascade="all", foreign_keys=[parent_goal_id]
    )
    parent: Mapped["Goal | None"] = relationship(
        "Goal", back_populates="children", remote_side=[id], foreign_keys=[parent_goal_id]
    )


class Constraint(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "constraints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # hours | deadline | boundary
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class Skill(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="beginner")
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    evidence: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="skill")


class Evidence(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)  # project | repo | cert | internship | course | other
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    skill: Mapped["Skill"] = relationship("Skill", back_populates="evidence")


class Decision(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="user")


class Weakness(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "weaknesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class Opportunity(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    org: Mapped[str | None] = mapped_column(String(300), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="internship")
    requirements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="curated")


class FitAssessment(Base, TimestampMixin):
    __tablename__ = "fit_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    band: Mapped[str] = mapped_column(String(20), nullable=False)
    per_requirement: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    top_gap: Mapped[str | None] = mapped_column(String(300), nullable=True)
    refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    judged_by: Mapped[str] = mapped_column(String(50), nullable=False, default="deterministic")


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    daily_budget_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    replaced_by_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id"), nullable=True)

    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="plan", cascade="all, delete-orphan", order_by="Task.order_index"
    )


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="Medium")
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo")
    why: Mapped[str] = mapped_column(Text, nullable=False, default="")
    refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    role_impact: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    must_keep: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    plan: Mapped["Plan"] = relationship("Plan", back_populates="tasks")


class PracticeSession(Base, TimestampMixin):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_concepts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric_scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    missing_concepts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    weakness_id: Mapped[int | None] = mapped_column(ForeignKey("weaknesses.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    evaluator: Mapped[str] = mapped_column(String(50), nullable=False, default="deterministic")
    question_source: Mapped[str] = mapped_column(String(30), nullable=False, default="question_bank", server_default="question_bank")
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class MemoryItem(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "memory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="user")
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="private")
    ref_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class ActionDraft(Base, TimestampMixin):
    __tablename__ = "action_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    permission_level: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
