"""Offline schema tests for MemoryItem and SuggestionsResponse."""

import pytest
from pydantic import ValidationError

from app.schemas.memory import MemoryItem
from app.schemas.suggestions import OpportunitySuggestion, SuggestionsResponse


# ---------- MemoryItem ----------


def test_valid_memory_item():
    item = MemoryItem(
        memory_id="weakness#01",
        memory_type="weakness",
        content="Struggled with backpropagation concepts.",
        reference_tags=["practice", "weakness"],
        source="practice:neural networks",
        confidence=40,
    )
    assert item.memory_type == "weakness"
    assert item.confidence == 40


def test_memory_type_must_be_literal():
    with pytest.raises(ValidationError):
        MemoryItem(
            memory_id="x#1",
            memory_type="unknown_type",
            content="Invalid type.",
            source="test",
            confidence=50,
        )


def test_empty_content_rejected():
    with pytest.raises(ValidationError):
        MemoryItem(
            memory_id="w#1",
            memory_type="weakness",
            content="",
            source="test",
            confidence=50,
        )


def test_confidence_bounds():
    with pytest.raises(ValidationError):
        MemoryItem(
            memory_id="w#1",
            memory_type="weakness",
            content="Over 100.",
            source="test",
            confidence=101,
        )

    with pytest.raises(ValidationError):
        MemoryItem(
            memory_id="w#1",
            memory_type="weakness",
            content="Below 0.",
            source="test",
            confidence=-1,
        )


def test_learning_insight_type():
    item = MemoryItem(
        memory_id="learning_insight#03",
        memory_type="learning_insight",
        content="Understood the difference between precision and recall.",
        source="practice:model evaluation",
        confidence=75,
    )
    assert item.memory_type == "learning_insight"


# ---------- SuggestionsResponse ----------


def _suggestion(category: str, index: int = 1) -> OpportunitySuggestion:
    return OpportunitySuggestion(
        title=f"Suggestion {category} {index}",
        organization=None,
        opportunity_type="Job" if category == "Jobs" else "Project",
        category=category,
        explanation=f"Relevant because of the user's interest in {category}.",
    )


def test_valid_suggestions_response():
    suggestions = []
    for category in ("Jobs", "Projects", "Resources", "Other"):
        for i in range(3):
            suggestions.append(_suggestion(category, i))
    response = SuggestionsResponse(suggestions=suggestions)
    assert len(response.suggestions) == 12


def test_wrong_count_raises():
    suggestions = [_suggestion("Jobs", i) for i in range(12)]
    with pytest.raises(ValidationError, match="Jobs"):
        SuggestionsResponse(suggestions=suggestions)


def test_too_few_suggestions_raises():
    with pytest.raises(ValidationError):
        SuggestionsResponse(suggestions=[_suggestion("Jobs")])
