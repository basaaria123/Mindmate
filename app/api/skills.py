"""Skills with evidence, weaknesses and the gap ranking endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.contracts import EvidenceIn, GapsIn, SkillIn, SkillPatch
from app.api.deps import get_current_user, get_db
from app.db import models
from app.memory import service as memory_service
from app.memory.retrieval import _evidence_dict, _skill_dict, _weakness_dict, active_evidence, active_skills, active_weaknesses
from app.services.memory_writes import add_evidence, add_skill, update_skill
from app.services.opportunity_service import gaps_for, get_opportunity

router = APIRouter(tags=["skills"])


def _get_skill(db: Session, user: models.User, skill_id: int) -> models.Skill:
    skill = db.get(models.Skill, skill_id)
    if skill is None or skill.user_id != user.id or skill.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Skill not found.")
    return skill


@router.get("/skills")
def list_skills(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    return {"skills": [_skill_dict(skill) for skill in active_skills(db, user.id)]}


@router.post("/skills", status_code=201)
def create_skill(body: SkillIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    try:
        skill = add_skill(db, user, **body.model_dump())
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return _skill_dict(skill)


@router.patch("/skills/{skill_id}")
def patch_skill(skill_id: int, body: SkillPatch, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    skill = _get_skill(db, user, skill_id)
    try:
        update_skill(db, skill, level=body.level, confidence=body.confidence)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return _skill_dict(skill)


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    _get_skill(db, user, skill_id)
    item = next((i for i in memory_service.list_items(db, user.id, types={"skill"}) if i.ref_id == f"skill#{skill_id}"), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Skill not found.")
    memory_service.soft_delete_item(db, item)
    db.commit()
    return {"deleted": True, "ref": f"skill#{skill_id}"}


@router.get("/evidence")
def list_evidence(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    return {"evidence": [_evidence_dict(ev) for ev in active_evidence(db, user.id)]}


@router.post("/skills/{skill_id}/evidence", status_code=201)
def create_evidence(skill_id: int, body: EvidenceIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    skill = _get_skill(db, user, skill_id)
    try:
        evidence = add_evidence(db, user, skill, type=body.type, description=body.description, url=body.url)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return _evidence_dict(evidence)


@router.post("/evidence", status_code=201)
def create_evidence_flat(body: EvidenceIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    if body.skill_id is None:
        raise HTTPException(status_code=422, detail="skill_id is required.")
    return create_evidence(body.skill_id, body, db, user)


@router.get("/weaknesses")
def list_weaknesses(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    return {"weaknesses": [_weakness_dict(w) for w in active_weaknesses(db, user.id)]}


@router.post("/skills/gaps")
def skill_gaps(body: GapsIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    opportunity = get_opportunity(db, user, body.opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    result = gaps_for(db, user, opportunity)
    db.commit()
    return result
