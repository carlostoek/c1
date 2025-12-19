"""
Handlers para el wizard de configuración de gamificación.

Entry point: /config
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import (
    ConfigMainStates,
    ActionConfigStates,
    LevelConfigStates,
    BadgeConfigStates,
    RewardConfigStates,
    MissionConfigStates,
    ConfigDataKeys
)
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


# ═══════════════════════════════════════════════════════════════
# SUBMENÚS PRINCIPALES
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data == "config:actions")
async def callback_config_actions(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de acciones configuradas."""
    await state.update_data(current_menu="actions")

    container = ServiceContainer(session, callback.bot)
    actions = await container.configuration.list_actions()

    # Crear texto con la lista de acciones
    if actions:
        actions_list = "\n".join([
            f"• {action.display_name} ({action.points_amount} pts) - {action.action_key}"
            for action in actions
        ])
        text = (
            "📊 <b>Acciones Configuradas</b>\n\n"
            f"Se encontraron {len(actions)} acciones:\n\n"
            f"{actions_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "📊 <b>Acciones Configuradas</b>\n\n"
            "No hay acciones configuradas aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Crear keyboard con botones de navegación
    from bot.utils.config_keyboards import config_list_keyboard
    # Convertir acciones para usar con config_list_keyboard
    items = [(action.id, f"{action.display_name} ({action.points_amount} pts)") for action in actions]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:actions",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(ActionConfigStates.list_actions)
    await callback.answer()


@config_router.callback_query(F.data == "config:levels")
async def callback_config_levels(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de niveles configurados."""
    await state.update_data(current_menu="levels")

    container = ServiceContainer(session, callback.bot)
    levels = await container.configuration.list_levels()

    # Crear texto con la lista de niveles
    if levels:
        levels_list = "\n".join([
            f"• {level.name} (≥{level.min_points} pts) - {level.icon}"
            for level in levels
        ])
        text = (
            "📈 <b>Niveles Configurados</b>\n\n"
            f"Se encontraron {len(levels)} niveles:\n\n"
            f"{levels_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "📈 <b>Niveles Configurados</b>\n\n"
            "No hay niveles configurados aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Crear keyboard con botones de navegación
    from bot.utils.config_keyboards import config_list_keyboard
    # Convertir niveles para usar con config_list_keyboard
    items = [(level.id, f"{level.name} (≥{level.min_points} pts)") for level in levels]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:levels",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(LevelConfigStates.list_levels)
    await callback.answer()


@config_router.callback_query(F.data == "config:badges")
async def callback_config_badges(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de badges configurados."""
    await state.update_data(current_menu="badges")

    container = ServiceContainer(session, callback.bot)
    badges = await container.configuration.list_badges()

    # Crear texto con la lista de badges
    if badges:
        badges_list = "\n".join([
            f"• {badge.icon} {badge.name} - {badge.badge_key}"
            for badge in badges
        ])
        text = (
            "🏆 <b>Badges Configurados</b>\n\n"
            f"Se encontraron {len(badges)} badges:\n\n"
            f"{badges_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "🏆 <b>Badges Configurados</b>\n\n"
            "No hay badges configurados aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Crear keyboard con botones de navegación
    from bot.utils.config_keyboards import config_list_keyboard
    # Convertir badges para usar con config_list_keyboard
    items = [(badge.id, f"{badge.icon} {badge.name}") for badge in badges]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:badges",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(BadgeConfigStates.list_badges)
    await callback.answer()


@config_router.callback_query(F.data == "config:rewards")
async def callback_config_rewards(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de recompensas configuradas."""
    await state.update_data(current_menu="rewards")

    container = ServiceContainer(session, callback.bot)
    rewards = await container.configuration.list_rewards()

    # Crear texto con la lista de recompensas
    if rewards:
        rewards_list = "\n".join([
            f"• {reward.name} ({reward.reward_type})"
            for reward in rewards
        ])
        text = (
            "🎁 <b>Recompensas Configuradas</b>\n\n"
            f"Se encontraron {len(rewards)} recompensas:\n\n"
            f"{rewards_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "🎁 <b>Recompensas Configuradas</b>\n\n"
            "No hay recompensas configuradas aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Crear keyboard con botones de navegación
    from bot.utils.config_keyboards import config_list_keyboard
    # Convertir recompensas para usar con config_list_keyboard
    items = [(reward.id, f"🎁 {reward.name}") for reward in rewards]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:rewards",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(RewardConfigStates.list_rewards)
    await callback.answer()


@config_router.callback_query(F.data == "config:missions")
async def callback_config_missions(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de misiones configuradas."""
    await state.update_data(current_menu="missions")

    container = ServiceContainer(session, callback.bot)
    missions = await container.configuration.list_missions()

    # Crear texto con la lista de misiones
    if missions:
        missions_list = "\n".join([
            f"• {mission.name} ({mission.mission_type})"
            for mission in missions
        ])
        text = (
            "🎯 <b>Misiones Configuradas</b>\n\n"
            f"Se encontraron {len(missions)} misiones:\n\n"
            f"{missions_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "🎯 <b>Misiones Configuradas</b>\n\n"
            "No hay misiones configuradas aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Crear keyboard con botones de navegación
    from bot.utils.config_keyboards import config_list_keyboard
    # Convertir misiones para usar con config_list_keyboard
    items = [(mission.id, f"🎯 {mission.name}") for mission in missions]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:missions",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(MissionConfigStates.list_missions)
    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA VER ITEMS
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data.startswith("config:actions:view:"))
async def callback_config_view_action(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de una acción específica."""
    action_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        action = await configuration_service.get_action_by_id(action_id)

        text = (
            f"📊 <b>Detalles de la Acción</b>\n\n"
            f"<b>Nombre:</b> {action.display_name}\n"
            f"<b>Clave:</b> {action.action_key}\n"
            f"<b>Puntos:</b> {action.points_amount}\n"
            f"<b>Descripción:</b> {action.description or 'Sin descripción'}\n"
            f"<b>Activa:</b> {'Sí' if action.is_active else 'No'}\n"
            f"<b>Creada:</b> {action.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
            "<i>¿Qué deseas hacer con esta acción?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=action_id,
            prefix="config:actions",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=action_id, editing_type="action")
        await state.set_state(ActionConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver acción {action_id}: {e}")
        await callback.answer("❌ Error al cargar la acción", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:levels:view:"))
async def callback_config_view_level(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de un nivel específico."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        level = await configuration_service.get_level(level_id)

        text = (
            f"📈 <b>Detalles del Nivel</b>\n\n"
            f"<b>Nombre:</b> {level.name}\n"
            f"<b>Icono:</b> {level.icon}\n"
            f"<b>Puntos mínimos:</b> {level.min_points}\n"
            f"<b>Puntos máximos:</b> {level.max_points or '∞'}\n"
            f"<b>Multiplicador:</b> {level.multiplier}x\n"
            f"<b>Color:</b> {level.color or 'Sin color'}\n"
            f"<b>Orden:</b> {level.order}\n"
            f"<b>Activo:</b> {'Sí' if level.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este nivel?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=level_id,
            prefix="config:levels",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=level_id, editing_type="level")
        await state.set_state(LevelConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver nivel {level_id}: {e}")
        await callback.answer("❌ Error al cargar el nivel", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:badges:view:"))
async def callback_config_view_badge(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de un badge específico."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        badge = await configuration_service.get_badge_by_id(badge_id)

        text = (
            f"🏆 <b>Detalles del Badge</b>\n\n"
            f"<b>Icono:</b> {badge.icon}\n"
            f"<b>Nombre:</b> {badge.name}\n"
            f"<b>Clave:</b> {badge.badge_key}\n"
            f"<b>Tipo de requisito:</b> {badge.requirement_type}\n"
            f"<b>Valor del requisito:</b> {badge.requirement_value}\n"
            f"<b>Descripción:</b> {badge.description or 'Sin descripción'}\n"
            f"<b>Activo:</b> {'Sí' if badge.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este badge?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=badge_id,
            prefix="config:badges",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=badge_id, editing_type="badge")
        await state.set_state(BadgeConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver badge {badge_id}: {e}")
        await callback.answer("❌ Error al cargar el badge", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:rewards:view:"))
async def callback_config_view_reward(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de una recompensa específica."""
    reward_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        reward = await configuration_service.get_reward(reward_id)

        badge_info = ""
        if reward.badge:
            badge_info = f"\n<b>Badge:</b> {reward.badge.icon} {reward.badge.name}"

        text = (
            f"🎁 <b>Detalles de la Recompensa</b>\n\n"
            f"<b>Nombre:</b> {reward.name}\n"
            f"<b>Tipo:</b> {reward.reward_type}\n"
            f"<b>Puntos:</b> {reward.points_amount or 'N/A'}\n"
            f"<b>Descripción:</b> {reward.description or 'Sin descripción'}\n"
            f"{badge_info}\n"
            f"<b>Activa:</b> {'Sí' if reward.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta recompensa?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=reward_id,
            prefix="config:rewards",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=reward_id, editing_type="reward")
        await state.set_state(RewardConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver recompensa {reward_id}: {e}")
        await callback.answer("❌ Error al cargar la recompensa", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:missions:view:"))
async def callback_config_view_mission(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de una misión específica."""
    mission_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        mission = await configuration_service.get_mission(mission_id)

        reward_info = ""
        if mission.reward:
            reward_info = f"\n<b>Recompensa:</b> {mission.reward.name}"

        text = (
            f"🎯 <b>Detalles de la Misión</b>\n\n"
            f"<b>Nombre:</b> {mission.name}\n"
            f"<b>Tipo:</b> {mission.mission_type}\n"
            f"<b>Acción objetivo:</b> {mission.target_action or 'N/A'}\n"
            f"<b>Valor objetivo:</b> {mission.target_value}\n"
            f"<b>Límite de tiempo:</b> {mission.time_limit_hours or 'N/A'}h\n"
            f"<b>Repetible:</b> {'Sí' if mission.is_repeatable else 'No'}\n"
            f"{reward_info}\n"
            f"<b>Activa:</b> {'Sí' if mission.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta misión?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=mission_id,
            prefix="config:missions",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=mission_id, editing_type="mission")
        await state.set_state(MissionConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver misión {mission_id}: {e}")
        await callback.answer("❌ Error al cargar la misión", show_alert=True)

    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA CREAR ITEMS
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data == "config:actions:create")
async def callback_config_create_action(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nueva acción."""
    await state.clear()
    await state.set_state(ActionConfigStates.create_key)

    text = (
        "📊 <b>Creando Nueva Acción</b>\n\n"
        "Primero, ingresa la clave única de la acción.\n\n"
        "<b>Ejemplo:</b> custom_reaction, daily_checkin, post_share\n"
        "<b>Requisitos:</b> Solo letras, números y guiones bajos. Mínimo 3 caracteres."
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@config_router.callback_query(F.data == "config:levels:create")
async def callback_config_create_level(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nuevo nivel."""
    await state.clear()
    await state.set_state(LevelConfigStates.create_name)

    text = (
        "📈 <b>Creando Nuevo Nivel</b>\n\n"
        "Primero, ingresa el nombre del nivel.\n\n"
        "<b>Ejemplo:</b> Principiante, Intermedio, Experto"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@config_router.callback_query(F.data == "config:badges:create")
async def callback_config_create_badge(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nuevo badge."""
    await state.clear()
    await state.set_state(BadgeConfigStates.create_key)

    text = (
        "🏆 <b>Creando Nuevo Badge</b>\n\n"
        "Primero, ingresa la clave única del badge.\n\n"
        "<b>Ejemplo:</b> super_reactor, daily_visitor, content_creator\n"
        "<b>Requisitos:</b> Solo letras, números y guiones bajos. Mínimo 3 caracteres."
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@config_router.callback_query(F.data == "config:rewards:create")
async def callback_config_create_reward(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nueva recompensa."""
    await state.clear()
    await state.set_state(RewardConfigStates.create_name)

    text = (
        "🎁 <b>Creando Nueva Recompensa</b>\n\n"
        "Primero, ingresa el nombre de la recompensa.\n\n"
        "<b>Ejemplo:</b> Bonus Points, Special Badge, Premium Access"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@config_router.callback_query(F.data == "config:missions:create")
async def callback_config_create_mission(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nueva misión."""
    await state.clear()
    await state.set_state(MissionConfigStates.create_name)

    text = (
        "🎯 <b>Creando Nueva Misión</b>\n\n"
        "Primero, ingresa el nombre de la misión.\n\n"
        "<b>Ejemplo:</b> Daily Streak, Reaction Master, Community Helper"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA EDITAR ITEMS
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data.startswith("config:actions:edit:"))
async def callback_config_edit_action(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar una acción específica."""
    action_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        action = await configuration_service.get_action_by_id(action_id)

        await state.update_data(editing_id=action_id)
        await state.set_state(ActionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Acción</b>\n\n"
            f"<b>Actual:</b> {action.display_name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🔢 Puntos", callback_data="edit_field:points")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:actions:view:{action_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar acción {action_id}: {e}")
        await callback.answer("❌ Error al cargar la acción para editar", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:levels:edit:"))
async def callback_config_edit_level(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar un nivel específico."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        level = await configuration_service.get_level(level_id)

        await state.update_data(editing_id=level_id)
        await state.set_state(LevelConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Nivel</b>\n\n"
            f"<b>Actual:</b> {level.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🔢 Min Puntos", callback_data="edit_field:min_points")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Max Puntos", callback_data="edit_field:max_points"),
            InlineKeyboardButton(text="🔄 Multiplicador", callback_data="edit_field:multiplier")
        )
        builder.row(
            InlineKeyboardButton(text="😊 Icono", callback_data="edit_field:icon"),
            InlineKeyboardButton(text="🎨 Color", callback_data="edit_field:color")
        )
        builder.row(
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status"),
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:levels:view:{level_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar nivel {level_id}: {e}")
        await callback.answer("❌ Error al cargar el nivel para editar", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:badges:edit:"))
async def callback_config_edit_badge(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar un badge específico."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        badge = await configuration_service.get_badge_by_id(badge_id)

        await state.update_data(editing_id=badge_id)
        await state.set_state(BadgeConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Badge</b>\n\n"
            f"<b>Actual:</b> {badge.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="😊 Icono", callback_data="edit_field:icon")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="📋 Tipo Req.", callback_data="edit_field:req_type")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Valor Req.", callback_data="edit_field:req_value"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:badges:view:{badge_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar badge {badge_id}: {e}")
        await callback.answer("❌ Error al cargar el badge para editar", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:rewards:edit:"))
async def callback_config_edit_reward(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar una recompensa específica."""
    reward_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        reward = await configuration_service.get_reward(reward_id)

        await state.update_data(editing_id=reward_id)
        await state.set_state(RewardConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Recompensa</b>\n\n"
            f"<b>Actual:</b> {reward.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🏷️ Tipo", callback_data="edit_field:type")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Puntos", callback_data="edit_field:points"),
            InlineKeyboardButton(text="🏆 Badge", callback_data="edit_field:badge")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:rewards:view:{reward_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar recompensa {reward_id}: {e}")
        await callback.answer("❌ Error al cargar la recompensa para editar", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:missions:edit:"))
async def callback_config_edit_mission(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar una misión específica."""
    mission_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        mission = await configuration_service.get_mission(mission_id)

        await state.update_data(editing_id=mission_id)
        await state.set_state(MissionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Misión</b>\n\n"
            f"<b>Actual:</b> {mission.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🏷️ Tipo", callback_data="edit_field:type")
        )
        builder.row(
            InlineKeyboardButton(text="🎯 Acción Obj.", callback_data="edit_field:target_action"),
            InlineKeyboardButton(text="🔢 Valor Obj.", callback_data="edit_field:target_value")
        )
        builder.row(
            InlineKeyboardButton(text="⏰ Límite T.", callback_data="edit_field:time_limit"),
            InlineKeyboardButton(text="🔁 Repetible", callback_data="edit_field:repeatable")
        )
        builder.row(
            InlineKeyboardButton(text="⏱️ Cooldown", callback_data="edit_field:cooldown"),
            InlineKeyboardButton(text="🎁 Recompensa", callback_data="edit_field:reward")
        )
        builder.row(
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status"),
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:missions:view:{mission_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar misión {mission_id}: {e}")
        await callback.answer("❌ Error al cargar la misión para editar", show_alert=True)

    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA ELIMINAR ITEMS
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data.startswith("config:actions:delete:"))
async def callback_config_delete_action(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar una acción específica."""
    action_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        action = await configuration_service.get_action_by_id(action_id)

        text = (
            f"🗑️ <b>Eliminar Acción</b>\n\n"
            f"<b>Nombre:</b> {action.display_name}\n"
            f"<b>Clave:</b> {action.action_key}\n\n"
            "<b>¿Estás seguro de que deseas eliminar esta acción?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        from bot.utils.config_keyboards import confirm_keyboard
        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:action:{action_id}",
            cancel_callback=f"config:actions:view:{action_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de acción {action_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:levels:delete:"))
async def callback_config_delete_level(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar un nivel específico."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        level = await configuration_service.get_level(level_id)

        text = (
            f"🗑️ <b>Eliminar Nivel</b>\n\n"
            f"<b>Nombre:</b> {level.name}\n"
            f"<b>Icono:</b> {level.icon}\n\n"
            "<b>¿Estás seguro de que deseas eliminar este nivel?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        from bot.utils.config_keyboards import confirm_keyboard
        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:level:{level_id}",
            cancel_callback=f"config:levels:view:{level_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de nivel {level_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:badges:delete:"))
async def callback_config_delete_badge(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar un badge específico."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        badge = await configuration_service.get_badge_by_id(badge_id)

        text = (
            f"🗑️ <b>Eliminar Badge</b>\n\n"
            f"<b>Nombre:</b> {badge.name}\n"
            f"<b>Icono:</b> {badge.icon}\n\n"
            "<b>¿Estás seguro de que deseas eliminar este badge?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        from bot.utils.config_keyboards import confirm_keyboard
        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:badge:{badge_id}",
            cancel_callback=f"config:badges:view:{badge_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de badge {badge_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:rewards:delete:"))
async def callback_config_delete_reward(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar una recompensa específica."""
    reward_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        reward = await configuration_service.get_reward(reward_id)

        text = (
            f"🗑️ <b>Eliminar Recompensa</b>\n\n"
            f"<b>Nombre:</b> {reward.name}\n"
            f"<b>Tipo:</b> {reward.reward_type}\n\n"
            "<b>¿Estás seguro de que deseas eliminar esta recompensa?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        from bot.utils.config_keyboards import confirm_keyboard
        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:reward:{reward_id}",
            cancel_callback=f"config:rewards:view:{reward_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de recompensa {reward_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@config_router.callback_query(F.data.startswith("config:missions:delete:"))
async def callback_config_delete_mission(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar una misión específica."""
    mission_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        mission = await configuration_service.get_mission(mission_id)

        text = (
            f"🗑️ <b>Eliminar Misión</b>\n\n"
            f"<b>Nombre:</b> {mission.name}\n"
            f"<b>Tipo:</b> {mission.mission_type}\n\n"
            "<b>¿Estás seguro de que deseas eliminar esta misión?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        from bot.utils.config_keyboards import confirm_keyboard
        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:mission:{mission_id}",
            cancel_callback=f"config:missions:view:{mission_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de misión {mission_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA SELECCIÓN DE CAMPO A EDITAR
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data.startswith("edit_field:"))
async def callback_config_select_edit_field(
    callback: CallbackQuery,
    state: FSMContext
):
    """Seleccionar campo específico para editar."""
    field = callback.data.split(":")[1]
    data = await state.get_data()
    editing_id = data.get("editing_id")
    editing_type = data.get("editing_type")

    # Mensaje genérico - cada tipo de entidad manejará la lógica específica
    await state.update_data(editing_field=field)

    if editing_type == "action":
        await state.set_state(ActionConfigStates.edit_value)
        # Aquí iría la lógica específica para solicitar el nuevo valor del campo
        text = f"✏️ <b>Editando campo '{field}' de la acción</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "level":
        await state.set_state(LevelConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' del nivel</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "badge":
        await state.set_state(BadgeConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' del badge</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "reward":
        await state.set_state(RewardConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' de la recompensa</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "mission":
        await state.set_state(MissionConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' de la misión</b>\n\nIngresa el nuevo valor:"
    else:
        await callback.answer("❌ Tipo de entidad desconocido", show_alert=True)
        return

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA EDITAR VALORES (inputs del usuario)
# ═══════════════════════════════════════════════════════════════

@config_router.message(ActionConfigStates.edit_value)
async def message_edit_action_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de acción."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Obtener la acción actual para obtener la action_key
        action = await configuration_service.get_action_by_id(editing_id)
        action_key = action.action_key

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["display_name"] = new_value
        elif editing_field == "points":
            try:
                points = int(new_value)
                if points < 0:
                    await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["points_amount"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "description":
            update_kwargs["description"] = new_value if new_value else None
        elif editing_field == "status":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si"]:
                update_kwargs["is_active"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_active"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'activo' o 'inactivo'.\n\n"
                    "Inténtalo de nuevo:"
                )
                return

        # Actualizar la acción
        updated_action = await configuration_service.update_action(
            action_key=action_key,
            **update_kwargs
        )

        await message.answer(
            f"✅ Acción actualizada correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición de la acción
        await state.update_data(editing_id=editing_id, editing_type="action")
        await state.set_state(ActionConfigStates.edit_select)

        # Volver a mostrar los detalles de la acción
        text = (
            f"📊 <b>Detalles de la Acción</b>\n\n"
            f"<b>Nombre:</b> {updated_action.display_name}\n"
            f"<b>Clave:</b> {updated_action.action_key}\n"
            f"<b>Puntos:</b> {updated_action.points_amount}\n"
            f"<b>Descripción:</b> {updated_action.description or 'Sin descripción'}\n"
            f"<b>Activa:</b> {'Sí' if updated_action.is_active else 'No'}\n"
            f"<b>Creada:</b> {updated_action.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
            "<i>¿Qué deseas hacer con esta acción?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:actions",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de acción: {e}")
        await message.answer("❌ Error al actualizar la acción. Inténtalo de nuevo.")


@config_router.message(LevelConfigStates.edit_value)
async def message_edit_level_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de nivel."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["name"] = new_value
        elif editing_field == "min_points":
            try:
                points = int(new_value)
                if points < 0:
                    await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["min_points"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos mínimos.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "max_points":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["max_points"] = None
                else:
                    points = int(new_value)
                    if points < 0:
                        await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["max_points"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos máximos o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "multiplier":
            try:
                multiplier = float(new_value)
                if multiplier < 0.1 or multiplier > 10:
                    await message.answer("❌ El multiplicador debe estar entre 0.1 y 10.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["multiplier"] = multiplier
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para el multiplicador.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "icon":
            # Validar que sea un emoji o caracteres válidos
            if len(new_value) > 4:  # Permitir un emoji o texto corto
                await message.answer("❌ El icono debe ser un emoji o texto corto.\n\nInténtalo de nuevo:")
                return
            update_kwargs["icon"] = new_value
        elif editing_field == "color":
            # Puede ser un código de color o texto, aceptamos cualquier valor o vacío
            update_kwargs["color"] = new_value if new_value else None
        elif editing_field == "status":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si"]:
                update_kwargs["is_active"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_active"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'activo' o 'inactivo'.\n\n"
                    "Inténtalo de nuevo:"
                )
                return

        # Actualizar el nivel
        updated_level = await configuration_service.update_level(
            level_id=editing_id,
            **update_kwargs
        )

        await message.answer(
            f"✅ Nivel actualizado correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición del nivel
        await state.update_data(editing_id=editing_id, editing_type="level")
        await state.set_state(LevelConfigStates.edit_select)

        # Volver a mostrar los detalles del nivel
        text = (
            f"📈 <b>Detalles del Nivel</b>\n\n"
            f"<b>Nombre:</b> {updated_level.name}\n"
            f"<b>Icono:</b> {updated_level.icon}\n"
            f"<b>Puntos mínimos:</b> {updated_level.min_points}\n"
            f"<b>Puntos máximos:</b> {updated_level.max_points or '∞'}\n"
            f"<b>Multiplicador:</b> {updated_level.multiplier}x\n"
            f"<b>Color:</b> {updated_level.color or 'Sin color'}\n"
            f"<b>Orden:</b> {updated_level.order}\n"
            f"<b>Activo:</b> {'Sí' if updated_level.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este nivel?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:levels",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de nivel: {e}")
        await message.answer("❌ Error al actualizar el nivel. Inténtalo de nuevo.")


@config_router.message(BadgeConfigStates.edit_value)
async def message_edit_badge_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de badge."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Obtener el badge actual para obtener la badge_key
        badge = await configuration_service.get_badge_by_id(editing_id)
        badge_key = badge.badge_key

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["name"] = new_value
        elif editing_field == "icon":
            # Validar que sea un emoji o caracteres válidos
            if len(new_value) > 4:  # Permitir un emoji o texto corto
                await message.answer("❌ El icono debe ser un emoji o texto corto.\n\nInténtalo de nuevo:")
                return
            update_kwargs["icon"] = new_value
        elif editing_field == "description":
            update_kwargs["description"] = new_value if new_value else None
        elif editing_field == "req_type":
            valid_types = [
                "total_reactions",
                "total_points",
                "streak_days",
                "is_vip",
                "total_missions",
                "level_reached",
                "custom"
            ]
            if new_value.lower() not in valid_types:
                await message.answer(
                    f"❌ Tipo de requisito inválido.\n"
                    f"Opciones válidas: {', '.join(valid_types)}\n\n"
                    "Inténtalo de nuevo:"
                )
                return
            update_kwargs["requirement_type"] = new_value.lower()
        elif editing_field == "req_value":
            try:
                value = int(new_value)
                if value < 0:
                    await message.answer("❌ El valor del requisito no puede ser negativo.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["requirement_value"] = value
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para el valor del requisito.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "status":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si"]:
                update_kwargs["is_active"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_active"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'activo' o 'inactivo'.\n\n"
                    "Inténtalo de nuevo:"
                )
                return

        # Actualizar el badge
        updated_badge = await configuration_service.update_badge(
            badge_key=badge_key,
            **update_kwargs
        )

        await message.answer(
            f"✅ Badge actualizado correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición del badge
        await state.update_data(editing_id=editing_id, editing_type="badge")
        await state.set_state(BadgeConfigStates.edit_select)

        # Volver a mostrar los detalles del badge
        text = (
            f"🏆 <b>Detalles del Badge</b>\n\n"
            f"<b>Icono:</b> {updated_badge.icon}\n"
            f"<b>Nombre:</b> {updated_badge.name}\n"
            f"<b>Clave:</b> {updated_badge.badge_key}\n"
            f"<b>Tipo de requisito:</b> {updated_badge.requirement_type}\n"
            f"<b>Valor del requisito:</b> {updated_badge.requirement_value}\n"
            f"<b>Descripción:</b> {updated_badge.description or 'Sin descripción'}\n"
            f"<b>Activo:</b> {'Sí' if updated_badge.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este badge?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:badges",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de badge: {e}")
        await message.answer("❌ Error al actualizar el badge. Inténtalo de nuevo.")


@config_router.message(RewardConfigStates.edit_value)
async def message_edit_reward_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de recompensa."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["name"] = new_value
        elif editing_field == "type":
            valid_types = ["points", "badge", "both", "custom"]
            if new_value.lower() not in valid_types:
                await message.answer(
                    f"❌ Tipo de recompensa inválido.\n"
                    f"Opciones válidas: {', '.join(valid_types)}\n\n"
                    "Inténtalo de nuevo:"
                )
                return
            update_kwargs["reward_type"] = new_value.lower()
        elif editing_field == "points":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["points_amount"] = None
                else:
                    points = int(new_value)
                    if points < 0:
                        await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["points_amount"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "badge":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["badge_id"] = None
                else:
                    badge_id = int(new_value)
                    # Validar que el badge exista
                    await configuration_service.get_badge_by_id(badge_id)
                    update_kwargs["badge_id"] = badge_id
            except ValueError:
                await message.answer("❌ Por favor ingresa un ID de badge válido o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "description":
            update_kwargs["description"] = new_value if new_value else None
        elif editing_field == "status":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si"]:
                update_kwargs["is_active"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_active"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'activo' o 'inactivo'.\n\n"
                    "Inténtalo de nuevo:"
                )
                return

        # Actualizar la recompensa
        updated_reward = await configuration_service.update_reward(
            reward_id=editing_id,
            **update_kwargs
        )

        await message.answer(
            f"✅ Recompensa actualizada correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición de la recompensa
        await state.update_data(editing_id=editing_id, editing_type="reward")
        await state.set_state(RewardConfigStates.edit_select)

        # Volver a mostrar los detalles de la recompensa
        badge_info = ""
        if updated_reward.badge:
            badge_info = f"\n<b>Badge:</b> {updated_reward.badge.icon} {updated_reward.badge.name}"

        text = (
            f"🎁 <b>Detalles de la Recompensa</b>\n\n"
            f"<b>Nombre:</b> {updated_reward.name}\n"
            f"<b>Tipo:</b> {updated_reward.reward_type}\n"
            f"<b>Puntos:</b> {updated_reward.points_amount or 'N/A'}\n"
            f"<b>Descripción:</b> {updated_reward.description or 'Sin descripción'}\n"
            f"{badge_info}\n"
            f"<b>Activa:</b> {'Sí' if updated_reward.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta recompensa?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:rewards",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de recompensa: {e}")
        await message.answer("❌ Error al actualizar la recompensa. Inténtalo de nuevo.")


@config_router.message(MissionConfigStates.edit_value)
async def message_edit_mission_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de misión."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["name"] = new_value
        elif editing_field == "type":
            valid_types = ["single", "streak", "cumulative", "timed"]
            if new_value.lower() not in valid_types:
                await message.answer(
                    f"❌ Tipo de misión inválido.\n"
                    f"Opciones válidas: {', '.join(valid_types)}\n\n"
                    "Inténtalo de nuevo:"
                )
                return
            update_kwargs["mission_type"] = new_value.lower()
        elif editing_field == "target_action":
            if new_value.lower() in ["none", "null", "n/a", ""]:
                update_kwargs["target_action"] = None
            else:
                # Validar que la acción exista
                try:
                    await configuration_service.get_action(new_value)
                    update_kwargs["target_action"] = new_value
                except Exception:
                    await message.answer(
                        "❌ La acción especificada no existe.\n"
                        "Verifica la clave de la acción e inténtalo de nuevo:"
                    )
                    return
        elif editing_field == "target_value":
            try:
                value = int(new_value)
                if value <= 0:
                    await message.answer("❌ El valor objetivo debe ser positivo.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["target_value"] = value
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para el valor objetivo.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "time_limit":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["time_limit_hours"] = None
                else:
                    hours = int(new_value)
                    if hours < 0:
                        await message.answer("❌ Las horas no pueden ser negativas.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["time_limit_hours"] = hours
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para las horas o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "repeatable":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si", "yes"]:
                update_kwargs["is_repeatable"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_repeatable"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'sí' o 'no' para repetible.\n\n"
                    "Inténtalo de nuevo:"
                )
                return
        elif editing_field == "cooldown":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["cooldown_hours"] = None
                else:
                    hours = int(new_value)
                    if hours < 0:
                        await message.answer("❌ Las horas no pueden ser negativas.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["cooldown_hours"] = hours
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para las horas o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "reward":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["reward_id"] = None
                else:
                    reward_id = int(new_value)
                    # Validar que la recompensa exista
                    await configuration_service.get_reward(reward_id)
                    update_kwargs["reward_id"] = reward_id
            except ValueError:
                await message.answer("❌ Por favor ingresa un ID de recompensa válido o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "status":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si"]:
                update_kwargs["is_active"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_active"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'activo' o 'inactivo'.\n\n"
                    "Inténtalo de nuevo:"
                )
                return

        # Actualizar la misión
        updated_mission = await configuration_service.update_mission(
            mission_id=editing_id,
            **update_kwargs
        )

        await message.answer(
            f"✅ Misión actualizada correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición de la misión
        await state.update_data(editing_id=editing_id, editing_type="mission")
        await state.set_state(MissionConfigStates.edit_select)

        # Volver a mostrar los detalles de la misión
        reward_info = ""
        if updated_mission.reward:
            reward_info = f"\n<b>Recompensa:</b> {updated_mission.reward.name}"

        text = (
            f"🎯 <b>Detalles de la Misión</b>\n\n"
            f"<b>Nombre:</b> {updated_mission.name}\n"
            f"<b>Tipo:</b> {updated_mission.mission_type}\n"
            f"<b>Acción objetivo:</b> {updated_mission.target_action or 'N/A'}\n"
            f"<b>Valor objetivo:</b> {updated_mission.target_value}\n"
            f"<b>Límite de tiempo:</b> {updated_mission.time_limit_hours or 'N/A'}h\n"
            f"<b>Repetible:</b> {'Sí' if updated_mission.is_repeatable else 'No'}\n"
            f"{reward_info}\n"
            f"<b>Activa:</b> {'Sí' if updated_mission.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta misión?</i>"
        )

        from bot.utils.config_keyboards import config_item_keyboard
        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:missions",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de misión: {e}")
        await message.answer("❌ Error al actualizar la misión. Inténtalo de nuevo.")


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA CONFIRMAR EDICIÓN (edit_confirm)
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data == "edit_confirm:continue")
async def callback_edit_confirm_continue(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Continuar editando el mismo elemento."""
    data = await state.get_data()
    editing_type = data.get("editing_type")
    editing_id = data.get("editing_id")

    if editing_type == "action":
        await state.set_state(ActionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Acción</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🔢 Puntos", callback_data="edit_field:points")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:actions:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "level":
        await state.set_state(LevelConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Nivel</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🔢 Min Puntos", callback_data="edit_field:min_points")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Max Puntos", callback_data="edit_field:max_points"),
            InlineKeyboardButton(text="🔄 Multiplicador", callback_data="edit_field:multiplier")
        )
        builder.row(
            InlineKeyboardButton(text="😊 Icono", callback_data="edit_field:icon"),
            InlineKeyboardButton(text="🎨 Color", callback_data="edit_field:color")
        )
        builder.row(
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status"),
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:levels:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "badge":
        await state.set_state(BadgeConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Badge</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="😊 Icono", callback_data="edit_field:icon")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="📋 Tipo Req.", callback_data="edit_field:req_type")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Valor Req.", callback_data="edit_field:req_value"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:badges:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "reward":
        await state.set_state(RewardConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Recompensa</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🏷️ Tipo", callback_data="edit_field:type")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Puntos", callback_data="edit_field:points"),
            InlineKeyboardButton(text="🏆 Badge", callback_data="edit_field:badge")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:rewards:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "mission":
        await state.set_state(MissionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Misión</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🏷️ Tipo", callback_data="edit_field:type")
        )
        builder.row(
            InlineKeyboardButton(text="🎯 Acción Obj.", callback_data="edit_field:target_action"),
            InlineKeyboardButton(text="🔢 Valor Obj.", callback_data="edit_field:target_value")
        )
        builder.row(
            InlineKeyboardButton(text="⏰ Límite T.", callback_data="edit_field:time_limit"),
            InlineKeyboardButton(text="🔁 Repetible", callback_data="edit_field:repeatable")
        )
        builder.row(
            InlineKeyboardButton(text="⏱️ Cooldown", callback_data="edit_field:cooldown"),
            InlineKeyboardButton(text="🎁 Recompensa", callback_data="edit_field:reward")
        )
        builder.row(
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status"),
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:missions:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    await callback.answer()


@config_router.callback_query(F.data == "edit_confirm:finish")
async def callback_edit_confirm_finish(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Finalizar edición y volver al listado."""
    data = await state.get_data()
    editing_type = data.get("editing_type")

    # Limpiar estado y volver al listado correspondiente
    await state.clear()

    if editing_type == "action":
        await callback_config_actions(callback, state, session)
    elif editing_type == "level":
        await callback_config_levels(callback, state, session)
    elif editing_type == "badge":
        await callback_config_badges(callback, state, session)
    elif editing_type == "reward":
        await callback_config_rewards(callback, state, session)
    elif editing_type == "mission":
        await callback_config_missions(callback, state, session)
    else:
        # Si no se reconoce el tipo, volver al menú principal
        await callback_config_main(callback, state, session)

    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# HANDLERS PARA CONFIRMAR ELIMINACIÓN
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data.startswith("confirm_delete:"))
async def callback_config_confirm_delete(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Confirmar eliminación de un elemento."""
    _, entity_type, entity_id_str = callback.data.split(":")
    entity_id = int(entity_id_str)

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        # Determinar qué servicio usar según el tipo
        if entity_type == "action":
            # Para acciones, necesitamos obtener la key primero
            action = await configuration_service.get_action_by_id(entity_id)
            await configuration_service.delete_action(action.action_key)
            message = "acción"
        elif entity_type == "level":
            await configuration_service.delete_level(entity_id)
            message = "nivel"
        elif entity_type == "badge":
            # Para badges, necesitamos obtener la key primero
            badge = await configuration_service.get_badge_by_id(entity_id)
            await configuration_service.delete_badge(badge.badge_key)
            message = "badge"
        elif entity_type == "reward":
            await configuration_service.delete_reward(entity_id)
            message = "recompensa"
        elif entity_type == "mission":
            await configuration_service.delete_mission(entity_id)
            message = "misión"
        else:
            await callback.answer("❌ Tipo de entidad desconocido", show_alert=True)
            return

        await callback.message.edit_text(
            text=f"✅ {message.capitalize()} eliminado/a correctamente.",
            parse_mode="HTML"
        )

        # Limpiar estado y volver al menú principal
        await state.clear()

    except Exception as e:
        logger.error(f"Error al eliminar {entity_type} {entity_id}: {e}")
        await callback.answer(f"❌ Error al eliminar el/la {message}", show_alert=True)

    await callback.answer()


# ═══════════════════════════════════════════════════════════════
# NAVEGACIÓN ENTRE SUBMENÚS
# ═══════════════════════════════════════════════════════════════

@config_router.callback_query(F.data.endswith(":list"))
async def callback_config_back_to_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Volver a la lista correspondiente al tipo de configuración."""
    # Extraer el tipo de configuración del callback data
    config_type = callback.data.replace(":list", "").replace("config:", "")

    # Redirigir al handler correspondiente
    if config_type == "actions":
        await callback_config_actions(callback, state, session)
    elif config_type == "levels":
        await callback_config_levels(callback, state, session)
    elif config_type == "badges":
        await callback_config_badges(callback, state, session)
    elif config_type == "rewards":
        await callback_config_rewards(callback, state, session)
    elif config_type == "missions":
        await callback_config_missions(callback, state, session)
    else:
        # Si no coincide con ninguno, volver al menú principal
        await callback_config_main(callback, state, session)


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