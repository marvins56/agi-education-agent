"""Session management & auth hardening tables.

Revision ID: 005
Revises: 004
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("device_info", sa.String(255), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # --- sessions: add new columns ---
    op.add_column("sessions", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("sessions", sa.Column("message_count", sa.Integer(), server_default=sa.text("0")))
    op.add_column("sessions", sa.Column("device_info", sa.String(255), nullable=True))

    # --- users: add new columns ---
    op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("login_count", sa.Integer(), server_default=sa.text("0")))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("users", "is_verified")
    op.drop_column("users", "login_count")
    op.drop_column("users", "last_login")
    op.drop_column("sessions", "device_info")
    op.drop_column("sessions", "message_count")
    op.drop_column("sessions", "is_archived")
    op.drop_column("sessions", "summary")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
