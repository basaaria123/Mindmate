"""The memory layer: the single place that writes, edits and purges memory.

Design rules (proposal sections 7 and 8):
* Every typed entity (skill, evidence, decision, weakness, goal, constraint)
  gets a ``MemoryItem`` row so the user can view, edit and delete it.
* Deleting is a soft delete on both the memory item and the entity it
  references; retrieval always filters ``deleted_at IS NULL`` so purged items
  never reach a prompt again.
* ``purge`` removes soft-deleted rows for good.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.db.models import utcnow
from app.memory.refs import CANONICAL_PREFIX, REF_TYPES, make_ref, parse_ref
from app.services.events import log_event

MEMORY_TYPES = {
    "profile",
    "goal",
    "constraint",
    "skill",
    "evidence",
    "decision",
    "weakness",
    "preference",
    "learning_insight",
    "note",
}

ENTITY_MEMORY_TYPE = {
    models.Goal: "goal",
    models.Constraint: "constraint",
    models.Skill: "skill",
    models.Evidence: "evidence",
    models.Decision: "decision",
    models.Weakness: "weakness",
}


def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def entity_payload(entity: models.Base) -> dict:
    """Plain-dict snapshot of an entity for the memory payload."""

    payload = {}
    for column in entity.__table__.columns:
        if column.name in {"deleted_at", "created_at", "updated_at"}:
            continue
        payload[column.name] = _json_safe(getattr(entity, column.name))
    payload["ref"] = make_ref(entity)
    return payload


def summarize_entity(entity: models.Base) -> str:
    if isinstance(entity, models.Skill):
        return f"{entity.name} ({entity.level}, confidence {entity.confidence})"
    if isinstance(entity, models.Evidence):
        return f"{entity.type}: {entity.description}"
    if isinstance(entity, models.Decision):
        return f"{entity.statement} — because {entity.reason}"
    if isinstance(entity, models.Weakness):
        return f"{entity.topic} ({entity.severity}, seen {entity.evidence_count}x)"
    if isinstance(entity, models.Goal):
        deadline = f" by {entity.deadline.isoformat()}" if entity.deadline else ""
        return f"{entity.title}{deadline} (priority {entity.priority_rank})"
    if isinstance(entity, models.Constraint):
        return f"{entity.kind}: {entity.value}"
    return str(entity)


def record_entity(
    db: Session,
    entity: models.Base,
    *,
    source: str = "user",
    tags: list[str] | None = None,
    visibility: str = "private",
) -> models.MemoryItem:
    """Create (or refresh) the memory item for a typed entity."""

    db.flush()
    ref = make_ref(entity)
    existing = db.scalar(
        select(models.MemoryItem).where(
            models.MemoryItem.ref_id == ref, models.MemoryItem.deleted_at.is_(None)
        )
    )
    if existing is not None:
        existing.content = summarize_entity(entity)
        existing.payload = entity_payload(entity)
        if tags:
            existing.tags = sorted(set(existing.tags or []) | set(tags))
        db.flush()
        return existing

    item = models.MemoryItem(
        user_id=entity.user_id,
        type=ENTITY_MEMORY_TYPE[type(entity)],
        content=summarize_entity(entity),
        payload=entity_payload(entity),
        source=source,
        visibility=visibility,
        ref_id=ref,
        tags=list(tags or []),
    )
    db.add(item)
    db.flush()
    return item


def record_note(
    db: Session,
    user_id: int,
    *,
    type: str,
    content: str,
    source: str = "user",
    payload: dict | None = None,
    tags: list[str] | None = None,
    visibility: str = "private",
    ref_id: str | None = None,
) -> models.MemoryItem:
    """Store a free-form memory item (preference, note, learning insight...)."""

    if type not in MEMORY_TYPES:
        raise ValueError(f"Unsupported memory type: {type}")
    item = models.MemoryItem(
        user_id=user_id,
        type=type,
        content=content.strip(),
        payload=dict(payload or {}),
        source=source,
        visibility=visibility,
        ref_id=ref_id,
        tags=list(tags or []),
    )
    db.add(item)
    db.flush()
    return item


def list_items(
    db: Session,
    user_id: int,
    *,
    types: set[str] | None = None,
    include_deleted: bool = False,
    limit: int | None = None,
) -> list[models.MemoryItem]:
    query = select(models.MemoryItem).where(models.MemoryItem.user_id == user_id)
    if not include_deleted:
        query = query.where(models.MemoryItem.deleted_at.is_(None))
    if types:
        query = query.where(models.MemoryItem.type.in_(sorted(types)))
    query = query.order_by(models.MemoryItem.created_at.desc(), models.MemoryItem.id.desc())
    if limit:
        query = query.limit(limit)
    return list(db.scalars(query))


def get_item(db: Session, user_id: int, memory_id: int) -> models.MemoryItem | None:
    item = db.get(models.MemoryItem, memory_id)
    if item is None or item.user_id != user_id:
        return None
    return item


def _referenced_entity(db: Session, item: models.MemoryItem) -> models.Base | None:
    if not item.ref_id:
        return None
    try:
        ref = parse_ref(item.ref_id)
    except ValueError:
        return None
    return db.get(REF_TYPES[ref.prefix], ref.id)


def update_item(
    db: Session,
    item: models.MemoryItem,
    *,
    content: str | None = None,
    payload: dict | None = None,
    tags: list[str] | None = None,
    visibility: str | None = None,
) -> models.MemoryItem:
    """Edit a memory item; structured fields flow back to the typed entity."""

    entity = _referenced_entity(db, item)

    if content is not None and content.strip():
        item.content = content.strip()
        if isinstance(entity, models.Decision):
            entity.statement = content.strip()
        elif isinstance(entity, models.Weakness):
            entity.topic = content.strip()
        elif isinstance(entity, models.Skill):
            entity.name = content.strip()
        elif isinstance(entity, models.Goal):
            entity.title = content.strip()
        elif isinstance(entity, models.Evidence):
            entity.description = content.strip()
        elif isinstance(entity, models.Constraint):
            entity.value = content.strip()

    if payload:
        merged = dict(item.payload or {})
        merged.update(payload)
        item.payload = merged
        if entity is not None:
            for key, value in payload.items():
                if key in {"id", "user_id", "ref"}:
                    continue
                if hasattr(entity, key) and key in entity.__table__.columns.keys():
                    column = entity.__table__.columns[key]
                    if isinstance(column.type, models.Date) and isinstance(value, str):
                        value = date.fromisoformat(value)
                    setattr(entity, key, value)
            item.payload = entity_payload(entity) | {
                key: value for key, value in merged.items() if key not in entity.__table__.columns.keys()
            }
            if content is None:
                item.content = summarize_entity(entity)

    if tags is not None:
        item.tags = list(tags)
    if visibility is not None:
        item.visibility = visibility

    db.flush()
    log_event(
        db,
        user_id=item.user_id,
        agent="memory",
        action="memory_updated",
        summary=f"Memory item {item.ref_id or item.id} edited by the user.",
        refs=[item.ref_id] if item.ref_id else [f"memory#{item.id}"],
    )
    return item


def soft_delete_item(db: Session, item: models.MemoryItem) -> models.MemoryItem:
    """Hide a memory item (and its entity) from every later retrieval."""

    now = utcnow()
    item.deleted_at = now
    entity = _referenced_entity(db, item)
    if entity is not None and hasattr(entity, "deleted_at"):
        entity.deleted_at = now
        if isinstance(entity, models.Weakness):
            entity.status = "deleted"
        if isinstance(entity, models.Goal):
            entity.status = "deleted"
    db.flush()
    log_event(
        db,
        user_id=item.user_id,
        agent="memory",
        action="memory_deleted",
        summary=f"Memory item {item.ref_id or item.id} deleted by the user; it will not be used again.",
        refs=[],
    )
    return item


def purge_deleted(db: Session, user_id: int) -> int:
    """Permanently remove soft-deleted memory items and entities."""

    removed = 0
    items = list(
        db.scalars(
            select(models.MemoryItem).where(
                models.MemoryItem.user_id == user_id, models.MemoryItem.deleted_at.is_not(None)
            )
        )
    )
    for item in items:
        entity = _referenced_entity(db, item)
        if entity is not None and getattr(entity, "deleted_at", None) is not None:
            if isinstance(entity, models.Skill):
                for evidence in list(entity.evidence):
                    db.delete(evidence)
            if isinstance(entity, models.Weakness):
                for session in db.scalars(
                    select(models.PracticeSession).where(models.PracticeSession.weakness_id == entity.id)
                ):
                    session.weakness_id = None
            db.delete(entity)
        db.delete(item)
        removed += 1
    db.flush()
    if removed:
        log_event(
            db,
            user_id=user_id,
            agent="memory",
            action="memory_purged",
            summary=f"{removed} deleted memory item(s) permanently purged at the user's request.",
        )
    return removed


def delete_all(db: Session, user_id: int) -> int:
    """Soft-delete every memory item for the user (requires explicit confirmation upstream)."""

    count = 0
    for item in list_items(db, user_id):
        soft_delete_item(db, item)
        count += 1
    return count


def serialize_item(item: models.MemoryItem) -> dict:
    return {
        "id": item.id,
        "type": item.type,
        "content": item.content,
        "payload": dict(item.payload or {}),
        "source": item.source,
        "visibility": item.visibility,
        "ref": item.ref_id,
        "tags": list(item.tags or []),
        "createdAt": item.created_at.isoformat() + "Z",
        "updatedAt": item.updated_at.isoformat() + "Z",
        "deletedAt": item.deleted_at.isoformat() + "Z" if item.deleted_at else None,
    }


__all__ = [
    "MEMORY_TYPES",
    "CANONICAL_PREFIX",
    "record_entity",
    "record_note",
    "list_items",
    "get_item",
    "update_item",
    "soft_delete_item",
    "purge_deleted",
    "delete_all",
    "serialize_item",
    "entity_payload",
    "summarize_entity",
]
