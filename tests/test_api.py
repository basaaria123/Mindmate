"""API contract tests: shapes the frontend (mindmate-frontend/src/services/api.ts) relies on,
error handling, rate limiting, reset and reference validation."""

import pytest

from app.rate_limit import limiter


def test_health_and_status(seeded_client):
    assert seeded_client.get("/health").json() == {"status": "healthy"}
    status = seeded_client.get("/admin/status").json()
    assert status["database"] == "sqlite" and status["counts"]["users"] == 1
    assert status["llm_available"] is False


def test_profile_roundtrip_matches_frontend_shape(seeded_client):
    profile = seeded_client.get("/profile").json()
    assert {"name", "goal", "targetRole", "dailyMinutes"} <= profile.keys()
    updated = seeded_client.put("/profile", json={"name": "Meera", "goal": "Learn faster, Build skills", "targetRole": "Student", "dailyMinutes": 45}).json()
    assert updated["targetRole"] == "Student" and updated["dailyMinutes"] == 45
    assert seeded_client.get("/profile").json()["goal"] == "Learn faster, Build skills"


def test_memory_state_shape(seeded_client):
    state = seeded_client.get("/memory").json()
    assert isinstance(state["memoryNotes"], list) and state["memoryNotes"]
    assert isinstance(state["items"], list) and state["total"] == len(state["items"])
    assert isinstance(state["trace"], list) and {"id", "title", "detail", "occurredAt"} <= state["trace"][0].keys()
    assert state["originalPlan"] and state["updatedPlan"] is None and state["replanReason"] is None


def test_memory_crud_and_weakness_note(seeded_client):
    created = seeded_client.post("/memory", json={"type": "weakness", "content": "Practice focus: Model evaluation"})
    assert created.status_code == 201
    body = created.json()
    assert {"id", "type", "content", "createdAt"} <= body.keys()
    assert body["type"] == "weakness" and body["ref"].startswith("weakness#")
    assert "Model evaluation" in seeded_client.get("/weaknesses").json()["weaknesses"][0]["topic"]

    note = seeded_client.post("/memory", json={"type": "note", "content": "Prefers evening study sessions"}).json()
    patched = seeded_client.patch(f"/memory/{note['id']}", json={"content": "Prefers late evening study sessions"}).json()
    assert patched["content"] == "Prefers late evening study sessions"

    deleted = seeded_client.delete(f"/memory/{note['id']}")
    assert deleted.json()["deleted"] is True
    assert seeded_client.get(f"/memory/{note['id']}").json()["deletedAt"] is not None
    assert note["content"] not in seeded_client.get("/memory").json()["memoryNotes"]
    assert seeded_client.get("/memory?include_deleted=true").json()["total"] > seeded_client.get("/memory").json()["total"]
    assert seeded_client.post("/memory/purge").json()["purged"] == 1

    missing_reason = seeded_client.post("/memory", json={"type": "decision", "content": "Exams first"})
    assert missing_reason.status_code == 422
    decision = seeded_client.post("/memory", json={"type": "decision", "content": "Exams first", "reason": "Eligibility depends on results"})
    assert decision.status_code == 201 and decision.json()["ref"].startswith("decision#")


def test_delete_all_requires_confirmation(seeded_client):
    assert seeded_client.delete("/memory").status_code == 403
    response = seeded_client.delete("/memory?confirm=true")
    assert response.status_code == 200 and response.json()["deleted"] > 0
    assert seeded_client.get("/memory").json()["total"] == 0


def test_practice_flow_through_api(seeded_client):
    start = seeded_client.post("/practice/start", json={"topic": "Model evaluation"})
    assert start.status_code == 201 and start.json()["status"] == "open"
    short = seeded_client.post("/practice/evaluate", json={"answer": "short"})
    assert short.status_code == 422
    result = seeded_client.post("/practice/evaluate", json={"answer": "I would only check accuracy on the training data.", "session_id": start.json()["id"]}).json()
    assert {"answer", "score", "weakness", "feedback", "submittedAt"} <= result.keys()
    assert result["weakness_recorded"] is True
    replanned = seeded_client.post("/plans/replan", json={}).json()
    assert result["weakness_ref"] in replanned["rationale"]
    state = seeded_client.get("/memory").json()
    assert state["updatedPlan"] and state["replanReason"]
    assert state["latestPractice"]["weakness"] == "Model evaluation"


def test_events_endpoint_shape(seeded_client):
    events = seeded_client.get("/agent/events?limit=5").json()["events"]
    assert len(events) == 5
    assert {"timestamp", "agent", "action", "summary", "refs", "title", "detail", "occurredAt"} <= events[0].keys()


def test_fit_and_gaps_reject_unknown_evidence(seeded_client):
    fit = seeded_client.post("/opportunities/1/fit").json()
    assert fit["judged_by"] == "deterministic" and 0 <= fit["score"] <= 100
    assert fit["top_gap"] == "Model evaluation"
    bad = seeded_client.post("/opportunities/1/fit", json={"judgments": [{"requirement": "Python", "weight": "High", "coverage": "demonstrated", "evidence_refs": ["ev#999"]}]})
    assert bad.status_code == 422 and "ev#999" in bad.json()["detail"]
    good = seeded_client.post("/opportunities/1/fit", json={"judgments": [
        {"requirement": "Python", "weight": "High", "coverage": "demonstrated", "evidence_refs": ["ev#1"]},
        {"requirement": "Model evaluation", "weight": "High", "coverage": "not_shown", "mandatory": True},
    ]}).json()
    assert good["score"] == 50 and good["judged_by"] == "model"
    gaps = seeded_client.post("/skills/gaps", json={"opportunity_id": 1}).json()["gaps"]
    assert gaps[0]["requirement"] == "Model evaluation"


def test_ai_fit_agent_output_is_accepted(seeded_client):
    assessment = {
        "opportunity_title": "AI/ML Engineering Intern",
        "overall_fit": "Moderate",
        "matching_skills": [{"skill_name": "Python", "explanation": "Projects in Python"}],
        "partial_matches": [{"skill_name": "SQL", "explanation": "Some reporting queries"}],
        "missing_skills": [{"skill_name": "Model evaluation", "explanation": "No evidence"}],
        "strengths": [], "improvement_areas": [], "summary": "",
    }
    fit = seeded_client.post("/opportunities/1/fit", json={"ai_assessment": assessment}).json()
    assert fit["judged_by"] == "fit_agent"
    python = next(r for r in fit["per_requirement"] if r["requirement"] == "Python")
    assert python["coverage"] == "demonstrated" and python["evidence_refs"]


def test_opportunities_store_search_and_agent_shape(seeded_client):
    listing = seeded_client.get("/opportunities").json()
    assert listing["total"] == 12
    spec = {
        "opportunity_title": "Junior ML Engineer", "organization": "Example", "opportunity_type": "job",
        "required_skills": [{"skill_name": "Python", "importance": "High", "is_mandatory": True, "description": "core"}],
        "preferred_skills": ["Git"], "experience_level": "Beginner", "summary": "entry role",
    }
    created = seeded_client.post("/opportunities", json=spec)
    assert created.status_code == 201
    assert [r["name"] for r in created.json()["requirements"]] == ["Python", "Git"]
    results = seeded_client.post("/opportunities/search", json={"query": "evaluation internship"}).json()
    assert results["source"] == "curated" and results["results"][0]["relevance"] > 0
    assert seeded_client.post("/opportunities", json={"title": "No requirements"}).status_code == 422


def test_plan_create_and_task_status(seeded_client):
    created = seeded_client.post("/plans", json={"tasks": [
        {"title": "Task A", "minutes": 40, "priority": "High", "refs": ["decision#1"]},
        {"title": "Task B", "minutes": 40, "priority": "Low"},
    ], "daily_budget_minutes": 60})
    assert created.status_code == 201
    plan = created.json()
    assert plan["version"] == 2 and all(v <= 60 for v in plan["minutes_by_day"].values())
    task = plan["tasks"][0]
    done = seeded_client.patch(f"/plans/tasks/{task['id']}", json={"status": "done"}).json()
    assert done["status"] == "done"
    assert seeded_client.post("/plans", json={"tasks": [{"title": "X", "minutes": 10, "refs": ["ev#999"]}]}).status_code == 422
    generated = seeded_client.post("/plans", json={"generate_from_opportunity_id": 1})
    assert generated.status_code == 201 and generated.json()["tasks"]


def test_goals_constraints_decisions(seeded_client):
    goals = seeded_client.get("/goals").json()
    assert goals["current_goal"]["priority_rank"] == 1 and len(goals["goals"]) == 3
    new_goal = seeded_client.post("/goals", json={"title": "Publish a blog post", "priority_rank": 4}).json()
    assert new_goal["ref"].startswith("goal#")
    assert seeded_client.delete(f"/goals/{new_goal['id']}").json()["deleted"]
    assert len(seeded_client.get("/goals").json()["goals"]) == 3
    assert seeded_client.post("/constraints", json={"kind": "weird", "value": "x"}).status_code == 422
    assert seeded_client.post("/constraints", json={"kind": "hours", "value": "30 minutes on weekends"}).status_code == 201
    decision = seeded_client.post("/decisions", json={"statement": "Exams first", "reason": "Eligibility", "goal_id": 3}).json()
    assert decision["goal_ref"] == "goal#3"


def test_memory_context_excludes_deleted(seeded_client):
    before = seeded_client.get("/memory/context?task=planner").json()
    ref = before["decisions"][0]["ref"]
    item = next(i for i in seeded_client.get("/memory").json()["items"] if i["ref"] == ref)
    seeded_client.delete(f"/memory/{item['id']}")
    after = seeded_client.get("/memory/context?task=planner").json()
    assert ref not in after["refs"] and ref not in after["prompt_text"]
    assert seeded_client.get("/memory/context?task=nope").status_code == 422


def test_reset_demo_restores_persona(seeded_client):
    seeded_client.delete("/memory?confirm=true")
    assert seeded_client.get("/memory").json()["total"] == 0
    reset = seeded_client.post("/admin/reset-demo").json()
    assert reset["status"] == "reset"
    assert seeded_client.get("/memory").json()["total"] > 0
    assert seeded_client.get("/plans").json()["active"]["version"] == 1


def test_admin_token_enforced(client, monkeypatch):
    monkeypatch.setenv("MINDMATE_ADMIN_TOKEN", "secret")
    assert client.post("/admin/reset-demo").status_code == 403
    assert client.post("/admin/reset-demo", headers={"X-Admin-Token": "secret"}).status_code == 200


def test_rate_limit(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    limiter.reset()
    codes = [client.get("/profile").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and 429 in codes[3:]
    assert client.get("/health").status_code == 200  # exempt
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "0")


def test_validation_errors_use_detail(client):
    response = client.put("/profile", json={"dailyMinutes": 0})
    assert response.status_code == 422 and "dailyMinutes" in response.json()["detail"]


@pytest.mark.parametrize("path", ["/memory/999", "/plans/999", "/opportunities/999"])
def test_not_found(seeded_client, path):
    assert seeded_client.get(path).status_code == 404
