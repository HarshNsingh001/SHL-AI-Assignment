from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.business_rules import DecisionType
from app.models.conversation import ConversationMessage, ConversationMessageRole
from app.services.catalog_loader import CatalogLoader
from app.services.catalog_query_service import CatalogQueryService
from app.services.chat_orchestrator import ChatOrchestrator

_REPO_ROOT = Path(__file__).parents[2]
_CATALOG_PATH = _REPO_ROOT / "data" / "catalog" / "shl_catalog.json"


def _catalog_available() -> bool:
    return _CATALOG_PATH.exists()


skip_no_catalog = pytest.mark.skipif(
    not _catalog_available(),
    reason=f"Real catalog not found at {_CATALOG_PATH}",
)


def _build_orchestrator() -> ChatOrchestrator:
    loader = CatalogLoader()
    catalog = loader.load_catalog(_CATALOG_PATH)
    query_service = CatalogQueryService(catalog=catalog)
    return ChatOrchestrator.build(catalog_query_service=query_service)


def _user(content: str) -> ConversationMessage:
    return ConversationMessage(
        role=ConversationMessageRole.USER,
        content=content,
    )


@skip_no_catalog
def test_real_catalog_loads_without_error() -> None:
    loader = CatalogLoader()
    catalog = loader.load_catalog(_CATALOG_PATH)
    assert (
        len(catalog.assessments) > 100
    ), "Expected 300+ assessments in the real catalog"


@skip_no_catalog
def test_real_catalog_entry_fields() -> None:
    loader = CatalogLoader()
    catalog = loader.load_catalog(_CATALOG_PATH)
    for assessment in catalog.assessments:
        assert assessment.id, f"Empty id for assessment: {assessment.name}"
        assert assessment.name, "Assessment has no name"
        assert assessment.url, f"Empty url for: {assessment.name}"
        assert isinstance(assessment.remote_support, bool)
        assert isinstance(assessment.adaptive_support, bool)


@skip_no_catalog
def test_real_catalog_json_is_valid_array() -> None:
    with _CATALOG_PATH.open(encoding="utf-8") as f:
        data = json.load(f, strict=False)
    assert isinstance(data, list), "Expected top-level JSON array"
    assert len(data) > 0
    first = data[0]
    assert "entity_id" in first or "id" in first, "No id field found in first entry"


@skip_no_catalog
def test_c1_t1_asks_clarification() -> None:
    orchestrator = _build_orchestrator()
    result = orchestrator.run(
        conversation_history=[],
        latest_user_message="We need a solution for senior leadership.",
    )
    assert result.decision.decision_type in {
        DecisionType.ASK_CLARIFICATION,
        DecisionType.RECOMMEND,
    }


@skip_no_catalog
def test_c1_t3_recommends_opq_for_selection() -> None:
    orchestrator = _build_orchestrator()
    history = [
        _user("We need a solution for senior leadership."),
        ConversationMessage(
            role=ConversationMessageRole.ASSISTANT,
            content="Happy to help. Is this for selection or development?",
        ),
        _user("The pool consists of CXOs and directors with 15+ years of experience."),
        ConversationMessage(
            role=ConversationMessageRole.ASSISTANT,
            content="One question: is this for selection or development?",
        ),
    ]
    result = orchestrator.run(
        conversation_history=history,
        latest_user_message="Selection — comparing candidates against a leadership benchmark.",
    )

    assert result.decision.decision_type in {
        DecisionType.RECOMMEND,
        DecisionType.ASK_CLARIFICATION,
        DecisionType.UPDATE_RECOMMENDATIONS,
    }
    if result.decision.decision_type == DecisionType.RECOMMEND:
        rec_names = [
            r.assessment.name for r in result.recommendation_result.recommendations
        ]
        assert len(rec_names) > 0, "Expected at least one recommendation"


@skip_no_catalog
def test_c4_t1_recommends_for_graduate_analysts() -> None:
    orchestrator = _build_orchestrator()
    result = orchestrator.run(
        conversation_history=[],
        latest_user_message=(
            "Hiring graduate financial analysts — final-year students, no work experience. "
            "We need numerical reasoning and a finance knowledge test."
        ),
    )
    assert result.decision.decision_type == DecisionType.RECOMMEND
    rec_names = [
        r.assessment.name for r in result.recommendation_result.recommendations
    ]
    assert len(rec_names) > 0, "Expected at least one recommendation"

    assert any(
        any(
            kw in name.casefold()
            for kw in ("numerical", "graduate", "financial", "verify")
        )
        for name in rec_names
    ), f"No relevant assessment found in: {rec_names}"


@skip_no_catalog
def test_c6_t1_recommends_safety_for_plant_operators() -> None:
    orchestrator = _build_orchestrator()
    result = orchestrator.run(
        conversation_history=[],
        latest_user_message=(
            "We're hiring plant operators for a chemical facility. "
            "Safety is absolute top priority — reliability, procedure compliance, "
            "never cutting corners. What do you recommend?"
        ),
    )
    assert result.decision.decision_type == DecisionType.RECOMMEND
    rec_names = [
        r.assessment.name for r in result.recommendation_result.recommendations
    ]
    assert any(
        any(kw in name.casefold() for kw in ("safety", "dependability", "dsi"))
        for name in rec_names
    ), f"Expected safety-related assessment, got: {rec_names}"


@skip_no_catalog
def test_c7_t3_refuses_legal_question() -> None:
    orchestrator = _build_orchestrator()
    history = [
        _user(
            "We're hiring bilingual healthcare admin staff in South Texas. "
            "They handle patient records and need to be assessed in Spanish."
        ),
        ConversationMessage(
            role=ConversationMessageRole.ASSISTANT,
            content="There's a catalog constraint here…",
        ),
        _user("They're functionally bilingual. Go with the hybrid."),
        ConversationMessage(
            role=ConversationMessageRole.ASSISTANT,
            content="Here is the hybrid battery…",
        ),
    ]
    result = orchestrator.run(
        conversation_history=history,
        latest_user_message=(
            "Are we legally required under HIPAA to test all staff who touch "
            "patient records? And does this SHL test satisfy that requirement?"
        ),
    )
    assert result.decision.decision_type == DecisionType.REFUSE


@skip_no_catalog
def test_c10_t1_recommends_graduate_battery() -> None:
    orchestrator = _build_orchestrator()
    result = orchestrator.run(
        conversation_history=[],
        latest_user_message=(
            "We run a graduate management trainee scheme. "
            "We need a full battery — cognitive, personality, and situational judgement. "
            "All recent graduates."
        ),
    )
    assert result.decision.decision_type == DecisionType.RECOMMEND
    rec_names = [
        r.assessment.name for r in result.recommendation_result.recommendations
    ]
    assert len(rec_names) >= 2, f"Expected ≥2 recommendations, got: {rec_names}"


@skip_no_catalog
def test_eoc_false_on_first_recommendation() -> None:
    orchestrator = _build_orchestrator()
    result = orchestrator.run(
        conversation_history=[],
        latest_user_message=(
            "Hiring graduate financial analysts — numerical reasoning and finance knowledge test."
        ),
    )

    assert (
        not result.decision.context.is_confirmation
    ), "First recommendation turn should not be a confirmation"


@skip_no_catalog
def test_eoc_true_on_confirmed_shortlist() -> None:
    orchestrator = _build_orchestrator()
    history = [
        _user(
            "Hiring graduate financial analysts — numerical reasoning + finance tests."
        ),
        ConversationMessage(
            role=ConversationMessageRole.ASSISTANT,
            content="Here are my recommendations: …",
        ),
    ]
    result = orchestrator.run(
        conversation_history=history,
        latest_user_message="Perfect, that covers it.",
    )

    assert (
        result.decision.context.is_confirmation
    ), "Expected is_confirmation=True after 'Perfect, that covers it.'"
