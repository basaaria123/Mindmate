"""POST /assistant/chat — the AI Assistant, answered by Nemotron on Nebius Token Factory."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db import models
from app.schemas.assistant import ChatMessage
from app.services.assistant_service import AssistantFailed, AssistantUnavailable, reply

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)
    think_harder: bool = False


@router.post("/chat")
def chat(body: ChatRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    if body.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="The last message must come from the user.")
    try:
        answer = reply(db, user, body.messages, think_harder=body.think_harder)
    except AssistantUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except AssistantFailed as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {"reply": answer.reply, "model": answer.model, "source": "nemotron"}
