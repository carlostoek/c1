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

        # Notificar tiempo restante con progreso visual
        if request:
            from bot.utils.formatters import format_progress_with_time

            wait_time = await container.config.get_wait_time()
            minutes_since = request.minutes_since_request()
            minutes_remaining = max(0, wait_time - minutes_since)

            # Generar barra de progreso
            progress_bar = format_progress_with_time(minutes_remaining, wait_time, length=15)

            try:
                # Mostrar typing indicator
                await join_request.bot.send_chat_action(
                    chat_id=user_id,
                    action="typing"
                )

                await join_request.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"ℹ️ <b>Ya Tienes Una Solicitud Pendiente</b>\n\n"
                        f"📺 Canal: <b>{channel_name}</b>\n\n"
                        f"No es necesario solicitar de nuevo. Tu solicitud anterior sigue activa:\n\n"
                        f"<b>Progreso de Aprobación:</b>\n"
                        f"{progress_bar}\n\n"
                        f"⏰ <b>Tiempo Estimado:</b>\n"
                        f"• Tiempo transcurrido: <b>{minutes_since} min</b>\n"
                        f"• Tiempo restante: <b>{minutes_remaining} min</b>\n"
                        f"• Total configurado: <b>{wait_time} min</b>\n\n"
                        f"✅ Serás aprobado <b>automáticamente</b> en {minutes_remaining} minutos.\n"
                        f"No es necesario hacer nada, solo espera. 🎯"
                    ),
                    parse_mode="HTML"
                )

                # Auto-reaccionar con ❤️ al mensaje del join request
                try:
                    await join_request.bot.send_reaction(
                        chat_id=user_id,
                        message_id=join_request.message_id if hasattr(join_request, 'message_id') else None,
                        emoji="❤️"
                    )
                except Exception as e:
                    logger.debug(f"⚠️ No se pudo reaccionar: {e}")

                logger.info(f"✅ Notificación duplicada enviada a user {user_id} con progreso visual")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo notificar duplicada a user {user_id}: {e}")

        return

    # Solicitud nueva creada exitosamente
    logger.info(f"✅ Nueva solicitud Free registrada: user {user_id}")

    # Obtener tiempo de espera
    wait_time = await container.config.get_wait_time()

    # Mostrar typing indicator
    try:
        await join_request.bot.send_chat_action(
            chat_id=user_id,
            action="typing"
        )
    except Exception as e:
        logger.debug(f"⚠️ No se pudo enviar typing indicator: {e}")

    # Enviar notificación automática mejorada
    try:
        await join_request.bot.send_message(
            chat_id=user_id,
            text=(
                f"👋 <b>¡Solicitud de Acceso Free Registrada!</b>\n\n"
                f"📺 Canal: <b>{channel_name}</b>\n\n"
                f"✅ Tu solicitud ha sido registrada en el sistema.\n\n"
                f"⏰ <b>Tiempo de Espera:</b> {wait_time} minutos\n\n"
                f"<b>¿Qué sucede ahora?</b>\n"
                f"1. Tu solicitud está en la cola de aprobación\n"
                f"2. En aproximadamente {wait_time} minutos serás aprobado automáticamente\n"
                f"3. Recibirás una notificación cuando sea aprobada\n"
                f"4. Entonces podrás acceder al canal Free\n\n"
                f"💡 <b>Tips:</b>\n"
                f"• Mantén el chat abierto para recibir notificaciones\n"
                f"• No necesitas hacer nada más, es automático\n"
                f"• Si hay problema, contacta al soporte\n\n"
                f"¡Gracias por tu paciencia! ⏳"
            ),
            parse_mode="HTML"
        )

        # Auto-reaccionar con ❤️
        try:
            await join_request.bot.send_reaction(
                chat_id=user_id,
                message_id=None,  # No se puede reaccionar a ChatJoinRequest
                emoji="❤️"
            )
        except Exception as e:
            logger.debug(f"⚠️ No se pudo reaccionar: {e}")

        logger.info(
            f"✅ Usuario {user_id} notificado | "
            f"Aprobación automática en {wait_time} min"
        )
    except Exception as e:
        logger.warning(
            f"⚠️ No se pudo notificar a user {user_id}, pero solicitud registrada: {e}"
        )
