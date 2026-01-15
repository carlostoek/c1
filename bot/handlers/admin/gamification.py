"""
Gamification Admin Handlers - Menú y configuración de gamificación.

Handlers:
- callback_gamification_menu: Menú principal de gamificación
- callback_gamification_config: Configuración global
- FSM handlers para configurar puntos y emojis
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import GamificationConfigStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.validators import validate_emoji_list

logger = logging.getLogger(__name__)


def create_gamification_menu_keyboard() -> InlineKeyboardMarkup:
    """Crea keyboard del menú de gamificación."""
    builder = InlineKeyboardBuilder()

    # Publicación
    builder.row(
        InlineKeyboardButton(text="📝 Publicar con Reacciones", callback_data="admin:gamification:publish")
    )

    # Configuración
    builder.row(
        InlineKeyboardButton(text="⚙️ Configurar Gamificación", callback_data="admin:gamification:config")
    )

    # Gestión
    builder.row(
        InlineKeyboardButton(text="🏆 Badges", callback_data="admin:gamification:badges"),
        InlineKeyboardButton(text="🏅 Niveles", callback_data="admin:gamification:levels")
    )

    builder.row(
        InlineKeyboardButton(text="📋 Misiones", callback_data="admin:gamification:missions"),
        InlineKeyboardButton(text="📦 Media Sets", callback_data="admin:gamification:media_sets")
    )

    builder.row(
        InlineKeyboardButton(text="🛒 Tienda", callback_data="admin:gamification:shop")
    )

    # Volver
    builder.row(
        InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="admin:main")
    )

    return builder.as_markup()


@admin_router.callback_query(F.data == "admin:gamification")
async def callback_gamification_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el menú principal de gamificación.

    Opciones:
    - Publicar con reacciones
    - Configurar gamificación
    - Badges, Niveles, Misiones, Media Sets, Tienda
    """
    logger.debug("🎮 Admin abriendo menú de gamificación")

    container = ServiceContainer(session, callback.bot)
    config = await container.config.get_config_status()

    # Verificar estado de configuración
    has_vip = config.get("vip_channel_id") is not None
    has_free = config.get("free_channel_id") is not None

    if not has_vip and not has_free:
        status = "⚠️ <b>No hay canales configurados</b>\n\n"
        status += "Configura al menos un canal (VIP o Free) antes de usar gamificación."
    else:
        status = "✅ <b>Sistema de Gamificación</b>\n\n"
        if has_vip:
            status += f"• Canal VIP: ✅ Configurado\n"
        if has_free:
            status += f"• Canal Free: ✅ Configurado\n"

    text = (
        f"{status}\n"
        f"Selecciona una opción:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_gamification_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin:gamification:config")
async def callback_gamification_config(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el menú de configuración de gamificación.

    Opciones:
    - Configurar puntos por reacción
    - Configurar regalo diario
    - Configurar multiplicador de racha
    - Configurar emojis predeterminados
    """
    logger.debug("⚙️ Admin configurando gamificación")

    container = ServiceContainer(session, callback.bot)
    gamification_config = await container.points._get_config()

    text = (
        "⚙️ <b>Configuración de Gamificación</b>\n\n"
        f"<b>Puntos por Reacción:</b> {gamification_config.points_per_reaction}\n"
        f"<b>Regalo Diario:</b> {gamification_config.daily_gift_points} puntos\n"
        f"<b>Multiplicador de Racha:</b> x{gamification_config.streak_multiplier}\n\n"
        f"<b>Emojis Predeterminados:</b>\n"
        f"{' '.join(gamification_config.default_reaction_emojis) if gamification_config.default_reaction_emojis else 'Sin configurar'}\n\n"
        f"Selecciona qué configurar:"
    )

    keyboard = create_inline_keyboard([
        [{"text": "💰 Puntos por Reacción", "callback_data": "admin:gamification:config:points"}],
        [{"text": "🎁 Regalo Diario", "callback_data": "admin:gamification:config:daily"}],
        [{"text": "🔥 Multiplicador de Racha", "callback_data": "admin:gamification:config:streak"}],
        [{"text": "🎨 Emojis Predeterminados", "callback_data": "admin:gamification:config:emojis"}],
        [{"text": "🔙 Volver a Gamificación", "callback_data": "admin:gamification"}]
    ])

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin:gamification:config:points")
async def callback_config_points(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """Inicia configuración de puntos por reacción."""
    container = ServiceContainer(session, callback.bot)
    config = await container.points._get_config()

    await state.set_state(GamificationConfigStates.waiting_for_points_per_reaction)

    text = (
        "💰 <b>Configurar Puntos por Reacción</b>\n\n"
        f"<b>Valor Actual:</b> {config.points_per_reaction} punto(s)\n\n"
        "Envía el nuevo número de puntos que los usuarios ganarán por cada reacción.\n\n"
        "<b>Reglas:</b>\n"
        "• Mínimo: 1 punto\n"
        "• Máximo: 100 puntos\n\n"
        "<b>Ejemplo:</b> <code>5</code>"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:gamification:config"}]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(GamificationConfigStates.waiting_for_points_per_reaction)
async def process_points_per_reaction(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """Procesa el input de puntos por reacción."""
    user_id = message.from_user.id
    text = message.text.strip()

    logger.debug(f"💰 Admin {user_id} configurando puntos por reacción: {text}")

    # Validar número
    try:
        points = int(text)
        if points < 1 or points > 100:
            await message.answer(
                "❌ <b>Valor Inválido</b>\n\n"
                "El valor debe estar entre 1 y 100 puntos.\n\n"
                "Intenta nuevamente.",
                parse_mode="HTML"
            )
            return
    except ValueError:
        await message.answer(
            "❌ <b>Formato Inválido</b>\n\n"
            "Debes enviar un número entero.\n\n"
            "Ejemplo: <code>5</code>",
            parse_mode="HTML"
        )
        return

    # Actualizar configuración
    container = ServiceContainer(session, message.bot)
    config = await container.points._get_config()
    config.points_per_reaction = points
    await session.commit()

    await message.answer(
        f"✅ <b>Puntos por Reacción Actualizados</b>\n\n"
        f"<b>Nuevo Valor:</b> {points} puntos por reacción",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver a Configuración", "callback_data": "admin:gamification:config"}]
        ]),
        parse_mode="HTML"
    )
    await state.clear()


@admin_router.callback_query(F.data == "admin:gamification:config:emojis")
async def callback_config_emojis(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """Inicia configuración de emojis predeterminados."""
    container = ServiceContainer(session, callback.bot)
    config = await container.points._get_config()

    await state.set_state(GamificationConfigStates.waiting_for_default_emojis)

    current_emojis = " ".join(config.default_reaction_emojis) if config.default_reaction_emojis else "Sin configurar"

    text = (
        "🎨 <b>Configurar Emojis Predeterminados</b>\n\n"
        f"<b>Emojis Actuales:</b> {current_emojis}\n\n"
        "Envía los emojis que se usarán por defecto en las publicaciones.\n\n"
        "<b>Reglas:</b>\n"
        "• Mínimo: 1 emoji\n"
        "• Máximo: 10 emojis\n"
        "• Separados por espacios\n\n"
        "<b>Ejemplo:</b> <code>👍 ❤️ 🔥 🎉 💯</code>"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:gamification:config"}]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(GamificationConfigStates.waiting_for_default_emojis)
async def process_default_emojis(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """Procesa el input de emojis predeterminados."""
    user_id = message.from_user.id
    text = message.text.strip()

    logger.debug(f"🎨 Admin {user_id} configurando emojis: {text}")

    # Validar emojis
    is_valid, error_msg, emojis = validate_emoji_list(text)

    if not is_valid:
        await message.answer(
            f"❌ <b>Input Inválido</b>\n\n"
            f"{error_msg}\n\n"
            f"Envía los emojis separados por espacios.\n"
            f"Ejemplo: <code>👍 ❤️ 🔥</code>",
            parse_mode="HTML"
        )
        return

    # Actualizar configuración
    container = ServiceContainer(session, message.bot)
    await container.reactions.set_default_emojis(emojis)

    emojis_text = " ".join(emojis)

    await message.answer(
        f"✅ <b>Emojis Predeterminados Configurados</b>\n\n"
        f"<b>Emojis:</b> {emojis_text}\n"
        f"<b>Total:</b> {len(emojis)} emojis\n\n"
        f"Estos emojis se usarán en nuevas publicaciones.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver a Configuración", "callback_data": "admin:gamification:config"}]
        ]),
        parse_mode="HTML"
    )
    await state.clear()


# Placeholders para otras configuraciones
@admin_router.callback_query(F.data.startswith("admin:gamification:config:daily"))
async def callback_config_daily(callback: CallbackQuery):
    """TODO: Configurar regalo diario."""
    await callback.answer("🚧 En desarrollo próximamente", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin:gamification:config:streak"))
async def callback_config_streak(callback: CallbackQuery):
    """TODO: Configurar multiplicador de racha."""
    await callback.answer("🚧 En desarrollo próximamente", show_alert=True)
