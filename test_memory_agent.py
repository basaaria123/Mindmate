"""Unit tests for memory_agent.py: candidate creation, ID generation, and store integration."""

import json
import pytest

from app.agents.memory_agent import (
    create_and_store_memory,
    create_memory_candidate,
    generate_memory_id,
)
from app.schemas.memory import MemoryItem
from app.schemas.practice import PracticeEvaluation
from app.services.memory_store import MEMORY_FILE


@pytest.fixture(autouse=True)
def _clean_memory_file(tmp_path, monkeypatch):
    """Redirect the memory store to a temp file so tests don't pollute data/."""
    temp_file = tmp_path / "memories.json"
    monkeypatch.setattr("app.services.memory_store.MEMORY_FILE", temp_file)
    monkeypatch.setattr("app.agents.memory_agent.MEMORY_FILE", temp_file, raising=False)
    yield


def _evaluation(
    *,
    correctness=80,
    depth=70,
    clarity=85,
    feedback="Solid answer.",
    weakness_candidate=None,
    is_store_worthy=True,
    memory_tag="weakness",
):
    return PracticeEvaluation(
        correctness=correctness,
        depth=depth,
        clarity=clarity,
        feedback=feedback,
        weakness_candidate=weakness_candidate,
        is_store_worthy=is_store_worthy,
        memory_tag=memory_tag,
    )


# ---------- create_memory_candidate ----------


def test_candidate_returns_none_when_not_store_worthy():
    evaluation = _evaluation(is_store_worthy=False, memory_tag=None)
    result = create_memory_candidate(evaluation, source="test", memory_id="w#01")
    assert result is None


def test_candidate_returns_none_when_no_content():
    evaluation = _evaluation(
        weakness_candidate=None,
        feedback="   ",
        is_store_worthy=True,
    )
    result = create_memory_candidate(evaluation, source="test", memory_id="w#01")
    assert result is None


def test_candidate_with_weakness():
    evaluation = _evaluation(
        weakness_candidate="Cannot explain backpropagation.",
        correctness=30,
        depth=25,
        clarity=40,
    )
    candidate = create_memory_candidate(evaluation, source="practice:nn", memory_id="weakness#01")
    assert candidate is not None
    assert candidate.memory_type == "weakness"
    assert candidate.content == "Cannot explain backpropagation."
    assert candidate.confidence == 25  # min(30, 25, 40)
    assert "weakness" in candidate.reference_tags


def test_candidate_with_feedback_only():
    evaluation = _evaluation(
        weakness_candidate=None,
        feedback="Key insight about model evaluation.",
        correctness=85,
        depth=90,
        clarity=80,
    )
    candidate = create_memory_candidate(evaluation, source="practice:eval", memory_id="learning_insight#01")
    assert candidate is not None
    assert candidate.memory_type == "learning_insight"
    assert candidate.content == "Key insight about model evaluation."
    assert candidate.confidence == 80  # min(85, 90, 80)


def test_candidate_rejects_empty_memory_id():
    evaluation = _evaluation(weakness_candidate="Some weakness.")
    with pytest.raises(ValueError, match="memory ID"):
        create_memory_candidate(evaluation, source="test", memory_id="   ")


def test_candidate_rejects_empty_source():
    evaluation = _evaluation(weakness_candidate="Some weakness.")
    with pytest.raises(ValueError, match="source"):
        create_memory_candidate(evaluation, source="  ", memory_id="w#01")


# ---------- generate_memory_id ----------


def test_generate_first_weakness_id():
    assert generate_memory_id("weakness") == "weakness#01"


def test_generate_first_learning_insight_id():
    assert generate_memory_id("learning_insight") == "learning_insight#01"


def test_generate_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unsupported memory type"):
        generate_memory_id("invalid_type")


def test_generate_increments_after_existing(tmp_path, monkeypatch):
    temp_file = tmp_path / "memories.json"
    existing = [
        MemoryItem(
            memory_id="weakness#01",
            memory_type="weakness",
            content="First weakness.",
            source="test",
            confidence=50,
        ).model_dump(),
        MemoryItem(
            memory_id="weakness#02",
            memory_type="weakness",
            content="Second weakness.",
            source="test",
            confidence=40,
        ).model_dump(),
    ]
    temp_file.write_text(json.dumps(existing), encoding="utf-8")
    assert generate_memory_id("weakness") == "weakness#03"


# ---------- create_and_store_memory ----------


def test_create_and_store_persists_weakness():
    evaluation = _evaluation(
        weakness_candidate="Cannot explain gradient descent.",
        correctness=30,
        depth=20,
        clarity=40,
    )
    result = create_and_store_memory(evaluation, source="practice:nn")
    assert result is not None
    assert isinstance(result, MemoryItem)
    assert result.memory_id == "weakness#01"
    assert result.memory_type == "weakness"


def test_create_and_store_returns_none_for_low_value():
    evaluation = _evaluation(is_store_worthy=False, memory_tag=None)
    result = create_and_store_memory(evaluation, source="test")
    assert result is None
