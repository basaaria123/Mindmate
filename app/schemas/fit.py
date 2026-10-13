from pydantic import BaseModel, Field


class SkillMatch(BaseModel):
    skill_name: str = Field(
        description="The skill being evaluated."
    )

    user_level: str = Field(
        description="The user's demonstrated level for this skill."
    )

    required_level: str = Field(
        description="The level expected by the opportunity, if specified."
    )

    match_status: str = Field(
        description="Whether the skill matches, partially matches, or is missing."
    )

    explanation: str = Field(
        description="Evidence-based explanation of the skill match."
    )


class FitAssessment(BaseModel):
    opportunity_title: str = Field(
        description="The title of the opportunity being evaluated."
    )

    overall_fit: str = Field(
        description="A qualitative assessment of the user's fit."
    )

    matching_skills: list[SkillMatch] = Field(
        description="Skills that match the opportunity requirements."
    )

    partial_matches: list[SkillMatch] = Field(
        description="Skills that partially match the requirements."
    )

    missing_skills: list[SkillMatch] = Field(
        description="Required skills the user has not demonstrated."
    )

    strengths: list[str] = Field(
        description="Evidence-based strengths relevant to the opportunity."
    )

    improvement_areas: list[str] = Field(
        description="Areas the user could improve to better match the opportunity."
    )

    summary: str = Field(
        description="A concise explanation of the overall fit assessment."
    )