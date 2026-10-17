"""GET/PUT /profile — the stored user profile (frontend shape plus extras)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.contracts import ProfileIn
from app.api.deps import get_current_user, get_db
from app.db import models
from app.memory.service import record_note
from app.services.events import log_event

router = APIRouter(tags=["profile"])


def serialize_user(user: models.User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "goal": user.goal_text or "",
        "targetRole": user.target_role or "",
        "dailyMinutes": user.daily_minutes,
        "education": user.education,
        "summary": user.summary,
        "allowTaskWrites": user.allow_task_writes,
        "preferences": dict(user.preferences or {}),
        "updatedAt": user.updated_at.isoformat() + "Z",
    }


@router.get("/profile")
def read_profile(user: models.User = Depends(get_current_user)) -> dict:
    return serialize_user(user)


@router.put("/profile")
def update_profile(
    body: ProfileIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    changed: list[str] = []
    for field, attribute in (
        ("name", "name"),
        ("goal", "goal_text"),
        ("targetRole", "target_role"),
        ("dailyMinutes", "daily_minutes"),
        ("education", "education"),
        ("summary", "summary"),
        ("email", "email"),
        ("allowTaskWrites", "allow_task_writes"),
    ):
        value = getattr(body, field)
        if value is not None and getattr(user, attribute) != value:
            setattr(user, attribute, value)
            changed.append(field)
    if body.preferences is not None:
        merged = dict(user.preferences or {})
        merged.update(body.preferences)
        user.preferences = merged
        changed.append("preferences")
        for key, value in body.preferences.items():
            record_note(db, user.id, type="preference", content=f"{key.replace('_', ' ')}: {value}", payload={key: value})
    db.flush()
    if changed:
        record_note(
            db,
            user.id,
            type="profile",
            content=f"Profile updated: {', '.join(changed)}.",
            payload={field: getattr(body, field) for field in changed if field != "preferences"},
        )
        log_event(db, user_id=user.id, agent="profile", action="profile_updated", summary=f"Profile fields updated: {', '.join(changed)}.")
    db.commit()
    db.refresh(user)
    return serialize_user(user)
