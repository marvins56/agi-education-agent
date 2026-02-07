"""Add topic_mastery table.

Revision ID: 004
Revises: 003
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topic_mastery",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "student_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("mastery_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_assessed", sa.DateTime(), nullable=True),
        sa.Column("last_reviewed", sa.DateTime(), nullable=True),
        sa.Column("decay_rate", sa.Float(), server_default="0.02", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_unique_constraint(
        "uq_student_subject_topic",
        "topic_mastery",
        ["student_id", "subject", "topic"],
    )
    op.create_index("ix_topic_mastery_student_id", "topic_mastery", ["student_id"])
    op.create_index("ix_topic_mastery_subject", "topic_mastery", ["subject"])


def downgrade() -> None:
    op.drop_index("ix_topic_mastery_subject", table_name="topic_mastery")
    op.drop_index("ix_topic_mastery_student_id", table_name="topic_mastery")
    op.drop_constraint("uq_student_subject_topic", "topic_mastery", type_="unique")
    op.drop_table("topic_mastery")
