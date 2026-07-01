from app.models.constraints import (
    AssessmentPurpose,
    EmploymentType,
    JobLevel,
    Seniority,
    WorkLocation,
)
from app.models.conversation import (
    ConversationContext,
    ConversationMessage,
    ConversationMessageRole,
    ConversationState,
)
from app.services.constraint_extractor import ConstraintExtractor


def make_state(message: str = "") -> ConversationState:
    messages = []
    if message:
        messages.append(
            ConversationMessage(
                role=ConversationMessageRole.USER,
                content=message,
            )
        )
    return ConversationState(messages=messages)


def test_extracts_graduate_financial_analyst_constraints() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(
        make_state(),
        "Graduate financial analyst hiring for 40 candidates in English.",
    )

    assert result.constraints.role == "Financial Analyst"
    assert result.constraints.job_level is JobLevel.GRADUATE
    assert result.constraints.industry == "Finance"
    assert result.constraints.purpose is AssessmentPurpose.HIRING
    assert result.constraints.candidate_volume == 40
    assert result.constraints.languages == ["English"]


def test_extracts_campus_hire_as_graduate() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Campus hire analyst screening.")

    assert result.constraints.job_level is JobLevel.GRADUATE
    assert result.constraints.seniority is Seniority.GRADUATE
    assert result.constraints.purpose is AssessmentPurpose.HIRING


def test_extracts_senior_java_backend_engineer() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Senior Java backend engineer.")

    assert result.constraints.role == "Backend Engineer"
    assert result.constraints.job_level is JobLevel.SENIOR
    assert result.constraints.required_skills == ["Java"]
    assert result.constraints.technical_role is True


def test_extracts_backend_developer_normalization() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Backend developer with AWS.")

    assert result.constraints.role == "Backend Engineer"
    assert result.constraints.required_skills == ["AWS"]
    assert result.constraints.industry == "Technology"


def test_extracts_contact_centre_agent_normalization() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Contact centre agent assessment.")

    assert result.constraints.role == "Contact Center Agent"
    assert result.constraints.industry == "Customer Support"
    assert result.constraints.customer_facing is True


def test_extracts_sales_manager_leadership() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Sales manager hiring.")

    assert result.constraints.role == "Sales Manager"
    assert result.constraints.job_level is JobLevel.MANAGER
    assert result.constraints.leadership_required is True
    assert result.constraints.customer_facing is True


def test_extracts_executive_leadership() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Executive leadership development.")

    assert result.constraints.role == "Executive Leadership"
    assert result.constraints.job_level is JobLevel.EXECUTIVE
    assert result.constraints.leadership_required is True
    assert result.constraints.purpose is AssessmentPurpose.DEVELOPMENT


def test_extracts_rust_engineer() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Rust engineer technical screening.")

    assert result.constraints.role == "Software Engineer"
    assert result.constraints.required_skills == ["Rust"]
    assert result.constraints.technical_role is True
    assert result.constraints.assessment_types == ["Technical"]


def test_extracts_plant_operator_manufacturing() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Plant operator onsite hiring.")

    assert result.constraints.role == "Plant Operator"
    assert result.constraints.industry == "Manufacturing"
    assert result.constraints.work_location is WorkLocation.ONSITE


def test_detects_missing_role() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Need English screening for 12 people.")

    assert "role" in result.missing_information.missing_fields
    assert result.constraints.role is None
    assert result.confidence <= 0.65


def test_detects_missing_seniority() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(make_state(), "Financial analyst hiring.")

    assert result.constraints.role == "Financial Analyst"
    assert "seniority" in result.missing_information.missing_fields
    assert result.constraints.seniority is None


def test_extracts_multiple_technical_skills() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(
        make_state(),
        "Senior software engineer requires Python, SQL, AWS and Docker.",
    )

    assert result.constraints.required_skills == ["Python", "SQL", "AWS", "Docker"]
    assert result.constraints.additional_requirements == ["Python, SQL, AWS and Docker"]


def test_extracts_languages() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(
        make_state(),
        "Customer support agent hiring in English, Spanish and French.",
    )

    assert result.constraints.languages == ["English", "Spanish", "French"]


def test_extracts_employment_type_and_location() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(
        make_state(),
        "Entry level sales representative full-time remote hiring.",
    )

    assert result.constraints.employment_type is EmploymentType.FULL_TIME
    assert result.constraints.work_location is WorkLocation.REMOTE
    assert result.constraints.job_level is JobLevel.ENTRY_LEVEL


def test_extracts_assessment_types() -> None:
    extractor = ConstraintExtractor()

    result = extractor.extract(
        make_state(),
        "Senior manager needs leadership, personality and cognitive assessment.",
    )

    assert result.constraints.assessment_types == [
        "Personality",
        "Cognitive",
        "Leadership",
    ]


def test_preserves_context_when_latest_message_adds_detail() -> None:
    extractor = ConstraintExtractor()
    state = ConversationState(
        context=ConversationContext(
            current_role="Financial Analyst",
            industry="Finance",
            required_skills=["Financial Analysis"],
        )
    )

    result = extractor.extract(state, "Senior hiring in German.")

    assert result.constraints.role == "Financial Analyst"
    assert result.constraints.industry == "Finance"
    assert result.constraints.required_skills == ["Financial Analysis"]
    assert result.constraints.job_level is JobLevel.SENIOR
    assert result.constraints.languages == ["German"]


def test_plural_forms_normalize_and_stem() -> None:
    extractor = ConstraintExtractor()

    assert extractor._stem_text("developers") == "developer"
    assert extractor._stem_text("engineers") == "engineer"
    assert extractor._stem_text("assistants") == "assistant"
    assert extractor._stem_text("operators") == "operator"
    assert extractor._stem_text("managers") == "manager"
    assert extractor._stem_text("trainees") == "trainee"


def test_role_synonym_coverage_expanded() -> None:
    extractor = ConstraintExtractor()

    res1 = extractor.extract(make_state(), "We need a management trainee.")
    assert res1.constraints.role == "Graduate Trainee"

    res2 = extractor.extract(make_state(), "Hiring for our graduate program.")
    assert res2.constraints.role == "Graduate Trainee"

    res3 = extractor.extract(make_state(), "Screening trainee candidates.")
    assert res3.constraints.role == "Graduate Trainee"

    res4 = extractor.extract(make_state(), "Hiring administrative assistants.")
    assert res4.constraints.role == "Admin Assistant"

    res5 = extractor.extract(make_state(), "Hiring admin assistants.")
    assert res5.constraints.role == "Admin Assistant"

    res6 = extractor.extract(make_state(), "Re-skilling our sales organization.")
    assert res6.constraints.role == "Sales Representative"

    res7 = extractor.extract(make_state(), "Training the sales team.")
    assert res7.constraints.role == "Sales Representative"

    res8 = extractor.extract(make_state(), "Aligning the sales force.")
    assert res8.constraints.role == "Sales Representative"

    res9 = extractor.extract(make_state(), "We need plant operators.")
    assert res9.constraints.role == "Plant Operator"

    res10 = extractor.extract(make_state(), "Hiring software developers.")
    assert res10.constraints.role == "Software Engineer"

    res11 = extractor.extract(make_state(), "Hiring backend developers.")
    assert res11.constraints.role == "Backend Engineer"


def test_organization_to_role_mappings() -> None:
    extractor = ConstraintExtractor()

    assert (
        extractor.extract(make_state(), "Sales organization").constraints.role
        == "Sales Representative"
    )
    assert (
        extractor.extract(make_state(), "Graduate program").constraints.role
        == "Graduate Trainee"
    )
    assert (
        extractor.extract(make_state(), "Leadership hiring").constraints.role
        == "Executive Leadership"
    )


def test_confidence_scoring_boosts_on_multiple_signals() -> None:
    extractor = ConstraintExtractor()

    res1 = extractor.extract(make_state(), "Hiring java.")

    res2 = extractor.extract(
        make_state(), "Hiring java backend developer with spring and sql."
    )

    assert res2.confidence > res1.confidence
