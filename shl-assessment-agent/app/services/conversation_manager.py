from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from app.models.conversation import (
    ClarificationRecord,
    ConversationConstraints,
    ConversationContext,
    ConversationMessage,
    ConversationPreference,
    ConversationState,
    RecommendationRecord,
)


@dataclass
class ConversationManager:

    _state: ConversationState | None = field(default=None, init=False, repr=False)

    def start_conversation(
        self,
        messages: Sequence[ConversationMessage] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationState:
        self._state = ConversationState(
            messages=list(messages or []),
            metadata=dict(metadata or {}),
        )
        return self._state

    def update_state(
        self,
        messages: Sequence[ConversationMessage] | None = None,
        context: ConversationContext | None = None,
        constraints: ConversationConstraints | None = None,
        preferences: Sequence[ConversationPreference] | None = None,
        current_clarification_question: str | None = None,
        user_answers: dict[str, str] | None = None,
        conversation_summary: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationState:
        state = self._require_state()

        if messages:
            state.messages.extend(messages)
        if context is not None:
            state.context = context
        if constraints is not None:
            state.constraints = constraints
        if preferences:
            state.preferences.extend(preferences)
        if current_clarification_question is not None:
            state.current_clarification_question = current_clarification_question
        if user_answers:
            state.user_answers.update(user_answers)
        if conversation_summary is not None:
            state.conversation_summary = conversation_summary
        if metadata:
            state.metadata.update(metadata)

        return state

    def get_state(self) -> ConversationState:
        return self._require_state()

    def reset(self) -> ConversationState:
        self._state = ConversationState()
        return self._state

    def record_recommendation(
        self,
        assessment_ids: Sequence[str],
        metadata: dict[str, Any] | None = None,
    ) -> ConversationState:
        state = self._require_state()
        record = RecommendationRecord(
            assessment_ids=list(assessment_ids),
            metadata=dict(metadata or {}),
        )
        state.recommendation_history.records.append(record)

        for assessment_id in assessment_ids:
            if assessment_id not in state.recommended_assessment_ids:
                state.recommended_assessment_ids.append(assessment_id)

        return state

    def record_clarification(
        self,
        question: str,
        answer: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationState:
        state = self._require_state()
        record = ClarificationRecord(
            question=question,
            answer=answer,
            metadata=dict(metadata or {}),
        )
        state.clarification_history.records.append(record)
        state.current_clarification_question = question

        if answer is not None:
            state.user_answers[question] = answer

        return state

    def summarize(self) -> str:
        state = self._require_state()
        summary_parts = [
            f"Messages: {len(state.messages)}",
            f"Clarifications: {len(state.clarification_history.records)}",
            f"Recommendation records: {len(state.recommendation_history.records)}",
            f"Recommended assessments: {len(state.recommended_assessment_ids)}",
        ]
        state.conversation_summary = "; ".join(summary_parts)
        return state.conversation_summary

    def _require_state(self) -> ConversationState:
        if self._state is None:
            return self.start_conversation()
        return self._state
