"""Initial schema — users, student_profiles, sessions, learning_events.

Revision ID: 001
Revises: None
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="student"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- student_profiles ---
    op.create_table(
        "student_profiles",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learning_style", sa.String(50), server_default="balanced"),
        sa.Column("pace", sa.String(50), server_default="moderate"),
        sa.Column("grade_level", sa.String(50), nullable=True),
        sa.Column("strengths", ARRAY(sa.String), nullable=True),
        sa.Column("weaknesses", ARRAY(sa.String), nullable=True),
        sa.Column("preferences", JSONB, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- sessions ---
    op.create_table(
        "sessions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mode", sa.String(50), server_default="tutoring"),
        sa.Column("subject", sa.String(100), nullable=True),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'")),
    )

    # --- learning_events ---
    op.create_table(
        "learning_events",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(100), nullable=True),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("data", JSONB, nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Indexes for learning_events
    op.create_index("ix_learning_events_student_id", "learning_events", ["student_id"])
    op.create_index("ix_learning_events_subject", "learning_events", ["subject"])
    op.create_index("ix_learning_events_created_at", "learning_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("learning_events")
    op.drop_table("sessions")
    op.drop_table("student_profiles")
    op.drop_table("users")
