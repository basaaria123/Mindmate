
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.practice import PracticeEvaluation, PracticeQuestionSet
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt


def evaluate_practice(
    question: str,
    user_answer: str,
    topic: str,
) -> PracticeEvaluation:
    """Evaluate a practice answer and return structured feedback."""

    client = create_llm_client()
    model = get_model("reasoning")

    prompt = render_prompt(
        "practice",
        topic=topic,
        question=question,
        user_answer=user_answer,
    )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                load_prompt("practice.system")
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



def generate_practice_questions(
    target_role: str,
    skills: list[str],
    gaps: list[dict],
    weaknesses: list[dict],
    topic: str | None = None,
    count: int = 3,
    allowed_refs: list[str] | None = None,
) -> PracticeQuestionSet:
    """Generate mock-interview questions from the role, the learner's evidence, gaps and weaknesses.

    Every cited reference must come from ``allowed_refs``; otherwise the reply is
    retried once and then rejected.
    """

    if not 1 <= count <= 5:
        raise ValueError("count must be between 1 and 5.")

    client = create_llm_client()
    model = get_model("reasoning")
    allowed = sorted(set(allowed_refs or []))

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": load_prompt("practice_questions.system")},
        {
            "role": "user",
            "content": render_prompt(
                "practice_questions",
                count=count,
                target_role=target_role or "Not specified",
                topic=topic or "",
                skills=skills,
                gaps=gaps,
                weaknesses=weaknesses,
                allowed_refs=allowed,
            ),
        },
    ]

    for attempt in range(2):
        response = client.chat.completions.create(model=model, messages=messages, temperature=0)
        response_text = response.choices[0].message.content

        try:
            if not response_text:
                raise ValueError("The Practice Agent returned an empty response.")

            question_set = PracticeQuestionSet.model_validate(parse_json_response(response_text))

            unknown = {
                ref
                for question in question_set.questions
                for ref in question.source_refs
                if ref not in allowed
            }
            if unknown:
                raise ValueError(f"Questions cite unknown references: {sorted(unknown)}")

            if topic and any(topic.lower() not in q.topic.lower() for q in question_set.questions):
                raise ValueError(f"Every question must test the requested topic: {topic}")

            return question_set

        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    "The Practice Agent could not generate valid questions after one retry."
                ) from error

            messages.append({"role": "assistant", "content": response_text or ""})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Correct your previous JSON so it matches the schema and every rule. "
                        f"Return only JSON. Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Practice Agent.")
