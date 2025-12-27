"""
Handlers de usuario para la Mochila (Inventario).

Permite a los usuarios:
- Ver su inventario completo
- Ver detalles de items poseídos
- Usar items consumibles
- Equipar/desequipar cosméticos
"""

import logging
from typing import Optional, List

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.services.container import ShopContainer
from bot.shop.database.enums import ItemType, ItemRarity
from bot.shop.database.models import UserInventoryItem

logger = logging.getLogger(__name__)

# Router para handlers de mochila
backpack_router = Router(name="backpack")


def _build_backpack_main_keyboard() -> InlineKeyboardMarkup:
    """Construye teclado principal de la mochila."""
    buttons = [
        [InlineKeyboardButton(text="📜 Artefactos", callback_data="backpack:type:narrative")],
        [InlineKeyboardButton(text="💾 Digital", callback_data="backpack:type:digital")],
        [InlineKeyboardButton(text="🧪 Consumibles", callback_data="backpack:type:consumable")],
        [InlineKeyboardButton(text="✨ Cosméticos", callback_data="backpack:type:cosmetic")],
        [InlineKeyboardButton(text="📊 Historial de Compras", callback_data="backpack:history")],
        [InlineKeyboardButton(text="🏪 Ir a Tienda", callback_data="shop:main")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="menu:main")],
    ]
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


@backpack_router.message(Command("mochila", "backpack", "inventory"))
async def cmd_backpack(message: Message, session: AsyncSession):
    """Handler para /mochila - Muestra el inventario del usuario."""
    container = ShopContainer(session)
    user_id = message.from_user.id

    # Obtener resumen del inventario
    summary = await container.inventory.get_inventory_summary(user_id)

    text = (
        "🎒 <b>Tu Mochila</b>\n\n"
        f"📦 Items totales: <b>{summary['total_items']}</b>\n"
        f"💋 Total gastado: <b>{summary['total_spent']}</b> besitos\n"
    )

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
        reply_markup=_build_backpack_main_keyboard(),
        parse_mode="HTML"
    )


@backpack_router.callback_query(F.data == "backpack:main")
async def callback_backpack_main(callback: CallbackQuery, session: AsyncSession):
    """Callback para volver al menú principal de mochila."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    summary = await container.inventory.get_inventory_summary(user_id)

    text = (
        "🎒 <b>Tu Mochila</b>\n\n"
        f"📦 Items totales: <b>{summary['total_items']}</b>\n"
        f"💋 Total gastado: <b>{summary['total_spent']}</b> besitos\n"
    )

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
        reply_markup=_build_backpack_main_keyboard(),
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
