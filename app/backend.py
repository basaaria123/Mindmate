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
from app.demo_cache import DemoCacheMiddleware
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


EXPOSED_HEADERS = ["X-MindMate-Source", "X-MindMate-Cache"]


def _extend_cors(app: FastAPI) -> None:
    """Add the deployed frontend's origins from CORS_ORIGINS (exact, comma-separated) and
    CORS_ORIGIN_REGEX (optional, e.g. for Vercel preview URLs). There is no wildcard default."""

    import os

    extra = get_settings().cors_origins
    origin_regex = os.getenv("CORS_ORIGIN_REGEX", "").strip()
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            if origin_regex:
                middleware.kwargs["allow_origin_regex"] = origin_regex
            # Let the browser read which engine answered (Nemotron, offline analysis, recording).
            exposed = list(middleware.kwargs.get("expose_headers", []))
            middleware.kwargs["expose_headers"] = exposed + [h for h in EXPOSED_HEADERS if h not in exposed]
            if not extra:
                continue
            current = list(middleware.kwargs.get("allow_origins", []))
            middleware.kwargs["allow_origins"] = current + [origin for origin in extra if origin not in current]


def _startup() -> None:
    init_db()
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


def _readiness() -> JSONResponse:
    """Readiness for hosting platforms: the database answers and settings are loaded."""

    from sqlalchemy import text

    from app.config import llm_available
    from app.demo_cache import cache_mode

    checks = {"database": "ok"}
    status = 200
    try:
        session = get_session_factory()()
        try:
            session.execute(text("SELECT 1"))
        finally:
            session.close()
    except Exception as error:  # noqa: BLE001 - report any database failure as not ready
        checks["database"] = f"error: {type(error).__name__}"
        status = 503
    checks.update({"llm_available": llm_available(), "demo_cache": cache_mode()})
    return JSONResponse({"status": "ready" if status == 200 else "not_ready", "checks": checks}, status_code=status)


def register_backend(app: FastAPI) -> FastAPI:
    app.add_api_route("/health/ready", _readiness, methods=["GET"], tags=["health"])
    for router in ROUTERS:
        app.include_router(router)
    app.add_exception_handler(ValueError, _value_error_handler)
    app.add_exception_handler(InvalidReference, _value_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_middleware(DemoCacheMiddleware)
    app.add_middleware(RateLimitMiddleware)
    _extend_cors(app)
    # CORS must be the outermost middleware: responses built by the demo cache or the
    # rate limiter would otherwise lack CORS headers and the browser would discard them.
    app.user_middleware.sort(key=lambda middleware: middleware.cls is not CORSMiddleware)

    existing_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        _startup()
        async with existing_lifespan(application) as state:
            yield state

    app.router.lifespan_context = lifespan
    return app
