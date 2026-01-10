"""add menu system tables

Revision ID: 015
Revises: 014
Create Date: 2026-01-10

Agrega sistema de men\u00fas din\u00e1micos:
- menu_items: Items de men\u00fa configurables por admin
- menu_configs: Configuraci\u00f3n de men\u00fa por rol
- user_interests: Registro de inter\u00e9s de usuarios en productos
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create menu system tables."""

    # Tabla: menu_items
    op.create_table(
        'menu_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_key', sa.String(length=100), nullable=False),
        sa.Column('target_role', sa.String(length=20), nullable=False),
        sa.Column('parent_key', sa.String(length=100), nullable=True),
        sa.Column('button_text', sa.String(length=100), nullable=False),
        sa.Column('button_emoji', sa.String(length=10), nullable=True),
        sa.Column('action_type', sa.String(length=20), nullable=False),
        sa.Column('action_content', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('requires_onboarding', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_key'], ['menu_items.item_key'], ondelete='CASCADE'),
    )

    # Índices para menu_items
    op.create_index('idx_menu_role_active', 'menu_items', ['target_role', 'is_active'])
    op.create_index('idx_menu_parent', 'menu_items', ['parent_key'])
    op.create_index('idx_menu_order', 'menu_items', ['display_order', 'row_number'])
    op.create_index(op.f('ix_menu_items_item_key'), 'menu_items', ['item_key'], unique=True)
    op.create_index(op.f('ix_menu_items_target_role'), 'menu_items', ['target_role'])
    op.create_index(op.f('ix_menu_items_is_active'), 'menu_items', ['is_active'])

    # Tabla: menu_configs
    op.create_table(
        'menu_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('welcome_message', sa.Text(), nullable=False),
        sa.Column('footer_message', sa.Text(), nullable=True),
        sa.Column('show_subscription_info', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Índices para menu_configs
    op.create_index(op.f('ix_menu_configs_role'), 'menu_configs', ['role'], unique=True)

    # Tabla: user_interests
    op.create_table(
        'user_interests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('product_type', sa.String(length=50), nullable=False),
        sa.Column('product_key', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('contacted_at', sa.DateTime(), nullable=True),
        sa.Column('contacted_by', sa.BigInteger(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )

    # Índices para user_interests
    op.create_index('idx_interest_user_status', 'user_interests', ['user_id', 'status'])
    op.create_index('idx_interest_product', 'user_interests', ['product_type', 'product_key'])
    op.create_index('idx_interest_pending', 'user_interests', ['status', 'created_at'])
    op.create_index(op.f('ix_user_interests_user_id'), 'user_interests', ['user_id'])
    op.create_index(op.f('ix_user_interests_product_type'), 'user_interests', ['product_type'])
    op.create_index(op.f('ix_user_interests_status'), 'user_interests', ['status'])
    op.create_index(op.f('ix_user_interests_created_at'), 'user_interests', ['created_at'])


def downgrade() -> None:
    """Drop menu system tables."""
    op.drop_table('user_interests')
    op.drop_table('menu_configs')
    op.drop_table('menu_items')
