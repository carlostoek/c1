"""add immersive narrative system

Revision ID: 013
Revises: 012
Create Date: 2025-12-28

Sistema narrativo inmersivo con:
- Variantes de fragmentos por contexto
- Tracking de visitas y engagement
- Sistema de cooldowns
- Desafíos interactivos
- Ventanas de disponibilidad temporal
- Tracking de capítulos completados
- Límites diarios de narrativa
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for immersive narrative system."""

    # ============================================================
    # 1. FRAGMENT VARIANTS - Contenido dinámico por contexto
    # ============================================================
    op.create_table(
        'fragment_variants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fragment_key', sa.String(50), sa.ForeignKey('narrative_fragments.fragment_key'), nullable=False),
        sa.Column('variant_key', sa.String(50), nullable=False),
        sa.Column('priority', sa.Integer(), default=0, nullable=False),
        sa.Column('condition_type', sa.String(30), nullable=False),
        sa.Column('condition_value', sa.String(100), nullable=False),
        sa.Column('content_override', sa.Text(), nullable=True),
        sa.Column('speaker_override', sa.String(50), nullable=True),
        sa.Column('visual_hint_override', sa.String(500), nullable=True),
        sa.Column('media_file_id_override', sa.String(100), nullable=True),
        sa.Column('additional_decisions', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_variant_fragment_priority', 'fragment_variants', ['fragment_key', 'priority'])
    op.create_index('idx_variant_key', 'fragment_variants', ['fragment_key', 'variant_key'], unique=True)

    # ============================================================
    # 2. USER FRAGMENT VISITS - Tracking de visitas y tiempo
    # ============================================================
    op.create_table(
        'user_fragment_visits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('fragment_key', sa.String(50), nullable=False),
        sa.Column('visit_count', sa.Integer(), default=1, nullable=False),
        sa.Column('first_visit', sa.DateTime(), nullable=False),
        sa.Column('last_visit', sa.DateTime(), nullable=False),
        sa.Column('total_time_seconds', sa.Integer(), default=0, nullable=False),
        sa.Column('reading_started_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_user_fragment_visit', 'user_fragment_visits', ['user_id', 'fragment_key'], unique=True)
    op.create_index('idx_visits_user', 'user_fragment_visits', ['user_id'])
    op.create_index('idx_visits_fragment', 'user_fragment_visits', ['fragment_key'])

    # ============================================================
    # 3. NARRATIVE COOLDOWNS - Tiempos de espera
    # ============================================================
    op.create_table(
        'narrative_cooldowns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('cooldown_type', sa.String(20), nullable=False),
        sa.Column('target_key', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('narrative_message', sa.Text(), nullable=True),
    )
    op.create_index('idx_cooldown_user_type', 'narrative_cooldowns', ['user_id', 'cooldown_type', 'target_key'])
    op.create_index('idx_cooldown_expires', 'narrative_cooldowns', ['user_id', 'expires_at'])

    # ============================================================
    # 4. FRAGMENT CHALLENGES - Desafíos/Acertijos
    # ============================================================
    op.create_table(
        'fragment_challenges',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fragment_key', sa.String(50), sa.ForeignKey('narrative_fragments.fragment_key'), nullable=False),
        sa.Column('challenge_type', sa.String(20), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('question_image_file_id', sa.String(100), nullable=True),
        sa.Column('correct_answers', sa.Text(), nullable=False),
        sa.Column('hints', sa.Text(), nullable=True),
        sa.Column('attempts_allowed', sa.Integer(), default=3, nullable=False),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True),
        sa.Column('failure_redirect_key', sa.String(50), nullable=True),
        sa.Column('failure_message', sa.Text(), nullable=True),
        sa.Column('success_clue_slug', sa.String(100), nullable=True),
        sa.Column('success_besitos', sa.Integer(), default=0, nullable=False),
        sa.Column('success_message', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
    )
    op.create_index('idx_challenge_fragment', 'fragment_challenges', ['fragment_key'])

    # ============================================================
    # 5. USER CHALLENGE ATTEMPTS - Intentos de desafíos
    # ============================================================
    op.create_table(
        'user_challenge_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), sa.ForeignKey('fragment_challenges.id'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), default=1, nullable=False),
        sa.Column('answer_given', sa.String(200), nullable=True),
        sa.Column('is_correct', sa.Boolean(), default=False, nullable=False),
        sa.Column('hints_used', sa.Integer(), default=0, nullable=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
        sa.Column('response_time_seconds', sa.Integer(), nullable=True),
    )
    op.create_index('idx_challenge_attempts', 'user_challenge_attempts', ['user_id', 'challenge_id'])

    # ============================================================
    # 6. FRAGMENT TIME WINDOWS - Disponibilidad temporal
    # ============================================================
    op.create_table(
        'fragment_time_windows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fragment_key', sa.String(50), sa.ForeignKey('narrative_fragments.fragment_key'), nullable=False),
        sa.Column('available_hours', sa.Text(), nullable=True),
        sa.Column('available_days', sa.Text(), nullable=True),
        sa.Column('special_dates', sa.Text(), nullable=True),
        sa.Column('special_dates_inclusive', sa.Boolean(), default=True, nullable=False),
        sa.Column('unavailable_message', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
    )
    op.create_index('idx_time_window_fragment', 'fragment_time_windows', ['fragment_key'])

    # ============================================================
    # 7. CHAPTER COMPLETIONS - Capítulos completados
    # ============================================================
    op.create_table(
        'chapter_completions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('chapter_slug', sa.String(50), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.Column('fragments_visited', sa.Integer(), default=0, nullable=False),
        sa.Column('decisions_made', sa.Integer(), default=0, nullable=False),
        sa.Column('total_time_seconds', sa.Integer(), default=0, nullable=False),
        sa.Column('clues_found', sa.Integer(), default=0, nullable=False),
        sa.Column('chapter_archetype', sa.String(20), nullable=True),
    )
    op.create_index('idx_chapter_completion', 'chapter_completions', ['user_id', 'chapter_slug'], unique=True)
    op.create_index('idx_chapter_user', 'chapter_completions', ['user_id'])

    # ============================================================
    # 8. DAILY NARRATIVE LIMITS - Límites diarios
    # ============================================================
    op.create_table(
        'daily_narrative_limits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), unique=True, nullable=False),
        sa.Column('limit_date', sa.DateTime(), nullable=False),
        sa.Column('fragments_viewed', sa.Integer(), default=0, nullable=False),
        sa.Column('decisions_made', sa.Integer(), default=0, nullable=False),
        sa.Column('challenges_attempted', sa.Integer(), default=0, nullable=False),
        sa.Column('max_fragments_per_day', sa.Integer(), nullable=True),
        sa.Column('max_decisions_per_day', sa.Integer(), nullable=True),
    )
    op.create_index('idx_daily_limit_user', 'daily_narrative_limits', ['user_id'])


def downgrade() -> None:
    """Remove immersive narrative tables."""
    op.drop_table('daily_narrative_limits')
    op.drop_table('chapter_completions')
    op.drop_table('fragment_time_windows')
    op.drop_table('user_challenge_attempts')
    op.drop_table('fragment_challenges')
    op.drop_table('narrative_cooldowns')
    op.drop_table('user_fragment_visits')
    op.drop_table('fragment_variants')
