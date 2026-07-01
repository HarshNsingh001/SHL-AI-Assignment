from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobLevel(StrEnum):

    GRADUATE = "Graduate"
    ENTRY_LEVEL = "Entry Level"
    MID_LEVEL = "Mid Level"
    SENIOR = "Senior"
    MANAGER = "Manager"
    EXECUTIVE = "Executive"


class EmploymentType(StrEnum):

    FULL_TIME = "Full Time"
    PART_TIME = "Part Time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"


class WorkLocation(StrEnum):

    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "Onsite"


class AssessmentPurpose(StrEnum):

    HIRING = "Hiring"
    SCREENING = "Screening"
    DEVELOPMENT = "Development"
    PROMOTION = "Promotion"


class Seniority(StrEnum):

    GRADUATE = "Graduate"
    ENTRY_LEVEL = "Entry Level"
    MID_LEVEL = "Mid Level"
    SENIOR = "Senior"
    MANAGER = "Manager"
    EXECUTIVE = "Executive"


class HiringConstraints(BaseModel):

    role: str | None = Field(default=None, description="Normalized role name.")
    job_level: JobLevel | None = Field(
        default=None,
        description="Normalized job level.",
    )
    experience_level: str | None = Field(
        default=None,
        description="Experience level mentioned by the user.",
    )
    industry: str | None = Field(default=None, description="Normalized industry.")
    employment_type: EmploymentType | None = Field(
        default=None,
        description="Normalized employment type.",
    )
    required_skills: list[str] | None = Field(
        default=None,
        description="Required skills detected from the text.",
    )
    preferred_skills: list[str] | None = Field(
        default=None,
        description="Preferred skills detected from the text.",
    )
    languages: list[str] | None = Field(
        default=None,
        description="Languages detected from the text.",
    )
    assessment_types: list[str] | None = Field(
        default=None,
        description="Assessment types requested by the user.",
    )
    purpose: AssessmentPurpose | None = Field(
        default=None,
        description="Detected assessment purpose.",
    )
    candidate_volume: int | None = Field(
        default=None,
        ge=0,
        description="Number of candidates or hires mentioned by the user.",
    )
    work_location: WorkLocation | None = Field(
        default=None,
        description="Detected work location.",
    )
    seniority: Seniority | None = Field(
        default=None,
        description="Normalized seniority.",
    )
    leadership_required: bool | None = Field(
        default=None,
        description="Whether leadership capability was requested.",
    )
    technical_role: bool | None = Field(
        default=None,
        description="Whether the role appears technical.",
    )
    customer_facing: bool | None = Field(
        default=None,
        description="Whether the role appears customer-facing.",
    )
    additional_requirements: list[str] | None = Field(
        default=None,
        description="Additional explicit requirements from the text.",
    )

    model_config = ConfigDict(extra="allow")


class MissingInformation(BaseModel):

    missing_fields: list[str] = Field(
        default_factory=list,
        description="Constraint fields still missing after extraction.",
    )
    questions: list[str] = Field(
        default_factory=list,
        description="Deterministic clarification questions for missing fields.",
    )
    is_complete: bool = Field(
        default=False,
        description="Whether required extraction fields are present.",
    )


class ConstraintExtractionResult(BaseModel):

    constraints: HiringConstraints = Field(
        description="Extracted hiring constraints.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Deterministic confidence based on extracted field coverage.",
    )
    missing_information: MissingInformation = Field(
        description="Missing fields and clarification questions.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal extraction warnings.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional extraction metadata.",
    )

    model_config = ConfigDict(extra="allow")
