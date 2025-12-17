"""
Modelos de base de datos para el bot VIP/Free.

Tablas:
- bot_config: Configuración global del bot (singleton)
- users: Usuarios del sistema con roles (FREE/VIP/ADMIN)
- vip_subscribers: Suscriptores del canal VIP
- invitation_tokens: Tokens de invitación generados
- free_channel_requests: Solicitudes de acceso al canal Free
- subscription_plans: Planes de suscripción/tarifas configurables
"""
import logging
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    BigInteger, JSON, ForeignKey, Index, Float, Enum, Text,
    CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, foreign
from datetime import timezone

from bot.database.base import Base
from bot.database.enums import UserRole

logger = logging.getLogger(__name__)


class TransactionType(str, enum.Enum):
    """
    Tipos de transacciones de puntos.

    - EARNED: Puntos ganados (positivo)
    - SPENT: Puntos gastados (negativo)
    - ADJUSTED: Ajuste manual por admin (puede ser + o -)
    """
    EARNED = "earned"
    SPENT = "spent"
    ADJUSTED = "adjusted"


class BotConfig(Base):
    """
    Configuración global del bot (tabla singleton - solo 1 registro).

    Almacena:
    - IDs de canales VIP y Free
    - Configuración de tiempo de espera
    - Configuración de reacciones
    - Tarifas de suscripción
    """
    __tablename__ = "bot_config"

    id = Column(Integer, primary_key=True, default=1)

    # Canales
    vip_channel_id = Column(String(50), nullable=True)  # ID del canal VIP
    free_channel_id = Column(String(50), nullable=True)  # ID del canal Free

    # Configuración
    wait_time_minutes = Column(Integer, default=5)  # Tiempo espera Free

    # Reacciones (JSON arrays de emojis)
    vip_reactions = Column(JSON, default=list)   # ["👍", "❤️", "🔥"]
    free_reactions = Column(JSON, default=list)  # ["👍", "👎"]

    # Tarifas (JSON object)
    subscription_fees = Column(
        JSON,
        default=lambda: {"monthly": 10, "yearly": 100}
    )

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<BotConfig(vip={self.vip_channel_id}, "
            f"free={self.free_channel_id}, wait={self.wait_time_minutes}min)>"
        )


class User(Base):
    """
    Modelo de usuario del sistema.

    Representa un usuario que ha interactuado con el bot.
    Almacena información básica y su rol actual.

    Attributes:
        user_id: ID único de Telegram (Primary Key)
        username: Username de Telegram (puede ser None)
        first_name: Nombre del usuario
        last_name: Apellido (puede ser None)
        role: Rol actual del usuario (FREE/VIP/ADMIN)
        created_at: Fecha de primer contacto con el bot
        updated_at: Última actualización de datos

    Relaciones:
        vip_subscription: Suscripción VIP si existe
        free_requests: Solicitudes al canal Free
    """

    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.FREE
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones (se definen después en VIPSubscriber y FreeChannelRequest)
    progress = relationship(
        "UserProgress",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    reactions = relationship(
        "MessageReaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Retorna nombre completo del usuario."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        """Retorna mention HTML del usuario."""
        return f'<a href="tg://user?id={self.user_id}">{self.full_name}</a>'

    @property
    def is_admin(self) -> bool:
        """Verifica si el usuario es admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_vip(self) -> bool:
        """Verifica si el usuario es VIP."""
        return self.role == UserRole.VIP

    @property
    def is_free(self) -> bool:
        """Verifica si el usuario es Free."""
        return self.role == UserRole.FREE

    def __repr__(self) -> str:
        return (
            f"<User(user_id={self.user_id}, username='{self.username}', "
            f"role={self.role.value})>"
        )


class UserProgress(Base):
    """
    Estado de progreso de gamificación del usuario.

    Almacena:
    - Saldo actual de besitos
    - Nivel actual
    - Totales acumulados (ganados/gastados)
    - Timestamps de creación y actualización

    Relación 1:1 con User.
    """
    __tablename__ = "user_progress"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key a User (relación 1:1)
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Saldo actual de besitos
    besitos_balance = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Saldo actual de besitos del usuario"
    )

    # Nivel actual (empieza en 1)
    current_level = Column(
        Integer,
        nullable=False,
        default=1,
        doc="Nivel actual del usuario (mínimo 1)"
    )

    # Total de puntos ganados (histórico)
    total_points_earned = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total acumulado de puntos ganados (histórico)"
    )

    # Total de puntos gastados (histórico)
    total_points_spent = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total acumulado de puntos gastados (histórico)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Fecha de creación del registro"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Fecha de última actualización"
    )

    # Relación con User (1:1)
    user = relationship("User", back_populates="progress", uselist=False)

    # Relación con transacciones (1:N)
    # Nota: PointTransaction tiene FK a users.user_id, no a user_progress
    transactions = relationship(
        "PointTransaction",
        primaryjoin="UserProgress.user_id == foreign(PointTransaction.user_id)",
        back_populates="user_progress",
        lazy="dynamic"
    )

    def __repr__(self):
        return (
            f"<UserProgress(id={self.id}, user_id={self.user_id}, "
            f"balance={self.besitos_balance}, level={self.current_level})>"
        )

    @property
    def net_points(self) -> int:
        """
        Calcula puntos netos (ganados - gastados).

        Returns:
            Total de puntos netos
        """
        return self.total_points_earned - self.total_points_spent

    def can_afford(self, amount: int) -> bool:
        """
        Verifica si el usuario tiene suficientes puntos.

        Args:
            amount: Cantidad de puntos requeridos

        Returns:
            True si tiene suficientes puntos, False si no
        """
        return self.besitos_balance >= amount


class PointTransaction(Base):
    """
    Registro de transacciones de puntos.

    Cada fila representa una transacción única e inmutable:
    - Puntos ganados por acción
    - Puntos gastados en canje
    - Ajustes manuales de admin

    Características:
    - Histórico completo e inmutable
    - Rastreabilidad de cada operación
    - Balance after para auditoría
    - Metadata flexible en JSON
    """
    __tablename__ = "point_transactions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key a User (no a UserProgress, para auditoría)
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID del usuario (FK a users)"
    )

    # Cantidad de puntos (puede ser negativo para gastos)
    amount = Column(
        Integer,
        nullable=False,
        doc="Cantidad de puntos (positivo=ganado, negativo=gastado)"
    )

    # Tipo de transacción
    transaction_type = Column(
        Enum(TransactionType),
        nullable=False,
        index=True,
        doc="Tipo: earned, spent, adjusted"
    )

    # Razón de la transacción
    reason = Column(
        String(255),
        nullable=False,
        doc="Descripción de por qué se otorgaron/restaron puntos"
    )

    # Metadata adicional (JSON flexible)
    transaction_metadata = Column(
        JSON,
        nullable=True,
        doc="Metadata adicional de la transacción (multiplicadores, contexto, etc)"
    )

    # Balance después de la transacción (para auditoría)
    balance_after = Column(
        Integer,
        nullable=False,
        doc="Saldo del usuario después de aplicar esta transacción"
    )

    # Timestamp (inmutable)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Fecha de la transacción (inmutable)"
    )

    # Relación con UserProgress
    user_progress = relationship(
        "UserProgress",
        primaryjoin="UserProgress.user_id == foreign(PointTransaction.user_id)",
        back_populates="transactions"
    )

    def __repr__(self):
        return (
            f"<PointTransaction(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, type={self.transaction_type.value})>"
        )

    @property
    def is_credit(self) -> bool:
        """
        Verifica si es una transacción de crédito (puntos ganados).

        Returns:
            True si amount > 0, False si no
        """
        return self.amount > 0

    @property
    def is_debit(self) -> bool:
        """
        Verifica si es una transacción de débito (puntos gastados).

        Returns:
            True si amount < 0, False si no
        """
        return self.amount < 0

    @property
    def absolute_amount(self) -> int:
        """
        Retorna el valor absoluto de la cantidad.

        Returns:
            Valor absoluto de amount
        """
        return abs(self.amount)


class UserBadge(Base):
    """
    Insignia desbloqueada por un usuario.

    Attributes:
        id: ID único
        user_id: ID del usuario
        badge_id: ID de la insignia (del config)
        unlocked_at: Fecha de desbloqueo
    """

    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("user_progress.user_id"),
        nullable=False
    )
    badge_id = Column(String(50), nullable=False)
    unlocked_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relación (comentada - UserProgress se redefinió para Servicio de Puntos)
    # user_progress = relationship(
    #     "UserProgress",
    #     back_populates="badges"
    # )

    __table_args__ = (
        Index('idx_user_badges_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<UserBadge(user_id={self.user_id}, badge_id='{self.badge_id}')>"


class DailyStreak(Base):
    """
    Racha de login diario de un usuario.

    Attributes:
        user_id: ID del usuario (PK y FK)
        current_streak: Días consecutivos actuales
        longest_streak: Récord de días consecutivos
        last_login_date: Última fecha de login
        total_logins: Total de logins (lifetime)
    """

    __tablename__ = "daily_streaks"

    user_id = Column(
        BigInteger,
        ForeignKey("user_progress.user_id"),
        primary_key=True
    )
    current_streak = Column(Integer, nullable=False, default=0)
    longest_streak = Column(Integer, nullable=False, default=0)
    last_login_date = Column(DateTime, nullable=True)
    total_logins = Column(Integer, nullable=False, default=0)

    # Relación (comentada - UserProgress se redefinió para Servicio de Puntos)
    # user_progress = relationship(
    #     "UserProgress",
    #     back_populates="daily_streak"
    # )

    def __repr__(self) -> str:
        return (
            f"<DailyStreak(user_id={self.user_id}, "
            f"streak={self.current_streak}, longest={self.longest_streak})>"
        )


class BesitosTransaction(Base):
    """
    Historial de transacciones de Besitos.

    Lleva un log de todos los Besitos ganados/gastados.

    Attributes:
        id: ID único
        user_id: ID del usuario
        amount: Cantidad (+ ganados, - gastados)
        reason: Razón de la transacción
        created_at: Fecha de la transacción
    """

    __tablename__ = "besitos_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_besitos_transactions_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        sign = "+" if self.amount > 0 else ""
        return (
            f"<BesitosTransaction(user_id={self.user_id}, "
            f"amount={sign}{self.amount}, reason='{self.reason}')>"
        )


class SubscriptionPlan(Base):
    """
    Modelo de planes de suscripción/tarifas.

    Representa un plan que el admin configura con nombre, duración y precio.
    Los tokens VIP se generan vinculados a un plan específico.

    Attributes:
        id: ID único del plan
        name: Nombre del plan (ej: "Plan Mensual", "Plan Anual")
        duration_days: Duración en días del plan
        price: Precio del plan (en USD u otra moneda)
        currency: Símbolo de moneda (default: "$")
        active: Si el plan está activo (visible para generar tokens)
        created_at: Fecha de creación
        created_by: User ID del admin que creó el plan

    Relaciones:
        tokens: Tokens generados con este plan
    """
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    duration_days = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="$")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(BigInteger, nullable=False)

    # Relación con tokens
    tokens = relationship(
        "InvitationToken",
        back_populates="plan",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<SubscriptionPlan(id={self.id}, name='{self.name}', "
            f"days={self.duration_days}, price={self.price})>"
        )


class InvitationToken(Base):
    """
    Tokens de invitación generados por administradores.

    Cada token:
    - Es único (16 caracteres alfanuméricos)
    - Tiene duración limitada (expira después de X horas)
    - Se marca como "usado" al ser canjeado
    - Registra quién lo generó y quién lo usó
    - Puede estar asociado a un plan de suscripción
    """
    __tablename__ = "invitation_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Token único
    token = Column(String(16), unique=True, nullable=False, index=True)

    # Generación
    generated_by = Column(BigInteger, nullable=False)  # User ID del admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_hours = Column(Integer, default=24, nullable=False)  # Duración en horas

    # Uso
    used = Column(Boolean, default=False, nullable=False, index=True)
    used_by = Column(BigInteger, nullable=True)  # User ID que canjeó
    used_at = Column(DateTime, nullable=True)

    # Plan asociado (nullable para compatibilidad con tokens antiguos)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    plan = relationship("SubscriptionPlan", back_populates="tokens")

    # Relación: 1 Token → Many Subscribers
    subscribers = relationship(
        "VIPSubscriber",
        back_populates="token",
        cascade="all, delete-orphan"
    )

    # Índice compuesto para queries de tokens no usados
    __table_args__ = (
        Index('idx_token_used_created', 'used', 'created_at'),
    )

    def is_expired(self) -> bool:
        """Verifica si el token ha expirado"""
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(hours=self.duration_hours)
        return datetime.utcnow() > expiry_time

    def is_valid(self) -> bool:
        """Verifica si el token es válido (no usado y no expirado)"""
        return not self.used and not self.is_expired()

    def __repr__(self):
        status = "USADO" if self.used else ("EXPIRADO" if self.is_expired() else "VÁLIDO")
        return f"<Token({self.token[:8]}... - {status})>"


class VIPSubscriber(Base):
    """
    Suscriptores del canal VIP.

    Cada suscriptor:
    - Canjeó un token de invitación
    - Tiene fecha de expiración
    - Puede estar activo o expirado
    """
    __tablename__ = "vip_subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario
    user_id = Column(BigInteger, ForeignKey("users.user_id"), unique=True, nullable=False, index=True)  # ID Telegram

    # Suscripción
    join_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = Column(DateTime, nullable=False)  # Fecha de expiración
    status = Column(
        String(20),
        default="active",
        nullable=False,
        index=True
    )  # "active" o "expired"

    # Token usado
    token_id = Column(Integer, ForeignKey("invitation_tokens.id"), nullable=False)
    token = relationship("InvitationToken", back_populates="subscribers")

    # Usuario (relación inversa)
    user = relationship("User", uselist=False, lazy="selectin")

    # Índice compuesto para buscar activos próximos a expirar
    __table_args__ = (
        Index('idx_status_expiry', 'status', 'expiry_date'),
    )

    def is_expired(self) -> bool:
        """Verifica si la suscripción ha expirado"""
        return datetime.utcnow() > self.expiry_date

    def days_remaining(self) -> int:
        """Retorna días restantes de suscripción (negativo si expirado)"""
        delta = self.expiry_date - datetime.utcnow()
        return delta.days

    def __repr__(self):
        days = self.days_remaining()
        return f"<VIPSubscriber(user={self.user_id}, status={self.status}, days={days})>"


class FreeChannelRequest(Base):
    """
    Solicitudes de acceso al canal Free (cola de espera).

    Cada solicitud:
    - Se crea cuando un usuario solicita acceso
    - Se procesa después de N minutos de espera
    - Se marca como "procesada" al enviar invitación
    """
    __tablename__ = "free_channel_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)  # ID Telegram
    user = relationship("User", uselist=False, lazy="selectin")

    # Solicitud
    request_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)

    # Índice compuesto para queries de pendientes por fecha
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'request_date'),
        Index('idx_processed_date', 'processed', 'request_date'),
    )

    def minutes_since_request(self) -> int:
        """Retorna minutos transcurridos desde la solicitud"""
        delta = datetime.utcnow() - self.request_date
        return int(delta.total_seconds() / 60)

    def is_ready(self, wait_time_minutes: int) -> bool:
        """Verifica si la solicitud cumplió el tiempo de espera"""
        return self.minutes_since_request() >= wait_time_minutes

    def __repr__(self):
        status = "PROCESADA" if self.processed else f"PENDIENTE ({self.minutes_since_request()}min)"
        return f"<FreeRequest(user={self.user_id}, {status})>"


class NotificationTemplate(Base):
    """
    Modelo de templates de notificaciones personalizados.

    Permite a los admins personalizar los mensajes del bot
    sin tocar código.

    Attributes:
        id: ID único
        type: Tipo de notificación (NotificationType)
        name: Nombre descriptivo
        content: Contenido HTML del template
        active: Si el template está activo
        created_at: Fecha de creación
        updated_at: Última actualización
    """

    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<NotificationTemplate(type='{self.type}', name='{self.name}')>"


class ReactionConfig(Base):
    """
    Configuración de reacciones disponibles para publicaciones.

    Almacena emojis, labels y puntajes de besitos para reacciones inline.
    Permite a los administradores definir qué reacciones están disponibles
    en los mensajes broadcasted.

    Attributes:
        id: ID único de la configuración
        emoji: Emoji unicode único para la reacción (ej: "❤️", "👍")
        label: Etiqueta/descripción corta (ej: "Like", "Love")
        besitos_reward: Cantidad de besitos otorgados al reaccionar
        active: Si la reacción está activa y disponible para usar
        created_at: Fecha de creación
        updated_at: Última actualización

    Constraints:
        - Emoji debe ser único en el sistema
        - besitos_reward debe ser >= 1
    """

    __tablename__ = "reaction_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emoji = Column(String(10), nullable=False, unique=True, index=True)
    label = Column(String(50), nullable=False)
    besitos_reward = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint("emoji", name="uq_reaction_emoji"),
        CheckConstraint("besitos_reward >= 1", name="ck_besitos_positive"),
    )

    def __repr__(self) -> str:
        status = "✅" if self.active else "❌"
        return (
            f"<ReactionConfig(id={self.id}, emoji='{self.emoji}', "
            f"label='{self.label}', besitos={self.besitos_reward}, "
            f"active={status})>"
        )


class MessageReaction(Base):
    """
    Reacciones de usuarios a mensajes de canal.

    Rastrea qué usuario reaccionó a qué mensaje, con qué emoji,
    y cuántos besitos se otorgaron.

    Constraint: Un usuario solo puede tener UNA reacción activa por mensaje.

    Attributes:
        id: ID único de la reacción
        channel_id: ID del canal de Telegram donde está el mensaje
        message_id: ID del mensaje de Telegram
        user_id: ID del usuario que reaccionó (FK a users)
        emoji: Emoji de la reacción (ej: "❤️", "👍")
        besitos_awarded: Cantidad de besitos otorgados en este momento
        created_at: Fecha de la reacción
        user: Relación a User
    """

    __tablename__ = "message_reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identificación del mensaje
    channel_id = Column(BigInteger, nullable=False, index=True)
    message_id = Column(BigInteger, nullable=False, index=True)

    # Usuario que reacciona
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Reacción seleccionada
    emoji = Column(String(10), nullable=False)
    besitos_awarded = Column(Integer, nullable=False)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    user = relationship("User", back_populates="reactions")

    # Constraints
    __table_args__ = (
        # Un usuario solo puede tener una reacción por mensaje
        UniqueConstraint("channel_id", "message_id", "user_id", name="uq_message_user_reaction"),
        # Índice compuesto para queries frecuentes
        Index("ix_message_reactions_lookup", "channel_id", "message_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<MessageReaction(id={self.id}, user={self.user_id}, "
            f"msg={self.message_id}, emoji='{self.emoji}', "
            f"besitos={self.besitos_awarded})>"
        )


class Level(Base):
    """
    Definición de niveles del sistema de gamificación.

    Cada nivel define:
    - Rango de puntos requeridos (min_points - max_points)
    - Multiplicador de puntos progresivo
    - Nombre y emoji representativo
    - Beneficios/perks asociados

    Niveles predefinidos:
    1. Novato (0-99 pts, 1.0x)
    2. Aprendiz (100-249 pts, 1.1x)
    3. Competente (250-499 pts, 1.2x)
    4. Avanzado (500-999 pts, 1.3x)
    5. Experto (1000-2499 pts, 1.5x)
    6. Maestro (2500-4999 pts, 1.8x)
    7. Leyenda (5000+ pts, 2.0x)

    Attributes:
        id: ID único del nivel
        level: Número de nivel (1-7, único)
        name: Nombre del nivel
        icon: Emoji representativo
        min_points: Puntos mínimos para alcanzar este nivel
        max_points: Puntos máximos (None = sin límite superior)
        multiplier: Multiplicador de puntos en este nivel
        perks: Lista JSON de beneficios/ventajas
        created_at: Fecha de creación del registro
    """
    __tablename__ = "levels"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Número de nivel (1-7)
    level = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        doc="Número de nivel (1-7)"
    )

    # Nombre del nivel
    name = Column(
        String(50),
        nullable=False,
        doc="Nombre del nivel (ej: Experto)"
    )

    # Emoji representativo
    icon = Column(
        String(10),
        nullable=False,
        doc="Emoji del nivel (ej: 🌟)"
    )

    # Puntos mínimos requeridos
    min_points = Column(
        Integer,
        nullable=False,
        doc="Puntos mínimos para alcanzar este nivel"
    )

    # Puntos máximos del nivel (None = sin límite)
    max_points = Column(
        Integer,
        nullable=True,
        doc="Puntos máximos del nivel (None = sin límite superior)"
    )

    # Multiplicador de puntos
    multiplier = Column(
        Float,
        nullable=False,
        default=1.0,
        doc="Multiplicador de puntos para este nivel"
    )

    # Beneficios (JSON)
    perks = Column(
        JSON,
        nullable=True,
        doc="Lista de beneficios del nivel"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return (
            f"<Level(level={self.level}, name={self.name}, "
            f"points={self.min_points}-{self.max_points}, mult={self.multiplier})>"
        )

    @property
    def display_name(self) -> str:
        """
        Retorna nombre con emoji.

        Returns:
            Nombre formateado con emoji

        Example:
            >>> level.display_name
            "🌟 Experto"
        """
        return f"{self.icon} {self.name}"

    def is_in_range(self, points: int) -> bool:
        """
        Verifica si una cantidad de puntos está en el rango de este nivel.

        Args:
            points: Cantidad de puntos a verificar

        Returns:
            True si está en rango, False si no
        """
        if points < self.min_points:
            return False

        if self.max_points is None:
            return True  # Nivel máximo, sin límite superior

        return points <= self.max_points
