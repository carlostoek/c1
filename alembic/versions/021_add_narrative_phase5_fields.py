"""add narrative phase5 fields

Revision ID: 021_add_narrative_phase5_fields
Revises: 020_add_conversion_tracking_tables
Create Date: 2025-12-30

Extiende modelos de narrativa con campos de Fase 5:
- NarrativeChapter: level, requisitos, recompensas
- NarrativeFragment: delays, condiciones, navegación
- FragmentDecision: subtext, favor_change, flags
- UserNarrativeProgress: niveles, flags, misiones, timestamps
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '021_add_narrative_phase5_fields'
down_revision: Union[str, None] = '020_add_conversion_tracking_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agregar campos de Fase 5 a modelos narrativos."""

    # NarrativeChapter: Sistema de niveles y requisitos
    with op.batch_alter_table('narrative_chapters', schema=None) as batch_op:
        batch_op.add_column(sa.Column('level', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('requires_level', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('requires_chapter_completed', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('requires_archetype', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('favor_reward', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('badge_reward', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('item_reward', sa.String(length=50), nullable=True))
        batch_op.create_foreign_key('fk_requires_chapter', 'narrative_chapters', ['requires_chapter_completed'], ['id'])

    # NarrativeFragment: Navegación y condiciones dinámicas
    with op.batch_alter_table('narrative_fragments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delay_seconds', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_decision_point', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('next_fragment_key', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('condition_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('condition_value', sa.String(length=100), nullable=True))

    # FragmentDecision: Sistema de flags y favores
    with op.batch_alter_table('fragment_decisions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('subtext', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('favor_change', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('sets_flag', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('requires_flag', sa.String(length=50), nullable=True))

    # UserNarrativeProgress: Niveles, flags, misiones y timestamps
    with op.batch_alter_table('user_narrative_progress', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_level', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('chapters_completed_list', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('fragments_seen', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('decisions_made', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('narrative_flags', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('active_mission_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('mission_started_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('mission_data', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('level_1_completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('level_2_completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('level_3_completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('level_4_completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('level_5_completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('level_6_completed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remover campos de Fase 5 de modelos narrativos."""

    # UserNarrativeProgress: Remover campos de Fase 5
    with op.batch_alter_table('user_narrative_progress', schema=None) as batch_op:
        batch_op.drop_column('level_6_completed_at')
        batch_op.drop_column('level_5_completed_at')
        batch_op.drop_column('level_4_completed_at')
        batch_op.drop_column('level_3_completed_at')
        batch_op.drop_column('level_2_completed_at')
        batch_op.drop_column('level_1_completed_at')
        batch_op.drop_column('mission_data')
        batch_op.drop_column('mission_started_at')
        batch_op.drop_column('active_mission_id')
        batch_op.drop_column('narrative_flags')
        batch_op.drop_column('decisions_made')
        batch_op.drop_column('fragments_seen')
        batch_op.drop_column('chapters_completed_list')
        batch_op.drop_column('current_level')

    # FragmentDecision: Remover campos de Fase 5
    with op.batch_alter_table('fragment_decisions', schema=None) as batch_op:
        batch_op.drop_column('requires_flag')
        batch_op.drop_column('sets_flag')
        batch_op.drop_column('favor_change')
        batch_op.drop_column('subtext')

    # NarrativeFragment: Remover campos de Fase 5
    with op.batch_alter_table('narrative_fragments', schema=None) as batch_op:
        batch_op.drop_column('condition_value')
        batch_op.drop_column('condition_type')
        batch_op.drop_column('next_fragment_key')
        batch_op.drop_column('is_decision_point')
        batch_op.drop_column('delay_seconds')

    # NarrativeChapter: Remover campos de Fase 5
    with op.batch_alter_table('narrative_chapters', schema=None) as batch_op:
        batch_op.drop_constraint('fk_requires_chapter', type_='foreignkey')
        batch_op.drop_column('item_reward')
        batch_op.drop_column('badge_reward')
        batch_op.drop_column('favor_reward')
        batch_op.drop_column('estimated_duration_minutes')
        batch_op.drop_column('requires_archetype')
        batch_op.drop_column('requires_chapter_completed')
        batch_op.drop_column('requires_level')
        batch_op.drop_column('level')
