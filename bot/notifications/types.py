"""
Notification Types - Tipos y configuraciones de notificaciones.
"""
from enum import Enum


class NotificationType(str, Enum):
    """
    Tipos de notificaciones del sistema.

    Cada tipo puede tener su propio template HTML.
    """

    # Bienvenida y onboarding
    WELCOME = "welcome"

    # Recompensas (Besitos, badges, ranks)
    REWARD = "reward"
    POINTS_EARNED = "points_earned"
    BADGE_UNLOCKED = "badge_unlocked"
    RANK_UP = "rank_up"

    # VIP
    VIP_ACTIVATED = "vip_activated"
    VIP_EXPIRING_SOON = "vip_expiring_soon"
    VIP_EXPIRED = "vip_expired"

    # Daily rewards
    DAILY_LOGIN = "daily_login"
    STREAK_MILESTONE = "streak_milestone"

    # Referrals
    REFERRAL_SUCCESS = "referral_success"

    # Achievements
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"

    # Errores y avisos
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self) -> str:
        return self.value
