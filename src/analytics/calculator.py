"""Pure calculation functions for analytics metrics."""

from datetime import date, timedelta

# Default weights for topic mastery calculation
MASTERY_WEIGHTS = {
    "quiz": 0.40,
    "ai_assessment": 0.30,
    "interaction": 0.20,
    "recency": 0.10,
}


class MetricsCalculator:
    """Stateless calculator for student analytics metrics."""

    @staticmethod
    def calculate_engagement_rate(active_days: int, total_days: int) -> float:
        """Calculate engagement as percentage of active days over total period."""
        return (active_days / max(total_days, 1)) * 100

    @staticmethod
    def calculate_accuracy_rate(
        correct: int,
        total: int,
        difficulty_weights: dict | None = None,
    ) -> float:
        """Calculate accuracy rate, optionally weighted by difficulty.

        If difficulty_weights maps difficulty -> {correct, total, weight},
        computes a weighted ratio. Otherwise simple correct/total * 100.
        """
        if difficulty_weights is not None:
            weighted_correct = 0.0
            weighted_total = 0.0
            for _diff, bucket in difficulty_weights.items():
                if isinstance(bucket, dict) and "weight" in bucket:
                    w = bucket["weight"]
                    weighted_correct += bucket.get("correct", 0) * w
                    weighted_total += bucket.get("total", 0) * w
            if weighted_total > 0:
                return (weighted_correct / weighted_total) * 100

        if total == 0:
            return 0.0

        return (correct / total) * 100

    @staticmethod
    def calculate_topic_mastery(
        quiz_score: float = 0.0,
        ai_assessment_score: float = 0.0,
        interaction_score: float = 0.0,
        recency_score: float = 0.0,
        weights: dict | None = None,
    ) -> float:
        """Calculate weighted topic mastery.

        Default weights: quiz 40%, ai_assessment 30%, interaction 20%, recency 10%.
        All scores should be 0-100.
        """
        w = weights or MASTERY_WEIGHTS
        mastery = (
            quiz_score * w.get("quiz", 0.4)
            + ai_assessment_score * w.get("ai_assessment", 0.3)
            + interaction_score * w.get("interaction", 0.2)
            + recency_score * w.get("recency", 0.1)
        )
        return round(min(100.0, max(0.0, mastery)), 2)

    @staticmethod
    def calculate_quiz_score_trend(scores: list[float], window: int = 5) -> dict:
        """Calculate rolling average quiz score trend.

        Returns {"average": float, "direction": "improving"|"declining"|"stable",
                 "scores": list[float]}.
        """
        if not scores:
            return {"average": 0.0, "direction": "stable", "scores": []}

        recent = scores[-window:]
        avg = sum(recent) / len(recent)

        direction = "stable"
        if len(recent) >= 2:
            first_half = recent[: len(recent) // 2]
            second_half = recent[len(recent) // 2 :]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            if avg_second - avg_first > 2.0:
                direction = "improving"
            elif avg_first - avg_second > 2.0:
                direction = "declining"

        return {"average": round(avg, 2), "direction": direction, "scores": recent}

    @staticmethod
    def calculate_active_study_time(
        session_durations: list[dict],
        idle_threshold_minutes: int = 5,
    ) -> int:
        """Sum session durations, excluding idle segments > threshold.

        Each dict should have 'duration_minutes' and optionally 'idle_minutes'.
        Returns total active minutes.
        """
        total = 0
        for s in session_durations:
            duration = s.get("duration_minutes", 0)
            idle = s.get("idle_minutes", 0)
            if idle > idle_threshold_minutes:
                duration -= idle
            total += max(0, duration)
        return total

    @staticmethod
    def calculate_streak(activity_dates: list[date]) -> int:
        """Count consecutive days of activity counting backwards from today."""
        if not activity_dates:
            return 0

        unique_dates = sorted(set(activity_dates), reverse=True)
        today = date.today()

        # If the most recent activity is not today or yesterday, streak is 0
        if unique_dates[0] < today - timedelta(days=1):
            return 0

        streak = 0
        expected = unique_dates[0]
        for d in unique_dates:
            if d == expected:
                streak += 1
                expected = d - timedelta(days=1)
            else:
                break

        return streak

    @staticmethod
    def calculate_best_study_time(sessions: list[dict]) -> str | None:
        """Return the hour (HH:00) with the highest average accuracy.

        Each session dict should have 'hour' (int 0-23) and 'accuracy' (float).
        """
        if not sessions:
            return None

        hour_totals: dict[int, list[float]] = {}
        for s in sessions:
            hour = s.get("hour")
            accuracy = s.get("accuracy", 0.0)
            if hour is not None:
                hour_totals.setdefault(hour, []).append(accuracy)

        if not hour_totals:
            return None

        best_hour = max(
            hour_totals,
            key=lambda h: sum(hour_totals[h]) / len(hour_totals[h]),
        )
        return f"{best_hour:02d}:00"

    @staticmethod
    def calculate_learning_velocity(mastery_history: list[dict]) -> float:
        """Calculate the slope of mastery scores over time using linear regression.

        Each dict should have 'day_index' (int) and 'mastery' (float).
        Returns slope (mastery points per day). Positive = improving.
        """
        if len(mastery_history) < 2:
            return 0.0

        n = len(mastery_history)
        xs = [entry["day_index"] for entry in mastery_history]
        ys = [entry["mastery"] for entry in mastery_history]

        sum_x = sum(xs)
        sum_y = sum(ys)
        sum_xy = sum(x * y for x, y in zip(xs, ys))
        sum_x2 = sum(x * x for x in xs)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return round(slope, 4)

    @staticmethod
    def aggregate_daily_metrics(events: list[dict], target_date: date) -> dict:
        """Aggregate learning events for a single day.

        Each event dict should have: 'event_type', 'subject', 'topic',
        'outcome', 'created_at' (date or datetime).
        """
        sessions_count = 0
        time_studied = 0
        questions_answered = 0
        correct = 0
        topics = set()

        for event in events:
            if event.get("event_type") == "session_start":
                sessions_count += 1
            if event.get("event_type") in ("quiz_answer", "question"):
                questions_answered += 1
                if event.get("outcome") == "correct":
                    correct += 1

            duration = event.get("duration_minutes", 0)
            time_studied += duration

            topic = event.get("topic")
            if topic:
                topics.add(topic)

        accuracy = (correct / questions_answered * 100) if questions_answered > 0 else 0.0

        return {
            "date": target_date.isoformat(),
            "sessions_count": sessions_count,
            "time_studied_minutes": time_studied,
            "questions_answered": questions_answered,
            "accuracy": round(accuracy, 2),
            "topics": sorted(topics),
        }
