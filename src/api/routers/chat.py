"""Chat and session endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import AgentContext
from src.agents.orchestrator import MasterOrchestrator
from src.api.dependencies import get_current_user, get_db, get_memory, get_orchestrator
from src.memory.manager import MemoryManager
from src.models.session import Session
from src.models.user import User
from src.schemas.chat import (
    MessageRequest,
    MessageResponse,
    SessionCreateRequest,
    SessionResponse,
)

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    memory: MemoryManager = Depends(get_memory),
):
    """Create a new tutoring session."""
    session_id = str(uuid.uuid4())

    # Store in PostgreSQL
    db_session = Session(
        id=session_id,
        student_id=current_user.id,
        mode=body.mode,
        subject=body.subject,
        topic=body.topic,
    )
    db.add(db_session)
    await db.flush()

    # Initialize session context in Redis
    context = {
        "session_id": session_id,
        "student_id": str(current_user.id),
        "student_profile": {},
        "current_subject": body.subject,
        "current_topic": body.topic,
        "mode": body.mode,
        "conversation_history": [],
        "learning_objectives": [],
    }

    # Load student profile if available
    if current_user.profile:
        context["student_profile"] = {
            "name": current_user.name,
            "learning_style": current_user.profile.learning_style or "balanced",
            "pace": current_user.profile.pace or "moderate",
            "grade_level": current_user.profile.grade_level or "",
            "strengths": current_user.profile.strengths or [],
            "weaknesses": current_user.profile.weaknesses or [],
        }

    await memory.set_session_context(session_id, context)

    return SessionResponse(
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
        mode=body.mode,
    )


@router.post("/message", response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
    memory: MemoryManager = Depends(get_memory),
):
    """Send a message to the AI tutor."""
    # Get session context from Redis
    context_data = await memory.get_session_context(body.session_id)
    if not context_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Verify session belongs to user
    if context_data.get("student_id") != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Override subject/topic if provided in the message
    if body.subject:
        context_data["current_subject"] = body.subject
    if body.topic:
        context_data["current_topic"] = body.topic

    # Get conversation history
    history = await memory.get_conversation_history(body.session_id)
    context_data["conversation_history"] = history

    # Build agent context
    agent_context = AgentContext(
        session_id=body.session_id,
        student_id=str(current_user.id),
        student_profile=context_data.get("student_profile", {}),
        conversation_history=history,
        current_subject=context_data.get("current_subject"),
        current_topic=context_data.get("current_topic"),
        learning_objectives=context_data.get("learning_objectives", []),
    )

    # Per-request LLM override: swap orchestrator's tutor LLM if requested
    _original_llm = None
    if body.provider or body.model:
        from src.llm.factory import LLMFactory

        tutor = orchestrator.agents.get("tutor")
        if tutor:
            _original_llm = tutor.llm
            tutor.llm = LLMFactory.create(
                provider=body.provider,
                model=body.model,
            )

    # Process message through orchestrator
    response = await orchestrator.process(body.content, agent_context)

    # Restore original LLM after request
    if _original_llm is not None:
        orchestrator.agents["tutor"].llm = _original_llm

    # Save messages to conversation history
    await memory.add_to_conversation(body.session_id, "user", body.content)
    await memory.add_to_conversation(body.session_id, "assistant", response.text)

    # Save learning event
    await memory.save_learning_event(
        student_id=str(current_user.id),
        event_type="interaction",
        subject=context_data.get("current_subject"),
        topic=context_data.get("current_topic"),
        data={"input": body.content, "response_length": len(response.text)},
        outcome="completed",
    )

    return MessageResponse(
        text=response.text,
        session_id=body.session_id,
        sources=response.metadata.get("knowledge_sources", []),
        suggested_actions=response.suggested_actions,
        metadata={
            "agent": response.agent_name,
            "processing_time": response.processing_time,
        },
    )


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory),
):
    """Get conversation history for a session."""
    context_data = await memory.get_session_context(session_id)
    if not context_data or context_data.get("student_id") != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    history = await memory.get_conversation_history(session_id, limit)
    return {"messages": history}
