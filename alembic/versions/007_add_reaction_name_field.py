"""add reaction name field

Revision ID: 007
Revises: 006
Create Date: 2025-12-26 04:50:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add name column to reactions table."""
    # Agregar columna name (nullable temporalmente)
    op.add_column('reactions', sa.Column('name', sa.String(length=50), nullable=True))

    # Actualizar registros existentes con nombre basado en emoji
    # Esto es para datos existentes; nuevos registros requerirán name
    op.execute("""
        UPDATE reactions
        SET name = CASE emoji
            WHEN '❤️' THEN 'Corazón'
            WHEN '🔥' THEN 'Fuego'
            WHEN '👍' THEN 'Me gusta'
            WHEN '💰' THEN 'Dinero'
            WHEN '⭐' THEN 'Estrella'
            WHEN '🎉' THEN 'Celebración'
            WHEN '😍' THEN 'Amor'
            WHEN '💪' THEN 'Fuerza'
            WHEN '🚀' THEN 'Cohete'
            WHEN '💎' THEN 'Diamante'
            ELSE 'Reacción'
        END
        WHERE name IS NULL
    """)

    # Hacer columna NOT NULL después de rellenar datos existentes
    op.alter_column('reactions', 'name', nullable=False)


def downgrade() -> None:
    """Remove name column from reactions table."""
    op.drop_column('reactions', 'name')
