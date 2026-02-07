"""Async data aggregation layer for analytics dashboard."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.analytics.calculator import MetricsCalculator
from src.models.learning_event import LearningEvent


class DataAggregator:
    """Fetches data from the database and computes dashboard metrics."""

    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession]):
        self.db_session_factory = db_session_factory
        self.calc = MetricsCalculator()

    async def get_student_summary(self, student_id: str) -> dict:
        """Fetch and compute all student dashboard metrics."""
        async with self.db_session_factory() as session:
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)

            result = await session.execute(
                select(LearningEvent)
                .where(LearningEvent.student_id == student_id)
                .where(LearningEvent.created_at >= thirty_days_ago)
                .order_by(LearningEvent.created_at.desc())
            )
            events = result.scalars().all()

            if not events:
                return {
                    "total_events": 0,
                    "engagement_rate": 0.0,
                    "streak": 0,
                    "accuracy": 0.0,
                    "best_study_time": None,
                    "velocity": 0.0,
                    "active_days": 0,
                    "total_days": 30,
                }

            # Compute active days
            active_dates = list({e.created_at.date() for e in events if e.created_at})
            engagement = self.calc.calculate_engagement_rate(len(active_dates), 30)
            streak = self.calc.calculate_streak(active_dates)

            # Accuracy
            quiz_events = [e for e in events if e.event_type in ("quiz_answer", "question")]
            correct = sum(1 for e in quiz_events if e.outcome == "correct")
            accuracy = self.calc.calculate_accuracy_rate(correct, len(quiz_events))

            return {
                "total_events": len(events),
                "engagement_rate": round(engagement, 2),
                "streak": streak,
                "accuracy": round(accuracy, 2),
                "best_study_time": None,
                "velocity": 0.0,
                "active_days": len(active_dates),
                "total_days": 30,
            }

    async def get_student_activity_heatmap(
        self, student_id: str, days: int = 30
    ) -> list[dict]:
        """Return activity counts grouped by day and hour."""
        async with self.db_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            result = await session.execute(
                select(LearningEvent)
                .where(LearningEvent.student_id == student_id)
                .where(LearningEvent.created_at >= cutoff)
            )
            events = result.scalars().all()

            heatmap: dict[tuple[str, int], int] = {}
            for event in events:
                if event.created_at:
                    day = event.created_at.strftime("%Y-%m-%d")
                    hour = event.created_at.hour
                    key = (day, hour)
                    heatmap[key] = heatmap.get(key, 0) + 1

            return [
                {"day": day, "hour": hour, "count": count}
                for (day, hour), count in sorted(heatmap.items())
            ]

    async def get_student_mastery_by_subject(self, student_id: str) -> dict:
        """Return mastery levels grouped by subject and topic.

        Mastery data is derived from learning events. If no mastery data
        exists yet, returns empty subjects.
        """
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(LearningEvent)
                .where(LearningEvent.student_id == student_id)
                .where(LearningEvent.subject.isnot(None))
            )
            events = result.scalars().all()

            subjects: dict[str, dict] = {}
            for event in events:
                subj = event.subject
                topic = event.topic or "general"

                if subj not in subjects:
                    subjects[subj] = {"topics": {}}

                if topic not in subjects[subj]["topics"]:
                    subjects[subj]["topics"][topic] = {
                        "topic": topic,
                        "total": 0,
                        "correct": 0,
                    }

                entry = subjects[subj]["topics"][topic]
                if event.event_type in ("quiz_answer", "question"):
                    entry["total"] += 1
                    if event.outcome == "correct":
                        entry["correct"] += 1

            # Convert to list format with mastery scores
            result_dict = {}
            for subj, data in subjects.items():
                topic_list = []
                for topic_data in data["topics"].values():
                    total = topic_data["total"]
                    mastery = (topic_data["correct"] / total * 100) if total > 0 else 0.0
                    level = "beginner"
                    if mastery >= 80:
                        level = "advanced"
                    elif mastery >= 50:
                        level = "intermediate"

                    topic_list.append({
                        "topic": topic_data["topic"],
                        "mastery": round(mastery, 2),
                        "level": level,
                    })

                result_dict[subj] = {"topics": topic_list}

            return result_dict
