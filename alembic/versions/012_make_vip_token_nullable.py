"""make vip token_id nullable

Revision ID: 012
Revises: 011_add_shop_module
Create Date: 2025-12-27

Permite otorgar VIP sin token asociado (para recompensas de gamificación).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make token_id nullable in vip_subscribers."""
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # For production, you might want to use a different approach
    # Here we use batch_alter_table which handles SQLite limitations

    with op.batch_alter_table('vip_subscribers') as batch_op:
        batch_op.alter_column(
            'token_id',
            existing_type=sa.Integer(),
            nullable=True
        )


def downgrade() -> None:
    """Revert token_id to NOT NULL."""
    with op.batch_alter_table('vip_subscribers') as batch_op:
        batch_op.alter_column(
            'token_id',
            existing_type=sa.Integer(),
            nullable=False
        )
