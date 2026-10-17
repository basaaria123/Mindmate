"""Practice sessions: start a question, evaluate an answer, feed the loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import PracticeEvaluateIn, PracticeStartIn
from app.api.deps import get_current_user, get_db
from app.db import models
from app.services.practice_service import evaluate, serialize_session, start_session, topics

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/topics")
def list_topics() -> dict:
    return {"topics": topics()}


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    sessions = db.scalars(
        select(models.PracticeSession).where(models.PracticeSession.user_id == user.id).order_by(models.PracticeSession.created_at.desc())
    )
    return {"sessions": [serialize_session(s) for s in sessions]}


@router.post("/start", status_code=201)
def start(body: PracticeStartIn | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    body = body or PracticeStartIn()
    session = start_session(db, user, topic=body.topic, question=body.question)
    db.commit()
    return serialize_session(session)


@router.post("/evaluate")
def evaluate_answer(body: PracticeEvaluateIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    try:
        result = evaluate(db, user, answer=body.answer, session_id=body.session_id, question=body.question, topic=body.topic)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return result
