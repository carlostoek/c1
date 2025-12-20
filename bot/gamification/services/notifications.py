"""
Sistema de notificaciones del módulo de gamificación.
"""

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Dict, Any

from bot.gamification.database.models import Mission, Reward, Level
from bot.gamification.config import GamificationConfig

logger = logging.getLogger(__name__)


NOTIFICATION_TEMPLATES = {
    'level_up': (
        "🎉 <b>¡Subiste de nivel!</b>\n\n"
        "{old_level_name} → <b>{new_level_name}</b>\n\n"
        "Mínimo de besitos: {min_besitos}"
    ),

    'mission_completed': (
        "✅ <b>Misión Completada</b>\n\n"
        "<b>{mission_name}</b>\n"
        "Recompensa: {besitos_reward} besitos\n\n"
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
    """Servicio de notificaciones."""

    def __init__(self, bot: Bot, session: AsyncSession):
        self.bot = bot
        self.session = session

    async def _is_notification_type_enabled(self, notification_type: str) -> bool:
        """Verifica si un tipo específico de notificación está habilitado."""
        # This would check specific notification type settings from environment/dynamic config
        # For now, using general notification setting from config
        notifications_enabled = await GamificationConfig.get_notifications_enabled(self.session)
        return notifications_enabled

    async def _send_notification(self, user_id: int, message: str, notification_type: str = None) -> bool:
        """Envía notificación si está habilitado."""
        # Verificar si las notificaciones están habilitadas globalmente
        if notification_type:
            is_enabled = await self._is_notification_type_enabled(notification_type)
            if not is_enabled:
                logger.debug(f"{notification_type} notifications disabled for user {user_id}, skipping message")
                return False

        try:
            await self.bot.send_message(user_id, message, parse_mode="HTML")
            logger.info(f"Notification {notification_type or 'generic'} sent to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")
            return False
    
    async def notify_level_up(self, user_id: int, old_level: Level, new_level: Level):
        """Notifica level-up."""
        if not old_level or not new_level:
            logger.warning(f"Missing level data for user {user_id}")
            return

        message = NOTIFICATION_TEMPLATES['level_up'].format(
            old_level_name=old_level.name,
            new_level_name=new_level.name,
            min_besitos=new_level.min_besitos
        )
        return await self._send_notification(user_id, message, 'level_up')

    async def notify_mission_completed(self, user_id: int, mission: Mission):
        """Notifica misión completada."""
        if not mission:
            logger.warning(f"Missing mission data for user {user_id}")
            return

        message = NOTIFICATION_TEMPLATES['mission_completed'].format(
            mission_name=mission.name,
            besitos_reward=mission.besitos_reward
        )
        return await self._send_notification(user_id, message, 'mission_completed')

    async def notify_reward_unlocked(self, user_id: int, reward: Reward):
        """Notifica recompensa desbloqueada."""
        if not reward:
            logger.warning(f"Missing reward data for user {user_id}")
            return

        message = NOTIFICATION_TEMPLATES['reward_unlocked'].format(
            reward_name=reward.name,
            description=reward.description
        )
        return await self._send_notification(user_id, message, 'reward_unlocked')

    async def notify_streak_milestone(self, user_id: int, days: int):
        """Notifica milestone de racha."""
        # Solo notificar en milestones específicos
        milestones = [7, 14, 30, 60, 100]
        if days not in milestones:
            logger.debug(f"Streak milestone {days} not in target milestones, skipping notification")
            return

        message = NOTIFICATION_TEMPLATES['streak_milestone'].format(days=days)
        return await self._send_notification(user_id, message, 'streak_milestone')

    async def notify_streak_lost(self, user_id: int, days: int):
        """Notifica racha perdida."""
        # Solo notificar si racha era significativa
        if days < 7:
            logger.debug(f"Streak of {days} days is below threshold, skipping notification")
            return

        message = NOTIFICATION_TEMPLATES['streak_lost'].format(days=days)
        return await self._send_notification(user_id, message, 'streak_lost')