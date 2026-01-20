"""
VIP Handlers - Gestión del canal VIP.

Handlers para:
- Submenú VIP
- Configuración del canal VIP
- Generación de tokens de invitación
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import ChannelSetupStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from config import Config

logger = logging.getLogger(__name__)


def vip_menu_keyboard(is_configured: bool) -> "InlineKeyboardMarkup":
    """
    Keyboard del submenú VIP.

    Args:
        is_configured: Si el canal VIP está configurado

    Returns:
        InlineKeyboardMarkup con opciones VIP
    """
    buttons = []

    if is_configured:
        buttons.extend([
            [{"text": "🎟️ Generar Token de Invitación", "callback_data": "vip:generate_token"}],
            [{"text": "📤 Enviar Publicación", "callback_data": "vip:broadcast"}],
            [{"text": "🔧 Reconfigurar Canal", "callback_data": "vip:setup"}],
        ])
    else:
        buttons.append([{"text": "⚙️ Configurar Canal VIP", "callback_data": "vip:setup"}])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:main"}])

    return create_inline_keyboard(buttons)


@admin_router.callback_query(F.data == "admin:vip")
async def callback_vip_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el submenú de gestión VIP.

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.debug(f"📺 Usuario {callback.from_user.id} abrió menú VIP")

    container = ServiceContainer(session, callback.bot)

    # Verificar si canal VIP está configurado
    is_configured = await container.channel.is_vip_channel_configured()

    if is_configured:
        vip_channel_id = await container.channel.get_vip_channel_id()

        # Obtener info del canal
        channel_info = await container.channel.get_channel_info(vip_channel_id)
        channel_name = channel_info.title if channel_info else "Canal VIP"

        text = (
            f"📺 <b>Gestión Canal VIP</b>\n\n"
            f"✅ Canal configurado: <b>{channel_name}</b>\n"
            f"ID: <code>{vip_channel_id}</code>\n\n"
            f"Selecciona una opción:"
        )
    else:
        text = (
            "📺 <b>Gestión Canal VIP</b>\n\n"
            "⚠️ Canal VIP no configurado\n\n"
            "Configura el canal para comenzar a generar tokens de invitación."
        )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=vip_menu_keyboard(is_configured),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje VIP: {e}")

    await callback.answer()


@admin_router.callback_query(F.data == "vip:setup")
async def callback_vip_setup(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el proceso de configuración del canal VIP.

    Entra en estado FSM esperando que el admin reenvíe un mensaje del canal.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} iniciando setup VIP")

    # Entrar en estado FSM
    await state.set_state(ChannelSetupStates.waiting_for_vip_channel)

    text = (
        "⚙️ <b>Configurar Canal VIP</b>\n\n"
        "Para configurar el canal VIP, necesito que:\n\n"
        "1️⃣ Vayas al canal VIP\n"
        "2️⃣ Reenvíes cualquier mensaje del canal a este chat\n"
        "3️⃣ Yo extraeré el ID automáticamente\n\n"
        "⚠️ <b>Importante:</b>\n"
        "- El bot debe ser administrador del canal\n"
        "- El bot debe tener permiso para invitar usuarios\n\n"
        "👉 Reenvía un mensaje del canal ahora..."
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "❌ Cancelar", "callback_data": "admin:vip"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje setup VIP: {e}")

    await callback.answer()


@admin_router.message(ChannelSetupStates.waiting_for_vip_channel)
async def process_vip_channel_forward(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el mensaje reenviado para configurar el canal VIP.

    Extrae el ID del canal del forward y lo configura.

    Args:
        message: Mensaje reenviado del canal
        session: Sesión de BD
        state: FSM context
    """
    # Verificar que es un forward de un canal
    if not message.forward_from_chat:
        await message.answer(
            "❌ Debes <b>reenviar</b> un mensaje del canal VIP.\n\n"
            "No me envíes el ID manualmente, reenvía un mensaje.",
            parse_mode="HTML"
        )
        return

    forward_chat = message.forward_from_chat

    # Verificar que es un canal (no grupo ni usuario)
    if forward_chat.type not in ["channel", "supergroup"]:
        await message.answer(
            "❌ El mensaje debe ser de un <b>canal</b> o <b>supergrupo</b>.\n\n"
            "Reenvía un mensaje del canal VIP.",
            parse_mode="HTML"
        )
        return

    channel_id = str(forward_chat.id)
    channel_title = forward_chat.title

    logger.info(f"📺 Configurando canal VIP: {channel_id} ({channel_title})")

    container = ServiceContainer(session, message.bot)

    # Intentar configurar el canal
    success, msg = await container.channel.setup_vip_channel(channel_id)

    if success:
        # Configuración exitosa
        await message.answer(
            f"✅ <b>Canal VIP Configurado</b>\n\n"
            f"Canal: <b>{channel_title}</b>\n"
            f"ID: <code>{channel_id}</code>\n\n"
            f"Ya puedes generar tokens de invitación.",
            parse_mode="HTML",
            reply_markup=vip_menu_keyboard(True)
        )

        # Limpiar estado FSM
        await state.clear()
    else:
        # Error en configuración
        await message.answer(
            f"{msg}\n\n"
            f"Verifica que:\n"
            f"• El bot es administrador del canal\n"
            f"• El bot tiene permiso para invitar usuarios\n\n"
            f"Intenta nuevamente reenviando un mensaje del canal.",
            parse_mode="HTML"
        )
        # Mantener estado FSM para reintentar


@admin_router.callback_query(F.data == "vip:generate_token")
async def callback_generate_vip_token(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Genera un token de invitación VIP.

    Token válido por 24 horas, un solo uso.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"🎟️ Usuario {callback.from_user.id} generando token VIP")

    container = ServiceContainer(session, callback.bot)

    # Verificar que canal VIP está configurado
    if not await container.channel.is_vip_channel_configured():
        await callback.answer(
            "❌ Debes configurar el canal VIP primero",
            show_alert=True
        )
        return

    try:
        # Generar token (24 horas por defecto)
        token = await container.subscription.generate_vip_token(
            generated_by=callback.from_user.id,
            duration_hours=Config.DEFAULT_TOKEN_DURATION_HOURS
        )

        # Crear mensaje con el token
        token_message = (
            f"🎟️ <b>Token VIP Generado</b>\n\n"
            f"Token: <code>{token.token}</code>\n\n"
            f"⏱️ Válido por: {token.duration_hours} horas\n"
            f"📅 Expira: {token.created_at.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
            f"👉 Comparte este token con el usuario.\n"
            f"El usuario debe enviarlo al bot para canjear acceso VIP."
        )

        await callback.message.answer(
            text=token_message,
            parse_mode="HTML"
        )

        await callback.answer("✅ Token generado")

    except Exception as e:
        logger.error(f"Error generando token VIP: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al generar token. Intenta nuevamente.",
            show_alert=True
        )
