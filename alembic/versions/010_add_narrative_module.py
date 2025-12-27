"""Add narrative module

Revision ID: 010
Revises: 009
Create Date: 2025-12-26 20:00:00.000000

Changes:
- Add narrative_chapters table for story chapters
- Add narrative_fragments table for story fragments/scenes
- Add fragment_decisions table for user choices
- Add fragment_requirements table for access conditions
- Add user_narrative_progress table for tracking user progress
- Add user_decision_history table for decision tracking and archetype detection
- Add indexes for efficient querying
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agregar módulo de narrativa completo.

    Características:
    - Sistema de capítulos y fragmentos narrativos
    - Decisiones del usuario con ramificaciones
    - Requisitos para acceso (VIP, besitos, arquetipo)
    - Tracking de progreso y detección de arquetipos
    """

    # 1. Crear tabla narrative_chapters
    op.create_table(
        'narrative_chapters',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('chapter_type', sa.String(20), nullable=False, server_default='free'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    # Índice para slug
    op.create_index('ix_narrative_chapters_slug', 'narrative_chapters', ['slug'], unique=True)

    # 2. Crear tabla narrative_fragments
    op.create_table(
        'narrative_fragments',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('fragment_key', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('speaker', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('visual_hint', sa.String(500), nullable=True),
        sa.Column('media_file_id', sa.String(100), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_entry_point', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_ending', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['chapter_id'], ['narrative_chapters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fragment_key'),
    )

    # Índices para narrative_fragments
    op.create_index('ix_narrative_fragments_key', 'narrative_fragments', ['fragment_key'], unique=True)
    op.create_index('idx_chapter_order', 'narrative_fragments', ['chapter_id', 'order'], unique=False)
    op.create_index('idx_entry_points', 'narrative_fragments', ['chapter_id', 'is_entry_point'], unique=False)

    # 3. Crear tabla fragment_decisions
    op.create_table(
        'fragment_decisions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('fragment_id', sa.Integer(), nullable=False),
        sa.Column('button_text', sa.String(100), nullable=False),
        sa.Column('button_emoji', sa.String(10), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('target_fragment_key', sa.String(50), nullable=False),
        sa.Column('besitos_cost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('grants_besitos', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('affects_archetype', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['fragment_id'], ['narrative_fragments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Índice para fragment_decisions
    op.create_index('idx_fragment_order', 'fragment_decisions', ['fragment_id', 'order'], unique=False)

    # 4. Crear tabla fragment_requirements
    op.create_table(
        'fragment_requirements',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('fragment_id', sa.Integer(), nullable=False),
        sa.Column('requirement_type', sa.String(20), nullable=False),
        sa.Column('value', sa.String(100), nullable=False),
        sa.Column('rejection_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['fragment_id'], ['narrative_fragments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Índice para fragment_requirements
    op.create_index('idx_fragment_requirements', 'fragment_requirements', ['fragment_id'], unique=False)

    # 5. Crear tabla user_narrative_progress
    op.create_table(
        'user_narrative_progress',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('current_chapter_id', sa.Integer(), nullable=True),
        sa.Column('current_fragment_key', sa.String(50), nullable=True),
        sa.Column('detected_archetype', sa.String(20), nullable=False, server_default='unknown'),
        sa.Column('archetype_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_decisions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chapters_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_interaction', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['current_chapter_id'], ['narrative_chapters.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Índice único para user_narrative_progress
    op.create_index('idx_user_narrative', 'user_narrative_progress', ['user_id'], unique=True)

    # 6. Crear tabla user_decision_history
    op.create_table(
        'user_decision_history',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('fragment_key', sa.String(50), nullable=False),
        sa.Column('decision_id', sa.Integer(), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('response_time_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['decision_id'], ['fragment_decisions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Índices para user_decision_history
    op.create_index('ix_user_decision_history_user', 'user_decision_history', ['user_id'], unique=False)
    op.create_index('idx_user_decisions', 'user_decision_history', ['user_id', 'fragment_key'], unique=False)


def downgrade() -> None:
    """
    Eliminar módulo de narrativa.

    ADVERTENCIA: Esto eliminará TODO el contenido narrativo y progreso de usuarios.
    """

    # Eliminar índices
    op.drop_index('idx_user_decisions', table_name='user_decision_history')
    op.drop_index('ix_user_decision_history_user', table_name='user_decision_history')
    op.drop_index('idx_user_narrative', table_name='user_narrative_progress')
    op.drop_index('idx_fragment_requirements', table_name='fragment_requirements')
    op.drop_index('idx_fragment_order', table_name='fragment_decisions')
    op.drop_index('idx_entry_points', table_name='narrative_fragments')
    op.drop_index('idx_chapter_order', table_name='narrative_fragments')
    op.drop_index('ix_narrative_fragments_key', table_name='narrative_fragments')
    op.drop_index('ix_narrative_chapters_slug', table_name='narrative_chapters')

    # Eliminar tablas (orden inverso por foreign keys)
    op.drop_table('user_decision_history')
    op.drop_table('user_narrative_progress')
    op.drop_table('fragment_requirements')
    op.drop_table('fragment_decisions')
    op.drop_table('narrative_fragments')
    op.drop_table('narrative_chapters')
