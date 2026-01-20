"""
Reactions Handlers - Configuración de reacciones automáticas.

Handlers para:
- Configurar reacciones del canal VIP
- Configurar reacciones del canal Free
- Ver reacciones actuales
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import ReactionSetupStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.validators import validate_emoji_list

logger = logging.getLogger(__name__)


# ===== CONFIGURACIÓN DE REACCIONES VIP =====

@admin_router.callback_query(F.data == "config:reactions:vip")
async def callback_setup_vip_reactions(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia configuración de reacciones para canal VIP.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} configurando reacciones VIP")

    container = ServiceContainer(session, callback.bot)

    # Obtener reacciones actuales
    current_reactions = await container.config.get_vip_reactions()

    if current_reactions:
        current_text = " ".join(current_reactions)
        status_text = f"<b>Reacciones actuales:</b> {current_text}\n\n"
    else:
        status_text = "<b>Reacciones actuales:</b> <i>Ninguna configurada</i>\n\n"

    # Entrar en estado FSM
    await state.set_state(ReactionSetupStates.waiting_for_vip_reactions)

    text = (
        "⚙️ <b>Configurar Reacciones VIP</b>\n\n"
        f"{status_text}"
        "Envía los emojis que quieres usar como reacciones, "
        "separados por espacios.\n\n"
        "<b>Ejemplo:</b> <code>👍 ❤️ 🔥 🎉 💯</code>\n\n"
        "<b>Reglas:</b>\n"
        "• Mínimo: 1 emoji\n"
        "• Máximo: 10 emojis\n"
        "• Solo emojis válidos\n\n"
        "Las reacciones se aplicarán automáticamente a "
        "nuevas publicaciones en el canal VIP."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:config"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


@admin_router.message(ReactionSetupStates.waiting_for_vip_reactions)
async def process_vip_reactions_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el input de reacciones VIP.

    Args:
        message: Mensaje con emojis
        session: Sesión de BD
        state: FSM context
    """
    user_id = message.from_user.id
    text = message.text.strip()

    logger.info(f"⚙️ Usuario {user_id} enviando reacciones VIP: {text}")

    # Validar emojis
    is_valid, error_msg, emojis = validate_emoji_list(text)

    if not is_valid:
        # Input inválido
        await message.answer(
            f"❌ <b>Input Inválido</b>\n\n"
            f"{error_msg}\n\n"
            f"Por favor, envía los emojis separados por espacios.\n"
            f"Ejemplo: <code>👍 ❤️ 🔥</code>",
            parse_mode="HTML"
        )
        # Mantener estado FSM para reintentar
        return

    container = ServiceContainer(session, message.bot)

    try:
        # Guardar reacciones
        await container.config.set_vip_reactions(emojis)

        reactions_text = " ".join(emojis)

        await message.answer(
            f"✅ <b>Reacciones VIP Configuradas</b>\n\n"
            f"<b>Reacciones:</b> {reactions_text}\n"
            f"<b>Total:</b> {len(emojis)} emojis\n\n"
            f"Estas reacciones se aplicarán automáticamente a "
            f"nuevas publicaciones en el canal VIP.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver a Configuración", "callback_data": "admin:config"}]
            ]),
            parse_mode="HTML"
        )

        # Limpiar estado FSM
        await state.clear()

        logger.info(f"✅ Reacciones VIP configuradas: {len(emojis)} emojis")

    except ValueError as e:
        # Error de validación del service
        logger.error(f"❌ Error validando reacciones VIP: {e}")

        await message.answer(
            f"❌ <b>Error al Guardar Reacciones</b>\n\n"
            f"{str(e)}\n\n"
            f"Intenta nuevamente.",
            parse_mode="HTML"
        )
        # Mantener estado para reintentar

    except Exception as e:
        # Error inesperado
        logger.error(f"❌ Error guardando reacciones VIP: {e}", exc_info=True)

        await message.answer(
            "❌ <b>Error Inesperado</b>\n\n"
            "No se pudieron guardar las reacciones.\n"
            "Intenta nuevamente.",
            parse_mode="HTML"
        )
        await state.clear()


# ===== CONFIGURACIÓN DE REACCIONES FREE =====

@admin_router.callback_query(F.data == "config:reactions:free")
async def callback_setup_free_reactions(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia configuración de reacciones para canal Free.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} configurando reacciones Free")

    container = ServiceContainer(session, callback.bot)

    # Obtener reacciones actuales
    current_reactions = await container.config.get_free_reactions()

    if current_reactions:
        current_text = " ".join(current_reactions)
        status_text = f"<b>Reacciones actuales:</b> {current_text}\n\n"
    else:
        status_text = "<b>Reacciones actuales:</b> <i>Ninguna configurada</i>\n\n"

    # Entrar en estado FSM
    await state.set_state(ReactionSetupStates.waiting_for_free_reactions)

    text = (
        "⚙️ <b>Configurar Reacciones Free</b>\n\n"
        f"{status_text}"
        "Envía los emojis que quieres usar como reacciones, "
        "separados por espacios.\n\n"
        "<b>Ejemplo:</b> <code>👍 ❤️ 🔥 🎉 💯</code>\n\n"
        "<b>Reglas:</b>\n"
        "• Mínimo: 1 emoji\n"
        "• Máximo: 10 emojis\n"
        "• Solo emojis válidos\n\n"
        "Las reacciones se aplicarán automáticamente a "
        "nuevas publicaciones en el canal Free."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:config"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


@admin_router.message(ReactionSetupStates.waiting_for_free_reactions)
async def process_free_reactions_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el input de reacciones Free.

    Args:
        message: Mensaje con emojis
        session: Sesión de BD
        state: FSM context
    """
    user_id = message.from_user.id
    text = message.text.strip()

    logger.info(f"⚙️ Usuario {user_id} enviando reacciones Free: {text}")

    # Validar emojis
    is_valid, error_msg, emojis = validate_emoji_list(text)

    if not is_valid:
        await message.answer(
            f"❌ <b>Input Inválido</b>\n\n"
            f"{error_msg}\n\n"
            f"Por favor, envía los emojis separados por espacios.\n"
            f"Ejemplo: <code>👍 ❤️ 🔥</code>",
            parse_mode="HTML"
        )
        return

    container = ServiceContainer(session, message.bot)

    try:
        # Guardar reacciones
        await container.config.set_free_reactions(emojis)

        reactions_text = " ".join(emojis)

        await message.answer(
            f"✅ <b>Reacciones Free Configuradas</b>\n\n"
            f"<b>Reacciones:</b> {reactions_text}\n"
            f"<b>Total:</b> {len(emojis)} emojis\n\n"
            f"Estas reacciones se aplicarán automáticamente a "
            f"nuevas publicaciones en el canal Free.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver a Configuración", "callback_data": "admin:config"}]
            ]),
            parse_mode="HTML"
        )

        await state.clear()

        logger.info(f"✅ Reacciones Free configuradas: {len(emojis)} emojis")

    except ValueError as e:
        logger.error(f"❌ Error validando reacciones Free: {e}")

        await message.answer(
            f"❌ <b>Error al Guardar Reacciones</b>\n\n"
            f"{str(e)}\n\n"
            f"Intenta nuevamente.",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"❌ Error guardando reacciones Free: {e}", exc_info=True)

        await message.answer(
            "❌ <b>Error Inesperado</b>\n\n"
            "No se pudieron guardar las reacciones.\n"
            "Intenta nuevamente.",
            parse_mode="HTML"
        )
        await state.clear()
