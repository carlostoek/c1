"""
Modelos de base de datos para el módulo de Tienda.

Define los modelos SQLAlchemy 2.0 para:
- ItemCategory: Categorías de productos
- ShopItem: Productos de la tienda
- UserInventory: Inventario del usuario (Mochila)
- UserInventoryItem: Items que posee el usuario
- ItemPurchase: Historial de compras
"""

from typing import Optional, List
from datetime import datetime, UTC

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, DateTime,
    ForeignKey, Index, Text, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Importar Base del sistema core
try:
    from bot.database.base import Base
except ImportError:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass


class ItemCategory(Base):
    """
    Categoría de productos en la tienda.

    Permite organizar los productos por categorías (Artefactos, Paquetes, etc.)
    Cada categoría puede tener un orden de visualización y un emoji.

    Attributes:
        id: ID único de la categoría
        name: Nombre de la categoría (ej: "Artefactos Narrativos")
        slug: Identificador URL-friendly (ej: "artefactos-narrativos")
        description: Descripción de la categoría
        emoji: Emoji representativo
        order: Orden de visualización (menor = primero)
        is_active: Si la categoría está visible
        created_at: Fecha de creación
    """
    __tablename__ = "shop_item_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emoji: Mapped[str] = mapped_column(String(10), default="📦")
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relaciones
    items: Mapped[List["ShopItem"]] = relationship(
        "ShopItem",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index("idx_shop_category_order", "order"),
        Index("idx_shop_category_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ItemCategory(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class ShopItem(Base):
    """
    Producto de la tienda.

    Representa un item que puede comprarse con besitos.
    Puede ser narrativo (desbloquea contenido), digital, consumible o cosmético.

    Attributes:
        id: ID único del producto
        category_id: FK a la categoría
        name: Nombre del producto
        slug: Identificador URL-friendly
        description: Descripción corta
        long_description: Descripción detallada (HTML permitido)
        item_type: Tipo de item (narrative, digital, consumable, cosmetic)
        rarity: Rareza del item (common, uncommon, rare, epic, legendary)
        price_besitos: Precio en besitos
        icon: Emoji o icono del item
        image_file_id: File ID de Telegram para imagen
        metadata: JSON con datos específicos del tipo
        stock: Cantidad disponible (None = ilimitado)
        max_per_user: Máximo que puede tener un usuario (None = ilimitado)
        requires_vip: Si requiere ser VIP para comprar
        is_featured: Si está destacado en la tienda
        is_active: Si está disponible para compra
        order: Orden de visualización
        created_by: ID del admin que lo creó
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shop_item_categories.id"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tipo y rareza
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), default="common")

    # Precio
    price_besitos: Mapped[int] = mapped_column(Integer, nullable=False)

    # Visual
    icon: Mapped[str] = mapped_column(String(10), default="📦")
    image_file_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Metadata específica del tipo (JSON)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Stock y límites
    stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Requisitos
    requires_vip: Mapped[bool] = mapped_column(Boolean, default=False)

    # Estado y ordenamiento
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Auditoría
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relaciones
    category: Mapped["ItemCategory"] = relationship(
        "ItemCategory",
        back_populates="items"
    )
    inventory_items: Mapped[List["UserInventoryItem"]] = relationship(
        "UserInventoryItem",
        back_populates="item",
        cascade="all, delete-orphan"
    )
    purchases: Mapped[List["ItemPurchase"]] = relationship(
        "ItemPurchase",
        back_populates="item",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index("idx_shop_item_category", "category_id"),
        Index("idx_shop_item_type", "item_type"),
        Index("idx_shop_item_active", "is_active"),
        Index("idx_shop_item_featured", "is_featured"),
        Index("idx_shop_item_order", "order"),
        Index("idx_shop_item_price", "price_besitos"),
    )

    def __repr__(self) -> str:
        return f"<ShopItem(id={self.id}, name='{self.name}', price={self.price_besitos})>"

    @property
    def is_in_stock(self) -> bool:
        """Verifica si hay stock disponible."""
        return self.stock is None or self.stock > 0


class UserInventory(Base):
    """
    Inventario del usuario (Mochila).

    Relación 1-to-1 con usuario. Almacena estadísticas generales
    del inventario y preferencias.

    Attributes:
        user_id: ID del usuario (PK)
        total_items: Total de items únicos en el inventario
        total_spent: Total de besitos gastados en la tienda
        favorite_item_id: Item favorito para mostrar en perfil
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    __tablename__ = "user_inventories"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    total_spent: Mapped[int] = mapped_column(Integer, default=0)
    favorite_item_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("shop_items.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relaciones
    items: Mapped[List["UserInventoryItem"]] = relationship(
        "UserInventoryItem",
        back_populates="inventory",
        cascade="all, delete-orphan"
    )
    favorite_item: Mapped[Optional["ShopItem"]] = relationship(
        "ShopItem",
        foreign_keys=[favorite_item_id]
    )

    def __repr__(self) -> str:
        return f"<UserInventory(user_id={self.user_id}, total_items={self.total_items})>"


class UserInventoryItem(Base):
    """
    Item en el inventario del usuario.

    Representa la posesión de un item específico por un usuario.
    Para items consumibles, trackea la cantidad.

    Attributes:
        id: ID único del registro
        user_id: ID del usuario
        item_id: ID del item de la tienda
        quantity: Cantidad poseída (para consumibles)
        obtained_at: Fecha de obtención
        obtained_via: Cómo se obtuvo (purchase, gift, reward)
        is_equipped: Si el item está equipado (para cosméticos)
        is_used: Si el item ha sido usado (para consumibles)
        used_at: Fecha de uso (para consumibles)
    """
    __tablename__ = "user_inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_inventories.user_id", ondelete="CASCADE"),
        nullable=False
    )
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shop_items.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    obtained_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    obtained_via: Mapped[str] = mapped_column(String(50), default="purchase")
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones
    inventory: Mapped["UserInventory"] = relationship(
        "UserInventory",
        back_populates="items"
    )
    item: Mapped["ShopItem"] = relationship(
        "ShopItem",
        back_populates="inventory_items"
    )

    # Índices
    __table_args__ = (
        Index("idx_inventory_user_item", "user_id", "item_id"),
        Index("idx_inventory_item", "item_id"),
        Index("idx_inventory_equipped", "user_id", "is_equipped"),
    )

    def __repr__(self) -> str:
        return f"<UserInventoryItem(user_id={self.user_id}, item_id={self.item_id}, qty={self.quantity})>"


class ItemPurchase(Base):
    """
    Registro de compra de un item.

    Historial de todas las compras realizadas en la tienda.
    Permite auditoría y estadísticas de ventas.

    Attributes:
        id: ID único de la compra
        user_id: ID del usuario que compró
        item_id: ID del item comprado
        quantity: Cantidad comprada
        price_paid: Precio pagado (puede diferir del precio actual)
        status: Estado de la compra (completed, refunded, cancelled)
        purchased_at: Fecha de compra
        refunded_at: Fecha de reembolso (si aplica)
        notes: Notas adicionales
    """
    __tablename__ = "shop_item_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shop_items.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relaciones
    item: Mapped["ShopItem"] = relationship(
        "ShopItem",
        back_populates="purchases"
    )

    # Índices
    __table_args__ = (
        Index("idx_purchase_user", "user_id"),
        Index("idx_purchase_item", "item_id"),
        Index("idx_purchase_date", "purchased_at"),
        Index("idx_purchase_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ItemPurchase(id={self.id}, user={self.user_id}, item={self.item_id}, price={self.price_paid})>"
