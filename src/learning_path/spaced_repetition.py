"""SM-2 spaced repetition algorithm implementation."""

from datetime import date, timedelta


class SpacedRepetitionScheduler:
    """SuperMemo SM-2 algorithm for scheduling review sessions."""

    @staticmethod
    def calculate_next_review(
        quality: int,
        repetition_count: int,
        easiness_factor: float,
        current_interval: int,
    ) -> dict:
        """Calculate the next review date using the SM-2 algorithm.

        Args:
            quality: 0-5 rating of recall quality (from quiz performance).
            repetition_count: Number of consecutive successful reviews.
            easiness_factor: Current easiness factor (minimum 1.3).
            current_interval: Current interval in days.

        Returns:
            dict with next_interval_days, easiness_factor, next_review_date.
        """
        # Clamp quality to 0-5
        quality = max(0, min(5, quality))

        # Adjust easiness factor
        new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(1.3, new_ef)

        if quality >= 3:
            # Successful recall
            if repetition_count == 0:
                new_interval = 1
            elif repetition_count == 1:
                new_interval = 6
            else:
                new_interval = max(1, round(current_interval * new_ef))
        else:
            # Failed recall — reset
            new_interval = 1

        next_review = date.today() + timedelta(days=new_interval)

        return {
            "next_interval_days": new_interval,
            "easiness_factor": round(new_ef, 4),
            "next_review_date": next_review,
        }

    @staticmethod
    def get_reviews_due(
        schedules: list[dict],
        as_of: date | None = None,
    ) -> list[dict]:
        """Filter schedules to only those due for review.

        Each schedule dict should have 'next_review_date' (date).
        Returns schedules where next_review_date <= as_of.
        """
        if as_of is None:
            as_of = date.today()

        return [s for s in schedules if s.get("next_review_date") and s["next_review_date"] <= as_of]
