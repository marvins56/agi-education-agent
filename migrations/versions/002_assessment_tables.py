"""Assessment tables — assessments, questions, submissions, question_grades.

Revision ID: 002
Revises: 001
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- assessments ---
    op.create_table(
        "assessments",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("config", JSONB, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("due_at", sa.DateTime(), nullable=True),
    )

    # --- questions ---
    op.create_table(
        "questions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("options", JSONB, nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("rubric", sa.Text(), nullable=True),
        sa.Column("points", sa.Integer(), server_default="10"),
        sa.Column("difficulty", sa.String(20), server_default="medium"),
        sa.Column("order_num", sa.Integer(), server_default="0"),
    )

    # --- submissions ---
    op.create_table(
        "submissions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answers", JSONB, nullable=False),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("graded_at", sa.DateTime(), nullable=True),
        sa.Column("total_score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
    )

    # --- question_grades ---
    op.create_table(
        "question_grades",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("graded_by", sa.String(50), server_default="ai"),
    )

    # Indexes
    op.create_index("ix_assessments_created_by", "assessments", ["created_by"])
    op.create_index("ix_questions_assessment_id", "questions", ["assessment_id"])
    op.create_index("ix_submissions_assessment_id", "submissions", ["assessment_id"])
    op.create_index("ix_submissions_student_id", "submissions", ["student_id"])
    op.create_index("ix_question_grades_submission_id", "question_grades", ["submission_id"])


def downgrade() -> None:
    op.drop_table("question_grades")
    op.drop_table("submissions")
    op.drop_table("questions")
    op.drop_table("assessments")
