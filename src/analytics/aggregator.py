"""Async data aggregation layer for analytics dashboard."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.analytics.alerts import AlertEngine
from src.analytics.calculator import MetricsCalculator
from src.models.analytics import DailyMetric, WeeklyAggregate
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
                    "quiz_score_trend": {"average": 0.0, "direction": "stable", "scores": []},
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

            # Quiz score trend
            quiz_scores = []
            for e in quiz_events:
                if e.data and isinstance(e.data, dict) and "score" in e.data:
                    quiz_scores.append(float(e.data["score"]))
            quiz_trend = self.calc.calculate_quiz_score_trend(quiz_scores)

            # Best study time
            session_data = []
            for e in quiz_events:
                if e.created_at:
                    score = 100.0 if e.outcome == "correct" else 0.0
                    session_data.append({"hour": e.created_at.hour, "accuracy": score})
            best_time = self.calc.calculate_best_study_time(session_data)

            return {
                "total_events": len(events),
                "engagement_rate": round(engagement, 2),
                "streak": streak,
                "accuracy": round(accuracy, 2),
                "quiz_score_trend": quiz_trend,
                "best_study_time": best_time,
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

    async def get_student_mastery_by_subject(
        self, student_id: str, days: int = 90
    ) -> dict:
        """Return mastery levels grouped by subject and topic."""
        async with self.db_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            stmt = (
                select(LearningEvent)
                .where(LearningEvent.student_id == student_id)
                .where(LearningEvent.subject.isnot(None))
                .where(LearningEvent.created_at >= cutoff)
            )
            result = await session.execute(stmt)
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

    # ── Teacher / class-level methods ──────────────────────────────────────

    async def get_class_overview(self, class_id: str) -> dict:
        """Get class-level aggregate metrics.

        Note: class enrollment tables are not yet implemented.
        Returns a stub with the expected structure so the endpoint is functional.
        When class enrollment is added, this will query enrolled students.
        """
        return {
            "class_id": class_id,
            "class_avg_mastery": 0.0,
            "class_engagement": 0.0,
            "at_risk_count": 0,
            "total_students": 0,
            "topic_difficulty_ranking": [],
        }

    async def get_class_students(self, class_id: str) -> list[dict]:
        """Get per-student metrics for a class.

        Stub until class enrollment tables are available.
        """
        return []

    async def get_class_at_risk(self, class_id: str) -> list[dict]:
        """Get at-risk students in a class with alerts.

        Stub until class enrollment tables are available.
        """
        return []

    # ── Metric materialization ────────────────────────────────────────────

    async def record_daily_metrics(
        self, student_id: str, target_date: date
    ) -> dict:
        """Compute and persist daily metrics for a student.

        Fetches learning events for the given date, computes aggregate metrics
        using MetricsCalculator, and upserts a DailyMetric row.
        """
        async with self.db_session_factory() as session:
            day_start = datetime.combine(target_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            day_end = day_start + timedelta(days=1)

            result = await session.execute(
                select(LearningEvent)
                .where(LearningEvent.student_id == student_id)
                .where(LearningEvent.created_at >= day_start)
                .where(LearningEvent.created_at < day_end)
            )
            events = result.scalars().all()

            event_dicts = [
                {
                    "event_type": e.event_type,
                    "subject": e.subject,
                    "topic": e.topic,
                    "outcome": e.outcome,
                    "duration_minutes": (e.data or {}).get("duration_minutes", 0),
                }
                for e in events
            ]

            aggregated = self.calc.aggregate_daily_metrics(event_dicts, target_date)

            # Upsert: check if a row already exists
            existing = await session.execute(
                select(DailyMetric)
                .where(DailyMetric.student_id == student_id)
                .where(DailyMetric.date == target_date)
            )
            metric = existing.scalars().first()

            if metric:
                metric.sessions_count = aggregated["sessions_count"]
                metric.time_studied_minutes = aggregated["time_studied_minutes"]
                metric.questions_answered = aggregated["questions_answered"]
                metric.accuracy = aggregated["accuracy"]
                metric.topics_covered = aggregated["topics"]
            else:
                metric = DailyMetric(
                    student_id=student_id,
                    date=target_date,
                    sessions_count=aggregated["sessions_count"],
                    time_studied_minutes=aggregated["time_studied_minutes"],
                    questions_answered=aggregated["questions_answered"],
                    accuracy=aggregated["accuracy"],
                    topics_covered=aggregated["topics"],
                )
                session.add(metric)

            await session.commit()
            return aggregated

    async def record_weekly_aggregate(
        self, student_id: str, week_start: date
    ) -> dict:
        """Compute and persist weekly aggregates for a student.

        Summarises DailyMetric rows for the given week.
        """
        async with self.db_session_factory() as session:
            week_end = week_start + timedelta(days=7)

            result = await session.execute(
                select(DailyMetric)
                .where(DailyMetric.student_id == student_id)
                .where(DailyMetric.date >= week_start)
                .where(DailyMetric.date < week_end)
            )
            daily_rows = result.scalars().all()

            active_days = len(daily_rows)
            engagement = self.calc.calculate_engagement_rate(active_days, 7)
            accuracies = [d.accuracy for d in daily_rows if d.accuracy is not None]
            avg_mastery = sum(accuracies) / len(accuracies) if accuracies else 0.0

            data = {
                "week_start": week_start.isoformat(),
                "avg_mastery": round(avg_mastery, 2),
                "engagement_rate": round(engagement, 2),
                "velocity": 0.0,
                "streak_max": active_days,
            }

            existing = await session.execute(
                select(WeeklyAggregate)
                .where(WeeklyAggregate.student_id == student_id)
                .where(WeeklyAggregate.week_start == week_start)
            )
            agg = existing.scalars().first()

            if agg:
                agg.avg_mastery = data["avg_mastery"]
                agg.engagement_rate = data["engagement_rate"]
                agg.velocity = data["velocity"]
                agg.streak_max = data["streak_max"]
            else:
                agg = WeeklyAggregate(
                    student_id=student_id,
                    week_start=week_start,
                    avg_mastery=data["avg_mastery"],
                    velocity=data["velocity"],
                    engagement_rate=data["engagement_rate"],
                    streak_max=data["streak_max"],
                )
                session.add(agg)

            await session.commit()
            return data
