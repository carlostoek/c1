"""
Modelos de base de datos para el bot VIP/Free.

Tablas:
- bot_config: Configuración global del bot (singleton)
- users: Usuarios del sistema con roles (FREE/VIP/ADMIN)
- vip_subscribers: Suscriptores del canal VIP
- invitation_tokens: Tokens de invitación generados
- free_channel_requests: Solicitudes de acceso al canal Free
- subscription_plans: Planes de suscripción/tarifas configurables
- broadcast_messages: Mensajes de broadcasting con gamificación
"""
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    BigInteger, JSON, ForeignKey, Index, Float, Enum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from bot.database.base import Base
from bot.database.enums import UserRole

logger = logging.getLogger(__name__)


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

    # Mensaje de bienvenida Free (con variables: {user_name}, {channel_name}, {wait_time})
    free_welcome_message = Column(
        String(1000),
        nullable=True,
        default="Hola {user_name}, tu solicitud de acceso a {channel_name} ha sido registrada. Debes esperar {wait_time} minutos antes de ser aprobado."
    )

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

    # Relaciones (se definen después en VIPSubscriber, FreeChannelRequest, ConversionEvent)
    conversion_events = relationship("ConversionEvent", back_populates="user", lazy="selectin")

    # ONDA D Relationships
    lifecycle = relationship("UserLifecycle", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    notification_preferences = relationship("NotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    reengagement_logs = relationship("ReengagementLog", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

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

    # Token usado (nullable para VIP otorgado por recompensas sin token)
    token_id = Column(Integer, ForeignKey("invitation_tokens.id"), nullable=True)
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


class BroadcastMessage(Base):
    """
    Registro de mensajes de broadcasting enviados con gamificación.

    Cada registro:
    - Almacena información del mensaje enviado (texto, media)
    - Configuración de gamificación (botones de reacción)
    - Protección de contenido
    - Cache de estadísticas de reacciones
    """
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identificación del mensaje
    message_id = Column(BigInteger, nullable=False)  # ID del mensaje en Telegram
    chat_id = Column(BigInteger, nullable=False)  # ID del canal donde se envió

    # Contenido
    content_type = Column(String(20), nullable=False)  # "text", "photo", "video"
    content_text = Column(String(4096), nullable=True)  # Texto del mensaje
    media_file_id = Column(String(200), nullable=True)  # File ID de Telegram (si es media)

    # Auditoría
    sent_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)  # Admin que envió
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Gamificación
    gamification_enabled = Column(Boolean, default=False, nullable=False)
    reaction_buttons = Column(JSON, default=list)  # Lista de configs: [{"emoji": "👍", "label": "...", "reaction_type_id": 1, "besitos": 10}]
    content_protected = Column(Boolean, default=False, nullable=False)  # Protección anti-forward

    # Cache de estadísticas
    total_reactions = Column(Integer, default=0, nullable=False)
    unique_reactors = Column(Integer, default=0, nullable=False)

    # Relación con usuario
    sender = relationship("User", uselist=False, lazy="selectin")

    # Índices para optimización
    __table_args__ = (
        Index('idx_chat_message', 'chat_id', 'message_id', unique=True),
        Index('idx_sent_at', 'sent_at'),
        Index('idx_gamification_enabled', 'gamification_enabled'),
    )

    def __repr__(self):
        return (
            f"<BroadcastMessage(id={self.id}, chat_id={self.chat_id}, "
            f"message_id={self.message_id}, gamification={self.gamification_enabled})>"
        )


class ConversionEvent(Base):
    """
    Registro de eventos de conversión para análisis y rate limiting.

    Almacena:
    - Ofertas mostradas a usuarios
    - Ofertas aceptadas o rechazadas
    - Descuentos aplicados
    - Timestamps para análisis de comportamiento
    """
    __tablename__ = "conversion_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    # Evento
    event_type = Column(
        String(50),
        nullable=False
    )  # "offer_shown", "offer_accepted", "offer_declined"

    offer_type = Column(
        String(50),
        nullable=False
    )  # "free_to_vip", "vip_renewal", "shop_item", etc.

    # Detalles de la oferta (JSON flexible)
    offer_details = Column(JSON, default=dict, nullable=False)

    # Descuento aplicado
    discount_applied = Column(Float, default=0.0, nullable=False)

    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relación
    user = relationship("User", back_populates="conversion_events", lazy="selectin")

    # Índices para queries comunes
    __table_args__ = (
        Index('idx_user_offer_type', 'user_id', 'offer_type'),
        Index('idx_event_type', 'event_type'),
        Index('idx_created_at', 'created_at'),
    )

    def __repr__(self):
        return (
            f"<ConversionEvent(id={self.id}, user_id={self.user_id}, "
            f"event_type={self.event_type}, offer_type={self.offer_type})>"
        )


class LimitedStock(Base):
    """
    Gestión de ítems con stock limitado para crear escasez y urgencia.

    Permite:
    - Definir cantidad limitada de un item
    - Reservar temporalmente mientras usuario completa compra
    - Liberar reservas expiradas
    - Eventos de tiempo limitado
    """
    __tablename__ = "limited_stock"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Item del shop
    item_id = Column(Integer, nullable=False)  # FK a shop_items (gamification)

    # Cantidades
    initial_quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)

    # Ventana de tiempo
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=True)  # None = permanente

    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Índices
    __table_args__ = (
        Index('idx_item_id', 'item_id', unique=True),
        Index('idx_active_items', 'start_date', 'end_date'),
    )

    def __repr__(self):
        return (
            f"<LimitedStock(id={self.id}, item_id={self.item_id}, "
            f"remaining={self.remaining_quantity}/{self.initial_quantity})>"
        )

    @property
    def is_active(self) -> bool:
        """Verifica si el item está activo (dentro de ventana de tiempo)."""
        now = datetime.utcnow()
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True

    @property
    def is_sold_out(self) -> bool:
        """Verifica si el stock se agotó."""
        return self.remaining_quantity <= 0


class UserLifecycle(Base):
    """Estado del ciclo de vida del usuario."""
    __tablename__ = "user_lifecycle"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    current_state: Mapped[str] = mapped_column(String(50), default="new", index=True)  # new, active, at_risk, dormant, lost
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    messages_sent_count: Mapped[int] = mapped_column(Integer, default=0)
    last_message_sent: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    do_not_disturb: Mapped[bool] = mapped_column(Boolean, default=False)
    state_changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="lifecycle")

    def __repr__(self):
        return (
            f"<UserLifecycle(user_id={self.user_id}, state='{self.current_state}', "
            f"risk_score={self.risk_score})>"
        )


class NotificationPreferences(Base):
    """Preferencias de notificación del usuario."""
    __tablename__ = "notification_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    content_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    streak_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    offer_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    reengagement_messages: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_hours_start: Mapped[int] = mapped_column(Integer, default=22)
    quiet_hours_end: Mapped[int] = mapped_column(Integer, default=8)
    max_messages_per_day: Mapped[int] = mapped_column(Integer, default=3)
    timezone: Mapped[str] = mapped_column(String(100), default="America/Mexico_City")

    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self):
        return f"<NotificationPreferences(user_id={self.user_id})>"


class ReengagementLog(Base):
    """Log de mensajes de re-engagement enviados."""
    __tablename__ = "reengagement_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    message_type: Mapped[str] = mapped_column(String(100))  # at_risk_1, dormant_1, etc.
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    user_responded: Mapped[bool] = mapped_column(Boolean, default=False)
    response_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="reengagement_logs")

    def __repr__(self):
        return (
            f"<ReengagementLog(user_id={self.user_id}, type='{self.message_type}', "
            f"sent_at='{self.sent_at.isoformat()}')>"
        )
