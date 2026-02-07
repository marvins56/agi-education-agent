"""At-risk student detection with configurable alert thresholds."""


class AlertEngine:
    """Check student data for at-risk indicators and generate alerts."""

    @staticmethod
    def check_at_risk(student_data: dict) -> list[dict]:
        """Return a list of alerts for at-risk indicators.

        student_data should include:
            - days_since_last_activity: int
            - recent_mastery_scores: list[float] (last N sessions)
            - engagement_rate: float (0-100)
            - recent_quiz_scores: list[float] (0-100)
        """
        alerts: list[dict] = []

        # 1. No activity for 7+ days
        days_inactive = student_data.get("days_since_last_activity", 0)
        if days_inactive >= 7:
            severity = "critical" if days_inactive >= 14 else "warning"
            alerts.append({
                "type": "no_activity_7_days",
                "severity": severity,
                "message": f"No activity for {days_inactive} days.",
                "suggestion": "Consider sending a re-engagement reminder or checking in.",
            })

        # 2. Mastery declining over last 3 sessions
        mastery_scores = student_data.get("recent_mastery_scores", [])
        if len(mastery_scores) >= 3:
            last_three = mastery_scores[-3:]
            if last_three[0] > last_three[1] > last_three[2]:
                alerts.append({
                    "type": "mastery_declining_3_sessions",
                    "severity": "warning",
                    "message": (
                        f"Mastery declining over last 3 sessions: "
                        f"{last_three[0]:.1f} -> {last_three[1]:.1f} -> {last_three[2]:.1f}."
                    ),
                    "suggestion": (
                        "Review foundational concepts or adjust difficulty level."
                    ),
                })

        # 3. Engagement below 30%
        engagement = student_data.get("engagement_rate", 100.0)
        if engagement < 30:
            alerts.append({
                "type": "engagement_below_30",
                "severity": "warning",
                "message": f"Engagement rate is {engagement:.1f}%, below 30% threshold.",
                "suggestion": "Try gamification or shorter, more frequent sessions.",
            })

        # 4. Quiz scores below 40%
        quiz_scores = student_data.get("recent_quiz_scores", [])
        if quiz_scores:
            avg_quiz = sum(quiz_scores) / len(quiz_scores)
            if avg_quiz < 40:
                alerts.append({
                    "type": "quiz_scores_below_40",
                    "severity": "critical",
                    "message": f"Average quiz score is {avg_quiz:.1f}%, below 40% threshold.",
                    "suggestion": (
                        "Revisit prerequisite topics and provide additional practice."
                    ),
                })

        return alerts
