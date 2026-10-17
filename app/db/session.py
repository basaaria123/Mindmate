"""SQLAlchemy engine and session management.

PostgreSQL is the production store (``DATABASE_URL=postgresql+psycopg://...``).
SQLite is used automatically for local development and tests so the backend
runs without any external service.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

_engine: Engine | None = None
_engine_url: str | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if ":memory:" in url or url.endswith("sqlite://"):
            engine = create_engine(
                url,
                connect_args=connect_args,
                poolclass=StaticPool,
                future=True,
            )
        else:
            engine = create_engine(url, connect_args=connect_args, future=True)

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover - driver hook
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(url, pool_pre_ping=True, future=True)


def get_engine() -> Engine:
    """Return the engine for the configured DATABASE_URL, creating it lazily."""

    global _engine, _engine_url, _SessionLocal

    url = get_settings().database_url
    if _engine is None or _engine_url != url:
        if _engine is not None:
            _engine.dispose()
        _engine = _build_engine(url)
        _engine_url = url
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def reset_engine() -> None:
    """Drop the cached engine (used by tests that switch DATABASE_URL)."""

    global _engine, _engine_url, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _engine_url = None
    _SessionLocal = None


def init_db(create: bool | None = None) -> None:
    """Create tables when auto-create is enabled (dev/test); Alembic owns production."""

    from app.db.models import Base  # local import avoids circular import at module load

    should_create = get_settings().auto_create_schema if create is None else create
    if should_create:
        Base.metadata.create_all(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a session and always closes it."""

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
