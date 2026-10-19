"""Plans, tasks, the time-budget scheduler and the replan engine.

The model (Planner / Replanning agents) may propose tasks and write the
rationale, but this module is the only thing that decides what fits in the
budget, what order tasks take, and which tasks are kept. Same inputs always
produce the same plan, and every change cites the memory that caused it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import models
from app.memory.refs import filter_valid_refs, make_ref
from app.memory.retrieval import active_decisions, active_goals, active_weaknesses
from app.scoring.fit import skill_matches
from app.scoring.priority import compute_priority
from app.services.events import log_event

PRIORITY_LABELS = ("High", "Medium", "Low")


@dataclass
class TaskCandidate:
    title: str
    minutes: int
    priority: str = "Medium"
    preferred_day: int = 1
    why: str = ""
    refs: list[str] = field(default_factory=list)
    role_impact: float = 0.5
    goal_id: int | None = None
    deadline: date | None = None
    origin_task_id: int | None = None
    status: str = "todo"
    score: float = 0.0
    must_keep: bool = False
    breakdown: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    is_new: bool = False


@dataclass
class ScheduledTask:
    candidate: TaskCandidate
    day_number: int
    minutes: int
    rank: int


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


def schedule_within_budget(
    candidates: list[TaskCandidate], budget: int, plan_days: int
) -> tuple[list[ScheduledTask], list[TaskCandidate]]:
    """Place tasks by priority so no day exceeds ``budget`` minutes.

    Must-keep tasks are placed first from day 1; other tasks start from their
    preferred day and slide later until a day has room. A task longer than
    the budget is clipped to the budget (and says so in its notes). Tasks that
    cannot fit inside ``plan_days`` are deferred, never silently dropped.
    """

    if budget <= 0:
        raise ValueError("The daily budget must be a positive number of minutes.")

    ordered = sorted(
        candidates,
        key=lambda c: (not c.must_keep, -c.score, c.preferred_day, c.title.lower()),
    )
    capacity = {day: budget for day in range(1, plan_days + 1)}
    scheduled: list[ScheduledTask] = []
    deferred: list[TaskCandidate] = []

    for rank, candidate in enumerate(ordered, start=1):
        minutes = candidate.minutes
        if minutes > budget:
            candidate.notes.append(f"Clipped from {minutes} to {budget} minutes to fit the daily budget.")
            minutes = budget
        start_day = 1 if candidate.must_keep else max(1, min(candidate.preferred_day, plan_days))
        placed = False
        for day in range(start_day, plan_days + 1):
            if capacity[day] >= minutes:
                capacity[day] -= minutes
                scheduled.append(ScheduledTask(candidate=candidate, day_number=day, minutes=minutes, rank=rank))
                placed = True
                break
        if not placed:
            deferred.append(candidate)

    scheduled.sort(key=lambda item: (item.day_number, item.rank))
    return scheduled, deferred


# ---------------------------------------------------------------------------
# Plan persistence
# ---------------------------------------------------------------------------


def active_plan(db: Session, user_id: int) -> models.Plan | None:
    return db.scalar(
        select(models.Plan)
        .where(models.Plan.user_id == user_id, models.Plan.status == "active")
        .order_by(models.Plan.version.desc())
        .limit(1)
    )


def previous_plan(db: Session, plan: models.Plan) -> models.Plan | None:
    return db.scalar(select(models.Plan).where(models.Plan.replaced_by_id == plan.id).limit(1))


def plan_history(db: Session, user_id: int) -> list[models.Plan]:
    return list(db.scalars(select(models.Plan).where(models.Plan.user_id == user_id).order_by(models.Plan.version.desc())))


def serialize_task(task: models.Task) -> dict:
    return {
        "id": task.id,
        "ref": make_ref(task),
        "title": task.title,
        "minutes": task.minutes,
        "priority": task.priority,
        "day_number": task.day_number,
        "order_index": task.order_index,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "status": task.status,
        "why": task.why,
        "refs": list(task.refs or []),
        "role_impact": task.role_impact,
        "must_keep": task.must_keep,
        "priority_score": round(task.priority_score, 4) if task.priority_score is not None else None,
        "goal": f"goal#{task.goal_id}" if task.goal_id else None,
    }


def serialize_plan(plan: models.Plan) -> dict:
    tasks = sorted(plan.tasks, key=lambda t: (t.day_number, t.order_index))
    minutes_by_day: dict[int, int] = {}
    for task in tasks:
        if task.status in {"todo", "done"}:
            minutes_by_day[task.day_number] = minutes_by_day.get(task.day_number, 0) + task.minutes
    return {
        "id": plan.id,
        "ref": make_ref(plan),
        "version": plan.version,
        "status": plan.status,
        "goal": f"goal#{plan.goal_id}" if plan.goal_id else None,
        "daily_budget_minutes": plan.daily_budget_minutes,
        "rationale": plan.rationale,
        "refs": list(plan.refs or []),
        "created_at": plan.created_at.isoformat() + "Z",
        "minutes_by_day": {str(day): minutes for day, minutes in sorted(minutes_by_day.items())},
        "tasks": [serialize_task(task) for task in tasks],
    }


def plan_titles(plan: models.Plan | None) -> list[str]:
    if plan is None:
        return []
    tasks = sorted((t for t in plan.tasks if t.status != "deferred"), key=lambda t: (t.day_number, t.order_index))
    return [f"Day {t.day_number}: {t.title}" for t in tasks]


def _goal_rank_map(db: Session, user_id: int) -> dict[int, int]:
    return {goal.id: goal.priority_rank for goal in active_goals(db, user_id)}


def _weakness_map(db: Session, user_id: int) -> dict[str, models.Weakness]:
    return {make_ref(w): w for w in active_weaknesses(db, user_id)}


def score_candidates(db: Session, user: models.User, candidates: list[TaskCandidate], today: date) -> None:
    settings = get_settings()
    goal_ranks = _goal_rank_map(db, user.id)
    weaknesses = _weakness_map(db, user.id)
    severity_by_ref = {ref: w.severity for ref, w in weaknesses.items()}

    for candidate in candidates:
        # Attach active weaknesses whose topic matches the task title so the
        # plan reacts to new evidence even for tasks created earlier.
        for ref, weakness in weaknesses.items():
            if ref not in candidate.refs and skill_matches(weakness.topic, candidate.title):
                candidate.refs.append(ref)
                candidate.notes.append(f"Linked to active weakness {ref} ({weakness.topic}).")
        breakdown = compute_priority(
            role_impact=candidate.role_impact,
            task_refs=candidate.refs,
            active_weaknesses=severity_by_ref,
            goal_rank=goal_ranks.get(candidate.goal_id) if candidate.goal_id else None,
            deadline=candidate.deadline,
            today=today,
            weights=settings.priority_weights,
            hard_deadline_days=settings.hard_deadline_days,
        )
        candidate.score = breakdown.score
        candidate.must_keep = breakdown.must_keep
        candidate.breakdown = breakdown.as_dict()


def _persist_plan(
    db: Session,
    user: models.User,
    *,
    scheduled: list[ScheduledTask],
    deferred: list[TaskCandidate],
    budget: int,
    goal_id: int | None,
    rationale: str,
    refs: list[str],
    previous: models.Plan | None,
) -> models.Plan:
    version = (previous.version + 1) if previous else 1
    plan = models.Plan(
        user_id=user.id,
        goal_id=goal_id,
        version=version,
        daily_budget_minutes=budget,
        status="active",
        rationale=rationale,
        refs=list(dict.fromkeys(refs)),
    )
    db.add(plan)
    db.flush()

    order_by_day: dict[int, int] = {}
    for item in scheduled:
        order = order_by_day.get(item.day_number, 0)
        order_by_day[item.day_number] = order + 1
        c = item.candidate
        db.add(
            models.Task(
                plan_id=plan.id,
                user_id=user.id,
                goal_id=c.goal_id,
                title=c.title,
                minutes=item.minutes,
                priority=c.priority,
                day_number=item.day_number,
                order_index=order,
                deadline=c.deadline,
                status=c.status,
                why=c.why + (" " + " ".join(c.notes) if c.notes else ""),
                refs=list(dict.fromkeys(c.refs)),
                role_impact=c.role_impact,
                must_keep=c.must_keep,
                priority_score=c.score,
                origin_task_id=c.origin_task_id,
            )
        )
    for c in deferred:
        db.add(
            models.Task(
                plan_id=plan.id,
                user_id=user.id,
                goal_id=c.goal_id,
                title=c.title,
                minutes=c.minutes,
                priority=c.priority,
                day_number=get_settings().plan_days,
                order_index=999,
                deadline=c.deadline,
                status="deferred",
                why=c.why + " Deferred: does not fit the current daily budget.",
                refs=list(dict.fromkeys(c.refs)),
                role_impact=c.role_impact,
                must_keep=c.must_keep,
                priority_score=c.score,
                origin_task_id=c.origin_task_id,
            )
        )
    if previous is not None:
        previous.status = "superseded"
        previous.replaced_by_id = plan.id
    db.flush()
    db.refresh(plan)
    return plan


def _priority_label(candidate: TaskCandidate) -> str:
    if candidate.priority in PRIORITY_LABELS:
        return candidate.priority
    return "High" if candidate.score >= 0.6 else "Low" if candidate.score < 0.35 else "Medium"


def create_plan(
    db: Session,
    user: models.User,
    *,
    tasks: list[dict],
    daily_budget_minutes: int | None = None,
    goal_id: int | None = None,
    rationale: str | None = None,
    refs: list[str] | None = None,
    agent: str = "planner",
    today: date | None = None,
) -> models.Plan:
    """Create a new plan version from task proposals (user, seed or planner agent)."""

    today = today or date.today()
    budget = daily_budget_minutes or user.daily_minutes
    if goal_id is not None:
        goal = db.get(models.Goal, goal_id)
        if goal is None or goal.user_id != user.id or goal.deleted_at is not None:
            raise ValueError(f"Goal {goal_id} does not exist.")

    candidates: list[TaskCandidate] = []
    all_refs: list[str] = list(refs or [])
    for index, data in enumerate(tasks):
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValueError("Every task needs a title.")
        minutes = int(data.get("minutes") or data.get("duration_minutes") or 0)
        if minutes <= 0:
            raise ValueError(f"Task {title!r} needs a positive number of minutes.")
        task_refs = list(data.get("refs") or data.get("source_refs") or [])
        valid, invalid = filter_valid_refs(db, task_refs)
        if invalid:
            raise ValueError(f"Task {title!r} cites unknown references: {invalid}")
        task_goal = data.get("goal_id", goal_id)
        deadline = data.get("deadline")
        if isinstance(deadline, str):
            deadline = date.fromisoformat(deadline)
        candidate = TaskCandidate(
            title=title,
            minutes=minutes,
            priority=str(data.get("priority") or "Medium").title(),
            preferred_day=int(data.get("day_number") or index // 2 + 1),
            why=str(data.get("why") or data.get("why_it_matters") or ""),
            refs=valid,
            role_impact=float(data.get("role_impact", 0.5)),
            goal_id=task_goal,
            deadline=deadline,
            is_new=True,
        )
        if candidate.priority not in PRIORITY_LABELS:
            candidate.priority = "Medium"
        candidates.append(candidate)
        all_refs.extend(valid)

    score_candidates(db, user, candidates, today)
    scheduled, deferred = schedule_within_budget(candidates, budget, get_settings().plan_days)
    previous = active_plan(db, user.id)
    plan = _persist_plan(
        db,
        user,
        scheduled=scheduled,
        deferred=deferred,
        budget=budget,
        goal_id=goal_id,
        rationale=rationale or f"Plan created with {len(scheduled)} tasks inside a {budget}-minute daily budget.",
        refs=all_refs,
        previous=previous,
    )
    log_event(
        db,
        user_id=user.id,
        agent=agent,
        action="plan_created",
        summary=f"Plan v{plan.version} created: {len(scheduled)} tasks scheduled, {len(deferred)} deferred, budget {budget} min/day.",
        refs=[make_ref(plan)] + list(dict.fromkeys(all_refs)),
    )
    return plan


def generate_candidates_from_gaps(gaps: list[dict], budget: int) -> list[dict]:
    """Deterministic planner used when no model proposal is supplied."""

    tasks: list[dict] = []
    day = 1
    for index, gap in enumerate(gaps[:8]):
        name = gap["requirement"]
        coverage = gap.get("coverage", "not_shown")
        tasks.append(
            {
                "title": f"Practice {name}: targeted exercise" if coverage != "not_shown" else f"Build evidence for {name}: starter project",
                "minutes": min(30, budget),
                "priority": "High" if index < 2 else "Medium",
                "day_number": day,
                "role_impact": round(min(1.0, 0.5 + gap.get("impact_score", 50) / 200), 2),
                "why": gap.get("rationale", "") + " " + gap.get("recommended_focus", ""),
                "refs": list(gap.get("refs", [])),
            }
        )
        day = day + 1 if (index % 2 == 1) else day
    return tasks


# ---------------------------------------------------------------------------
# Replan
# ---------------------------------------------------------------------------


def _candidates_from_plan(plan: models.Plan) -> list[TaskCandidate]:
    candidates: list[TaskCandidate] = []
    for task in plan.tasks:
        if task.status in {"done", "dropped"}:
            continue
        candidates.append(
            TaskCandidate(
                title=task.title,
                minutes=task.minutes,
                priority=task.priority,
                preferred_day=task.day_number if task.status != "deferred" else 1,
                why=task.why.split(" Deferred:")[0].split(" Clipped from")[0].split(" Linked to active")[0],
                refs=list(task.refs or []),
                role_impact=task.role_impact,
                goal_id=task.goal_id,
                deadline=task.deadline,
                origin_task_id=task.origin_task_id or task.id,
                status="todo",
            )
        )
    return candidates


def _weakness_candidates(db: Session, user: models.User, existing: list[TaskCandidate], budget: int) -> list[TaskCandidate]:
    new: list[TaskCandidate] = []
    for weakness in active_weaknesses(db, user.id):
        ref = make_ref(weakness)
        covered = any(ref in c.refs or skill_matches(weakness.topic, c.title) for c in existing)
        if covered:
            continue
        new.append(
            TaskCandidate(
                title=f"Focus practice: {weakness.topic}",
                minutes=min(30, budget),
                priority="High",
                preferred_day=1,
                why=(
                    f"Added because practice shows a {weakness.severity} weakness on {weakness.topic} "
                    f"({weakness.evidence_count} low-scoring answer(s)) [{ref}]."
                ),
                refs=[ref] + list(weakness.refs or []),
                role_impact=0.85,
                is_new=True,
            )
        )
    return new


def replan(
    db: Session,
    user: models.User,
    *,
    available_minutes: int | None = None,
    reason: str | None = None,
    trigger: str = "user",
    today: date | None = None,
    agent: str = "replan",
) -> dict:
    """Rebuild the active plan and explain exactly what moved and why."""

    today = today or date.today()
    settings = get_settings()
    current = active_plan(db, user.id)
    if current is None:
        raise ValueError("There is no active plan to replan. Create a plan first.")

    old_budget = current.daily_budget_minutes
    budget = available_minutes or old_budget
    if budget <= 0:
        raise ValueError("available_minutes must be positive.")

    candidates = _candidates_from_plan(current)
    added = _weakness_candidates(db, user, candidates, budget)
    candidates.extend(added)
    score_candidates(db, user, candidates, today)
    scheduled, deferred = schedule_within_budget(candidates, budget, settings.plan_days)

    # ---- diff -------------------------------------------------------------
    before_tasks = sorted(
        (t for t in current.tasks if t.status in {"todo", "deferred"}),
        key=lambda t: (t.status == "deferred", t.day_number, t.order_index),
    )
    before_rank = {(t.origin_task_id or t.id): (index + 1, t.day_number, t.status) for index, t in enumerate(before_tasks)}
    after_entries: list[dict] = []
    moved: list[dict] = []
    added_entries: list[dict] = []
    kept: list[dict] = []
    for index, item in enumerate(scheduled, start=1):
        c = item.candidate
        entry = {
            "title": c.title,
            "to_day": item.day_number,
            "to_rank": index,
            "minutes": item.minutes,
            "priority_score": round(c.score, 4),
            "must_keep": c.must_keep,
            "refs": list(dict.fromkeys(c.refs)),
            "breakdown": c.breakdown,
        }
        after_entries.append(entry)
        if c.is_new:
            added_entries.append(entry)
        elif c.origin_task_id in before_rank:
            rank, day, status = before_rank[c.origin_task_id]
            entry["from_day"] = day
            entry["from_rank"] = rank
            if day != item.day_number or rank != index or status == "deferred":
                moved.append(entry)
            else:
                kept.append(entry)
    deferred_entries = [
        {
            "title": c.title,
            "minutes": c.minutes,
            "priority_score": round(c.score, 4),
            "refs": list(dict.fromkeys(c.refs)),
            "from_day": before_rank.get(c.origin_task_id, (None, None, None))[1],
        }
        for c in deferred
    ]

    # ---- rationale ----------------------------------------------------------
    weaknesses = _weakness_map(db, user.id)
    decisions = active_decisions(db, user.id)
    rationale_lines: list[str] = []
    refs: list[str] = []

    if available_minutes and available_minutes != old_budget:
        rationale_lines.append(
            f"Daily budget changed from {old_budget} to {budget} minutes"
            + (f" ({reason})" if reason else "")
            + "; the plan was re-fitted so no day exceeds the new budget."
        )
    elif reason:
        rationale_lines.append(f"Replanned because {reason}.")
    else:
        rationale_lines.append("Replanned on request using the latest memory." if trigger == "user" else f"Replanned after {trigger} using the latest memory.")

    for entry in added_entries:
        weakness_refs = [r for r in entry["refs"] if r in weaknesses]
        for ref in weakness_refs:
            w = weaknesses[ref]
            rationale_lines.append(
                f"Added '{entry['title']}' on day {entry['to_day']} because {w.topic} is an active "
                f"{w.severity} weakness with {w.evidence_count} low-scoring answer(s) [{ref}]."
            )
            refs.append(ref)
            refs.extend(w.refs or [])
    for index, entry in enumerate(moved):
        if index >= 6:
            rationale_lines.append(f"{len(moved) - 6} more task(s) shifted to fit the budget.")
            break
        weakness_refs = [r for r in entry["refs"] if r in weaknesses]
        cause = ""
        if weakness_refs:
            cause = " because it targets active weakness " + ", ".join(f"[{r}]" for r in weakness_refs)
            refs.extend(weakness_refs)
            for r in weakness_refs:
                refs.extend(weaknesses[r].refs or [])
        elif entry["breakdown"].get("inputs", {}).get("hard_deadline"):
            cause = " because its deadline is within the hard-deadline window"
        elif available_minutes and available_minutes != old_budget:
            cause = " to fit the reduced daily budget"
        from_day = entry.get("from_day")
        if from_day != entry["to_day"]:
            rationale_lines.append(
                f"Moved '{entry['title']}' from day {from_day} to day {entry['to_day']}{cause} "
                f"(priority {entry['priority_score']})."
            )
        else:
            rationale_lines.append(
                f"Re-ranked '{entry['title']}' on day {entry['to_day']} from #{entry.get('from_rank')} to #{entry['to_rank']}{cause}."
            )
    for entry in deferred_entries:
        rationale_lines.append(
            f"Deferred '{entry['title']}' because it no longer fits the {budget}-minute daily budget over {settings.plan_days} days."
        )
    must_keep_titles = [e["title"] for e in after_entries if e["must_keep"]]
    if must_keep_titles:
        rationale_lines.append("Kept regardless of budget (active weakness or hard deadline): " + "; ".join(must_keep_titles) + ".")
    for decision in decisions[:2]:
        rationale_lines.append(f"Respected decision [{make_ref(decision)}]: {decision.statement}.")
        refs.append(make_ref(decision))
    for c in candidates:
        refs.extend(c.refs)

    rationale = " ".join(rationale_lines)
    plan = _persist_plan(
        db,
        user,
        scheduled=scheduled,
        deferred=deferred,
        budget=budget,
        goal_id=current.goal_id,
        rationale=rationale,
        refs=list(dict.fromkeys(refs)),
        previous=current,
    )
    db.refresh(current)

    diff = {
        "before": plan_titles(current),
        "after": plan_titles(plan),
        "added": added_entries,
        "moved": moved,
        "deferred": deferred_entries,
        "kept": kept,
    }
    log_event(
        db,
        user_id=user.id,
        agent=agent,
        action="replan",
        summary=rationale,
        refs=[make_ref(plan), make_ref(current)] + list(dict.fromkeys(refs)),
        payload={"added": len(added_entries), "moved": len(moved), "deferred": len(deferred_entries), "budget": budget},
    )
    return {
        "plan": serialize_plan(plan),
        "previous_plan_id": current.id,
        "daily_budget_minutes": budget,
        "diff": diff,
        "rationale": rationale,
        "refs": list(dict.fromkeys(refs)),
    }


def update_task_status(db: Session, user: models.User, task: models.Task, status: str) -> models.Task:
    if status not in {"todo", "done", "deferred", "dropped"}:
        raise ValueError("status must be one of todo, done, deferred, dropped.")
    previous = task.status
    task.status = status
    db.flush()
    log_event(
        db,
        user_id=user.id,
        agent="observe",
        action="task_status_changed",
        summary=f"Task '{task.title}' changed from {previous} to {status}.",
        refs=[make_ref(task), f"plan#{task.plan_id}"],
    )
    return task


def plan_tasks_from_agent(db: Session, user: models.User, opportunity: models.Opportunity, gaps: list[dict], budget: int, goal_id: int | None) -> list[dict] | None:
    """Ask the Planner agent for tasks using database memory; None when the model is off or fails.

    The agent validates its own references against the memories it is given
    (all database refs); create_plan validates them against the database again.
    """

    from app.agents.planner_agent import generate_plan
    from app.services.agent_bridge import call_agent, gap_vector_input, opportunity_input, planner_memories, user_profile_input

    decisions, memories = planner_memories(db, user)
    plan = call_agent(
        db,
        user,
        "planner",
        generate_plan,
        user_profile=user_profile_input(db, user, daily_minutes=budget),
        opportunity=opportunity_input(opportunity),
        gap_vector=gap_vector_input(opportunity, gaps),
        goal_id=f"goal#{goal_id}" if goal_id else "goal#none",
        existing_decisions=decisions,
        existing_memories=memories,
    )
    if plan is None:
        return None
    return [
        {
            "title": task.title,
            "minutes": task.duration_minutes,
            "priority": task.priority,
            "day_number": task.day_number,
            "why": task.why_it_matters,
            "refs": list(task.source_refs),
            "role_impact": {"High": 0.85, "Medium": 0.6, "Low": 0.35}.get(task.priority, 0.5),
        }
        for task in plan.schedule
    ]
