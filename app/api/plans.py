"""Plans and tasks: create, read, observe (status) and replan with a diff."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.contracts import PlanIn, ReplanIn, TaskStatusIn
from app.api.deps import get_current_user, get_db
from app.db import models
from app.permissions import check_permission
from app.services.opportunity_service import gaps_for, get_opportunity
from app.services.plan_service import (
    active_plan,
    create_plan,
    generate_candidates_from_gaps,
    plan_history,
    replan,
    serialize_plan,
    update_task_status,
)

router = APIRouter(tags=["plans"])


@router.get("/plans")
def read_plans(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    plan = active_plan(db, user.id)
    history = plan_history(db, user.id)
    return {
        "active": serialize_plan(plan) if plan else None,
        "history": [{"id": p.id, "version": p.version, "status": p.status, "created_at": p.created_at.isoformat() + "Z", "rationale": p.rationale} for p in history],
    }


@router.post("/plans", status_code=201)
def create(body: PlanIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    decision = check_permission("create_task", allow_task_writes=user.allow_task_writes)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    tasks = [task.model_dump() for task in body.tasks]
    rationale = body.rationale
    refs = list(body.refs)
    budget = body.daily_budget_minutes or user.daily_minutes
    if body.generate_from_opportunity_id is not None:
        opportunity = get_opportunity(db, user, body.generate_from_opportunity_id)
        if opportunity is None:
            raise HTTPException(status_code=404, detail="Opportunity not found.")
        gap_result = gaps_for(db, user, opportunity)
        tasks = generate_candidates_from_gaps(gap_result["gaps"], budget) + tasks
        rationale = rationale or f"Plan generated from the ranked gaps for '{opportunity.title}' (fit {gap_result['fit']['score']}%)."
        refs.append(f"opp#{opportunity.id}")
    if not tasks:
        raise HTTPException(status_code=422, detail="A plan needs at least one task (or generate_from_opportunity_id).")
    try:
        plan = create_plan(db, user, tasks=tasks, daily_budget_minutes=budget, goal_id=body.goal_id, rationale=rationale, refs=refs)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return serialize_plan(plan)


@router.post("/plans/replan")
def do_replan(body: ReplanIn | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    body = body or ReplanIn()
    try:
        result = replan(db, user, available_minutes=body.available_minutes, reason=body.reason)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return result


@router.get("/plans/{plan_id}")
def read_plan(plan_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    plan = db.get(models.Plan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return serialize_plan(plan)


@router.patch("/plans/tasks/{task_id}")
def set_task_status(task_id: int, body: TaskStatusIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    task = db.get(models.Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found.")
    try:
        update_task_status(db, user, task, body.status)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    from app.services.plan_service import serialize_task

    return serialize_task(task)
