from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):

    role: str = Field(description="Message author role.")
    content: str = Field(description="Message content.")


class ChatRequest(BaseModel):

    message: str = Field(description="User message.")
    conversation: list[ConversationMessage] = Field(
        default_factory=list,
        description="Prior conversation messages.",
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
