"""Add besito transaction table with audit trail.

Revision ID: 005_add_besito_transaction
Revises: 004_add_gamification_module
Create Date: 2025-12-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '005_add_besito_transaction'
down_revision = '004_add_gamification_module'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Crea la tabla de transacciones de besitos para auditoría.

    Campos:
    - id: PK
    - user_id: FK → UserGamification.user_id
    - amount: Puede ser positivo (ganancias) o negativo (gastos)
    - transaction_type: Tipo de transacción (enum)
    - description: Descripción de la operación
    - reference_id: ID de referencia (mission_id, reward_id, etc)
    - balance_after: Balance después de esta transacción
    - created_at: Timestamp UTC

    Índices:
    - (user_id, created_at DESC) - para historial de usuario
    - (user_id, transaction_type) - para filtrar por tipo
    - (reference_id, transaction_type) - para buscar por referencia
    """

    # Crear tabla besito_transactions
    op.create_table(
        'besito_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['user_gamification.user_id'], 
            name='fk_besito_transactions_user_id', 
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices compuestos
    op.create_index(
        'ix_besito_transactions_user_created', 
        'besito_transactions', 
        ['user_id', 'created_at'], 
        unique=False
    )
    op.create_index(
        'ix_besito_transactions_user_type', 
        'besito_transactions', 
        ['user_id', 'transaction_type'], 
        unique=False
    )
    op.create_index(
        'ix_besito_transactions_ref_type', 
        'besito_transactions', 
        ['reference_id', 'transaction_type'], 
        unique=False
    )
    op.create_index(
        'ix_besito_transactions_created_at', 
        'besito_transactions', 
        ['created_at'], 
        unique=False
    )


def downgrade() -> None:
    """
    Elimina la tabla de transacciones de besitos.

    El orden de operación es inverso al de upgrade.
    """
    # Eliminar índices
    op.drop_index('ix_besito_transactions_created_at', table_name='besito_transactions')
    op.drop_index('ix_besito_transactions_ref_type', table_name='besito_transactions')
    op.drop_index('ix_besito_transactions_user_type', table_name='besito_transactions')
    op.drop_index('ix_besito_transactions_user_created', table_name='besito_transactions')

    # Eliminar tabla
    op.drop_table('besito_transactions')