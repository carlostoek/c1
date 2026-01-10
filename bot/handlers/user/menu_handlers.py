"""
Menu Handlers - Handlers de menús dinámicos para usuarios.

Maneja:
- Opciones bloqueadas (requieren onboarding)
- Navegación de submenús
- Registro de interés en productos comerciales
"""
import logging

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.start import user_router
from bot.services.lucien_voice import LucienVoiceService
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@user_router.callback_query(F.data.startswith("blocked:"))
async def callback_blocked_option(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra mensaje de Lucien cuando usuario intenta acceder a opción bloqueada.

    Las opciones bloqueadas requieren que el usuario complete el onboarding
    antes de poder acceder a la narrativa, juegos, o perfil completo.

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    user_id = callback.from_user.id

    logger.info(f"🚫 Usuario {user_id} intentó acceder a opción bloqueada: {callback.data}")

    # Mensaje de Lucien explicando que necesita completar onboarding
    lucien = LucienVoiceService()
    message = await lucien.format_error("onboarding_required")

    # Keyboard con botón para iniciar tutorial
    keyboard = create_inline_keyboard([
        [{"text": "📖 Iniciar Tutorial", "callback_data": "narr:start"}],
        [{"text": "🔙 Volver al Menú", "callback_data": "profile:back"}]
    ])

    await callback.message.edit_text(
        message,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("submenu:"))
async def callback_submenu(callback: CallbackQuery, session: AsyncSession):
    """
    Navega hacia un submenú dinámico.

    Los submenús son items de menú con parent_key != None.
    Ejemplo: submenu:free_sets → Muestra items con parent_key='free_sets'

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    user_id = callback.from_user.id

    # Parsear: submenu:free_sets
    parts = callback.data.split(":", 1)
    if len(parts) < 2:
        logger.warning(f"⚠️ Formato inválido de submenu: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    parent_key = parts[1]

    logger.info(f"📂 Usuario {user_id} navegando a submenú: {parent_key}")

    from bot.services.container import ServiceContainer
    from bot.narrative.services.container import NarrativeContainer

    container = ServiceContainer(session, callback.bot)
    narrative = NarrativeContainer(session, callback.bot)

    # Obtener usuario y verificar onboarding
    user = await container.user.get_user(user_id)
    role = user.role.value if user else "free"
    completed_onboarding = await narrative.onboarding.has_completed_onboarding(user_id)

    # Construir keyboard de submenú
    keyboard_buttons = await container.menu.build_keyboard_for_role(
        role=role,
        user_id=user_id,
        completed_onboarding=completed_onboarding,
        parent_key=parent_key
    )

    # Agregar botón de volver
    keyboard_buttons.append([{"text": "🔙 Volver", "callback_data": "profile:back"}])

    keyboard = create_inline_keyboard(keyboard_buttons)

    # Obtener item de menú para el título
    menu_item = await container.menu.get_menu_item_by_key(parent_key)

    if menu_item:
        title = f"{menu_item.button_emoji} {menu_item.button_text}" if menu_item.button_emoji else menu_item.button_text
        message_text = f"<b>{title}</b>\n\n<i>Seleccione una opción:</i>"
    else:
        message_text = "<b>Menú</b>\n\n<i>Seleccione una opción:</i>"

    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
