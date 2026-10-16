
from typing import Literal

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    memory_id: str = Field(
        description="Stable identifier for this memory, such as weakness#04 or decision#01."
    )

    memory_type: Literal[
        "weakness",
        "decision",
        "learning_insight",
    ] = Field(
        description="Category of the stored memory."
    )

    content: str = Field(
        min_length=1,
        description="The supported insight or decision being remembered."
    )

    reference_tags: list[str] = Field(
        default_factory=list,
        description="Tags that help connect this memory to relevant context."
    )

    source: str = Field(
        min_length=1,
        description="Where the memory came from, such as a practice evaluation."
    )

    confidence: int = Field(
        ge=0,
        le=100,
        description="Confidence that the memory is supported by its source."
    )


class MemoryStoreRequest(BaseModel):
    items: list[MemoryItem] = Field(
        description="Memory items to validate for storage."
    )


class MemoryStoreResponse(BaseModel):
    stored_items: list[MemoryItem] = Field(
        description="Memory items accepted by the storage operation."
    )
