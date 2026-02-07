"""Analytics dashboard endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.aggregator import DataAggregator
from src.api.dependencies import get_current_user, get_db
from src.models.database import async_session
from src.models.user import User

router = APIRouter()


def _get_aggregator() -> DataAggregator:
    return DataAggregator(db_session_factory=async_session)


@router.get("/analytics/summary")
async def get_summary(
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get student dashboard summary: engagement, streak, accuracy, velocity."""
    summary = await aggregator.get_student_summary(str(current_user.id))
    return {"success": True, "data": summary}


@router.get("/analytics/mastery")
async def get_mastery(
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get mastery breakdown by subject with per-topic details."""
    mastery = await aggregator.get_student_mastery_by_subject(str(current_user.id))
    return {"success": True, "data": mastery}


@router.get("/analytics/activity")
async def get_activity(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get activity heatmap data for the last N days."""
    heatmap = await aggregator.get_student_activity_heatmap(str(current_user.id), days=days)
    return {"success": True, "data": heatmap}


@router.get("/analytics/streaks")
async def get_streaks(
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get streak data for the current student."""
    summary = await aggregator.get_student_summary(str(current_user.id))
    return {
        "success": True,
        "data": {
            "current_streak": summary.get("streak", 0),
            "active_days": summary.get("active_days", 0),
        },
    }
