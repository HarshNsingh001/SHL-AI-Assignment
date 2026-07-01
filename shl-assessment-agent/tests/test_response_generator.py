from typing import Any, cast

import pytest

from app.models.business_rules import (
    ClarificationRequest,
    ConversationDecision,
    DecisionContext,
    DecisionType,
    RuleEvaluation,
)
from app.models.catalog import Assessment
from app.models.constraints import (
    ConstraintExtractionResult,
    HiringConstraints,
    MissingInformation,
)
from app.models.conversation import (
    ConversationContext,
    ConversationMessage,
    ConversationMessageRole,
    ConversationState,
    RecommendationRecord,
    RecommendationHistory,
)
from app.models.recommendation_engine import (
    AssessmentRecommendation,
    RecommendationMetadata,
    RecommendationReason,
    RecommendationResult,
    RecommendationScore,
)
from app.models.response_generation import (
    GeneratedReply,
    ReplyContext,
    ResponseMetadata,
)
from app.services.response_generator import ResponseGenerator, build_response_generator


def _make_assessment(
    identifier: str = "test-001",
    name: str = "Test Assessment",
    description: str = "A test assessment.",
    job_levels: list[str] | None = None,
    keys: list[str] | None = None,
    test_type: str = "K",
    languages: list[str] | None = None,
    duration: int | None = 20,
    url: str | None = None,
) -> Assessment:
    return Assessment(
        id=identifier,
        name=name,
        url=cast(
            Any,
            url or f"https://www.shl.com/products/product-catalog/view/{identifier}/",
        ),
        description=description,
        duration=duration,
        job_levels=job_levels or ["Graduate"],
        languages=languages or ["English (USA)"],
        remote_support=True,
        adaptive_support=False,
        test_type=test_type,
        keys=keys or ["Knowledge & Skills"],
    )


def _make_recommendation(
    assessment: Assessment | None = None,
    total_score: float = 3.0,
) -> AssessmentRecommendation:
    if assessment is None:
        assessment = _make_assessment()
    score = RecommendationScore(
        catalog_score=1.0,
        constraint_score=0.5,
        context_score=0.5,
        decision_score=0.35,
        total=total_score,
    )
    return AssessmentRecommendation(
        assessment=assessment,
        score=score,
        matched_constraints=["role"],
        reason=RecommendationReason(
            summary="Matched deterministic catalog signal.",
            evidence=["key:Knowledge & Skills"],
        ),
        confidence=0.75,
    )


def _make_recommendation_result(
    recommendations: list[AssessmentRecommendation] | None = None,
    decision_type: str = "recommend",
) -> RecommendationResult:
    recs = recommendations or []
    return RecommendationResult(
        recommendations=recs,
        metadata=RecommendationMetadata(
            decision_type=decision_type,
            requested_limit=10,
            candidate_count=len(recs),
            returned_count=len(recs),
        ),
        warnings=[],
    )


def _make_decision(
    decision_type: DecisionType = DecisionType.RECOMMEND,
    clarification_request: ClarificationRequest | None = None,
    turn_count: int = 1,
    has_previous_recommendations: bool = False,
    has_catalog_candidates: bool = True,
) -> ConversationDecision:
    context = DecisionContext(
        latest_user_message="Test message.",
        turn_count=turn_count,
        has_previous_recommendations=has_previous_recommendations,
        has_catalog_candidates=has_catalog_candidates,
    )
    return ConversationDecision(
        decision_type=decision_type,
        context=context,
        clarification_request=clarification_request,
        rule_evaluations=[
            RuleEvaluation(
                rule_name="test_rule",
                matched=True,
                reason="Test evaluation.",
            )
        ],
    )


def _make_state(
    current_role: str | None = None,
    job_level: str | None = None,
    industry: str | None = None,
    recommended_ids: list[str] | None = None,
) -> ConversationState:
    context = ConversationContext(
        current_role=current_role,
        job_level=job_level,
        industry=industry,
    )
    state = ConversationState(context=context)
    if recommended_ids:
        state.recommended_assessment_ids.extend(recommended_ids)
    return state


def _generator() -> ResponseGenerator:
    return ResponseGenerator()


class TestGeneratedReplyProperties:

    def _base_context(self) -> ReplyContext:
        return ReplyContext(
            decision_type=DecisionType.RECOMMEND.value,
            recommendation_count=2,
        )

    def _base_metadata(self, template: str = "recommend") -> ResponseMetadata:
        return ResponseMetadata(
            template_key=template,
            decision_type=DecisionType.RECOMMEND.value,
            includes_table=True,
            table_row_count=2,
        )

    def test_is_recommendation_reply_true_when_table_present(self) -> None:
        reply = GeneratedReply(
            reply_text="For role:\n\n| # | ...",
            table_markdown="| # | ...",
            decision_type=DecisionType.RECOMMEND.value,
            context=self._base_context(),
            metadata=self._base_metadata(),
        )
        assert reply.is_recommendation_reply is True

    def test_is_recommendation_reply_false_when_no_table(self) -> None:
        reply = GeneratedReply(
            reply_text="Here is a question.",
            table_markdown="",
            decision_type=DecisionType.ASK_CLARIFICATION.value,
            context=ReplyContext(decision_type=DecisionType.ASK_CLARIFICATION.value),
            metadata=ResponseMetadata(
                template_key="clarification",
                decision_type=DecisionType.ASK_CLARIFICATION.value,
            ),
        )
        assert reply.is_recommendation_reply is False

    def test_is_clarification_reply_true(self) -> None:
        reply = GeneratedReply(
            reply_text="What language?",
            table_markdown="",
            decision_type=DecisionType.ASK_CLARIFICATION.value,
            context=ReplyContext(decision_type=DecisionType.ASK_CLARIFICATION.value),
            metadata=ResponseMetadata(
                template_key="clarification",
                decision_type=DecisionType.ASK_CLARIFICATION.value,
            ),
        )
        assert reply.is_clarification_reply is True

    def test_is_clarification_reply_false_for_recommend(self) -> None:
        reply = GeneratedReply(
            reply_text="For role:",
            table_markdown="| # |",
            decision_type=DecisionType.RECOMMEND.value,
            context=self._base_context(),
            metadata=self._base_metadata(),
        )
        assert reply.is_clarification_reply is False

    def test_is_refusal_reply_true(self) -> None:
        reply = GeneratedReply(
            reply_text="That is outside my scope.",
            table_markdown="",
            decision_type=DecisionType.REFUSE.value,
            context=ReplyContext(decision_type=DecisionType.REFUSE.value),
            metadata=ResponseMetadata(
                template_key="refuse",
                decision_type=DecisionType.REFUSE.value,
            ),
        )
        assert reply.is_refusal_reply is True

    def test_is_refusal_reply_false_for_recommend(self) -> None:
        reply = GeneratedReply(
            reply_text="Recommendations:",
            table_markdown="| # |",
            decision_type=DecisionType.RECOMMEND.value,
            context=self._base_context(),
            metadata=self._base_metadata(),
        )
        assert reply.is_refusal_reply is False


class TestClarificationReply:

    def test_reply_text_contains_question(self) -> None:
        gen = _generator()
        clarification = ClarificationRequest(
            question="What language are the calls in?",
            missing_field="languages",
            reason="Contact center screening depends on spoken-language coverage.",
        )
        decision = _make_decision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_request=clarification,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result(
                decision_type="ask_clarification"
            ),
            conversation_state=_make_state(),
        )

        assert "What language are the calls in?" in result.reply_text

    def test_no_table_in_clarification_reply(self) -> None:
        gen = _generator()
        clarification = ClarificationRequest(
            question="Which role are you hiring for?",
            missing_field="role",
            reason="A role is required before assessment selection.",
        )
        decision = _make_decision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_request=clarification,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result(
                decision_type="ask_clarification"
            ),
            conversation_state=_make_state(),
        )

        assert result.table_markdown == ""
        assert not result.is_recommendation_reply

    def test_decision_type_is_ask_clarification(self) -> None:
        gen = _generator()
        clarification = ClarificationRequest(
            question="Is this for hiring or development?",
            missing_field="purpose",
            reason="Leadership requests need a purpose before selection.",
        )
        decision = _make_decision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_request=clarification,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result(
                decision_type="ask_clarification"
            ),
            conversation_state=_make_state(),
        )

        assert result.decision_type == DecisionType.ASK_CLARIFICATION.value

    def test_template_key_is_clarification(self) -> None:
        gen = _generator()
        clarification = ClarificationRequest(
            question="Is this a senior IC or tech lead role?",
            missing_field="seniority",
            reason="Senior technical roles need ownership context.",
        )
        decision = _make_decision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_request=clarification,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result(
                decision_type="ask_clarification"
            ),
            conversation_state=_make_state(),
        )

        assert result.metadata.template_key == "clarification"

    def test_no_clarification_request_produces_fallback_text(self) -> None:
        gen = _generator()
        decision = _make_decision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_request=None,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result(
                decision_type="ask_clarification"
            ),
            conversation_state=_make_state(),
        )

        assert result.reply_text != ""
        assert "?" in result.reply_text or "more" in result.reply_text.casefold()

    def test_is_clarification_reply_property(self) -> None:
        gen = _generator()
        clarification = ClarificationRequest(
            question="Which English accent fits the operation?",
            missing_field="language_variant",
            reason="English spoken-language screens vary by accent.",
        )
        decision = _make_decision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_request=clarification,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result(
                decision_type="ask_clarification"
            ),
            conversation_state=_make_state(),
        )

        assert result.is_clarification_reply is True

    def test_context_contains_question(self) -> None:
        gen = _generator()
        question_text = "What language are the calls in?"
        clarification = ClarificationRequest(
            question=question_text,
            missing_field="languages",
            reason="Contact center screening depends on spoken-language coverage.",
        )
        decision = _make_decision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_request=clarification,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result(
                decision_type="ask_clarification"
            ),
            conversation_state=_make_state(),
        )

        assert result.context.clarification_question == question_text


class TestRecommendReply:

    def _multi_rec_result(self) -> RecommendationResult:
        a1 = _make_assessment(
            "java-adv",
            "Core Java (Advanced Level) (New)",
            "Java.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            ["English (USA)"],
            13,
        )
        a2 = _make_assessment(
            "sql-new",
            "SQL (New)",
            "SQL.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            ["English (USA)"],
            9,
        )
        a3 = _make_assessment(
            "opq32r",
            "Occupational Personality Questionnaire OPQ32r",
            "Personality.",
            ["Graduate", "Manager", "Executive"],
            ["Personality & Behavior"],
            "P",
            ["English International", "Spanish"],
            25,
        )
        return _make_recommendation_result(
            recommendations=[
                _make_recommendation(a1, 4.0),
                _make_recommendation(a2, 3.5),
                _make_recommendation(a3, 3.0),
            ]
        )

    def test_reply_contains_markdown_table(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "|" in result.reply_text
        assert result.table_markdown != ""

    def test_table_has_correct_row_count(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.metadata.table_row_count == 3

    def test_table_contains_assessment_names(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "Core Java (Advanced Level) (New)" in result.reply_text
        assert "SQL (New)" in result.reply_text
        assert "Occupational Personality Questionnaire OPQ32r" in result.reply_text

    def test_table_contains_urls(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "shl.com" in result.reply_text

    def test_framing_sentence_includes_role(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        state = _make_state(current_role="Software Engineer", job_level="Senior")
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=state,
        )

        assert "software engineer" in result.reply_text.casefold()

    def test_decision_type_field_is_recommend(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.decision_type == "recommend"

    def test_metadata_includes_table_flag(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.metadata.includes_table is True

    def test_empty_recommendations_returns_no_table(self) -> None:
        gen = _generator()
        recs = _make_recommendation_result(
            recommendations=[], decision_type="recommend"
        )
        decision = _make_decision(DecisionType.RECOMMEND, has_catalog_candidates=False)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.table_markdown == ""
        assert result.metadata.template_key == "recommend_empty"

    def test_is_recommendation_reply_true(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.is_recommendation_reply is True

    def test_row_numbers_are_sequential(self) -> None:
        gen = _generator()
        recs = self._multi_rec_result()
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        table_lines = [
            ln
            for ln in result.table_markdown.splitlines()
            if ln.startswith("| ") and not ln.startswith("| #") and "---" not in ln
        ]
        for i, line in enumerate(table_lines, start=1):
            assert f"| {i} |" in line, f"Row {i} missing from table"


class TestUpdateRecommendationsReply:

    def _update_result(self) -> RecommendationResult:
        a1 = _make_assessment(
            "java-adv",
            "Core Java (Advanced Level) (New)",
            "Java.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            ["English (USA)"],
            13,
        )
        a2 = _make_assessment(
            "docker-new",
            "Docker (New)",
            "Docker.",
            ["Mid-Professional"],
            ["Knowledge & Skills"],
            "K",
            ["English (USA)"],
            10,
        )
        return _make_recommendation_result(
            recommendations=[
                _make_recommendation(a1, 4.0),
                _make_recommendation(a2, 3.2),
            ],
            decision_type="update_recommendations",
        )

    def test_reply_contains_table(self) -> None:
        gen = _generator()
        recs = self._update_result()
        decision = _make_decision(
            DecisionType.UPDATE_RECOMMENDATIONS,
            has_previous_recommendations=True,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(recommended_ids=["old-001"]),
        )

        assert result.table_markdown != ""
        assert result.metadata.table_row_count == 2

    def test_reply_acknowledges_update(self) -> None:
        gen = _generator()
        recs = self._update_result()
        decision = _make_decision(
            DecisionType.UPDATE_RECOMMENDATIONS,
            has_previous_recommendations=True,
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(recommended_ids=["old-001"]),
        )

        first_line = result.reply_text.splitlines()[0].casefold()
        update_words = {"updated", "shortlist", "added", "removed", "confirmed"}
        assert any(word in first_line for word in update_words)

    def test_decision_type_is_update(self) -> None:
        gen = _generator()
        recs = self._update_result()
        decision = _make_decision(
            DecisionType.UPDATE_RECOMMENDATIONS, has_previous_recommendations=True
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(recommended_ids=["old-001"]),
        )

        assert result.decision_type == "update_recommendations"

    def test_template_key_is_update(self) -> None:
        gen = _generator()
        recs = self._update_result()
        decision = _make_decision(
            DecisionType.UPDATE_RECOMMENDATIONS, has_previous_recommendations=True
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(recommended_ids=["old-001"]),
        )

        assert result.metadata.template_key == "update"

    def test_empty_update_returns_update_empty_template(self) -> None:
        gen = _generator()
        recs = _make_recommendation_result([], "update_recommendations")
        decision = _make_decision(
            DecisionType.UPDATE_RECOMMENDATIONS, has_previous_recommendations=True
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(recommended_ids=["old-001"]),
        )

        assert result.table_markdown == ""
        assert result.metadata.template_key == "update_empty"

    def test_updated_assessment_names_in_table(self) -> None:
        gen = _generator()
        recs = self._update_result()
        decision = _make_decision(
            DecisionType.UPDATE_RECOMMENDATIONS, has_previous_recommendations=True
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(recommended_ids=["old-001"]),
        )

        assert "Core Java (Advanced Level) (New)" in result.table_markdown
        assert "Docker (New)" in result.table_markdown


class TestRefuseReply:

    def _refusal_result(self) -> RecommendationResult:
        return _make_recommendation_result([], "refuse")

    def test_refusal_reply_has_no_table(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.REFUSE)
        result = gen.generate(
            decision=decision,
            recommendation_result=self._refusal_result(),
            conversation_state=_make_state(),
        )

        assert result.table_markdown == ""
        assert not result.is_recommendation_reply

    def test_refusal_reply_mentions_scope(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.REFUSE)
        result = gen.generate(
            decision=decision,
            recommendation_result=self._refusal_result(),
            conversation_state=_make_state(),
        )

        lower = result.reply_text.casefold()
        assert any(
            word in lower for word in ("outside", "scope", "advise", "can't", "cannot")
        )

    def test_refusal_reply_offers_alternative(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.REFUSE)
        result = gen.generate(
            decision=decision,
            recommendation_result=self._refusal_result(),
            conversation_state=_make_state(),
        )

        lower = result.reply_text.casefold()
        assert any(
            word in lower for word in ("assessment", "shortlist", "help", "happy")
        )

    def test_decision_type_is_refuse(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.REFUSE)
        result = gen.generate(
            decision=decision,
            recommendation_result=self._refusal_result(),
            conversation_state=_make_state(),
        )

        assert result.decision_type == "refuse"

    def test_is_refusal_reply_property(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.REFUSE)
        result = gen.generate(
            decision=decision,
            recommendation_result=self._refusal_result(),
            conversation_state=_make_state(),
        )

        assert result.is_refusal_reply is True

    def test_template_key_is_refuse(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.REFUSE)
        result = gen.generate(
            decision=decision,
            recommendation_result=self._refusal_result(),
            conversation_state=_make_state(),
        )

        assert result.metadata.template_key == "refuse"


class TestInsufficientInformationReply:

    def _insuff_result(self) -> RecommendationResult:
        return _make_recommendation_result([], "insufficient_information")

    def test_no_table_in_insufficient_reply(self) -> None:
        gen = _generator()
        decision = _make_decision(
            DecisionType.INSUFFICIENT_INFORMATION, has_catalog_candidates=False
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=self._insuff_result(),
            conversation_state=_make_state(),
        )

        assert result.table_markdown == ""

    def test_reply_invites_more_detail(self) -> None:
        gen = _generator()
        decision = _make_decision(
            DecisionType.INSUFFICIENT_INFORMATION, has_catalog_candidates=False
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=self._insuff_result(),
            conversation_state=_make_state(),
        )

        lower = result.reply_text.casefold()
        assert any(
            phrase in lower
            for phrase in ("more detail", "could you", "share", "information")
        )

    def test_reply_mentions_role_when_available(self) -> None:
        gen = _generator()
        decision = _make_decision(
            DecisionType.INSUFFICIENT_INFORMATION, has_catalog_candidates=False
        )
        state = _make_state(current_role="Financial Analyst")
        result = gen.generate(
            decision=decision,
            recommendation_result=self._insuff_result(),
            conversation_state=state,
        )

        assert "financial analyst" in result.reply_text.casefold()

    def test_decision_type_is_insufficient(self) -> None:
        gen = _generator()
        decision = _make_decision(
            DecisionType.INSUFFICIENT_INFORMATION, has_catalog_candidates=False
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=self._insuff_result(),
            conversation_state=_make_state(),
        )

        assert result.decision_type == "insufficient_information"

    def test_template_key_is_insufficient(self) -> None:
        gen = _generator()
        decision = _make_decision(
            DecisionType.INSUFFICIENT_INFORMATION, has_catalog_candidates=False
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=self._insuff_result(),
            conversation_state=_make_state(),
        )

        assert result.metadata.template_key == "insufficient_information"

    def test_is_refusal_reply_false(self) -> None:
        gen = _generator()
        decision = _make_decision(
            DecisionType.INSUFFICIENT_INFORMATION, has_catalog_candidates=False
        )
        result = gen.generate(
            decision=decision,
            recommendation_result=self._insuff_result(),
            conversation_state=_make_state(),
        )

        assert result.is_refusal_reply is False


class TestTableRendering:

    def _assessment_with_many_languages(self) -> Assessment:
        return _make_assessment(
            "opq32r",
            "Occupational Personality Questionnaire OPQ32r",
            "Personality.",
            ["Graduate", "Manager"],
            ["Personality & Behavior"],
            "P",
            languages=[
                "English International",
                "French (Canada)",
                "Portuguese",
                "Chinese Simplified",
                "Spanish",
                "German",
            ],
            duration=25,
        )

    def test_table_header_present(self) -> None:
        gen = _generator()
        rec = _make_recommendation(_make_assessment())
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert (
            "| # | Name | Test Type | Keys | Duration | Languages | URL |"
            in result.table_markdown
        )

    def test_separator_row_present(self) -> None:
        gen = _generator()
        rec = _make_recommendation(_make_assessment())
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "|---|" in result.table_markdown

    def test_language_overflow_notation(self) -> None:
        gen = _generator()
        assessment = self._assessment_with_many_languages()
        rec = _make_recommendation(assessment)
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "_(+2 more)_" in result.table_markdown

    def test_duration_shown_in_minutes(self) -> None:
        gen = _generator()
        assessment = _make_assessment(duration=36)
        rec = _make_recommendation(assessment)
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "36 minutes" in result.table_markdown

    def test_no_duration_shows_dash(self) -> None:
        gen = _generator()
        assessment = _make_assessment(duration=None)
        rec = _make_recommendation(assessment)
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "| — |" in result.table_markdown or "| — " in result.table_markdown

    def test_url_in_angle_brackets(self) -> None:
        gen = _generator()
        assessment = _make_assessment("verify-g-plus")
        rec = _make_recommendation(assessment)
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "<https://" in result.table_markdown

    def test_custom_max_inline_languages(self) -> None:
        gen = ResponseGenerator(max_inline_languages=2)
        assessment = self._assessment_with_many_languages()
        rec = _make_recommendation(assessment)
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "_(+4 more)_" in result.table_markdown

    def test_single_language_no_overflow(self) -> None:
        gen = _generator()
        assessment = _make_assessment(languages=["English (USA)"])
        rec = _make_recommendation(assessment)
        recs = _make_recommendation_result([rec])
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "_(+" not in result.table_markdown
        assert "English (USA)" in result.table_markdown

    def test_empty_languages_shows_dash(self) -> None:
        gen = _generator()

        result = gen._format_languages([])  # noqa: SLF001
        assert result == "—"


class TestContextBuilder:

    def test_decision_type_propagated(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.RECOMMEND)
        recs = _make_recommendation_result([_make_recommendation()])
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.context.decision_type == "recommend"

    def test_recommendation_count_in_context(self) -> None:
        gen = _generator()
        a1 = _make_assessment("a1")
        a2 = _make_assessment("a2")
        recs = _make_recommendation_result(
            [_make_recommendation(a1), _make_recommendation(a2)]
        )
        decision = _make_decision(DecisionType.RECOMMEND)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.context.recommendation_count == 2

    def test_has_prior_recommendations_true(self) -> None:
        gen = _generator()
        recs = _make_recommendation_result([_make_recommendation()])
        decision = _make_decision(DecisionType.RECOMMEND)
        state = _make_state(recommended_ids=["prior-001"])
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=state,
        )

        assert result.context.has_prior_recommendations is True

    def test_has_prior_recommendations_false(self) -> None:
        gen = _generator()
        recs = _make_recommendation_result([_make_recommendation()])
        decision = _make_decision(DecisionType.RECOMMEND)
        state = _make_state(recommended_ids=None)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=state,
        )

        assert result.context.has_prior_recommendations is False

    def test_role_propagated_from_state(self) -> None:
        gen = _generator()
        recs = _make_recommendation_result([_make_recommendation()])
        decision = _make_decision(DecisionType.RECOMMEND)
        state = _make_state(current_role="Financial Analyst")
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=state,
        )

        assert result.context.role == "Financial Analyst"

    def test_conversation_turn_from_decision(self) -> None:
        gen = _generator()
        recs = _make_recommendation_result([_make_recommendation()])
        decision = _make_decision(DecisionType.RECOMMEND, turn_count=5)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.context.conversation_turn == 5

    def test_missing_fields_populated_for_clarification(self) -> None:
        gen = _generator()
        clarification = ClarificationRequest(
            question="Which role are you hiring for?",
            missing_field="role",
            reason="A role is required.",
        )
        decision = _make_decision(
            DecisionType.ASK_CLARIFICATION,
            clarification_request=clarification,
        )
        recs = _make_recommendation_result([], "ask_clarification")
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert "role" in result.context.missing_fields

    def test_missing_fields_empty_when_no_clarification(self) -> None:
        gen = _generator()
        recs = _make_recommendation_result([_make_recommendation()])
        decision = _make_decision(DecisionType.RECOMMEND, clarification_request=None)
        result = gen.generate(
            decision=decision,
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.context.missing_fields == []


class TestResponseMetadataInvariants:

    @pytest.mark.parametrize(
        "decision_type",
        [
            DecisionType.ASK_CLARIFICATION,
            DecisionType.RECOMMEND,
            DecisionType.UPDATE_RECOMMENDATIONS,
            DecisionType.REFUSE,
            DecisionType.INSUFFICIENT_INFORMATION,
        ],
    )
    def test_decision_type_matches_for_all_types(
        self, decision_type: DecisionType
    ) -> None:
        gen = _generator()
        clarification = None
        if decision_type is DecisionType.ASK_CLARIFICATION:
            clarification = ClarificationRequest(
                question="Question?",
                missing_field="role",
                reason="Reason.",
            )
        recs = []
        if decision_type in {
            DecisionType.RECOMMEND,
            DecisionType.UPDATE_RECOMMENDATIONS,
        }:
            recs = [_make_recommendation()]
        result = gen.generate(
            decision=_make_decision(decision_type, clarification_request=clarification),
            recommendation_result=_make_recommendation_result(
                recs, decision_type.value
            ),
            conversation_state=_make_state(),
        )

        assert result.metadata.decision_type == decision_type.value

    @pytest.mark.parametrize(
        "decision_type",
        [
            DecisionType.ASK_CLARIFICATION,
            DecisionType.REFUSE,
            DecisionType.INSUFFICIENT_INFORMATION,
        ],
    )
    def test_no_table_for_non_recommendation_types(
        self, decision_type: DecisionType
    ) -> None:
        gen = _generator()
        clarification = None
        if decision_type is DecisionType.ASK_CLARIFICATION:
            clarification = ClarificationRequest(
                question="Question?",
                missing_field="role",
                reason="Reason.",
            )
        result = gen.generate(
            decision=_make_decision(decision_type, clarification_request=clarification),
            recommendation_result=_make_recommendation_result([], decision_type.value),
            conversation_state=_make_state(),
        )

        assert result.metadata.includes_table is False
        assert result.metadata.table_row_count == 0

    def test_table_row_count_matches_table(self) -> None:
        gen = _generator()
        a1 = _make_assessment(
            "a1",
            "Alpha Assessment",
            "A.",
            ["Graduate"],
            ["Ability & Aptitude"],
            "A",
            ["English (USA)"],
            20,
        )
        a2 = _make_assessment(
            "a2",
            "Beta Assessment",
            "B.",
            ["Graduate"],
            ["Knowledge & Skills"],
            "K",
            ["English (USA)"],
            10,
        )
        a3 = _make_assessment(
            "a3",
            "Gamma Assessment",
            "G.",
            ["Graduate"],
            ["Personality & Behavior"],
            "P",
            ["English (USA)"],
            25,
        )
        recs = _make_recommendation_result(
            [
                _make_recommendation(a1),
                _make_recommendation(a2),
                _make_recommendation(a3),
            ]
        )
        result = gen.generate(
            decision=_make_decision(DecisionType.RECOMMEND),
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert result.metadata.table_row_count == 3
        assert result.metadata.includes_table is True


class TestBuildResponseGeneratorFactory:

    def test_returns_response_generator_instance(self) -> None:
        gen = build_response_generator()
        assert isinstance(gen, ResponseGenerator)

    def test_default_max_inline_languages(self) -> None:
        gen = build_response_generator()
        assert gen.max_inline_languages == 4

    def test_custom_max_inline_languages(self) -> None:
        gen = build_response_generator(max_inline_languages=6)
        assert gen.max_inline_languages == 6

    def test_factory_generator_produces_valid_output(self) -> None:
        gen = build_response_generator()
        recs = _make_recommendation_result([_make_recommendation()])
        result = gen.generate(
            decision=_make_decision(DecisionType.RECOMMEND),
            recommendation_result=recs,
            conversation_state=_make_state(),
        )

        assert isinstance(result, GeneratedReply)
        assert result.reply_text != ""


class TestGeneratorNeverChangesRecommendations:

    def test_recommendations_unchanged_after_generate(self) -> None:
        gen = _generator()
        a1 = _make_assessment(
            "a1",
            "Alpha",
            "A.",
            ["Graduate"],
            ["Ability & Aptitude"],
            "A",
            ["English (USA)"],
            20,
        )
        original_recs = [_make_recommendation(a1)]
        recs_result = _make_recommendation_result(original_recs)
        before_ids = [r.assessment.id for r in recs_result.recommendations]

        gen.generate(
            decision=_make_decision(DecisionType.RECOMMEND),
            recommendation_result=recs_result,
            conversation_state=_make_state(),
        )

        after_ids = [r.assessment.id for r in recs_result.recommendations]
        assert before_ids == after_ids

    def test_decision_unchanged_after_generate(self) -> None:
        gen = _generator()
        decision = _make_decision(DecisionType.RECOMMEND)
        original_type = decision.decision_type

        gen.generate(
            decision=decision,
            recommendation_result=_make_recommendation_result([_make_recommendation()]),
            conversation_state=_make_state(),
        )

        assert decision.decision_type is original_type

    def test_conversation_state_unchanged_after_generate(self) -> None:
        gen = _generator()
        state = _make_state(current_role="Software Engineer")
        original_role = state.context.current_role

        gen.generate(
            decision=_make_decision(DecisionType.RECOMMEND),
            recommendation_result=_make_recommendation_result([_make_recommendation()]),
            conversation_state=state,
        )

        assert state.context.current_role == original_role
