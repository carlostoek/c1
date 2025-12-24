"""
Sistema de notificaciones del módulo de gamificación.

Este servicio gestiona el envío de notificaciones push a usuarios sobre:
- Level-ups (subida de nivel)
- Misiones completadas
- Recompensas desbloqueadas
- Milestones de rachas
- Rachas perdidas
"""

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import Mission, Reward, Level, GamificationConfig

logger = logging.getLogger(__name__)


NOTIFICATION_TEMPLATES = {
    'level_up': (
        "🎉 <b>¡Subiste de nivel!</b>\n\n"
        "{old_level} → <b>{new_level}</b>\n\n"
        "Mínimo de besitos: {min_besitos}"
    ),

    'mission_completed': (
        "✅ <b>Misión Completada</b>\n\n"
        "<b>{mission_name}</b>\n"
        "Recompensa: {besitos} besitos\n\n"
        "Usa /profile para reclamarla"
    ),

    'reward_unlocked': (
        "🎁 <b>Nueva Recompensa Disponible</b>\n\n"
        "<b>{reward_name}</b>\n"
        "{description}\n\n"
        "Visita /profile para verla"
    ),

    'streak_milestone': (
        "🔥 <b>¡Racha Épica!</b>\n\n"
        "Has reaccionado {days} días consecutivos\n\n"
        "¡Sigue así!"
    ),

    'streak_lost': (
        "💔 <b>Racha Perdida</b>\n\n"
        "Tu racha de {days} días expiró\n\n"
        "Reacciona hoy para empezar una nueva"
    )
}


class NotificationService:
    """
    Servicio de notificaciones del sistema de gamificación.

    Responsabilidades:
    - Enviar notificaciones formateadas a usuarios
    - Respetar configuración de notificaciones habilitadas
    - Implementar lógica de milestones inteligentes (evitar spam)
    - Manejar errores de envío (usuarios que bloquearon bot)
    """

    def __init__(self, bot: Bot, session: AsyncSession):
        """
        Inicializa el servicio de notificaciones.

        Args:
            bot: Instancia del bot de Telegram
            session: Sesión de base de datos
        """
        self.bot = bot
        self.session = session

    async def _send_notification(self, user_id: int, message: str) -> None:
        """
        Envía notificación si está habilitado en configuración.

        Args:
            user_id: ID del usuario a notificar
            message: Mensaje formateado en HTML
        """
        config = await self.session.get(GamificationConfig, 1)
        if not config or not config.notifications_enabled:
            logger.debug(f"Notifications disabled, skipping notification to {user_id}")
            return

        try:
            await self.bot.send_message(user_id, message, parse_mode="HTML")
            logger.info(f"Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")

    async def notify_level_up(
        self,
        user_id: int,
        old_level: Level,
        new_level: Level
    ) -> None:
        """
        Notifica al usuario que subió de nivel.

        Args:
            user_id: ID del usuario
            old_level: Nivel anterior
            new_level: Nuevo nivel alcanzado
        """
        message = NOTIFICATION_TEMPLATES['level_up'].format(
            old_level=old_level.name,
            new_level=new_level.name,
            min_besitos=new_level.min_besitos
        )
        await self._send_notification(user_id, message)

    async def notify_mission_completed(
        self,
        user_id: int,
        mission: Mission
    ) -> None:
        """
        Notifica al usuario que completó una misión.

        Args:
            user_id: ID del usuario
            mission: Misión completada
        """
        message = NOTIFICATION_TEMPLATES['mission_completed'].format(
            mission_name=mission.name,
            besitos=mission.besitos_reward
        )
        await self._send_notification(user_id, message)

    async def notify_reward_unlocked(
        self,
        user_id: int,
        reward: Reward
    ) -> None:
        """
        Notifica al usuario que desbloqueó una recompensa.

        Args:
            user_id: ID del usuario
            reward: Recompensa desbloqueada
        """
        message = NOTIFICATION_TEMPLATES['reward_unlocked'].format(
            reward_name=reward.name,
            description=reward.description
        )
        await self._send_notification(user_id, message)

    async def notify_streak_milestone(
        self,
        user_id: int,
        days: int
    ) -> None:
        """
        Notifica milestone de racha (solo en hitos específicos).

        Solo notifica en: 7, 14, 30, 60, 100 días para evitar spam.

        Args:
            user_id: ID del usuario
            days: Número de días de racha actual
        """
        # Solo notificar en milestones específicos
        milestones = [7, 14, 30, 60, 100]
        if days not in milestones:
            logger.debug(f"Streak {days} days is not a milestone, skipping notification")
            return

        message = NOTIFICATION_TEMPLATES['streak_milestone'].format(days=days)
        await self._send_notification(user_id, message)

    async def notify_streak_lost(
        self,
        user_id: int,
        days: int
    ) -> None:
        """
        Notifica racha perdida (solo si era significativa).

        Solo notifica si la racha era >= 7 días.

        Args:
            user_id: ID del usuario
            days: Número de días de racha perdida
        """
        # Solo notificar si racha era significativa
        if days < 7:
            logger.debug(f"Streak {days} days too short, skipping lost notification")
            return

        message = NOTIFICATION_TEMPLATES['streak_lost'].format(days=days)
        await self._send_notification(user_id, message)
