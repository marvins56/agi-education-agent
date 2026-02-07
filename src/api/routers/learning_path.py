"""Learning path and spaced repetition endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db, get_memory
from src.learning_path.graph import PrerequisiteGraph
from src.learning_path.recommender import PathRecommender
from src.learning_path.spaced_repetition import SpacedRepetitionScheduler
from src.memory.manager import MemoryManager
from src.models.learning_path import ReviewSchedule, StudentGoal, TopicEdge, TopicNode
from src.models.user import User

router = APIRouter()


class GoalCreateRequest(BaseModel):
    topic_id: str
    target_mastery: float = 80.0
    deadline: date | None = None


class ReviewCompletedRequest(BaseModel):
    topic_id: str
    quality: int  # 0-5


@router.get("/learning-path/recommended")
async def get_recommended_path(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    memory_manager: MemoryManager = Depends(get_memory),
):
    """Get personalized study path based on goals and prerequisites."""
    graph = PrerequisiteGraph()
    await graph.load_from_db(db)

    # Load student goals
    result = await db.execute(
        select(StudentGoal)
        .where(StudentGoal.student_id == current_user.id)
        .where(StudentGoal.is_completed.is_(False))
    )
    goals = result.scalars().all()

    if not goals:
        return {"success": True, "data": []}

    goal_dicts = [
        {
            "topic_id": str(g.topic_id),
            "target_mastery": g.target_mastery,
        }
        for g in goals
    ]

    # Load actual student mastery data from TopicMastery records
    mastery_records = await memory_manager.get_student_mastery(str(current_user.id))
    student_mastery: dict[str, float] = {
        r["topic"]: r["mastery_score"] for r in mastery_records
    }

    recommender = PathRecommender(graph)
    recommendations = recommender.recommend(
        student_mastery=student_mastery,
        goals=goal_dicts,
    )

    return {"success": True, "data": recommendations}


@router.get("/learning-path/graph/{subject}")
async def get_prerequisite_graph(
    subject: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the prerequisite graph for a given subject."""
    result = await db.execute(
        select(TopicNode).where(TopicNode.subject == subject)
    )
    nodes = result.scalars().all()

    # Filter edges at SQL level instead of loading all edges
    node_id_list = [n.id for n in nodes]
    result = await db.execute(
        select(TopicEdge).where(
            or_(
                TopicEdge.from_topic_id.in_(node_id_list),
                TopicEdge.to_topic_id.in_(node_id_list),
            )
        )
    )
    filtered_edges = result.scalars().all()

    edges = [
        {
            "from_topic_id": str(e.from_topic_id),
            "to_topic_id": str(e.to_topic_id),
            "relationship": e.relationship_type,
            "weight": e.weight,
        }
        for e in filtered_edges
    ]

    node_list = [
        {
            "id": str(n.id),
            "subject": n.subject,
            "topic": n.topic,
            "display_name": n.display_name,
            "difficulty": n.difficulty,
            "estimated_minutes": n.estimated_minutes,
        }
        for n in nodes
    ]

    return {"success": True, "data": {"nodes": node_list, "edges": edges}}


@router.post("/learning-path/goals", status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new learning goal for the current student."""
    # Verify topic exists
    result = await db.execute(
        select(TopicNode).where(TopicNode.id == body.topic_id)
    )
    topic = result.scalars().first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    goal = StudentGoal(
        student_id=current_user.id,
        topic_id=body.topic_id,
        target_mastery=body.target_mastery,
        deadline=body.deadline,
    )
    db.add(goal)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(goal.id),
            "topic_id": str(goal.topic_id),
            "target_mastery": goal.target_mastery,
            "deadline": goal.deadline.isoformat() if goal.deadline else None,
        },
    }


@router.get("/learning-path/reviews-due")
async def get_reviews_due(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get topics due for spaced repetition review."""
    result = await db.execute(
        select(ReviewSchedule).where(ReviewSchedule.student_id == current_user.id)
    )
    schedules = result.scalars().all()

    schedule_dicts = [
        {
            "id": str(s.id),
            "topic_id": str(s.topic_id),
            "next_review_date": s.next_review_date,
            "interval_days": s.interval_days,
            "easiness_factor": s.easiness_factor,
            "review_count": s.review_count,
        }
        for s in schedules
    ]

    scheduler = SpacedRepetitionScheduler()
    due = scheduler.get_reviews_due(schedule_dicts, as_of=date.today())

    # Convert dates to strings for JSON serialization
    for item in due:
        if isinstance(item.get("next_review_date"), date):
            item["next_review_date"] = item["next_review_date"].isoformat()

    return {"success": True, "data": due}


@router.post("/learning-path/review-completed")
async def record_review_completed(
    body: ReviewCompletedRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a completed review and update the spaced repetition schedule."""
    result = await db.execute(
        select(ReviewSchedule)
        .where(ReviewSchedule.student_id == current_user.id)
        .where(ReviewSchedule.topic_id == body.topic_id)
    )
    schedule = result.scalars().first()

    scheduler = SpacedRepetitionScheduler()

    if schedule:
        updated = scheduler.calculate_next_review(
            quality=body.quality,
            repetition_count=schedule.review_count,
            easiness_factor=schedule.easiness_factor,
            current_interval=schedule.interval_days,
        )
        schedule.next_review_date = updated["next_review_date"]
        schedule.interval_days = updated["next_interval_days"]
        schedule.easiness_factor = updated["easiness_factor"]
        schedule.review_count += 1
        schedule.last_quality = body.quality
    else:
        updated = scheduler.calculate_next_review(
            quality=body.quality,
            repetition_count=0,
            easiness_factor=2.5,
            current_interval=1,
        )
        schedule = ReviewSchedule(
            student_id=current_user.id,
            topic_id=body.topic_id,
            next_review_date=updated["next_review_date"],
            interval_days=updated["next_interval_days"],
            easiness_factor=updated["easiness_factor"],
            review_count=1,
            last_quality=body.quality,
        )
        db.add(schedule)

    await db.flush()

    return {
        "success": True,
        "data": {
            "topic_id": str(schedule.topic_id),
            "next_review_date": schedule.next_review_date.isoformat(),
            "interval_days": schedule.interval_days,
            "easiness_factor": schedule.easiness_factor,
            "review_count": schedule.review_count,
        },
    }
