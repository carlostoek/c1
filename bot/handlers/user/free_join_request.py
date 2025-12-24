"""
Free Join Request Handler - ChatJoinRequest del canal Free.

Flujo:
1. Usuario hace click en "Unirse" en el canal Free
2. Telegram envía ChatJoinRequest al bot
3. Bot verifica canal correcto
4. Si duplicada: Declina + notifica tiempo restante
5. Si nueva: Registra en BD + envía mensaje de espera
6. Background task aprobará después de N minutos
"""
import logging
from aiogram import Router, F
from aiogram.types import ChatJoinRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.services.container import ServiceContainer

logger = logging.getLogger(__name__)

free_join_router = Router(name="free_join")
free_join_router.chat_join_request.middleware(DatabaseMiddleware())


@free_join_router.chat_join_request(F.chat.type.in_({"channel", "supergroup"}))
async def handle_free_join_request(
    join_request: ChatJoinRequest,
    session: AsyncSession
):
    """
    Handler para ChatJoinRequest del canal Free.

    Valida canal, verifica duplicados, registra solicitud y envía notificación.

    Args:
        join_request: Solicitud de unión al canal
        session: Sesión de base de datos (inyectada por middleware)
    """
    user_id = join_request.from_user.id
    user_name = join_request.from_user.first_name or "Usuario"
    from_chat_id = str(join_request.chat.id)
    channel_name = join_request.chat.title or "Canal Free"

    logger.info(f"📺 ChatJoinRequest: User={user_id} | Chat={from_chat_id}")

    container = ServiceContainer(session, join_request.bot)

    # Verificar canal configurado
    configured_channel_id = await container.channel.get_free_channel_id()

    if not configured_channel_id:
        logger.warning("⚠️ Canal Free no configurado")
        try:
            await join_request.decline()
        except Exception as e:
            logger.error(f"❌ Error declinando (canal no configurado): {e}")
        return

    # Verificar canal correcto (SEGURIDAD)
    if configured_channel_id != from_chat_id:
        logger.warning(
            f"⚠️ Solicitud desde canal no autorizado: {from_chat_id} "
            f"(esperado: {configured_channel_id})"
        )
        try:
            await join_request.decline()
        except Exception as e:
            logger.error(f"❌ Error declinando (canal no autorizado): {e}")
        return

    # Crear solicitud (verifica duplicados internamente)
    success, message, request = await container.subscription.create_free_request_from_join_request(
        user_id=user_id,
        from_chat_id=from_chat_id
    )

    if not success:
        # Solicitud duplicada
        logger.info(f"⚠️ Solicitud duplicada: user {user_id}")

        # Declinar
        try:
            await join_request.decline()
        except Exception as e:
            logger.error(f"❌ Error declinando duplicada: {e}")

        # Notificar tiempo restante
        if request:
            wait_time = await container.config.get_wait_time()
            minutes_since = request.minutes_since_request()
            minutes_remaining = max(0, wait_time - minutes_since)

            try:
                await join_request.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"⚠️ <b>Solicitud Duplicada</b>\n\n"
                        f"Ya tienes una solicitud pendiente para el canal {channel_name}.\n\n"
                        f"⏱️ Tiempo transcurrido: <b>{minutes_since} min</b>\n"
                        f"⏱️ Tiempo restante: <b>{minutes_remaining} min</b>\n\n"
                        f"Serás aprobado automáticamente cuando se cumpla el tiempo de espera."
                    ),
                    parse_mode="HTML"
                )
                logger.info(f"✅ Notificación duplicada enviada a user {user_id}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo notificar duplicada a user {user_id}: {e}")

        return

    # Solicitud nueva creada exitosamente
    logger.info(f"✅ Nueva solicitud Free registrada: user {user_id}")

    # Obtener tiempo de espera
    wait_time = await container.config.get_wait_time()

    # Enviar notificación automática
    notification_sent = await container.subscription.send_free_request_notification(
        user_id=user_id,
        user_name=user_name,
        channel_name=channel_name,
        wait_time_minutes=wait_time
    )

    if notification_sent:
        logger.info(
            f"✅ Usuario {user_id} notificado | "
            f"Aprobación automática en {wait_time} min"
        )
    else:
        logger.warning(
            f"⚠️ No se pudo notificar a user {user_id}, pero solicitud registrada"
        )
