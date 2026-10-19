"""Demo fallback for the AI endpoints: shipped defaults match the AI schemas, and each mode behaves."""

import json
from pathlib import Path

import pytest

from app.demo_cache import AI_ENDPOINTS

CACHE = Path(__file__).resolve().parents[1] / "data" / "demo_cache"


def _default(name):
    return json.loads((CACHE / f"{name}.json").read_text())["default"]


def test_shipped_defaults_validate_against_ai_schemas():
    from app.schemas.fit import FitAssessment
    from app.schemas.gap import GapVectorJSON
    from app.schemas.opportunity import OpportunitySpec
    from app.schemas.plan import PlanScheduleJSON
    from app.schemas.practice import PracticeEvaluation
    from app.schemas.profile import UserProfile
    from app.schemas.suggestions import SuggestionsResponse

    UserProfile.model_validate(_default("profile"))
    OpportunitySpec.model_validate(_default("opportunity"))
    FitAssessment.model_validate(_default("fit"))
    GapVectorJSON.model_validate(_default("gap"))
    PlanScheduleJSON.model_validate(_default("plan"))
    SuggestionsResponse.model_validate(_default("suggestions"))
    PracticeEvaluation.model_validate({k: v for k, v in _default("practice").items() if k != "memory_saved"})
    assert set(AI_ENDPOINTS.values()) == {p.stem for p in CACHE.glob("*.json")}


def test_off_mode_answers_offline_without_key(client, monkeypatch):
    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    monkeypatch.setenv("MINDMATE_DEMO_CACHE", "off")
    response = client.post("/profile", json={"user_message": "I am a student. I know Python and SQL."})
    assert response.status_code == 200
    assert response.headers["X-MindMate-Source"] == "offline"
    assert "X-MindMate-Cache" not in response.headers
    assert response.json()["skills"] == ["Python", "SQL"]


def test_fallback_serves_exact_recording_else_offline_analysis(client, monkeypatch, tmp_path):
    from app.demo_cache import request_key

    monkeypatch.setenv("MINDMATE_DEMO_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("MINDMATE_DEMO_CACHE", "fallback")
    recorded = json.loads((CACHE / "opportunity.json").read_text())["default"]
    demo_body = {"opportunity_text": "AI intern, Python required"}
    (tmp_path / "opportunity.json").write_text(json.dumps({
        "entries": {request_key(json.dumps(demo_body).encode()): recorded}, "default": recorded}))

    response = client.post("/opportunity", json=demo_body)
    assert response.status_code == 200
    assert response.headers["X-MindMate-Cache"] == "fallback"
    assert response.json()["opportunity_title"] == "AI/ML Engineering Intern"
    events = client.get("/agent/events?agent=opportunity").json()["events"]
    assert any(e["action"] == "demo_cache_fallback" for e in events)

    # Any other posting is analysed offline instead of answered with another posting's recording.
    other = client.post("/opportunity", json={"opportunity_text": "Data Analyst Intern\nSQL and Excel required."})
    assert other.headers["X-MindMate-Source"] == "offline" and "X-MindMate-Cache" not in other.headers
    assert other.json()["opportunity_title"] == "Data Analyst Intern"
    assert [r["skill_name"] for r in other.json()["required_skills"]] == ["SQL", "Excel"]


def test_fallback_does_not_hide_request_validation_errors(client, monkeypatch):
    monkeypatch.setenv("MINDMATE_DEMO_CACHE", "fallback")
    response = client.post("/opportunity", json={})
    assert response.status_code == 422 and "X-MindMate-Cache" not in response.headers


def test_replay_never_calls_the_model(client, monkeypatch):
    def must_not_run(*args, **kwargs):
        raise AssertionError("model called in replay mode")

    monkeypatch.setattr("main.extract_user_profile", must_not_run)
    monkeypatch.setenv("MINDMATE_DEMO_CACHE", "replay")
    response = client.post("/profile", json={"user_message": "anything"})
    assert response.status_code == 200 and response.headers["X-MindMate-Cache"] == "replay"
    assert response.json()["daily_available_minutes"] == 60
    # the stored-profile endpoints are untouched by the cache
    assert "X-MindMate-Cache" not in client.get("/profile").headers


def test_record_then_replay_exact_request(client, monkeypatch, tmp_path):
    from app.schemas.profile import UserProfile

    monkeypatch.setenv("MINDMATE_DEMO_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.agent_bridge.llm_available", lambda: True)
    monkeypatch.setattr("main.extract_user_profile", lambda message: UserProfile(
        education=f"echo:{message}", goals=[], skills=[], interests=[], daily_available_minutes=30, learning_preferences=[]))
    monkeypatch.setenv("MINDMATE_DEMO_CACHE", "record")
    first = client.post("/profile", json={"user_message": "first"})
    client.post("/profile", json={"user_message": "second"})
    assert first.headers["X-MindMate-Cache"] == "recorded"
    assert len(json.loads((tmp_path / "profile.json").read_text())["entries"]) == 2

    monkeypatch.setattr("main.extract_user_profile", lambda message: pytest.fail("model called"))
    monkeypatch.setenv("MINDMATE_DEMO_CACHE", "replay")
    assert client.post("/profile", json={"user_message": "first"}).json()["education"] == "echo:first"
    assert client.post("/profile", json={"user_message": "unseen"}).json()["education"] == "echo:second"  # latest = default


def test_cached_and_rate_limited_responses_keep_cors_headers(client, monkeypatch):
    """Browsers discard responses without CORS headers; middleware-built responses must carry them."""

    from app.rate_limit import limiter

    origin = {"Origin": "http://localhost:5173"}
    monkeypatch.setenv("MINDMATE_DEMO_CACHE", "replay")
    replayed = client.post("/opportunity", json={"opportunity_text": "x"}, headers=origin)
    assert replayed.headers["X-MindMate-Cache"] == "replay"
    assert replayed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    limiter.reset()
    client.get("/profile", headers=origin)
    limited = client.get("/profile", headers=origin)
    assert limited.status_code == 429
    assert limited.headers.get("access-control-allow-origin") == "http://localhost:5173"
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "0")
