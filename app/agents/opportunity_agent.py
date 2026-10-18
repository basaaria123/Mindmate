from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.opportunity import OpportunitySpec
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response


def extract_opportunity(opportunity_text: str) -> OpportunitySpec:
    """
    Extract structured information from an opportunity description.

    If the model returns invalid JSON or data that fails schema
    validation, retry the request once with a correction prompt.
    """

    client = create_llm_client()
    model = get_model("fast")

    prompt = f"""
You are MindMate's Opportunity Agent.

Analyze the opportunity description below and extract its details.

Return ONLY a valid JSON object with these fields:

{{
    "opportunity_title": "Title of the opportunity",
    "organization": "Organization name or null",
    "opportunity_type": "job, internship, hackathon, or other",
    "required_skills": [
        {{
            "skill_name": "Name of the skill",
            "importance": "High, Medium, or Low",
            "is_mandatory": true,
            "description": "Why or how this skill is required"
        }}
    ],
    "preferred_skills": ["Additional desirable skills"],
    "experience_level": "Beginner, Intermediate, Experienced, or Not specified",
    "summary": "A short summary of the opportunity"
}}

Rules:
1. Extract information only from the provided description.
2. Do not invent skills, qualifications, or experience requirements.
3. Mark a skill as mandatory only when the description explicitly
   states that it is required or mandatory.
4. Use High, Medium, or Low for skill importance.
5. If the organization is not mentioned, use null.
6. If the experience level is unclear, use "Not specified".
7. If preferred skills are not mentioned, return an empty list.
8. Return valid JSON only. Do not include Markdown or explanations.

Opportunity description:
{opportunity_text}
"""

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You extract opportunity details into structured JSON. "
                "Follow the requested JSON structure exactly."
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
                    "The Opportunity Agent returned an empty response."
                )

            opportunity_data = parse_json_response(response_text)

            return OpportunitySpec.model_validate(opportunity_data)

        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "The Opportunity Agent failed to return valid "
                    "opportunity data after one retry."
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
                        "Your previous response was invalid. "
                        "Correct the JSON and ensure every field "
                        "matches the required schema. Return only "
                        "the corrected JSON object. "
                        f"Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Opportunity Agent.")