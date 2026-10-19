"""Seed and reset: one command returns the database to the demo persona.

``reset_demo`` wipes every table and rebuilds Meera's memory (profile, goals,
constraints, decisions, skills with evidence, curated opportunities, one prior
weak practice answer and the day-one plan). The scripted demo then runs:
practice -> weakness -> replan on top of this state.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from app.config import data_file
from app.db import models
from app.db.models import utcnow
from app.memory.refs import make_ref
from app.memory.service import record_note
from app.services.events import log_event
from app.services.memory_writes import add_constraint, add_decision, add_evidence, add_goal, add_skill
from app.services.opportunity_service import assess_fit, curated_opportunities, store_opportunity
from app.services.plan_service import create_plan
from app.services.practice_service import question_bank

WIPE_ORDER = (
    models.Task,
    models.Plan,
    models.PracticeSession,
    models.FitAssessment,
    models.ActionDraft,
    models.MemoryItem,
    models.Event,
    models.Weakness,
    models.Evidence,
    models.Skill,
    models.Decision,
    models.Constraint,
    models.Opportunity,
    models.Goal,
    models.User,
)


def load_persona() -> dict:
    with data_file("MINDMATE_SEED_PERSONA", "seed_persona.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def wipe(db: Session) -> None:
    """Remove all rows. On PostgreSQL identities restart too, so every reset
    produces the same reference IDs (weakness#1, plan#1, ...) as on SQLite."""

    if db.get_bind().dialect.name == "postgresql":
        tables = ", ".join(model.__tablename__ for model in WIPE_ORDER)
        db.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    else:
        for model in WIPE_ORDER:
            db.execute(delete(model))
    db.flush()


def seed(db: Session, *, today: date | None = None) -> dict:
    """Populate an empty database with the demo persona. Returns a summary."""

    today = today or date.today()
    persona = load_persona()

    user_data = persona["user"]
    user = models.User(
        name=user_data["name"],
        email=user_data.get("email"),
        education=user_data.get("education"),
        summary=user_data.get("summary"),
        target_role=user_data.get("target_role"),
        goal_text=user_data.get("goal_text"),
        daily_minutes=user_data.get("daily_minutes", 60),
        preferences=user_data.get("preferences", {}),
    )
    db.add(user)
    db.flush()
    record_note(
        db,
        user.id,
        type="profile",
        content=f"{user.name}: {user.education}. {user.summary}",
        source="seed",
        payload={"education": user.education, "target_role": user.target_role, "daily_minutes": user.daily_minutes},
    )
    for key, value in (user_data.get("preferences") or {}).items():
        record_note(db, user.id, type="preference", content=f"{key.replace('_', ' ')}: {value}", source="seed", payload={key: value})

    goals_by_key: dict[str, models.Goal] = {}
    for goal_data in persona["goals"]:
        goal = add_goal(
            db,
            user,
            title=goal_data["title"],
            target_role=goal_data.get("target_role"),
            deadline=today + timedelta(days=goal_data["deadline_in_days"]) if goal_data.get("deadline_in_days") else None,
            hours_per_day=goal_data.get("hours_per_day"),
            priority_rank=goal_data.get("priority_rank", 1),
            source="seed",
        )
        goals_by_key[goal_data["key"]] = goal

    for constraint_data in persona["constraints"]:
        add_constraint(db, user, kind=constraint_data["kind"], value=constraint_data["value"], source="seed")

    decisions = []
    for decision_data in persona["decisions"]:
        goal = goals_by_key.get(decision_data.get("goal_key"))
        decisions.append(
            add_decision(db, user, statement=decision_data["statement"], reason=decision_data["reason"], goal_id=goal.id if goal else None, source="seed")
        )

    skills: dict[str, models.Skill] = {}
    for skill_data in persona["skills"]:
        skill = add_skill(db, user, name=skill_data["name"], level=skill_data["level"], confidence=skill_data["confidence"], source="seed")
        skills[skill.name] = skill
        for evidence_data in skill_data.get("evidence", []):
            add_evidence(db, user, skill, type=evidence_data["type"], description=evidence_data["description"], url=evidence_data.get("url"), source="seed")

    opportunity_data = persona.get("opportunities") or curated_opportunities()
    opportunities = [store_opportunity(db, None, data, source="curated", agent="seed") for data in opportunity_data]
    for opportunity in opportunities:
        assess_fit(db, user, opportunity, use_model=False)

    bank = question_bank()
    for history in persona.get("practice_history", []):
        entry = [q for q in bank if q["topic"] == history["topic"]][history.get("question_index", 0)]
        session = models.PracticeSession(
            user_id=user.id,
            topic=history["topic"],
            question=entry["question"],
            expected_concepts=list(entry.get("expected_concepts", [])),
            answer=history["answer"],
            rubric_scores=history["rubric_scores"],
            missing_concepts=history["missing_concepts"],
            score=history["score"],
            feedback=history["feedback"],
            status="evaluated",
            evaluator="seed",
            evaluated_at=utcnow() - timedelta(days=2),
        )
        db.add(session)
        db.flush()
        log_event(
            db,
            user_id=user.id,
            agent="practice",
            action="answer_evaluated",
            summary=f"Earlier practice answer on {session.topic} scored {session.score}/100.",
            refs=[make_ref(session)],
        )

    plan_data = persona["plan"]
    decision_ref = make_ref(decisions[0]) if decisions else None
    tasks = []
    for task in plan_data["tasks"]:
        task = dict(task)
        goal_key = task.pop("goal_key", plan_data.get("goal_key"))
        goal = goals_by_key.get(goal_key)
        task["goal_id"] = goal.id if goal else None
        refs = []
        if goal:
            refs.append(make_ref(goal))
        if "[decision]" in task.get("why", "") and decision_ref:
            task["why"] = task["why"].replace("[decision]", f"[{decision_ref}]")
            refs.append(decision_ref)
        # cite evidence/skills that the task builds on
        for skill_name, skill in skills.items():
            if skill_name.lower() in task["title"].lower():
                refs.append(make_ref(skill))
        task["refs"] = refs
        tasks.append(task)
    plan = create_plan(
        db,
        user,
        tasks=tasks,
        daily_budget_minutes=plan_data.get("daily_budget_minutes", user.daily_minutes),
        goal_id=goals_by_key[plan_data["goal_key"]].id,
        rationale="Day-one plan built from the internship goal, the ranked gaps and the exams-first decision.",
        refs=[decision_ref] if decision_ref else [],
        agent="seed",
        today=today,
    )

    log_event(db, user_id=user.id, agent="admin", action="demo_seeded", summary="Demo persona seeded (Meera).", refs=[make_ref(plan)])
    db.commit()
    return {
        "user_id": user.id,
        "goals": len(goals_by_key),
        "skills": len(skills),
        "opportunities": len(opportunities),
        "decisions": len(decisions),
        "plan_id": plan.id,
        "tasks": len(plan.tasks),
    }


def reset_demo(db: Session, *, today: date | None = None) -> dict:
    wipe(db)
    db.commit()
    summary = seed(db, today=today)
    return {"status": "reset", **summary}
