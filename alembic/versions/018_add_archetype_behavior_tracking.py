"""Add archetype and behavior tracking system (F3.1, F3.2)

Revision ID: 018
Revises: 017
Create Date: 2024-12-30

Adds:
- Archetype fields to users table (archetype, confidence, scores, detected_at, version)
- user_behavior_signals table for tracking behavioral metrics
- behavior_interactions table for individual interaction logs
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018_add_archetype_behavior_tracking'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add archetype fields to users and create behavior tracking tables."""

    # ========================================
    # 1. Add archetype fields to users table
    # ========================================
    op.add_column('users', sa.Column(
        'archetype',
        sa.Enum('explorer', 'direct', 'romantic', 'analytical', 'persistent', 'patient',
                name='archetypetype'),
        nullable=True
    ))
    op.add_column('users', sa.Column('archetype_confidence', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('archetype_scores', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('archetype_detected_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('archetype_version', sa.Integer(), nullable=True, default=1))

    # ========================================
    # 2. Create user_behavior_signals table
    # ========================================
    op.create_table(
        'user_behavior_signals',
        # Primary key
        sa.Column('user_id', sa.BigInteger(),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  primary_key=True),

        # Exploration metrics (EXPLORER)
        sa.Column('content_sections_visited', sa.Integer(), default=0, nullable=False),
        sa.Column('content_completion_rate', sa.Float(), default=0.0, nullable=False),
        sa.Column('easter_eggs_found', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_time_on_content', sa.Float(), default=0.0, nullable=False),
        sa.Column('revisits_old_content', sa.Integer(), default=0, nullable=False),

        # Speed/Directness metrics (DIRECT)
        sa.Column('avg_response_time', sa.Float(), default=0.0, nullable=False),
        sa.Column('avg_response_length', sa.Float(), default=0.0, nullable=False),
        sa.Column('button_vs_text_ratio', sa.Float(), default=0.0, nullable=False),
        sa.Column('avg_decision_time', sa.Float(), default=0.0, nullable=False),
        sa.Column('actions_per_session', sa.Float(), default=0.0, nullable=False),

        # Emotional metrics (ROMANTIC)
        sa.Column('emotional_words_count', sa.Integer(), default=0, nullable=False),
        sa.Column('question_count', sa.Integer(), default=0, nullable=False),
        sa.Column('long_responses_count', sa.Integer(), default=0, nullable=False),
        sa.Column('personal_questions_about_diana', sa.Integer(), default=0, nullable=False),

        # Analysis metrics (ANALYTICAL)
        sa.Column('quiz_avg_score', sa.Float(), default=0.0, nullable=False),
        sa.Column('structured_responses', sa.Integer(), default=0, nullable=False),
        sa.Column('error_reports', sa.Integer(), default=0, nullable=False),

        # Persistence metrics (PERSISTENT)
        sa.Column('return_after_inactivity', sa.Integer(), default=0, nullable=False),
        sa.Column('retry_failed_actions', sa.Integer(), default=0, nullable=False),
        sa.Column('incomplete_flows_completed', sa.Integer(), default=0, nullable=False),

        # Patience metrics (PATIENT)
        sa.Column('skip_actions_used', sa.Integer(), default=0, nullable=False),
        sa.Column('current_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('best_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_session_duration', sa.Float(), default=0.0, nullable=False),

        # Metadata
        sa.Column('total_interactions', sa.Integer(), default=0, nullable=False),
        sa.Column('first_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
    )

    # Indexes for user_behavior_signals
    op.create_index('idx_behavior_total_interactions', 'user_behavior_signals',
                    ['total_interactions'])
    op.create_index('idx_behavior_last_updated', 'user_behavior_signals',
                    ['last_updated_at'])

    # ========================================
    # 3. Create behavior_interactions table
    # ========================================
    op.create_table(
        'behavior_interactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('interaction_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
    )

    # Indexes for behavior_interactions
    op.create_index('idx_behavior_user_type', 'behavior_interactions',
                    ['user_id', 'interaction_type'])
    op.create_index('idx_behavior_user_created', 'behavior_interactions',
                    ['user_id', 'created_at'])
    op.create_index('idx_behavior_type_created', 'behavior_interactions',
                    ['interaction_type', 'created_at'])


def downgrade() -> None:
    """Remove archetype fields and behavior tracking tables."""

    # Drop behavior_interactions table and indexes
    op.drop_index('idx_behavior_type_created', 'behavior_interactions')
    op.drop_index('idx_behavior_user_created', 'behavior_interactions')
    op.drop_index('idx_behavior_user_type', 'behavior_interactions')
    op.drop_table('behavior_interactions')

    # Drop user_behavior_signals table and indexes
    op.drop_index('idx_behavior_last_updated', 'user_behavior_signals')
    op.drop_index('idx_behavior_total_interactions', 'user_behavior_signals')
    op.drop_table('user_behavior_signals')

    # Remove archetype columns from users
    op.drop_column('users', 'archetype_version')
    op.drop_column('users', 'archetype_detected_at')
    op.drop_column('users', 'archetype_scores')
    op.drop_column('users', 'archetype_confidence')
    op.drop_column('users', 'archetype')

    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS archetypetype')
