"""Create point_transactions table (Phase 1.2)

Revision ID: phase1_002
Revises: phase1_001
Create Date: 2025-12-16 05:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'phase1_002'
down_revision: Union[str, None] = 'phase1_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create point_transactions table
    op.create_table('point_transactions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('reason', sa.String(255), nullable=False),
        sa.Column('transaction_metadata', sa.JSON(), nullable=True),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes
    op.create_index(op.f('ix_point_transactions_id'), 'point_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_point_transactions_user_id'), 'point_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_point_transactions_transaction_type'), 'point_transactions', ['transaction_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_point_transactions_transaction_type'), table_name='point_transactions')
    op.drop_index(op.f('ix_point_transactions_user_id'), table_name='point_transactions')
    op.drop_index(op.f('ix_point_transactions_id'), table_name='point_transactions')
    op.drop_table('point_transactions')
