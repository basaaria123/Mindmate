"""Turn practice results into weakness memory, using thresholds not single answers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import models
from app.db.models import utcnow
from app.memory.refs import make_ref
from app.memory.service import record_entity
from app.scoring.fit import skill_matches
from app.scoring.weakness import decide_weakness
from app.services.events import log_event


def find_active_weakness(db: Session, user_id: int, topic: str) -> models.Weakness | None:
    for weakness in db.scalars(
        select(models.Weakness).where(
            models.Weakness.user_id == user_id,
            models.Weakness.status == "active",
            models.Weakness.deleted_at.is_(None),
        )
    ):
        if skill_matches(topic, weakness.topic):
            return weakness
    return None


def low_scores_for_topic(db: Session, user_id: int, topic: str, threshold: int) -> list[models.PracticeSession]:
    sessions = db.scalars(
        select(models.PracticeSession)
        .where(
            models.PracticeSession.user_id == user_id,
            models.PracticeSession.status == "evaluated",
            models.PracticeSession.score.is_not(None),
        )
        .order_by(models.PracticeSession.evaluated_at, models.PracticeSession.id)
    )
    return [s for s in sessions if s.score is not None and s.score < threshold and skill_matches(topic, s.topic)]


def apply_thresholds(db: Session, user: models.User, session: models.PracticeSession) -> tuple[models.Weakness | None, str]:
    """Create or update a weakness for the session's topic if thresholds are met."""

    settings = get_settings()
    low_sessions = low_scores_for_topic(db, user.id, session.topic, settings.weakness_score_threshold)
    decision = decide_weakness(
        [s.score for s in low_sessions if s.score is not None],
        score_threshold=settings.weakness_score_threshold,
        min_occurrences=settings.weakness_min_occurrences,
        severe_score=settings.weakness_severe_score,
    )
    if not decision.should_record:
        return None, decision.reason

    refs = [make_ref(s) for s in low_sessions]
    weakness = find_active_weakness(db, user.id, session.topic)
    created = weakness is None
    if weakness is None:
        weakness = models.Weakness(
            user_id=user.id,
            topic=session.topic,
            severity=decision.severity,
            evidence_count=decision.evidence_count,
            last_seen=utcnow(),
            refs=refs,
        )
        db.add(weakness)
        db.flush()
    else:
        weakness.severity = decision.severity
        weakness.evidence_count = decision.evidence_count
        weakness.last_seen = utcnow()
        weakness.refs = refs
        db.flush()

    session.weakness_id = weakness.id
    record_entity(db, weakness, source="practice", tags=["practice", session.topic])
    log_event(
        db,
        user_id=user.id,
        agent="memory",
        action="weakness_recorded" if created else "weakness_updated",
        summary=(
            f"{'Recorded' if created else 'Updated'} weakness '{weakness.topic}' "
            f"({weakness.severity}): {decision.reason}"
        ),
        refs=[make_ref(weakness)] + refs,
    )
    return weakness, decision.reason


def record_user_weakness(db: Session, user: models.User, topic: str, *, source: str = "user", severity: str = "medium") -> models.Weakness:
    """A weakness the user saves explicitly (for example from the Memory screen)."""

    weakness = find_active_weakness(db, user.id, topic)
    created = weakness is None
    if weakness is None:
        weakness = models.Weakness(user_id=user.id, topic=topic.strip(), severity=severity, evidence_count=1, last_seen=utcnow(), refs=[])
        db.add(weakness)
        db.flush()
    else:
        weakness.last_seen = utcnow()
    # attach any evaluated sessions on the topic as evidence
    settings = get_settings()
    low_sessions = low_scores_for_topic(db, user.id, weakness.topic, settings.weakness_score_threshold)
    if low_sessions:
        weakness.refs = [make_ref(s) for s in low_sessions]
        weakness.evidence_count = max(weakness.evidence_count, len(low_sessions))
    record_entity(db, weakness, source=source, tags=["weakness"])
    log_event(
        db,
        user_id=user.id,
        agent="memory",
        action="weakness_recorded" if created else "weakness_updated",
        summary=f"User saved weakness '{weakness.topic}' to memory.",
        refs=[make_ref(weakness)] + list(weakness.refs or []),
    )
    return weakness
