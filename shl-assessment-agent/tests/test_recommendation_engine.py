from typing import Any, cast

from app.models.business_rules import (
    CatalogQueryResult,
    ConversationDecision,
    DecisionContext,
    DecisionType,
)
from app.models.catalog import Assessment
from app.models.constraints import (
    AssessmentPurpose,
    ConstraintExtractionResult,
    HiringConstraints,
    JobLevel,
    MissingInformation,
)
from app.models.conversation import (
    ConversationMessage,
    ConversationMessageRole,
    ConversationState,
)
from app.services.catalog_query_service import CatalogCandidate
from app.services.recommendation_engine import RecommendationEngine


def make_assessment(
    identifier: str,
    name: str,
    description: str,
    job_levels: list[str],
    keys: list[str],
    test_type: str,
    languages: list[str] | None = None,
    duration: int | None = None,
) -> Assessment:
    return Assessment(
        id=identifier,
        name=name,
        url=cast(
            Any,
            f"https://www.shl.com/products/product-catalog/view/{identifier}/",
        ),
        description=description,
        duration=duration,
        job_levels=job_levels,
        languages=languages or ["English (USA)"],
        remote_support=True,
        adaptive_support=False,
        test_type=test_type,
        keys=keys,
    )


def catalog_items() -> dict[str, Assessment]:
    return {
        "opq32r": make_assessment(
            "opq32r",
            "Occupational Personality Questionnaire OPQ32r",
            "Workplace personality and leadership behaviour dimensions.",
            ["Graduate", "Manager", "Executive"],
            ["Personality & Behavior"],
            "P",
            ["English International", "Spanish"],
            25,
        ),
        "opq-leadership-report": make_assessment(
            "opq-leadership-report",
            "OPQ Leadership Report",
            "Leadership report generated from OPQ results.",
            ["Manager", "Executive"],
            ["Personality & Behavior"],
            "P",
        ),
        "smart-interview-live-coding": make_assessment(
            "smart-interview-live-coding",
            "Smart Interview Live Coding",
            "Live coding interview for technical software roles.",
            ["Graduate", "Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
        ),
        "linux-programming-general": make_assessment(
            "linux-programming-general",
            "Linux Programming (General)",
            "Linux systems programming knowledge.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            duration=25,
        ),
        "core-java-advanced-level-new": make_assessment(
            "core-java-advanced-level-new",
            "Core Java (Advanced Level) (New)",
            "Advanced Core Java, concurrency, performance, and JVM topics.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            duration=13,
        ),
        "spring-new": make_assessment(
            "spring-new",
            "Spring (New)",
            "Spring framework backend service development.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            duration=9,
        ),
        "sql-new": make_assessment(
            "sql-new",
            "SQL (New)",
            "SQL and relational database knowledge.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            duration=9,
        ),
        "aws-development-new": make_assessment(
            "aws-development-new",
            "Amazon Web Services (AWS) Development (New)",
            "AWS cloud deployment and development.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            duration=6,
        ),
        "docker-new": make_assessment(
            "docker-new",
            "Docker (New)",
            "Docker container knowledge.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            duration=10,
        ),
        "restful-web-services-new": make_assessment(
            "restful-web-services-new",
            "RESTful Web Services (New)",
            "REST API design and web services.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            duration=12,
        ),
        "shl-verify-interactive-g": make_assessment(
            "shl-verify-interactive-g",
            "SHL Verify Interactive G+",
            "General cognitive reasoning ability.",
            ["Graduate", "Mid-Professional"],
            ["Ability & Aptitude"],
            "A",
            ["English (USA)", "Spanish"],
            36,
        ),
        "shl-verify-numerical-reasoning": make_assessment(
            "shl-verify-numerical-reasoning",
            "SHL Verify Interactive - Numerical Reasoning",
            "Numerical reasoning assessment for graduate analysts.",
            ["Graduate"],
            ["Ability & Aptitude", "Simulations"],
            "A,S",
            duration=20,
        ),
        "financial-accounting-new": make_assessment(
            "financial-accounting-new",
            "Financial Accounting (New)",
            "Finance and accounting knowledge for analysts.",
            ["Graduate"],
            ["Knowledge & Skills"],
            "K",
            duration=9,
        ),
        "basic-statistics-new": make_assessment(
            "basic-statistics-new",
            "Basic Statistics (New)",
            "Statistics knowledge for analysts.",
            ["Graduate"],
            ["Knowledge & Skills"],
            "K",
            duration=10,
        ),
        "graduate-scenarios": make_assessment(
            "graduate-scenarios",
            "Graduate Scenarios",
            "Situational judgment for graduate candidates.",
            ["Graduate"],
            ["Biodata & Situational Judgment"],
            "B",
            ["English International"],
        ),
        "svar-spoken-english-us-new": make_assessment(
            "svar-spoken-english-us-new",
            "SVAR Spoken English (US) (New)",
            "Spoken English screen for US contact center calls.",
            ["Entry-Level"],
            ["Simulations"],
            "K",
        ),
        "contact-center-call-simulation-new": make_assessment(
            "contact-center-call-simulation-new",
            "Contact Center Call Simulation (New)",
            "Standalone contact center call simulation.",
            ["Entry-Level"],
            ["Simulations"],
            "S",
            duration=15,
        ),
        "customer-service-phone-simulation": make_assessment(
            "customer-service-phone-simulation",
            "Customer Service Phone Simulation",
            "Customer service phone simulation.",
            ["Entry-Level"],
            ["Biodata & Situational Judgment", "Simulations"],
            "B,S",
            duration=20,
        ),
        "entry-level-customer-service": make_assessment(
            "entry-level-customer-service",
            "Entry Level Customer Serv - Retail & Contact Center",
            "Customer service fit for retail and contact center.",
            ["Entry-Level"],
            ["Personality & Behavior", "Competencies"],
            "P,C",
            ["Spanish", "English (USA)"],
            19,
        ),
        "dependability-safety-instrument-dsi": make_assessment(
            "dependability-safety-instrument-dsi",
            "Dependability and Safety Instrument (DSI)",
            "Dependability reliability and safety attitudes.",
            ["Entry-Level"],
            ["Personality & Behavior"],
            "P",
            ["Spanish", "English (USA)"],
            10,
        ),
        "safety-dependability-focus-8": make_assessment(
            "safety-dependability-focus-8",
            "Manufac. & Indust. - Safety & Dependability 8.0",
            "Manufacturing industrial safety dependability personality bundle.",
            ["Entry-Level"],
            ["Personality & Behavior"],
            "P",
            duration=16,
        ),
        "workplace-health-safety-new": make_assessment(
            "workplace-health-safety-new",
            "Workplace Health and Safety (New)",
            "Workplace health and safety knowledge.",
            ["Entry-Level"],
            ["Knowledge & Skills"],
            "K",
            duration=9,
        ),
        "global-skills-assessment": make_assessment(
            "global-skills-assessment",
            "Global Skills Assessment",
            "Self-reported skills measure for development.",
            ["Graduate", "Manager", "Executive"],
            ["Competencies", "Knowledge & Skills"],
            "C,K",
            duration=16,
        ),
        "global-skills-development-report": make_assessment(
            "global-skills-development-report",
            "Global Skills Development Report",
            "Development report for Global Skills Assessment.",
            ["Graduate", "Manager", "Executive"],
            ["Development & 360", "Competencies"],
            "D",
        ),
        "opq-mq-sales-report": make_assessment(
            "opq-mq-sales-report",
            "OPQ MQ Sales Report",
            "Sales-specific OPQ report with motivators.",
            ["Manager"],
            ["Personality & Behavior"],
            "P",
        ),
        "sales-transformation-ic": make_assessment(
            "sales-transformation-ic",
            "Sales Transformation 2.0 - Individual Contributor",
            "Sales transformation behaviours for individual contributors.",
            ["Mid-Professional"],
            ["Personality & Behavior"],
            "P",
        ),
        "hipaa-security": make_assessment(
            "hipaa-security",
            "HIPAA (Security)",
            "HIPAA security knowledge for patient records.",
            ["Entry-Level"],
            ["Knowledge & Skills"],
            "K",
            duration=15,
        ),
        "medical-terminology-new": make_assessment(
            "medical-terminology-new",
            "Medical Terminology (New)",
            "Medical terminology knowledge.",
            ["Entry-Level"],
            ["Knowledge & Skills"],
            "K",
            duration=3,
        ),
        "microsoft-word-365-essentials-new": make_assessment(
            "microsoft-word-365-essentials-new",
            "Microsoft Word 365 - Essentials (New)",
            "Microsoft Word essentials simulation.",
            ["Entry-Level"],
            ["Knowledge & Skills", "Simulations"],
            "K,S",
            duration=25,
        ),
        "ms-excel-new": make_assessment(
            "ms-excel-new",
            "MS Excel (New)",
            "Fast Microsoft Excel knowledge check.",
            ["Entry-Level"],
            ["Knowledge & Skills"],
            "K",
            duration=6,
        ),
        "ms-word-new": make_assessment(
            "ms-word-new",
            "MS Word (New)",
            "Fast Microsoft Word knowledge check.",
            ["Entry-Level"],
            ["Knowledge & Skills"],
            "K",
            duration=4,
        ),
        "microsoft-excel-365-new": make_assessment(
            "microsoft-excel-365-new",
            "Microsoft Excel 365 (New)",
            "Microsoft Excel simulation for daily spreadsheet work.",
            ["Entry-Level"],
            ["Knowledge & Skills", "Simulations"],
            "K,S",
            duration=35,
        ),
        "microsoft-word-365-new": make_assessment(
            "microsoft-word-365-new",
            "Microsoft Word 365 (New)",
            "Microsoft Word simulation for daily document work.",
            ["Entry-Level"],
            ["Knowledge & Skills", "Simulations"],
            "K,S",
            duration=35,
        ),
    }


def candidate(identifier: str, score: float = 4.0) -> CatalogCandidate:
    return CatalogCandidate(assessment=catalog_items()[identifier], score=score)


def decision(decision_type: DecisionType) -> ConversationDecision:
    return ConversationDecision(
        decision_type=decision_type,
        context=DecisionContext(
            has_catalog_candidates=decision_type
            in {DecisionType.RECOMMEND, DecisionType.UPDATE_RECOMMENDATIONS}
        ),
    )


def extraction(constraints: HiringConstraints) -> ConstraintExtractionResult:
    return ConstraintExtractionResult(
        constraints=constraints,
        confidence=0.8,
        missing_information=MissingInformation(is_complete=True),
        warnings=[],
    )


def state(
    latest_message: str = "",
    prior_ids: list[str] | None = None,
) -> ConversationState:
    messages: list[ConversationMessage] = []
    if latest_message:
        messages.append(
            ConversationMessage(
                role=ConversationMessageRole.USER,
                content=latest_message,
            )
        )
    return ConversationState(
        messages=messages,
        recommended_assessment_ids=prior_ids or [],
    )


def query_result(candidates: list[CatalogCandidate]) -> CatalogQueryResult:
    return CatalogQueryResult(
        candidate_count=len(candidates),
        candidate_ids=[item.assessment.id for item in candidates],
        top_score=max((item.score for item in candidates), default=None),
        metadata={"candidates": candidates},
    )


def recommend_ids(
    candidates: list[CatalogCandidate],
    constraints: HiringConstraints,
    decision_type: DecisionType = DecisionType.RECOMMEND,
    latest_message: str = "",
    prior_ids: list[str] | None = None,
    limit: int | None = None,
) -> list[str]:
    result = RecommendationEngine().generate(
        state(latest_message, prior_ids),
        extraction(constraints),
        decision(decision_type),
        query_result(candidates),
        limit=limit,
    )
    return [item.assessment.id for item in result.recommendations]


def test_returns_empty_for_clarification_decision() -> None:
    ids = recommend_ids(
        [candidate("opq32r")],
        HiringConstraints(role="Executive Leadership"),
        DecisionType.ASK_CLARIFICATION,
    )

    assert ids == []


def test_returns_empty_for_refusal_decision() -> None:
    ids = recommend_ids(
        [candidate("hipaa-security")],
        HiringConstraints(role="Healthcare Admin"),
        DecisionType.REFUSE,
    )

    assert ids == []


def test_leadership_selection_ranks_opq_first() -> None:
    ids = recommend_ids(
        [
            candidate("opq32r", 5.0),
            candidate("opq-leadership-report", 4.8),
        ],
        HiringConstraints(
            role="Executive Leadership",
            job_level=JobLevel.EXECUTIVE,
            purpose=AssessmentPurpose.HIRING,
            leadership_required=True,
        ),
    )

    assert ids[:2] == ["opq32r", "opq-leadership-report"]


def test_rust_engineering_ranks_live_coding_and_linux() -> None:
    ids = recommend_ids(
        [
            candidate("smart-interview-live-coding", 5.0),
            candidate("linux-programming-general", 4.5),
            candidate("shl-verify-interactive-g", 2.0),
        ],
        HiringConstraints(
            role="Software Engineer",
            job_level=JobLevel.SENIOR,
            required_skills=["Rust", "Linux", "Networking"],
            technical_role=True,
        ),
    )

    assert ids[:2] == ["smart-interview-live-coding", "linux-programming-general"]


def test_senior_java_backend_ranks_core_stack() -> None:
    ids = recommend_ids(
        [
            candidate("core-java-advanced-level-new", 5.0),
            candidate("spring-new", 4.8),
            candidate("sql-new", 4.7),
            candidate("opq32r", 2.0),
        ],
        HiringConstraints(
            role="Backend Engineer",
            job_level=JobLevel.SENIOR,
            required_skills=["Java", "Spring", "SQL"],
            technical_role=True,
        ),
    )

    assert ids[:3] == [
        "core-java-advanced-level-new",
        "spring-new",
        "sql-new",
    ]


def test_backend_update_adds_aws_and_docker() -> None:
    ids = recommend_ids(
        [
            candidate("core-java-advanced-level-new", 4.0),
            candidate("spring-new", 4.0),
            candidate("sql-new", 4.0),
            candidate("aws-development-new", 5.0),
            candidate("docker-new", 5.0),
            candidate("restful-web-services-new", 3.0),
        ],
        HiringConstraints(
            role="Backend Engineer",
            required_skills=["AWS", "Docker"],
            technical_role=True,
        ),
        DecisionType.UPDATE_RECOMMENDATIONS,
        latest_message="Add AWS and Docker.",
        prior_ids=["core-java-advanced-level-new", "spring-new", "sql-new"],
    )

    assert ids[:2] == ["aws-development-new", "docker-new"]


def test_backend_update_drops_rest() -> None:
    ids = recommend_ids(
        [
            candidate("restful-web-services-new", 5.0),
            candidate("aws-development-new", 4.0),
            candidate("docker-new", 4.0),
        ],
        HiringConstraints(role="Backend Engineer", required_skills=["AWS", "Docker"]),
        DecisionType.UPDATE_RECOMMENDATIONS,
        latest_message="Drop REST and add AWS and Docker.",
        prior_ids=["restful-web-services-new"],
    )

    assert "restful-web-services-new" not in ids
    assert ids[:2] == ["aws-development-new", "docker-new"]


def test_graduate_finance_ranks_numerical_and_accounting() -> None:
    ids = recommend_ids(
        [
            candidate("shl-verify-numerical-reasoning", 5.0),
            candidate("financial-accounting-new", 4.8),
            candidate("basic-statistics-new", 4.2),
            candidate("opq32r", 2.5),
        ],
        HiringConstraints(
            role="Financial Analyst",
            job_level=JobLevel.GRADUATE,
            industry="Finance",
            required_skills=["Numerical Reasoning", "Financial Accounting"],
        ),
    )

    assert ids[:2] == [
        "shl-verify-numerical-reasoning",
        "financial-accounting-new",
    ]


def test_graduate_update_adds_situational_judgment() -> None:
    ids = recommend_ids(
        [
            candidate("shl-verify-numerical-reasoning", 4.0),
            candidate("financial-accounting-new", 4.0),
            candidate("graduate-scenarios", 5.0),
        ],
        HiringConstraints(
            role="Financial Analyst",
            job_level=JobLevel.GRADUATE,
            assessment_types=["Biodata & Situational Judgment"],
        ),
        DecisionType.UPDATE_RECOMMENDATIONS,
        latest_message="Add a situational judgement element.",
        prior_ids=["shl-verify-numerical-reasoning", "financial-accounting-new"],
    )

    assert ids[0] == "graduate-scenarios"


def test_contact_center_ranks_svar_first() -> None:
    ids = recommend_ids(
        [
            candidate("svar-spoken-english-us-new", 5.0),
            candidate("contact-center-call-simulation-new", 4.7),
            candidate("entry-level-customer-service", 3.5),
        ],
        HiringConstraints(
            role="Contact Center Agent",
            job_level=JobLevel.ENTRY_LEVEL,
            languages=["English"],
            customer_facing=True,
        ),
    )

    assert ids[:2] == [
        "svar-spoken-english-us-new",
        "contact-center-call-simulation-new",
    ]


def test_contact_center_finalist_update_prefers_old_phone_simulation() -> None:
    ids = recommend_ids(
        [
            candidate("contact-center-call-simulation-new", 4.0),
            candidate("customer-service-phone-simulation", 5.0),
        ],
        HiringConstraints(
            role="Contact Center Agent",
            required_skills=["Customer Service"],
            customer_facing=True,
        ),
        DecisionType.UPDATE_RECOMMENDATIONS,
        latest_message="Use new simulation for volume, old solution for finalists.",
        prior_ids=["contact-center-call-simulation-new"],
    )

    assert ids[0] == "customer-service-phone-simulation"


def test_sales_audit_ranks_gsa_and_development_report() -> None:
    ids = recommend_ids(
        [
            candidate("global-skills-assessment", 5.0),
            candidate("global-skills-development-report", 4.8),
            candidate("opq32r", 4.0),
            candidate("opq-mq-sales-report", 3.8),
            candidate("sales-transformation-ic", 3.5),
        ],
        HiringConstraints(
            role="Sales Representative",
            industry="Sales",
            purpose=AssessmentPurpose.DEVELOPMENT,
            required_skills=["Sales"],
        ),
    )

    assert ids[:2] == [
        "global-skills-assessment",
        "global-skills-development-report",
    ]


def test_sales_comparison_preserves_shortlist_candidates() -> None:
    ids = recommend_ids(
        [
            candidate("opq32r", 4.0),
            candidate("opq-mq-sales-report", 4.0),
        ],
        HiringConstraints(role="Sales Representative", required_skills=["Sales"]),
        DecisionType.RECOMMEND,
        latest_message="What's the difference between OPQ and OPQ MQ Sales Report?",
        prior_ids=["opq32r", "opq-mq-sales-report"],
    )

    assert ids == ["opq-mq-sales-report", "opq32r"]


def test_manufacturing_safety_ranks_personality_before_knowledge() -> None:
    ids = recommend_ids(
        [
            candidate("dependability-safety-instrument-dsi", 5.0),
            candidate("safety-dependability-focus-8", 4.8),
            candidate("workplace-health-safety-new", 4.0),
        ],
        HiringConstraints(
            role="Plant Operator",
            industry="Manufacturing",
            required_skills=["Safety", "Dependability"],
        ),
    )

    assert ids[:2] == [
        "dependability-safety-instrument-dsi",
        "safety-dependability-focus-8",
    ]


def test_manufacturing_update_prefers_industrial_bundle() -> None:
    ids = recommend_ids(
        [
            candidate("dependability-safety-instrument-dsi", 4.0),
            candidate("safety-dependability-focus-8", 5.0),
            candidate("workplace-health-safety-new", 4.5),
        ],
        HiringConstraints(
            role="Plant Operator",
            industry="Manufacturing",
            required_skills=["Safety"],
        ),
        DecisionType.UPDATE_RECOMMENDATIONS,
        latest_message="We're industrial. The 8.0 bundle is the right fit.",
        prior_ids=["dependability-safety-instrument-dsi"],
    )

    assert ids[0] == "safety-dependability-focus-8"


def test_healthcare_hybrid_ranks_hipaa_and_medical_terms() -> None:
    ids = recommend_ids(
        [
            candidate("hipaa-security", 5.0),
            candidate("medical-terminology-new", 4.8),
            candidate("microsoft-word-365-essentials-new", 4.2),
            candidate("dependability-safety-instrument-dsi", 3.5),
            candidate("opq32r", 3.2),
        ],
        HiringConstraints(
            role="Healthcare Admin",
            industry="Healthcare",
            languages=["Spanish", "English"],
            required_skills=["HIPAA", "Medical Terminology", "Word"],
        ),
    )

    assert ids[:2] == ["hipaa-security", "medical-terminology-new"]


def test_admin_quick_screen_ranks_short_knowledge_tests() -> None:
    ids = recommend_ids(
        [
            candidate("ms-excel-new", 5.0),
            candidate("ms-word-new", 4.8),
            candidate("opq32r", 3.0),
        ],
        HiringConstraints(
            role="Admin Assistant",
            required_skills=["Excel", "Word"],
        ),
    )

    assert ids[:2] == ["ms-excel-new", "ms-word-new"]


def test_admin_update_adds_simulations() -> None:
    ids = recommend_ids(
        [
            candidate("microsoft-excel-365-new", 5.0),
            candidate("microsoft-word-365-new", 4.8),
            candidate("ms-excel-new", 3.0),
            candidate("ms-word-new", 3.0),
        ],
        HiringConstraints(
            role="Admin Assistant",
            required_skills=["Excel", "Word"],
            assessment_types=["Simulations"],
        ),
        DecisionType.UPDATE_RECOMMENDATIONS,
        latest_message="I am OK with adding a simulation.",
        prior_ids=["ms-excel-new", "ms-word-new"],
    )

    assert ids[:2] == ["microsoft-excel-365-new", "microsoft-word-365-new"]


def test_graduate_management_battery_ranks_three_dimensions() -> None:
    ids = recommend_ids(
        [
            candidate("shl-verify-interactive-g", 5.0),
            candidate("opq32r", 4.8),
            candidate("graduate-scenarios", 4.6),
        ],
        HiringConstraints(
            role="Graduate Trainee",
            job_level=JobLevel.GRADUATE,
            assessment_types=[
                "Ability & Aptitude",
                "Personality & Behavior",
                "Biodata & Situational Judgment",
            ],
        ),
    )

    assert ids == [
        "shl-verify-interactive-g",
        "opq32r",
        "graduate-scenarios",
    ]


def test_graduate_update_drops_opq() -> None:
    ids = recommend_ids(
        [
            candidate("shl-verify-interactive-g", 5.0),
            candidate("opq32r", 4.8),
            candidate("graduate-scenarios", 4.6),
        ],
        HiringConstraints(role="Graduate Trainee", job_level=JobLevel.GRADUATE),
        DecisionType.UPDATE_RECOMMENDATIONS,
        latest_message="Drop the OPQ. Final list: Verify G+ and Graduate Scenarios.",
        prior_ids=["shl-verify-interactive-g", "opq32r", "graduate-scenarios"],
    )

    assert ids == ["shl-verify-interactive-g", "graduate-scenarios"]


def test_limit_caps_results_to_assignment_maximum() -> None:
    candidates = [candidate(identifier, 1.0) for identifier in catalog_items().keys()]

    ids = recommend_ids(
        candidates,
        HiringConstraints(role="General Hiring"),
        limit=25,
    )

    assert len(ids) == 10


def test_limit_can_return_smaller_shortlist() -> None:
    ids = recommend_ids(
        [
            candidate("core-java-advanced-level-new", 5.0),
            candidate("spring-new", 4.0),
            candidate("sql-new", 3.0),
        ],
        HiringConstraints(role="Backend Engineer", required_skills=["Java"]),
        limit=2,
    )

    assert len(ids) == 2


def test_score_explanation_includes_matched_constraints() -> None:
    result = RecommendationEngine().generate(
        state(),
        extraction(
            HiringConstraints(
                role="Financial Analyst",
                job_level=JobLevel.GRADUATE,
                required_skills=["Accounting"],
            )
        ),
        decision(DecisionType.RECOMMEND),
        query_result([candidate("financial-accounting-new", 5.0)]),
    )

    recommendation = result.recommendations[0]
    assert recommendation.score.total > 0
    assert "required_skills" in recommendation.matched_constraints
    assert recommendation.reason.evidence


def test_confidence_is_bounded() -> None:
    result = RecommendationEngine().generate(
        state(),
        extraction(HiringConstraints(role="Backend Engineer")),
        decision(DecisionType.RECOMMEND),
        query_result([candidate("core-java-advanced-level-new", 100.0)]),
    )

    assert 0.0 <= result.recommendations[0].confidence <= 1.0


def test_metadata_records_previous_recommendations() -> None:
    result = RecommendationEngine().generate(
        state(prior_ids=["ms-excel-new"]),
        extraction(HiringConstraints(role="Admin Assistant")),
        decision(DecisionType.UPDATE_RECOMMENDATIONS),
        query_result([candidate("ms-excel-new", 5.0)]),
    )

    assert result.metadata.updated_from_previous is True
    assert result.metadata.prior_recommendation_ids == ["ms-excel-new"]


def test_metadata_records_excluded_items() -> None:
    result = RecommendationEngine().generate(
        state("Drop OPQ.", prior_ids=["opq32r"]),
        extraction(HiringConstraints(role="Graduate Trainee")),
        decision(DecisionType.UPDATE_RECOMMENDATIONS),
        query_result([candidate("opq32r", 5.0), candidate("graduate-scenarios", 4.0)]),
    )

    assert result.metadata.excluded_assessment_ids == ["opq32r"]


def test_empty_candidates_returns_warning() -> None:
    result = RecommendationEngine().generate(
        state(),
        extraction(HiringConstraints(role="Unknown Role")),
        decision(DecisionType.RECOMMEND),
        query_result([]),
    )

    assert result.recommendations == []
    assert result.warnings


def test_dictionary_candidate_metadata_is_supported() -> None:
    item = catalog_items()["opq32r"]
    result = RecommendationEngine().generate(
        state(),
        extraction(HiringConstraints(role="Executive Leadership")),
        decision(DecisionType.RECOMMEND),
        CatalogQueryResult(
            candidate_count=1,
            candidate_ids=[item.id],
            top_score=5.0,
            metadata={"candidates": [{"assessment": item, "score": 5.0}]},
        ),
    )

    assert [
        recommendation.assessment.id for recommendation in result.recommendations
    ] == ["opq32r"]
