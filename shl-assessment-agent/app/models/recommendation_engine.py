from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.catalog import Assessment


class RecommendationReason(BaseModel):

    summary: str = Field(description="Short deterministic reason summary.")
    evidence: list[str] = Field(
        default_factory=list,
        description="Catalog fields or constraints that support the recommendation.",
    )


class RecommendationScore(BaseModel):

    catalog_score: float = Field(
        ge=0.0,
        description="Normalized score from catalog retrieval.",
    )
    constraint_score: float = Field(
        ge=0.0,
        description="Score based on matched extracted constraints.",
    )
    context_score: float = Field(
        ge=0.0,
        description="Score based on conversation context.",
    )
    decision_score: float = Field(
        ge=0.0,
        description="Score based on the business-rule decision.",
    )
    total: float = Field(ge=0.0, description="Final deterministic score.")


class AssessmentRecommendation(BaseModel):

    assessment: Assessment = Field(description="Validated assessment catalog item.")
    score: RecommendationScore = Field(description="Deterministic score breakdown.")
    matched_constraints: list[str] = Field(
        default_factory=list,
        description="Constraint fields matched by this assessment.",
    )
    reason: RecommendationReason = Field(
        description="Structured reason for selecting this assessment.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence derived from score and constraint coverage.",
    )


class RecommendationMetadata(BaseModel):

    decision_type: str = Field(description="Business-rule decision used.")
    requested_limit: int = Field(ge=0, description="Requested recommendation limit.")
    candidate_count: int = Field(
        ge=0,
        description="Number of candidate assessments considered.",
    )
    returned_count: int = Field(
        ge=0,
        description="Number of recommendations returned.",
    )
    updated_from_previous: bool = Field(
        default=False,
        description="Whether previous recommendations influenced the result.",
    )
    prior_recommendation_ids: list[str] = Field(
        default_factory=list,
        description="Assessment identifiers recommended earlier.",
    )
    excluded_assessment_ids: list[str] = Field(
        default_factory=list,
        description="Assessment identifiers excluded by deterministic update rules.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional recommendation run metadata.",
    )

    model_config = ConfigDict(extra="allow")


class RecommendationResult(BaseModel):

    recommendations: list[AssessmentRecommendation] = Field(
        default_factory=list,
        description="Ranked assessment recommendations.",
    )
    metadata: RecommendationMetadata = Field(
        description="Recommendation run metadata.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal recommendation warnings.",
    )

    model_config = ConfigDict(extra="allow")
