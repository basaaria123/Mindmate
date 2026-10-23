"""AI Assistant chat: real model path, honest failures, and the activity trace."""

import pytest

from app.schemas.assistant import AssistantReply

HELLO = {"messages": [{"role": "user", "content": "Hello, what can you help me with?"}]}


@pytest.fixture()
def live(monkeypatch):
    monkeypatch.setattr("app.services.assistant_service.llm_available", lambda: True)


def _events(client, action):
    return [e for e in client.get("/agent/events?agent=assistant").json()["events"] if e["action"] == action]


def test_reply_comes_from_the_agent_and_is_traced_with_model_and_seconds(seeded_client, live, monkeypatch):
    seen = {}

    def fake_chat_reply(messages, memory, think_harder=False):
        seen.update(messages=messages, memory=memory, think_harder=think_harder)
        return AssistantReply(reply="I can help you plan, practise and track progress [goal#1].",
                              model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")

    monkeypatch.setattr("app.agents.assistant_agent.chat_reply", fake_chat_reply)
    response = seeded_client.post("/assistant/chat", json=HELLO)
    assert response.status_code == 200
    body = response.json()
    assert body == {"reply": "I can help you plan, practise and track progress [goal#1].",
                    "model": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", "source": "nemotron"}
    # grounded in memory: goals, decisions, plan and target fit
    assert "[goal#1]" in seen["memory"] and "[decision#1]" in seen["memory"]
    assert "PLAN: [plan#1]" in seen["memory"] and "TARGET OPPORTUNITY" in seen["memory"]
    call = _events(seeded_client, "model_call")[0]
    assert call["summary"].startswith("assistant: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B answered in")
    assert call["payload"]["model"] == "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B" and call["payload"]["seconds"] >= 0
    # the message text is never stored in the trace
    assert "Hello" not in str(call)


def test_follow_up_sends_the_conversation_and_think_harder_uses_ultra(seeded_client, live, monkeypatch):
    from app.services.llm_client import REASONING_MODEL

    seen = {}

    def fake_chat_reply(messages, memory, think_harder=False):
        seen.update(roles=[m.role for m in messages], think_harder=think_harder)
        return AssistantReply(reply="Start with model evaluation.", model=REASONING_MODEL)

    monkeypatch.setattr("app.agents.assistant_agent.chat_reply", fake_chat_reply)
    conversation = {"messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi Meera."},
        {"role": "user", "content": "What should I study first?"},
    ], "think_harder": True}
    assert seeded_client.post("/assistant/chat", json=conversation).status_code == 200
    assert seen == {"roles": ["user", "assistant", "user"], "think_harder": True}
    assert REASONING_MODEL in _events(seeded_client, "model_call")[0]["summary"]


def test_model_failure_is_an_error_not_a_successful_call(seeded_client, live, monkeypatch):
    def broken(messages, memory, think_harder=False):
        raise TimeoutError("provider timed out")

    monkeypatch.setattr("app.agents.assistant_agent.chat_reply", broken)
    response = seeded_client.post("/assistant/chat", json=HELLO)
    assert response.status_code == 502 and "did not answer (TimeoutError)" in response.json()["detail"]
    assert _events(seeded_client, "model_call") == []
    error = _events(seeded_client, "model_error")[0]
    assert "failed after" in error["summary"] and error["payload"]["error"] == "TimeoutError"


def test_without_a_key_no_call_is_made_and_the_reason_is_explicit(seeded_client, monkeypatch):
    monkeypatch.setattr("app.agents.assistant_agent.chat_reply", lambda *a, **k: pytest.fail("model called"))
    response = seeded_client.post("/assistant/chat", json=HELLO)
    assert response.status_code == 503
    assert "NEBIUS_API_KEY" in response.json()["detail"]
    assert _events(seeded_client, "model_call") == [] and _events(seeded_client, "model_unavailable")


def test_conversation_must_end_with_the_user(seeded_client, live):
    response = seeded_client.post("/assistant/chat", json={"messages": [{"role": "assistant", "content": "Hi"}]})
    assert response.status_code == 422
