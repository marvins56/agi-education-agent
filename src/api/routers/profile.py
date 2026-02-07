"""Profile and mastery endpoints."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.models.mastery import TopicMastery
from src.models.user import StudentProfile, User

router = APIRouter()


# --- Schemas ---

class ProfileResponse(BaseModel):
    name: str
    email: str
    learning_style: str
    pace: str
    grade_level: str | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    preferences: dict[str, Any] = {}

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    learning_style: str | None = None
    pace: str | None = None
    grade_level: str | None = None


class TopicMasteryResponse(BaseModel):
    subject: str
    topic: str
    mastery_score: float
    confidence: float
    attempts: int
    last_assessed: datetime | None = None

    model_config = {"from_attributes": True}


class MasteryBySubjectResponse(BaseModel):
    subject: str
    topics: list[TopicMasteryResponse]
    average_mastery: float


class LearningHistoryItem(BaseModel):
    event_type: str
    subject: str | None = None
    topic: str | None = None
    outcome: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class LearningHistoryResponse(BaseModel):
    items: list[LearningHistoryItem]
    total: int


class StreaksResponse(BaseModel):
    last_active: datetime | None = None
    total_sessions: int = 0


# --- Endpoints ---

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile with learning preferences."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalars().first()

    if not profile:
        return ProfileResponse(
            name=current_user.name,
            email=current_user.email,
            learning_style="balanced",
            pace="moderate",
        )

    return ProfileResponse(
        name=current_user.name,
        email=current_user.email,
        learning_style=profile.learning_style or "balanced",
        pace=profile.pace or "moderate",
        grade_level=profile.grade_level,
        strengths=profile.strengths or [],
        weaknesses=profile.weaknesses or [],
        preferences=profile.preferences or {},
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update learning preferences."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalars().first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    if body.learning_style is not None:
        profile.learning_style = body.learning_style
    if body.pace is not None:
        profile.pace = body.pace
    if body.grade_level is not None:
        profile.grade_level = body.grade_level

    await db.flush()

    return ProfileResponse(
        name=current_user.name,
        email=current_user.email,
        learning_style=profile.learning_style or "balanced",
        pace=profile.pace or "moderate",
        grade_level=profile.grade_level,
        strengths=profile.strengths or [],
        weaknesses=profile.weaknesses or [],
        preferences=profile.preferences or {},
    )


@router.get("/profile/mastery", response_model=list[MasteryBySubjectResponse])
async def get_mastery(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mastery scores grouped by subject."""
    result = await db.execute(
        select(TopicMastery)
        .where(TopicMastery.student_id == current_user.id)
        .order_by(TopicMastery.subject, TopicMastery.topic)
    )
    records = result.scalars().all()

    grouped: dict[str, list[TopicMastery]] = {}
    for r in records:
        grouped.setdefault(r.subject, []).append(r)

    return [
        MasteryBySubjectResponse(
            subject=subject,
            topics=[
                TopicMasteryResponse(
                    subject=t.subject,
                    topic=t.topic,
                    mastery_score=t.mastery_score,
                    confidence=t.confidence,
                    attempts=t.attempts,
                    last_assessed=t.last_assessed,
                )
                for t in topics
            ],
            average_mastery=(
                sum(t.mastery_score for t in topics) / len(topics) if topics else 0.0
            ),
        )
        for subject, topics in grouped.items()
    ]


@router.get("/profile/mastery/{subject}", response_model=MasteryBySubjectResponse)
async def get_mastery_by_subject(
    subject: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mastery for a specific subject with topic breakdown."""
    result = await db.execute(
        select(TopicMastery)
        .where(
            TopicMastery.student_id == current_user.id,
            TopicMastery.subject == subject,
        )
        .order_by(TopicMastery.topic)
    )
    records = result.scalars().all()

    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mastery data found for subject: {subject}",
        )

    return MasteryBySubjectResponse(
        subject=subject,
        topics=[
            TopicMasteryResponse(
                subject=t.subject,
                topic=t.topic,
                mastery_score=t.mastery_score,
                confidence=t.confidence,
                attempts=t.attempts,
                last_assessed=t.last_assessed,
            )
            for t in records
        ],
        average_mastery=sum(t.mastery_score for t in records) / len(records),
    )


@router.get("/profile/history", response_model=LearningHistoryResponse)
async def get_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get learning history summary."""
    from src.models.learning_event import LearningEvent
    from sqlalchemy import func

    result = await db.execute(
        select(LearningEvent)
        .where(LearningEvent.student_id == current_user.id)
        .order_by(LearningEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    count_result = await db.execute(
        select(func.count(LearningEvent.id)).where(
            LearningEvent.student_id == current_user.id
        )
    )
    total = count_result.scalar() or 0

    return LearningHistoryResponse(
        items=[
            LearningHistoryItem(
                event_type=e.event_type,
                subject=e.subject,
                topic=e.topic,
                outcome=e.outcome,
                created_at=e.created_at,
            )
            for e in events
        ],
        total=total,
    )


@router.get("/profile/streaks", response_model=StreaksResponse)
async def get_streaks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get engagement data (total sessions, last active)."""
    from src.models.session import Session
    from sqlalchemy import func

    result = await db.execute(
        select(
            func.count(Session.id).label("total"),
            func.max(Session.started_at).label("last_active"),
        ).where(Session.student_id == current_user.id)
    )
    row = result.one_or_none()

    if not row or row.total == 0:
        return StreaksResponse()

    return StreaksResponse(
        total_sessions=row.total,
        last_active=row.last_active,
    )
