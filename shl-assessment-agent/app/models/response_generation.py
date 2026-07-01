from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.business_rules import DecisionType

class ReplyContext(BaseModel):

    decision_type: str = Field(
        description="DecisionType value that selected the reply template.",
    )
    recommendation_count: int = Field(
        default=0,
        ge=0,
        description="Number of assessment recommendations included in this reply.",
    )
    has_prior_recommendations: bool = Field(
        default=False,
        description="Whether prior recommendations existed before this turn.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question asked when the decision requires one.",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Constraint fields that remain unknown after extraction.",
    )
    conversation_turn: int = Field(
        default=0,
        ge=0,
        description="Zero-based index of the current conversation turn.",
    )
    role: str | None = Field(
        default=None,
        description="Extracted role name, when available.",
    )
    job_level: str | None = Field(
        default=None,
        description="Extracted job level, when available.",
    )
    industry: str | None = Field(
        default=None,
        description="Extracted industry, when available.",
    )

    model_config = ConfigDict(extra="allow")


class ResponseMetadata(BaseModel):

    template_key: str = Field(
        description="Stable identifier of the template that was selected.",
    )
    decision_type: str = Field(
        description="DecisionType value that drove template selection.",
    )
    includes_table: bool = Field(
        default=False,
        description="Whether the rendered reply includes a Markdown table.",
    )
    table_row_count: int = Field(
        default=0,
        ge=0,
        description="Number of data rows in the rendered Markdown table.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings from the response generation step.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata produced during rendering.",
    )

    model_config = ConfigDict(extra="allow")


class GeneratedReply(BaseModel):

    reply_text: str = Field(
        description="Full assistant reply text, ready to send to the user.",
    )
    table_markdown: str = Field(
        default="",
        description=(
            "The Markdown table portion of the reply. "
            "Empty string when no recommendations were rendered."
        ),
    )
    decision_type: str = Field(
        description="DecisionType value that was applied.",
    )
    context: ReplyContext = Field(
        description="Pipeline state snapshot used when rendering this reply.",
    )
    metadata: ResponseMetadata = Field(
        description="Operational metadata for this generation run.",
    )

    model_config = ConfigDict(extra="allow")

    @property
    def is_recommendation_reply(self) -> bool:
        return bool(self.table_markdown)

    @property
    def is_clarification_reply(self) -> bool:
        return self.decision_type == DecisionType.ASK_CLARIFICATION

    @property
    def is_refusal_reply(self) -> bool:
        return self.decision_type == DecisionType.REFUSE
