"""Add context summaries table for educational summarization

Revision ID: 008
Revises: 007
Create Date: 2026-02-17 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """Create context summaries table."""
    op.create_table(
        'context_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('summary_type', sa.String(50), nullable=False),
        sa.Column('summary_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index(
        'ix_context_summaries_session_id', 
        'context_summaries', 
        ['session_id']
    )
    op.create_index(
        'ix_context_summaries_student_id', 
        'context_summaries', 
        ['student_id']
    )
    op.create_index(
        'ix_context_summaries_created_at', 
        'context_summaries', 
        ['created_at']
    )
    op.create_index(
        'ix_context_summaries_summary_type', 
        'context_summaries', 
        ['summary_type']
    )
    
    # Composite index for common query patterns
    op.create_index(
        'ix_context_summaries_session_created', 
        'context_summaries', 
        ['session_id', 'created_at']
    )


def downgrade():
    """Drop context summaries table."""
    op.drop_index('ix_context_summaries_session_created', table_name='context_summaries')
    op.drop_index('ix_context_summaries_summary_type', table_name='context_summaries')
    op.drop_index('ix_context_summaries_created_at', table_name='context_summaries')
    op.drop_index('ix_context_summaries_student_id', table_name='context_summaries')
    op.drop_index('ix_context_summaries_session_id', table_name='context_summaries')
    op.drop_table('context_summaries')