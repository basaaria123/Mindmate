from pydantic import ValidationError

from app.schemas.fit import FitAssessment
from app.schemas.opportunity import OpportunitySpec
from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response


def assess_fit(
    user_profile: UserProfile,
    opportunity: OpportunitySpec,
) -> FitAssessment:
    """
    Compare a user's profile with an opportunity and return
    a structured fit assessment.
    """

    client = create_llm_client()
    model = get_model("reasoning")

    profile_data = user_profile.model_dump()
    opportunity_data = opportunity.model_dump()

    prompt = f"""
You are MindMate's Fit Agent.

Compare the user's profile with the opportunity requirements.

USER PROFILE:
{profile_data}

OPPORTUNITY:
{opportunity_data}

Return ONLY a valid JSON object with these fields:

{{
    "opportunity_title": "Title of the opportunity",
    "overall_fit": "Strong, Moderate, or Low",
    "matching_skills": [
        {{
            "skill_name": "Skill name",
            "user_level": "Level supported by the profile",
            "required_level": "Expected level or Not specified",
            "match_status": "Match",
            "explanation": "Evidence-based explanation"
        }}
    ],
    "partial_matches": [
        {{
            "skill_name": "Skill name",
            "user_level": "Level supported by the profile",
            "required_level": "Expected level or Not specified",
            "match_status": "Partial match",
            "explanation": "Explain what matches and what needs improvement"
        }}
    ],
    "missing_skills": [
        {{
            "skill_name": "Skill name",
            "user_level": "Not demonstrated",
            "required_level": "Expected level or Not specified",
            "match_status": "Missing",
            "explanation": "Explain that the profile does not demonstrate this skill"
        }}
    ],
    "strengths": [
        "Evidence-based strength relevant to the opportunity"
    ],
    "improvement_areas": [
        "Specific area the user could improve"
    ],
    "summary": "Concise explanation of the user's fit"
}}

RULES:
1. Use only information supported by the profile and opportunity.
2. Do not invent skills, experience, qualifications, or proficiency levels.
3. Do not assume the user is proficient in a skill just because it
   appears in their profile.
4. A skill absent from the profile is "Not demonstrated", not proof
   that the user does not possess it.
5. Distinguish required skills from preferred skills.
6. Avoid unnecessary duplication between skill categories.
7. Explain uncertainty when there is insufficient evidence.
8. Return valid JSON only, without Markdown or extra explanations.
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are MindMate's career-fit assessment agent. "
                "Follow the requested JSON structure and do not invent "
                "information about the user."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
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
                    "The Fit Agent returned an empty response."
                )

            assessment_data = parse_json_response(response_text)

            return FitAssessment.model_validate(assessment_data)

        except (ValueError, ValidationError) as error:
            if attempt == 1:
                raise ValueError(
                    "The Fit Agent could not return valid assessment "
                    "data after one retry."
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
                        "Your previous response was invalid. Correct "
                        "the JSON so it matches the required schema. "
                        "Return only the corrected JSON object. "
                        f"Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Fit Agent.")