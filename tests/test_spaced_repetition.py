"""Dedicated tests for the SM-2 spaced repetition algorithm."""

from datetime import date, timedelta

from src.learning_path.spaced_repetition import SpacedRepetitionScheduler


class TestSM2Algorithm:
    """Core SM-2 algorithm tests."""

    def test_quality_5_increases_ef(self):
        """Perfect recall (quality=5) should increase the easiness factor."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=5, repetition_count=3, easiness_factor=2.5, current_interval=10
        )
        # EF' = 2.5 + (0.1 - 0*0.08) = 2.6
        assert result["easiness_factor"] == 2.6

    def test_quality_4_barely_changes_ef(self):
        """Quality 4 should barely change the easiness factor."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=4, repetition_count=3, easiness_factor=2.5, current_interval=10
        )
        # EF' = 2.5 + (0.1 - 1*(0.08 + 1*0.02)) = 2.5 + 0.0 = 2.5
        assert result["easiness_factor"] == 2.5

    def test_quality_3_decreases_ef(self):
        """Minimal pass (quality=3) should decrease EF."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=3, repetition_count=3, easiness_factor=2.5, current_interval=10
        )
        # EF' = 2.5 + (0.1 - 2*(0.08 + 2*0.02)) = 2.5 - 0.14 = 2.36
        assert result["easiness_factor"] == 2.36

    def test_quality_0_clamps_ef_to_minimum(self):
        """Quality 0 with low EF should clamp to 1.3."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=0, repetition_count=0, easiness_factor=1.3, current_interval=1
        )
        assert result["easiness_factor"] == 1.3

    def test_quality_clamped_above_5(self):
        """Quality above 5 should be clamped to 5."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=8, repetition_count=2, easiness_factor=2.5, current_interval=6
        )
        # Should behave like quality=5
        assert result["easiness_factor"] == 2.6

    def test_quality_clamped_below_0(self):
        """Quality below 0 should be clamped to 0."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=-2, repetition_count=2, easiness_factor=2.5, current_interval=6
        )
        # Should behave like quality=0 (reset)
        assert result["next_interval_days"] == 1


class TestSM2IntervalProgression:
    """Test the interval progression through SM-2 stages."""

    def test_first_review_interval_is_1(self):
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=4, repetition_count=0, easiness_factor=2.5, current_interval=0
        )
        assert result["next_interval_days"] == 1

    def test_second_review_interval_is_6(self):
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=4, repetition_count=1, easiness_factor=2.5, current_interval=1
        )
        assert result["next_interval_days"] == 6

    def test_third_review_uses_ef_multiplication(self):
        """Third+ reviews: interval = prev * EF."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=5, repetition_count=2, easiness_factor=2.5, current_interval=6
        )
        # EF adjusts to 2.6, interval = round(6 * 2.6) = 16
        assert result["next_interval_days"] == 16

    def test_failed_recall_resets_interval(self):
        """Quality < 3 should always reset interval to 1."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=2, repetition_count=10, easiness_factor=2.5, current_interval=60
        )
        assert result["next_interval_days"] == 1

    def test_interval_minimum_is_1(self):
        """Interval should never go below 1 day."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=3, repetition_count=2, easiness_factor=1.3, current_interval=1
        )
        assert result["next_interval_days"] >= 1


class TestSM2ReviewDate:
    def test_review_date_is_today_plus_interval(self):
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=5, repetition_count=0, easiness_factor=2.5, current_interval=0
        )
        assert result["next_review_date"] == date.today() + timedelta(days=1)


class TestReviewsDue:
    def test_overdue_included(self):
        today = date.today()
        schedules = [
            {"topic_id": "a", "next_review_date": today - timedelta(days=3)},
        ]
        due = SpacedRepetitionScheduler.get_reviews_due(schedules, as_of=today)
        assert len(due) == 1

    def test_today_included(self):
        today = date.today()
        schedules = [{"topic_id": "a", "next_review_date": today}]
        due = SpacedRepetitionScheduler.get_reviews_due(schedules, as_of=today)
        assert len(due) == 1

    def test_future_excluded(self):
        today = date.today()
        schedules = [{"topic_id": "a", "next_review_date": today + timedelta(days=1)}]
        due = SpacedRepetitionScheduler.get_reviews_due(schedules, as_of=today)
        assert len(due) == 0

    def test_none_review_date_excluded(self):
        schedules = [{"topic_id": "a", "next_review_date": None}]
        due = SpacedRepetitionScheduler.get_reviews_due(schedules, as_of=date.today())
        assert len(due) == 0

    def test_default_as_of_is_today(self):
        today = date.today()
        schedules = [{"topic_id": "a", "next_review_date": today}]
        due = SpacedRepetitionScheduler.get_reviews_due(schedules)
        assert len(due) == 1
