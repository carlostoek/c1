"""Add rewards and user_rewards tables

Revision ID: be059c4027eb
Revises: phase3_001
Create Date: 2025-12-17 16:57:50.911426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be059c4027eb'
down_revision: Union[str, None] = 'phase3_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rewards table
    op.create_table(
        'rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('icon', sa.String(length=10), nullable=False),
        sa.Column('reward_type', sa.String(length=50), nullable=False),
        sa.Column('cost', sa.Integer(), nullable=False),
        sa.Column('limit_type', sa.String(length=50), nullable=False),
        sa.Column('required_level', sa.Integer(), nullable=False),
        sa.Column('is_vip_only', sa.Boolean(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=True),
        sa.Column('content_id', sa.String(length=100), nullable=True),
        sa.Column('points_amount', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=True),
        sa.Column('reward_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_rewards_cost', 'cost'),
        sa.Index('ix_rewards_is_active', 'is_active'),
        sa.Index('ix_rewards_limit_type', 'limit_type'),
        sa.Index('ix_rewards_name', 'name'),
        sa.Index('ix_rewards_reward_type', 'reward_type'),
    )

    # Create user_rewards table
    op.create_table(
        'user_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('reward_id', sa.Integer(), nullable=False),
        sa.Column('cost_paid', sa.Integer(), nullable=False),
        sa.Column('redeemed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_delivered', sa.Boolean(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_user_reward', 'user_id', 'reward_id'),
        sa.Index('idx_user_redeemed', 'user_id', 'redeemed_at'),
        sa.Index('ix_user_rewards_reward_id', 'reward_id'),
        sa.Index('ix_user_rewards_user_id', 'user_id'),
    )


def downgrade() -> None:
    op.drop_table('user_rewards')
    op.drop_table('rewards')
