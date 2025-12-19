"""
Handlers para el wizard de configuración de gamificación.

Entry point: /config
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import ConfigMainStates
from bot.utils.config_keyboards import config_main_menu_keyboard

# Import routers for different configuration parts
from bot.handlers.admin.config_parts.actions import actions_router
from bot.handlers.admin.config_parts.levels import levels_router
from bot.handlers.admin.config_parts.badges import badges_router
from bot.handlers.admin.config_parts.rewards import rewards_router
from bot.handlers.admin.config_parts.missions import missions_router
from bot.handlers.admin.config_parts.common import common_router

logger = logging.getLogger(__name__)

# Main router with middlewares
config_router = Router(name="configuration")
config_router.message.middleware(DatabaseMiddleware())
config_router.message.middleware(AdminAuthMiddleware())
config_router.callback_query.middleware(DatabaseMiddleware())
config_router.callback_query.middleware(AdminAuthMiddleware())

# Include sub-routers
config_router.include_router(actions_router)
config_router.include_router(levels_router)
config_router.include_router(badges_router)
config_router.include_router(rewards_router)
config_router.include_router(missions_router)
config_router.include_router(common_router)


@config_router.message(Command("config"))
async def cmd_config(message: Message, state: FSMContext, session: AsyncSession):
    """
    Handler del comando /config.

    Muestra el menú principal de configuración de gamificación.
    """
    logger.info(f"📋 Config wizard abierto por user {message.from_user.id}")

    # Limpiar estado previo
    await state.clear()

    # Obtener estadísticas rápidas
    container = ServiceContainer(session, message.bot)
    configuration_service = container.configuration

    actions = await configuration_service.list_actions()
    levels = await configuration_service.list_levels()
    badges = await configuration_service.list_badges()
    rewards = await configuration_service.list_rewards()
    missions = await configuration_service.list_missions()

    text = (
        "⚙️ <b>Configuración de Gamificación</b>\n\n"
        "📊 Estado actual:\n"
        f"   • Acciones: {len(actions)} configuradas\n"
        f"   • Niveles: {len(levels)} configurados\n"
        f"   • Badges: {len(badges)} configurados\n"
        f"   • Recompensas: {len(rewards)} configuradas\n"
        f"   • Misiones: {len(missions)} configuradas\n\n"
        "Selecciona qué deseas configurar:"
    )

    await message.answer(
        text=text,
        reply_markup=config_main_menu_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(ConfigMainStates.main_menu)


@config_router.callback_query(F.data == "config:main")
async def callback_config_main(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Volver al menú principal de configuración."""
    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    actions = await configuration_service.list_actions()
    levels = await configuration_service.list_levels()
    badges = await configuration_service.list_badges()
    rewards = await configuration_service.list_rewards()
    missions = await configuration_service.list_missions()

    text = (
        "⚙️ <b>Configuración de Gamificación</b>\n\n"
        "📊 Estado actual:\n"
        f"   • Acciones: {len(actions)} configuradas\n"
        f"   • Niveles: {len(levels)} configurados\n"
        f"   • Badges: {len(badges)} configurados\n"
        f"   • Recompensas: {len(rewards)} configuradas\n"
        f"   • Misiones: {len(missions)} configuradas\n\n"
        "Selecciona qué deseas configurar:"
    )

    # Prepare the new content
    new_reply_markup = config_main_menu_keyboard()

    try:
        # Try to edit the message
        await callback.message.edit_text(
            text=text,
            reply_markup=new_reply_markup,
            parse_mode="HTML"
        )
        await state.set_state(ConfigMainStates.main_menu)
    except TelegramBadRequest as e:
        # Handle the case where the message is not modified
        if "message is not modified" in str(e.message).lower():
            # Content is the same, just acknowledge the callback
            pass
        else:
            # Some other bad request error occurred
            logger.error(f"BadRequest error editing message in callback_config_main: {e}")
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error editing message in callback_config_main: {e}")

    await callback.answer()


@config_router.callback_query(F.data == "config:close")
async def callback_config_close(callback: CallbackQuery, state: FSMContext):
    """Cerrar el wizard de configuración."""
    await state.clear()
    await callback.message.edit_text(
        "✅ Configuración cerrada.\n\n"
        "Usa /config para volver a abrir."
    )
    await callback.answer()