import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.models.business_rules import ConversationDecision, DecisionType
from app.models.catalog import Assessment
from app.models.conversation import ConversationState
from app.models.recommendation_engine import (
    AssessmentRecommendation,
    RecommendationResult,
)
from app.models.response_generation import (
    GeneratedReply,
    ReplyContext,
    ResponseMetadata,
)

_TABLE_HEADER = (
    "| # | Name | Test Type | Keys | Duration | Languages | URL |\n"
    "|---|------|-----------|------|----------|-----------|-----|"
)

_MAX_INLINE_LANGUAGES = 4


@dataclass(frozen=True)
class ResponseGenerator:

    max_inline_languages: int = field(default=_MAX_INLINE_LANGUAGES)

    def generate(
        self,
        decision: ConversationDecision,
        recommendation_result: RecommendationResult,
        conversation_state: ConversationState,
    ) -> GeneratedReply:
        context = self._build_context(
            decision=decision,
            recommendation_result=recommendation_result,
            conversation_state=conversation_state,
        )
        dt = decision.decision_type
        warnings: list[str] = []

        if dt is DecisionType.ASK_CLARIFICATION:
            reply_text, table_md, template_key = self._render_clarification(
                decision, context
            )
        elif dt is DecisionType.RECOMMEND:
            reply_text, table_md, template_key = self._render_recommend(
                recommendation_result, context
            )
        elif dt is DecisionType.UPDATE_RECOMMENDATIONS:
            reply_text, table_md, template_key = self._render_update(
                recommendation_result, context
            )
        elif dt is DecisionType.REFUSE:
            reply_text, table_md, template_key = self._render_refuse(context)
        elif dt is DecisionType.INSUFFICIENT_INFORMATION:
            reply_text, table_md, template_key = self._render_insufficient(context)
        else:

            reply_text = "I'm unable to process this request."
            table_md = ""
            template_key = "fallback"
            warnings.append(
                f"Unrecognised decision type '{dt}'; used fallback template."
            )

        metadata = ResponseMetadata(
            template_key=template_key,
            decision_type=dt.value,
            includes_table=bool(table_md),
            table_row_count=self._count_table_rows(table_md),
            warnings=warnings,
        )

        return GeneratedReply(
            reply_text=reply_text,
            table_markdown=table_md,
            decision_type=dt.value,
            context=context,
            metadata=metadata,
        )

    def _build_context(
        self,
        decision: ConversationDecision,
        recommendation_result: RecommendationResult,
        conversation_state: ConversationState,
    ) -> ReplyContext:
        clarification_question: str | None = None
        missing_field: str | None = None
        if decision.clarification_request is not None:
            clarification_question = decision.clarification_request.question
            missing_field = decision.clarification_request.missing_field

        missing_fields: list[str] = [missing_field] if missing_field else []

        has_prior = bool(
            conversation_state.recommended_assessment_ids
            or conversation_state.recommendation_history.records
        )

        return ReplyContext(
            decision_type=decision.decision_type.value,
            recommendation_count=len(recommendation_result.recommendations),
            has_prior_recommendations=has_prior,
            clarification_question=clarification_question,
            missing_fields=missing_fields,
            conversation_turn=decision.context.turn_count,
            role=conversation_state.context.current_role,
            job_level=conversation_state.context.job_level,
            industry=conversation_state.context.industry,
        )

    def _render_clarification(
        self,
        decision: ConversationDecision,
        context: ReplyContext,
    ) -> tuple[str, str, str]:
        if decision.clarification_request is not None:
            question = decision.clarification_request.question
            reason = decision.clarification_request.reason

            preamble = self._clarification_preamble(reason)
            if preamble:
                reply_text = f"{preamble} {question}"
            else:
                reply_text = question
        else:
            reply_text = (
                "Before I can build a shortlist, could you tell me a bit more "
                "about the role and its requirements?"
            )

        return reply_text, "", "clarification"

    def _render_recommend(
        self,
        recommendation_result: RecommendationResult,
        context: ReplyContext,
    ) -> tuple[str, str, str]:
        recommendations = recommendation_result.recommendations

        if not recommendations:

            reply_text = (
                "I wasn't able to find catalog items matching all of your "
                "requirements.  Could you share more details about the role "
                "or relax some of the constraints?"
            )
            return reply_text, "", "recommend_empty"

        framing = self._recommend_framing(context)
        table_md = self._render_table(recommendations)
        reply_text = f"{framing}\n\n{table_md}"

        return reply_text, table_md, "recommend"

    def _render_update(
        self,
        recommendation_result: RecommendationResult,
        context: ReplyContext,
    ) -> tuple[str, str, str]:
        recommendations = recommendation_result.recommendations

        if not recommendations:
            reply_text = (
                "Updated. The shortlist is now empty — let me know what you'd "
                "like to add."
            )
            return reply_text, "", "update_empty"

        ack = self._update_acknowledgement(context)
        table_md = self._render_table(recommendations)
        reply_text = f"{ack}\n\n{table_md}"

        return reply_text, table_md, "update"

    def _render_refuse(
        self,
        context: ReplyContext,
    ) -> tuple[str, str, str]:
        reply_text = (
            "That's outside what I can advise on — I help select SHL "
            "assessments, but I can't interpret legal or regulatory obligations "
            "or provide general HR advice.\n\n"
            "If you'd like to build or refine an assessment shortlist for a "
            "specific role, I'm happy to help with that."
        )
        return reply_text, "", "refuse"

    def _render_insufficient(
        self,
        context: ReplyContext,
    ) -> tuple[str, str, str]:
        role_part = f"the **{context.role}**" if context.role else "this role"
        reply_text = (
            f"I wasn't able to find catalog assessments matching {role_part} "
            "with the information provided.\n\n"
            "Could you share more details — for example, the job level, "
            "required skills, or assessment purpose?"
        )
        return reply_text, "", "insufficient_information"

    def _render_table(
        self,
        recommendations: Sequence[AssessmentRecommendation],
    ) -> str:
        rows = [_TABLE_HEADER]
        for idx, rec in enumerate(recommendations, start=1):
            row = self._render_table_row(idx, rec.assessment)
            rows.append(row)
        return "\n".join(rows)

    def _render_table_row(self, index: int, assessment: Assessment) -> str:
        name = assessment.name
        test_type = assessment.test_type
        keys = ", ".join(assessment.keys) if assessment.keys else "—"
        duration = self._format_duration(assessment)
        languages = self._format_languages(list(assessment.languages))
        url = str(assessment.url)

        return (
            f"| {index} | {name} | {test_type} | {keys} "
            f"| {duration} | {languages} | <{url}> |"
        )

    def _recommend_framing(self, context: ReplyContext) -> str:
        parts: list[str] = []
        if context.job_level:
            parts.append(context.job_level.casefold())
        if context.role:
            parts.append(context.role)

        if parts:
            descriptor = " ".join(parts)
            return f"For {descriptor}:"

        return "Here are the assessments that best match your requirements:"

    def _update_acknowledgement(self, context: ReplyContext) -> str:
        return "Updated shortlist:"

    def _clarification_preamble(self, reason: str) -> str:
        if not reason or len(reason) < 10:  # noqa: PLR2004
            return ""

        sentence = reason.rstrip(".!?")
        sentence = sentence[0].upper() + sentence[1:]
        return f"{sentence}."

    def _format_duration(self, assessment: Assessment) -> str:
        if assessment.duration is not None:
            return f"{assessment.duration} minutes"

        extras = assessment.model_extra or {}
        raw = extras.get("duration_raw") or extras.get("duration")
        if raw:
            raw_str = str(raw).strip()

            if re.search(r"[a-zA-Z]", raw_str):
                return raw_str

            if raw_str.lstrip("-").isdigit():
                return f"{raw_str} minutes"
            return raw_str

        return "—"

    def _format_languages(self, languages: list[str]) -> str:
        if not languages:
            return "—"

        limit = self.max_inline_languages
        if len(languages) <= limit:
            return ", ".join(languages)

        shown = ", ".join(languages[:limit])
        extra = len(languages) - limit
        return f"{shown} _(+{extra} more)_"

    @staticmethod
    def _count_table_rows(table_md: str) -> int:
        if not table_md:
            return 0
        lines = table_md.splitlines()

        data_lines = [
            line
            for line in lines[2:]
            if line.strip().startswith("|") and line.strip().endswith("|")
        ]
        return len(data_lines)


def build_response_generator(
    max_inline_languages: int = _MAX_INLINE_LANGUAGES,
    extra_config: dict[str, Any] | None = None,
) -> ResponseGenerator:
    _ = extra_config
    return ResponseGenerator(max_inline_languages=max_inline_languages)
