"""Document tables for content management.

Revision ID: 003
Revises: 002
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(100), nullable=True),
        sa.Column("grade_level", sa.String(50), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'")),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("ix_documents_subject", "documents", ["subject"])
    op.create_index("ix_documents_status", "documents", ["status"])


def downgrade() -> None:
    op.drop_table("documents")
