"""Add missions and user_missions tables

Revision ID: 252ed237c98b
Revises: be059c4027eb
Create Date: 2025-12-17 17:06:14.201854

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '252ed237c98b'
down_revision: Union[str, None] = 'be059c4027eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create missions table
    op.create_table(
        'missions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('icon', sa.String(length=10), nullable=False),
        sa.Column('mission_type', sa.String(length=50), nullable=False),
        sa.Column('objective_type', sa.String(length=50), nullable=False),
        sa.Column('objective_value', sa.Integer(), nullable=False),
        sa.Column('reward_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('required_level', sa.Integer(), nullable=False),
        sa.Column('is_vip_only', sa.Boolean(), nullable=False),
        sa.Column('mission_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_missions_is_active', 'is_active'),
        sa.Index('ix_missions_mission_type', 'mission_type'),
        sa.Index('ix_missions_name', 'name'),
        sa.Index('ix_missions_objective_type', 'objective_type'),
    )

    # Create user_missions table
    op.create_table(
        'user_missions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('mission_id', sa.Integer(), nullable=False),
        sa.Column('current_progress', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_user_active', 'user_id', 'is_completed'),
        sa.Index('idx_user_mission', 'user_id', 'mission_id'),
        sa.Index('ix_user_missions_is_completed', 'is_completed'),
        sa.Index('ix_user_missions_mission_id', 'mission_id'),
        sa.Index('ix_user_missions_user_id', 'user_id'),
    )


def downgrade() -> None:
    op.drop_table('user_missions')
    op.drop_table('missions')
