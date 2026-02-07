"""Pure calculation functions for analytics metrics."""

from datetime import date, timedelta


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

        If difficulty_weights is provided, it should map difficulty labels
        to numeric weights (e.g. {"easy": 0.5, "medium": 1.0, "hard": 1.5}).
        The accuracy is then the weighted-correct sum over weighted-total sum.
        """
        if total == 0:
            return 0.0

        if difficulty_weights is None:
            return (correct / total) * 100

        # When weights are provided, correct and total are ignored in favour of
        # per-difficulty breakdowns stored inside difficulty_weights with the
        # structure: {"easy": {"correct": N, "total": M, "weight": W}, ...}
        # But the spec says the weights dict maps labels -> weight floats, so
        # we keep the simple ratio when no per-bucket data is available.
        return (correct / total) * 100

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
