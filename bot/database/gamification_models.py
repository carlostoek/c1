"""
Modelos de base de datos para el sistema de gamificación.

Tablas:
- gamification_config: Configuración global de gamificación (singleton)
- publications: Publicaciones con botones de reacción
- user_reactions: Reacciones de usuarios en publicaciones
- user_points: Balance de puntos de usuarios
- points_transactions: Historial de transacciones de puntos
- badges: Badges/insignias disponibles
- user_badges: Badges desbloqueados por usuarios
- user_levels: Niveles de usuario
- media_sets: Sets de contenido multimedia (CMS)
- media_set_items: Items dentro de un set multimedia
- shop_items: Productos de la tienda
- shop_purchases: Compras realizadas por usuarios
- missions: Misiones disponibles
- user_mission_progress: Progreso de usuarios en misiones
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    BigInteger, JSON, ForeignKey, Index, Float, Enum, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from bot.database.base import Base
from bot.database.enums import (
    TransactionType, BadgeRarity, ChannelType,
    MediaType, ShopItemType, MissionType, RewardType
)

logger = logging.getLogger(__name__)


class GamificationConfig(Base):
    """
    Configuración global del sistema de gamificación (singleton - solo 1 registro).

    Almacena:
    - Puntos por reacción
    - Puntos del regalo diario
    - Multiplicador de racha
    - Emojis predeterminados para reacciones
    """
    __tablename__ = "gamification_config"

    id = Column(Integer, primary_key=True, default=1)

    # Configuración de puntos
    points_per_reaction = Column(Integer, default=1, nullable=False)
    daily_gift_points = Column(Integer, default=5, nullable=False)
    streak_multiplier = Column(Float, default=1.5, nullable=False)

    # Emojis predeterminados (set global)
    default_reaction_emojis = Column(
        JSON,
        default=lambda: ["👍", "❤️", "🔥", "🎉", "💯"],
        nullable=False
    )

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<GamificationConfig(points_per_reaction={self.points_per_reaction}, "
            f"daily_gift={self.daily_gift_points}, streak_mult={self.streak_multiplier})>"
        )


class Publication(Base):
    """
    Publicaciones con botones de reacción.

    Cada publicación representa un mensaje enviado a un canal
    con botones inline de reacción.

    Attributes:
        id: ID único de la publicación
        channel_id: ID del canal de Telegram
        message_id: ID del mensaje en Telegram
        channel_type: Tipo de canal (VIP/FREE)
        reaction_buttons: Lista de emojis configurados como botones
        active: Si la publicación acepta reacciones
        created_at: Fecha de creación

    Relaciones:
        reactions: Reacciones de usuarios en esta publicación
    """
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Canal y mensaje
    channel_id = Column(String(50), nullable=False, index=True)
    message_id = Column(BigInteger, nullable=False)
    channel_type = Column(Enum(ChannelType), nullable=False)

    # Configuración de reacciones
    reaction_buttons = Column(JSON, nullable=False)  # Lista de emojis

    # Estado
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relaciones
    reactions = relationship(
        "UserReaction",
        back_populates="publication",
        cascade="all, delete-orphan"
    )

    # Índices compuestos
    __table_args__ = (
        Index('idx_channel_message', 'channel_id', 'message_id', unique=True),
        Index('idx_active_created', 'active', 'created_at'),
    )

    def __repr__(self):
        return (
            f"<Publication(id={self.id}, channel={self.channel_type.value}, "
            f"message_id={self.message_id}, active={self.active})>"
        )


class UserReaction(Base):
    """
    Reacciones de usuarios en publicaciones.

    Registra cada vez que un usuario reacciona a una publicación,
    incluyendo el emoji usado y los puntos otorgados.

    Attributes:
        id: ID único de la reacción
        user_id: ID del usuario que reaccionó
        publication_id: ID de la publicación
        emoji: Emoji usado en la reacción
        points_awarded: Puntos otorgados por esta reacción
        created_at: Fecha de la reacción

    Relaciones:
        publication: Publicación a la que se reaccionó
        user: Usuario que reaccionó
    """
    __tablename__ = "user_reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario y publicación
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=False, index=True)

    # Detalles de la reacción
    emoji = Column(String(10), nullable=False)
    points_awarded = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    publication = relationship("Publication", back_populates="reactions")
    user = relationship("User", lazy="selectin")

    # Índice compuesto: evita doble reacción
    __table_args__ = (
        Index('idx_user_publication', 'user_id', 'publication_id', unique=True),
    )

    def __repr__(self):
        return (
            f"<UserReaction(user={self.user_id}, pub={self.publication_id}, "
            f"emoji={self.emoji}, points={self.points_awarded})>"
        )


class UserPoints(Base):
    """
    Balance de puntos ("besitos") de usuarios.

    Almacena el balance actual y estadísticas de puntos de cada usuario.

    Attributes:
        user_id: ID del usuario (Primary Key)
        balance: Balance actual de puntos
        total_earned: Total de puntos ganados históricamente
        total_spent: Total de puntos gastados históricamente
        last_daily_gift: Última vez que reclamó regalo diario
        current_streak: Racha actual (publicaciones consecutivas)
        max_streak: Racha máxima alcanzada
        updated_at: Última actualización

    Relaciones:
        user: Usuario asociado
        transactions: Historial de transacciones
    """
    __tablename__ = "user_points"

    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)

    # Balance
    balance = Column(Integer, default=0, nullable=False)
    total_earned = Column(Integer, default=0, nullable=False)
    total_spent = Column(Integer, default=0, nullable=False)

    # Regalo diario
    last_daily_gift = Column(DateTime, nullable=True)

    # Rachas
    current_streak = Column(Integer, default=0, nullable=False)
    max_streak = Column(Integer, default=0, nullable=False)

    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    user = relationship("User", uselist=False, lazy="selectin")
    transactions = relationship(
        "PointsTransaction",
        back_populates="user_points",
        cascade="all, delete-orphan",
        order_by="PointsTransaction.created_at.desc()"
    )

    def can_claim_daily_gift(self) -> bool:
        """Verifica si el usuario puede reclamar el regalo diario."""
        if self.last_daily_gift is None:
            return True

        # Verificar si han pasado 24 horas
        time_since_last = datetime.utcnow() - self.last_daily_gift
        return time_since_last >= timedelta(hours=24)

    def has_enough_points(self, amount: int) -> bool:
        """Verifica si el usuario tiene suficientes puntos."""
        return self.balance >= amount

    def __repr__(self):
        return (
            f"<UserPoints(user={self.user_id}, balance={self.balance}, "
            f"streak={self.current_streak})>"
        )


class PointsTransaction(Base):
    """
    Historial de transacciones de puntos.

    Registra cada movimiento de puntos (ganancia o gasto).

    Attributes:
        id: ID único de la transacción
        user_id: ID del usuario
        amount: Cantidad de puntos (positivo=ganancia, negativo=gasto)
        transaction_type: Tipo de transacción
        reference_id: ID de referencia (reacción, compra, etc.)
        description: Descripción de la transacción
        created_at: Fecha de la transacción

    Relaciones:
        user_points: Balance del usuario
    """
    __tablename__ = "points_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario
    user_id = Column(BigInteger, ForeignKey("user_points.user_id"), nullable=False, index=True)

    # Transacción
    amount = Column(Integer, nullable=False)  # Positivo=ganancia, Negativo=gasto
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    reference_id = Column(Integer, nullable=True)  # ID de reacción, compra, etc.
    description = Column(String(200), nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relaciones
    user_points = relationship("UserPoints", back_populates="transactions")

    def __repr__(self):
        return (
            f"<PointsTransaction(user={self.user_id}, amount={self.amount:+d}, "
            f"type={self.transaction_type.value})>"
        )


class Badge(Base):
    """
    Badges/insignias disponibles en el sistema.

    Attributes:
        id: ID único del badge
        name: Nombre del badge
        emoji: Emoji representativo
        description: Descripción del badge
        rarity: Rareza del badge
        active: Si el badge está activo
        created_at: Fecha de creación
        created_by: ID del admin que creó el badge

    Relaciones:
        user_badges: Usuarios que tienen este badge
    """
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información del badge
    name = Column(String(50), nullable=False, unique=True)
    emoji = Column(String(10), nullable=False)
    description = Column(String(200), nullable=False)
    rarity = Column(Enum(BadgeRarity), nullable=False, default=BadgeRarity.COMMON)

    # Estado
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(BigInteger, nullable=False)

    # Relaciones
    user_badges = relationship(
        "UserBadge",
        back_populates="badge",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Badge(id={self.id}, name='{self.name}', "
            f"rarity={self.rarity.value})>"
        )


class UserBadge(Base):
    """
    Badges desbloqueados por usuarios.

    Attributes:
        id: ID único del registro
        user_id: ID del usuario
        badge_id: ID del badge
        unlocked_at: Fecha de desbloqueo

    Relaciones:
        badge: Badge desbloqueado
        user: Usuario que desbloqueó
    """
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario y badge
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False, index=True)

    # Metadata
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    badge = relationship("Badge", back_populates="user_badges")
    user = relationship("User", lazy="selectin")

    # Índice compuesto: evita duplicados
    __table_args__ = (
        Index('idx_user_badge', 'user_id', 'badge_id', unique=True),
    )

    def __repr__(self):
        return f"<UserBadge(user={self.user_id}, badge={self.badge_id})>"


class UserLevel(Base):
    """
    Niveles de usuario en el sistema de gamificación.

    Attributes:
        id: ID único del nivel
        name: Nombre del nivel
        min_points_required: Puntos mínimos requeridos
        emoji: Emoji del nivel
        perks: Beneficios del nivel (JSON)
        order: Orden del nivel (para sorting)
        active: Si el nivel está activo
        created_at: Fecha de creación

    Note:
        Los niveles se ordenan por min_points_required.
        Un usuario está en el nivel más alto para el que tenga puntos.
    """
    __tablename__ = "user_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información del nivel
    name = Column(String(50), nullable=False, unique=True)
    min_points_required = Column(Integer, nullable=False, index=True)
    emoji = Column(String(10), nullable=False)
    perks = Column(JSON, default=dict, nullable=False)  # {"description": "..."}

    # Orden
    order = Column(Integer, nullable=False, default=0, index=True)

    # Estado
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<UserLevel(id={self.id}, name='{self.name}', "
            f"min_points={self.min_points_required})>"
        )


class MediaSet(Base):
    """
    Sets de contenido multimedia (CMS).

    Un MediaSet es una colección de archivos multimedia
    que puede ser usado como recompensa o vendido en la tienda.

    Attributes:
        id: ID único del set
        name: Nombre del set
        description: Descripción del set
        cover_emoji: Emoji de portada
        active: Si el set está activo
        created_at: Fecha de creación
        created_by: ID del admin que creó el set

    Relaciones:
        items: Items del set
    """
    __tablename__ = "media_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información del set
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    cover_emoji = Column(String(10), nullable=False, default="📦")

    # Estado
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(BigInteger, nullable=False)

    # Relaciones
    items = relationship(
        "MediaSetItem",
        back_populates="media_set",
        cascade="all, delete-orphan",
        order_by="MediaSetItem.order"
    )

    def __repr__(self):
        return f"<MediaSet(id={self.id}, name='{self.name}')>"


class MediaSetItem(Base):
    """
    Items dentro de un MediaSet.

    Cada item representa un archivo multimedia (foto, video, etc.).

    Attributes:
        id: ID único del item
        set_id: ID del set al que pertenece
        item_type: Tipo de media
        file_id: file_id de Telegram
        caption: Texto descriptivo (opcional)
        order: Orden dentro del set
        created_at: Fecha de creación

    Relaciones:
        media_set: Set al que pertenece
    """
    __tablename__ = "media_set_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Set
    set_id = Column(Integer, ForeignKey("media_sets.id"), nullable=False, index=True)

    # Media
    item_type = Column(Enum(MediaType), nullable=False)
    file_id = Column(String(200), nullable=False)  # Telegram file_id
    caption = Column(Text, nullable=True)

    # Orden
    order = Column(Integer, nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    media_set = relationship("MediaSet", back_populates="items")

    def __repr__(self):
        return (
            f"<MediaSetItem(id={self.id}, set={self.set_id}, "
            f"type={self.item_type.value})>"
        )


class ShopItem(Base):
    """
    Productos de la tienda de gamificación.

    Attributes:
        id: ID único del item
        name: Nombre del producto
        description: Descripción del producto
        item_type: Tipo de item
        price_points: Precio en puntos (besitos)
        reference_id: ID del badge/nivel/set referenciado
        vip_days: Días VIP (si item_type=VIP_DAYS)
        stock: Stock disponible (-1 = ilimitado)
        active: Si el item está en venta
        created_at: Fecha de creación
        created_by: ID del admin que creó el item

    Relaciones:
        purchases: Compras de este item
    """
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información del producto
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    item_type = Column(Enum(ShopItemType), nullable=False, index=True)

    # Precio y referencia
    price_points = Column(Integer, nullable=False)
    reference_id = Column(Integer, nullable=True)  # badge_id, level_id, set_id
    vip_days = Column(Integer, nullable=True)  # Solo si item_type=VIP_DAYS

    # Stock
    stock = Column(Integer, default=-1, nullable=False)  # -1 = ilimitado

    # Estado
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(BigInteger, nullable=False)

    # Relaciones
    purchases = relationship(
        "ShopPurchase",
        back_populates="item",
        cascade="all, delete-orphan"
    )

    def is_available(self) -> bool:
        """Verifica si el item está disponible para compra."""
        if not self.active:
            return False
        if self.stock == -1:  # Ilimitado
            return True
        return self.stock > 0

    def __repr__(self):
        return (
            f"<ShopItem(id={self.id}, name='{self.name}', "
            f"price={self.price_points}, type={self.item_type.value})>"
        )


class ShopPurchase(Base):
    """
    Compras realizadas en la tienda.

    Attributes:
        id: ID único de la compra
        user_id: ID del usuario que compró
        item_id: ID del item comprado
        points_spent: Puntos gastados
        purchased_at: Fecha de compra

    Relaciones:
        item: Item comprado
        user: Usuario que compró
    """
    __tablename__ = "shop_purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario e item
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=False, index=True)

    # Detalles de la compra
    points_spent = Column(Integer, nullable=False)

    # Metadata
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    item = relationship("ShopItem", back_populates="purchases")
    user = relationship("User", lazy="selectin")

    def __repr__(self):
        return (
            f"<ShopPurchase(id={self.id}, user={self.user_id}, "
            f"item={self.item_id}, points={self.points_spent})>"
        )


class Mission(Base):
    """
    Misiones del sistema de gamificación.

    Attributes:
        id: ID único de la misión
        name: Nombre de la misión
        description: Descripción de la misión
        mission_type: Tipo de misión
        target_value: Valor objetivo a alcanzar
        reward_type: Tipo de recompensa
        reward_id: ID del badge/set si aplica
        reward_points: Puntos si reward_type=POINTS
        active: Si la misión está activa
        created_at: Fecha de creación
        created_by: ID del admin que creó la misión

    Relaciones:
        progress: Progreso de usuarios en esta misión
    """
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información de la misión
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    mission_type = Column(Enum(MissionType), nullable=False, index=True)
    target_value = Column(Integer, nullable=False)

    # Recompensa
    reward_type = Column(Enum(RewardType), nullable=False)
    reward_id = Column(Integer, nullable=True)  # badge_id o set_id
    reward_points = Column(Integer, nullable=True)  # Si reward_type=POINTS

    # Estado
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(BigInteger, nullable=False)

    # Relaciones
    progress = relationship(
        "UserMissionProgress",
        back_populates="mission",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Mission(id={self.id}, name='{self.name}', "
            f"type={self.mission_type.value}, target={self.target_value})>"
        )


class UserMissionProgress(Base):
    """
    Progreso de usuarios en misiones.

    Attributes:
        id: ID único del registro
        user_id: ID del usuario
        mission_id: ID de la misión
        current_value: Valor actual (progreso)
        completed: Si la misión fue completada
        completed_at: Fecha de completado
        reward_claimed: Si la recompensa fue reclamada
        created_at: Fecha de inicio

    Relaciones:
        mission: Misión asociada
        user: Usuario asociado
    """
    __tablename__ = "user_mission_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario y misión
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False, index=True)

    # Progreso
    current_value = Column(Integer, default=0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    reward_claimed = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    mission = relationship("Mission", back_populates="progress")
    user = relationship("User", lazy="selectin")

    # Índice compuesto: un usuario, una misión
    __table_args__ = (
        Index('idx_user_mission', 'user_id', 'mission_id', unique=True),
    )

    def is_complete(self) -> bool:
        """Verifica si la misión está completada."""
        return self.completed

    def can_claim_reward(self) -> bool:
        """Verifica si la recompensa puede ser reclamada."""
        return self.completed and not self.reward_claimed

    def __repr__(self):
        return (
            f"<UserMissionProgress(user={self.user_id}, mission={self.mission_id}, "
            f"progress={self.current_value}, completed={self.completed})>"
        )
