"""Goals, constraints and decisions: the goal engine's inputs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.contracts import ConstraintIn, DecisionIn, GoalIn, GoalPatch
from app.api.deps import get_current_user, get_db
from app.db import models
from app.memory import service as memory_service
from app.memory.retrieval import _constraint_dict, _decision_dict, _goal_dict, active_constraints, active_decisions, active_goals
from app.services.memory_writes import add_constraint, add_decision, add_goal

router = APIRouter(tags=["goals"])


def _hierarchy(goals: list[models.Goal]) -> list[dict]:
    """Goals ordered by priority rank with their parent chain (exams before GATE)."""

    by_id = {goal.id: goal for goal in goals}
    ordered = sorted(goals, key=lambda g: (g.priority_rank, g.id))
    result = []
    for goal in ordered:
        chain = []
        parent = by_id.get(goal.parent_goal_id) if goal.parent_goal_id else None
        while parent is not None:
            chain.append(f"goal#{parent.id}")
            parent = by_id.get(parent.parent_goal_id) if parent.parent_goal_id else None
        result.append({**_goal_dict(goal), "parent_chain": chain, "comes_before": [f"goal#{g.id}" for g in ordered if g.priority_rank > goal.priority_rank]})
    return result


def _soft_delete_entity(db: Session, user: models.User, ref: str) -> None:
    item = next((i for i in memory_service.list_items(db, user.id) if i.ref_id == ref), None)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{ref} not found.")
    memory_service.soft_delete_item(db, item)


@router.get("/goals")
def list_goals(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    goals = active_goals(db, user.id)
    return {"goals": _hierarchy(goals), "current_goal": _hierarchy(goals)[0] if goals else None}


@router.post("/goals", status_code=201)
def create_goal(body: GoalIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    try:
        goal = add_goal(db, user, **body.model_dump())
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return _goal_dict(goal)


@router.patch("/goals/{goal_id}")
def update_goal(goal_id: int, body: GoalPatch, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    goal = db.get(models.Goal, goal_id)
    if goal is None or goal.user_id != user.id or goal.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Goal not found.")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(goal, field, value)
    db.flush()
    memory_service.record_entity(db, goal)
    from app.services.events import log_event

    log_event(db, user_id=user.id, agent="goal_engine", action="goal_updated", summary=f"Goal updated: {goal.title}.", refs=[f"goal#{goal.id}"])
    db.commit()
    return _goal_dict(goal)


@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    _soft_delete_entity(db, user, f"goal#{goal_id}")
    db.commit()
    return {"deleted": True, "ref": f"goal#{goal_id}"}


@router.get("/constraints")
def list_constraints(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    return {"constraints": [_constraint_dict(c) for c in active_constraints(db, user.id)], "daily_minutes": user.daily_minutes}


@router.post("/constraints", status_code=201)
def create_constraint(body: ConstraintIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    try:
        constraint = add_constraint(db, user, **body.model_dump())
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return _constraint_dict(constraint)


@router.delete("/constraints/{constraint_id}")
def delete_constraint(constraint_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    _soft_delete_entity(db, user, f"constraint#{constraint_id}")
    db.commit()
    return {"deleted": True, "ref": f"constraint#{constraint_id}"}


@router.get("/decisions")
def list_decisions(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    return {"decisions": [_decision_dict(d) for d in active_decisions(db, user.id)]}


@router.post("/decisions", status_code=201)
def create_decision(body: DecisionIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    try:
        decision = add_decision(db, user, **body.model_dump())
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return _decision_dict(decision)


@router.delete("/decisions/{decision_id}")
def delete_decision(decision_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    _soft_delete_entity(db, user, f"decision#{decision_id}")
    db.commit()
    return {"deleted": True, "ref": f"decision#{decision_id}"}
