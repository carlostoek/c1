"""
VIP Flow Handler - Canje de tokens de invitación.

Flujo para que usuarios canjeen tokens VIP y reciban invite link.
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.start import user_router
from bot.states.user import TokenRedemptionStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@user_router.callback_query(F.data == "user:redeem_token")
async def callback_redeem_token(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el flujo de canje de token VIP.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    user_id = callback.from_user.id
    logger.info(f"🎟️ Usuario {user_id} iniciando canje de token")

    # Mostrar typing indicator
    await callback.bot.send_chat_action(
        chat_id=callback.message.chat.id,
        action="typing"
    )

    # Verificar que canal VIP está configurado
    container = ServiceContainer(session, callback.bot)

    if not await container.channel.is_vip_channel_configured():
        await callback.answer(
            "⚠️ Canal VIP no está configurado. Contacta al administrador.",
            show_alert=True
        )
        return

    # Entrar en estado FSM
    await state.set_state(TokenRedemptionStates.waiting_for_token)

    try:
        await callback.message.edit_text(
            "🎟️ <b>Canjear Token VIP</b>\n\n"
            "Por favor, envíe su token de invitación.\n\n"
            "El token tiene este formato:\n"
            "<code>A1b2C3d4E5f6G7h8</code>\n\n"
            "⏰ <b>Nota:</b> El token expira en 24 horas desde su creación.\n\n"
            "👉 Copie y pegue su token aquí:\n"
            "⏳ Esperando su token...",
            reply_markup=create_inline_keyboard([
                [{"text": "❌ Cancelar", "callback_data": "user:cancel"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje: {e}")

    await callback.answer()


@user_router.message(TokenRedemptionStates.waiting_for_token)
async def process_token_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el token enviado por el usuario.

    Valida el token, lo canjea y envía invite link.

    Args:
        message: Mensaje con el token
        session: Sesión de BD
        state: FSM context
    """
    user_id = message.from_user.id
    token_str = message.text.strip()

    logger.info(f"🎟️ Usuario {user_id} canjeando token: {token_str[:8]}...")

    # Los middlewares globales se encargan de:
    # - Typing indicator (TypingIndicatorMiddleware)
    # - Auto-reacción con ❤️ (AutoReactionMiddleware)

    container = ServiceContainer(session, message.bot)

    # Intentar canjear token
    success, msg, subscriber = await container.subscription.redeem_vip_token(
        token_str=token_str,
        user_id=user_id
    )

    if not success:
        # Token inválido - Diferenciar tipos de error
        error_messages = {
            "no_encontrado": (
                "❌ <b>Token No Encontrado</b>\n\n"
                "El token que ingresaste no existe en nuestro sistema.\n\n"
                "Verifica que hayas copiado correctamente el token.\n"
                "Asegúrate de que tenga este formato:\n"
                "<code>A1b2C3d4E5f6G7h8</code>\n\n"
                "Si el problema persiste, contacta al administrador."
            ),
            "ya_usado": (
                "⚠️ <b>Token Ya Fue Utilizado</b>\n\n"
                "Este token ya fue canjeado anteriormente.\n\n"
                "Cada token solo puede usarse una sola vez.\n\n"
                "Si crees que esto es un error, contacta al administrador para solicitar un nuevo token."
            ),
            "expirado": (
                "⏰ <b>Token Expirado</b>\n\n"
                "Este token ha expirado y ya no es válido.\n\n"
                "Los tokens tienen una duración de 24 horas desde su creación.\n\n"
                "Solicita un nuevo token al administrador."
            ),
            "default": (
                "❌ <b>Token Inválido</b>\n\n"
                f"{msg}\n\n"
                "Verifica el token e intenta nuevamente.\n\n"
                "Si el problema persiste, contacta al administrador."
            )
        }

        # Determinar tipo de error por el mensaje
        error_type = "default"
        if "no encontrado" in msg.lower() or "no existe" in msg.lower():
            error_type = "no_encontrado"
        elif "ya fue usado" in msg.lower() or "ya fue utilizado" in msg.lower():
            error_type = "ya_usado"
        elif "expirado" in msg.lower():
            error_type = "expirado"

        await message.answer(
            error_messages.get(error_type, error_messages["default"]),
            parse_mode="HTML"
        )
        # Mantener estado para reintentar
        return

    # Token válido: crear invite link
    vip_channel_id = await container.channel.get_vip_channel_id()

    try:
        invite_link = await container.subscription.create_invite_link(
            channel_id=vip_channel_id,
            user_id=user_id,
            expire_hours=1  # Link expira en 1 hora
        )

        # Calcular días restantes
        if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
            from datetime import datetime, timezone

            # Asegurar que expiry_date tiene timezone
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                # Si es naive, asumimos UTC
                expiry = expiry.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)
        else:
            days_remaining = 0

        await message.answer(
            f"🎉 <b>¡Token Canjeado Exitosamente!</b>\n\n"
            f"✅ Su acceso VIP está ahora <b>ACTIVO</b>\n"
            f"⏱️ Duración: <b>{days_remaining} días</b> de acceso exclusivo\n\n"
            f"👇 Haga clic para unirse al canal VIP:\n"
            f"{invite_link.invite_link}\n\n"
            f"<b>⚡ Detalles Importantes:</b>\n"
            f"• ⏳ El link expira en 1 hora\n"
            f"• 🔐 Solo puede usarlo 1 vez\n"
            f"• 🚫 No comparta el link con otros\n"
            f"• 📲 Si no puede hacer clic, cópielo y ábralo en su navegador\n\n"
            f"🎯 Disfrute del contenido exclusivo!",
            parse_mode="HTML"
        )

        # Limpiar estado
        await state.clear()

        logger.info(f"✅ Usuario {user_id} obtuvo acceso VIP ({days_remaining} días)")

    except Exception as e:
        logger.error(f"Error creando invite link para user {user_id}: {e}", exc_info=True)

        await message.answer(
            "✅ <b>Token Canjeado Correctamente</b>\n\n"
            "⚠️ Sin embargo, ocurrió un problema técnico al crear el link de invitación.\n\n"
            "Su suscripción VIP está activa y su token ha sido registrado.\n\n"
            "⏱️ Por favor, contacte al administrador para obtener acceso al canal VIP.\n"
            "Su solicitud será procesada manualmente.",
            parse_mode="HTML"
        )
        await state.clear()


@user_router.callback_query(F.data == "user:cancel")
async def callback_cancel(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Cancela el flujo actual y limpia estado FSM.

    Args:
        callback: Callback query
        state: FSM context
    """
    await state.clear()

    try:
        await callback.message.edit_text(
            "❌ Operación cancelada.\n\n"
            "Usa /start para volver al menú principal.",
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje: {e}")

    await callback.answer()
