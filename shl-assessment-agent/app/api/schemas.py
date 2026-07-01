from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):

    role: str = Field(
        description="Message author role.  One of 'user' or 'assistant'.",
    )
    content: str = Field(
        description="Raw text of the message.",
    )


class ChatRequest(BaseModel):

    messages: list[ConversationTurn] = Field(
        description="Full conversation history ending with the latest user message.",
        min_length=1,
    )


class RecommendationItem(BaseModel):

    id: str = Field(description="Stable catalog assessment identifier.")
    name: str = Field(description="Human-readable assessment name.")
    url: str = Field(description="Canonical SHL catalog URL.")
    test_type: str = Field(description="Assessment test-type code.")
    keys: list[str] = Field(
        default_factory=list,
        description="Searchable category labels.",
    )
    duration: int | None = Field(
        default=None,
        description="Duration in minutes, or null when untimed.",
    )
    languages: list[str] = Field(
        default_factory=list,
        description="Languages supported by the assessment.",
    )
    remote_support: bool = Field(
        default=False,
        description="Whether the assessment supports remote administration.",
    )
    adaptive_support: bool = Field(
        default=False,
        description="Whether the assessment supports adaptive testing.",
    )
    description: str = Field(
        default="",
        description="Short assessment description.",
    )


class ChatResponse(BaseModel):

    reply: str = Field(
        description="Assistant reply text ready to display to the user.",
    )
    recommendations: list[RecommendationItem] = Field(
        default_factory=list,
        description=(
            "Ordered list of recommended assessments.  Empty when the current "
            "turn does not produce recommendations."
        ),
    )
    end_of_conversation: bool = Field(
        default=False,
        description=(
            "true when the pipeline has produced a final confirmed shortlist "
            "and the conversation is complete."
        ),
    )
