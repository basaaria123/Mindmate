"""Offline schema tests for PracticeEvaluation."""

import pytest
from pydantic import ValidationError

from app.schemas.practice import PracticeEvaluation


def test_valid_evaluation():
    evaluation = PracticeEvaluation(
        correctness=80,
        depth=70,
        clarity=85,
        feedback="Good answer with clear reasoning.",
        weakness_candidate=None,
        is_store_worthy=False,
        memory_tag=None,
    )
    assert evaluation.correctness == 80
    assert evaluation.is_store_worthy is False


def test_store_worthy_with_weakness():
    evaluation = PracticeEvaluation(
        correctness=40,
        depth=35,
        clarity=50,
        feedback="Several key concepts are missing.",
        weakness_candidate="Lacks understanding of gradient descent.",
        is_store_worthy=True,
        memory_tag="weakness",
    )
    assert evaluation.weakness_candidate is not None
    assert evaluation.memory_tag == "weakness"


def test_score_out_of_range_rejected():
    with pytest.raises(ValidationError):
        PracticeEvaluation(
            correctness=110,
            depth=70,
            clarity=85,
            feedback="Score above 100.",
            is_store_worthy=False,
        )


def test_negative_score_rejected():
    with pytest.raises(ValidationError):
        PracticeEvaluation(
            correctness=-5,
            depth=70,
            clarity=85,
            feedback="Negative score.",
            is_store_worthy=False,
        )


def test_defaults_for_optional_fields():
    evaluation = PracticeEvaluation(
        correctness=50,
        depth=50,
        clarity=50,
        feedback="Average.",
        is_store_worthy=False,
    )
    assert evaluation.weakness_candidate is None
    assert evaluation.memory_tag is None
