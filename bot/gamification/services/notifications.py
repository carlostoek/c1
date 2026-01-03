"""
Sistema de notificaciones del módulo de gamificación.

Este servicio gestiona el envío de notificaciones push a usuarios sobre:
- Level-ups (subida de nivel)
- Misiones completadas
- Recompensas desbloqueadas
- Milestones de rachas
- Rachas perdidas
- Milestones de besitos totales
"""

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import Mission, Reward, Level, GamificationConfig
from bot.gamification.config.economy import EconomyConfig
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio de notificaciones del sistema de gamificación.

    Responsabilidades:
    - Enviar notificaciones formateadas a usuarios
    - Respetar configuración de notificaciones habilitadas
    - Implementar lógica de milestones inteligentes (evitar spam)
    - Manejar errores de envío (usuarios que bloquearon bot)
    - Usar voz de Lucien para todas las notificaciones
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
            message: Mensaje formateado en HTML o texto plano
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
        # Buscar mensaje específico del nivel si existe
        level_key = f"LEVEL_UP_{new_level.order}"
        message = LucienMessages.profile(level_key, new_level=new_level.name)

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
        message = LucienMessages.missions(
            "MISSION_COMPLETED",
            mission_name=mission.name,
            reward=mission.besitos_reward
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
        # Usar mensaje de besitos para notificar recompensa desbloqueada
        message = (
            f"<b>Nueva Recompensa Disponible</b>\n\n"
            f"{reward.name}\n"
            f"{reward.description}\n\n"
            f"Visite su perfil para reclamarla."
        )
        await self._send_notification(user_id, message)

    async def notify_streak_milestone(
        self,
        user_id: int,
        days: int,
        bonus: float
    ) -> None:
        """
        Notifica milestone de racha (solo en hitos específicos).

        Solo notifica en milestones definidos en EconomyConfig.STREAK_MILESTONES.

        Args:
            user_id: ID del usuario
            days: Número de días de racha actual
            bonus: Cantidad de besitos de bonificación
        """
        # Solo notificar en milestones específicos
        if days not in EconomyConfig.STREAK_MILESTONES:
            logger.debug(f"Streak {days} days is not a milestone, skipping notification")
            return

        # Obtener message_key desde config
        milestone_info = EconomyConfig.STREAK_MILESTONES[days]
        message_key = milestone_info.get("message_key", f"MILESTONE_{days}")

        message = LucienMessages.streak(
            message_key,
            bonus=bonus
        )
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

        message = LucienMessages.streak("LOST", days=days)
        await self._send_notification(user_id, message)

    async def notify_besitos_milestone(
        self,
        user_id: int,
        total_besitos: int
    ) -> None:
        """
        Notifica milestone de besitos totales.

        Solo notifica si el total está en BESITOS_MILESTONES.

        Args:
            user_id: ID del usuario
            total_besitos: Total actual de besitos del usuario
        """
        # Verificar si es un milestone
        if not EconomyConfig.is_milestone(total_besitos):
            logger.debug(
                f"Besitos {total_besitos} is not a milestone, "
                f"skipping notification for user {user_id}"
            )
            return

        message = LucienMessages.besitos(
            "BESITO_EARNED_MILESTONE",
            amount=total_besitos
        )
        await self._send_notification(user_id, message)

        logger.info(
            f"Besitos milestone notification sent to user {user_id} "
            f"for {total_besitos} besitos"
        )
