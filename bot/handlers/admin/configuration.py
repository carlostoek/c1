"""
Handlers para el wizard de configuración de gamificación.

Entry point: /config
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import ConfigMainStates, ConfigDataKeys
from bot.utils.config_keyboards import config_main_menu_keyboard

logger = logging.getLogger(__name__)

# Router con middlewares
config_router = Router(name="configuration")
config_router.message.middleware(DatabaseMiddleware())
config_router.message.middleware(AdminAuthMiddleware())
config_router.callback_query.middleware(DatabaseMiddleware())
config_router.callback_query.middleware(AdminAuthMiddleware())


# ═══════════════════════════════════════════════════════════════
# COMANDO PRINCIPAL
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# NAVEGACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════

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
    
    await callback.message.edit_text(
        text=text,
        reply_markup=config_main_menu_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(ConfigMainStates.main_menu)
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


# ═══════════════════════════════════════════════════════════════
# CANCELAR OPERACIÓN EN CUALQUIER MOMENTO
# ═══════════════════════════════════════════════════════════════

@config_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Cancelar operación actual y volver al menú principal.
    
    Disponible en cualquier estado del wizard.
    """
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("No hay operación en curso.")
        return
    
    await state.clear()
    await message.answer(
        "❌ Operación cancelada.\n\n"
        "Usa /config para volver al menú de configuración."
    )
    logger.debug(f"🚫 Operación cancelada desde estado {current_state}")