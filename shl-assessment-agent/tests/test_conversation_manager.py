from app.models.conversation import (
    ConversationConstraints,
    ConversationContext,
    ConversationMessage,
    ConversationMessageRole,
    ConversationPreference,
)
from app.services.conversation_manager import ConversationManager


def test_start_conversation_creates_new_state_with_messages() -> None:
    manager = ConversationManager()
    message = ConversationMessage(
        role=ConversationMessageRole.USER,
        content="I need an assessment for a sales role.",
    )

    state = manager.start_conversation(messages=[message], metadata={"source": "test"})

    assert len(state.messages) == 1
    assert state.messages[0].content == "I need an assessment for a sales role."
    assert state.metadata == {"source": "test"}


def test_update_state_preserves_previous_context() -> None:
    manager = ConversationManager()
    initial_message = ConversationMessage(
        role=ConversationMessageRole.USER,
        content="Hiring entry level analysts.",
    )
    follow_up_message = ConversationMessage(
        role=ConversationMessageRole.USER,
        content="English language assessments only.",
    )
    manager.start_conversation(messages=[initial_message])

    state = manager.update_state(
        messages=[follow_up_message],
        context=ConversationContext(
            current_role="Analyst",
            industry="Financial services",
            experience_level="Entry level",
            job_level="Graduate",
            languages=["English"],
            assessment_types_requested=["cognitive"],
            required_skills=["data analysis"],
            required_competencies=["problem solving"],
        ),
        constraints=ConversationConstraints(
            duration_minutes=45,
            remote_required=True,
            languages=["English"],
            assessment_types=["cognitive"],
        ),
        preferences=[
            ConversationPreference(name="delivery", value="remote"),
        ],
        metadata={"tenant": "sample"},
    )

    assert [message.content for message in state.messages] == [
        "Hiring entry level analysts.",
        "English language assessments only.",
    ]
    assert state.context.current_role == "Analyst"
    assert state.context.required_skills == ["data analysis"]
    assert state.constraints.remote_required is True
    assert state.preferences[0].name == "delivery"
    assert state.metadata == {"tenant": "sample"}


def test_record_clarification_updates_history_and_user_answers() -> None:
    manager = ConversationManager()
    manager.start_conversation()

    state = manager.record_clarification(
        question="Which job level should this target?",
        answer="Graduate",
    )

    assert state.current_clarification_question == "Which job level should this target?"
    assert len(state.clarification_history.records) == 1
    assert state.clarification_history.records[0].answer == "Graduate"
    assert state.user_answers == {"Which job level should this target?": "Graduate"}


def test_record_recommendation_updates_history_and_unique_ids() -> None:
    manager = ConversationManager()
    manager.start_conversation()

    manager.record_recommendation(["assessment-1", "assessment-2"])
    state = manager.record_recommendation(["assessment-2", "assessment-3"])

    assert len(state.recommendation_history.records) == 2
    assert state.recommendation_history.records[0].assessment_ids == [
        "assessment-1",
        "assessment-2",
    ]
    assert state.recommended_assessment_ids == [
        "assessment-1",
        "assessment-2",
        "assessment-3",
    ]


def test_reset_replaces_existing_conversation_state() -> None:
    manager = ConversationManager()
    original_state = manager.start_conversation(
        messages=[
            ConversationMessage(
                role=ConversationMessageRole.USER,
                content="Keep this only before reset.",
            )
        ]
    )

    reset_state = manager.reset()

    assert reset_state.conversation_id != original_state.conversation_id
    assert reset_state.messages == []
    assert manager.get_state() == reset_state


def test_summarize_stores_deterministic_conversation_summary() -> None:
    manager = ConversationManager()
    manager.start_conversation(
        messages=[
            ConversationMessage(
                role=ConversationMessageRole.USER,
                content="Need a coding assessment.",
            )
        ]
    )
    manager.record_clarification("Which language?", "Python")
    manager.record_recommendation(["coding-simulation"])

    summary = manager.summarize()

    assert summary == (
        "Messages: 1; Clarifications: 1; Recommendation records: 1; "
        "Recommended assessments: 1"
    )
    assert manager.get_state().conversation_summary == summary
