"""rename metadata to extra_metadata

Revision ID: 015
Revises: 014
Create Date: 2025-12-28

Renombra la columna 'metadata' a 'extra_metadata' en narrative_fragments
para evitar conflictos con el atributo reserved de SQLAlchemy.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename metadata column to extra_metadata."""

    # SQLite no soporta ALTER COLUMN directamente, usamos batch operation
    with op.batch_alter_table('narrative_fragments', schema=None) as batch_op:
        batch_op.alter_column(
            'metadata',
            new_column_name='extra_metadata',
            existing_type=sa.JSON(),
            nullable=True
        )


def downgrade() -> None:
    """Revert extra_metadata back to metadata."""

    with op.batch_alter_table('narrative_fragments', schema=None) as batch_op:
        batch_op.alter_column(
            'extra_metadata',
            new_column_name='metadata',
            existing_type=sa.JSON(),
            nullable=True
        )
