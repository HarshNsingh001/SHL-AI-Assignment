from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ConversationMessageRole(StrEnum):

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(BaseModel):

    role: ConversationMessageRole = Field(description="Message author role.")
    content: str = Field(description="Message content.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time the message was recorded.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional message metadata.",
    )

    model_config = ConfigDict(extra="allow")


class ConversationPreference(BaseModel):

    name: str = Field(description="Preference name.")
    value: str | int | float | bool | list[str] | None = Field(
        default=None,
        description="Preference value.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional preference metadata.",
    )

    model_config = ConfigDict(extra="allow")


class ConversationConstraints(BaseModel):

    duration_minutes: int | None = Field(
        default=None,
        ge=0,
        description="Maximum assessment duration in minutes.",
    )
    remote_required: bool | None = Field(
        default=None,
        description="Whether remote support is required.",
    )
    adaptive_required: bool | None = Field(
        default=None,
        description="Whether adaptive support is required.",
    )
    languages: list[str] = Field(
        default_factory=list,
        description="Required assessment languages.",
    )
    assessment_types: list[str] = Field(
        default_factory=list,
        description="Requested assessment types.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional constraint metadata.",
    )

    model_config = ConfigDict(extra="allow")


class ConversationContext(BaseModel):

    current_role: str | None = Field(
        default=None,
        description="Current role under discussion.",
    )
    industry: str | None = Field(
        default=None,
        description="Industry under discussion.",
    )
    experience_level: str | None = Field(
        default=None,
        description="Candidate or role experience level.",
    )
    job_level: str | None = Field(
        default=None,
        description="Job level under discussion.",
    )
    languages: list[str] = Field(
        default_factory=list,
        description="Languages mentioned in the conversation.",
    )
    assessment_types_requested: list[str] = Field(
        default_factory=list,
        description="Assessment types requested by the user.",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills mentioned as requirements.",
    )
    required_competencies: list[str] = Field(
        default_factory=list,
        description="Competencies mentioned as requirements.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context metadata.",
    )

    model_config = ConfigDict(extra="allow")


class RecommendationRecord(BaseModel):

    assessment_ids: list[str] = Field(
        default_factory=list,
        description="Recommended assessment identifiers.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time the recommendation record was created.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional recommendation metadata.",
    )

    model_config = ConfigDict(extra="allow")


class RecommendationHistory(BaseModel):

    records: list[RecommendationRecord] = Field(
        default_factory=list,
        description="Recommendation history records.",
    )


class ClarificationRecord(BaseModel):

    question: str = Field(description="Clarification question.")
    answer: str | None = Field(
        default=None,
        description="User answer to the clarification question.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time the clarification record was created.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional clarification metadata.",
    )

    model_config = ConfigDict(extra="allow")


class ClarificationHistory(BaseModel):

    records: list[ClarificationRecord] = Field(
        default_factory=list,
        description="Clarification history records.",
    )


class ConversationState(BaseModel):

    conversation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Stable conversation identifier.",
    )
    messages: list[ConversationMessage] = Field(
        default_factory=list,
        description="Messages recorded for the conversation.",
    )
    context: ConversationContext = Field(
        default_factory=ConversationContext,
        description="Current conversation context.",
    )
    constraints: ConversationConstraints = Field(
        default_factory=ConversationConstraints,
        description="Current conversation constraints.",
    )
    preferences: list[ConversationPreference] = Field(
        default_factory=list,
        description="Preferences recorded from the user.",
    )
    recommendation_history: RecommendationHistory = Field(
        default_factory=RecommendationHistory,
        description="History of assessments already recommended.",
    )
    clarification_history: ClarificationHistory = Field(
        default_factory=ClarificationHistory,
        description="History of clarification questions.",
    )
    current_clarification_question: str | None = Field(
        default=None,
        description="Current open clarification question.",
    )
    user_answers: dict[str, str] = Field(
        default_factory=dict,
        description="User answers keyed by question or field name.",
    )
    recommended_assessment_ids: list[str] = Field(
        default_factory=list,
        description="Assessment identifiers already recommended.",
    )
    conversation_summary: str | None = Field(
        default=None,
        description="Human-readable conversation summary.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional conversation metadata.",
    )

    model_config = ConfigDict(extra="allow")
