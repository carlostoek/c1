"""Add besito_transactions table for audit trail

Revision ID: 006
Revises: 005
Create Date: 2025-12-26 00:00:00.000000

Changes:
- Add besito_transactions table for complete audit trail of besitos operations
- Add composite indexes for efficient querying (user_id + created_at, transaction_type)
- Enable transaction history and balance verification
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agregar tabla de auditoría de transacciones de besitos.

    Características:
    - Registra TODA operación de besitos (grants, deductions, purchases, etc)
    - Incluye balance_after para verificación de integridad
    - Índices compuestos para queries eficientes por usuario y tipo
    """

    # Crear tabla besito_transactions
    op.create_table(
        'besito_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.user_id'],
            ondelete='CASCADE'
        ),
    )

    # Índice compuesto: user_id + created_at (para historial ordenado)
    op.create_index(
        'idx_user_transactions_history',
        'besito_transactions',
        ['user_id', 'created_at'],
        unique=False
    )

    # Índice compuesto: user_id + transaction_type (para filtros)
    op.create_index(
        'idx_user_transaction_type',
        'besito_transactions',
        ['user_id', 'transaction_type'],
        unique=False
    )

    # Índice compuesto: reference_id + transaction_type (para rastrear origen)
    op.create_index(
        'idx_reference_transaction',
        'besito_transactions',
        ['reference_id', 'transaction_type'],
        unique=False
    )


def downgrade() -> None:
    """
    Eliminar tabla de transacciones de besitos.

    ADVERTENCIA: Esto eliminará TODO el historial de transacciones.
    """

    # Eliminar índices primero
    op.drop_index('idx_reference_transaction', table_name='besito_transactions')
    op.drop_index('idx_user_transaction_type', table_name='besito_transactions')
    op.drop_index('idx_user_transactions_history', table_name='besito_transactions')

    # Eliminar tabla
    op.drop_table('besito_transactions')
