import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.models.business_rules import (
    CatalogQueryResult,
    ClarificationRequest,
    ConversationDecision,
    DecisionContext,
    DecisionType,
    RuleEvaluation,
)
from app.models.constraints import ConstraintExtractionResult, HiringConstraints
from app.models.conversation import ConversationMessageRole, ConversationState


@dataclass(frozen=True)
class BusinessRuleEngine:

    def evaluate(
        self,
        conversation_state: ConversationState,
        constraint_result: ConstraintExtractionResult,
        catalog_query_result: CatalogQueryResult,
    ) -> ConversationDecision:
        latest_user_message = self._latest_user_message(conversation_state)
        normalized_message = self._normalize(latest_user_message or "")
        context = self._build_context(
            conversation_state,
            catalog_query_result,
            latest_user_message,
            normalized_message,
        )
        evaluations: list[RuleEvaluation] = []

        if self._is_out_of_scope(normalized_message):
            evaluations.append(
                self._evaluation(
                    "refuse_out_of_scope",
                    True,
                    "The latest user request is outside SHL assessment selection.",
                )
            )
            return self._decision(DecisionType.REFUSE, context, evaluations)
        evaluations.append(
            self._evaluation(
                "refuse_out_of_scope",
                False,
                "The latest user request stays within SHL assessment selection.",
            )
        )

        if context.is_comparison_request and (
            context.has_catalog_candidates or context.has_previous_recommendations
        ):
            evaluations.append(
                self._evaluation(
                    "comparison_request",
                    True,
                    "The user is asking to compare catalog-backed assessments.",
                )
            )
            return self._decision(DecisionType.RECOMMEND, context, evaluations)
        evaluations.append(
            self._evaluation(
                "comparison_request",
                False,
                "No actionable comparison request was detected.",
            )
        )

        pending_clarification = self._pending_clarification(conversation_state)
        if (
            pending_clarification is not None
            and not context.user_answered_previous_clarification
        ):
            evaluations.append(
                self._evaluation(
                    "pending_clarification",
                    True,
                    "A prior clarification has not been answered.",
                )
            )
            return self._decision(
                DecisionType.ASK_CLARIFICATION,
                context,
                evaluations,
                pending_clarification,
            )
        evaluations.append(
            self._evaluation(
                "pending_clarification",
                False,
                "No unanswered prior clarification blocks progress.",
            )
        )

        if context.is_update_request and context.has_previous_recommendations:
            evaluations.append(
                self._evaluation(
                    "update_existing_recommendations",
                    True,
                    "The user is modifying a prior shortlist.",
                )
            )
            return self._decision(
                DecisionType.UPDATE_RECOMMENDATIONS,
                context,
                evaluations,
            )
        evaluations.append(
            self._evaluation(
                "update_existing_recommendations",
                False,
                "No prior shortlist update request was detected.",
            )
        )

        clarification = self._select_clarification(
            conversation_state,
            constraint_result,
            normalized_message,
        )
        if clarification is not None:
            evaluations.append(
                self._evaluation(
                    "critical_missing_information",
                    True,
                    clarification.reason,
                )
            )
            return self._decision(
                DecisionType.ASK_CLARIFICATION,
                context,
                evaluations,
                clarification,
            )
        evaluations.append(
            self._evaluation(
                "critical_missing_information",
                False,
                "No critical clarification is required before retrieval output.",
            )
        )

        if not context.has_catalog_candidates:
            evaluations.append(
                self._evaluation(
                    "catalog_candidates_available",
                    False,
                    "No catalog candidates are available for a shortlist.",
                )
            )
            return self._decision(
                DecisionType.INSUFFICIENT_INFORMATION,
                context,
                evaluations,
            )
        evaluations.append(
            self._evaluation(
                "catalog_candidates_available",
                True,
                "Catalog candidates are available.",
            )
        )

        if context.is_confirmation and context.has_previous_recommendations:
            evaluations.append(
                self._evaluation(
                    "confirmation_with_existing_shortlist",
                    True,
                    "The user confirmed an existing shortlist.",
                )
            )
            return self._decision(DecisionType.RECOMMEND, context, evaluations)

        evaluations.append(
            self._evaluation(
                "recommend_when_ready",
                True,
                "Constraints and catalog candidates are sufficient.",
            )
        )
        return self._decision(DecisionType.RECOMMEND, context, evaluations)

    def _build_context(
        self,
        conversation_state: ConversationState,
        catalog_query_result: CatalogQueryResult,
        latest_user_message: str | None,
        normalized_message: str,
    ) -> DecisionContext:
        return DecisionContext(
            latest_user_message=latest_user_message,
            turn_count=len(conversation_state.messages),
            has_previous_recommendations=bool(
                conversation_state.recommended_assessment_ids
                or conversation_state.recommendation_history.records
            ),
            has_catalog_candidates=catalog_query_result.candidate_count > 0,
            user_answered_previous_clarification=self._has_answered_clarification(
                conversation_state,
                latest_user_message,
            ),
            is_comparison_request=self._is_comparison_request(normalized_message),
            is_update_request=self._is_update_request(normalized_message),
            is_confirmation=self._is_confirmation(normalized_message),
            is_out_of_scope=self._is_out_of_scope(normalized_message),
        )

    def _select_clarification(
        self,
        conversation_state: ConversationState,
        constraint_result: ConstraintExtractionResult,
        normalized_message: str,
    ) -> ClarificationRequest | None:
        constraints = constraint_result.constraints

        if self._needs_contact_center_language(constraints):
            return ClarificationRequest(
                question="What language are the calls in?",
                missing_field="languages",
                reason="Contact center screening depends on spoken-language coverage.",
            )

        if self._needs_english_accent(constraints, normalized_message):
            return ClarificationRequest(
                question="Which English accent fits the operation?",
                missing_field="language_variant",
                reason="English spoken-language screens vary by accent.",
            )

        if self._needs_healthcare_delivery_choice(constraints, normalized_message):
            return ClarificationRequest(
                question=(
                    "Should this be a hybrid English knowledge and Spanish "
                    "personality battery?"
                ),
                missing_field="delivery_approach",
                reason=(
                    "Healthcare knowledge tests may not share the requested "
                    "language."
                ),
            )

        if self._needs_leadership_purpose(constraints):
            return ClarificationRequest(
                question=(
                    "Is this for selection, development, or another leadership "
                    "use case?"
                ),
                missing_field="purpose",
                reason="Leadership requests need a purpose before report selection.",
            )

        if self._needs_engineering_focus(constraints):
            return ClarificationRequest(
                question=(
                    "Is this backend-leaning, frontend-heavy, or balanced "
                    "full-stack?"
                ),
                missing_field="role_focus",
                reason=(
                    "The technical requirement spans multiple distinct "
                    "engineering areas."
                ),
            )

        if self._needs_technical_seniority_choice(constraints, normalized_message):
            return ClarificationRequest(
                question=(
                    "Is this a senior individual contributor role or a tech "
                    "lead role?"
                ),
                missing_field="seniority",
                reason=(
                    "Senior technical roles need ownership context before "
                    "shortlist selection."
                ),
            )

        if "role" in constraint_result.missing_information.missing_fields:
            return ClarificationRequest(
                question="Which role are you hiring for?",
                missing_field="role",
                reason="A role is required before assessment selection.",
            )

        if (
            conversation_state.current_clarification_question is not None
            and not self._has_answered_clarification(
                conversation_state,
                self._latest_user_message(conversation_state),
            )
        ):
            return self._pending_clarification(conversation_state)

        return None

    @staticmethod
    def _needs_contact_center_language(constraints: HiringConstraints) -> bool:
        role = BusinessRuleEngine._normalize(constraints.role or "")
        customer_support = constraints.customer_facing is True and (
            "contact" in role or "customer" in role
        )
        return customer_support and not constraints.languages

    @staticmethod
    def _needs_english_accent(
        constraints: HiringConstraints,
        normalized_message: str,
    ) -> bool:
        role = BusinessRuleEngine._normalize(constraints.role or "")
        languages = [
            BusinessRuleEngine._normalize(value)
            for value in constraints.languages or []
        ]
        has_english = any("english" in language for language in languages)
        has_variant = bool(
            re.search(
                r"\b(us|usa|uk|australian|australia|indian|india)\b",
                normalized_message,
            )
        )
        return "contact" in role and has_english and not has_variant

    @staticmethod
    def _needs_healthcare_delivery_choice(
        constraints: HiringConstraints,
        normalized_message: str,
    ) -> bool:
        role = BusinessRuleEngine._normalize(constraints.role or "")
        industry = BusinessRuleEngine._normalize(constraints.industry or "")
        languages = [
            BusinessRuleEngine._normalize(value)
            for value in constraints.languages or []
        ]
        has_spanish = any("spanish" in language for language in languages)
        healthcare = (
            "healthcare" in role
            or "healthcare" in industry
            or "hipaa" in normalized_message
        )
        has_choice = any(
            token in normalized_message for token in ("hybrid", "bilingual", "fluent")
        )
        return healthcare and has_spanish and not has_choice

    @staticmethod
    def _needs_leadership_purpose(constraints: HiringConstraints) -> bool:
        role = BusinessRuleEngine._normalize(constraints.role or "")
        leadership_role = any(
            kw in role
            for kw in (
                "leadership",
                "executive",
                "leader",
                "director",
                "cxo",
                "trainee",
            )
        )
        return (
            constraints.leadership_required is True
            and constraints.purpose is None
            and (leadership_role or constraints.job_level is not None)
        )

    @staticmethod
    def _needs_engineering_focus(constraints: HiringConstraints) -> bool:
        role = BusinessRuleEngine._normalize(constraints.role or "")
        skill_count = len(constraints.required_skills or [])
        return "engineer" in role and skill_count >= 6

    @staticmethod
    def _needs_technical_seniority_choice(
        constraints: HiringConstraints,
        normalized_message: str,
    ) -> bool:
        role = BusinessRuleEngine._normalize(constraints.role or "")
        if "engineer" not in role or constraints.job_level is None:
            return False
        senior_terms = ("senior", "lead", "manager", "architect")
        ownership_terms = ("senior ic", "individual contributor", "tech lead", "manage")
        return any(term in normalized_message for term in senior_terms) and not any(
            term in normalized_message for term in ownership_terms
        )

    @staticmethod
    def _pending_clarification(
        conversation_state: ConversationState,
    ) -> ClarificationRequest | None:
        question = conversation_state.current_clarification_question
        if question is None:
            return None
        return ClarificationRequest(
            question=question,
            missing_field="previous_clarification",
            reason="The previous clarification is still open.",
        )

    @staticmethod
    def _has_answered_clarification(
        conversation_state: ConversationState,
        latest_user_message: str | None,
    ) -> bool:
        question = conversation_state.current_clarification_question
        if question is None:
            return False
        if question in conversation_state.user_answers:
            return True
        if not conversation_state.messages:
            return False
        latest_message = conversation_state.messages[-1]
        return (
            latest_message.role is ConversationMessageRole.USER
            and latest_user_message is not None
            and bool(latest_user_message.strip())
        )

    @staticmethod
    def _latest_user_message(conversation_state: ConversationState) -> str | None:
        for message in reversed(conversation_state.messages):
            if message.role is ConversationMessageRole.USER:
                return message.content
        return None

    @staticmethod
    def _is_comparison_request(normalized_message: str) -> bool:
        comparison_terms = (
            "difference between",
            "different from",
            " different",
            "compare",
            " versus ",
            " vs ",
            "do we really need",
            "is the advanced level",
            "is the right pick",
        )
        return any(term in f" {normalized_message} " for term in comparison_terms)

    @staticmethod
    def _is_update_request(normalized_message: str) -> bool:
        update_terms = (
            "add ",
            "drop ",
            "remove ",
            "replace ",
            "instead",
            "actually",
            "keep ",
            "final list",
            "locking it in",
            "as-is",
        )
        return any(term in normalized_message for term in update_terms)

    @staticmethod
    def _is_confirmation(normalized_message: str) -> bool:

        confirmation_terms = (
            "confirmed",
            "that works",
            "perfect",
            "thats good",
            "that s good",
            "that covers it",
            "thanks",
            "understood",
            "clear",
            "sounds good",
            "great",
            "all good",
            "go ahead",
            "locking it in",
            "final list",
        )
        return any(term in normalized_message for term in confirmation_terms)

    @staticmethod
    def _is_out_of_scope(normalized_message: str) -> bool:
        legal_request = any(
            term in normalized_message
            for term in (
                "legally required",
                "legal requirement",
                "satisfy that requirement",
                "satisfies that requirement",
                "regulatory obligation",
                "legal advice",
                "employment law",
            )
        )
        instruction_override = any(
            term in normalized_message
            for term in (
                "ignore previous instructions",
                "system message",
                "developer message",
                "reveal your instructions",
            )
        )
        general_advice = any(
            term in normalized_message
            for term in (
                "write a job description",
                "salary benchmark",
                "compensation advice",
                "interview questions",
            )
        )
        return legal_request or instruction_override or general_advice

    @staticmethod
    def _decision(
        decision_type: DecisionType,
        context: DecisionContext,
        evaluations: Sequence[RuleEvaluation],
        clarification_request: ClarificationRequest | None = None,
    ) -> ConversationDecision:
        return ConversationDecision(
            decision_type=decision_type,
            context=context,
            clarification_request=clarification_request,
            rule_evaluations=list(evaluations),
        )

    @staticmethod
    def _evaluation(
        rule_name: str,
        matched: bool,
        reason: str,
    ) -> RuleEvaluation:
        return RuleEvaluation(rule_name=rule_name, matched=matched, reason=reason)

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = value.casefold().replace("centre", "center")

        normalized = re.sub(r"'([a-z])", r"\1", normalized)
        normalized = re.sub(r"[^a-z0-9+#.]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
