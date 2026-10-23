"""AI Assistant chat: Nemotron answers with the learner's memory as context.

Every request is recorded in the activity trace as what actually happened:
``model_call`` (model ID and measured seconds), ``model_error`` (the call failed;
no reply was generated) or ``model_unavailable`` (no key or model mode off; no call
was made). Message text is never written to the trace, only its length.
"""

from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.config import llm_available
from app.db import models
from app.memory.retrieval import prompt_text, retrieve_for_task
from app.schemas.assistant import AssistantReply, ChatMessage
from app.services.events import log_event


class AssistantUnavailable(RuntimeError):
    """The model cannot be called (no key, or MINDMATE_LLM_MODE is not live)."""


class AssistantFailed(RuntimeError):
    """The model was called but no usable reply came back."""


def memory_context(db: Session, user: models.User) -> str:
    """The learner's memory (deleted items excluded), current plan and target fit, as prompt text."""

    from app.services.opportunity_service import target_fit, target_opportunity
    from app.services.plan_service import active_plan

    lines = [prompt_text(retrieve_for_task(db, user, "assistant"))]
    plan = active_plan(db, user.id)
    if plan is not None:
        tasks = sorted(plan.tasks, key=lambda t: (t.day_number, t.order_index))
        done = [t for t in tasks if t.status == "done"]
        todo = [t for t in tasks if t.status != "done"]
        lines.append(f"PLAN: [plan#{plan.id}] version {plan.version}, {plan.daily_budget_minutes} min/day, "
                     f"{len(done)} of {len(tasks)} tasks done.")
        for task in todo[:8]:
            lines.append(f"  day {task.day_number}: {task.title} ({task.minutes} min, {task.priority})")
    opportunity, fit = target_opportunity(db, user), target_fit(db, user)
    if opportunity is not None:
        score = f", fit {fit.score}% ({fit.band})" if fit is not None else ""
        lines.append(f"TARGET OPPORTUNITY: [opp#{opportunity.id}] {opportunity.title}{score}")
    return "\n".join(line for line in lines if line)


def reply(db: Session, user: models.User, messages: list[ChatMessage], think_harder: bool = False) -> AssistantReply:
    from app.agents.assistant_agent import chat_reply
    from app.services.llm_client import get_model

    model = get_model("reasoning" if think_harder else "fast")
    size = {"messages": len(messages), "chars": len(messages[-1].content) if messages else 0}
    if not llm_available():
        log_event(db, user_id=user.id, agent="assistant", action="model_unavailable",
                  summary="assistant: no model call made; NEBIUS_API_KEY is not configured or MINDMATE_LLM_MODE is not live.",
                  payload={"model": model, **size})
        db.commit()
        raise AssistantUnavailable(
            "The AI model is not configured on the server. Set NEBIUS_API_KEY and MINDMATE_LLM_MODE=live on the backend."
        )

    context = memory_context(db, user)
    started = time.perf_counter()
    try:
        answer = chat_reply(messages, context, think_harder=think_harder)
    except Exception as error:  # noqa: BLE001 - every failure is reported, never hidden
        elapsed = round(time.perf_counter() - started, 2)
        log_event(db, user_id=user.id, agent="assistant", action="model_error",
                  summary=f"assistant: {model} failed after {elapsed}s ({type(error).__name__}); no reply was generated.",
                  payload={"model": model, "seconds": elapsed, "error": type(error).__name__, **size})
        db.commit()
        raise AssistantFailed(f"The AI model did not answer ({type(error).__name__}). Please try again.") from error

    elapsed = round(time.perf_counter() - started, 2)
    log_event(db, user_id=user.id, agent="assistant", action="model_call",
              summary=f"assistant: {answer.model} answered in {elapsed}s.",
              payload={"model": answer.model, "seconds": elapsed, "think_harder": think_harder, **size})
    db.commit()
    return answer
