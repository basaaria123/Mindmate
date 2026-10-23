"""Offline tests for every agent: a fake client replaces Nebius, so no key or network is needed.

Covers success-criterion 6: model outputs that fail validation are retried once,
then safely rejected.
"""

import json
from types import SimpleNamespace

import pytest

from app.schemas.fit import FitAssessment
from app.schemas.gap import GapVectorJSON
from app.schemas.opportunity import OpportunitySpec
from app.schemas.profile import UserProfile

PROFILE = UserProfile(education="B.E. CSE", goals=["AI internship"], skills=["Python"], interests=["AI"],
                      daily_available_minutes=60, learning_preferences=["Hands-on"])
OPPORTUNITY = OpportunitySpec(opportunity_title="AI Intern", organization="Acme", opportunity_type="internship",
                              required_skills=[{"skill_name": "Python", "importance": "High", "is_mandatory": True, "description": "core"}],
                              preferred_skills=[], experience_level="Beginner", summary="s")
FIT = FitAssessment(opportunity_title="AI Intern", overall_fit="Moderate", matching_skills=[], partial_matches=[],
                    missing_skills=[], strengths=[], improvement_areas=[], summary="s")
GAPS = GapVectorJSON(opportunity_title="AI Intern", gaps=[])


class FakeClient:
    """Returns the queued replies in order and records every request."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        reply = self.replies.pop(0)
        content = reply if isinstance(reply, str) else json.dumps(reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def install(monkeypatch, module, *replies):
    client = FakeClient(*replies)
    monkeypatch.setattr(f"{module}.create_llm_client", lambda: client)
    return client


SUGGESTIONS = {"suggestions": [{"title": f"{c} {i}", "organization": None, "opportunity_type": "Job", "category": c, "explanation": "fits"}
                               for c in ("Jobs", "Projects", "Resources", "Other") for i in range(3)]}
PLAN = {"goal_id": "goal#1", "daily_budget_minutes": 60, "total_tasks": 1, "schedule": [
    {"task_id": "t1", "day_number": 1, "title": "Practice", "duration_minutes": 30, "priority": "High", "why_it_matters": "gap", "source_refs": ["decision#1"]}]}
PRACTICE = {"correctness": 40, "depth": 30, "clarity": 60, "feedback": "Misses recall.", "weakness_candidate": "Model evaluation",
            "is_store_worthy": True, "memory_tag": "weakness"}

CASES = [
    ("profile", "app.agents.profile_agent", lambda m: m.extract_user_profile("I study CS"), PROFILE.model_dump()),
    ("opportunity", "app.agents.opportunity_agent", lambda m: m.extract_opportunity("AI intern"), OPPORTUNITY.model_dump()),
    ("fit", "app.agents.fit_agent", lambda m: m.assess_fit(PROFILE, OPPORTUNITY), FIT.model_dump()),
    ("gap", "app.agents.gap_agent", lambda m: m.identify_skill_gaps(PROFILE, OPPORTUNITY, FIT), GAPS.model_dump()),
    ("planner", "app.agents.planner_agent",
     lambda m: m.generate_plan(PROFILE, OPPORTUNITY, GAPS, "goal#1", [], [{"memory_id": "decision#1"}]), PLAN),
    ("practice", "app.agents.practice_agent", lambda m: m.evaluate_practice("Q?", "An answer", "Model evaluation"), PRACTICE),
    ("suggestions", "app.agents.suggestions_agent", lambda m: m.generate_suggestions(PROFILE), SUGGESTIONS),
]


@pytest.mark.parametrize("name,module,call,reply", CASES, ids=[c[0] for c in CASES])
def test_agent_accepts_valid_reply(monkeypatch, name, module, call, reply):
    import importlib

    client = install(monkeypatch, module, reply)
    result = call(importlib.import_module(module))
    assert result is not None and len(client.requests) == 1


@pytest.mark.parametrize("name,module,call,reply", CASES, ids=[c[0] for c in CASES])
def test_agent_retries_once_after_invalid_json(monkeypatch, name, module, call, reply):
    import importlib

    client = install(monkeypatch, module, "not json at all", reply)
    call(importlib.import_module(module))
    assert len(client.requests) == 2
    assert "error" in client.requests[1]["messages"][-1]["content"].lower()


@pytest.mark.parametrize("name,module,call,reply", CASES, ids=[c[0] for c in CASES])
def test_agent_rejects_after_second_invalid_reply(monkeypatch, name, module, call, reply):
    import importlib

    install(monkeypatch, module, "{broken", {"unexpected": "shape"})
    with pytest.raises(ValueError):
        call(importlib.import_module(module))


def test_planner_rejects_invented_reference(monkeypatch):
    import app.agents.planner_agent as planner

    bad = json.loads(json.dumps(PLAN))
    bad["schedule"][0]["source_refs"] = ["ev#999"]
    install(monkeypatch, "app.agents.planner_agent", bad, bad)
    with pytest.raises(ValueError):
        planner.generate_plan(PROFILE, OPPORTUNITY, GAPS, "goal#1", [], [{"memory_id": "decision#1"}])


# ---------------- question generation ----------------

QUESTIONS = {"questions": [{"topic": "Model evaluation", "question": "How do you evaluate a classifier on imbalanced data?",
                            "expected_concepts": ["precision", "recall", "cross-validation"], "difficulty": "medium",
                            "why_this_question": "Active weakness", "source_refs": ["weakness#1"]}]}


def test_question_generation(monkeypatch):
    import app.agents.practice_agent as practice

    client = install(monkeypatch, "app.agents.practice_agent", QUESTIONS)
    result = practice.generate_practice_questions("AI/ML Intern", ["Python (intermediate)"], [{"requirement": "Model evaluation"}],
                                                  [{"ref": "weakness#1", "topic": "Model evaluation"}], topic="Model evaluation",
                                                  count=1, allowed_refs=["weakness#1"])
    assert result.questions[0].expected_concepts == ["precision", "recall", "cross-validation"]
    prompt = client.requests[0]["messages"][1]["content"]
    assert "AI/ML Intern" in prompt and "weakness#1" in prompt


def test_question_generation_rejects_unknown_refs_and_off_topic(monkeypatch):
    import app.agents.practice_agent as practice

    install(monkeypatch, "app.agents.practice_agent", QUESTIONS, QUESTIONS)
    with pytest.raises(ValueError):
        practice.generate_practice_questions("AI/ML Intern", [], [], [], allowed_refs=[])
    off_topic = json.loads(json.dumps(QUESTIONS))
    off_topic["questions"][0]["source_refs"] = []
    install(monkeypatch, "app.agents.practice_agent", off_topic, off_topic)
    with pytest.raises(ValueError):
        practice.generate_practice_questions("AI/ML Intern", [], [], [], topic="SQL")
    with pytest.raises(ValueError):
        practice.generate_practice_questions("AI/ML Intern", [], [], [], count=9)


# ---------------- replan explanation ----------------

def test_replan_explanation_cites_only_allowed_refs(monkeypatch):
    import app.agents.replan_agent as replan

    good = {"summary": "Model evaluation practice moved to day 1 because practice showed a recurring weakness [weakness#1].",
            "cited_refs": ["weakness#1"]}
    install(monkeypatch, "app.agents.replan_agent", good)
    assert replan.explain_replan({"moved": ["Mock interview"]}, ["weakness#1", "decision#1"]).cited_refs == ["weakness#1"]

    invented = {"summary": "Moved because of a new certificate [ev#42] and a weakness [weakness#1].", "cited_refs": ["ev#42", "weakness#1"]}
    install(monkeypatch, "app.agents.replan_agent", invented, invented)
    with pytest.raises(ValueError):
        replan.explain_replan({"moved": []}, ["weakness#1"])

    uncited = {"summary": "Your plan changed because of your recent practice results.", "cited_refs": []}
    install(monkeypatch, "app.agents.replan_agent", uncited, good)
    assert replan.explain_replan({}, ["weakness#1"]).summary.startswith("Model evaluation")


def test_assistant_agent_uses_memory_strips_thinking_and_picks_the_tier(monkeypatch):
    from app.agents import assistant_agent
    from app.schemas.assistant import ChatMessage
    from app.services.llm_client import FAST_MODEL, REASONING_MODEL

    client = install(monkeypatch, "app.agents.assistant_agent", "<think>plan the answer</think>Hello Meera! I can help.")
    history = [ChatMessage(role="user", content="Hello")]
    reply = assistant_agent.chat_reply(history, "GOALS:\n  [goal#1] Land an AI/ML internship")
    assert reply.reply == "Hello Meera! I can help." and reply.model == FAST_MODEL
    request = client.requests[0]
    assert request["model"] == FAST_MODEL
    assert "[goal#1] Land an AI/ML internship" in request["messages"][1]["content"]
    assert request["messages"][-1] == {"role": "user", "content": "Hello"}

    client = install(monkeypatch, "app.agents.assistant_agent", "", "Here is a deeper answer.")
    reply = assistant_agent.chat_reply(history, "memory", think_harder=True)
    assert reply.model == REASONING_MODEL and len(client.requests) == 2

    install(monkeypatch, "app.agents.assistant_agent", "", "  ")
    with pytest.raises(ValueError, match="empty response"):
        assistant_agent.chat_reply(history, "memory")
