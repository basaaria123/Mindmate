from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.opportunity import OpportunitySpec
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt


def extract_opportunity(opportunity_text: str) -> OpportunitySpec:
    """
    Extract structured information from an opportunity description.

    If the model returns invalid JSON or data that fails schema
    validation, retry the request once with a correction prompt.
    """

    client = create_llm_client()
    model = get_model("fast")

    prompt = render_prompt(
        "opportunity",
        opportunity_text=opportunity_text,
    )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                load_prompt("opportunity.system")
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