
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.practice import PracticeEvaluation
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response


def evaluate_practice(
    question: str,
    user_answer: str,
    topic: str,
) -> PracticeEvaluation:
    """Evaluate a practice answer and return structured feedback."""

    client = create_llm_client()
    model = get_model("reasoning")

    prompt = f"""
You are MindMate's Practice Agent.

Evaluate the user's answer to a practice question.

TOPIC:
{topic}

QUESTION:
{question}

USER ANSWER:
{user_answer}

Return ONLY a JSON object with this structure:
{{
  "correctness": 80,
  "depth": 70,
  "clarity": 85,
  "feedback": "Explain what is correct and what needs improvement.",
  "weakness_candidate": "A specific weakness, or null if none is supported.",
  "is_store_worthy": true,
  "memory_tag": "weakness, or null if the result should not be stored."
}}

RULES:
1. Score correctness, depth, and clarity independently from 0 to 100.
2. Correctness measures factual and technical accuracy.
3. Depth measures completeness and quality of reasoning.
4. Clarity measures how understandable and well-organized the answer is.
5. Give specific, constructive feedback grounded in the answer.
6. Identify a weakness only when the answer provides evidence for it.
7. Do not treat a missing detail as proof that the user lacks a skill.
8. Set is_store_worthy to true only when the result contains a useful,
   supported learning insight that could help future personalization.
9. If is_store_worthy is false, set memory_tag to null.
10. Do not invent memory IDs or claim that anything has been saved.
11. Return valid JSON only, without Markdown.
"""

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are MindMate's Practice Agent. "
                "Evaluate fairly and constructively. "
                "Return only valid JSON matching the requested schema."
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
                    "The Practice Agent returned an empty response."
                )

            evaluation_data = parse_json_response(response_text)
            evaluation = PracticeEvaluation.model_validate(evaluation_data)

            if not evaluation.is_store_worthy and evaluation.memory_tag is not None:
                raise ValueError(
                    "memory_tag must be null when is_store_worthy is false."
                )

            return evaluation

        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "The Practice Agent could not return valid data after one retry."
                ) from error

            messages.append(
                {"role": "assistant", "content": response_text or ""}
            )
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Correct your previous JSON response to match the schema "
                        "and every rule. Return only JSON. "
                        f"Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Practice Agent.")
