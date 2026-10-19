"""Memory API: the user can view, add, edit, delete and purge every item.

GET /memory returns both the full item list and the compact state the
frontend's Memory/Pipeline screens read (memoryNotes, latestPractice,
trace, originalPlan, updatedPlan, replanReason).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import MemoryIn, MemoryPatch
from app.api.deps import get_current_user, get_db
from app.db import models
from app.memory import service as memory_service
from app.memory.retrieval import TASK_MEMORY_KINDS, active_weaknesses, prompt_text, retrieve_for_task
from app.permissions import check_permission
from app.services.events import list_events, log_event, serialize_event
from app.services.memory_writes import add_constraint, add_decision, add_evidence, add_goal, add_skill
from app.services.plan_service import active_plan, plan_titles, previous_plan
from app.services.weakness_service import record_user_weakness

router = APIRouter(tags=["memory"])

PRACTICE_PREFIX = "practice focus:"


def _latest_practice(db: Session, user_id: int) -> dict | None:
    session = db.scalar(
        select(models.PracticeSession)
        .where(models.PracticeSession.user_id == user_id, models.PracticeSession.status == "evaluated")
        .order_by(models.PracticeSession.evaluated_at.desc(), models.PracticeSession.id.desc())
        .limit(1)
    )
    if session is None:
        return None
    return {
        "session_id": session.id,
        "answer": session.answer or "",
        "score": session.score,
        "weakness": session.topic,
        "feedback": session.feedback or "",
        "submittedAt": (session.evaluated_at or session.created_at).isoformat() + "Z",
        "missing_concepts": list(session.missing_concepts or []),
    }


def memory_notes(db: Session, user_id: int, items: list[models.MemoryItem]) -> list[str]:
    """Plain-text notes for the frontend's Memory screen.

    Each active weakness also appears as ``"Practice focus: <topic>"``: the
    Memory and Pipeline screens use that exact text to show an insight as saved.
    """

    focus = [f"Practice focus: {weakness.topic}" for weakness in active_weaknesses(db, user_id)]
    notes = focus + [item.content for item in items if item.deleted_at is None]
    return list(dict.fromkeys(notes))


def memory_state(db: Session, user: models.User, *, include_deleted: bool = False, types: set[str] | None = None) -> dict:
    items = memory_service.list_items(db, user.id, include_deleted=include_deleted, types=types)
    plan = active_plan(db, user.id)
    previous = previous_plan(db, plan) if plan else None
    return {
        "total": len(items),
        "items": [memory_service.serialize_item(item) for item in items],
        "memoryNotes": memory_notes(db, user.id, items),
        "latestPractice": _latest_practice(db, user.id),
        "trace": [serialize_event(event) for event in list_events(db, user_id=user.id, limit=50)],
        "originalPlan": plan_titles(previous) if previous else plan_titles(plan),
        "updatedPlan": plan_titles(plan) if previous else None,
        "replanReason": plan.rationale if (plan and previous) else None,
    }


@router.get("/memory")
def read_memory(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    include_deleted: bool = False,
    type: list[str] | None = Query(default=None),
) -> dict:
    return memory_state(db, user, include_deleted=include_deleted, types=set(type) if type else None)


@router.get("/memory/context")
def memory_context(
    task: str = Query(..., description=f"One of {sorted(TASK_MEMORY_KINDS)}"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    """The exact memory slice an agent task would receive (deleted items never appear)."""

    try:
        bundle = retrieve_for_task(db, user, task)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {**bundle.as_dict(), "prompt_text": prompt_text(bundle), "refs": sorted(bundle.all_refs())}


@router.post("/memory", status_code=201)
def create_memory(
    body: MemoryIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    memory_type = body.type.strip().lower()
    payload = dict(body.payload or {})
    extra = dict(body.model_extra or {})
    payload.update({k: v for k, v in extra.items() if k not in payload})
    content = body.content.strip()

    try:
        if memory_type == "weakness":
            topic = content[len(PRACTICE_PREFIX):].strip() if content.lower().startswith(PRACTICE_PREFIX) else content
            weakness = record_user_weakness(db, user, topic, source=body.source, severity=str(payload.get("severity", "medium")))
            item = memory_service.list_items(db, user.id, types={"weakness"})
            item = next(i for i in item if i.ref_id == f"weakness#{weakness.id}")
        elif memory_type == "decision":
            reason = body.reason or payload.get("reason")
            if not reason:
                raise ValueError("A decision needs a reason (the 'why').")
            decision = add_decision(db, user, statement=content, reason=str(reason), goal_id=payload.get("goal_id"), source=body.source)
            item = next(i for i in memory_service.list_items(db, user.id, types={"decision"}) if i.ref_id == f"decision#{decision.id}")
        elif memory_type == "goal":
            goal = add_goal(
                db,
                user,
                title=content,
                target_role=payload.get("target_role"),
                priority_rank=int(payload.get("priority_rank", 1)),
                hours_per_day=payload.get("hours_per_day"),
                source=body.source,
            )
            item = next(i for i in memory_service.list_items(db, user.id, types={"goal"}) if i.ref_id == f"goal#{goal.id}")
        elif memory_type == "constraint":
            constraint = add_constraint(db, user, kind=str(payload.get("kind", "boundary")), value=content, source=body.source)
            item = next(i for i in memory_service.list_items(db, user.id, types={"constraint"}) if i.ref_id == f"constraint#{constraint.id}")
        elif memory_type == "skill":
            skill = add_skill(db, user, name=content, level=str(payload.get("level", "beginner")), confidence=int(payload.get("confidence", 50)), source=body.source)
            item = next(i for i in memory_service.list_items(db, user.id, types={"skill"}) if i.ref_id == f"skill#{skill.id}")
        elif memory_type == "evidence":
            skill_id = payload.get("skill_id")
            skill = db.get(models.Skill, int(skill_id)) if skill_id is not None else None
            if skill is None or skill.user_id != user.id or skill.deleted_at is not None:
                raise ValueError("Evidence needs an existing skill_id in payload.")
            evidence = add_evidence(db, user, skill, type=str(payload.get("evidence_type", payload.get("kind", "other"))), description=content, url=payload.get("url"), source=body.source)
            item = next(i for i in memory_service.list_items(db, user.id, types={"evidence"}) if i.ref_id == f"ev#{evidence.id}")
        else:
            item = memory_service.record_note(
                db,
                user.id,
                type=memory_type,
                content=content,
                source=body.source,
                payload=payload,
                tags=body.tags,
                visibility=body.visibility,
            )
            from app.services.events import log_event

            log_event(db, user_id=user.id, agent="memory", action="memory_added", summary=f"{memory_type} saved: {content}", refs=[f"memory#{item.id}"])
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error

    if body.tags and item.tags != body.tags:
        item.tags = sorted(set(item.tags or []) | set(body.tags))
    db.commit()
    db.refresh(item)
    return memory_service.serialize_item(item)


@router.post("/memory/import-legacy")
def import_legacy_memory(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    """Copy memories the AI's /practice endpoint wrote to data/memories.json into the database.

    Weaknesses become weakness entities (so they influence replanning),
    decisions become decision entities, learning insights become notes.
    Each legacy item is imported once (tracked by a ``legacy:<id>`` tag).
    """

    from app.services.memory_store import load_memories
    from app.services.memory_writes import add_decision

    try:
        legacy = load_memories()
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail=f"Could not read the legacy memory file: {error}") from error

    already = {tag for item in memory_service.list_items(db, user.id, include_deleted=True) for tag in (item.tags or []) if tag.startswith("legacy:")}
    imported: list[str] = []
    for memory in legacy:
        tag = f"legacy:{memory.memory_id}"
        if tag in already:
            continue
        source = f"legacy:{memory.source}"
        if memory.memory_type == "weakness":
            weakness = record_user_weakness(db, user, memory.content, source=source)
            ref = f"weakness#{weakness.id}"
        elif memory.memory_type == "decision":
            decision = add_decision(db, user, statement=memory.content, reason=f"Recorded by the Memory agent from {memory.source}.", source=source)
            ref = f"decision#{decision.id}"
        else:
            note = memory_service.record_note(db, user.id, type="learning_insight", content=memory.content, source=source,
                                              payload={"confidence": memory.confidence, "reference_tags": memory.reference_tags})
            ref = f"memory#{note.id}"
        item = next((i for i in memory_service.list_items(db, user.id) if i.ref_id == ref or f"memory#{i.id}" == ref), None)
        if item is not None:
            item.tags = sorted(set(item.tags or []) | {tag})
        imported.append(memory.memory_id)
    if imported:
        log_event(db, user_id=user.id, agent="memory", action="legacy_imported",
                  summary=f"Imported {len(imported)} memory item(s) from the legacy JSON store into the database.")
    db.commit()
    return {"imported": imported, "skipped": len(legacy) - len(imported), "total_legacy": len(legacy)}


@router.get("/memory/{memory_id}")
def read_memory_item(memory_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    item = memory_service.get_item(db, user.id, memory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    return memory_service.serialize_item(item)


@router.patch("/memory/{memory_id}")
def patch_memory_item(
    memory_id: int,
    body: MemoryPatch,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    item = memory_service.get_item(db, user.id, memory_id)
    if item is None or item.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    try:
        memory_service.update_item(db, item, content=body.content, payload=body.payload, tags=body.tags, visibility=body.visibility)
    except (ValueError, TypeError) as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    db.refresh(item)
    return memory_service.serialize_item(item)


@router.delete("/memory/{memory_id}")
def delete_memory_item(memory_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    item = memory_service.get_item(db, user.id, memory_id)
    if item is None or item.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    memory_service.soft_delete_item(db, item)
    db.commit()
    return {"deleted": True, "id": item.id, "ref": item.ref_id}


@router.post("/memory/purge")
def purge_memory(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    removed = memory_service.purge_deleted(db, user.id)
    db.commit()
    return {"purged": removed}


@router.delete("/memory")
def delete_all_memory(
    confirm: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    decision = check_permission("delete_all_memory", user_confirmed=confirm)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    count = memory_service.delete_all(db, user.id)
    db.commit()
    return {"deleted": count, "permission": decision.as_dict()}
