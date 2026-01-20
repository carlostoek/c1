"""
Free Handlers - Gestión del canal Free.

Handlers para:
- Submenú Free
- Configuración del canal Free
- Configuración de tiempo de espera
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import ChannelSetupStates, WaitTimeSetupStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


def free_menu_keyboard(is_configured: bool) -> "InlineKeyboardMarkup":
    """
    Keyboard del submenú Free.

    Args:
        is_configured: Si el canal Free está configurado

    Returns:
        InlineKeyboardMarkup con opciones Free
    """
    buttons = []

    if is_configured:
        buttons.extend([
            [{"text": "⏱️ Configurar Tiempo de Espera", "callback_data": "free:set_wait_time"}],
            [{"text": "📤 Enviar Publicación", "callback_data": "free:broadcast"}],
            [{"text": "🔧 Reconfigurar Canal", "callback_data": "free:setup"}],
        ])
    else:
        buttons.append([{"text": "⚙️ Configurar Canal Free", "callback_data": "free:setup"}])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:main"}])

    return create_inline_keyboard(buttons)


@admin_router.callback_query(F.data == "admin:free")
async def callback_free_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el submenú de gestión Free.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.debug(f"📺 Usuario {callback.from_user.id} abrió menú Free")

    container = ServiceContainer(session, callback.bot)

    # Verificar si canal Free está configurado
    is_configured = await container.channel.is_free_channel_configured()

    if is_configured:
        free_channel_id = await container.channel.get_free_channel_id()
        wait_time = await container.config.get_wait_time()

        # Obtener info del canal
        channel_info = await container.channel.get_channel_info(free_channel_id)
        channel_name = channel_info.title if channel_info else "Canal Free"

        text = (
            f"📺 <b>Gestión Canal Free</b>\n\n"
            f"✅ Canal configurado: <b>{channel_name}</b>\n"
            f"ID: <code>{free_channel_id}</code>\n\n"
            f"⏱️ Tiempo de espera: <b>{wait_time} minutos</b>\n\n"
            f"Selecciona una opción:"
        )
    else:
        text = (
            "📺 <b>Gestión Canal Free</b>\n\n"
            "⚠️ Canal Free no configurado\n\n"
            "Configura el canal para que usuarios puedan solicitar acceso."
        )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=free_menu_keyboard(is_configured),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje Free: {e}")

    await callback.answer()


@admin_router.callback_query(F.data == "free:setup")
async def callback_free_setup(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el proceso de configuración del canal Free.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} iniciando setup Free")

    # Entrar en estado FSM
    await state.set_state(ChannelSetupStates.waiting_for_free_channel)

    text = (
        "⚙️ <b>Configurar Canal Free</b>\n\n"
        "Para configurar el canal Free:\n\n"
        "1️⃣ Vayas al canal Free\n"
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
                [{"text": "❌ Cancelar", "callback_data": "admin:free"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje setup Free: {e}")

    await callback.answer()


@admin_router.message(ChannelSetupStates.waiting_for_free_channel)
async def process_free_channel_forward(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el mensaje reenviado para configurar el canal Free.

    Args:
        message: Mensaje reenviado del canal
        session: Sesión de BD
        state: FSM context
    """
    # Validaciones idénticas a VIP
    if not message.forward_from_chat:
        await message.answer(
            "❌ Debes <b>reenviar</b> un mensaje del canal Free.\n\n"
            "No me envíes el ID manualmente, reenvía un mensaje.",
            parse_mode="HTML"
        )
        return

    forward_chat = message.forward_from_chat

    if forward_chat.type not in ["channel", "supergroup"]:
        await message.answer(
            "❌ El mensaje debe ser de un <b>canal</b> o <b>supergrupo</b>.\n\n"
            "Reenvía un mensaje del canal Free.",
            parse_mode="HTML"
        )
        return

    channel_id = str(forward_chat.id)
    channel_title = forward_chat.title

    logger.info(f"📺 Configurando canal Free: {channel_id} ({channel_title})")

    container = ServiceContainer(session, message.bot)

    # Intentar configurar el canal
    success, msg = await container.channel.setup_free_channel(channel_id)

    if success:
        await message.answer(
            f"✅ <b>Canal Free Configurado</b>\n\n"
            f"Canal: <b>{channel_title}</b>\n"
            f"ID: <code>{channel_id}</code>\n\n"
            f"Los usuarios ya pueden solicitar acceso.",
            parse_mode="HTML",
            reply_markup=free_menu_keyboard(True)
        )

        await state.clear()
    else:
        await message.answer(
            f"{msg}\n\n"
            f"Verifica permisos del bot e intenta nuevamente.",
            parse_mode="HTML"
        )


@admin_router.callback_query(F.data == "free:set_wait_time")
async def callback_set_wait_time(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia configuración de tiempo de espera.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⏱️ Usuario {callback.from_user.id} configurando wait time")

    container = ServiceContainer(session, callback.bot)
    current_wait_time = await container.config.get_wait_time()

    # Entrar en estado FSM
    await state.set_state(WaitTimeSetupStates.waiting_for_minutes)

    text = (
        f"⏱️ <b>Configurar Tiempo de Espera</b>\n\n"
        f"Tiempo actual: <b>{current_wait_time} minutos</b>\n\n"
        f"Envía el nuevo tiempo de espera en minutos.\n"
        f"Ejemplo: <code>5</code>\n\n"
        f"El tiempo debe ser mayor o igual a 1 minuto."
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "❌ Cancelar", "callback_data": "admin:free"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje wait time: {e}")

    await callback.answer()


@admin_router.message(WaitTimeSetupStates.waiting_for_minutes)
async def process_wait_time_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el input de tiempo de espera.

    Args:
        message: Mensaje con los minutos
        session: Sesión de BD
        state: FSM context
    """
    # Intentar convertir a número
    try:
        minutes = int(message.text)
    except ValueError:
        await message.answer(
            "❌ Debes enviar un número válido.\n\n"
            "Ejemplo: <code>5</code>",
            parse_mode="HTML"
        )
        return

    # Validar rango
    if minutes < 1:
        await message.answer(
            "❌ El tiempo debe ser al menos 1 minuto.\n\n"
            "Envía un número mayor o igual a 1.",
            parse_mode="HTML"
        )
        return

    container = ServiceContainer(session, message.bot)

    try:
        # Actualizar configuración
        await container.config.set_wait_time(minutes)

        await message.answer(
            f"✅ <b>Tiempo de Espera Actualizado</b>\n\n"
            f"Nuevo tiempo: <b>{minutes} minutos</b>\n\n"
            f"Las nuevas solicitudes esperarán {minutes} minutos antes de procesarse.",
            parse_mode="HTML",
            reply_markup=free_menu_keyboard(True)
        )

        # Limpiar estado
        await state.clear()

    except Exception as e:
        logger.error(f"Error actualizando wait time: {e}", exc_info=True)
        await message.answer(
            "❌ Error al actualizar el tiempo de espera.\n\n"
            "Intenta nuevamente.",
            parse_mode="HTML"
        )
