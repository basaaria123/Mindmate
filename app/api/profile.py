"""GET/PUT /profile — the stored user profile (frontend shape plus extras)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.contracts import ProfileImportIn, ProfileIn
from app.api.deps import get_current_user, get_db
from app.db import models
from app.memory.retrieval import active_goals, active_skills
from app.memory.service import list_items, record_note
from app.scoring.fit import skill_matches
from app.services.memory_writes import add_goal, add_skill
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


PLACEHOLDER_VALUES = {"", "not specified", "none", "n/a", "unknown"}


@router.post("/profile/import")
def import_profile(
    body: ProfileImportIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    """Store what the Profile agent extracted (POST /profile) in structured memory.

    Goals become goal entities, skills become skill entities at beginner level
    with no evidence (a stated skill is a claim until evidence is added, so it
    does not raise fit scores), and interests and learning preferences become
    preference notes. Items that already exist are skipped, so the call is
    safe to repeat.
    """

    added: dict[str, list[str]] = {"goals": [], "skills": [], "preferences": []}
    skipped: list[str] = []

    if body.education and body.education.strip().lower() not in PLACEHOLDER_VALUES:
        user.education = body.education.strip()
    if body.daily_available_minutes:
        user.daily_minutes = body.daily_available_minutes

    goals = active_goals(db, user.id)
    existing_titles = {goal.title.strip().lower() for goal in goals}
    next_rank = max((goal.priority_rank for goal in goals), default=0) + 1
    for title in body.goals:
        title = title.strip()
        if not title:
            continue
        if title.lower() in existing_titles:
            skipped.append(f"goal: {title}")
            continue
        add_goal(db, user, title=title, priority_rank=next_rank, source="profile_agent")
        existing_titles.add(title.lower())
        added["goals"].append(title)
        next_rank += 1
    if added["goals"] and not user.goal_text:
        user.goal_text = added["goals"][0]

    skills = [skill.name for skill in active_skills(db, user.id)]
    for name in body.skills:
        name = name.strip()
        if not name:
            continue
        if any(skill_matches(name, existing) for existing in skills):
            skipped.append(f"skill: {name}")
            continue
        add_skill(db, user, name=name, level="beginner", confidence=40, source="profile_agent")
        skills.append(name)
        added["skills"].append(name)

    existing_notes = {item.content.strip().lower() for item in list_items(db, user.id, types={"preference"})}
    for label, values in (("interest", body.interests), ("learning preference", body.learning_preferences)):
        for value in values:
            value = value.strip()
            if not value:
                continue
            content = f"{label}: {value}"
            if content.lower() in existing_notes:
                skipped.append(content)
                continue
            record_note(db, user.id, type="preference", content=content, source="profile_agent", payload={label.replace(" ", "_"): value})
            existing_notes.add(content.lower())
            added["preferences"].append(content)

    log_event(
        db,
        user_id=user.id,
        agent="profile",
        action="profile_imported",
        summary=(
            f"Profile agent output stored: {len(added['goals'])} goal(s), {len(added['skills'])} skill(s), "
            f"{len(added['preferences'])} preference(s); {len(skipped)} already known."
        ),
    )
    db.commit()
    db.refresh(user)
    return {"added": added, "skipped": skipped, "profile": serialize_user(user)}
