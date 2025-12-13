"""
Free Flow Handler - Solicitud de acceso al canal Free.

Flujo para que usuarios soliciten acceso Free y esperen aprobación automática.
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.start import user_router
from bot.services.container import ServiceContainer

logger = logging.getLogger(__name__)


@user_router.callback_query(F.data == "user:request_free")
async def callback_request_free(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Procesa solicitud de acceso al canal Free.

    Crea la solicitud y notifica al usuario del tiempo de espera.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    logger.info(f"📺 Usuario {user_id} solicitando acceso Free")

    container = ServiceContainer(session, callback.bot)

    # Verificar que canal Free está configurado
    if not await container.channel.is_free_channel_configured():
        await callback.answer(
            "⚠️ Canal Free no está configurado. Contacta al administrador.",
            show_alert=True
        )
        return

    # Verificar si ya tiene solicitud pendiente
    existing_request = await container.subscription.get_free_request(user_id)

    if existing_request:
        # Calcular tiempo restante
        from datetime import datetime, timezone, timedelta

        wait_time_minutes = await container.config.get_wait_time()
        time_since_request = (datetime.now(timezone.utc) - existing_request.request_date).total_seconds() / 60
        minutes_remaining = max(0, int(wait_time_minutes - time_since_request))

        try:
            await callback.message.edit_text(
                f"⏱️ <b>Solicitud Pendiente</b>\n\n"
                f"Ya tienes una solicitud en proceso.\n\n"
                f"Tiempo transcurrido: <b>{int(time_since_request)} minutos</b>\n"
                f"Tiempo restante: <b>{minutes_remaining} minutos</b>\n\n"
                f"Recibirás el link de acceso automáticamente cuando el tiempo se cumpla.\n\n"
                f"💡 <i>Puedes cerrar este chat, te notificaré cuando esté listo.</i>",
                parse_mode="HTML"
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                logger.error(f"Error editando mensaje: {e}")

        await callback.answer()
        return

    # Crear nueva solicitud
    request = await container.subscription.create_free_request(user_id)
    wait_time = await container.config.get_wait_time()

    try:
        await callback.message.edit_text(
            f"✅ <b>Solicitud Recibida</b>\n\n"
            f"Tu solicitud de acceso al canal Free ha sido registrada.\n\n"
            f"⏱️ Tiempo de espera: <b>{wait_time} minutos</b>\n\n"
            f"📨 Recibirás un mensaje con el link de invitación cuando el tiempo se cumpla.\n\n"
            f"💡 <i>No necesitas hacer nada más, el proceso es automático.</i>\n\n"
            f"Puedes cerrar este chat, te notificaré cuando esté listo! 🔔",
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje: {e}")

    await callback.answer("✅ Solicitud creada")

    logger.info(f"✅ Solicitud Free creada para user {user_id} (wait: {wait_time}min)")
