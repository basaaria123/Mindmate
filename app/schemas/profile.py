from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Structured information extracted from a MindMate user's profile."""

    education: str = Field(
        description="The user's education or current academic level."
    )

    goals: list[str] = Field(
        description="The goals explicitly mentioned by the user."
    )

    skills: list[str] = Field(
        description="The skills the user says they already have."
    )

    interests: list[str] = Field(
        description="The user's explicitly mentioned interests."
    )

    daily_available_minutes: int | None = Field(
        default=None,
        ge=0,
        description="Minutes available per day, if specified."
    )

    learning_preferences: list[str] = Field(
        description="The user's stated learning preferences."
    )