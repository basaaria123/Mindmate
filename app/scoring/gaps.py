"""Gap scoring: rank what to fix first for a target opportunity.

    gap_impact = weight(req) x (1 - coverage) x (1.0 if mandatory else 0.8)
    weakness tie-in: an active weakness on the same topic adds +0.5

The output lists gaps from highest to lowest impact with the references
(evidence, skills, weaknesses) that justify each entry.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.scoring.fit import FitResult, skill_matches


@dataclass(frozen=True)
class Gap:
    requirement: str
    impact: float
    impact_score: int  # 0-100
    weight: str
    coverage: str
    mandatory: bool
    refs: tuple[str, ...]
    rationale: str
    recommended_focus: str

    def as_dict(self) -> dict:
        return {
            "requirement": self.requirement,
            "impact": round(self.impact, 3),
            "impact_score": self.impact_score,
            "weight": self.weight,
            "coverage": self.coverage,
            "mandatory": self.mandatory,
            "refs": list(self.refs),
            "rationale": self.rationale,
            "recommended_focus": self.recommended_focus,
        }


def rank_gaps(fit: FitResult, weaknesses: list[dict] | None = None) -> list[Gap]:
    weaknesses = weaknesses or []
    max_impact = 3.0 + 0.5  # High weight, fully missing, mandatory, plus weakness boost
    gaps: list[Gap] = []
    for item in fit.per_requirement:
        if item.gap <= 0:
            continue
        impact = item.gap
        refs = list(item.evidence_refs)
        rationale_parts = [
            f"{item.weight} weight requirement is {item.coverage.replace('_', ' ')}"
            + (" and mandatory" if item.mandatory else "")
            + "."
        ]
        for weakness in weaknesses:
            if skill_matches(item.requirement, weakness.get("topic", "")):
                impact += 0.5
                refs.append(weakness["ref"])
                rationale_parts.append(
                    f"Practice shows a {weakness.get('severity')} weakness on {weakness.get('topic')} [{weakness['ref']}]."
                )
        focus = (
            f"Build demonstrable evidence for {item.requirement}"
            if item.coverage == "not_shown"
            else f"Deepen {item.requirement} and document it with a project or practice result"
        )
        gaps.append(
            Gap(
                requirement=item.requirement,
                impact=impact,
                impact_score=int(round(100 * min(impact, max_impact) / max_impact)),
                weight=item.weight,
                coverage=item.coverage,
                mandatory=item.mandatory,
                refs=tuple(dict.fromkeys(refs)),
                rationale=" ".join(rationale_parts),
                recommended_focus=focus,
            )
        )
    gaps.sort(key=lambda gap: (-gap.impact, gap.requirement.lower()))
    return gaps
