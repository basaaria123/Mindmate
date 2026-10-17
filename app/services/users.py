"""Current-user resolution. MindMate is single-user per database in the MVP;
an optional ``X-User-Id`` header selects another user when one exists."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db, models


def get_or_create_default_user(db: Session) -> models.User:
    user = db.scalar(select(models.User).order_by(models.User.id).limit(1))
    if user is None:
        user = models.User(name="MindMate learner", daily_minutes=get_settings().default_daily_minutes)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> models.User:
    if x_user_id is not None:
        user = db.get(models.User, x_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User {x_user_id} not found.")
        return user
    return get_or_create_default_user(db)
