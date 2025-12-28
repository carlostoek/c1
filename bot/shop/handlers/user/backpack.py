"""
Handlers de usuario para la Mochila (Inventario) Unificada.

Permite a los usuarios:
- Ver su inventario completo con filtros
- Ver detalles de items poseídos
- Usar items consumibles
- Equipar/desequipar cosméticos
- Ver pistas narrativas con información especial
- Filtrar por modo de obtención (recompensas, descubrimientos)
"""

import logging
import json
from typing import Optional, List, Dict, Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.services.container import ShopContainer
from bot.shop.database.enums import ItemType, ItemRarity, ObtainedVia
from bot.shop.database.models import UserInventoryItem, ShopItem

logger = logging.getLogger(__name__)

# Router para handlers de mochila
backpack_router = Router(name="backpack")

# Aplicar middleware de database
from bot.middlewares import DatabaseMiddleware
backpack_router.message.middleware(DatabaseMiddleware())
backpack_router.callback_query.middleware(DatabaseMiddleware())


# ============================================================
# HELPERS PARA PISTAS
# ============================================================

def _is_clue_item(item) -> bool:
    """Verifica si un item es una pista narrativa."""
    if item.item_type != ItemType.NARRATIVE.value:
        return False
    if not item.item_metadata:
        return False
    try:
        metadata = json.loads(item.item_metadata) if isinstance(item.item_metadata, str) else item.item_metadata
        return metadata.get("is_clue", False)
    except (json.JSONDecodeError, TypeError):
        return False


def _get_clue_metadata(item) -> Dict[str, Any]:
    """Obtiene metadata de pista de un item."""
    if not item.item_metadata:
        return {}
    try:
        metadata = json.loads(item.item_metadata) if isinstance(item.item_metadata, str) else item.item_metadata
        return metadata
    except (json.JSONDecodeError, TypeError):
        return {}


def _build_backpack_main_keyboard(clues_count: int = 0, rewards_count: int = 0) -> InlineKeyboardMarkup:
    """Construye teclado principal de la mochila."""
    buttons = []

    # Filtros especiales (pistas y recompensas)
    special_row = []
    if clues_count > 0:
        special_row.append(
            InlineKeyboardButton(text=f"🔍 Pistas ({clues_count})", callback_data="backpack:filter:clues")
        )
    if rewards_count > 0:
        special_row.append(
            InlineKeyboardButton(text=f"🎁 Recompensas ({rewards_count})", callback_data="backpack:filter:rewards")
        )
    if special_row:
        buttons.append(special_row)

    # Categorías por tipo
    buttons.extend([
        [InlineKeyboardButton(text="📜 Artefactos", callback_data="backpack:type:narrative")],
        [
            InlineKeyboardButton(text="💾 Digital", callback_data="backpack:type:digital"),
            InlineKeyboardButton(text="🧪 Consumibles", callback_data="backpack:type:consumable"),
        ],
        [InlineKeyboardButton(text="✨ Cosméticos", callback_data="backpack:type:cosmetic")],
        [InlineKeyboardButton(text="📊 Historial", callback_data="backpack:history")],
        [
            InlineKeyboardButton(text="🏪 Tienda", callback_data="shop:main"),
            InlineKeyboardButton(text="🔙 Volver", callback_data="menu:main"),
        ],
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_items_list_keyboard(
    items: List[UserInventoryItem],
    item_type: str,
    page: int = 0,
    items_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Construye teclado de lista de items."""
    buttons = []

    # Paginación
    start = page * items_per_page
    end = start + items_per_page
    page_items = items[start:end]

    for inv_item in page_items:
        item = inv_item.item
        qty_text = f" x{inv_item.quantity}" if inv_item.quantity > 1 else ""
        equipped = " [E]" if inv_item.is_equipped else ""
        text = f"{item.icon} {item.name}{qty_text}{equipped}"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"backpack:item:{inv_item.id}"
            )
        ])

    # Navegación de páginas
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"backpack:type:{item_type}:{page-1}")
        )
    if end < len(items):
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"backpack:type:{item_type}:{page+1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    # Volver
    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_item_actions_keyboard(
    inv_item: UserInventoryItem
) -> InlineKeyboardMarkup:
    """Construye teclado de acciones para un item."""
    buttons = []
    item = inv_item.item

    if item.item_type == ItemType.CONSUMABLE.value:
        buttons.append([
            InlineKeyboardButton(
                text="🧪 Usar",
                callback_data=f"backpack:use:{inv_item.id}"
            )
        ])

    if item.item_type == ItemType.COSMETIC.value:
        if inv_item.is_equipped:
            buttons.append([
                InlineKeyboardButton(
                    text="⬇️ Desequipar",
                    callback_data=f"backpack:unequip:{inv_item.id}"
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text="⬆️ Equipar",
                    callback_data=f"backpack:equip:{inv_item.id}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="⭐ Favorito",
            callback_data=f"backpack:fav:{inv_item.item_id}"
        )
    ])

    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _get_special_counts(container, user_id: int) -> tuple[int, int]:
    """
    Obtiene conteo de pistas y recompensas usando queries eficientes.

    Optimizado para evitar cargar todos los items en memoria.
    """
    session = container._session

    # Contar recompensas - simple query por obtained_via
    rewards_stmt = (
        select(func.count())
        .select_from(UserInventoryItem)
        .where(
            and_(
                UserInventoryItem.user_id == user_id,
                UserInventoryItem.obtained_via == ObtainedVia.REWARD.value
            )
        )
    )
    rewards_result = await session.execute(rewards_stmt)
    rewards_count = rewards_result.scalar() or 0

    # Contar pistas - require JOIN con ShopItem y filtrado por tipo NARRATIVE
    # Usamos JSON extract para verificar is_clue en metadata
    clues_stmt = (
        select(func.count())
        .select_from(UserInventoryItem)
        .join(ShopItem, UserInventoryItem.item_id == ShopItem.id)
        .where(
            and_(
                UserInventoryItem.user_id == user_id,
                ShopItem.item_type == ItemType.NARRATIVE.value,
                # SQLite json_extract: verificar si item_metadata contiene is_clue: true
                func.json_extract(ShopItem.item_metadata, '$.is_clue') == True
            )
        )
    )
    clues_result = await session.execute(clues_stmt)
    clues_count = clues_result.scalar() or 0

    return clues_count, rewards_count


@backpack_router.message(Command("mochila", "backpack", "inventory"))
async def cmd_backpack(message: Message, session: AsyncSession):
    """Handler para /mochila - Muestra el inventario del usuario."""
    container = ShopContainer(session)
    user_id = message.from_user.id

    # Obtener resumen del inventario
    summary = await container.inventory.get_inventory_summary(user_id)
    clues_count, rewards_count = await _get_special_counts(container, user_id)

    text = (
        "🎒 <b>Tu Mochila</b>\n\n"
        f"📦 Items totales: <b>{summary['total_items']}</b>\n"
        f"💋 Total gastado: <b>{summary['total_spent']}</b> besitos\n"
    )

    # Mostrar pistas y recompensas si hay
    if clues_count > 0 or rewards_count > 0:
        text += "\n<b>Especiales:</b>\n"
        if clues_count > 0:
            text += f"  🔍 {clues_count} pista(s) encontrada(s)\n"
        if rewards_count > 0:
            text += f"  🎁 {rewards_count} recompensa(s) obtenida(s)\n"

    # Mostrar distribución por tipo
    if summary['items_by_type']:
        text += "\n<b>Por categoría:</b>\n"
        type_emojis = {
            "narrative": "📜",
            "digital": "💾",
            "consumable": "🧪",
            "cosmetic": "✨",
        }
        for type_name, data in summary['items_by_type'].items():
            emoji = type_emojis.get(type_name, "📦")
            text += f"  {emoji} {data['count']} items ({data['quantity']} total)\n"

    if summary['equipped_count'] > 0:
        text += f"\n✅ {summary['equipped_count']} item(s) equipado(s)"

    text += "\n\nSelecciona una categoría para ver tus items:"

    await message.answer(
        text,
        reply_markup=_build_backpack_main_keyboard(clues_count, rewards_count),
        parse_mode="HTML"
    )


@backpack_router.callback_query(F.data == "backpack:main")
async def callback_backpack_main(callback: CallbackQuery, session: AsyncSession):
    """Callback para volver al menú principal de mochila."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    summary = await container.inventory.get_inventory_summary(user_id)
    clues_count, rewards_count = await _get_special_counts(container, user_id)

    text = (
        "🎒 <b>Tu Mochila</b>\n\n"
        f"📦 Items totales: <b>{summary['total_items']}</b>\n"
        f"💋 Total gastado: <b>{summary['total_spent']}</b> besitos\n"
    )

    # Mostrar pistas y recompensas si hay
    if clues_count > 0 or rewards_count > 0:
        text += "\n<b>Especiales:</b>\n"
        if clues_count > 0:
            text += f"  🔍 {clues_count} pista(s) encontrada(s)\n"
        if rewards_count > 0:
            text += f"  🎁 {rewards_count} recompensa(s) obtenida(s)\n"

    if summary['items_by_type']:
        text += "\n<b>Por categoría:</b>\n"
        type_emojis = {
            "narrative": "📜",
            "digital": "💾",
            "consumable": "🧪",
            "cosmetic": "✨",
        }
        for type_name, data in summary['items_by_type'].items():
            emoji = type_emojis.get(type_name, "📦")
            text += f"  {emoji} {data['count']} items ({data['quantity']} total)\n"

    if summary['equipped_count'] > 0:
        text += f"\n✅ {summary['equipped_count']} item(s) equipado(s)"

    text += "\n\nSelecciona una categoría para ver tus items:"

    await callback.message.edit_text(
        text,
        reply_markup=_build_backpack_main_keyboard(clues_count, rewards_count),
        parse_mode="HTML"
    )
    await callback.answer()


@backpack_router.callback_query(F.data.startswith("backpack:type:"))
async def callback_backpack_type(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver items de un tipo específico."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    parts = callback.data.split(":")
    type_name = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 0

    # Mapear tipo
    type_map = {
        "narrative": ItemType.NARRATIVE,
        "digital": ItemType.DIGITAL,
        "consumable": ItemType.CONSUMABLE,
        "cosmetic": ItemType.COSMETIC,
    }

    item_type = type_map.get(type_name)
    if not item_type:
        await callback.answer("Tipo no válido", show_alert=True)
        return

    # Obtener items
    items = await container.inventory.get_inventory_items(user_id, item_type=item_type)

    type_emojis = {
        "narrative": "📜 Artefactos Narrativos",
        "digital": "💾 Contenido Digital",
        "consumable": "🧪 Consumibles",
        "cosmetic": "✨ Cosméticos",
    }

    if not items:
        text = (
            f"🎒 <b>{type_emojis.get(type_name, 'Items')}</b>\n\n"
            "No tienes items de este tipo.\n\n"
            "¡Visita la tienda para conseguir algunos!"
        )
        buttons = [
            [InlineKeyboardButton(text="🏪 Ir a Tienda", callback_data="shop:main")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")],
        ]
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = (
        f"🎒 <b>{type_emojis.get(type_name, 'Items')}</b>\n\n"
        f"Tienes {len(items)} item(s) de este tipo:\n"
        "[E] = Equipado"
    )

    await callback.message.edit_text(
        text,
        reply_markup=_build_items_list_keyboard(items, type_name, page),
        parse_mode="HTML"
    )
    await callback.answer()


@backpack_router.callback_query(F.data.startswith("backpack:item:"))
async def callback_backpack_item_detail(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver detalle de un item del inventario."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    inv_item_id = int(callback.data.split(":")[2])

    # Obtener el registro de inventario
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from bot.shop.database.models import UserInventoryItem

    stmt = (
        select(UserInventoryItem)
        .options(selectinload(UserInventoryItem.item))
        .where(
            UserInventoryItem.id == inv_item_id,
            UserInventoryItem.user_id == user_id
        )
    )
    result = await session.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        await callback.answer("Item no encontrado", show_alert=True)
        return

    item = inv_item.item
    rarity = ItemRarity(item.rarity) if item.rarity else ItemRarity.COMMON
    item_type = ItemType(item.item_type)

    text = (
        f"{item.icon} <b>{item.name}</b>\n"
        f"{rarity.emoji} {rarity.display_name} | {item_type.emoji} {item_type.display_name}\n\n"
        f"{item.description}\n"
    )

    if item.long_description:
        text += f"\n{item.long_description}\n"

    text += f"\n📦 <b>Cantidad:</b> {inv_item.quantity}\n"
    text += f"📅 <b>Obtenido:</b> {inv_item.obtained_at.strftime('%d/%m/%Y')}\n"
    text += f"🔑 <b>Vía:</b> {inv_item.obtained_via}\n"

    if inv_item.is_equipped:
        text += "\n✅ <b>Estado:</b> Equipado"

    if inv_item.is_used:
        text += f"\n🕐 <b>Usado:</b> {inv_item.used_at.strftime('%d/%m/%Y') if inv_item.used_at else 'Sí'}"

    await callback.message.edit_text(
        text,
        reply_markup=_build_item_actions_keyboard(inv_item),
        parse_mode="HTML"
    )
    await callback.answer()


@backpack_router.callback_query(F.data.startswith("backpack:use:"))
async def callback_use_item(callback: CallbackQuery, session: AsyncSession):
    """Callback para usar un item consumible."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    inv_item_id = int(callback.data.split(":")[2])

    # Obtener el item_id desde el registro de inventario
    from sqlalchemy import select
    from bot.shop.database.models import UserInventoryItem

    stmt = select(UserInventoryItem).where(
        UserInventoryItem.id == inv_item_id,
        UserInventoryItem.user_id == user_id
    )
    result = await session.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        await callback.answer("Item no encontrado", show_alert=True)
        return

    # Usar el item
    success, message, effect_data = await container.inventory.use_item(
        user_id, inv_item.item_id
    )

    if success:
        text = f"✅ <b>¡Item usado!</b>\n\n{message}"
        if effect_data and effect_data.get("applied"):
            if "besitos_granted" in effect_data:
                text += f"\n\n+{effect_data['besitos_granted']} besitos"
    else:
        text = f"❌ <b>Error</b>\n\n{message}"

    buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@backpack_router.callback_query(F.data.startswith("backpack:equip:"))
async def callback_equip_item(callback: CallbackQuery, session: AsyncSession):
    """Callback para equipar un item cosmético."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    inv_item_id = int(callback.data.split(":")[2])

    # Obtener item_id
    from sqlalchemy import select
    from bot.shop.database.models import UserInventoryItem

    stmt = select(UserInventoryItem).where(
        UserInventoryItem.id == inv_item_id,
        UserInventoryItem.user_id == user_id
    )
    result = await session.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        await callback.answer("Item no encontrado", show_alert=True)
        return

    success, message = await container.inventory.equip_item(user_id, inv_item.item_id)

    await callback.answer(message, show_alert=not success)

    if success:
        # Refrescar vista
        await callback_backpack_item_detail(callback, session)


@backpack_router.callback_query(F.data.startswith("backpack:unequip:"))
async def callback_unequip_item(callback: CallbackQuery, session: AsyncSession):
    """Callback para desequipar un item cosmético."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    inv_item_id = int(callback.data.split(":")[2])

    # Obtener item_id
    from sqlalchemy import select
    from bot.shop.database.models import UserInventoryItem

    stmt = select(UserInventoryItem).where(
        UserInventoryItem.id == inv_item_id,
        UserInventoryItem.user_id == user_id
    )
    result = await session.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        await callback.answer("Item no encontrado", show_alert=True)
        return

    success, message = await container.inventory.unequip_item(user_id, inv_item.item_id)

    await callback.answer(message, show_alert=not success)

    if success:
        # Refrescar vista
        await callback_backpack_item_detail(callback, session)


@backpack_router.callback_query(F.data.startswith("backpack:fav:"))
async def callback_set_favorite(callback: CallbackQuery, session: AsyncSession):
    """Callback para establecer un item como favorito."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    item_id = int(callback.data.split(":")[2])

    success, message = await container.inventory.set_favorite_item(user_id, item_id)

    await callback.answer(
        "⭐ Item favorito actualizado" if success else message,
        show_alert=not success
    )


@backpack_router.callback_query(F.data == "backpack:history")
async def callback_purchase_history(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver historial de compras."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    purchases = await container.inventory.get_purchase_history(user_id, limit=10)

    if not purchases:
        text = (
            "📊 <b>Historial de Compras</b>\n\n"
            "No has realizado ninguna compra aún.\n\n"
            "¡Visita la tienda para comenzar!"
        )
    else:
        text = "📊 <b>Historial de Compras</b>\n\n"
        for purchase in purchases:
            date_str = purchase.purchased_at.strftime("%d/%m/%Y")
            status_emoji = "✅" if purchase.status == "completed" else "↩️"
            text += (
                f"{status_emoji} {date_str} - {purchase.item.name}\n"
                f"   💋 {purchase.price_paid} besitos x{purchase.quantity}\n\n"
            )

    buttons = [
        [InlineKeyboardButton(text="🏪 Ir a Tienda", callback_data="shop:main")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================================
# FILTROS ESPECIALES: PISTAS Y RECOMPENSAS
# ============================================================

def _build_clues_list_keyboard(
    clue_items: List[UserInventoryItem],
    page: int = 0,
    items_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Construye teclado de lista de pistas."""
    buttons = []

    # Paginación
    start = page * items_per_page
    end = start + items_per_page
    page_items = clue_items[start:end]

    for inv_item in page_items:
        item = inv_item.item
        metadata = _get_clue_metadata(item)
        clue_icon = metadata.get("clue_icon", "🔍")
        text = f"{clue_icon} {item.name}"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"backpack:clue:{inv_item.id}"
            )
        ])

    # Navegación de páginas
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"backpack:filter:clues:{page-1}")
        )
    if end < len(clue_items):
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"backpack:filter:clues:{page+1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    # Volver
    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@backpack_router.callback_query(F.data.startswith("backpack:filter:clues"))
async def callback_filter_clues(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver pistas narrativas."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 0

    # Obtener todos los items y filtrar pistas
    all_items = await container.inventory.get_inventory_items(user_id)
    clue_items = [inv for inv in all_items if _is_clue_item(inv.item)]

    if not clue_items:
        text = (
            "🔍 <b>Tus Pistas</b>\n\n"
            "Aún no has encontrado ninguna pista.\n\n"
            "<i>Las pistas se encuentran explorando la historia.\n"
            "Presta atención a los detalles...</i>"
        )
        buttons = [
            [InlineKeyboardButton(text="📖 Ir a Historia", callback_data="narr:start")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")],
        ]
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = (
        "🔍 <b>Tus Pistas</b>\n\n"
        f"Has encontrado <b>{len(clue_items)}</b> pista(s).\n\n"
        "<i>Las pistas te ayudan a avanzar en la historia\n"
        "y desbloquear caminos secretos.</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=_build_clues_list_keyboard(clue_items, page),
        parse_mode="HTML"
    )
    await callback.answer()


@backpack_router.callback_query(F.data.startswith("backpack:clue:"))
async def callback_clue_detail(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver detalle de una pista."""
    user_id = callback.from_user.id
    inv_item_id = int(callback.data.split(":")[2])

    # Obtener el item
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = (
        select(UserInventoryItem)
        .options(selectinload(UserInventoryItem.item))
        .where(
            UserInventoryItem.id == inv_item_id,
            UserInventoryItem.user_id == user_id
        )
    )
    result = await session.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        await callback.answer("Pista no encontrada", show_alert=True)
        return

    item = inv_item.item
    metadata = _get_clue_metadata(item)

    clue_icon = metadata.get("clue_icon", "🔍")
    category = metadata.get("clue_category", "general")
    source_fragment = metadata.get("source_fragment_key")
    required_for = metadata.get("required_for_fragments", [])
    hint = metadata.get("clue_hint")
    lore = metadata.get("lore_text")

    # Construir texto
    text = f"{clue_icon} <b>{item.name}</b>\n"
    text += f"🏷️ Categoría: {category.title()}\n\n"

    if item.description:
        text += f"<i>{item.description}</i>\n\n"

    if lore:
        text += f"📜 <b>Lore:</b>\n{lore}\n\n"

    if source_fragment:
        text += f"📍 <b>Encontrada en:</b> {source_fragment}\n"

    text += f"📅 <b>Obtenida:</b> {inv_item.obtained_at.strftime('%d/%m/%Y %H:%M')}\n"

    if required_for:
        text += f"\n🔓 <b>Desbloquea:</b>\n"
        for frag_key in required_for[:3]:  # Máximo 3 para no saturar
            text += f"  • {frag_key}\n"
        if len(required_for) > 3:
            text += f"  • ...y {len(required_for) - 3} más\n"

    if hint:
        text += f"\n💡 <b>Pista:</b> <i>{hint}</i>"

    buttons = []

    # Botón para ir al fragmento origen
    if source_fragment:
        buttons.append([
            InlineKeyboardButton(
                text="📖 Ver fragmento origen",
                callback_data=f"story:goto:{source_fragment}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Volver a Pistas", callback_data="backpack:filter:clues")])
    buttons.append([InlineKeyboardButton(text="🎒 Ir a Mochila", callback_data="backpack:main")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@backpack_router.callback_query(F.data.startswith("backpack:filter:rewards"))
async def callback_filter_rewards(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver items obtenidos como recompensas."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 0

    # Obtener todos los items y filtrar recompensas
    all_items = await container.inventory.get_inventory_items(user_id)
    reward_items = [inv for inv in all_items if inv.obtained_via == ObtainedVia.REWARD]

    if not reward_items:
        text = (
            "🎁 <b>Tus Recompensas</b>\n\n"
            "Aún no has obtenido ninguna recompensa.\n\n"
            "<i>Completa misiones y explora la historia\n"
            "para obtener recompensas especiales.</i>"
        )
        buttons = [
            [InlineKeyboardButton(text="📖 Ver Misiones", callback_data="gamif:missions")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")],
        ]
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = (
        "🎁 <b>Tus Recompensas</b>\n\n"
        f"Has obtenido <b>{len(reward_items)}</b> recompensa(s).\n\n"
    )

    # Construir lista
    buttons = []
    start = page * 5
    end = start + 5
    page_items = reward_items[start:end]

    for inv_item in page_items:
        item = inv_item.item
        icon = item.icon or "🎁"
        text_btn = f"{icon} {item.name}"
        buttons.append([
            InlineKeyboardButton(
                text=text_btn,
                callback_data=f"backpack:item:{inv_item.id}"
            )
        ])

    # Navegación
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"backpack:filter:rewards:{page-1}")
        )
    if end < len(reward_items):
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"backpack:filter:rewards:{page+1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="backpack:main")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()
