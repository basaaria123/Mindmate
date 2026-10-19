
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.profile import UserProfile
from app.schemas.suggestions import SuggestionsResponse
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt


def generate_suggestions(
    user_profile: UserProfile,
) -> SuggestionsResponse:
    """Generate exactly twelve personalized suggestions."""

    client = create_llm_client()
    model = get_model("fast")

    profile_data = user_profile.model_dump()

    prompt = render_prompt(
        "suggestions",
        profile=profile_data,
    )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                load_prompt("suggestions.system")
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
                    "The Suggestions Agent returned an empty response."
                )

            suggestions_data = parse_json_response(response_text)

            return SuggestionsResponse.model_validate(suggestions_data)

        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "The Suggestions Agent failed to return exactly "
                    "12 valid suggestions, with 3 per category, "
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
                        "Your previous response failed validation. "
                        "Correct the JSON and return exactly 12 distinct "
                        "suggestions: 3 Jobs, 3 Projects, 3 Resources, "
                        "and 3 Other. Follow the schema exactly. "
                        "Return only the corrected JSON object. "
                        f"Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Suggestions Agent.")
