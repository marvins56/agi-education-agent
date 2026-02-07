"""Add indexes and unique constraints for analytics and learning path tables.

Revision ID: 007
Revises: 006
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- daily_metrics indexes ---
    op.create_index(
        "ix_daily_metrics_student_date", "daily_metrics", ["student_id", "date"]
    )
    op.create_index(
        "ix_daily_metrics_student_metric_type",
        "daily_metrics",
        ["student_id", "date"],
    )
    op.create_unique_constraint(
        "uq_daily_metrics_student_date", "daily_metrics", ["student_id", "date"]
    )

    # --- weekly_aggregates indexes ---
    op.create_index(
        "ix_weekly_aggregates_student_week",
        "weekly_aggregates",
        ["student_id", "week_start"],
    )
    op.create_unique_constraint(
        "uq_weekly_aggregates_student_week",
        "weekly_aggregates",
        ["student_id", "week_start"],
    )

    # --- topic_edges indexes ---
    op.create_index("ix_topic_edges_from", "topic_edges", ["from_topic_id"])
    op.create_index("ix_topic_edges_to", "topic_edges", ["to_topic_id"])
    op.create_unique_constraint(
        "uq_topic_edges_from_to", "topic_edges", ["from_topic_id", "to_topic_id"]
    )

    # --- student_goals indexes ---
    op.create_index(
        "ix_student_goals_student_status",
        "student_goals",
        ["student_id", "is_completed"],
    )
    op.create_unique_constraint(
        "uq_student_goals_student_topic",
        "student_goals",
        ["student_id", "topic_id"],
    )

    # --- review_schedule indexes ---
    op.create_index(
        "ix_review_schedule_student_review",
        "review_schedule",
        ["student_id", "next_review_date"],
    )
    op.create_unique_constraint(
        "uq_review_schedule_student_topic",
        "review_schedule",
        ["student_id", "topic_id"],
    )


def downgrade() -> None:
    # --- review_schedule ---
    op.drop_constraint("uq_review_schedule_student_topic", "review_schedule")
    op.drop_index("ix_review_schedule_student_review", "review_schedule")

    # --- student_goals ---
    op.drop_constraint("uq_student_goals_student_topic", "student_goals")
    op.drop_index("ix_student_goals_student_status", "student_goals")

    # --- topic_edges ---
    op.drop_constraint("uq_topic_edges_from_to", "topic_edges")
    op.drop_index("ix_topic_edges_to", "topic_edges")
    op.drop_index("ix_topic_edges_from", "topic_edges")

    # --- weekly_aggregates ---
    op.drop_constraint("uq_weekly_aggregates_student_week", "weekly_aggregates")
    op.drop_index("ix_weekly_aggregates_student_week", "weekly_aggregates")

    # --- daily_metrics ---
    op.drop_constraint("uq_daily_metrics_student_date", "daily_metrics")
    op.drop_index("ix_daily_metrics_student_metric_type", "daily_metrics")
    op.drop_index("ix_daily_metrics_student_date", "daily_metrics")
