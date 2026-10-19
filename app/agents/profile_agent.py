from openai.types.chat import ChatCompletionMessageParam

from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt


def extract_user_profile(user_message: str) -> UserProfile:
    """Extract a structured user profile from a natural-language message.

    Like the other agents, an invalid or off-schema reply is retried once with
    the validation error, then rejected with a ValueError.
    """

    client = create_llm_client()
    model = get_model("fast")

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": load_prompt("profile.system")},
        {"role": "user", "content": render_prompt("profile", user_message=user_message)},
    ]

    for attempt in range(2):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=1000,
        )

        response_text = response.choices[0].message.content

        try:
            if not response_text:
                raise ValueError("The Profile Agent returned an empty response.")

            profile_data = parse_json_response(response_text)
            return UserProfile.model_validate(profile_data)

        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "The Profile Agent could not return a valid profile after one retry."
                ) from error

            messages.append({"role": "assistant", "content": response_text or ""})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response was invalid. Return only the corrected "
                        "JSON object with exactly the requested fields. "
                        f"Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Profile Agent.")
