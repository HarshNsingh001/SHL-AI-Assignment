from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.business_rules import ConversationDecision
from app.models.constraints import ConstraintExtractionResult
from app.models.conversation import ConversationState
from app.models.recommendation_engine import RecommendationResult


class ExecutionTrace(BaseModel):

    invoked_services: list[str] = Field(
        default_factory=list,
        description="Ordered list of service class names invoked by the pipeline.",
    )
    elapsed_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Wall-clock duration of the complete pipeline run in seconds.",
    )
    selected_decision: str = Field(
        default="",
        description="DecisionType value returned by the business rule engine.",
    )
    recommendation_count: int = Field(
        default=0,
        ge=0,
        description="Number of assessment recommendations returned by the engine.",
    )

    model_config = ConfigDict(extra="allow")


class PipelineMetadata(BaseModel):

    conversation_id: str = Field(
        default="",
        description="Identifier of the conversation processed by this pipeline run.",
    )
    turn_index: int = Field(
        default=0,
        ge=0,
        description="Zero-based index of the current conversation turn.",
    )
    constraint_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score reported by the constraint extractor.",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Constraint fields still missing after extraction.",
    )
    candidate_count: int = Field(
        default=0,
        ge=0,
        description="Number of catalog candidate assessments retrieved.",
    )
    trace: ExecutionTrace = Field(
        default_factory=ExecutionTrace,
        description="Detailed execution trace for the pipeline run.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Aggregated non-fatal warnings from all pipeline stages.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata produced by individual pipeline stages.",
    )

    model_config = ConfigDict(extra="allow")


class ChatPipelineResult(BaseModel):

    conversation_state: ConversationState = Field(
        description="Updated conversation state after this pipeline turn.",
    )
    constraint_result: ConstraintExtractionResult = Field(
        description="Constraint extraction result from the deterministic extractor.",
    )
    decision: ConversationDecision = Field(
        description="Business-rule decision for the current turn.",
    )
    recommendation_result: RecommendationResult = Field(
        description="Ranked assessment recommendations produced by the engine.",
    )
    metadata: PipelineMetadata = Field(
        description="Operational metadata and execution trace for this run.",
    )

    model_config = ConfigDict(extra="allow")
