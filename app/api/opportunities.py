"""Opportunities: curated set, search over it, and deterministic fit."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.contracts import FitIn, OpportunityExtractIn, OpportunityIn, OpportunitySearchIn
from app.api.deps import get_current_user, get_db
from app.db import models
from app.services.opportunity_service import (
    assess_fit,
    extract_and_store,
    get_opportunity,
    latest_fit,
    list_opportunities,
    search_opportunities,
    serialize_fit,
    serialize_opportunity,
    store_opportunity,
)

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
def read_opportunities(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    items = [serialize_opportunity(o, latest_fit(db, user, o.id)) for o in list_opportunities(db, user)]
    return {"total": len(items), "opportunities": items}


@router.post("/opportunities", status_code=201)
def create_opportunity(body: OpportunityIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    data = body.model_dump(exclude_none=True)
    data.update(body.model_extra or {})
    try:
        opportunity = store_opportunity(db, user, data)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return serialize_opportunity(opportunity)


@router.post("/opportunities/extract", status_code=201)
def extract(body: OpportunityExtractIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    """Paste a posting: the Opportunity agent extracts requirements (keyword fallback offline) and it is stored."""

    try:
        opportunity, extractor = extract_and_store(db, user, body.text)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return {**serialize_opportunity(opportunity), "extracted_by": extractor}


@router.post("/opportunities/search")
def search(body: OpportunitySearchIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    results = search_opportunities(db, user, body.query, limit=body.limit)
    return {
        "query": body.query,
        "source": "curated",  # live search (Tavily) is P1 and not claimed here
        "results": [{**serialize_opportunity(o, latest_fit(db, user, o.id)), "relevance": score} for o, score in results],
    }


@router.get("/opportunities/{opportunity_id}")
def read_opportunity(opportunity_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    opportunity = get_opportunity(db, user, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    fit = latest_fit(db, user, opportunity.id)
    return {**serialize_opportunity(opportunity, fit), "latest_fit": serialize_fit(fit, opportunity) if fit else None}


@router.post("/opportunities/{opportunity_id}/fit")
def fit(opportunity_id: int, body: FitIn | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)) -> dict:
    opportunity = get_opportunity(db, user, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    body = body or FitIn()
    try:
        assessment = assess_fit(db, user, opportunity, judgments=body.judgments, ai_assessment=body.ai_assessment, use_model=body.use_model)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return serialize_fit(assessment, opportunity)
