"""Analytics dashboard endpoints for students and teachers."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.aggregator import DataAggregator
from src.analytics.alerts import AlertEngine
from src.api.dependencies import get_current_user, get_db
from src.auth.rbac import Role, require_role
from src.models.database import async_session
from src.models.user import User

router = APIRouter()


def _get_aggregator() -> DataAggregator:
    return DataAggregator(db_session_factory=async_session)


# ── Student endpoints ──────────────────────────────────────────────────────

@router.get("/analytics/student/summary")
async def get_student_summary(
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get student dashboard summary: engagement, streak, accuracy, velocity."""
    summary = await aggregator.get_student_summary(str(current_user.id))
    return {"success": True, "data": summary}


@router.get("/analytics/student/mastery")
async def get_student_mastery(
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get mastery breakdown by subject with per-topic details."""
    mastery = await aggregator.get_student_mastery_by_subject(str(current_user.id))
    return {"success": True, "data": mastery}


@router.get("/analytics/student/activity")
async def get_student_activity(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get activity heatmap data for the last N days."""
    heatmap = await aggregator.get_student_activity_heatmap(str(current_user.id), days=days)
    return {"success": True, "data": heatmap}


@router.get("/analytics/student/streaks")
async def get_student_streaks(
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


@router.get("/analytics/student/alerts")
async def get_student_alerts(
    current_user: User = Depends(get_current_user),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Check for at-risk indicators and return alerts for the current student."""
    summary = await aggregator.get_student_summary(str(current_user.id))

    # Build the data dict expected by AlertEngine
    student_data = {
        "days_since_last_activity": 30 - summary.get("active_days", 0)
        if summary.get("total_events", 0) == 0
        else 0,
        "recent_mastery_scores": [],
        "engagement_rate": summary.get("engagement_rate", 0.0),
        "recent_quiz_scores": summary.get("quiz_score_trend", {}).get("scores", []),
    }

    alerts = AlertEngine.check_at_risk(student_data)
    return {"success": True, "data": alerts}


# ── Teacher endpoints ──────────────────────────────────────────────────────

@router.get("/analytics/teacher/class/{class_id}/overview")
async def get_class_overview(
    class_id: str,
    current_user: User = Depends(require_role(Role.teacher, Role.admin)),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get class-level summary: average mastery, engagement, at-risk count."""
    overview = await aggregator.get_class_overview(class_id)
    return {"success": True, "data": overview}


@router.get("/analytics/teacher/class/{class_id}/students")
async def get_class_students(
    class_id: str,
    current_user: User = Depends(require_role(Role.teacher, Role.admin)),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get per-student metrics for a class."""
    students = await aggregator.get_class_students(class_id)
    return {"success": True, "data": students}


@router.get("/analytics/teacher/class/{class_id}/at-risk")
async def get_class_at_risk(
    class_id: str,
    current_user: User = Depends(require_role(Role.teacher, Role.admin)),
    aggregator: DataAggregator = Depends(_get_aggregator),
):
    """Get at-risk students in a class with intervention suggestions."""
    at_risk = await aggregator.get_class_at_risk(class_id)
    return {"success": True, "data": at_risk}
