"""The Alembic migration chain produces exactly the SQLAlchemy models' schema."""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

from app.db.models import Base

ROOT = Path(__file__).resolve().parents[1]


def test_migrations_match_models(tmp_path, monkeypatch):
    import os

    url = os.getenv("MINDMATE_TEST_DATABASE_URL") or f"sqlite:///{(tmp_path / 'migrated.db').as_posix()}"
    if url.startswith("postgresql"):
        engine = create_engine(url)
        Base.metadata.drop_all(bind=engine)
        with engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
        engine.dispose()
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    command.upgrade(config, "head")

    engine = create_engine(url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True, "render_as_batch": True})
        diff = compare_metadata(context, Base.metadata)
    assert diff == []
    command.downgrade(config, "base")
