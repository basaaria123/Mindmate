"""Backend <-> AI agent orchestration, with the agents replaced by fakes (no key or network)."""

import pytest

import app.services.agent_bridge as bridge
from app.schemas.fit import FitAssessment, SkillMatch
from app.schemas.opportunity import OpportunityRequirement, OpportunitySpec
from app.schemas.plan import PlanScheduleJSON, TaskItem


@pytest.fixture()
def live(monkeypatch):
    monkeypatch.setattr(bridge, "llm_available", lambda: True)


def _events(client, action):
    return [e for e in client.get("/agent/events?limit=200").json()["events"] if e["action"] == action]


def test_planner_agent_gets_database_memory_and_plan_is_stored(seeded_client, live, monkeypatch):
    seen = {}

    def fake_generate_plan(*, user_profile, opportunity, gap_vector, goal_id, existing_decisions, existing_memories):
        seen["memories"] = {m["memory_id"] for m in existing_memories}
        seen["budget"] = user_profile.daily_available_minutes
        seen["gaps"] = [g.skill_name for g in gap_vector.gaps]
        return PlanScheduleJSON(
            goal_id=goal_id,
            daily_budget_minutes=user_profile.daily_available_minutes,
            total_tasks=2,
            schedule=[
                TaskItem(task_id="t1", day_number=1, title="Precision and recall drill", duration_minutes=30, priority="High",
                         why_it_matters="Mandatory requirement with no evidence yet", source_refs=["decision#2"]),
                TaskItem(task_id="t2", day_number=2, title="SQL joins practice", duration_minutes=30, priority="Medium",
                         why_it_matters="Medium-weight gap", source_refs=[]),
            ],
        )

    monkeypatch.setattr("app.agents.planner_agent.generate_plan", fake_generate_plan)
    plan = seeded_client.post("/plans", json={"generate_from_opportunity_id": 1, "daily_budget_minutes": 45}).json()
    assert "planner_agent" in plan["rationale"]
    assert [t["title"] for t in plan["tasks"]][:2] == ["Precision and recall drill", "SQL joins practice"]
    assert {"decision#1", "decision#2", "goal#1", "ev#1"} <= seen["memories"]
    assert seen["budget"] == 45 and seen["gaps"][0] == "Model evaluation"
    assert _events(seeded_client, "model_call")


def test_planner_hallucinated_reference_is_rejected(seeded_client, live, monkeypatch):
    def fake_generate_plan(**kwargs):
        return PlanScheduleJSON(goal_id=kwargs["goal_id"], daily_budget_minutes=kwargs["user_profile"].daily_available_minutes, total_tasks=1,
                                schedule=[TaskItem(task_id="t1", day_number=1, title="Invented", duration_minutes=20, priority="High",
                                                   why_it_matters="x", source_refs=["ev#999"])])

    monkeypatch.setattr("app.agents.planner_agent.generate_plan", fake_generate_plan)
    response = seeded_client.post("/plans", json={"generate_from_opportunity_id": 1})
    assert response.status_code == 201
    assert "deterministic" in response.json()["rationale"]
    assert all(t["title"] != "Invented" for t in response.json()["tasks"])
    assert _events(seeded_client, "model_output_rejected")


def test_planner_failure_falls_back(seeded_client, live, monkeypatch):
    def boom(**kwargs):
        raise TimeoutError("provider timeout")

    monkeypatch.setattr("app.agents.planner_agent.generate_plan", boom)
    response = seeded_client.post("/plans", json={"generate_from_opportunity_id": 1})
    assert response.status_code == 201 and "deterministic" in response.json()["rationale"]
    assert _events(seeded_client, "model_fallback")


def test_fit_agent_cannot_claim_unevidenced_skill(seeded_client, live, monkeypatch):
    def fake_fit(*, user_profile, opportunity):
        match = lambda name: SkillMatch(skill_name=name, user_level="x", required_level="x", match_status="Match", explanation="model says yes")
        return FitAssessment(opportunity_title=opportunity.opportunity_title, overall_fit="Strong",
                             matching_skills=[match("Python"), match("Model evaluation")], partial_matches=[], missing_skills=[],
                             strengths=[], improvement_areas=[], summary="")

    monkeypatch.setattr("app.agents.fit_agent.assess_fit", fake_fit)
    fit = seeded_client.post("/opportunities/1/fit").json()
    assert fit["judged_by"] == "fit_agent"
    coverage = {r["requirement"]: r["coverage"] for r in fit["per_requirement"]}
    assert coverage["Python"] == "demonstrated"
    assert coverage["Model evaluation"] == "not_shown"  # no evidence in memory, so the claim is downgraded
    offline = seeded_client.post("/opportunities/1/fit", json={"use_model": False}).json()
    assert offline["judged_by"] == "deterministic"


def test_extract_offline_uses_keyword_fallback(seeded_client):
    text = "ML Intern at Acme\nRequired: Python and SQL\nModel evaluation experience is a plus\nRemote internship"
    created = seeded_client.post("/opportunities/extract", json={"text": text})
    assert created.status_code == 201
    body = created.json()
    assert body["extracted_by"] == "deterministic" and body["title"] == "ML Intern at Acme"
    weights = {r["name"]: r["weight"] for r in body["requirements"]}
    assert weights["Python"] == "High" and weights["SQL"] == "High" and weights["Model evaluation"] == "Low"
    assert seeded_client.post("/opportunities/extract", json={"text": "hello there"}).status_code == 422


def test_extract_live_uses_opportunity_agent(seeded_client, live, monkeypatch):
    def fake_extract(*, opportunity_text):
        return OpportunitySpec(opportunity_title="Data Intern", organization="Acme", opportunity_type="internship",
                               required_skills=[OpportunityRequirement(skill_name="Statistics", importance="High", is_mandatory=True, description="core")],
                               preferred_skills=["Git"], experience_level="Beginner", summary="s")

    monkeypatch.setattr("app.agents.opportunity_agent.extract_opportunity", fake_extract)
    body = seeded_client.post("/opportunities/extract", json={"text": "anything"}).json()
    assert body["extracted_by"] == "opportunity_agent" and body["org"] == "Acme"
    assert [r["name"] for r in body["requirements"]] == ["Statistics", "Git"]


def test_profile_input_reflects_memory_and_excludes_deleted(seeded, user):
    from app.memory import service as memory_service

    profile = bridge.user_profile_input(seeded, user)
    assert "Land an AI/ML internship" in profile.goals
    assert any(s.startswith("Python") for s in profile.skills)
    item = next(i for i in memory_service.list_items(seeded, user.id, types={"skill"}) if i.content.startswith("Python"))
    memory_service.soft_delete_item(seeded, item)
    assert not any(s.startswith("Python") for s in bridge.user_profile_input(seeded, user).skills)
