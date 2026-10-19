"""Admin: demo reset and backend status."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings, llm_available
from app.db import models
from app.services.seed import reset_demo

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")) -> None:
    token = get_settings().admin_token
    if token and x_admin_token != token:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Admin-Token.")


@router.post("/reset-demo", dependencies=[Depends(require_admin)])
def reset(db: Session = Depends(get_db)) -> dict:
    return reset_demo(db)


@router.get("/status")
def status(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    counts = {
        table.__tablename__: db.scalar(select(func.count()).select_from(table)) or 0
        for table in (models.User, models.Goal, models.Skill, models.Evidence, models.Decision, models.Weakness, models.Opportunity, models.Plan, models.Task, models.PracticeSession, models.MemoryItem, models.Event)
    }
    backend = settings.database_url.split(":", 1)[0].split("+", 1)[0]
    return {
        "database": backend,
        "llm_mode": settings.llm_mode,
        "llm_available": llm_available(),
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "thresholds": {
            "weakness_score_threshold": settings.weakness_score_threshold,
            "weakness_min_occurrences": settings.weakness_min_occurrences,
            "weakness_severe_score": settings.weakness_severe_score,
        },
        "priority_weights": settings.priority_weights.__dict__,
        "counts": counts,
    }
