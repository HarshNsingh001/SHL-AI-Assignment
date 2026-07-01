from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):

    role: str = Field(description="Message author role.")
    content: str = Field(description="Message content.")


class ChatRequest(BaseModel):

    messages: list[ConversationMessage] = Field(
        description="Full conversation history ending with the latest user message.",
        min_length=1,
    )


class Recommendation(BaseModel):

    identifier: str = Field(description="Recommendation identifier.")
    title: str = Field(description="Recommendation title.")
    rationale: str | None = Field(
        default=None,
        description="Optional recommendation rationale.",
    )


class ChatResponse(BaseModel):

    message: str = Field(description="Assistant response message.")
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Recommendations returned by the agent.",
    )
