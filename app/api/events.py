"""GET /agent/events — the activity trace."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db import models
from app.services.events import list_events, serialize_event

router = APIRouter(prefix="/agent", tags=["trace"])


@router.get("/events")
def read_events(
    limit: int = Query(default=100, ge=1, le=500),
    agent: str | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    events = list_events(db, user_id=user.id, agent=agent, limit=limit)
    return {"total": len(events), "events": [serialize_event(e) for e in events]}
