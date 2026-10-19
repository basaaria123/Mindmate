"""AI endpoints without a key: offline analysis with the agents' schemas, clearly marked."""

from app.schemas.profile import UserProfile
from app.services import offline_ai

POSTING = (
    "We are looking for a motivated Junior AI/ML Engineer to join our team in Hyderabad, India. "
    "The ideal candidate should have 0-2 years of experience and knowledge of Python, machine learning, "
    "Pandas, NumPy, scikit-learn, SQL, REST APIs, JSON, and Git. Familiarity with PyTorch, TensorFlow, "
    "large language models, AI agents, Docker, and cloud platforms is an added advantage."
)


def test_posting_extraction_separates_required_and_preferred():
    spec = offline_ai.opportunity_from_text(POSTING)
    assert spec.opportunity_title == "Junior AI/ML Engineer"
    assert spec.opportunity_type == "job"
    assert spec.experience_level == "0-2 years"
    required = {r.skill_name for r in spec.required_skills if r.is_mandatory}
    assert required == {"Python", "Machine learning", "Pandas", "NumPy", "scikit-learn", "SQL", "REST APIs", "JSON", "Git"}
    assert spec.preferred_skills == ["PyTorch", "TensorFlow", "Large language models", "AI agents", "Docker", "Cloud"]
    assert all(r.importance == "Low" for r in spec.required_skills if r.skill_name in spec.preferred_skills)


def test_profile_extraction_keeps_interests_out_of_skills():
    profile = offline_ai.profile_from_text(
        "I am a final-year B.Tech student. I know Python and SQL. I want to become an ML engineer. "
        "I am interested in NLP and computer vision. I can spend 2 hours a day and like hands-on projects."
    )
    assert profile.skills == ["Python", "SQL"]
    assert profile.interests == ["NLP", "computer vision"]
    assert profile.daily_available_minutes == 120
    assert profile.goals == ["I want to become an ML engineer."]
    assert profile.learning_preferences == ["Hands-on projects"]


def test_fit_uses_the_requirement_weights():
    spec = offline_ai.opportunity_from_text("Data Intern\nPython and SQL are required. Tableau is a plus.")
    profile = UserProfile(education="BSc", goals=[], skills=["Python", "Tableau"], interests=[], learning_preferences=[])
    fit = offline_ai.fit_for(profile, spec)
    # Python High (3) + Tableau Low (1) covered out of 3 + 3 + 1
    assert "57%" in fit.summary and fit.overall_fit == "Moderate"
    assert [m.skill_name for m in fit.missing_skills] == ["SQL"]
    gaps = offline_ai.gaps_for(profile, spec, fit)
    assert [g.skill_name for g in gaps.gaps] == ["SQL"] and gaps.gaps[0].career_impact_score == 100


def test_endpoints_answer_offline_with_agent_schemas(client):
    profile = client.post("/profile", json={"user_message": "I know Python and Git."})
    opportunity = client.post("/opportunity", json={"opportunity_text": POSTING})
    fit = client.post("/fit", json={"user_profile": profile.json(), "opportunity": opportunity.json()})
    gap = client.post("/gap", json={"user_profile": profile.json(), "opportunity": opportunity.json(),
                                    "fit_assessment": fit.json()})
    suggestions = client.post("/suggestions", json={"user_profile": profile.json()})
    for response in (profile, opportunity, fit, gap, suggestions):
        assert response.status_code == 200
        assert response.headers["X-MindMate-Source"] == "offline"
    assert fit.json()["summary"].startswith("Offline estimate")
    categories = [s["category"] for s in suggestions.json()["suggestions"]]
    assert {c: categories.count(c) for c in set(categories)} == {"Jobs": 3, "Projects": 3, "Resources": 3, "Other": 3}


def test_live_agent_is_used_when_available_and_failure_falls_back(client, monkeypatch):
    from app.schemas.profile import UserProfile as Schema

    monkeypatch.setattr("app.services.agent_bridge.llm_available", lambda: True)
    monkeypatch.setattr("main.extract_user_profile", lambda message: Schema(
        education="from model", goals=[], skills=[], interests=[], learning_preferences=[]))
    live = client.post("/profile", json={"user_message": "I know Python."})
    assert live.headers["X-MindMate-Source"] == "nemotron" and live.json()["education"] == "from model"

    def broken(message):
        raise ValueError("invalid JSON after retry")

    monkeypatch.setattr("main.extract_user_profile", broken)
    fallback = client.post("/profile", json={"user_message": "I know Python."})
    assert fallback.status_code == 200 and fallback.headers["X-MindMate-Source"] == "offline"
    assert fallback.json()["skills"] == ["Python"]
    events = client.get("/agent/events?agent=profile").json()["events"]
    assert any(e["action"] == "model_fallback" for e in events)


def test_browser_can_read_the_source_header(client):
    response = client.post("/opportunity", json={"opportunity_text": POSTING}, headers={"Origin": "http://localhost:5173"})
    exposed = response.headers.get("access-control-expose-headers", "")
    assert "X-MindMate-Source" in exposed


def test_browser_offline_analysis_uses_the_same_vocabulary_and_hints():
    """Mock mode runs mindmate-frontend/src/services/offlineAnalysis.ts; it must not drift from offline_ai.py."""

    import re
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "mindmate-frontend/src/services/offlineAnalysis.ts").read_text()

    def ts_list(name: str) -> list[str]:
        body = re.search(rf"export const {name} = \[(.*?)\]", source, re.DOTALL).group(1)
        return re.findall(r"'([^']*)'", body)

    assert ts_list("BASE_SKILLS") == offline_ai.BASE_SKILLS
    assert tuple(ts_list("MANDATORY_HINTS")) == offline_ai.MANDATORY_HINTS
    assert tuple(ts_list("PREFERRED_HINTS")) == offline_ai.PREFERRED_HINTS


def test_organization_stays_on_its_line():
    spec = offline_ai.opportunity_from_text("ML Intern at Acme\nMust know Python.")
    assert spec.organization == "Acme" and spec.opportunity_title == "ML Intern at Acme"
