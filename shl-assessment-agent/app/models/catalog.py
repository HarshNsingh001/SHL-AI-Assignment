from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AssessmentStatus(StrEnum):

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class Assessment(BaseModel):

    id: str = Field(description="Stable assessment identifier.")
    name: str = Field(description="Human-readable assessment name.")
    url: HttpUrl = Field(description="Canonical assessment URL.")
    description: str = Field(description="Assessment description.")
    duration: int | None = Field(
        default=None,
        ge=0,
        description="Assessment duration in minutes, when available.",
    )
    job_levels: list[str] = Field(
        default_factory=list,
        description="Job levels associated with the assessment.",
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
    test_type: str = Field(description="Assessment test type.")
    keys: list[str] = Field(
        default_factory=list,
        description="Searchable catalog keywords.",
    )
    status: AssessmentStatus = Field(
        default=AssessmentStatus.ACTIVE,
        description="Catalog lifecycle status.",
    )

    model_config = ConfigDict(extra="allow")


class Catalog(BaseModel):

    assessments: list[Assessment] = Field(
        default_factory=list,
        description="Assessments available in the catalog.",
    )

    model_config = ConfigDict(extra="allow")

    def additional_metadata(self) -> dict[str, Any]:
        return dict(self.model_extra or {})
