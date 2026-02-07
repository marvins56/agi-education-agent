"""Mastery calculation and decay functions."""


class MasteryCalculator:
    """Calculate and manage topic mastery scores."""

    LEVELS = [
        (20, "Novice"),
        (40, "Beginner"),
        (60, "Intermediate"),
        (80, "Advanced"),
        (100, "Expert"),
    ]

    @staticmethod
    def calculate_mastery(
        quiz_scores: list[float],
        ai_assessments: list[float],
        interaction_quality: list[float],
        days_since_last: int = 0,
        decay_rate: float = 0.02,
    ) -> float:
        """Calculate weighted mastery score.

        Weights: quiz 0.4, ai_assessment 0.3, interaction 0.2, recency 0.1.
        Recency = max(0, 1 - days_since_last * decay_rate).
        """
        quiz_avg = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0.0
        ai_avg = sum(ai_assessments) / len(ai_assessments) if ai_assessments else 0.0
        interaction_avg = (
            sum(interaction_quality) / len(interaction_quality)
            if interaction_quality
            else 0.0
        )
        recency = max(0.0, 1.0 - days_since_last * decay_rate)

        # Recency component is scaled to 100 for consistent weighting
        score = (
            quiz_avg * 0.4
            + ai_avg * 0.3
            + interaction_avg * 0.2
            + recency * 100.0 * 0.1
        )
        return round(min(100.0, max(0.0, score)), 2)

    @classmethod
    def get_mastery_level(cls, score: float) -> str:
        """Map a numeric mastery score to a human-readable level."""
        for threshold, label in cls.LEVELS:
            if score <= threshold:
                return label
        return "Expert"

    @staticmethod
    def apply_decay(
        current_mastery: float,
        days_since_review: int,
        decay_rate: float = 0.02,
    ) -> float:
        """Apply time-based decay to a mastery score."""
        return round(max(0.0, current_mastery - decay_rate * days_since_review), 2)
