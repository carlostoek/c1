"""
Notification Service - Servicio centralizado de notificaciones.

Maneja el envío de notificaciones al usuario con templates,
logging automático y sistema de RewardBatch.
"""
import logging
from typing import Optional, Dict, Any

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.notifications.types import NotificationType
from bot.notifications.templates import NotificationTemplates
from bot.notifications.batch import RewardBatch
from bot.database.models import NotificationTemplate

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio para enviar notificaciones a usuarios.

    Centraliza todo el envío de mensajes para:
    - Consistencia visual
    - Logging automático
    - Templates reutilizables
    - RewardBatch para agrupar recompensas

    Attributes:
        session: Sesión de BD
        bot: Instancia del bot
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el servicio de notificaciones.

        Args:
            session: Sesión de SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        self._session = session
        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def send(
        self,
        user_id: int,
        notification_type: NotificationType,
        context: Dict[str, Any],
        keyboard: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML",
    ) -> None:
        """
        Envía una notificación a un usuario.

        Args:
            user_id: ID del usuario
            notification_type: Tipo de notificación
            context: Variables para el template
            keyboard: Keyboard inline (opcional)
            parse_mode: Modo de parseo (default: HTML)

        Examples:
            >>> await service.send(
            ...     user_id=123,
            ...     notification_type=NotificationType.POINTS_EARNED,
            ...     context={
            ...         "amount": 50,
            ...         "reason": "Primera reacción",
            ...         "total_besitos": 150
            ...     }
            ... )
        """
        try:
            # Obtener template (primero de BD, luego default)
            template_text = await self._get_template(notification_type)

            # Renderizar template
            message = self._render_template(template_text, context)

            # Enviar mensaje
            await self._bot.send_message(
                chat_id=user_id, text=message, reply_markup=keyboard, parse_mode=parse_mode
            )

            self._logger.info(f"📧 Notificación enviada: {notification_type.value} → User {user_id}")

        except Exception as e:
            self._logger.error(f"❌ Error enviando notificación a {user_id}: {e}", exc_info=True)

    async def send_reward_batch(
        self, batch: RewardBatch, keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """
        Envía un lote de recompensas unificado.

        Args:
            batch: RewardBatch con las recompensas
            keyboard: Keyboard inline (opcional)

        Examples:
            >>> batch = RewardBatch(user_id=123, action="Reaccionaste a un mensaje")
            >>> batch.add_besitos(50)
            >>> batch.add_badge("🔥 Hot Streak")
            >>> await service.send_reward_batch(batch)
        """
        if batch.is_empty:
            self._logger.debug(f"⚠️ RewardBatch vacío para user {batch.user_id}, no se envía")
            return

        try:
            # Formatear mensaje del batch
            message = batch.format_message()

            # Enviar
            await self._bot.send_message(
                chat_id=batch.user_id, text=message, reply_markup=keyboard, parse_mode="HTML"
            )

            self._logger.info(
                f"🎁 RewardBatch enviado: {batch.count} recompensas → User {batch.user_id}"
            )

        except Exception as e:
            self._logger.error(f"❌ Error enviando RewardBatch a {batch.user_id}: {e}", exc_info=True)

    async def send_welcome(
        self, user_id: int, first_name: str, role_name: str, role_emoji: str
    ) -> None:
        """
        Envía mensaje de bienvenida.

        Args:
            user_id: ID del usuario
            first_name: Nombre del usuario
            role_name: Nombre del rol
            role_emoji: Emoji del rol
        """
        await self.send(
            user_id=user_id,
            notification_type=NotificationType.WELCOME,
            context={"first_name": first_name, "role_name": role_name, "role_emoji": role_emoji},
        )

    async def send_besitos(
        self, user_id: int, amount: int, reason: str, total_besitos: int
    ) -> None:
        """
        Envía notificación de Besitos ganados.

        Args:
            user_id: ID del usuario
            amount: Cantidad ganada
            reason: Razón de la recompensa
            total_besitos: Total acumulado
        """
        await self.send(
            user_id=user_id,
            notification_type=NotificationType.POINTS_EARNED,
            context={
                "amount": amount,
                "reason": reason,
                "total_besitos": total_besitos,
            },
        )

    async def _get_template(self, notification_type: NotificationType) -> str:
        """
        Obtiene el template de notificación.

        Primero busca en BD (personalizado), luego usa default.

        Args:
            notification_type: Tipo de notificación

        Returns:
            String del template
        """
        # Buscar template personalizado en BD
        result = await self._session.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.type == notification_type.value,
                NotificationTemplate.active == True,
            )
        )
        custom_template = result.scalar_one_or_none()

        if custom_template:
            self._logger.debug(f"📝 Usando template personalizado: {notification_type.value}")
            return custom_template.content

        # Usar template default
        self._logger.debug(f"📝 Usando template default: {notification_type.value}")

        # Mapear tipo a nombre de template
        template_map = {
            NotificationType.WELCOME: "WELCOME_DEFAULT",
            NotificationType.POINTS_EARNED: "BESITOS_EARNED",
            NotificationType.BADGE_UNLOCKED: "BADGE_UNLOCKED",
            NotificationType.RANK_UP: "RANK_UP",
            NotificationType.VIP_ACTIVATED: "VIP_ACTIVATED",
            NotificationType.VIP_EXPIRING_SOON: "VIP_EXPIRING_SOON",
            NotificationType.VIP_EXPIRED: "VIP_EXPIRED",
            NotificationType.DAILY_LOGIN: "DAILY_LOGIN",
            NotificationType.STREAK_MILESTONE: "STREAK_MILESTONE",
            NotificationType.REFERRAL_SUCCESS: "REFERRAL_SUCCESS",
            NotificationType.INFO: "INFO",
            NotificationType.WARNING: "WARNING",
            NotificationType.ERROR: "ERROR",
        }

        template_name = template_map.get(notification_type, "INFO")
        return getattr(NotificationTemplates, template_name)

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Renderiza un template con el contexto.

        Args:
            template: String del template
            context: Variables a reemplazar

        Returns:
            String renderizado
        """
        try:
            return template.format(**context)
        except KeyError as e:
            self._logger.error(f"❌ Variable faltante en template: {e}")
            # Retornar template sin renderizar (mejor que crashear)
            return template
