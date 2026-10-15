
from pydantic import BaseModel, Field, model_validator


class OpportunitySuggestion(BaseModel):
    """One personalized opportunity recommendation."""

    title: str = Field(
        min_length=1,
        description="A concise title for the recommended opportunity.",
    )

    organization: str | None = Field(
        default=None,
        description="Organization name, or null if not known.",
    )

    opportunity_type: str = Field(
        description="Job, internship, project, or learning resource.",
    )

    category: str = Field(
        description="Jobs, Projects, Resources, or Other.",
    )

    explanation: str = Field(
        min_length=1,
        description="Why this suggestion is relevant to the user's profile.",
    )


class SuggestionsResponse(BaseModel):
    """The twelve personalized suggestions returned by MindMate."""

    suggestions: list[OpportunitySuggestion] = Field(
        min_length=12,
        max_length=12,
        description="Exactly twelve personalized suggestions: three per category.",
    )

    @model_validator(mode="after")
    def validate_category_counts(self):
        required_categories = ["Jobs", "Projects", "Resources", "Other"]

        for category in required_categories:
            count = sum(
                suggestion.category == category
                for suggestion in self.suggestions
            )

            if count != 3:
                raise ValueError(
                    f"Expected exactly 3 suggestions for {category}, got {count}."
                )

        return self
