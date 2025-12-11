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
            "Por favor, envía tu token de invitación.\n\n"
            "El token tiene este formato:\n"
            "<code>A1b2C3d4E5f6G7h8</code>\n\n"
            "👉 Copia y pega tu token aquí:",
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

    container = ServiceContainer(session, message.bot)

    # Intentar canjear token
    success, msg, subscriber = await container.subscription.redeem_vip_token(
        token_str=token_str,
        user_id=user_id
    )

    if not success:
        # Token inválido
        await message.answer(
            f"{msg}\n\n"
            f"Verifica el token e intenta nuevamente.\n\n"
            f"Si el problema persiste, contacta al administrador.",
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
            days_remaining = max(0, (subscriber.expiry_date - datetime.now(timezone.utc)).days)
        else:
            days_remaining = 0

        await message.answer(
            f"✅ <b>Token Canjeado Exitosamente!</b>\n\n"
            f"🎉 Tu acceso VIP está activo\n"
            f"⏱️ Duración: <b>{days_remaining} días</b>\n\n"
            f"👇 Usa este link para unirte al canal VIP:\n"
            f"{invite_link.invite_link}\n\n"
            f"⚠️ <b>Importante:</b>\n"
            f"• El link expira en 1 hora\n"
            f"• Solo puedes usarlo 1 vez\n"
            f"• No lo compartas con otros\n\n"
            f"Disfruta del contenido exclusivo! 🚀",
            parse_mode="HTML"
        )

        # Limpiar estado
        await state.clear()

        logger.info(f"✅ Usuario {user_id} obtuvo acceso VIP ({days_remaining} días)")

    except Exception as e:
        logger.error(f"Error creando invite link para user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Error al crear el link de invitación.\n\n"
            "Tu token fue canjeado correctamente, pero hubo un problema técnico.\n"
            "Contacta al administrador.",
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
