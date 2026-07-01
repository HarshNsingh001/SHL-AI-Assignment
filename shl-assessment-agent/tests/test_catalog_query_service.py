from typing import Any, cast

from app.models.catalog import Assessment, Catalog
from app.models.constraints import (
    AssessmentPurpose,
    HiringConstraints,
    JobLevel,
    WorkLocation,
)
from app.services.catalog_query_service import CatalogQuery, CatalogQueryService


def make_assessment(
    identifier: str,
    name: str,
    description: str,
    duration: int | None,
    job_levels: list[str],
    languages: list[str],
    test_type: str,
    keys: list[str],
    remote_support: bool = True,
    adaptive_support: bool = False,
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
        languages=languages,
        remote_support=remote_support,
        adaptive_support=adaptive_support,
        test_type=test_type,
        keys=keys,
    )


def sample_catalog() -> Catalog:
    return Catalog(
        assessments=[
            make_assessment(
                "smart-interview-live-coding",
                "Smart Interview Live Coding",
                "Live coding interview for technical roles.",
                None,
                ["Graduate", "Mid-Professional"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "linux-programming-general",
                "Linux Programming (General)",
                "Systems programming and Linux knowledge.",
                25,
                ["Mid-Professional"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "core-java-advanced-level-new",
                "Core Java (Advanced Level) (New)",
                "Advanced Core Java, concurrency, performance, and JVM topics.",
                13,
                ["Mid-Professional", "Professional Individual Contributor"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "spring-new",
                "Spring (New)",
                "Spring framework for backend service development.",
                9,
                ["Mid-Professional"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "sql-new",
                "SQL (New)",
                "SQL and relational database knowledge.",
                9,
                ["Mid-Professional"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "shl-verify-interactive-g",
                "SHL Verify Interactive G+",
                "Inductive, numerical, and deductive reasoning.",
                36,
                ["Graduate", "Mid-Professional"],
                ["English (USA)", "Spanish", "French"],
                "A",
                ["Ability & Aptitude"],
                adaptive_support=True,
            ),
            make_assessment(
                "opq32r",
                "Occupational Personality Questionnaire OPQ32r",
                "Workplace personality and leadership behaviour dimensions.",
                25,
                ["Graduate", "Manager", "Executive"],
                ["English International", "Spanish", "French"],
                "P",
                ["Personality & Behavior"],
            ),
            make_assessment(
                "opq-leadership-report",
                "OPQ Leadership Report",
                "Leadership report generated from OPQ results.",
                None,
                ["Manager", "Executive"],
                ["English International"],
                "P",
                ["Personality & Behavior"],
            ),
            make_assessment(
                "svar-spoken-english-us-new",
                "SVAR Spoken English (US) (New)",
                "Spoken English screen for US contact center work.",
                None,
                ["Entry-Level"],
                ["English (USA)"],
                "K",
                ["Simulations"],
            ),
            make_assessment(
                "contact-center-call-simulation-new",
                "Contact Center Call Simulation (New)",
                "Standalone contact center call simulation.",
                15,
                ["Entry-Level"],
                ["English (USA)"],
                "S",
                ["Simulations"],
            ),
            make_assessment(
                "entry-level-customer-serv-retail-contact-center",
                "Entry Level Customer Serv - Retail & Contact Center",
                "Customer service fit for retail and contact center roles.",
                19,
                ["Entry-Level"],
                ["Spanish", "French", "English (USA)"],
                "P,C",
                ["Personality & Behavior", "Competencies"],
            ),
            make_assessment(
                "financial-accounting-new",
                "Financial Accounting (New)",
                "Finance and accounting knowledge for analyst roles.",
                9,
                ["Graduate"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "graduate-scenarios",
                "Graduate Scenarios",
                "Situational judgment for graduate candidates.",
                None,
                ["Graduate"],
                ["English International"],
                "B",
                ["Biodata & Situational Judgment"],
            ),
            make_assessment(
                "dependability-safety-instrument-dsi",
                "Dependability and Safety Instrument (DSI)",
                "Dependability, reliability, and safety attitudes.",
                10,
                ["Entry-Level"],
                ["Spanish", "English (USA)"],
                "P",
                ["Personality & Behavior"],
            ),
            make_assessment(
                "workplace-health-and-safety-new",
                "Workplace Health and Safety (New)",
                "Workplace health and safety knowledge.",
                9,
                ["Entry-Level"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "global-skills-assessment",
                "Global Skills Assessment",
                "Self-reported skills measure for development.",
                16,
                ["Graduate", "Manager", "Executive"],
                ["English (USA)", "Spanish"],
                "C,K",
                ["Competencies", "Knowledge & Skills"],
            ),
            make_assessment(
                "ms-excel-new",
                "MS Excel (New)",
                "Fast Microsoft Excel knowledge check.",
                6,
                ["Entry-Level"],
                ["English (USA)", "Spanish", "French"],
                "K",
                ["Knowledge & Skills"],
            ),
            make_assessment(
                "microsoft-excel-365-new",
                "Microsoft Excel 365 (New)",
                "Microsoft Excel simulation for daily spreadsheet work.",
                35,
                ["Entry-Level"],
                ["English (USA)"],
                "K,S",
                ["Knowledge & Skills", "Simulations"],
            ),
        ]
    )


def candidate_ids(query: CatalogQuery | HiringConstraints) -> list[str]:
    service = CatalogQueryService(sample_catalog())
    return [candidate.assessment.id for candidate in service.search(query)]


def test_queries_senior_java_backend_assessments() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Backend Engineer",
            job_level=JobLevel.SENIOR,
            required_skills=["Java", "Spring", "SQL"],
            languages=["English"],
            assessment_types=["Knowledge & Skills"],
            technical_role=True,
        )
    )

    assert ids[:3] == [
        "core-java-advanced-level-new",
        "spring-new",
        "sql-new",
    ]


def test_queries_rust_systems_engineering_candidates() -> None:
    ids = candidate_ids(
        CatalogQuery(
            job_levels=["Senior"],
            languages=["English"],
            assessment_keys=["Knowledge & Skills"],
            keywords=["systems", "programming", "coding"],
            skills=["Rust", "Linux", "networking"],
        )
    )

    assert ids[:2] == ["linux-programming-general", "smart-interview-live-coding"]


def test_filters_contact_center_by_language_and_simulation_key() -> None:
    ids = candidate_ids(
        CatalogQuery(
            job_levels=["Entry-Level"],
            languages=["English USA"],
            assessment_keys=["Simulations"],
            keywords=["contact center", "spoken english", "call"],
        )
    )

    assert ids[:2] == [
        "svar-spoken-english-us-new",
        "contact-center-call-simulation-new",
    ]


def test_queries_graduate_finance_assessments() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Financial Analyst",
            job_level=JobLevel.GRADUATE,
            industry="Finance",
            required_skills=["accounting", "numerical"],
            assessment_types=["Knowledge & Skills", "Ability & Aptitude"],
            purpose=AssessmentPurpose.HIRING,
        )
    )

    assert ids[:2] == ["financial-accounting-new", "shl-verify-interactive-g"]


def test_queries_graduate_situational_judgment() -> None:
    ids = candidate_ids(
        CatalogQuery(
            job_levels=["Graduate"],
            assessment_types=["Biodata & Situational Judgment"],
            keywords=["situational judgment graduate"],
        )
    )

    assert ids[0] == "graduate-scenarios"


def test_queries_executive_leadership_reports() -> None:
    ids = candidate_ids(
        CatalogQuery(
            job_levels=["Executive"],
            assessment_keys=["Personality & Behavior"],
            keywords=["leadership"],
        )
    )

    assert ids[:2] == ["opq32r", "opq-leadership-report"]


def test_queries_manufacturing_safety_short_duration() -> None:
    ids = candidate_ids(
        CatalogQuery(
            job_levels=["Entry-Level"],
            assessment_keys=["Personality & Behavior", "Knowledge & Skills"],
            max_duration=16,
            keywords=["safety", "dependability"],
        )
    )

    assert ids[:2] == [
        "dependability-safety-instrument-dsi",
        "workplace-health-and-safety-new",
    ]


def test_filters_by_max_duration() -> None:
    ids = candidate_ids(
        CatalogQuery(
            assessment_keys=["Knowledge & Skills"],
            max_duration=10,
            keywords=["excel"],
        )
    )

    assert ids == ["ms-excel-new"]


def test_filters_by_adaptive_support() -> None:
    ids = candidate_ids(
        CatalogQuery(
            adaptive=True,
            keywords=["reasoning"],
        )
    )

    assert ids == ["shl-verify-interactive-g"]


def test_filters_by_remote_support() -> None:
    catalog = Catalog(
        assessments=[
            make_assessment(
                "onsite-tool",
                "Onsite Tool",
                "Onsite only assessment.",
                10,
                ["Entry-Level"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
                remote_support=False,
            ),
            make_assessment(
                "remote-tool",
                "Remote Tool",
                "Remote assessment.",
                10,
                ["Entry-Level"],
                ["English (USA)"],
                "K",
                ["Knowledge & Skills"],
                remote_support=True,
            ),
        ]
    )

    results = CatalogQueryService(catalog).search(CatalogQuery(remote=False))

    assert [candidate.assessment.id for candidate in results] == ["onsite-tool"]


def test_filters_by_language_partial_match() -> None:
    ids = candidate_ids(CatalogQuery(languages=["English"], limit=20))

    assert "ms-excel-new" in ids
    assert "opq32r" in ids


def test_filters_by_assessment_type_code() -> None:
    ids = candidate_ids(CatalogQuery(assessment_types=["A"], keywords=["reasoning"]))

    assert ids == ["shl-verify-interactive-g"]


def test_filters_by_assessment_key_label() -> None:
    ids = candidate_ids(CatalogQuery(assessment_keys=["Competencies"]))

    assert ids[:2] == [
        "entry-level-customer-serv-retail-contact-center",
        "global-skills-assessment",
    ]


def test_scores_multiple_skill_matches_above_single_match() -> None:
    service = CatalogQueryService(sample_catalog())

    results = service.search(
        CatalogQuery(
            assessment_keys=["Knowledge & Skills"],
            skills=["Java", "Spring", "SQL"],
            languages=["English"],
        )
    )

    assert results[0].assessment.id == "core-java-advanced-level-new"
    assert results[0].score >= results[-1].score


def test_constraints_remote_location_maps_to_remote_filter() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Excel admin assistant",
            work_location=WorkLocation.REMOTE,
            required_skills=["Excel"],
            assessment_types=["Knowledge & Skills"],
        )
    )

    assert ids[0] == "ms-excel-new"


def test_regression_c1_executive_leadership() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Executive Leadership",
            job_level=JobLevel.EXECUTIVE,
            leadership_required=True,
            purpose=AssessmentPurpose.HIRING,
        )
    )

    assert "opq32r" in ids
    assert "opq-leadership-report" in ids


def test_regression_c2_senior_rust_engineer() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Software Engineer",
            job_level=JobLevel.SENIOR,
            required_skills=["Rust"],
            technical_role=True,
            purpose=AssessmentPurpose.HIRING,
        )
    )
    assert "smart-interview-live-coding" in ids
    assert "shl-verify-interactive-g" in ids
    assert "opq32r" in ids


def test_regression_c4_graduate_finance() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Financial Analyst",
            job_level=JobLevel.GRADUATE,
            required_skills=["numerical", "accounting", "statistics"],
            purpose=AssessmentPurpose.HIRING,
        )
    )
    assert "shl-verify-interactive-g" in ids
    assert "financial-accounting-new" in ids
    assert "opq32r" in ids
    assert "graduate-scenarios" in ids


def test_regression_c5_sales_audit() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Sales Representative",
            industry="Sales",
            purpose=AssessmentPurpose.DEVELOPMENT,
        )
    )
    assert "global-skills-assessment" in ids
    assert "opq32r" in ids


def test_regression_c6_plant_operator_safety() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Plant Operator",
            industry="Manufacturing",
            purpose=AssessmentPurpose.HIRING,
        )
    )
    assert "dependability-safety-instrument-dsi" in ids
    assert "workplace-health-and-safety-new" in ids


def test_regression_c8_admin_assistants() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Admin Assistant",
            required_skills=["Excel", "Word"],
            purpose=AssessmentPurpose.HIRING,
        )
    )
    assert "ms-excel-new" in ids
    assert "opq32r" in ids


def test_regression_c10_graduate_management_trainee() -> None:
    ids = candidate_ids(
        HiringConstraints(
            role="Graduate Trainee",
            job_level=JobLevel.GRADUATE,
            leadership_required=True,
            purpose=AssessmentPurpose.HIRING,
        )
    )
    assert "shl-verify-interactive-g" in ids
    assert "opq32r" in ids
    assert "graduate-scenarios" in ids
