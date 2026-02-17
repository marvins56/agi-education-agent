"""Add adaptive learning tables

Revision ID: 5909f1fc5982
Revises: 008
Create Date: 2026-02-17 14:50:48.971585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5909f1fc5982'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Student knowledge states table
    op.create_table(
        'student_knowledge_states',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('student_id', sa.String(50), nullable=False),
        sa.Column('concept_probabilities', sa.JSON(), nullable=False, default={}),
        sa.Column('confidence_intervals', sa.JSON(), nullable=False, default={}),
        sa.Column('knowledge_growth_rate', sa.Float(), nullable=False, default=0.5),
        sa.Column('forgetting_rate', sa.Float(), nullable=False, default=0.1),
        sa.Column('learning_efficiency', sa.Float(), nullable=False, default=0.5),
        sa.Column('interaction_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create index on student_id for fast lookups
    op.create_index('idx_student_knowledge_states_student_id', 'student_knowledge_states', ['student_id'])
    
    # FSRS cards table for spaced repetition
    op.create_table(
        'fsrs_cards',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('student_id', sa.String(50), nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=False),
        sa.Column('concept_name', sa.String(255), nullable=False),
        sa.Column('stability', sa.Float(), nullable=False, default=1.0),
        sa.Column('difficulty', sa.Float(), nullable=False, default=5.0),
        sa.Column('retrievability', sa.Float(), nullable=False, default=1.0),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('last_review', sa.DateTime(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=False, default=0),
        sa.Column('average_response_time', sa.Float(), nullable=False, default=0.0),
        sa.Column('success_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('consecutive_successes', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create composite index for efficient queries
    op.create_index('idx_fsrs_cards_student_concept', 'fsrs_cards', ['student_id', 'concept_id'])
    op.create_index('idx_fsrs_cards_due_date', 'fsrs_cards', ['due_date'])
    
    # Student interactions table for tracking learning history
    op.create_table(
        'student_interactions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('student_id', sa.String(50), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=False),
        sa.Column('concept_name', sa.String(255), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('correctness', sa.Float(), nullable=False),
        sa.Column('response_time_seconds', sa.Float(), nullable=False),
        sa.Column('hint_count', sa.Integer(), nullable=False, default=0),
        sa.Column('difficulty_level', sa.Float(), nullable=False, default=0.5),
        sa.Column('context_features', sa.JSON(), nullable=False, default={}),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_student_interactions_student_id', 'student_interactions', ['student_id'])
    op.create_index('idx_student_interactions_concept', 'student_interactions', ['concept_name'])
    op.create_index('idx_student_interactions_timestamp', 'student_interactions', ['timestamp'])
    op.create_index('idx_student_interactions_session', 'student_interactions', ['session_id'])
    
    # Learning style profiles table
    op.create_table(
        'learning_style_profiles',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('student_id', sa.String(50), nullable=False),
        sa.Column('visual_preference', sa.Float(), nullable=False, default=0.5),
        sa.Column('auditory_preference', sa.Float(), nullable=False, default=0.5),
        sa.Column('kinesthetic_preference', sa.Float(), nullable=False, default=0.5),
        sa.Column('reading_preference', sa.Float(), nullable=False, default=0.5),
        sa.Column('sequential_vs_global', sa.Float(), nullable=False, default=0.5),
        sa.Column('active_vs_reflective', sa.Float(), nullable=False, default=0.5),
        sa.Column('sensing_vs_intuitive', sa.Float(), nullable=False, default=0.5),
        sa.Column('preferred_session_length_minutes', sa.Integer(), nullable=False, default=30),
        sa.Column('optimal_difficulty_preference', sa.Float(), nullable=False, default=0.6),
        sa.Column('feedback_frequency_preference', sa.Float(), nullable=False, default=0.8),
        sa.Column('attention_span_indicator', sa.Float(), nullable=False, default=0.5),
        sa.Column('motivation_level', sa.Float(), nullable=False, default=0.7),
        sa.Column('self_regulation_skill', sa.Float(), nullable=False, default=0.5),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create index on student_id
    op.create_index('idx_learning_style_profiles_student_id', 'learning_style_profiles', ['student_id'])
    
    # Difficulty calibration records table
    op.create_table(
        'difficulty_calibrations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('student_id', sa.String(50), nullable=False),
        sa.Column('concept_name', sa.String(255), nullable=False),
        sa.Column('current_difficulty', sa.Float(), nullable=False, default=0.5),
        sa.Column('target_success_rate', sa.Float(), nullable=False, default=0.75),
        sa.Column('actual_success_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('difficulty_history', sa.JSON(), nullable=False, default=[]),
        sa.Column('performance_history', sa.JSON(), nullable=False, default=[]),
        sa.Column('adjustment_rate', sa.Float(), nullable=False, default=0.1),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=False, default=0.0),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=False, default=1.0),
        sa.Column('last_calibrated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create composite index for efficient queries
    op.create_index('idx_difficulty_calibrations_student_concept', 'difficulty_calibrations', ['student_id', 'concept_name'])
    
    # Adaptive learning metrics table
    op.create_table(
        'adaptive_learning_metrics',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('student_id', sa.String(50), nullable=False),
        sa.Column('concepts_learned_per_hour', sa.Float(), nullable=False, default=0.0),
        sa.Column('average_time_to_mastery_minutes', sa.Float(), nullable=False, default=0.0),
        sa.Column('retention_rate_after_week', sa.Float(), nullable=False, default=0.0),
        sa.Column('session_completion_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('voluntary_practice_frequency', sa.Float(), nullable=False, default=0.0),
        sa.Column('help_seeking_behavior_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('prediction_accuracy', sa.Float(), nullable=False, default=0.0),
        sa.Column('recommendation_acceptance_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('difficulty_calibration_accuracy', sa.Float(), nullable=False, default=0.0),
        sa.Column('knowledge_growth_velocity', sa.Float(), nullable=False, default=0.0),
        sa.Column('learning_momentum', sa.Float(), nullable=False, default=0.0),
        sa.Column('plateau_detection_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('calculation_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create index on student_id and calculation_date
    op.create_index('idx_adaptive_metrics_student_date', 'adaptive_learning_metrics', ['student_id', 'calculation_date'])


def downgrade() -> None:
    # Drop all adaptive learning tables in reverse order
    op.drop_table('adaptive_learning_metrics')
    op.drop_table('difficulty_calibrations')
    op.drop_table('learning_style_profiles')
    op.drop_table('student_interactions')
    op.drop_table('fsrs_cards')
    op.drop_table('student_knowledge_states')
