import json

from app.schemas.profile import UserProfile
from app.services.llm_client import create_llm_client, get_model


def extract_user_profile(user_message: str) -> UserProfile:
    """Extract a structured user profile from a natural-language message."""

    client = create_llm_client()
    model = get_model("fast")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
You are MindMate's Profile Extraction Agent.

Extract information explicitly stated by the user.

Rules:
1. Do not invent personal information.
2. If education is not mentioned, use "Not specified".
3. If goals, skills, interests, or learning preferences are not mentioned,
   return an empty list for those fields.
4. If daily available time is not mentioned, return null.
5. Convert time into minutes. For example, one hour is 60 minutes.
6. Return only valid JSON matching the requested fields.
""",
            },
            {
                "role": "user",
                "content": f"""
Extract the profile from this message:

{user_message}

Return a JSON object with exactly these fields:
- education: string
- goals: list of strings
- skills: list of strings
- interests: list of strings
- daily_available_minutes: integer or null
- learning_preferences: list of strings
""",
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=500,
    )

    response_text = response.choices[0].message.content

    if not response_text:
        raise ValueError("The AI returned an empty response.")

    profile_data = json.loads(response_text)

    return UserProfile.model_validate(profile_data)