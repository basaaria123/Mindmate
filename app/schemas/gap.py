
from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    skill_name: str = Field(
        description="The target skill where a gap has been identified."
    )

    career_impact_score: int = Field(
        ge=0,
        le=100,
        description="Career impact score from 0 to 100."
    )

    gap_type: str = Field(
        description=(
            "Whether the gap concerns missing skills, "
            "partial skills, or missing supporting evidence."
        )
    )

    missing_evidence: str = Field(
        description=(
            "What evidence is missing or insufficient to "
            "demonstrate this skill."
        )
    )

    rationale: str = Field(
        description="Why this gap matters for the target opportunity."
    )

    recommended_focus: str = Field(
        description="A specific learning or practice focus for this gap."
    )

    evidence_refs: list[str] = Field(
        default_factory=list,
        description=(
            "Existing evidence reference IDs supporting this assessment. "
            "Never invent reference IDs."
        )
    )



class GapVectorJSON(BaseModel):
    opportunity_title: str = Field(
        description="The target opportunity being assessed."
    )

    gaps: list[SkillGap] = Field(
        description=(
            "Skill gaps ranked from highest to lowest career impact."
        )
    )
