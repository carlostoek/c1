"""Add daily gift system

Revision ID: 008
Revises: 007
Create Date: 2025-12-26 12:00:00.000000

Changes:
- Add daily_gift_claims table for tracking user daily gift claims
- Add daily_gift_enabled and daily_gift_besitos to gamification_config
- Add indexes for efficient querying of claims and streaks
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agregar sistema de regalo diario.

    Características:
    - Tabla daily_gift_claims para trackear reclamaciones
    - Campos de configuración en gamification_config
    - Soporte para rachas de días consecutivos
    - Índices optimizados para queries eficientes
    """

    # 1. Agregar campos de configuración a gamification_config
    op.add_column(
        'gamification_config',
        sa.Column('daily_gift_enabled', sa.Boolean(), nullable=False, server_default='1')
    )
    op.add_column(
        'gamification_config',
        sa.Column('daily_gift_besitos', sa.Integer(), nullable=False, server_default='10')
    )

    # 2. Crear tabla daily_gift_claims
    op.create_table(
        'daily_gift_claims',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('last_claim_date', sa.DateTime(), nullable=True),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_claims', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id'),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.user_id'],
            ondelete='CASCADE'
        ),
    )

    # 3. Crear índices para optimización
    op.create_index(
        'idx_daily_gift_last_claim',
        'daily_gift_claims',
        ['last_claim_date'],
        unique=False
    )

    op.create_index(
        'idx_daily_gift_streak',
        'daily_gift_claims',
        ['current_streak'],
        unique=False
    )


def downgrade() -> None:
    """
    Eliminar sistema de regalo diario.

    ADVERTENCIA: Esto eliminará TODO el historial de reclamaciones diarias.
    """

    # Eliminar índices
    op.drop_index('idx_daily_gift_streak', table_name='daily_gift_claims')
    op.drop_index('idx_daily_gift_last_claim', table_name='daily_gift_claims')

    # Eliminar tabla
    op.drop_table('daily_gift_claims')

    # Eliminar campos de configuración
    op.drop_column('gamification_config', 'daily_gift_besitos')
    op.drop_column('gamification_config', 'daily_gift_enabled')
