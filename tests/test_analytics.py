"""Tests for analytics calculator, alerts, and related utilities."""

import pytest
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


class TestTopicMastery:
    def test_weighted_mastery_default_weights(self):
        mastery = MetricsCalculator.calculate_topic_mastery(
            quiz_score=80.0,
            ai_assessment_score=70.0,
            interaction_score=60.0,
            recency_score=90.0,
        )
        # 80*0.4 + 70*0.3 + 60*0.2 + 90*0.1 = 32 + 21 + 12 + 9 = 74
        assert mastery == 74.0

    def test_weighted_mastery_custom_weights(self):
        mastery = MetricsCalculator.calculate_topic_mastery(
            quiz_score=100.0,
            ai_assessment_score=0.0,
            interaction_score=0.0,
            recency_score=0.0,
            weights={"quiz": 1.0, "ai_assessment": 0.0, "interaction": 0.0, "recency": 0.0},
        )
        assert mastery == 100.0

    def test_weighted_mastery_clamped(self):
        mastery = MetricsCalculator.calculate_topic_mastery(
            quiz_score=0.0,
            ai_assessment_score=0.0,
            interaction_score=0.0,
            recency_score=0.0,
        )
        assert mastery == 0.0


class TestQuizScoreTrend:
    def test_improving_trend(self):
        scores = [40.0, 45.0, 50.0, 60.0, 70.0, 80.0]
        trend = MetricsCalculator.calculate_quiz_score_trend(scores)
        assert trend["direction"] == "improving"
        assert trend["average"] > 0

    def test_declining_trend(self):
        scores = [90.0, 80.0, 70.0, 60.0, 50.0]
        trend = MetricsCalculator.calculate_quiz_score_trend(scores)
        assert trend["direction"] == "declining"

    def test_stable_trend(self):
        scores = [70.0, 70.0, 70.0, 70.0, 70.0]
        trend = MetricsCalculator.calculate_quiz_score_trend(scores)
        assert trend["direction"] == "stable"
        assert trend["average"] == 70.0

    def test_empty_scores(self):
        trend = MetricsCalculator.calculate_quiz_score_trend([])
        assert trend["direction"] == "stable"
        assert trend["average"] == 0.0

    def test_window_limits_scores(self):
        scores = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
        trend = MetricsCalculator.calculate_quiz_score_trend(scores, window=3)
        # Only last 3: [60, 70, 80]
        assert len(trend["scores"]) == 3


class TestActiveStudyTime:
    def test_simple_durations(self):
        sessions = [
            {"duration_minutes": 30},
            {"duration_minutes": 45},
        ]
        total = MetricsCalculator.calculate_active_study_time(sessions)
        assert total == 75

    def test_idle_time_excluded(self):
        sessions = [
            {"duration_minutes": 60, "idle_minutes": 20},
        ]
        total = MetricsCalculator.calculate_active_study_time(sessions)
        assert total == 40  # 60 - 20

    def test_small_idle_kept(self):
        sessions = [
            {"duration_minutes": 60, "idle_minutes": 3},
        ]
        total = MetricsCalculator.calculate_active_study_time(sessions)
        assert total == 60  # idle < threshold, not subtracted

    def test_empty_sessions(self):
        assert MetricsCalculator.calculate_active_study_time([]) == 0


class TestAccuracyRateWeighted:
    def test_weighted_difficulty(self):
        rate = MetricsCalculator.calculate_accuracy_rate(
            correct=0,
            total=0,
            difficulty_weights={
                "easy": {"correct": 10, "total": 10, "weight": 0.5},
                "hard": {"correct": 5, "total": 10, "weight": 1.5},
            },
        )
        # weighted_correct = 10*0.5 + 5*1.5 = 5+7.5 = 12.5
        # weighted_total = 10*0.5 + 10*1.5 = 5+15 = 20
        # rate = 12.5/20 * 100 = 62.5
        assert rate == 62.5
