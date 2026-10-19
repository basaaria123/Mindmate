"""Score arithmetic: fixed inputs give fixed outputs (proposal section 12)."""

from datetime import date, timedelta

import pytest

from app.config import PriorityWeights
from app.scoring.fit import FitResult, RequirementJudgment, band_for, compute_fit, judge_from_skills, judgments_from_ai_assessment
from app.scoring.gaps import rank_gaps
from app.scoring.priority import compute_priority, deadline_urgency, goal_hierarchy_weight
from app.scoring.weakness import decide_weakness


def test_fit_formula_matches_proposal():
    judgments = [
        RequirementJudgment("Python", "High", "demonstrated", ("ev#1",)),
        RequirementJudgment("ML", "High", "partial", ("ev#2",)),
        RequirementJudgment("Model evaluation", "Medium", "not_shown", (), mandatory=True),
    ]
    result = compute_fit(judgments)
    # (3*1 + 3*0.5 + 2*0) / (3+3+2) = 4.5/8 = 56.25 -> 56
    assert result.score == 56
    assert result.band == "Moderate"
    assert result.top_gap == "Model evaluation"
    assert result.refs == ("ev#1", "ev#2")


def test_fit_is_deterministic():
    judgments = [RequirementJudgment("A", "High", "demonstrated", ("ev#1",)), RequirementJudgment("B", "Low", "not_shown")]
    assert compute_fit(judgments).as_dict() == compute_fit(judgments).as_dict()


@pytest.mark.parametrize("score,band", [(0, "Weak"), (49, "Weak"), (50, "Moderate"), (74, "Moderate"), (75, "Strong"), (100, "Strong")])
def test_bands(score, band):
    assert band_for(score) == band


def test_coverage_without_evidence_is_rejected():
    with pytest.raises(ValueError):
        compute_fit([RequirementJudgment("Python", "High", "demonstrated", ())])


def test_empty_requirements_score_zero():
    result = compute_fit([])
    assert result.score == 0 and result.top_gap is None


def test_deterministic_judge_requires_evidence():
    requirements = [{"name": "Python", "weight": "High"}, {"name": "SQL", "weight": "Medium"}, {"name": "Rust", "weight": "Low"}]
    skills = [
        {"name": "Python", "level": "intermediate", "ref": "skill#1", "evidence_refs": ["ev#1"]},
        {"name": "SQL", "level": "beginner", "ref": "skill#2", "evidence_refs": []},
    ]
    judged = {j.requirement: j for j in judge_from_skills(requirements, skills)}
    assert judged["Python"].coverage == "demonstrated" and judged["Python"].evidence_refs == ("ev#1",)
    assert judged["SQL"].coverage == "not_shown"  # bare claim, no evidence
    assert judged["Rust"].coverage == "not_shown"


def test_ai_assessment_cannot_claim_coverage_without_evidence():
    requirements = [{"name": "Python", "weight": "High"}, {"name": "Docker", "weight": "Low"}]
    skills = [{"name": "Python", "level": "intermediate", "ref": "skill#1", "evidence_refs": ["ev#1"]}]
    assessment = {"matching_skills": [{"skill_name": "Python"}, {"skill_name": "Docker"}]}
    judged = {j.requirement: j for j in judgments_from_ai_assessment(assessment, requirements, skills)}
    assert judged["Python"].coverage == "demonstrated"
    assert judged["Docker"].coverage == "not_shown"


def test_gap_ranking_prefers_mandatory_high_weight_and_weakness():
    fit = compute_fit(
        [
            RequirementJudgment("SQL", "Medium", "not_shown"),
            RequirementJudgment("Model evaluation", "High", "not_shown", mandatory=True),
            RequirementJudgment("Git", "Low", "partial", ("ev#3",)),
        ]
    )
    gaps = rank_gaps(fit, [{"topic": "Model evaluation", "severity": "high", "ref": "weakness#1"}])
    assert [g.requirement for g in gaps] == ["Model evaluation", "SQL", "Git"]
    assert "weakness#1" in gaps[0].refs
    assert gaps[0].impact_score == 100


def test_priority_formula():
    weights = PriorityWeights()
    today = date(2026, 10, 17)
    breakdown = compute_priority(
        role_impact=0.8,
        task_refs=["weakness#1"],
        active_weaknesses={"weakness#1": "high"},
        goal_rank=1,
        deadline=today + timedelta(days=7),
        today=today,
        weights=weights,
    )
    expected = 0.40 * 0.8 + 0.25 * 1.0 + 0.20 * 1.0 + 0.15 * 0.5
    assert breakdown.score == pytest.approx(expected)
    assert breakdown.must_keep is True
    assert breakdown.inputs.weakness_refs == ("weakness#1",)


def test_priority_without_weakness_or_deadline_is_not_must_keep():
    breakdown = compute_priority(role_impact=0.5, task_refs=[], active_weaknesses={}, goal_rank=2, deadline=None, today=date.today(), weights=PriorityWeights())
    assert breakdown.must_keep is False
    assert breakdown.score == pytest.approx(0.40 * 0.5 + 0.20 * 0.5)


def test_goal_hierarchy_and_urgency():
    assert goal_hierarchy_weight(1) == 1.0
    assert goal_hierarchy_weight(2) == 0.5
    assert goal_hierarchy_weight(None) == 0.5
    today = date(2026, 10, 17)
    assert deadline_urgency(today, today) == 1.0
    assert deadline_urgency(today + timedelta(days=14), today) == 0.0
    assert deadline_urgency(None, today) == 0.0


def test_weakness_thresholds():
    kwargs = {"score_threshold": 60, "min_occurrences": 2, "severe_score": 35}
    assert decide_weakness([], **kwargs).should_record is False
    assert decide_weakness([50], **kwargs).should_record is False  # one answer is not enough
    assert decide_weakness([30], **kwargs).should_record is True  # severe single answer
    decision = decide_weakness([45, 40], **kwargs)
    assert decision.should_record and decision.evidence_count == 2 and decision.severity == "medium"
    assert decide_weakness([45, 40, 50], **kwargs).severity == "high"


def test_fit_result_dict_roundtrip():
    result = compute_fit([RequirementJudgment("Python", "High", "demonstrated", ("ev#1",))])
    data = result.as_dict()
    assert data["score"] == 100 and data["per_requirement"][0]["evidence_refs"] == ["ev#1"]
    assert isinstance(result, FitResult)



@pytest.mark.parametrize("a,b,expected", [
    ("Python", "Basic Python", True),
    ("SQL", "Practice two SQL join questions", True),
    ("Model evaluation", "Mock interview: model evaluation questions", True),
    ("Model evaluation", "Model evaluation: metrics beyond accuracy", True),
    ("Machine learning fundamentals", "Machine learning", True),
    ("Data structures", "Data structure", True),
    ("Deep learning", "Machine learning fundamentals", False),
    ("Data visualisation", "core data structures", False),
    ("Java", "JavaScript", False),
    ("C++", "C", False),
    ("Statistics", "Basic statistics", True),
    ("", "Python", False),
])
def test_skill_matching(a, b, expected):
    from app.scoring.fit import skill_matches

    assert skill_matches(a, b) is expected and skill_matches(b, a) is expected


def test_deep_learning_requirement_is_not_credited_to_ml_evidence():
    requirements = [{"name": "Deep learning", "weight": "High"}]
    skills = [{"name": "Machine learning fundamentals", "level": "intermediate", "ref": "skill#2", "evidence_refs": ["ev#3"]},
              {"name": "Deep learning", "level": "none", "ref": "skill#6", "evidence_refs": []}]
    assert judge_from_skills(requirements, skills)[0].coverage == "not_shown"
