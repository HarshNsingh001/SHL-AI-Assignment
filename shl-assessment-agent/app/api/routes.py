from fastapi import APIRouter, Depends

from app.api.dependencies import get_orchestrator, get_response_generator
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationTurn,
    RecommendationItem,
)
from app.models.business_rules import DecisionType
from app.models.conversation import ConversationMessage, ConversationMessageRole
from app.models.recommendation_engine import AssessmentRecommendation
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.response_generator import ResponseGenerator

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Process one conversation turn",
    description=(
        "Receive the latest user message together with prior conversation "
        "history, run the deterministic SHL assessment pipeline, and return "
        "a structured assistant reply with optional assessment recommendations."
    ),
)
async def chat(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator),
    response_generator: ResponseGenerator = Depends(get_response_generator),
) -> ChatResponse:

    conversation_history: list[ConversationMessage] = [
        _api_turn_to_domain(turn) for turn in request.conversation
    ]

    pipeline_result = orchestrator.run(
        conversation_history=conversation_history,
        latest_user_message=request.message,
    )

    generated_reply = response_generator.generate(
        decision=pipeline_result.decision,
        recommendation_result=pipeline_result.recommendation_result,
        conversation_state=pipeline_result.conversation_state,
    )

    recommendation_items = [
        _domain_recommendation_to_api(rec)
        for rec in pipeline_result.recommendation_result.recommendations
    ]

    end_of_conversation = _is_end_of_conversation(
        pipeline_result.decision.decision_type,
        pipeline_result.decision.context.is_confirmation,
    )

    return ChatResponse(
        reply=generated_reply.reply_text,
        recommendations=recommendation_items,
        end_of_conversation=end_of_conversation,
    )


def _api_turn_to_domain(turn: ConversationTurn) -> ConversationMessage:
    try:
        role = ConversationMessageRole(turn.role.lower())
    except ValueError:
        role = ConversationMessageRole.USER
    return ConversationMessage(role=role, content=turn.content)


def _domain_recommendation_to_api(
    rec: AssessmentRecommendation,
) -> RecommendationItem:
    assessment = rec.assessment
    return RecommendationItem(
        id=assessment.id,
        name=assessment.name,
        url=str(assessment.url),
        test_type=assessment.test_type,
        keys=list(assessment.keys),
        duration=assessment.duration,
        languages=list(assessment.languages),
        remote_support=assessment.remote_support,
        adaptive_support=assessment.adaptive_support,
        description=assessment.description,
    )


def _is_end_of_conversation(
    decision_type: DecisionType,
    is_confirmation: bool = False,
) -> bool:
    terminal_decision = decision_type in {
        DecisionType.RECOMMEND,
        DecisionType.UPDATE_RECOMMENDATIONS,
    }
    return terminal_decision and is_confirmation
