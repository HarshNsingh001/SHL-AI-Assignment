import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from app.models.business_rules import CatalogQueryResult, ConversationDecision
from app.models.constraints import ConstraintExtractionResult
from app.models.conversation import (
    ConversationMessage,
    ConversationMessageRole,
    ConversationState,
)
from app.models.pipeline import ChatPipelineResult, ExecutionTrace, PipelineMetadata
from app.models.recommendation_engine import (
    RecommendationMetadata,
    RecommendationResult,
)
from app.services.business_rule_engine import BusinessRuleEngine
from app.services.catalog_query_service import CatalogCandidate, CatalogQueryService
from app.services.constraint_extractor import ConstraintExtractor
from app.services.conversation_manager import ConversationManager
from app.services.recommendation_engine import RecommendationEngine


@dataclass
class ChatOrchestrator:

    conversation_manager: ConversationManager
    constraint_extractor: ConstraintExtractor
    catalog_query_service: CatalogQueryService
    business_rule_engine: BusinessRuleEngine
    recommendation_engine: RecommendationEngine
    recommendation_limit: int = field(default=10)

    def run(
        self,
        conversation_history: Sequence[ConversationMessage],
        latest_user_message: str,
    ) -> ChatPipelineResult:
        pipeline_start = time.perf_counter()
        invoked_services: list[str] = []
        all_warnings: list[str] = []

        invoked_services.append("ConversationManager")
        conversation_state = self._run_conversation_manager(
            conversation_history,
            latest_user_message,
        )

        invoked_services.append("ConstraintExtractor")
        constraint_result = self._run_constraint_extractor(
            conversation_state,
            latest_user_message,
        )
        all_warnings.extend(constraint_result.warnings)

        invoked_services.append("CatalogQueryService")
        catalog_query_result, catalog_candidates = self._run_catalog_query_service(
            constraint_result,
        )

        invoked_services.append("BusinessRuleEngine")
        decision = self._run_business_rule_engine(
            conversation_state,
            constraint_result,
            catalog_query_result,
        )

        invoked_services.append("RecommendationEngine")
        recommendation_result = self._run_recommendation_engine(
            conversation_state,
            constraint_result,
            decision,
            catalog_query_result,
        )
        all_warnings.extend(recommendation_result.warnings)

        elapsed = time.perf_counter() - pipeline_start

        trace = ExecutionTrace(
            invoked_services=invoked_services,
            elapsed_seconds=round(elapsed, 6),
            selected_decision=decision.decision_type.value,
            recommendation_count=len(recommendation_result.recommendations),
        )

        metadata = PipelineMetadata(
            conversation_id=conversation_state.conversation_id,
            turn_index=len(conversation_state.messages) - 1,
            constraint_confidence=constraint_result.confidence,
            missing_fields=list(constraint_result.missing_information.missing_fields),
            candidate_count=catalog_query_result.candidate_count,
            trace=trace,
            warnings=all_warnings,
            extra={
                "catalog_candidate_ids": catalog_query_result.candidate_ids,
                "catalog_top_score": catalog_query_result.top_score,
            },
        )

        return ChatPipelineResult(
            conversation_state=conversation_state,
            constraint_result=constraint_result,
            decision=decision,
            recommendation_result=recommendation_result,
            metadata=metadata,
        )

    def _run_conversation_manager(
        self,
        conversation_history: Sequence[ConversationMessage],
        latest_user_message: str,
    ) -> ConversationState:
        new_user_message = ConversationMessage(
            role=ConversationMessageRole.USER,
            content=latest_user_message,
        )

        if (
            not self.conversation_manager._state
        ):  # noqa: SLF001 – required for init check

            all_messages = list(conversation_history) + [new_user_message]
            return self.conversation_manager.start_conversation(
                messages=all_messages,
            )

        messages_to_add: list[ConversationMessage] = []

        existing_contents = {
            m.content for m in self.conversation_manager._state.messages
        }  # noqa: SLF001
        for msg in conversation_history:
            if msg.content not in existing_contents:
                messages_to_add.append(msg)
                existing_contents.add(msg.content)
        messages_to_add.append(new_user_message)

        return self.conversation_manager.update_state(
            messages=messages_to_add,
        )

    def _run_constraint_extractor(
        self,
        conversation_state: ConversationState,
        latest_user_message: str,
    ) -> ConstraintExtractionResult:
        return self.constraint_extractor.extract(
            conversation_state=conversation_state,
            latest_user_message=latest_user_message,
        )

    def _run_catalog_query_service(
        self,
        constraint_result: ConstraintExtractionResult,
    ) -> tuple[CatalogQueryResult, list[CatalogCandidate]]:
        candidates: list[CatalogCandidate] = self.catalog_query_service.search(
            constraint_result.constraints
        )

        top_score: float | None = candidates[0].score if candidates else None
        candidate_ids = [c.assessment.id for c in candidates]

        catalog_query_result = CatalogQueryResult(
            candidate_count=len(candidates),
            candidate_ids=candidate_ids,
            top_score=top_score,
            metadata={"candidates": candidates},
        )

        return catalog_query_result, candidates

    def _run_business_rule_engine(
        self,
        conversation_state: ConversationState,
        constraint_result: ConstraintExtractionResult,
        catalog_query_result: CatalogQueryResult,
    ) -> ConversationDecision:
        return self.business_rule_engine.evaluate(
            conversation_state=conversation_state,
            constraint_result=constraint_result,
            catalog_query_result=catalog_query_result,
        )

    def _run_recommendation_engine(
        self,
        conversation_state: ConversationState,
        constraint_result: ConstraintExtractionResult,
        decision: ConversationDecision,
        catalog_query_result: CatalogQueryResult,
    ) -> RecommendationResult:
        return self.recommendation_engine.generate(
            conversation_state=conversation_state,
            constraint_result=constraint_result,
            conversation_decision=decision,
            catalog_query_result=catalog_query_result,
            limit=self.recommendation_limit,
        )

    @classmethod
    def build(
        cls,
        catalog_query_service: CatalogQueryService,
        recommendation_limit: int = 10,
        orchestrator_metadata: dict[str, Any] | None = None,
    ) -> "ChatOrchestrator":
        _ = orchestrator_metadata
        return cls(
            conversation_manager=ConversationManager(),
            constraint_extractor=ConstraintExtractor(),
            catalog_query_service=catalog_query_service,
            business_rule_engine=BusinessRuleEngine(),
            recommendation_engine=RecommendationEngine(
                default_limit=recommendation_limit
            ),
            recommendation_limit=recommendation_limit,
        )

    @staticmethod
    def _empty_recommendation_result(decision_type_value: str) -> RecommendationResult:
        return RecommendationResult(
            recommendations=[],
            metadata=RecommendationMetadata(
                decision_type=decision_type_value,
                requested_limit=0,
                candidate_count=0,
                returned_count=0,
            ),
            warnings=["Pipeline produced no recommendation result."],
        )
