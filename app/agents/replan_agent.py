import re

from openai.types.chat import ChatCompletionMessageParam

from app.schemas.replan import ReplanExplanation
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt

REF_IN_TEXT = re.compile(r"\b[a-z_]+#\d+\b")


def explain_replan(changes: dict, allowed_refs: list[str]) -> ReplanExplanation:
    """Explain a plan change computed by deterministic code.

    The agent only words the explanation: it cannot change tasks, numbers or
    order. Any reference ID it mentions that is not in ``allowed_refs`` makes
    the reply invalid (retried once, then rejected), so it cannot cite memory
    that does not exist.
    """

    client = create_llm_client()
    model = get_model("reasoning")
    allowed = sorted(set(allowed_refs))

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": load_prompt("replan.system")},
        {"role": "user", "content": render_prompt("replan", changes=changes, allowed_refs=allowed)},
    ]

    for attempt in range(2):
        response = client.chat.completions.create(model=model, messages=messages, temperature=0)
        response_text = response.choices[0].message.content

        try:
            if not response_text:
                raise ValueError("The Replanning Agent returned an empty response.")

            explanation = ReplanExplanation.model_validate(parse_json_response(response_text))

            mentioned = set(REF_IN_TEXT.findall(explanation.summary))
            unknown = (mentioned | set(explanation.cited_refs)) - set(allowed)
            if unknown:
                raise ValueError(f"The explanation cites unknown references: {sorted(unknown)}")
            if allowed and not mentioned:
                raise ValueError("The explanation must cite at least one reference ID.")
            if mentioned != set(explanation.cited_refs):
                raise ValueError("cited_refs must list exactly the IDs cited in the summary.")

            return explanation

        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "The Replanning Agent could not return a valid explanation after one retry."
                ) from error

            messages.append({"role": "assistant", "content": response_text or ""})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Correct your previous JSON so it follows every rule. "
                        f"Return only JSON. Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Replanning Agent.")
