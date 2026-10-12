import json


def parse_json_response(response_text: str) -> dict:
    """
    Parse a JSON response returned by an AI model.

    Raises ValueError if the response is not valid JSON.
    """

    cleaned_text = response_text.strip()

    # Remove Markdown code fences if the model includes them.
    if cleaned_text.startswith("```"):
        lines = cleaned_text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned_text = "\n".join(lines).strip()

    try:
        result = json.loads(cleaned_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            "The AI model returned invalid JSON."
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "The AI model response must be a JSON object."
        )

    return result