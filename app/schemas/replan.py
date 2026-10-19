from pydantic import BaseModel, Field


class ReplanExplanation(BaseModel):
    """Plain-language explanation of a plan change, written by the Replanning agent."""

    summary: str = Field(
        min_length=20,
        max_length=1200,
        description="Two to four sentences: what moved and why, citing reference IDs in brackets.",
    )

    cited_refs: list[str] = Field(
        default_factory=list,
        description="Every reference ID cited in the summary. Must come from the supplied list.",
    )
