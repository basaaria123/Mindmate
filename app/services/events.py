"""Event log: every agent action is recorded so the Trace screen can explain
what MindMate did and why (proposal section 7, ``Event`` entity)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def log_event(
    db: Session,
    *,
    agent: str,
    action: str,
    summary: str,
    refs: list[str] | None = None,
    user_id: int | None = None,
    payload: dict | None = None,
) -> models.Event:
    event = models.Event(
        user_id=user_id,
        agent=agent,
        action=action,
        summary=summary,
        refs=list(refs or []),
        payload=dict(payload or {}),
    )
    db.add(event)
    db.flush()
    return event


def list_events(
    db: Session,
    *,
    user_id: int | None = None,
    agent: str | None = None,
    limit: int = 100,
) -> list[models.Event]:
    query = select(models.Event).order_by(models.Event.timestamp.desc(), models.Event.id.desc())
    if user_id is not None:
        query = query.where((models.Event.user_id == user_id) | (models.Event.user_id.is_(None)))
    if agent:
        query = query.where(models.Event.agent == agent)
    return list(db.scalars(query.limit(limit)))


def serialize_event(event: models.Event) -> dict:
    timestamp = event.timestamp.isoformat() + "Z"
    return {
        "id": event.id,
        "timestamp": timestamp,
        "agent": event.agent,
        "action": event.action,
        "summary": event.summary,
        "refs": list(event.refs or []),
        "payload": dict(event.payload or {}),
        # Frontend-friendly aliases (mindmate-frontend/src/services/api.ts)
        "title": f"{event.agent}: {event.action}",
        "detail": event.summary,
        "occurredAt": timestamp,
    }
