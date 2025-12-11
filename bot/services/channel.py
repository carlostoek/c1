"""
Channel Service - Gestión de canales VIP y Free.

Responsabilidades:
- Configuración de canales (IDs, validación)
- Verificación de permisos del bot
- Envío de publicaciones a canales
- Validación de que canales estén configurados
"""
import logging
from typing import Optional, Tuple

from aiogram import Bot
from aiogram.types import Message, Chat
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import BotConfig

logger = logging.getLogger(__name__)


class ChannelService:
    """
    Service para gestionar canales VIP y Free.

    Flujo típico:
    1. Admin configura canal → setup_channel()
    2. Bot verifica permisos → verify_bot_permissions()
    3. Admin envía publicación → send_to_channel()
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
        logger.debug("✅ ChannelService inicializado")

    # ===== CONFIGURACIÓN DE CANALES =====

    async def get_bot_config(self) -> BotConfig:
        """
        Obtiene la configuración del bot (singleton).

        Returns:
            BotConfig: Configuración global

        Raises:
            RuntimeError: Si BotConfig no existe en BD
        """
        config = await self.session.get(BotConfig, 1)

        if config is None:
            # Esto no debería pasar (init_db crea el registro)
            raise RuntimeError("BotConfig no encontrado en base de datos")

        return config

    async def setup_vip_channel(self, channel_id: str) -> Tuple[bool, str]:
        """
        Configura el canal VIP.

        Validaciones:
        - Verifica que el canal existe
        - Verifica que el bot es admin del canal
        - Verifica permisos necesarios (invite users)

        Args:
            channel_id: ID del canal (ej: "-1001234567890")

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        # Verificar formato del ID
        if not channel_id.startswith("-100"):
            return False, "❌ ID de canal inválido (debe empezar con -100)"

        # Verificar que el canal existe y bot es admin
        try:
            chat = await self.bot.get_chat(channel_id)
        except TelegramBadRequest:
            return False, "❌ Canal no encontrado. Verifica el ID."
        except TelegramForbiddenError:
            return False, "❌ Bot no tiene acceso al canal. Agrégalo como administrador."
        except Exception as e:
            logger.error(f"Error al obtener chat {channel_id}: {e}")
            return False, f"❌ Error: {str(e)}"

        # Verificar permisos del bot
        is_valid, perm_message = await self.verify_bot_permissions(channel_id)
        if not is_valid:
            return False, perm_message

        # Guardar en configuración
        config = await self.get_bot_config()
        config.vip_channel_id = channel_id

        await self.session.commit()

        logger.info(f"✅ Canal VIP configurado: {channel_id} ({chat.title})")

        return True, f"✅ Canal VIP configurado: <b>{chat.title}</b>"

    async def setup_free_channel(self, channel_id: str) -> Tuple[bool, str]:
        """
        Configura el canal Free.

        Validaciones idénticas a setup_vip_channel().

        Args:
            channel_id: ID del canal

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        # Validaciones idénticas
        if not channel_id.startswith("-100"):
            return False, "❌ ID de canal inválido (debe empezar con -100)"

        try:
            chat = await self.bot.get_chat(channel_id)
        except TelegramBadRequest:
            return False, "❌ Canal no encontrado. Verifica el ID."
        except TelegramForbiddenError:
            return False, "❌ Bot no tiene acceso al canal. Agrégalo como administrador."
        except Exception as e:
            logger.error(f"Error al obtener chat {channel_id}: {e}")
            return False, f"❌ Error: {str(e)}"

        is_valid, perm_message = await self.verify_bot_permissions(channel_id)
        if not is_valid:
            return False, perm_message

        # Guardar en configuración
        config = await self.get_bot_config()
        config.free_channel_id = channel_id

        await self.session.commit()

        logger.info(f"✅ Canal Free configurado: {channel_id} ({chat.title})")

        return True, f"✅ Canal Free configurado: <b>{chat.title}</b>"

    async def verify_bot_permissions(self, channel_id: str) -> Tuple[bool, str]:
        """
        Verifica que el bot tiene los permisos necesarios en el canal.

        Permisos requeridos:
        - can_invite_users: Para crear invite links
        - can_post_messages: Para enviar publicaciones (canales solamente)

        Args:
            channel_id: ID del canal

        Returns:
            Tuple[bool, str]: (tiene_permisos, mensaje)
        """
        try:
            # Obtener información del bot en el chat
            bot_member = await self.bot.get_chat_member(
                chat_id=channel_id,
                user_id=self.bot.id
            )

            # Verificar que es admin
            if bot_member.status not in ["administrator", "creator"]:
                return False, (
                    "❌ Bot no es administrador del canal. "
                    "Agrégalo como admin con permisos de invitación."
                )

            # Verificar permisos específicos
            if not bot_member.can_invite_users:
                return False, (
                    "❌ Bot no tiene permiso para invitar usuarios. "
                    "Actívalo en la configuración de administradores."
                )

            # Para canales (no supergrupos), verificar can_post_messages
            chat = await self.bot.get_chat(channel_id)
            if chat.type == "channel":
                if not bot_member.can_post_messages:
                    return False, (
                        "❌ Bot no tiene permiso para publicar mensajes. "
                        "Actívalo en la configuración de administradores."
                    )

            return True, "✅ Bot tiene todos los permisos necesarios"

        except Exception as e:
            logger.error(f"Error al verificar permisos en {channel_id}: {e}")
            return False, f"❌ Error al verificar permisos: {str(e)}"

    # ===== VERIFICACIÓN DE CONFIGURACIÓN =====

    async def is_vip_channel_configured(self) -> bool:
        """
        Verifica si el canal VIP está configurado.

        Returns:
            True si configurado, False si no
        """
        config = await self.get_bot_config()
        return config.vip_channel_id is not None and config.vip_channel_id != ""

    async def is_free_channel_configured(self) -> bool:
        """
        Verifica si el canal Free está configurado.

        Returns:
            True si configurado, False si no
        """
        config = await self.get_bot_config()
        return config.free_channel_id is not None and config.free_channel_id != ""

    async def get_vip_channel_id(self) -> Optional[str]:
        """
        Retorna el ID del canal VIP configurado.

        Returns:
            ID del canal, o None si no configurado
        """
        config = await self.get_bot_config()
        return config.vip_channel_id if config.vip_channel_id else None

    async def get_free_channel_id(self) -> Optional[str]:
        """
        Retorna el ID del canal Free configurado.

        Returns:
            ID del canal, o None si no configurado
        """
        config = await self.get_bot_config()
        return config.free_channel_id if config.free_channel_id else None

    # ===== ENVÍO DE MENSAJES =====

    async def send_to_channel(
        self,
        channel_id: str,
        text: Optional[str] = None,
        photo: Optional[str] = None,
        video: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, str, Optional[Message]]:
        """
        Envía un mensaje al canal especificado.

        Soporta:
        - Solo texto
        - Solo foto (con caption opcional)
        - Solo video (con caption opcional)

        Args:
            channel_id: ID del canal
            text: Texto del mensaje
            photo: File ID o URL de foto
            video: File ID o URL de video
            **kwargs: Parámetros adicionales (parse_mode, etc)

        Returns:
            Tuple[bool, str, Optional[Message]]:
                - bool: éxito
                - str: mensaje descriptivo
                - Optional[Message]: mensaje enviado (si éxito)
        """
        try:
            sent_message = None

            # Determinar tipo de mensaje
            if photo:
                # Mensaje con foto
                sent_message = await self.bot.send_photo(
                    chat_id=channel_id,
                    photo=photo,
                    caption=text,
                    **kwargs
                )
            elif video:
                # Mensaje con video
                sent_message = await self.bot.send_video(
                    chat_id=channel_id,
                    video=video,
                    caption=text,
                    **kwargs
                )
            elif text:
                # Solo texto
                sent_message = await self.bot.send_message(
                    chat_id=channel_id,
                    text=text,
                    **kwargs
                )
            else:
                return False, "❌ Debes proporcionar texto, foto o video", None

            logger.info(f"✅ Mensaje enviado al canal {channel_id}")
            return True, "✅ Publicación enviada correctamente", sent_message

        except TelegramForbiddenError:
            return False, "❌ Bot no tiene permiso para publicar en el canal", None
        except TelegramBadRequest as e:
            return False, f"❌ Error al enviar: {str(e)}", None
        except Exception as e:
            logger.error(f"Error al enviar mensaje a {channel_id}: {e}")
            return False, f"❌ Error inesperado: {str(e)}", None

    async def forward_to_channel(
        self,
        channel_id: str,
        from_chat_id: int,
        message_id: int
    ) -> Tuple[bool, str]:
        """
        Reenvía un mensaje a un canal.

        Útil para broadcasting: admin reenvía mensaje a canales.

        Args:
            channel_id: ID del canal destino
            from_chat_id: ID del chat origen
            message_id: ID del mensaje a reenviar

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            await self.bot.forward_message(
                chat_id=channel_id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )

            logger.info(f"✅ Mensaje reenviado al canal {channel_id}")
            return True, "✅ Mensaje reenviado correctamente"

        except TelegramForbiddenError:
            return False, "❌ Bot no tiene permiso para reenviar al canal"
        except Exception as e:
            logger.error(f"Error al reenviar a {channel_id}: {e}")
            return False, f"❌ Error: {str(e)}"

    async def copy_to_channel(
        self,
        channel_id: str,
        from_chat_id: int,
        message_id: int
    ) -> Tuple[bool, str]:
        """
        Copia un mensaje a un canal (sin "Forwarded from").

        Diferencia con forward:
        - forward muestra "Forwarded from Chat X"
        - copy envía como nuevo mensaje (sin firma de origen)

        Args:
            channel_id: ID del canal destino
            from_chat_id: ID del chat origen
            message_id: ID del mensaje a copiar

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            await self.bot.copy_message(
                chat_id=channel_id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )

            logger.info(f"✅ Mensaje copiado al canal {channel_id}")
            return True, "✅ Mensaje copiado correctamente"

        except TelegramForbiddenError:
            return False, "❌ Bot no tiene permiso para publicar en el canal"
        except Exception as e:
            logger.error(f"Error al copiar a {channel_id}: {e}")
            return False, f"❌ Error: {str(e)}"

    # ===== INFORMACIÓN DE CANALES =====

    async def get_channel_info(self, channel_id: str) -> Optional[Chat]:
        """
        Obtiene información del canal.

        Args:
            channel_id: ID del canal

        Returns:
            Chat si existe, None si error
        """
        try:
            chat = await self.bot.get_chat(channel_id)
            return chat
        except Exception as e:
            logger.error(f"Error al obtener info de canal {channel_id}: {e}")
            return None

    async def get_channel_member_count(self, channel_id: str) -> Optional[int]:
        """
        Obtiene cantidad de miembros del canal.

        Args:
            channel_id: ID del canal

        Returns:
            Cantidad de miembros, o None si error
        """
        try:
            count = await self.bot.get_chat_member_count(channel_id)
            return count
        except Exception as e:
            logger.error(f"Error al obtener miembros de {channel_id}: {e}")
            return None
