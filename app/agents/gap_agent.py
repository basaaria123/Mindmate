
from pydantic import ValidationError

from app.schemas.fit import FitAssessment
from app.schemas.gap import GapVectorJSON
from app.schemas.opportunity import OpportunitySpec
from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response


def identify_skill_gaps(
    user_profile: UserProfile,
    opportunity: OpportunitySpec,
    fit_assessment: FitAssessment,
) -> GapVectorJSON:
    """Identify and rank career-relevant skill gaps."""

    client = create_llm_client()
    model = get_model("reasoning")

    prompt = f"""
You are MindMate's Skill Gap Agent.

Identify and rank the user's skill gaps for the target opportunity.

USER PROFILE:
{user_profile.model_dump()}

OPPORTUNITY:
{opportunity.model_dump()}

EXISTING FIT ASSESSMENT:
{fit_assessment.model_dump()}

Return ONLY a valid JSON object with this structure:
{{
    "opportunity_title": "Target opportunity title",
    "gaps": [
        {{
            "skill_name": "Skill name",
            "career_impact_score": 80,
            "gap_type": "missing_skill",
            "missing_evidence": "Evidence not demonstrated in the profile",
            "rationale": "Why this gap matters for the opportunity",
            "recommended_focus": "Specific learning or practice focus",
            "evidence_refs": []
        }}
    ]
}}

RULES:
1. Rank gaps from highest to lowest career impact.
2. Use only information supported by the profile, opportunity,
   and fit assessment.
3. Do not invent skills, qualifications, evidence, or reference IDs.
4. Treat an absent skill as not demonstrated, not proof the user
   does not possess it.
5. Use career_impact_score as an integer from 0 to 100.
6. Use existing evidence reference IDs only when they are actually
   present in the supplied context. Do not fabricate IDs.
7. Include relevant missing skills, partial matches, and evidence gaps.
8. If no gaps are supported by the input, return an empty gaps list.
9. Return valid JSON only, without Markdown.
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are MindMate's Skill Gap Agent. "
                "Return only JSON matching the requested schema. "
                "Never invent user evidence or reference IDs."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    for attempt in range(2):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )

        response_text = response.choices[0].message.content

        try:
            if not response_text:
                raise ValueError(
                    "The Skill Gap Agent returned an empty response."
                )

            gap_data = parse_json_response(response_text)
            return GapVectorJSON.model_validate(gap_data)

        except (ValueError, ValidationError) as error:
            if attempt == 1:
                raise ValueError(
                    "The Skill Gap Agent could not return valid data "
                    "after one retry."
                ) from error

            messages.append(
                {
                    "role": "assistant",
                    "content": response_text or "",
                }
            )
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Correct your previous JSON response so it "
                        "matches the required schema. Return only JSON. "
                        f"Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Skill Gap Agent.")
