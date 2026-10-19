
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.fit import FitAssessment
from app.schemas.gap import GapVectorJSON
from app.schemas.opportunity import OpportunitySpec
from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt


def identify_skill_gaps(
    user_profile: UserProfile,
    opportunity: OpportunitySpec,
    fit_assessment: FitAssessment,
) -> GapVectorJSON:
    """Identify and rank career-relevant skill gaps."""

    client = create_llm_client()
    model = get_model("reasoning")

    prompt = render_prompt(
        "gap",
        profile=user_profile.model_dump(),
        opportunity=opportunity.model_dump(),
        fit_assessment=fit_assessment.model_dump(),
    )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                load_prompt("gap.system")
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

        except ValueError as error:
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
