"""add_gamification_config_tables

Revision ID: 1b2279bda22d
Revises: 8de8653b2595
Create Date: 2025-12-18 08:41:27.715477

Crea las tablas de configuración de gamificación:
- action_configs: Acciones que otorgan puntos
- level_configs: Niveles/rangos del sistema
- badge_configs: Badges disponibles
- reward_configs: Recompensas configurables
- mission_configs: Misiones del sistema
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1b2279bda22d'
down_revision: Union[str, None] = '8de8653b2595'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === ACTION_CONFIGS ===
    op.create_table(
        'action_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action_key', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('points_amount', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_action_configs_action_key', 'action_configs', ['action_key'], unique=True)

    # === LEVEL_CONFIGS ===
    op.create_table(
        'level_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('min_points', sa.Integer(), nullable=False),
        sa.Column('max_points', sa.Integer(), nullable=True),
        sa.Column('multiplier', sa.Float(), nullable=False),
        sa.Column('icon', sa.String(length=10), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_level_order', 'level_configs', ['order'], unique=False)
    op.create_index('idx_level_points', 'level_configs', ['min_points'], unique=False)

    # === BADGE_CONFIGS ===
    op.create_table(
        'badge_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('badge_key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('icon', sa.String(length=10), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False),
        sa.Column('requirement_value', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_badge_configs_badge_key', 'badge_configs', ['badge_key'], unique=True)

    # === REWARD_CONFIGS ===
    op.create_table(
        'reward_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('reward_type', sa.String(length=20), nullable=False),
        sa.Column('points_amount', sa.Integer(), nullable=True),
        sa.Column('badge_id', sa.Integer(), nullable=True),
        sa.Column('custom_data', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['badge_id'], ['badge_configs.id'], ondelete='SET NULL')
    )

    # === MISSION_CONFIGS ===
    op.create_table(
        'mission_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('mission_type', sa.String(length=20), nullable=False),
        sa.Column('target_action', sa.String(length=50), nullable=True),
        sa.Column('target_value', sa.Integer(), nullable=False),
        sa.Column('reward_id', sa.Integer(), nullable=True),
        sa.Column('time_limit_hours', sa.Integer(), nullable=True),
        sa.Column('is_repeatable', sa.Boolean(), nullable=False),
        sa.Column('cooldown_hours', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['reward_id'], ['reward_configs.id'], ondelete='SET NULL')
    )
    op.create_index('idx_mission_type', 'mission_configs', ['mission_type'], unique=False)
    op.create_index('idx_mission_active', 'mission_configs', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_mission_active', table_name='mission_configs')
    op.drop_index('idx_mission_type', table_name='mission_configs')
    op.drop_table('mission_configs')
    op.drop_table('reward_configs')
    op.drop_index('idx_level_points', table_name='level_configs')
    op.drop_index('idx_level_order', table_name='level_configs')
    op.drop_table('level_configs')
    op.drop_index('ix_badge_configs_badge_key', table_name='badge_configs')
    op.drop_table('badge_configs')
    op.drop_index('ix_action_configs_action_key', table_name='action_configs')
    op.drop_table('action_configs')
