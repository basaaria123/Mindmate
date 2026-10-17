"""Deterministic fit score (proposal section 7, "Fit score").

    fit% = 100 x sum(weight_i x coverage_i) / sum(weight_i)
    weight:   High=3, Medium=2, Low=1
    coverage: not_shown=0, partial=0.5, demonstrated=1
    bands:    75+ Strong, 50-74 Moderate, below 50 Weak

A model (or the deterministic judge below) says how well each requirement is
covered and which evidence IDs back the judgement; this module validates the
shape and computes the number. Reference validation against the database
happens in the service layer so the arithmetic stays pure and testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

WEIGHTS: dict[str, int] = {"High": 3, "Medium": 2, "Low": 1}
COVERAGE: dict[str, float] = {"not_shown": 0.0, "partial": 0.5, "demonstrated": 1.0}
LEVEL_ORDER = ["none", "beginner", "intermediate", "advanced", "expert"]


def normalize_weight(value: str | int | None) -> str:
    if isinstance(value, int):
        return {3: "High", 2: "Medium", 1: "Low"}.get(value, "Medium")
    if not value:
        return "Medium"
    text = str(value).strip().lower()
    if text.startswith("h"):
        return "High"
    if text.startswith("l"):
        return "Low"
    return "Medium"


def normalize_coverage(value: str | float | None) -> str:
    if isinstance(value, (int, float)):
        return "demonstrated" if value >= 1 else "partial" if value > 0 else "not_shown"
    if not value:
        return "not_shown"
    text = str(value).strip().lower().replace(" ", "_")
    if text in COVERAGE:
        return text
    if text in {"match", "matched", "demonstrated", "full", "yes"}:
        return "demonstrated"
    if text.startswith("partial"):
        return "partial"
    return "not_shown"


@dataclass(frozen=True)
class RequirementJudgment:
    requirement: str
    weight: str = "Medium"
    coverage: str = "not_shown"
    evidence_refs: tuple[str, ...] = ()
    mandatory: bool = False
    explanation: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "RequirementJudgment":
        name = data.get("requirement") or data.get("name") or data.get("skill_name")
        if not name:
            raise ValueError("A requirement judgement needs a requirement name.")
        return cls(
            requirement=str(name).strip(),
            weight=normalize_weight(data.get("weight") or data.get("importance")),
            coverage=normalize_coverage(data.get("coverage") or data.get("match_status")),
            evidence_refs=tuple(str(ref) for ref in data.get("evidence_refs", []) or []),
            mandatory=bool(data.get("mandatory", data.get("is_mandatory", False))),
            explanation=str(data.get("explanation", "") or ""),
        )


@dataclass(frozen=True)
class RequirementScore:
    requirement: str
    weight: str
    weight_value: int
    coverage: str
    coverage_value: float
    contribution: float
    gap: float
    mandatory: bool
    evidence_refs: tuple[str, ...]
    explanation: str

    def as_dict(self) -> dict:
        return {
            "requirement": self.requirement,
            "weight": self.weight,
            "weight_value": self.weight_value,
            "coverage": self.coverage,
            "coverage_value": self.coverage_value,
            "contribution": round(self.contribution, 3),
            "gap": round(self.gap, 3),
            "mandatory": self.mandatory,
            "evidence_refs": list(self.evidence_refs),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class FitResult:
    score: int
    band: str
    per_requirement: tuple[RequirementScore, ...]
    top_gap: str | None
    refs: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "band": self.band,
            "per_requirement": [item.as_dict() for item in self.per_requirement],
            "top_gap": self.top_gap,
            "refs": list(self.refs),
        }


def band_for(score: int) -> str:
    if score >= 75:
        return "Strong"
    if score >= 50:
        return "Moderate"
    return "Weak"


def compute_fit(judgments: list[RequirementJudgment]) -> FitResult:
    """Pure arithmetic: same inputs always give the same score and top gap."""

    if not judgments:
        return FitResult(score=0, band=band_for(0), per_requirement=(), top_gap=None)

    scored: list[RequirementScore] = []
    weighted_total = 0.0
    weight_sum = 0

    for judgment in judgments:
        if judgment.coverage != "not_shown" and not judgment.evidence_refs:
            raise ValueError(
                f"Requirement {judgment.requirement!r} is marked {judgment.coverage} "
                "but cites no evidence. Claims without evidence are rejected."
            )
        weight_value = WEIGHTS[judgment.weight]
        coverage_value = COVERAGE[judgment.coverage]
        contribution = weight_value * coverage_value
        gap = weight_value * (1.0 - coverage_value) * (1.0 if judgment.mandatory else 0.8)
        weighted_total += contribution
        weight_sum += weight_value
        scored.append(
            RequirementScore(
                requirement=judgment.requirement,
                weight=judgment.weight,
                weight_value=weight_value,
                coverage=judgment.coverage,
                coverage_value=coverage_value,
                contribution=contribution,
                gap=gap,
                mandatory=judgment.mandatory,
                evidence_refs=judgment.evidence_refs,
                explanation=judgment.explanation,
            )
        )

    score = int(round(100 * weighted_total / weight_sum)) if weight_sum else 0
    gaps = [item for item in scored if item.gap > 0]
    top_gap = max(gaps, key=lambda item: (item.gap, item.weight_value)).requirement if gaps else None
    refs = tuple(sorted({ref for item in scored for ref in item.evidence_refs}))
    return FitResult(score=score, band=band_for(score), per_requirement=tuple(scored), top_gap=top_gap, refs=refs)


# ---------------------------------------------------------------------------
# Deterministic judge: used when no model judgement is supplied.
# ---------------------------------------------------------------------------

_STOP = {"and", "or", "the", "of", "with", "in", "for", "a", "an", "to", "basic", "basics", "knowledge"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9+#]+", text.lower()) if t and t not in _STOP}


def skill_matches(requirement: str, skill_name: str) -> bool:
    req = requirement.lower().strip()
    name = skill_name.lower().strip()
    if not req or not name:
        return False
    if req == name or req in name or name in req:
        return True
    overlap = _tokens(req) & _tokens(name)
    return bool(overlap) and len(overlap) >= max(1, min(len(_tokens(req)), len(_tokens(name))) // 2)


def judge_from_skills(
    requirements: list[dict],
    skills: list[dict],
) -> list[RequirementJudgment]:
    """Judge requirements from the skill store.

    ``skills`` items look like ``{"name", "level", "ref", "evidence_refs": [...]}``.
    A skill with evidence at intermediate level or above is *demonstrated*;
    a skill with evidence below that is *partial*; a skill without evidence
    is a bare claim and counts as *not_shown* (evidence over assertion).
    Every non-zero coverage cites the evidence refs that justify it.
    """

    judgments: list[RequirementJudgment] = []
    for requirement in requirements:
        name = requirement.get("name") or requirement.get("skill_name") or ""
        weight = normalize_weight(requirement.get("weight") or requirement.get("importance"))
        mandatory = bool(requirement.get("mandatory", requirement.get("is_mandatory", False)))
        best: dict | None = None
        for skill in skills:
            if skill_matches(name, skill.get("name", "")):
                if best is None or LEVEL_ORDER.index(skill.get("level", "beginner")) > LEVEL_ORDER.index(best.get("level", "beginner")):
                    best = skill
        if best is None:
            judgments.append(
                RequirementJudgment(requirement=name, weight=weight, mandatory=mandatory, explanation="Not demonstrated in the profile.")
            )
            continue
        evidence_refs = tuple(best.get("evidence_refs") or [])
        level = best.get("level", "beginner")
        level_index = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 1
        if not evidence_refs:
            # Evidence over assertion: a skill listed without evidence is a bare claim.
            judgments.append(
                RequirementJudgment(
                    requirement=name,
                    weight=weight,
                    mandatory=mandatory,
                    explanation=f"{best['name']} is listed at {level} level but has no evidence yet, so it does not count.",
                )
            )
            continue
        if level_index >= LEVEL_ORDER.index("intermediate"):
            coverage = "demonstrated"
            explanation = f"{best['name']} at {level} level with evidence."
        else:
            coverage = "partial"
            explanation = f"{best['name']} at {level} level with evidence; more depth needed."
        judgments.append(
            RequirementJudgment(
                requirement=name,
                weight=weight,
                coverage=coverage,
                evidence_refs=evidence_refs,
                mandatory=mandatory,
                explanation=explanation,
            )
        )
    return judgments


def judgments_from_ai_assessment(assessment: dict, requirements: list[dict], skills: list[dict]) -> list[RequirementJudgment]:
    """Convert the Fit Agent's output (app/schemas/fit.py) into judgements.

    The model decides match / partial / missing; the code attaches evidence
    refs from the skill store and refuses coverage claims it cannot back.
    """

    status_by_name: dict[str, str] = {}
    explanation_by_name: dict[str, str] = {}
    for key, coverage in (("matching_skills", "demonstrated"), ("partial_matches", "partial"), ("missing_skills", "not_shown")):
        for entry in assessment.get(key, []) or []:
            skill_name = str(entry.get("skill_name", "")).strip().lower()
            if skill_name:
                status_by_name[skill_name] = coverage
                explanation_by_name[skill_name] = str(entry.get("explanation", "") or "")

    judgments: list[RequirementJudgment] = []
    deterministic = {j.requirement.lower(): j for j in judge_from_skills(requirements, skills)}
    for requirement in requirements:
        name = requirement.get("name") or requirement.get("skill_name") or ""
        key = name.strip().lower()
        base = deterministic.get(key)
        coverage = status_by_name.get(key, base.coverage if base else "not_shown")
        refs = base.evidence_refs if base else ()
        if coverage != "not_shown" and not refs:
            coverage = "not_shown"  # the model claimed coverage with no evidence in memory
        judgments.append(
            RequirementJudgment(
                requirement=name,
                weight=normalize_weight(requirement.get("weight") or requirement.get("importance")),
                coverage=coverage,
                evidence_refs=refs,
                mandatory=bool(requirement.get("mandatory", requirement.get("is_mandatory", False))),
                explanation=explanation_by_name.get(key) or (base.explanation if base else ""),
            )
        )
    return judgments
