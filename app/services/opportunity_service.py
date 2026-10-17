"""Opportunities, fit assessments and gap ranking on top of the memory store."""

from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.db import models
from app.memory.refs import filter_valid_refs, make_ref
from app.memory.retrieval import active_skills, active_weaknesses
from app.scoring.fit import (
    RequirementJudgment,
    compute_fit,
    judge_from_skills,
    judgments_from_ai_assessment,
    normalize_weight,
    skill_matches,
)
from app.scoring.gaps import rank_gaps
from app.services.events import log_event


@lru_cache(maxsize=1)
def curated_opportunities() -> list[dict]:
    with (DATA_DIR / "opportunities.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)["opportunities"]


def normalise_requirements(data: dict) -> list[dict]:
    """Accept both the backend shape and the Opportunity Agent's OpportunitySpec."""

    if "required_skills" in data and isinstance(data["required_skills"], list):
        requirements = [
            {
                "name": item.get("skill_name") or item.get("name"),
                "weight": normalize_weight(item.get("importance") or item.get("weight")),
                "mandatory": bool(item.get("is_mandatory", item.get("mandatory", False))),
                "description": item.get("description", ""),
            }
            for item in data["required_skills"]
            if item.get("skill_name") or item.get("name")
        ]
        for extra in data.get("preferred_skills", []) or []:
            if isinstance(extra, str) and extra.strip():
                requirements.append({"name": extra.strip(), "weight": "Low", "mandatory": False, "description": "Preferred skill"})
        return requirements
    requirements = []
    for item in data.get("requirements", []) or []:
        if isinstance(item, str):
            requirements.append({"name": item, "weight": "Medium", "mandatory": False, "description": ""})
        elif item.get("name") or item.get("skill_name"):
            requirements.append(
                {
                    "name": item.get("name") or item.get("skill_name"),
                    "weight": normalize_weight(item.get("weight") or item.get("importance")),
                    "mandatory": bool(item.get("mandatory", item.get("is_mandatory", False))),
                    "description": item.get("description", ""),
                }
            )
    return requirements


def store_opportunity(db: Session, user: models.User | None, data: dict, *, source: str = "user", agent: str = "opportunity") -> models.Opportunity:
    title = data.get("title") or data.get("opportunity_title")
    if not title:
        raise ValueError("An opportunity needs a title.")
    requirements = normalise_requirements(data)
    if not requirements:
        raise ValueError("An opportunity needs at least one requirement.")
    deadline = data.get("deadline")
    if isinstance(deadline, str) and deadline:
        deadline = date.fromisoformat(deadline)
    elif not isinstance(deadline, date):
        deadline = None
    if deadline is None and data.get("deadline_in_days") is not None:
        deadline = date.today() + timedelta(days=int(data["deadline_in_days"]))
    opportunity = models.Opportunity(
        user_id=user.id if user else None,
        title=str(title).strip(),
        org=data.get("org") or data.get("organization"),
        deadline=deadline,
        type=str(data.get("type") or data.get("opportunity_type") or "internship").lower(),
        requirements=requirements,
        url=data.get("url"),
        summary=data.get("summary"),
        source=source,
    )
    db.add(opportunity)
    db.flush()
    log_event(
        db,
        user_id=user.id if user else None,
        agent=agent,
        action="opportunity_stored",
        summary=f"Stored opportunity '{opportunity.title}' with {len(requirements)} requirement(s).",
        refs=[make_ref(opportunity)],
    )
    return opportunity


def list_opportunities(db: Session, user: models.User) -> list[models.Opportunity]:
    query = (
        select(models.Opportunity)
        .where(models.Opportunity.deleted_at.is_(None))
        .where((models.Opportunity.user_id == user.id) | (models.Opportunity.user_id.is_(None)))
        .order_by(models.Opportunity.deadline.is_(None), models.Opportunity.deadline, models.Opportunity.id)
    )
    return list(db.scalars(query))


def get_opportunity(db: Session, user: models.User, opportunity_id: int) -> models.Opportunity | None:
    opportunity = db.get(models.Opportunity, opportunity_id)
    if opportunity is None or opportunity.deleted_at is not None:
        return None
    if opportunity.user_id not in (None, user.id):
        return None
    return opportunity


def search_opportunities(db: Session, user: models.User, query: str, *, limit: int = 12) -> list[tuple[models.Opportunity, float]]:
    """Rank the stored set by token overlap with the query (no live search is claimed)."""

    terms = {t for t in query.lower().replace(",", " ").split() if len(t) > 2}
    results: list[tuple[models.Opportunity, float]] = []
    for opportunity in list_opportunities(db, user):
        haystack = " ".join(
            [opportunity.title, opportunity.org or "", opportunity.summary or "", opportunity.type]
            + [r.get("name", "") for r in opportunity.requirements]
        ).lower()
        score = sum(1.0 for term in terms if term in haystack)
        for requirement in opportunity.requirements:
            if any(skill_matches(term, requirement.get("name", "")) for term in terms):
                score += 0.5
        if not terms or score > 0:
            results.append((opportunity, score))
    results.sort(key=lambda item: (-item[1], item[0].deadline or date.max, item[0].id))
    return results[:limit]


def serialize_opportunity(opportunity: models.Opportunity, latest_fit: models.FitAssessment | None = None) -> dict:
    data = {
        "id": opportunity.id,
        "ref": make_ref(opportunity),
        "title": opportunity.title,
        "org": opportunity.org,
        "deadline": opportunity.deadline.isoformat() if opportunity.deadline else None,
        "type": opportunity.type,
        "requirements": list(opportunity.requirements or []),
        "url": opportunity.url,
        "summary": opportunity.summary,
        "source": opportunity.source,
    }
    if latest_fit is not None:
        data["fit"] = {"score": latest_fit.score, "band": latest_fit.band, "top_gap": latest_fit.top_gap, "id": latest_fit.id}
    return data


def skill_dicts(db: Session, user: models.User) -> list[dict]:
    return [
        {
            "name": skill.name,
            "level": skill.level,
            "ref": make_ref(skill),
            "evidence_refs": [make_ref(ev) for ev in skill.evidence if ev.deleted_at is None],
        }
        for skill in active_skills(db, user.id)
    ]


def latest_fit(db: Session, user: models.User, opportunity_id: int) -> models.FitAssessment | None:
    return db.scalar(
        select(models.FitAssessment)
        .where(models.FitAssessment.user_id == user.id, models.FitAssessment.opportunity_id == opportunity_id)
        .order_by(models.FitAssessment.created_at.desc(), models.FitAssessment.id.desc())
        .limit(1)
    )


def assess_fit(
    db: Session,
    user: models.User,
    opportunity: models.Opportunity,
    *,
    judgments: list[dict] | None = None,
    ai_assessment: dict | None = None,
) -> models.FitAssessment:
    """Compute and store a fit assessment.

    ``judgments`` (from a model or a test) are validated: every cited evidence
    reference must exist and be undeleted, otherwise the request is rejected.
    Without judgements the deterministic judge reads the skill store.
    """

    skills = skill_dicts(db, user)
    if judgments:
        parsed = [RequirementJudgment.from_dict(item) for item in judgments]
        judged_by = "model"
        checked: list[RequirementJudgment] = []
        for judgment in parsed:
            valid, invalid = filter_valid_refs(db, list(judgment.evidence_refs))
            if invalid:
                raise ValueError(f"Requirement {judgment.requirement!r} cites unknown evidence: {invalid}")
            checked.append(RequirementJudgment(judgment.requirement, judgment.weight, judgment.coverage, tuple(valid), judgment.mandatory, judgment.explanation))
        parsed = checked
    elif ai_assessment:
        parsed = judgments_from_ai_assessment(ai_assessment, opportunity.requirements, skills)
        judged_by = "fit_agent"
    else:
        parsed = judge_from_skills(opportunity.requirements, skills)
        judged_by = "deterministic"

    result = compute_fit(parsed)
    assessment = models.FitAssessment(
        user_id=user.id,
        opportunity_id=opportunity.id,
        score=result.score,
        band=result.band,
        per_requirement=[item.as_dict() for item in result.per_requirement],
        top_gap=result.top_gap,
        refs=list(result.refs),
        judged_by=judged_by,
    )
    db.add(assessment)
    db.flush()
    log_event(
        db,
        user_id=user.id,
        agent="fit",
        action="fit_assessed",
        summary=f"Fit for '{opportunity.title}': {result.score}% ({result.band}); top gap: {result.top_gap or 'none'} [{judged_by}].",
        refs=[make_ref(assessment), make_ref(opportunity)] + list(result.refs),
    )
    return assessment


def serialize_fit(assessment: models.FitAssessment, opportunity: models.Opportunity | None = None) -> dict:
    return {
        "id": assessment.id,
        "ref": make_ref(assessment),
        "opportunity_id": assessment.opportunity_id,
        "opportunity_title": opportunity.title if opportunity else None,
        "score": assessment.score,
        "band": assessment.band,
        "per_requirement": list(assessment.per_requirement or []),
        "top_gap": assessment.top_gap,
        "refs": list(assessment.refs or []),
        "judged_by": assessment.judged_by,
        "created_at": assessment.created_at.isoformat() + "Z",
    }


def gaps_for(db: Session, user: models.User, opportunity: models.Opportunity) -> dict:
    assessment = latest_fit(db, user, opportunity.id) or assess_fit(db, user, opportunity)
    from app.scoring.fit import FitResult, RequirementScore

    per_requirement = tuple(
        RequirementScore(
            requirement=item["requirement"],
            weight=item["weight"],
            weight_value=item["weight_value"],
            coverage=item["coverage"],
            coverage_value=item["coverage_value"],
            contribution=item["contribution"],
            gap=item["gap"],
            mandatory=item["mandatory"],
            evidence_refs=tuple(item.get("evidence_refs", [])),
            explanation=item.get("explanation", ""),
        )
        for item in assessment.per_requirement
    )
    fit = FitResult(score=assessment.score, band=assessment.band, per_requirement=per_requirement, top_gap=assessment.top_gap, refs=tuple(assessment.refs or []))
    weaknesses = [{"topic": w.topic, "severity": w.severity, "ref": make_ref(w)} for w in active_weaknesses(db, user.id)]
    gaps = rank_gaps(fit, weaknesses)
    log_event(
        db,
        user_id=user.id,
        agent="skill_gap",
        action="gaps_ranked",
        summary=f"Ranked {len(gaps)} gap(s) for '{opportunity.title}'; highest impact: {gaps[0].requirement if gaps else 'none'}.",
        refs=[make_ref(opportunity), make_ref(assessment)] + [ref for gap in gaps for ref in gap.refs],
    )
    return {
        "opportunity": serialize_opportunity(opportunity, assessment),
        "fit": {"id": assessment.id, "score": assessment.score, "band": assessment.band},
        "gaps": [gap.as_dict() for gap in gaps],
    }
