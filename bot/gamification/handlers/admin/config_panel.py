"""
Handler del Panel de Configuración Central.

Dashboard con vista unificada de objetos cross-module:
- Estadísticas globales
- Listados de misiones, recompensas, items, capítulos
- Acciones rápidas (activar/desactivar)

Fase 5 de la integración cross-module.
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.states.admin import ConfigPanelStates
from bot.gamification.services.container import GamificationContainer

logger = logging.getLogger(__name__)

PAGE_SIZE = 5

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# COMANDO PRINCIPAL
# ========================================

@router.message(Command("config_panel"))
@router.message(Command("panel"))
async def cmd_config_panel(message: Message, gamification: GamificationContainer):
    """Comando para abrir panel de configuración central."""
    text = await gamification.config_panel.get_dashboard_text()
    keyboard = _build_main_keyboard()

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "config_panel:main")
async def show_config_panel(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra dashboard principal."""
    text = await gamification.config_panel.get_dashboard_text()
    keyboard = _build_main_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


def _build_main_keyboard() -> InlineKeyboardMarkup:
    """Construye teclado principal del panel."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Misiones",
                callback_data="config_panel:list:missions"
            ),
            InlineKeyboardButton(
                text="🎁 Recompensas",
                callback_data="config_panel:list:rewards"
            )
        ],
        [
            InlineKeyboardButton(
                text="🛒 Items Tienda",
                callback_data="config_panel:list:shop_items"
            ),
            InlineKeyboardButton(
                text="📖 Capítulos",
                callback_data="config_panel:list:chapters"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Refrescar",
                callback_data="config_panel:refresh"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Wizard Creación",
                callback_data="unified:wizard:menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Volver al Panel Admin",
                callback_data="gamif:menu"
            )
        ]
    ])


@router.callback_query(F.data == "config_panel:refresh")
async def refresh_panel(callback: CallbackQuery, gamification: GamificationContainer):
    """Refresca el dashboard."""
    text = await gamification.config_panel.get_dashboard_text()
    keyboard = _build_main_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer("✅ Dashboard actualizado")


# ========================================
# LISTADOS
# ========================================

@router.callback_query(F.data.startswith("config_panel:list:missions"))
async def list_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista misiones con paginación."""
    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 1

    # Obtener misiones
    offset = (page - 1) * PAGE_SIZE
    missions = await gamification.config_panel.get_all_missions(
        active_only=False,
        limit=PAGE_SIZE,
        offset=offset
    )

    # Contar total para paginación
    all_missions = await gamification.config_panel.get_all_missions(active_only=False, limit=100)
    total = len(all_missions)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    if not missions:
        await callback.answer("No hay misiones creadas", show_alert=True)
        return

    # Construir texto
    type_icons = {
        'one_time': '🎯',
        'daily': '📅',
        'weekly': '📆',
        'streak': '🔥'
    }

    text = f"📋 <b>Misiones</b> (Página {page}/{total_pages})\n\n"

    for m in missions:
        status = "🟢" if m['is_active'] else "🔴"
        icon = type_icons.get(m['type'], '📋')
        text += f"{status} {icon} <b>{m['name']}</b>\n"
        text += f"   💰 {m['besitos_reward']} besitos | ID: {m['id']}\n\n"

    # Construir teclado con paginación
    keyboard_rows = []

    # Botones de acción para cada misión
    for m in missions:
        action_text = "🔴 Desactivar" if m['is_active'] else "🟢 Activar"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{m['name'][:20]}...",
                callback_data=f"gamif:mission:view:{m['id']}"
            ),
            InlineKeyboardButton(
                text=action_text,
                callback_data=f"config_panel:toggle:mission:{m['id']}"
            )
        ])

    # Navegación
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"config_panel:list:missions:{page-1}"
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Siguiente",
                callback_data=f"config_panel:list:missions:{page+1}"
            )
        )

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="config_panel:main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("config_panel:list:rewards"))
async def list_rewards(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista recompensas con paginación."""
    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 1

    offset = (page - 1) * PAGE_SIZE
    rewards = await gamification.config_panel.get_all_rewards(
        active_only=False,
        limit=PAGE_SIZE,
        offset=offset
    )

    all_rewards = await gamification.config_panel.get_all_rewards(active_only=False, limit=100)
    total = len(all_rewards)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    if not rewards:
        await callback.answer("No hay recompensas creadas", show_alert=True)
        return

    type_icons = {
        'badge': '🏆',
        'permission': '🔑',
        'besitos': '💰',
        'item': '🎁',
        'shop_item': '📦',
        'vip_days': '⭐',
        'narrative_unlock': '📖'
    }

    text = f"🎁 <b>Recompensas</b> (Página {page}/{total_pages})\n\n"

    for r in rewards:
        status = "🟢" if r['is_active'] else "🔴"
        icon = type_icons.get(r['type'], '🎁')
        text += f"{status} {icon} <b>{r['name']}</b>\n"
        text += f"   Tipo: {r['type']} | ID: {r['id']}\n\n"

    keyboard_rows = []

    for r in rewards:
        action_text = "🔴 Desactivar" if r['is_active'] else "🟢 Activar"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{r['name'][:20]}...",
                callback_data=f"gamif:reward:view:{r['id']}"
            ),
            InlineKeyboardButton(
                text=action_text,
                callback_data=f"config_panel:toggle:reward:{r['id']}"
            )
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"config_panel:list:rewards:{page-1}"
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Siguiente",
                callback_data=f"config_panel:list:rewards:{page+1}"
            )
        )

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="config_panel:main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("config_panel:list:shop_items"))
async def list_shop_items(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista items de tienda con paginación."""
    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 1

    offset = (page - 1) * PAGE_SIZE
    items = await gamification.config_panel.get_all_shop_items(
        active_only=False,
        limit=PAGE_SIZE,
        offset=offset
    )

    all_items = await gamification.config_panel.get_all_shop_items(active_only=False, limit=100)
    total = len(all_items)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    if not items:
        await callback.answer("No hay items de tienda", show_alert=True)
        return

    text = f"🛒 <b>Items de Tienda</b> (Página {page}/{total_pages})\n\n"

    for i in items:
        status = "🟢" if i['is_active'] else "🔴"
        text += f"{status} {i['icon']} <b>{i['name']}</b>\n"
        text += f"   💰 {i['price']} besitos | ID: {i['id']}\n\n"

    keyboard_rows = []

    for i in items:
        action_text = "🔴 Desactivar" if i['is_active'] else "🟢 Activar"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{i['icon']} {i['name'][:15]}...",
                callback_data=f"shop:item:view:{i['id']}"
            ),
            InlineKeyboardButton(
                text=action_text,
                callback_data=f"config_panel:toggle:shop_item:{i['id']}"
            )
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"config_panel:list:shop_items:{page-1}"
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Siguiente",
                callback_data=f"config_panel:list:shop_items:{page+1}"
            )
        )

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="config_panel:main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("config_panel:list:chapters"))
async def list_chapters(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista capítulos narrativos con paginación."""
    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 1

    offset = (page - 1) * PAGE_SIZE
    chapters = await gamification.config_panel.get_all_chapters(
        active_only=False,
        limit=PAGE_SIZE,
        offset=offset
    )

    all_chapters = await gamification.config_panel.get_all_chapters(active_only=False, limit=100)
    total = len(all_chapters)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    if not chapters:
        await callback.answer("No hay capítulos narrativos", show_alert=True)
        return

    text = f"📖 <b>Capítulos Narrativos</b> (Página {page}/{total_pages})\n\n"

    for c in chapters:
        status = "🟢" if c['is_active'] else "🔴"
        type_icon = "🆓" if c['type'] == 'FREE' else "⭐"
        text += f"{status} {type_icon} <b>{c['name']}</b>\n"
        text += f"   Orden: {c['order']} | Slug: <code>{c['slug']}</code>\n\n"

    keyboard_rows = []

    for c in chapters:
        action_text = "🔴 Desactivar" if c['is_active'] else "🟢 Activar"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"📖 {c['name'][:15]}...",
                callback_data=f"narrative:chapter:view:{c['id']}"
            ),
            InlineKeyboardButton(
                text=action_text,
                callback_data=f"config_panel:toggle:chapter:{c['id']}"
            )
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"config_panel:list:chapters:{page-1}"
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Siguiente",
                callback_data=f"config_panel:list:chapters:{page+1}"
            )
        )

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="config_panel:main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# ACCIONES RÁPIDAS (TOGGLE)
# ========================================

@router.callback_query(F.data.startswith("config_panel:toggle:mission:"))
async def toggle_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Alterna estado activo de una misión."""
    mission_id = int(callback.data.split(":")[-1])

    success = await gamification.config_panel.toggle_mission_active(mission_id)

    if success:
        await callback.answer("✅ Estado actualizado")
        # Refrescar lista
        await list_missions(callback, gamification)
    else:
        await callback.answer("❌ Error al actualizar", show_alert=True)


@router.callback_query(F.data.startswith("config_panel:toggle:reward:"))
async def toggle_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """Alterna estado activo de una recompensa."""
    reward_id = int(callback.data.split(":")[-1])

    success = await gamification.config_panel.toggle_reward_active(reward_id)

    if success:
        await callback.answer("✅ Estado actualizado")
        await list_rewards(callback, gamification)
    else:
        await callback.answer("❌ Error al actualizar", show_alert=True)


@router.callback_query(F.data.startswith("config_panel:toggle:shop_item:"))
async def toggle_shop_item(callback: CallbackQuery, gamification: GamificationContainer):
    """Alterna estado activo de un item de tienda."""
    item_id = int(callback.data.split(":")[-1])

    success = await gamification.config_panel.toggle_shop_item_active(item_id)

    if success:
        await callback.answer("✅ Estado actualizado")
        await list_shop_items(callback, gamification)
    else:
        await callback.answer("❌ Error al actualizar", show_alert=True)


@router.callback_query(F.data.startswith("config_panel:toggle:chapter:"))
async def toggle_chapter(callback: CallbackQuery, gamification: GamificationContainer):
    """Alterna estado activo de un capítulo."""
    chapter_id = int(callback.data.split(":")[-1])

    success = await gamification.config_panel.toggle_chapter_active(chapter_id)

    if success:
        await callback.answer("✅ Estado actualizado")
        await list_chapters(callback, gamification)
    else:
        await callback.answer("❌ Error al actualizar", show_alert=True)
