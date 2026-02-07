"""Session management endpoints: list, get, end, resume."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.models.database import get_db
from src.models.session import Session
from src.models.user import User

router = APIRouter(tags=["Sessions"])


class SessionResponse(BaseModel):
    id: str
    student_id: str
    mode: str | None = None
    subject: str | None = None
    topic: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    summary: str | None = None
    is_archived: bool = False
    message_count: int = 0
    device_info: str | None = None

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all sessions for the current user."""
    result = await db.execute(
        select(Session)
        .where(Session.student_id == current_user.id)
        .order_by(Session.started_at.desc())
    )
    sessions = result.scalars().all()
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=str(s.id),
                student_id=str(s.student_id),
                mode=s.mode,
                subject=s.subject,
                topic=s.topic,
                started_at=s.started_at,
                ended_at=s.ended_at,
                summary=s.summary if hasattr(s, "summary") else None,
                is_archived=s.is_archived if hasattr(s, "is_archived") else False,
                message_count=s.message_count if hasattr(s, "message_count") else 0,
                device_info=s.device_info if hasattr(s, "device_info") else None,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details for a specific session."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.student_id == current_user.id,
        )
    )
    session = result.scalars().first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return SessionResponse(
        id=str(session.id),
        student_id=str(session.student_id),
        mode=session.mode,
        subject=session.subject,
        topic=session.topic,
        started_at=session.started_at,
        ended_at=session.ended_at,
        summary=session.summary if hasattr(session, "summary") else None,
        is_archived=session.is_archived if hasattr(session, "is_archived") else False,
        message_count=session.message_count if hasattr(session, "message_count") else 0,
        device_info=session.device_info if hasattr(session, "device_info") else None,
    )


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """End a session: set ended_at, generate summary, mark as archived."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.student_id == current_user.id,
        )
    )
    session = result.scalars().first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already ended",
        )

    now = datetime.now(timezone.utc)
    # Generate simple summary from session metadata
    topics = []
    if session.subject:
        topics.append(session.subject)
    if session.topic:
        topics.append(session.topic)
    summary = f"Session on {', '.join(topics) if topics else 'general tutoring'}"
    if session.started_at:
        duration_seconds = (now - session.started_at).total_seconds()
        duration_minutes = int(duration_seconds // 60)
        summary += f" ({duration_minutes} min)"

    session.ended_at = now
    session.summary = summary
    session.is_archived = True
    await db.flush()

    return SessionResponse(
        id=str(session.id),
        student_id=str(session.student_id),
        mode=session.mode,
        subject=session.subject,
        topic=session.topic,
        started_at=session.started_at,
        ended_at=session.ended_at,
        summary=session.summary,
        is_archived=session.is_archived,
        message_count=session.message_count if hasattr(session, "message_count") else 0,
        device_info=session.device_info if hasattr(session, "device_info") else None,
    )


@router.post("/sessions/{session_id}/resume", response_model=SessionResponse)
async def resume_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume an archived session: clear ended_at and is_archived flag."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.student_id == current_user.id,
        )
    )
    session = result.scalars().first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if not getattr(session, "is_archived", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not archived",
        )

    session.ended_at = None
    session.is_archived = False
    await db.flush()

    return SessionResponse(
        id=str(session.id),
        student_id=str(session.student_id),
        mode=session.mode,
        subject=session.subject,
        topic=session.topic,
        started_at=session.started_at,
        ended_at=session.ended_at,
        summary=session.summary if hasattr(session, "summary") else None,
        is_archived=session.is_archived,
        message_count=session.message_count if hasattr(session, "message_count") else 0,
        device_info=session.device_info if hasattr(session, "device_info") else None,
    )
