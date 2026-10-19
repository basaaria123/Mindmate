"""Shared fixtures: each test gets a fresh SQLite database and a seeded app."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.db import get_session_factory, init_db, models, reset_engine
from app.rate_limit import limiter
from app.services.seed import reset_demo


# Set MINDMATE_TEST_DATABASE_URL (for example a PostgreSQL URL) to run the suite
# against that database; every test starts from freshly created tables.
TEST_DATABASE_URL = os.getenv("MINDMATE_TEST_DATABASE_URL")


@pytest.fixture()
def db_env(tmp_path, monkeypatch):
    if TEST_DATABASE_URL:
        monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    else:
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "0")
    monkeypatch.setenv("MINDMATE_LLM_MODE", "off")
    monkeypatch.setenv("MINDMATE_AUTO_CREATE_SCHEMA", "true")
    monkeypatch.setenv("MINDMATE_AUTO_SEED", "false")
    monkeypatch.delenv("MINDMATE_ADMIN_TOKEN", raising=False)
    reset_engine()
    limiter.reset()
    if TEST_DATABASE_URL:
        from app.db import get_engine

        models.Base.metadata.drop_all(bind=get_engine())
    init_db(True)
    yield
    reset_engine()


@pytest.fixture()
def db(db_env):
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded(db):
    reset_demo(db)
    return db


@pytest.fixture()
def user(seeded):
    return seeded.get(models.User, 1)


@pytest.fixture()
def client(db_env):
    import main

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture()
def seeded_client(client):
    response = client.post("/admin/reset-demo")
    assert response.status_code == 200, response.text
    return client


def is_sorted_desc(values):
    return all(a >= b for a, b in zip(values, values[1:]))
