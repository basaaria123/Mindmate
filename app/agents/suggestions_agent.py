
from pydantic import ValidationError

from app.schemas.profile import UserProfile
from app.schemas.suggestions import SuggestionsResponse
from app.services.llm_client import create_llm_client, get_model
from app.utils.json_utils import parse_json_response


def generate_suggestions(
    user_profile: UserProfile,
) -> SuggestionsResponse:
    """Generate exactly twelve personalized suggestions."""

    client = create_llm_client()
    model = get_model("fast")

    profile_data = user_profile.model_dump()

    prompt = f"""
You are MindMate's Personalized Suggestions Agent.

Recommend exactly TWELVE useful, distinct suggestions for this user:
exactly 3 in Jobs, 3 in Projects, 3 in Resources, and 3 in Other.

USER PROFILE:
{profile_data}

Return ONLY a valid JSON object in this structure:

{{
    "suggestions": [
        {{
            "title": "A concise suggestion title",
            "organization": null,
            "opportunity_type": "Internship",
            "category": "Jobs",
            "explanation": "Why this suggestion suits the user's profile"
        }},
        {{
            "title": "A practical project title",
            "organization": null,
            "opportunity_type": "Project",
            "category": "Projects",
            "explanation": "Why this project suits the user's profile"
        }},
        {{
            "title": "A useful learning resource",
            "organization": null,
            "opportunity_type": "Learning Resource",
            "category": "Resources",
            "explanation": "Why this resource suits the user's profile"
        }},
        {{
            "title": "A career-building activity",
            "organization": null,
            "opportunity_type": "Career Activity",
            "category": "Other",
            "explanation": "Why this activity suits the user's profile"
        }}
    ]
}}

The example shows the required structure and category values.
Your actual suggestions array MUST contain exactly 12 objects:
- Exactly 3 objects with category "Jobs".
- Exactly 3 objects with category "Projects".
- Exactly 3 objects with category "Resources".
- Exactly 3 objects with category "Other".

RULES:
1. Personalize every suggestion using the user's skills, education,
   goals, interests, available time, and learning preferences.
2. Suggest realistic, actionable options suitable for the user's
   apparent experience level.
3. For Jobs, recommend relevant job roles, internship search strategies,
   or entry-level career opportunities.
4. For Projects, recommend practical projects suited to the user's
   interests, programming skills, and AI-engineering goals.
5. For Resources, recommend relevant courses, documentation, tutorials,
   and structured learning activities.
6. For Other, recommend useful hackathons, portfolio activities,
   networking, career preparation, or similar opportunities.
7. Use only these category values: Jobs, Projects, Resources, Other.
8. Every category must contain exactly 3 suggestions.
9. Use a suitable opportunity_type, such as Job, Internship, Project,
   Learning Resource, Hackathon, Portfolio Activity, or Career Activity.
10. Set organization to null if no specific organization is known.
11. Do not invent real job vacancies, hiring status, deadlines,
    application links, or claims that an opportunity is available.
12. Recommendations must be distinct, actionable, and relevant.
13. Explain clearly why each suggestion suits the user's profile.
14. Return valid JSON only. Do not include Markdown or commentary.
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are MindMate's personalized recommendation agent. "
                "Return structured JSON with exactly 12 suggestions, "
                "three per required category. Never invent verified "
                "job openings or availability."
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

        except (ValueError, ValidationError) as error:
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
                        "Return only the corrected JSON object."
                    ),
                }
            )

    raise RuntimeError("Unexpected error in the Suggestions Agent.")
