"""Add menu configuration system

Revision ID: 009
Revises: 008
Create Date: 2025-12-26 18:00:00.000000

Changes:
- Add menu_items table for configurable menu buttons
- Add menu_configs table for menu configuration by role
- Add indexes for efficient querying by role and active status
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agregar sistema de configuración dinámica de menús.

    Características:
    - Tabla menu_items para botones configurables
    - Tabla menu_configs para configuración por rol
    - Soporte para roles VIP/FREE/ALL
    - Índices optimizados para queries frecuentes
    """

    # 1. Crear tabla menu_items
    op.create_table(
        'menu_items',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('item_key', sa.String(50), nullable=False, unique=True),
        sa.Column('target_role', sa.String(20), nullable=False, server_default='all'),
        sa.Column('button_text', sa.String(100), nullable=False),
        sa.Column('button_emoji', sa.String(10), nullable=True),
        sa.Column('action_type', sa.String(20), nullable=False, server_default='info'),
        sa.Column('action_content', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('row_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_key'),
    )

    # 2. Crear índices para menu_items
    op.create_index(
        'ix_menu_items_role_active',
        'menu_items',
        ['target_role', 'is_active'],
        unique=False
    )

    op.create_index(
        'ix_menu_items_order',
        'menu_items',
        ['display_order', 'row_number'],
        unique=False
    )

    # 3. Crear tabla menu_configs
    op.create_table(
        'menu_configs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('role', sa.String(20), nullable=False, unique=True),
        sa.Column('welcome_message', sa.Text(), nullable=False, server_default='Bienvenido, selecciona una opción:'),
        sa.Column('footer_message', sa.Text(), nullable=True),
        sa.Column('show_subscription_info', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role'),
    )


def downgrade() -> None:
    """
    Eliminar sistema de configuración de menús.

    ADVERTENCIA: Esto eliminará TODA la configuración de menús personalizada.
    """

    # Eliminar índices de menu_items
    op.drop_index('ix_menu_items_order', table_name='menu_items')
    op.drop_index('ix_menu_items_role_active', table_name='menu_items')

    # Eliminar tablas
    op.drop_table('menu_configs')
    op.drop_table('menu_items')
