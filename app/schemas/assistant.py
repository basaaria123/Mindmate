from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AssistantReply(BaseModel):
    reply: str = Field(min_length=1, description="The assistant's answer in plain text.")
    model: str = Field(description="The Nemotron model that produced the answer.")
