"""Practice sessions: question bank, evaluation and the feedback loop.

Evaluation uses the Practice Agent (Nemotron) when a key is configured and
``MINDMATE_LLM_MODE=live``; otherwise, or on any model failure, it falls back
to a deterministic rubric over the question's expected concepts so the demo
loop always works. Either way the thresholds in ``weakness_service`` decide
whether anything becomes memory, never the model.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DATA_DIR, llm_available
from app.db import models
from app.db.models import utcnow
from app.memory.refs import make_ref
from app.memory.retrieval import active_weaknesses
from app.services.events import log_event
from app.services.weakness_service import apply_thresholds


@lru_cache(maxsize=1)
def question_bank() -> list[dict]:
    with (DATA_DIR / "question_bank.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)["questions"]


def topics() -> list[str]:
    seen: list[str] = []
    for item in question_bank():
        if item["topic"] not in seen:
            seen.append(item["topic"])
    return seen


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def matched_concepts(answer: str, question: dict) -> tuple[list[str], list[str]]:
    text = _normalise(answer)
    matched: list[str] = []
    missing: list[str] = []
    aliases = question.get("concept_aliases", {})
    for concept in question.get("expected_concepts", []):
        candidates = [concept.lower()] + [a.lower() for a in aliases.get(concept, [])]
        if any(candidate in text for candidate in candidates):
            matched.append(concept)
        else:
            missing.append(concept)
    return matched, missing


def deterministic_rubric(answer: str, question: dict) -> tuple[dict, list[str], list[str], str]:
    words = [w for w in re.split(r"\s+", answer.strip()) if w]
    sentences = [s for s in re.split(r"[.!?]+", answer) if s.strip()]
    matched, missing = matched_concepts(answer, question)
    expected = question.get("expected_concepts", [])
    coverage = len(matched) / len(expected) if expected else min(1.0, len(words) / 80)

    correctness = round(100 * coverage)
    depth = round(50 * coverage + 50 * min(1.0, len(words) / 100))
    avg_sentence = len(words) / len(sentences) if sentences else len(words)
    clarity = 70
    if 8 <= avg_sentence <= 28:
        clarity += 20
    if len(words) < 15:
        clarity -= 30
    if len(sentences) >= 3:
        clarity += 10
    clarity = max(0, min(100, clarity))

    rubric = {"correctness": correctness, "depth": depth, "clarity": clarity}
    feedback_parts = []
    if matched:
        feedback_parts.append("You covered: " + ", ".join(matched) + ".")
    if missing:
        feedback_parts.append("Not addressed: " + ", ".join(missing) + ".")
    if len(words) < 40:
        feedback_parts.append("The answer is short; explain the reasoning behind each point.")
    if not feedback_parts:
        feedback_parts.append("Solid answer with the expected concepts present.")
    return rubric, matched, missing, " ".join(feedback_parts)


def overall_score(rubric: dict) -> int:
    return int(round(0.5 * rubric["correctness"] + 0.3 * rubric["depth"] + 0.2 * rubric["clarity"]))


def pick_question(db: Session, user: models.User, topic: str | None) -> dict:
    bank = question_bank()
    if topic:
        pool = [q for q in bank if q["topic"].lower() == topic.lower()]
        if not pool:
            pool = [q for q in bank if topic.lower() in q["topic"].lower()]
        if not pool:
            return {"topic": topic, "question": f"Explain the key ideas of {topic} and how you have applied them.", "expected_concepts": [], "concept_aliases": {}}
    else:
        weaknesses = active_weaknesses(db, user.id)
        preferred = weaknesses[0].topic if weaknesses else None
        if preferred is None:
            latest_fit = db.scalar(
                select(models.FitAssessment).where(models.FitAssessment.user_id == user.id).order_by(models.FitAssessment.created_at.desc()).limit(1)
            )
            preferred = latest_fit.top_gap if latest_fit and latest_fit.top_gap else None
        pool = [q for q in bank if preferred and q["topic"].lower() == preferred.lower()] or bank

    # choose the least-used question in the pool
    used = {
        s.question: 0
        for s in db.scalars(select(models.PracticeSession).where(models.PracticeSession.user_id == user.id))
    }
    for s in db.scalars(select(models.PracticeSession).where(models.PracticeSession.user_id == user.id)):
        used[s.question] = used.get(s.question, 0) + 1
    return min(pool, key=lambda q: (used.get(q["question"], 0), pool.index(q)))


def start_session(db: Session, user: models.User, *, topic: str | None = None, question: str | None = None) -> models.PracticeSession:
    if question:
        chosen = {"topic": topic or "Custom", "question": question.strip(), "expected_concepts": [], "concept_aliases": {}}
    else:
        chosen = pick_question(db, user, topic)
    session = models.PracticeSession(
        user_id=user.id,
        topic=chosen["topic"],
        question=chosen["question"],
        expected_concepts=list(chosen.get("expected_concepts", [])),
        status="open",
    )
    db.add(session)
    db.flush()
    log_event(
        db,
        user_id=user.id,
        agent="practice",
        action="session_started",
        summary=f"Practice session started on {session.topic}.",
        refs=[make_ref(session)],
    )
    return session


def _bank_entry(session: models.PracticeSession) -> dict:
    for item in question_bank():
        if item["question"] == session.question:
            return item
    return {"topic": session.topic, "question": session.question, "expected_concepts": list(session.expected_concepts or []), "concept_aliases": {}}


def _evaluate_with_model(session: models.PracticeSession, answer: str) -> tuple[dict, str, str | None] | None:
    if not llm_available():
        return None
    try:
        from app.agents.practice_agent import evaluate_practice

        evaluation = evaluate_practice(question=session.question, user_answer=answer, topic=session.topic)
    except Exception:  # noqa: BLE001 - any model failure falls back to the deterministic path
        return None
    rubric = {"correctness": evaluation.correctness, "depth": evaluation.depth, "clarity": evaluation.clarity}
    return rubric, evaluation.feedback, evaluation.weakness_candidate


def evaluate(
    db: Session,
    user: models.User,
    *,
    answer: str,
    session_id: int | None = None,
    question: str | None = None,
    topic: str | None = None,
) -> dict:
    answer = answer.strip()
    if len(answer) < 10:
        raise ValueError("Please write at least 10 characters before submitting.")

    session: models.PracticeSession | None = None
    if session_id is not None:
        session = db.get(models.PracticeSession, session_id)
        if session is None or session.user_id != user.id:
            raise ValueError(f"Practice session {session_id} not found.")
    elif question:
        session = start_session(db, user, topic=topic, question=question)
    else:
        session = db.scalar(
            select(models.PracticeSession)
            .where(models.PracticeSession.user_id == user.id, models.PracticeSession.status == "open")
            .order_by(models.PracticeSession.created_at.desc())
            .limit(1)
        )
        if session is None or (topic and session.topic.lower() != topic.lower()):
            session = start_session(db, user, topic=topic)

    bank_entry = _bank_entry(session)
    matched, missing = matched_concepts(answer, bank_entry)
    model_result = _evaluate_with_model(session, answer)
    weakness_detail: str | None = None
    if model_result is not None:
        rubric, feedback, weakness_detail = model_result
        evaluator = "nemotron"
    else:
        rubric, matched, missing, feedback = deterministic_rubric(answer, bank_entry)
        evaluator = "deterministic"

    score = overall_score(rubric)
    session.answer = answer
    session.rubric_scores = rubric
    session.missing_concepts = missing
    session.score = score
    session.feedback = feedback
    session.status = "evaluated"
    session.evaluator = evaluator
    session.evaluated_at = utcnow()
    db.flush()

    log_event(
        db,
        user_id=user.id,
        agent="practice",
        action="answer_evaluated",
        summary=f"Answer on {session.topic} scored {score}/100 ({evaluator}); missing: {', '.join(missing) or 'nothing'}.",
        refs=[make_ref(session)],
        payload={"rubric": rubric},
    )

    weakness, reason = apply_thresholds(db, user, session)
    detail = weakness_detail or (f"{session.topic}: missing {', '.join(missing[:3])}" if missing else session.topic)
    return {
        "session_id": session.id,
        "ref": make_ref(session),
        "topic": session.topic,
        "question": session.question,
        "answer": answer,
        "score": score,
        "rubric_scores": rubric,
        "matched_concepts": matched,
        "missing_concepts": missing,
        "feedback": feedback,
        "weakness": session.topic,
        "weakness_detail": detail,
        "weakness_recorded": weakness is not None,
        "weakness_ref": make_ref(weakness) if weakness else None,
        "weakness_reason": reason,
        "evaluator": evaluator,
        "submittedAt": session.evaluated_at.isoformat() + "Z",
    }


def serialize_session(session: models.PracticeSession) -> dict:
    return {
        "id": session.id,
        "ref": make_ref(session),
        "topic": session.topic,
        "question": session.question,
        "expected_concepts": list(session.expected_concepts or []),
        "answer": session.answer,
        "rubric_scores": dict(session.rubric_scores or {}),
        "missing_concepts": list(session.missing_concepts or []),
        "score": session.score,
        "feedback": session.feedback,
        "weakness_ref": f"weakness#{session.weakness_id}" if session.weakness_id else None,
        "status": session.status,
        "evaluator": session.evaluator,
        "created_at": session.created_at.isoformat() + "Z",
        "evaluated_at": session.evaluated_at.isoformat() + "Z" if session.evaluated_at else None,
    }
