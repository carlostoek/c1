"""
Broadcast Service - Gestión de broadcasting con gamificación.

Responsabilidades:
- Envío de publicaciones a canales con gamificación
- Construcción de inline keyboards de reacciones
- Registro de mensajes en BroadcastMessage
- Configuración de protección de contenido
"""
import logging
from typing import Optional, Dict, List, Tuple

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import BroadcastMessage
from bot.gamification.database.models import Reaction
from bot.services.channel import ChannelService
from bot.services.config import ConfigService

logger = logging.getLogger(__name__)


class BroadcastService:
    """
    Service para broadcasting con soporte de gamificación.

    Flujo típico:
    1. Admin configura gamificación (opcional)
    2. Service envía a canales con botones de reacción
    3. Registra mensaje en BD si gamificación habilitada
    4. Usuarios presionan botones → CustomReactionService procesa
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el service.

        Args:
            session: Sesión de base de datos
            bot: Instancia del bot de Telegram
        """
        self.session = session
        self.bot = bot
        self.channel_service = ChannelService(session, bot)
        self.config_service = ConfigService(session)
        logger.debug("✅ BroadcastService inicializado")

    async def send_broadcast_with_gamification(
        self,
        target: str,
        content_type: str,
        content_text: Optional[str] = None,
        media_file_id: Optional[str] = None,
        sent_by: int = 0,
        gamification_config: Optional[Dict] = None,
        content_protected: bool = False
    ) -> Dict:
        """
        Envía broadcast con configuración de gamificación.

        Args:
            target: "vip", "free", o "both"
            content_type: "text", "photo", "video"
            content_text: Texto del mensaje o caption
            media_file_id: File ID de Telegram (si es media)
            sent_by: User ID del admin que envía
            gamification_config: {
                "enabled": bool,
                "reaction_types": [1, 2, 3]  # IDs de Reaction
            }
            content_protected: Si proteger contra forwards

        Returns:
            {
                "success": bool,
                "channels_sent": List[str],
                "channels_failed": List[str],
                "broadcast_message_ids": List[int],  # IDs en BD
                "errors": List[str]
            }
        """
        logger.info(f"📤 Enviando broadcast: target={target}, gamif={gamification_config is not None}")

        # 1. Determinar canales destino
        channels = await self._get_target_channels(target)

        if not channels:
            logger.warning(f"⚠️ No hay canales configurados para target={target}")
            return {
                "success": False,
                "channels_sent": [],
                "channels_failed": [],
                "broadcast_message_ids": [],
                "errors": ["No hay canales configurados para este destino"]
            }

        # 2. Construir keyboard si gamificación habilitada
        keyboard = None
        reaction_config_list = None

        if gamification_config and gamification_config.get("enabled"):
            reaction_type_ids = gamification_config.get("reaction_types", [])

            if reaction_type_ids:
                keyboard = await self._build_reaction_keyboard(reaction_type_ids)
                reaction_config_list = await self._build_reaction_config(reaction_type_ids)
            else:
                logger.warning("⚠️ Gamificación habilitada pero sin reaction_types")

        # 3. Enviar mensaje a cada canal
        channels_sent = []
        channels_failed = []
        broadcast_message_ids = []
        errors = []

        for channel_name, channel_id in channels:
            try:
                # Preparar kwargs para envío
                send_kwargs = {}
                if keyboard:
                    send_kwargs["reply_markup"] = keyboard
                if content_protected:
                    send_kwargs["protect_content"] = True

                # Enviar según tipo de contenido
                if content_type == "photo":
                    success, msg, sent_message = await self.channel_service.send_to_channel(
                        channel_id=channel_id,
                        text=content_text,
                        photo=media_file_id,
                        **send_kwargs
                    )
                elif content_type == "video":
                    success, msg, sent_message = await self.channel_service.send_to_channel(
                        channel_id=channel_id,
                        text=content_text,
                        video=media_file_id,
                        **send_kwargs
                    )
                else:  # text
                    success, msg, sent_message = await self.channel_service.send_to_channel(
                        channel_id=channel_id,
                        text=content_text,
                        **send_kwargs
                    )

                if success and sent_message:
                    channels_sent.append(channel_name)
                    logger.info(f"✅ Enviado a {channel_name}")

                    # 4. Registrar en BroadcastMessage si gamificación habilitada
                    if gamification_config and gamification_config.get("enabled") and reaction_config_list:
                        broadcast_msg = BroadcastMessage(
                            message_id=sent_message.message_id,
                            chat_id=int(channel_id),
                            content_type=content_type,
                            content_text=content_text,
                            media_file_id=media_file_id,
                            sent_by=sent_by,
                            gamification_enabled=True,
                            reaction_buttons=reaction_config_list,
                            content_protected=content_protected,
                            total_reactions=0,
                            unique_reactors=0
                        )
                        self.session.add(broadcast_msg)
                        await self.session.flush()
                        broadcast_message_ids.append(broadcast_msg.id)
                        logger.debug(f"✅ BroadcastMessage registrado: id={broadcast_msg.id}")

                else:
                    channels_failed.append(channel_name)
                    errors.append(f"{channel_name}: {msg}")
                    logger.error(f"❌ Error en {channel_name}: {msg}")

            except Exception as e:
                channels_failed.append(channel_name)
                errors.append(f"{channel_name}: {str(e)}")
                logger.error(f"❌ Excepción en {channel_name}: {e}", exc_info=True)

        # Commit si hay registros en BD
        if broadcast_message_ids:
            await self.session.commit()

        # 5. Retornar resultados
        return {
            "success": len(channels_sent) > 0,
            "channels_sent": channels_sent,
            "channels_failed": channels_failed,
            "broadcast_message_ids": broadcast_message_ids,
            "errors": errors
        }

    async def _build_reaction_keyboard(
        self,
        reaction_type_ids: List[int]
    ) -> InlineKeyboardMarkup:
        """
        Construye teclado de botones de reacción.

        Args:
            reaction_type_ids: Lista de IDs de Reaction

        Returns:
            InlineKeyboardMarkup con botones (máximo 3 por fila)
        """
        # Obtener Reactions de BD
        stmt = select(Reaction).where(
            Reaction.id.in_(reaction_type_ids),
            Reaction.active == True
        ).order_by(Reaction.sort_order)

        result = await self.session.execute(stmt)
        reactions = result.scalars().all()

        if not reactions:
            logger.warning(f"⚠️ No se encontraron reacciones activas para IDs: {reaction_type_ids}")
            return InlineKeyboardMarkup(inline_keyboard=[])

        # Construir botones
        buttons = []
        for reaction in reactions:
            # Formato: "emoji label"
            emoji = reaction.button_emoji or reaction.emoji
            label = reaction.button_label or ""

            button_text = f"{emoji} {label}".strip() if label else emoji

            buttons.append(
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"react:{reaction.id}"
                )
            )

        # Organizar en filas (máximo 3 botones por fila)
        keyboard = []
        for i in range(0, len(buttons), 3):
            keyboard.append(buttons[i:i+3])

        logger.debug(f"✅ Keyboard construido: {len(buttons)} botones, {len(keyboard)} filas")

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def _build_reaction_config(
        self,
        reaction_type_ids: List[int]
    ) -> List[Dict]:
        """
        Construye JSON de configuración de reacciones.

        Args:
            reaction_type_ids: Lista de IDs de Reaction

        Returns:
            [
                {
                    "emoji": "👍",
                    "label": "Me Gusta",
                    "reaction_type_id": 1,
                    "besitos": 10
                },
                ...
            ]
        """
        # Obtener Reactions de BD
        stmt = select(Reaction).where(
            Reaction.id.in_(reaction_type_ids),
            Reaction.active == True
        ).order_by(Reaction.sort_order)

        result = await self.session.execute(stmt)
        reactions = result.scalars().all()

        config_list = []
        for reaction in reactions:
            config_list.append({
                "emoji": reaction.button_emoji or reaction.emoji,
                "label": reaction.button_label or "",
                "reaction_type_id": reaction.id,
                "besitos": reaction.besitos_value
            })

        logger.debug(f"✅ Reaction config construido: {len(config_list)} items")

        return config_list

    async def _get_target_channels(self, target: str) -> List[Tuple[str, str]]:
        """
        Obtiene IDs de canales según target.

        Args:
            target: "vip", "free", o "both"

        Returns:
            Lista de tuplas: [("VIP", "-1001234..."), ...]
        """
        channels = []

        if target in ["vip", "both"]:
            vip_id = await self.channel_service.get_vip_channel_id()
            if vip_id:
                channels.append(("VIP", vip_id))

        if target in ["free", "both"]:
            free_id = await self.channel_service.get_free_channel_id()
            if free_id:
                channels.append(("Free", free_id))

        logger.debug(f"✅ Canales destino para '{target}': {len(channels)}")

        return channels
