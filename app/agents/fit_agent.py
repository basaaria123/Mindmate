from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.fit import FitAssessment
from app.schemas.opportunity import OpportunitySpec
from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt


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

    prompt = render_prompt(
        "fit",
        profile=profile_data,
        opportunity=opportunity_data,
    )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                load_prompt("fit.system")
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

        except ValueError as error:
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