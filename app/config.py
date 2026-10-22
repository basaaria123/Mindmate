"""Central backend configuration.

Everything that tunes the deterministic engines (fit score, replan priority,
weakness thresholds) lives here so it can be changed without touching code,
as the proposal requires. Values are read from the environment (a local
``.env`` file is honoured) and fall back to the defaults documented in
``.env.example``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PriorityWeights:
    """Weights for the replan priority formula (section 7 of the proposal)."""

    role_impact: float = 0.40
    weakness_boost: float = 0.25
    goal_hierarchy: float = 0.20
    deadline_urgency: float = 0.15


@dataclass(frozen=True)
class Settings:
    database_url: str
    auto_create_schema: bool
    rate_limit_per_minute: int
    llm_mode: str  # "live" uses Nemotron when a key exists, "off" forces the deterministic path
    admin_token: str | None
    default_daily_minutes: int
    plan_days: int
    weakness_score_threshold: int
    weakness_min_occurrences: int
    weakness_severe_score: int
    hard_deadline_days: int
    priority_weights: PriorityWeights = field(default_factory=PriorityWeights)
    cors_origins: tuple[str, ...] = ()


def get_settings() -> Settings:
    """Read settings from the environment on every call (cheap, test friendly)."""

    default_db = f"sqlite:///{(PROJECT_ROOT / 'data' / 'mindmate.db').as_posix()}"
    cors = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    )

    return Settings(
        # An empty DATABASE_URL (as copied from .env.example) means "use the local SQLite file".
        database_url=(os.getenv("DATABASE_URL") or "").strip() or default_db,
        auto_create_schema=_env_bool("MINDMATE_AUTO_CREATE_SCHEMA", True),
        rate_limit_per_minute=_env_int("RATE_LIMIT_PER_MINUTE", 120),
        llm_mode=os.getenv("MINDMATE_LLM_MODE", "live").strip().lower() or "live",
        admin_token=os.getenv("MINDMATE_ADMIN_TOKEN") or None,
        default_daily_minutes=_env_int("MINDMATE_DEFAULT_DAILY_MINUTES", 60),
        plan_days=_env_int("MINDMATE_PLAN_DAYS", 14),
        weakness_score_threshold=_env_int("WEAKNESS_SCORE_THRESHOLD", 60),
        weakness_min_occurrences=_env_int("WEAKNESS_MIN_OCCURRENCES", 2),
        weakness_severe_score=_env_int("WEAKNESS_SEVERE_SCORE", 35),
        hard_deadline_days=_env_int("MINDMATE_HARD_DEADLINE_DAYS", 3),
        priority_weights=PriorityWeights(
            role_impact=_env_float("PRIORITY_WEIGHT_ROLE_IMPACT", 0.40),
            weakness_boost=_env_float("PRIORITY_WEIGHT_WEAKNESS_BOOST", 0.25),
            goal_hierarchy=_env_float("PRIORITY_WEIGHT_GOAL_HIERARCHY", 0.20),
            deadline_urgency=_env_float("PRIORITY_WEIGHT_DEADLINE_URGENCY", 0.15),
        ),
        cors_origins=cors,
    )


def llm_available() -> bool:
    """True when live Nemotron calls are both configured and enabled."""

    settings = get_settings()
    return settings.llm_mode == "live" and bool(os.getenv("NEBIUS_API_KEY"))


def data_file(env_name: str, default_name: str) -> Path:
    """Path of a demo data file, overridable per environment variable.

    MINDMATE_SEED_PERSONA, MINDMATE_OPPORTUNITIES_FILE and MINDMATE_QUESTION_BANK
    let the product lead swap the demo persona without code changes.
    """

    override = os.getenv(env_name)
    return Path(override) if override else DATA_DIR / default_name
