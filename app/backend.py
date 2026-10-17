"""Wires the Backend & Memory layer into the existing FastAPI app.

``main.py`` keeps the agent endpoints owned by the AI role; this function
adds the memory, goal, plan, practice, trace and admin routes, the error
handlers, the rate limiter and the database start-up.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api import actions, admin, events, goals, memory, opportunities, plans, practice, profile, skills
from app.config import get_settings
from app.db import get_session_factory, init_db, models
from app.memory.refs import InvalidReference
from app.rate_limit import RateLimitMiddleware

ROUTERS = (
    profile.router,
    memory.router,
    goals.router,
    skills.router,
    opportunities.router,
    plans.router,
    practice.router,
    events.router,
    actions.router,
    admin.router,
)


def _extend_cors(app: FastAPI) -> None:
    extra = get_settings().cors_origins
    if not extra:
        return
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            current = list(middleware.kwargs.get("allow_origins", []))
            middleware.kwargs["allow_origins"] = current + [origin for origin in extra if origin not in current]


def _startup() -> None:
    init_db()
    if not get_settings().auto_create_schema:
        return
    import os

    if os.getenv("MINDMATE_AUTO_SEED", "true").strip().lower() in {"1", "true", "yes", "on"}:
        session = get_session_factory()()
        try:
            if session.scalar(select(models.User).limit(1)) is None:
                from app.services.seed import seed

                seed(session)
        finally:
            session.close()


async def _value_error_handler(_: Request, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(error)})


async def _validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    first = error.errors()[0] if error.errors() else {}
    location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    message = first.get("msg", "Invalid request.")
    return JSONResponse(
        status_code=422,
        content={"detail": f"{location}: {message}" if location else message, "errors": error.errors()},
    )


def register_backend(app: FastAPI) -> FastAPI:
    for router in ROUTERS:
        app.include_router(router)
    app.add_exception_handler(ValueError, _value_error_handler)
    app.add_exception_handler(InvalidReference, _value_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_middleware(RateLimitMiddleware)
    _extend_cors(app)

    existing_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        _startup()
        async with existing_lifespan(application) as state:
            yield state

    app.router.lifespan_context = lifespan
    return app
