"""
Event Types - Definiciones de todos los eventos del sistema.

Cada evento representa algo que ocurrió en el sistema y puede
desencadenar acciones en múltiples módulos (gamificación, notificaciones, etc.).
"""
from dataclasses import dataclass
from typing import Optional

from bot.events.base import Event


# ===== EVENTOS DE USUARIO =====


@dataclass
class UserStartedBotEvent(Event):
    """
    Usuario ejecutó /start por primera vez.

    Attributes:
        user_id: ID del usuario
        username: Username de Telegram
        first_name: Nombre del usuario
        is_new: Si es la primera vez que usa el bot
    """

    username: Optional[str] = None
    first_name: str = ""
    is_new: bool = True


@dataclass
class UserRoleChangedEvent(Event):
    """
    El rol de un usuario cambió.

    Attributes:
        user_id: ID del usuario
        old_role: Rol anterior
        new_role: Rol nuevo
        reason: Razón del cambio
    """

    old_role: str = ""
    new_role: str = ""
    reason: str = ""


# ===== EVENTOS VIP =====


@dataclass
class UserJoinedVIPEvent(Event):
    """
    Usuario activó suscripción VIP.

    Attributes:
        user_id: ID del usuario
        plan_id: ID del plan usado
        plan_name: Nombre del plan
        duration_days: Días de suscripción
        token_id: ID del token usado
    """

    plan_id: int = 0
    plan_name: str = ""
    duration_days: int = 0
    token_id: int = 0


@dataclass
class UserVIPExpiredEvent(Event):
    """
    Suscripción VIP de usuario expiró.

    Attributes:
        user_id: ID del usuario
        subscription_id: ID de la suscripción
        days_active: Días que estuvo activa la suscripción
    """

    subscription_id: int = 0
    days_active: int = 0


@dataclass
class TokenGeneratedEvent(Event):
    """
    Admin generó un token VIP.

    Attributes:
        admin_id: ID del admin que generó
        token_id: ID del token
        token_string: String del token
        plan_id: ID del plan asociado
        duration_hours: Duración del token
    """

    admin_id: int = 0
    token_id: int = 0
    token_string: str = ""
    plan_id: int = 0
    duration_hours: int = 0


# ===== EVENTOS FREE CHANNEL =====


@dataclass
class UserRequestedFreeChannelEvent(Event):
    """
    Usuario solicitó acceso al canal Free.

    Attributes:
        user_id: ID del usuario
        request_id: ID de la solicitud
    """

    request_id: int = 0


@dataclass
class UserJoinedFreeChannelEvent(Event):
    """
    Usuario fue procesado y recibió acceso al canal Free.

    Attributes:
        user_id: ID del usuario
        request_id: ID de la solicitud
        wait_time_minutes: Tiempo que esperó
    """

    request_id: int = 0
    wait_time_minutes: int = 0


# ===== EVENTOS DE INTERACCIÓN =====


@dataclass
class MessageReactedEvent(Event):
    """
    Usuario reaccionó a un mensaje (botón inline).

    Attributes:
        user_id: ID del usuario
        message_id: ID del mensaje
        channel_id: ID del canal
        reaction_type: Tipo de reacción (like, love, fire, etc.)
        is_first_reaction: Si es la primera reacción del usuario a ese mensaje
    """

    message_id: int = 0
    channel_id: int = 0
    reaction_type: str = ""
    is_first_reaction: bool = True


@dataclass
class DailyLoginEvent(Event):
    """
    Usuario reclamó su regalo diario.

    Attributes:
        user_id: ID del usuario
        streak_days: Días consecutivos de login
        is_new_streak: Si es un nuevo récord de streak
    """

    streak_days: int = 1
    is_new_streak: bool = False


@dataclass
class UserReferredEvent(Event):
    """
    Usuario refirió a otro usuario.

    Attributes:
        referrer_id: ID del usuario que refirió
        referred_id: ID del usuario referido
    """

    referrer_id: int = 0
    referred_id: int = 0


# ===== EVENTOS DE GAMIFICACIÓN =====


@dataclass
class PointsAwardedEvent(Event):
    """
    Puntos (Besitos) fueron otorgados a un usuario.

    Attributes:
        user_id: ID del usuario
        points: Cantidad de Besitos otorgados
        reason: Razón de la recompensa
        source_event: Tipo de evento que causó la recompensa
    """

    points: int = 0
    reason: str = ""
    source_event: str = ""


@dataclass
class BadgeUnlockedEvent(Event):
    """
    Usuario desbloqueó una insignia.

    Attributes:
        user_id: ID del usuario
        badge_id: ID de la insignia
        badge_name: Nombre de la insignia
    """

    badge_id: int = 0
    badge_name: str = ""


@dataclass
class RankUpEvent(Event):
    """
    Usuario subió de rango.

    Attributes:
        user_id: ID del usuario
        old_rank: Rango anterior
        new_rank: Rango nuevo
        total_points: Total de Besitos acumulados
    """

    old_rank: str = ""
    new_rank: str = ""
    total_points: int = 0


# ===== EVENTOS DE BROADCAST =====


@dataclass
class MessageBroadcastedEvent(Event):
    """
    Se envió un mensaje broadcast a un canal.

    Attributes:
        channel_id: ID del canal
        channel_type: Tipo de canal (vip/free)
        message_id: ID del mensaje enviado
        admin_id: ID del admin que envió
        content_type: Tipo de contenido (text/photo/video)
    """

    channel_id: int = 0
    channel_type: str = ""
    message_id: int = 0
    admin_id: int = 0
    content_type: str = "text"
