"""Add user LLM settings table

Revision ID: 009_user_llm_settings
Revises: 008_context_summaries
Create Date: 2026-02-18 17:49:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_user_llm_settings'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user LLM settings table."""
    op.create_table(
        'user_llm_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preferred_provider', sa.String(length=50), nullable=True),
        sa.Column('preferred_model', sa.String(length=100), nullable=True),
        sa.Column('anthropic_api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('openai_api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('google_api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('groq_api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Set default values
    op.alter_column('user_llm_settings', 'preferred_provider',
                   server_default='ollama')
    op.alter_column('user_llm_settings', 'is_active',
                   server_default=sa.text('true'))
    
    # Create index on user_id for faster lookups
    op.create_index('ix_user_llm_settings_user_id', 'user_llm_settings', ['user_id'])


def downgrade() -> None:
    """Drop user LLM settings table."""
    op.drop_index('ix_user_llm_settings_user_id', table_name='user_llm_settings')
    op.drop_table('user_llm_settings')