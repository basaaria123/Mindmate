from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.gap import GapVectorJSON
from app.schemas.opportunity import OpportunitySpec
from app.schemas.plan import PlanScheduleJSON
from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response
from app.utils.prompts import load_prompt, render_prompt


def generate_plan(
    user_profile: UserProfile,
    opportunity: OpportunitySpec,
    gap_vector: GapVectorJSON,
    goal_id: str,
    existing_decisions: list[str] | None = None,
    existing_memories: list[dict] | None = None,
) -> PlanScheduleJSON:
    """Generate a validated 14-day learning plan within the user's daily budget."""

    client = create_llm_client()
    model = get_model("reasoning")

    daily_budget = user_profile.daily_available_minutes
    decisions = existing_decisions or []
    memories = existing_memories or []

    prompt = render_prompt(
        "planner",
        profile=user_profile.model_dump(),
        opportunity=opportunity.model_dump(),
        gap_vector=gap_vector.model_dump(),
        goal_id=goal_id,
        decisions=decisions,
        memories=memories,
        daily_budget=daily_budget,
    )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                load_prompt("planner.system")
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
                raise ValueError("The Planner Agent returned an empty response.")

            plan_data = parse_json_response(response_text)
            plan = PlanScheduleJSON.model_validate(plan_data)

            if plan.goal_id != goal_id:
                raise ValueError("The returned goal_id does not match the requested goal.")

            if plan.daily_budget_minutes != daily_budget:
                raise ValueError(
                    "The returned daily budget does not match the user's budget."
                )

            # Collect valid references from stored memories.
            valid_refs = {
                memory["memory_id"]
                for memory in memories
                if memory.get("memory_id")
            }

            # Also allow references supplied by the Skill Gap Agent.
            valid_refs.update(
                ref
                for gap in gap_vector.gaps
                for ref in gap.evidence_refs
            )

            # Reject references that do not exist in the supplied data.
            invalid_refs = {
                ref
                for task in plan.schedule
                for ref in task.source_refs
                if ref not in valid_refs
            }

            if invalid_refs:
                raise ValueError(
                    "The plan contains unknown source references: "
                    f"{sorted(invalid_refs)}"
                )

            return plan

        
        except ValueError as error:
            if attempt == 1:
                raise ValueError(
                    f"The Planner Agent failed validation after one retry. "
                    f"Actual error: {error}"
                ) from error


            messages.append(
                {"role": "assistant", "content": response_text or ""}
            )
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Correct the previous JSON response. Return only JSON "
                        "matching the requested schema and all planning rules. "
                        f"Validation error: {error}"
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Planner Agent.")
