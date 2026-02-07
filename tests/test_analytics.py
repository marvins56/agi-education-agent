"""Tests for analytics calculator, alerts, and related utilities."""

from datetime import date, timedelta

from src.analytics.calculator import MetricsCalculator
from src.analytics.alerts import AlertEngine


class TestEngagementRate:
    def test_engagement_rate_calculation(self):
        rate = MetricsCalculator.calculate_engagement_rate(active_days=15, total_days=30)
        assert rate == 50.0

    def test_engagement_rate_zero_total(self):
        rate = MetricsCalculator.calculate_engagement_rate(active_days=0, total_days=0)
        assert rate == 0.0

    def test_engagement_rate_full(self):
        rate = MetricsCalculator.calculate_engagement_rate(active_days=30, total_days=30)
        assert rate == 100.0


class TestAccuracyRate:
    def test_accuracy_rate_calculation(self):
        rate = MetricsCalculator.calculate_accuracy_rate(correct=8, total=10)
        assert rate == 80.0

    def test_accuracy_rate_zero_total(self):
        rate = MetricsCalculator.calculate_accuracy_rate(correct=0, total=0)
        assert rate == 0.0

    def test_accuracy_rate_perfect(self):
        rate = MetricsCalculator.calculate_accuracy_rate(correct=20, total=20)
        assert rate == 100.0


class TestStreak:
    def test_streak_calculation(self):
        """Consecutive days ending at today should produce a streak."""
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(5)]
        streak = MetricsCalculator.calculate_streak(dates)
        assert streak == 5

    def test_streak_calculation_with_gap(self):
        """A gap in dates should break the streak."""
        today = date.today()
        # Today, yesterday, skip day before, then 3 days
        dates = [
            today,
            today - timedelta(days=1),
            # gap at day 2
            today - timedelta(days=3),
            today - timedelta(days=4),
            today - timedelta(days=5),
        ]
        streak = MetricsCalculator.calculate_streak(dates)
        assert streak == 2

    def test_streak_empty(self):
        assert MetricsCalculator.calculate_streak([]) == 0

    def test_streak_old_activity(self):
        """Activity only from long ago gives streak 0."""
        old_date = date.today() - timedelta(days=30)
        assert MetricsCalculator.calculate_streak([old_date]) == 0


class TestLearningVelocity:
    def test_learning_velocity(self):
        """Increasing mastery should give positive slope."""
        history = [
            {"day_index": 0, "mastery": 20.0},
            {"day_index": 1, "mastery": 30.0},
            {"day_index": 2, "mastery": 40.0},
            {"day_index": 3, "mastery": 50.0},
        ]
        velocity = MetricsCalculator.calculate_learning_velocity(history)
        assert velocity == 10.0

    def test_learning_velocity_declining(self):
        history = [
            {"day_index": 0, "mastery": 80.0},
            {"day_index": 1, "mastery": 70.0},
            {"day_index": 2, "mastery": 60.0},
        ]
        velocity = MetricsCalculator.calculate_learning_velocity(history)
        assert velocity == -10.0

    def test_learning_velocity_single_point(self):
        history = [{"day_index": 0, "mastery": 50.0}]
        velocity = MetricsCalculator.calculate_learning_velocity(history)
        assert velocity == 0.0


class TestBestStudyTime:
    def test_best_study_time(self):
        sessions = [
            {"hour": 9, "accuracy": 80.0},
            {"hour": 9, "accuracy": 90.0},
            {"hour": 14, "accuracy": 60.0},
            {"hour": 14, "accuracy": 50.0},
        ]
        best = MetricsCalculator.calculate_best_study_time(sessions)
        assert best == "09:00"

    def test_best_study_time_empty(self):
        assert MetricsCalculator.calculate_best_study_time([]) is None


class TestDailyMetrics:
    def test_aggregate_daily_metrics(self):
        today = date.today()
        events = [
            {"event_type": "session_start", "topic": "algebra", "outcome": None, "duration_minutes": 30},
            {"event_type": "quiz_answer", "topic": "algebra", "outcome": "correct", "duration_minutes": 2},
            {"event_type": "quiz_answer", "topic": "algebra", "outcome": "incorrect", "duration_minutes": 2},
            {"event_type": "quiz_answer", "topic": "geometry", "outcome": "correct", "duration_minutes": 2},
        ]
        result = MetricsCalculator.aggregate_daily_metrics(events, today)
        assert result["sessions_count"] == 1
        assert result["questions_answered"] == 3
        assert result["accuracy"] == pytest.approx(66.67, abs=0.01)
        assert set(result["topics"]) == {"algebra", "geometry"}


class TestAlertEngineAtRisk:
    def test_at_risk_no_activity(self):
        data = {
            "days_since_last_activity": 10,
            "recent_mastery_scores": [70, 75, 80],
            "engagement_rate": 50.0,
            "recent_quiz_scores": [70, 80],
        }
        alerts = AlertEngine.check_at_risk(data)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "no_activity_7_days"
        assert alerts[0]["severity"] == "warning"

    def test_at_risk_no_activity_critical(self):
        data = {
            "days_since_last_activity": 14,
            "recent_mastery_scores": [],
            "engagement_rate": 50.0,
            "recent_quiz_scores": [],
        }
        alerts = AlertEngine.check_at_risk(data)
        assert any(a["severity"] == "critical" for a in alerts)

    def test_at_risk_declining_mastery(self):
        data = {
            "days_since_last_activity": 1,
            "recent_mastery_scores": [80.0, 70.0, 60.0],
            "engagement_rate": 50.0,
            "recent_quiz_scores": [70],
        }
        alerts = AlertEngine.check_at_risk(data)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "mastery_declining_3_sessions"

    def test_alert_engine_healthy_student(self):
        """A healthy student should generate no alerts."""
        data = {
            "days_since_last_activity": 0,
            "recent_mastery_scores": [70.0, 75.0, 80.0],
            "engagement_rate": 60.0,
            "recent_quiz_scores": [75, 80, 85],
        }
        alerts = AlertEngine.check_at_risk(data)
        assert alerts == []

    def test_at_risk_low_engagement(self):
        data = {
            "days_since_last_activity": 2,
            "recent_mastery_scores": [70],
            "engagement_rate": 20.0,
            "recent_quiz_scores": [70],
        }
        alerts = AlertEngine.check_at_risk(data)
        types = [a["type"] for a in alerts]
        assert "engagement_below_30" in types

    def test_at_risk_low_quiz_scores(self):
        data = {
            "days_since_last_activity": 1,
            "recent_mastery_scores": [50],
            "engagement_rate": 50.0,
            "recent_quiz_scores": [30, 35, 25],
        }
        alerts = AlertEngine.check_at_risk(data)
        types = [a["type"] for a in alerts]
        assert "quiz_scores_below_40" in types


# Import pytest for approx
import pytest
