
from typing import Literal

from pydantic import BaseModel, Field


class PracticeEvaluation(BaseModel):
    correctness: int = Field(
        ge=0,
        le=100,
        description="Score for the correctness of the user's answer."
    )

    depth: int = Field(
        ge=0,
        le=100,
        description="Score for depth and completeness of the answer."
    )

    clarity: int = Field(
        ge=0,
        le=100,
        description="Score for clarity and organization of the answer."
    )

    feedback: str = Field(
        description="Specific feedback explaining strengths and improvements."
    )

    weakness_candidate: str | None = Field(
        default=None,
        description="A potential weakness identified during practice, if any."
    )

    is_store_worthy: bool = Field(
        description="Whether this result is useful enough to save in memory."
    )

    memory_tag: str | None = Field(
        default=None,
        description="A suitable tag for a store-worthy memory, if applicable."
    )
