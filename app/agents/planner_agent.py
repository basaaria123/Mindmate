from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.schemas.gap import GapVectorJSON
from app.schemas.opportunity import OpportunitySpec
from app.schemas.plan import PlanScheduleJSON
from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response


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

    prompt = f"""
You are MindMate's Planner Agent.

Create a practical 14-day plan to help the user prepare for the target opportunity.

USER PROFILE:
{user_profile.model_dump()}

TARGET OPPORTUNITY:
{opportunity.model_dump()}

RANKED SKILL GAPS:
{gap_vector.model_dump()}

GOAL ID:
{goal_id}

USER DECISIONS THAT MUST OVERRIDE GENERAL PREPARATION:
{decisions}

EXISTING STORED MEMORIES:
{memories}

DAILY TIME BUDGET:
{daily_budget} minutes maximum per day.

Return ONLY a JSON object in this structure:
{{
  "goal_id": "{goal_id}",
  "daily_budget_minutes": {daily_budget},
  "total_tasks": 2,
  "schedule": [
    {{
      "task_id": "task-01",
      "day_number": 1,
      "title": "Practice a priority skill",
      "duration_minutes": 30,
      "priority": "High",
      "why_it_matters": "Addresses a high-impact skill gap",
      "source_refs": []
    }}
  ]
}}

RULES:
1. Create a plan spanning the 14-day period. Tasks may be scheduled
   on any days from 1 through 14.
2. Never schedule more than {daily_budget} minutes on any day.
3. Include tasks addressing the highest-impact skill gaps within days 1-3.
4. Respect the user's existing decisions over generic preparation.
5. Prioritize gaps using career impact and the available evidence.
6. Use only supplied information. Do not invent user qualifications,
   evidence, or reference IDs.
7. Use unique task_id values.
8. Every task must have a positive duration.
9. priority must be High, Medium, or Low.
10. total_tasks must equal the number of tasks in schedule.
11. Include source_refs only when supported by existing reference IDs.
12. If no reference IDs are supplied, use an empty source_refs list.
13. Return valid JSON only, without Markdown.
"""

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are MindMate's Planner Agent. "
                "Return only valid JSON matching the requested schema. "
                "Respect the user's time budget and decisions."
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
