"""Agentic actions behind the permission layer: drafts only, user confirms."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import ActionIn
from app.api.deps import get_current_user, get_db
from app.db import models
from app.db.models import utcnow
from app.memory.refs import filter_valid_refs
from app.permissions import ACTION_PERMISSIONS, check_permission
from app.services.events import log_event

router = APIRouter(prefix="/actions", tags=["actions"])


def serialize_draft(draft: models.ActionDraft) -> dict:
    return {
        "id": draft.id,
        "kind": draft.kind,
        "permission_level": draft.permission_level,
        "payload": dict(draft.payload or {}),
        "status": draft.status,
        "refs": list(draft.refs or []),
        "created_at": draft.created_at.isoformat() + "Z",
        "confirmed_at": draft.confirmed_at.isoformat() + "Z" if draft.confirmed_at else None,
        "next_step": "The user reviews and submits this manually; MindMate never submits on their behalf."
        if draft.permission_level == "application_actions"
        else None,
    }


@router.get("/permissions")
def permissions() -> dict:
    return {
        "actions": {action: check_permission(action).as_dict() | {"level": level.value} for action, level in ACTION_PERMISSIONS.items()},
    }


@router.get("")
def list_drafts(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    drafts = db.scalars(select(models.ActionDraft).where(models.ActionDraft.user_id == user.id).order_by(models.ActionDraft.created_at.desc()))
    return {"drafts": [serialize_draft(d) for d in drafts]}


@router.post("", status_code=201)
def request_action(body: ActionIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    decision = check_permission(body.action, user_confirmed=body.confirmed, allow_task_writes=user.allow_task_writes)
    log_event(
        db,
        user_id=user.id,
        agent="permissions",
        action="permission_checked",
        summary=f"Action '{body.action}' {'allowed' if decision.allowed else 'denied'}: {decision.reason}",
        payload=decision.as_dict(),
    )
    if not decision.allowed:
        db.commit()
        raise HTTPException(status_code=403, detail=decision.reason)
    valid, invalid = filter_valid_refs(db, body.refs)
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unknown references: {invalid}")
    draft = models.ActionDraft(
        user_id=user.id,
        kind=body.action,
        permission_level=decision.level.value if decision.level else "read_only",
        payload=body.payload,
        status="draft",
        refs=valid,
    )
    db.add(draft)
    db.flush()
    log_event(db, user_id=user.id, agent="actions", action="draft_created", summary=f"Draft created for '{body.action}'.", refs=[f"memory#{0}"][:0] + valid)
    db.commit()
    return {**serialize_draft(draft), "permission": decision.as_dict()}


@router.post("/{draft_id}/confirm")
def confirm_draft(draft_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    draft = db.get(models.ActionDraft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise HTTPException(status_code=404, detail="Draft not found.")
    draft.status = "confirmed"
    draft.confirmed_at = utcnow()
    log_event(db, user_id=user.id, agent="actions", action="draft_confirmed", summary=f"User confirmed draft {draft.id} ({draft.kind}); any submission happens manually.")
    db.commit()
    return serialize_draft(draft)


@router.post("/{draft_id}/cancel")
def cancel_draft(draft_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    draft = db.get(models.ActionDraft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise HTTPException(status_code=404, detail="Draft not found.")
    draft.status = "cancelled"
    log_event(db, user_id=user.id, agent="actions", action="draft_cancelled", summary=f"Draft {draft.id} cancelled by the user.")
    db.commit()
    return serialize_draft(draft)
