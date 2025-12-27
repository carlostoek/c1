"""Add shop module

Revision ID: 011
Revises: 010
Create Date: 2025-12-27 00:00:00.000000

Changes:
- Add shop_item_categories table for product categories
- Add shop_items table for products
- Add user_inventories table for user inventories (Mochila)
- Add user_inventory_items table for items owned by users
- Add shop_item_purchases table for purchase history
- Add RequirementType.ITEM to narrative requirements (enum extension)
- Add indexes for efficient querying
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agregar módulo de tienda completo.

    Tablas:
    - shop_item_categories: Categorías de productos
    - shop_items: Productos de la tienda
    - user_inventories: Inventario del usuario
    - user_inventory_items: Items que posee el usuario
    - shop_item_purchases: Historial de compras
    """

    # ========================================
    # 1. SHOP_ITEM_CATEGORIES
    # ========================================
    op.create_table(
        'shop_item_categories',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('emoji', sa.String(10), nullable=False, server_default='📦'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index(
        'idx_shop_category_order',
        'shop_item_categories',
        ['order']
    )
    op.create_index(
        'idx_shop_category_active',
        'shop_item_categories',
        ['is_active']
    )

    # ========================================
    # 2. SHOP_ITEMS
    # ========================================
    op.create_table(
        'shop_items',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('shop_item_categories.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('long_description', sa.Text(), nullable=True),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('rarity', sa.String(20), nullable=False, server_default='common'),
        sa.Column('price_besitos', sa.Integer(), nullable=False),
        sa.Column('icon', sa.String(10), nullable=False, server_default='📦'),
        sa.Column('image_file_id', sa.String(200), nullable=True),
        sa.Column('item_metadata', sa.Text(), nullable=True),
        sa.Column('stock', sa.Integer(), nullable=True),
        sa.Column('max_per_user', sa.Integer(), nullable=True),
        sa.Column('requires_vip', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('idx_shop_item_category', 'shop_items', ['category_id'])
    op.create_index('idx_shop_item_type', 'shop_items', ['item_type'])
    op.create_index('idx_shop_item_active', 'shop_items', ['is_active'])
    op.create_index('idx_shop_item_featured', 'shop_items', ['is_featured'])
    op.create_index('idx_shop_item_order', 'shop_items', ['order'])
    op.create_index('idx_shop_item_price', 'shop_items', ['price_besitos'])

    # ========================================
    # 3. USER_INVENTORIES
    # ========================================
    op.create_table(
        'user_inventories',
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, primary_key=True),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_spent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('favorite_item_id', sa.Integer(), sa.ForeignKey('shop_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ========================================
    # 4. USER_INVENTORY_ITEMS
    # ========================================
    op.create_table(
        'user_inventory_items',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('user_inventories.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('shop_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('obtained_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('obtained_via', sa.String(50), nullable=False, server_default='purchase'),
        sa.Column('is_equipped', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('used_at', sa.DateTime(), nullable=True),
    )

    op.create_index('idx_inventory_user_item', 'user_inventory_items', ['user_id', 'item_id'])
    op.create_index('idx_inventory_item', 'user_inventory_items', ['item_id'])
    op.create_index('idx_inventory_equipped', 'user_inventory_items', ['user_id', 'is_equipped'])

    # ========================================
    # 5. SHOP_ITEM_PURCHASES
    # ========================================
    op.create_table(
        'shop_item_purchases',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('shop_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price_paid', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='completed'),
        sa.Column('purchased_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
    )

    op.create_index('idx_purchase_user', 'shop_item_purchases', ['user_id'])
    op.create_index('idx_purchase_item', 'shop_item_purchases', ['item_id'])
    op.create_index('idx_purchase_date', 'shop_item_purchases', ['purchased_at'])
    op.create_index('idx_purchase_status', 'shop_item_purchases', ['status'])

    # ========================================
    # 6. SEED DATA: Default Categories
    # ========================================
    op.execute("""
        INSERT INTO shop_item_categories (name, slug, description, emoji, "order", is_active)
        VALUES
            ('Artefactos Narrativos', 'artefactos-narrativos', 'Objetos místicos que desbloquean fragmentos de la historia', '📜', 1, 1),
            ('Contenido Digital', 'contenido-digital', 'Paquetes de contenido exclusivo y material adicional', '💾', 2, 1),
            ('Consumibles', 'consumibles', 'Items de uso único con efectos especiales', '🧪', 3, 1),
            ('Cosméticos', 'cosmeticos', 'Personaliza tu perfil con títulos y badges únicos', '✨', 4, 1)
    """)


def downgrade() -> None:
    """
    Eliminar módulo de tienda.
    """
    # Eliminar tablas en orden inverso
    op.drop_table('shop_item_purchases')
    op.drop_table('user_inventory_items')
    op.drop_table('user_inventories')
    op.drop_table('shop_items')
    op.drop_table('shop_item_categories')
