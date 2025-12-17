"""Add levels table for gamification system

Revision ID: phase2_001
Revises: 8de8653b2595
Create Date: 2025-12-17 00:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'phase2_001'
down_revision: Union[str, None] = 'phase1_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create levels table."""
    op.create_table(
        'levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('icon', sa.String(length=10), nullable=False),
        sa.Column('min_points', sa.Integer(), nullable=False),
        sa.Column('max_points', sa.Integer(), nullable=True),
        sa.Column('multiplier', sa.Float(), nullable=False),
        sa.Column('perks', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('level', name='uq_levels_level')
    )
    op.create_index(op.f('ix_levels_id'), 'levels', ['id'], unique=False)
    op.create_index(op.f('ix_levels_level'), 'levels', ['level'], unique=True)


def downgrade() -> None:
    """Drop levels table."""
    op.drop_index(op.f('ix_levels_level'), table_name='levels')
    op.drop_index(op.f('ix_levels_id'), table_name='levels')
    op.drop_table('levels')
