"""Analytics dashboard and learning path tables.

Revision ID: 006
Revises: 005
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- daily_metrics ---
    op.create_table(
        "daily_metrics",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("sessions_count", sa.Integer(), server_default="0"),
        sa.Column("time_studied_minutes", sa.Integer(), server_default="0"),
        sa.Column("questions_answered", sa.Integer(), server_default="0"),
        sa.Column("accuracy", sa.Float(), server_default="0.0"),
        sa.Column("topics_covered", ARRAY(sa.String), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- weekly_aggregates ---
    op.create_table(
        "weekly_aggregates",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("avg_mastery", sa.Float(), server_default="0.0"),
        sa.Column("velocity", sa.Float(), server_default="0.0"),
        sa.Column("engagement_rate", sa.Float(), server_default="0.0"),
        sa.Column("streak_max", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- topic_nodes ---
    op.create_table(
        "topic_nodes",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("difficulty", sa.String(20), server_default="medium"),
        sa.Column("estimated_minutes", sa.Integer(), server_default="30"),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'")),
    )

    # --- topic_edges ---
    op.create_table(
        "topic_edges",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("from_topic_id", UUID(as_uuid=True), sa.ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_topic_id", UUID(as_uuid=True), sa.ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(50), server_default="requires"),
        sa.Column("weight", sa.Float(), server_default="1.0"),
    )

    # --- student_goals ---
    op.create_table(
        "student_goals",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", UUID(as_uuid=True), sa.ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_mastery", sa.Float(), server_default="80.0"),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- review_schedule ---
    op.create_table(
        "review_schedule",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", UUID(as_uuid=True), sa.ForeignKey("topic_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=False),
        sa.Column("interval_days", sa.Integer(), server_default="1"),
        sa.Column("easiness_factor", sa.Float(), server_default="2.5"),
        sa.Column("review_count", sa.Integer(), server_default="0"),
        sa.Column("last_quality", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("review_schedule")
    op.drop_table("student_goals")
    op.drop_table("topic_edges")
    op.drop_table("topic_nodes")
    op.drop_table("weekly_aggregates")
    op.drop_table("daily_metrics")
