"""
Modelos de menús dinámicos y sistema de interés de usuarios.

Este módulo define los modelos para:
- MenuItem: Items de menú configurables por admin
- MenuConfig: Configuración global por rol
- UserInterest: Registro de interés de usuarios en productos
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from bot.database.base import Base


class MenuItem(Base):
    """
    Item de menú configurable por administradores.

    Permite crear menús dinámicos según rol (VIP/FREE) con soporte para:
    - Submenús (parent_key)
    - Diferentes tipos de acción (callback, url, submenu, info, blocked)
    - Restricción por onboarding
    - Ordenamiento personalizado
    """
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)
    item_key = Column(String(100), unique=True, nullable=False, index=True)

    # Rol objetivo
    target_role = Column(
        String(20),
        nullable=False,
        default="all",
        index=True
    )  # 'vip', 'free', 'all', 'admin'

    # Jerarquía
    parent_key = Column(
        String(100),
        ForeignKey("menu_items.item_key", ondelete="CASCADE"),
        nullable=True,
        index=True
    )  # Para submenús

    # Visualización
    button_text = Column(String(100), nullable=False)
    button_emoji = Column(String(10), nullable=True)

    # Acción
    action_type = Column(
        String(20),
        nullable=False
    )  # 'callback', 'url', 'submenu', 'info', 'blocked'

    action_content = Column(Text, nullable=False)  # Callback data, URL, mensaje, etc.

    # Ordenamiento
    display_order = Column(Integer, nullable=False, default=0)
    row_number = Column(Integer, nullable=False, default=0)  # Fila en keyboard

    # Restricciones
    requires_onboarding = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Auditoría
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    created_by = Column(BigInteger, nullable=True)  # Admin user_id

    # Relaciones
    children = relationship(
        "MenuItem",
        backref="parent",
        remote_side=[item_key],
        cascade="all, delete-orphan"
    )

    # Índices compuestos
    __table_args__ = (
        Index("idx_menu_role_active", "target_role", "is_active"),
        Index("idx_menu_parent", "parent_key"),
        Index("idx_menu_order", "display_order", "row_number"),
    )

    def __repr__(self):
        return f"<MenuItem(key='{self.item_key}', role='{self.target_role}', text='{self.button_text}')>"


class MenuConfig(Base):
    """
    Configuración global del menú para un rol específico.

    Define mensajes de bienvenida, footer y opciones de visualización
    para cada tipo de menú (vip, free, profile, etc).
    """
    __tablename__ = "menu_configs"

    id = Column(Integer, primary_key=True)
    role = Column(String(20), unique=True, nullable=False, index=True)  # 'vip', 'free', 'profile'

    # Mensajes
    welcome_message = Column(Text, nullable=False)
    footer_message = Column(Text, nullable=True)

    # Opciones de visualización
    show_subscription_info = Column(Boolean, nullable=False, default=False)

    # Auditoría
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<MenuConfig(role='{self.role}')>"


class UserInterest(Base):
    """
    Registro de interés de usuario en producto.

    Permite al admin hacer seguimiento de usuarios interesados
    en productos comerciales (sets, personalizados, VIP).
    """
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Producto
    product_type = Column(
        String(50),
        nullable=False,
        index=True
    )  # 'set', 'personalizado', 'vip', 'premium', 'mapa_deseo'

    product_key = Column(String(100), nullable=False)  # 'encanto_inicial', 'sensualidad_revelada'

    # Estado
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )  # 'pending', 'contacted', 'converted', 'rejected'

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    contacted_at = Column(DateTime, nullable=True)
    contacted_by = Column(BigInteger, nullable=True)  # Admin user_id que contactó

    # Notas del admin
    notes = Column(Text, nullable=True)

    # Relación con usuario
    user = relationship("User", backref="interests")

    # Índices compuestos
    __table_args__ = (
        Index("idx_interest_user_status", "user_id", "status"),
        Index("idx_interest_product", "product_type", "product_key"),
        Index("idx_interest_pending", "status", "created_at"),
    )

    def __repr__(self):
        return (
            f"<UserInterest(user_id={self.user_id}, "
            f"product='{self.product_type}:{self.product_key}', "
            f"status='{self.status}')>"
        )
