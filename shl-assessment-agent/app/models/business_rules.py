from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DecisionType(StrEnum):

    ASK_CLARIFICATION = "ask_clarification"
    RECOMMEND = "recommend"
    UPDATE_RECOMMENDATIONS = "update_recommendations"
    REFUSE = "refuse"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class ClarificationRequest(BaseModel):

    question: str = Field(description="Clarification question to ask.")
    missing_field: str = Field(description="Missing field the question addresses.")
    reason: str = Field(description="Reason this clarification is needed.")


class RuleEvaluation(BaseModel):

    rule_name: str = Field(description="Stable rule identifier.")
    matched: bool = Field(description="Whether the rule matched.")
    reason: str = Field(description="Human-readable evaluation reason.")


class DecisionContext(BaseModel):

    latest_user_message: str | None = Field(
        default=None,
        description="Latest user message considered by the rule engine.",
    )
    turn_count: int = Field(default=0, ge=0, description="Conversation turn count.")
    has_previous_recommendations: bool = Field(
        default=False,
        description="Whether recommendation history exists.",
    )
    has_catalog_candidates: bool = Field(
        default=False,
        description="Whether retrieval returned candidate assessments.",
    )
    user_answered_previous_clarification: bool = Field(
        default=False,
        description="Whether the latest user message answered an open clarification.",
    )
    is_comparison_request: bool = Field(
        default=False,
        description="Whether the user is asking to compare assessments.",
    )
    is_update_request: bool = Field(
        default=False,
        description="Whether the user is modifying an existing shortlist.",
    )
    is_confirmation: bool = Field(
        default=False,
        description="Whether the user appears to confirm the current shortlist.",
    )
    is_out_of_scope: bool = Field(
        default=False,
        description="Whether the latest user request is outside SHL assessment scope.",
    )


class CatalogQueryResult(BaseModel):

    candidate_count: int = Field(
        default=0,
        ge=0,
        description="Number of candidate assessments returned by retrieval.",
    )
    candidate_ids: list[str] = Field(
        default_factory=list,
        description="Candidate assessment identifiers returned by retrieval.",
    )
    top_score: float | None = Field(
        default=None,
        ge=0.0,
        description="Top retrieval score, when available.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional retrieval metadata.",
    )

    model_config = ConfigDict(extra="allow")


class ConversationDecision(BaseModel):

    decision_type: DecisionType = Field(description="Selected next action.")
    context: DecisionContext = Field(description="Derived decision context.")
    clarification_request: ClarificationRequest | None = Field(
        default=None,
        description="Clarification to ask when the decision requires one.",
    )
    rule_evaluations: list[RuleEvaluation] = Field(
        default_factory=list,
        description="Rule evaluations that led to the selected decision.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional decision metadata.",
    )

    model_config = ConfigDict(extra="allow")
