"""add archetype detection system

Revision ID: 015
Revises: 014
Create Date: 2025-01-03

Sistema de detección de arquetipos de usuario (FASE 3):
- Tabla UserBehaviorSignals para tracking de comportamiento
- Campos de arquetipo en UserGamification
- Enum InteractionType para tipos de interacción
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add archetype detection system."""

    # ============================================================
    # 1. CREATE USER BEHAVIOR SIGNALS TABLE
    # ============================================================
    op.create_table(
        'user_behavior_signals',
        sa.Column('user_id', sa.BigInteger(), primary_key=True),
        # Exploration metrics (EXPLORER)
        sa.Column('content_sections_visited', sa.Integer(), default=0, nullable=False),
        sa.Column('content_completion_rate', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('easter_eggs_found', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_time_on_content', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('revisits_old_content', sa.Integer(), default=0, nullable=False),
        sa.Column('unique_content_per_session', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('explore_depth', sa.Integer(), default=0, nullable=False),

        # Speed/efficiency metrics (DIRECT)
        sa.Column('avg_time_to_click', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('avg_decision_time', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('actions_per_session', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('quick_actions_count', sa.Integer(), default=0, nullable=False),
        sa.Column('direct_navigation_ratio', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('skips_explanation', sa.Integer(), default=0, nullable=False),

        # Emotional metrics (ROMANTIC) - DERIVED FROM CONTENT TAGS
        sa.Column('emotional_content_views', sa.Integer(), default=0, nullable=False),
        sa.Column('personal_stories_accessed', sa.Integer(), default=0, nullable=False),
        sa.Column('likes_vs_saves_ratio', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('repeat_emotional_visits', sa.Integer(), default=0, nullable=False),
        sa.Column('diana_mnemonics_interactions', sa.Integer(), default=0, nullable=False),

        # Analysis metrics (ANALYTICAL)
        sa.Column('evaluation_scores_avg', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('evaluation_completion_rate', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('info_requests', sa.Integer(), default=0, nullable=False),
        sa.Column('systematic_exploration', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('details_viewed', sa.Integer(), default=0, nullable=False),
        sa.Column('puzzle_completion_time', sa.Integer(), default=0, nullable=False),  # Stored as int*100

        # Persistence metrics (PERSISTENT)
        sa.Column('return_after_inactivity', sa.Integer(), default=0, nullable=False),
        sa.Column('retry_failed_actions', sa.Integer(), default=0, nullable=False),
        sa.Column('incomplete_flows_completed', sa.Integer(), default=0, nullable=False),
        sa.Column('account_age_days', sa.Integer(), default=0, nullable=False),
        sa.Column('return_rate', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('streak_restarts', sa.Integer(), default=0, nullable=False),

        # Patience metrics (PATIENT)
        sa.Column('skip_actions_used', sa.Integer(), default=0, nullable=False),
        sa.Column('current_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('best_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_session_duration', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('session_consistency', sa.Integer(), default=0, nullable=False),  # Stored as int*100
        sa.Column('slow_decision_count', sa.Integer(), default=0, nullable=False),

        # General metrics
        sa.Column('total_interactions', sa.Integer(), default=0, nullable=False),
        sa.Column('total_sessions', sa.Integer(), default=0, nullable=False),
        sa.Column('first_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('last_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE')
    )

    # Create indexes for UserBehaviorSignals
    op.create_index('idx_behavior_total_interactions', 'user_behavior_signals', ['total_interactions'])
    op.create_index('idx_behavior_last_interaction', 'user_behavior_signals', ['last_interaction_at'])
    op.create_index('idx_behavior_user_updated', 'user_behavior_signals', ['user_id', 'last_updated_at'])

    # ============================================================
    # 2. ADD ARCHETYPE FIELDS TO USER_GAMIFICATION
    # ============================================================
    op.add_column('user_gamification', sa.Column('archetype', sa.String(50), nullable=True))
    op.add_column('user_gamification', sa.Column('archetype_confidence', sa.Integer(), default=0, nullable=False))
    op.add_column('user_gamification', sa.Column('archetype_scores', sa.Text(), nullable=True))
    op.add_column('user_gamification', sa.Column('archetype_detected_at', sa.DateTime(), nullable=True))
    op.add_column('user_gamification', sa.Column('archetype_version', sa.Integer(), default=1, nullable=False))


def downgrade() -> None:
    """Remove archetype detection system."""

    # Remove archetype fields from UserGamification
    op.drop_column('user_gamification', 'archetype_version')
    op.drop_column('user_gamification', 'archetype_detected_at')
    op.drop_column('user_gamification', 'archetype_scores')
    op.drop_column('user_gamification', 'archetype_confidence')
    op.drop_column('user_gamification', 'archetype')

    # Remove UserBehaviorSignals table and indexes
    op.drop_index('idx_behavior_user_updated', 'user_behavior_signals')
    op.drop_index('idx_behavior_last_interaction', 'user_behavior_signals')
    op.drop_index('idx_behavior_total_interactions', 'user_behavior_signals')
    op.drop_table('user_behavior_signals')
