"""Add badges system with BadgeRarity

Revision ID: phase3_001
Revises: phase2_001
Create Date: 2025-12-17 11:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'phase3_001'
down_revision: Union[str, None] = 'phase2_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create badges table
    op.create_table('badges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('emoji', sa.String(length=10), nullable=False),
    sa.Column('rarity', sa.Enum('COMMON', 'RARE', 'EPIC', 'LEGENDARY', name='badgerarity'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_secret', sa.Boolean(), nullable=False),
    sa.Column('badge_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_badges_id'), 'badges', ['id'], unique=False)
    op.create_index(op.f('ix_badges_is_active'), 'badges', ['is_active'], unique=False)
    op.create_index(op.f('ix_badges_name'), 'badges', ['name'], unique=True)
    op.create_index(op.f('ix_badges_rarity'), 'badges', ['rarity'], unique=False)

    # Create user_badges table with new schema
    op.create_table('user_badges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('badge_id', sa.Integer(), nullable=False),
    sa.Column('earned_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_badge', 'user_badges', ['user_id', 'badge_id'], unique=True)
    op.create_index('idx_user_earned', 'user_badges', ['user_id', 'earned_at'], unique=False)
    op.create_index(op.f('ix_user_badges_badge_id'), 'user_badges', ['badge_id'], unique=False)
    op.create_index(op.f('ix_user_badges_id'), 'user_badges', ['id'], unique=False)
    op.create_index(op.f('ix_user_badges_user_id'), 'user_badges', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop user_badges table and indices
    op.drop_index(op.f('ix_user_badges_user_id'), table_name='user_badges')
    op.drop_index(op.f('ix_user_badges_id'), table_name='user_badges')
    op.drop_index(op.f('ix_user_badges_badge_id'), table_name='user_badges')
    op.drop_index('idx_user_earned', table_name='user_badges')
    op.drop_index('idx_user_badge', table_name='user_badges')
    op.drop_table('user_badges')

    # Drop badges table and indices
    op.drop_index(op.f('ix_badges_rarity'), table_name='badges')
    op.drop_index(op.f('ix_badges_name'), table_name='badges')
    op.drop_index(op.f('ix_badges_is_active'), table_name='badges')
    op.drop_index(op.f('ix_badges_id'), table_name='badges')
    op.drop_table('badges')
