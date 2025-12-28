"""
Handlers del menú principal de administración de gamificación.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType, RewardType

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# COMANDOS DE ENTRADA
# ========================================

@router.message(Command("gamification"))
@router.message(Command("gamif"))
async def gamification_menu(message: Message):
    """Muestra menú principal de gamificación."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data="gamif:admin:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="gamif:admin:rewards")
        ],
        [
            InlineKeyboardButton(text="⭐ Niveles", callback_data="gamif:admin:levels"),
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="gamif:admin:stats")
        ],
        [
            InlineKeyboardButton(text="💰 Transacciones", callback_data="gamif:admin:transactions"),
            InlineKeyboardButton(text="🔧 Configuración", callback_data="gamif:admin:config")
        ],
        [
            InlineKeyboardButton(text="🎨 Wizard Creación", callback_data="unified:wizard:menu"),
            InlineKeyboardButton(text="📊 Panel Central", callback_data="config_panel:main")
        ]
    ])

    await message.answer(
        "🎮 <b>Panel de Gamificación</b>\n\n"
        "Gestiona misiones, recompensas y niveles del sistema.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ========================================
# MENÚ PRINCIPAL
# ========================================

@router.callback_query(F.data == "gamif:menu")
async def show_main_menu(callback: CallbackQuery):
    """Volver al menú principal."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data="gamif:admin:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="gamif:admin:rewards")
        ],
        [
            InlineKeyboardButton(text="⭐ Niveles", callback_data="gamif:admin:levels"),
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="gamif:admin:stats")
        ],
        [
            InlineKeyboardButton(text="💰 Transacciones", callback_data="gamif:admin:transactions"),
            InlineKeyboardButton(text="🔧 Configuración", callback_data="gamif:admin:config")
        ],
        [
            InlineKeyboardButton(text="🎨 Wizard Creación", callback_data="unified:wizard:menu"),
            InlineKeyboardButton(text="📊 Panel Central", callback_data="config_panel:main")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="admin:main")
        ]
    ])

    await callback.message.edit_text(
        "🎮 <b>Panel de Gamificación</b>\n\n"
        "Gestiona misiones, recompensas y niveles del sistema.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ MISIONES
# ========================================

@router.callback_query(F.data == "gamif:admin:missions")
async def missions_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Submenú de gestión de misiones."""
    # Contar misiones activas
    missions = await gamification.mission.get_all_missions()
    count = len(missions)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Wizard Crear", callback_data="gamif:wizard:mission"),
            InlineKeyboardButton(text="📝 Listar", callback_data="gamif:missions:list")
        ],
        [
            InlineKeyboardButton(text="📄 Plantillas", callback_data="gamif:missions:templates"),
            InlineKeyboardButton(text="⚙️ Config Avanzada", callback_data="gamif:missions:advanced")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ]
    ])

    await callback.message.edit_text(
        f"📋 <b>Gestión de Misiones</b>\n\n"
        f"Misiones activas: {count}\n\n"
        f"• <b>Wizard:</b> Creación guiada paso a paso\n"
        f"• <b>Listar:</b> Ver y editar misiones existentes\n"
        f"• <b>Plantillas:</b> Aplicar configuraciones predefinidas",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ RECOMPENSAS
# ========================================

@router.callback_query(F.data == "gamif:admin:rewards")
async def rewards_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Submenú de gestión de recompensas."""
    rewards = await gamification.reward.get_all_rewards()
    badges = await gamification.reward.get_all_rewards(reward_type=RewardType.BADGE)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Wizard Crear", callback_data="gamif:wizard:reward"),
            InlineKeyboardButton(text="📝 Listar", callback_data="gamif:rewards:list")
        ],
        [
            InlineKeyboardButton(text="🏆 Badges", callback_data="gamif:rewards:badges"),
            InlineKeyboardButton(text="🎁 Set de Badges", callback_data="gamif:rewards:badge_set")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ]
    ])

    await callback.message.edit_text(
        f"🎁 <b>Gestión de Recompensas</b>\n\n"
        f"Recompensas totales: {len(rewards)}\n"
        f"Badges: {len(badges)}\n\n"
        f"Crea recompensas con unlock conditions automáticas.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ NIVELES
# ========================================

@router.callback_query(F.data == "gamif:admin:levels")
async def levels_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Submenú de gestión de niveles."""
    levels = await gamification.level.get_all_levels()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Crear Nivel", callback_data="gamif:wizard:level_prog"),
            InlineKeyboardButton(text="📝 Listar", callback_data="gamif:levels:list")
        ],
        [
            InlineKeyboardButton(text="📊 Distribución", callback_data="gamif:levels:distribution")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ]
    ])

    await callback.message.edit_text(
        f"⭐ <b>Gestión de Niveles</b>\n\n"
        f"Niveles configurados: {len(levels)}\n\n"
        f"Los niveles determinan la progresión de usuarios según besitos.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# LISTADOS
# ========================================

@router.callback_query(F.data == "gamif:missions:list")
async def list_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista todas las misiones."""
    missions = await gamification.mission.get_all_missions()

    if not missions:
        await callback.answer("No hay misiones creadas", show_alert=True)
        return

    text = "📋 <b>Misiones Activas</b>\n\n"
    keyboard_buttons = []

    for mission in missions:  # Mostrar todas las misiones
        type_icon = {
            MissionType.ONE_TIME: "🎯",
            MissionType.DAILY: "📅",
            MissionType.WEEKLY: "📆",
            MissionType.STREAK: "🔥"
        }.get(MissionType(mission.mission_type), "📋")

        text += f"{type_icon} <b>{mission.name}</b>\n"
        text += f"   Recompensa: {mission.besitos_reward} besitos\n\n"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{type_icon} {mission.name}",
                callback_data=f"gamif:mission:view:{mission.id}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:missions")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:rewards:list")
async def list_rewards(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista todas las recompensas."""
    rewards = await gamification.reward.get_all_rewards()

    if not rewards:
        await callback.answer("No hay recompensas creadas", show_alert=True)
        return

    text = "🎁 <b>Recompensas Disponibles</b>\n\n"
    keyboard_buttons = []

    for reward in rewards:  # Mostrar todas las recompensas
        type_icon = {
            RewardType.BADGE: "🏆",
            RewardType.PERMISSION: "🔑",
            RewardType.BESITOS: "💰",
            RewardType.ITEM: "🎁"
        }.get(RewardType(reward.reward_type), "🎁")

        text += f"{type_icon} <b>{reward.name}</b>\n"
        text += f"   Tipo: {reward.reward_type.title()}\n\n"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{type_icon} {reward.name}",
                callback_data=f"gamif:reward:view:{reward.id}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:rewards")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:levels:list")
async def list_levels(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista todos los niveles ordenados."""
    levels = await gamification.level.get_all_levels()

    if not levels:
        await callback.answer("No hay niveles creados", show_alert=True)
        return

    text = "⭐ <b>Niveles Configurados</b>\n\n"

    for level in levels:
        text += f"<b>{level.order}. {level.name}</b>\n"
        text += f"   Requiere: {level.min_besitos} besitos\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:levels")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:levels:distribution")
async def show_level_distribution(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra la distribución de usuarios por nivel."""
    distribution = await gamification.level.get_level_distribution()

    if not distribution:
        await callback.answer("No hay datos de distribución disponibles", show_alert=True)
        return

    text = "📊 <b>Distribución de Usuarios por Nivel</b>\n\n"

    # Calcular total de usuarios
    total_users = sum(distribution.values())

    # Mostrar cada nivel con su conteo y porcentaje
    for level_name, count in distribution.items():
        percentage = (count / total_users * 100) if total_users > 0 else 0
        bar_length = int(percentage / 5)  # 20 caracteres máximo
        bar = "█" * bar_length + "░" * (20 - bar_length)

        text += f"<b>{level_name}</b>\n"
        text += f"{bar} {percentage:.1f}%\n"
        text += f"👥 {count} usuario{'s' if count != 1 else ''}\n\n"

    text += f"<b>Total:</b> {total_users} usuario{'s' if total_users != 1 else ''}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:levels")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
