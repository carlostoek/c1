"""
Handlers del menú principal de administración de gamificación.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import AdminAuthMiddleware, DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType, RewardType

# Router para handlers de gamificación admin
router = Router(name="gamif_admin")

# Aplicar middlewares (orden correcto: Database primero, AdminAuth después)
router.message.middleware(DatabaseMiddleware())
router.message.middleware(AdminAuthMiddleware())
router.callback_query.middleware(DatabaseMiddleware())
router.callback_query.middleware(AdminAuthMiddleware())


# ========================================
# COMANDOS DE ENTRADA
# ========================================

@router.message(Command("gamification"))
@router.message(Command("gamif"))
async def gamification_menu(message: Message, session: AsyncSession):
    """Muestra menú principal de gamificación."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data="gamif:admin:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="gamif:admin:rewards")
        ],
        [
            InlineKeyboardButton(text="⭐ Niveles", callback_data="gamif:admin:levels"),
            InlineKeyboardButton(text="💬 Reacciones", callback_data="gamif:admin:reactions")
        ],
        [
            InlineKeyboardButton(text="💰 Transacciones", callback_data="gamif:admin:transactions"),
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="gamif:admin:stats")
        ],
        [
            InlineKeyboardButton(text="🔧 Configuración", callback_data="gamif:admin:config")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="admin:main")
        ]
    ])

    await message.answer(
        "🎮 <b>Panel de Gamificación</b>\n\n"
        "Gestiona misiones, recompensas, niveles, reacciones y transacciones del sistema.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ========================================
# MENÚ PRINCIPAL
# ========================================

@router.callback_query(F.data == "gamif:menu")
async def show_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Volver al menú principal."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data="gamif:admin:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="gamif:admin:rewards")
        ],
        [
            InlineKeyboardButton(text="⭐ Niveles", callback_data="gamif:admin:levels"),
            InlineKeyboardButton(text="💬 Reacciones", callback_data="gamif:admin:reactions")
        ],
        [
            InlineKeyboardButton(text="💰 Transacciones", callback_data="gamif:admin:transactions"),
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="gamif:admin:stats")
        ],
        [
            InlineKeyboardButton(text="🔧 Configuración", callback_data="gamif:admin:config")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="admin:main")
        ]
    ])

    await callback.message.edit_text(
        "🎮 <b>Panel de Gamificación</b>\n\n"
        "Gestiona misiones, recompensas, niveles, reacciones y transacciones del sistema.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ MISIONES (viejo - para mantener compatibilidad)
# ========================================

@router.callback_query(F.data == "gamif:missions:old_menu")
async def missions_menu(callback: CallbackQuery, session: AsyncSession):
    """Submenú de gestión de misiones (anterior)."""
    # Contar misiones activas
    gamification = GamificationContainer(session)
    missions = await gamification.mission.get_all_missions()
    count = len(missions)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 CRUD Misiones", callback_data="gamif:admin:missions"),
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
        f"• <b>CRUD:</b> Gestión completa de misiones\n"
        f"• <b>Listar:</b> Ver misiones existentes\n"
        f"• <b>Plantillas:</b> Aplicar configuraciones predefinidas",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ RECOMPENSAS (viejo - para mantener compatibilidad)
# ========================================

@router.callback_query(F.data == "gamif:rewards:old_menu")
async def rewards_menu(callback: CallbackQuery, session: AsyncSession):
    """Submenú de gestión de recompensas (anterior)."""
    gamification = GamificationContainer(session)
    rewards = await gamification.reward.get_all_rewards()
    badges = await gamification.reward.get_all_rewards(reward_type=RewardType.BADGE)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 CRUD Recompensas", callback_data="gamif:admin:rewards"),
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
# SUBMENÚ NIVELES (viejo - para mantener compatibilidad)
# ========================================

@router.callback_query(F.data == "gamif:levels:old_menu")
async def levels_menu(callback: CallbackQuery, session: AsyncSession):
    """Submenú de gestión de niveles (anterior)."""
    gamification = GamificationContainer(session)
    levels = await gamification.level.get_all_levels()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ CRUD Niveles", callback_data="gamif:admin:levels"),
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
# LISTADOS (antiguos - para mantener compatibilidad)
# ========================================

@router.callback_query(F.data == "gamif:missions:list")
async def list_missions(callback: CallbackQuery, session: AsyncSession):
    """Lista todas las misiones (versión antigua)."""
    gamification = GamificationContainer(session)
    missions = await gamification.mission.get_all_missions()

    if not missions:
        await callback.answer("No hay misiones creadas", show_alert=True)
        return

    text = "📋 <b>Misiones Activas</b>\n\n"
    keyboard_buttons = []

    for mission in missions[:10]:  # Mostrar primeras 10
        type_icon = {
            MissionType.ONE_TIME: "🎯",
            MissionType.DAILY: "📅",
            MissionType.WEEKLY: "📆",
            MissionType.STREAK: "🔥"
        }.get(mission.mission_type, "📋")

        text += f"{type_icon} <b>{mission.name}</b>\n"
        text += f"   Recompensa: {mission.besitos_reward} besitos\n\n"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{type_icon} {mission.name}",
                callback_data=f"gamif:mission:view:{mission.id}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:missions:old_menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()