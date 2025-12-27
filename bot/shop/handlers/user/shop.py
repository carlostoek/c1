"""
Handlers de usuario para la Tienda.

Permite a los usuarios:
- Ver catálogo de productos
- Ver detalles de productos
- Comprar productos
"""

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.services.container import ShopContainer
from bot.shop.database.enums import ItemType, ItemRarity

logger = logging.getLogger(__name__)

# Router para handlers de tienda de usuario
shop_user_router = Router(name="shop_user")


def _build_shop_main_keyboard() -> InlineKeyboardMarkup:
    """Construye teclado principal de la tienda."""
    buttons = [
        [InlineKeyboardButton(text="📜 Artefactos Narrativos", callback_data="shop:cat:artefactos-narrativos")],
        [InlineKeyboardButton(text="💾 Contenido Digital", callback_data="shop:cat:contenido-digital")],
        [InlineKeyboardButton(text="🧪 Consumibles", callback_data="shop:cat:consumibles")],
        [InlineKeyboardButton(text="✨ Cosméticos", callback_data="shop:cat:cosmeticos")],
        [InlineKeyboardButton(text="⭐ Destacados", callback_data="shop:featured")],
        [InlineKeyboardButton(text="🎒 Mi Mochila", callback_data="backpack:main")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_category_keyboard(
    items: list,
    category_slug: str,
    page: int = 0,
    items_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Construye teclado de productos de una categoría."""
    buttons = []

    # Paginación
    start = page * items_per_page
    end = start + items_per_page
    page_items = items[start:end]

    for item in page_items:
        rarity_emoji = ItemRarity(item.rarity).emoji if item.rarity else ""
        text = f"{item.icon} {item.name} - {item.price_besitos} 💋"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"shop:item:{item.id}"
            )
        ])

    # Navegación de páginas
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"shop:cat:{category_slug}:{page-1}")
        )
    if end < len(items):
        nav_buttons.append(
            InlineKeyboardButton(text="Siguiente ➡️", callback_data=f"shop:cat:{category_slug}:{page+1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    # Volver
    buttons.append([InlineKeyboardButton(text="🔙 Volver a Tienda", callback_data="shop:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_item_detail_keyboard(
    item_id: int,
    can_purchase: bool,
    reason: str = ""
) -> InlineKeyboardMarkup:
    """Construye teclado de detalle de producto."""
    buttons = []

    if can_purchase:
        buttons.append([
            InlineKeyboardButton(text="🛒 Comprar", callback_data=f"shop:buy:{item_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text=f"❌ {reason[:30]}", callback_data="shop:cannot_buy")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@shop_user_router.message(Command("tienda", "shop", "store"))
async def cmd_shop(message: Message, session: AsyncSession):
    """Handler para /tienda - Muestra la tienda principal."""
    container = ShopContainer(session)

    # Obtener resumen
    summary = await container.shop.get_shop_summary()

    # Obtener besitos del usuario
    try:
        from bot.gamification.database.models import UserGamification
        user_gamif = await session.get(UserGamification, message.from_user.id)
        user_besitos = user_gamif.total_besitos if user_gamif else 0
    except Exception:
        user_besitos = 0

    text = (
        "🏪 <b>Tienda de Artefactos</b>\n\n"
        f"💋 Tu saldo: <b>{user_besitos}</b> besitos\n\n"
        f"📦 {summary['total_items']} productos disponibles\n"
        f"📁 {summary['total_categories']} categorías\n\n"
        "Selecciona una categoría para explorar:"
    )

    await message.answer(
        text,
        reply_markup=_build_shop_main_keyboard(),
        parse_mode="HTML"
    )


@shop_user_router.callback_query(F.data == "shop:main")
async def callback_shop_main(callback: CallbackQuery, session: AsyncSession):
    """Callback para volver al menú principal de tienda."""
    container = ShopContainer(session)

    summary = await container.shop.get_shop_summary()

    try:
        from bot.gamification.database.models import UserGamification
        user_gamif = await session.get(UserGamification, callback.from_user.id)
        user_besitos = user_gamif.total_besitos if user_gamif else 0
    except Exception:
        user_besitos = 0

    text = (
        "🏪 <b>Tienda de Artefactos</b>\n\n"
        f"💋 Tu saldo: <b>{user_besitos}</b> besitos\n\n"
        f"📦 {summary['total_items']} productos disponibles\n"
        f"📁 {summary['total_categories']} categorías\n\n"
        "Selecciona una categoría para explorar:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=_build_shop_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:cat:"))
async def callback_shop_category(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver productos de una categoría."""
    container = ShopContainer(session)

    parts = callback.data.split(":")
    category_slug = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 0

    # Obtener categoría
    category = await container.shop.get_category_by_slug(category_slug)
    if not category:
        await callback.answer("Categoría no encontrada", show_alert=True)
        return

    # Obtener items
    items = await container.shop.get_items_by_category(category.id)

    if not items:
        text = (
            f"{category.emoji} <b>{category.name}</b>\n\n"
            "No hay productos disponibles en esta categoría."
        )
        buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")]]
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = (
        f"{category.emoji} <b>{category.name}</b>\n\n"
        f"{category.description or ''}\n\n"
        f"📦 {len(items)} productos disponibles"
    )

    await callback.message.edit_text(
        text,
        reply_markup=_build_category_keyboard(items, category_slug, page),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data == "shop:featured")
async def callback_shop_featured(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver productos destacados."""
    container = ShopContainer(session)

    items = await container.shop.get_featured_items(limit=10)

    if not items:
        text = (
            "⭐ <b>Productos Destacados</b>\n\n"
            "No hay productos destacados en este momento."
        )
        buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")]]
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = (
        "⭐ <b>Productos Destacados</b>\n\n"
        "Los mejores artículos de nuestra tienda:"
    )

    buttons = []
    for item in items:
        text_item = f"{item.icon} {item.name} - {item.price_besitos} 💋"
        buttons.append([
            InlineKeyboardButton(
                text=text_item,
                callback_data=f"shop:item:{item.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:item:"))
async def callback_shop_item_detail(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver detalle de un producto."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    item_id = int(callback.data.split(":")[2])
    item = await container.shop.get_item(item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Verificar si puede comprar
    can_buy, reason = await container.shop.can_purchase(user_id, item_id)

    # Obtener besitos del usuario
    try:
        from bot.gamification.database.models import UserGamification
        user_gamif = await session.get(UserGamification, user_id)
        user_besitos = user_gamif.total_besitos if user_gamif else 0
    except Exception:
        user_besitos = 0

    # Construir texto
    rarity = ItemRarity(item.rarity)
    item_type = ItemType(item.item_type)

    text = (
        f"{item.icon} <b>{item.name}</b>\n"
        f"{rarity.emoji} {rarity.display_name} | {item_type.emoji} {item_type.display_name}\n\n"
        f"{item.description}\n"
    )

    if item.long_description:
        text += f"\n{item.long_description}\n"

    text += (
        f"\n💋 <b>Precio:</b> {item.price_besitos} besitos\n"
        f"💰 <b>Tu saldo:</b> {user_besitos} besitos\n"
    )

    if item.stock is not None:
        text += f"📦 <b>Stock:</b> {item.stock} disponibles\n"

    if item.requires_vip:
        text += "⭐ <b>Requiere:</b> Suscripción VIP\n"

    # Verificar si ya lo tiene
    has_item = await container.inventory.has_item(user_id, item_id)
    if has_item:
        text += "\n✅ <i>Ya tienes este producto en tu mochila</i>"

    await callback.message.edit_text(
        text,
        reply_markup=_build_item_detail_keyboard(item_id, can_buy, reason),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:buy:"))
async def callback_shop_buy(callback: CallbackQuery, session: AsyncSession):
    """Callback para comprar un producto."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    item_id = int(callback.data.split(":")[2])

    # Intentar comprar
    success, message, purchase = await container.shop.purchase_item(user_id, item_id)

    if success:
        item = await container.shop.get_item(item_id)
        text = (
            f"🎉 <b>¡Compra exitosa!</b>\n\n"
            f"{item.icon} {item.name} ha sido agregado a tu mochila.\n\n"
            f"💋 Pagaste: {purchase.price_paid} besitos"
        )
        buttons = [
            [InlineKeyboardButton(text="🎒 Ver Mochila", callback_data="backpack:main")],
            [InlineKeyboardButton(text="🏪 Seguir Comprando", callback_data="shop:main")],
        ]
    else:
        text = f"❌ <b>No se pudo completar la compra</b>\n\n{message}"
        buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data == "shop:cannot_buy")
async def callback_cannot_buy(callback: CallbackQuery):
    """Callback cuando no se puede comprar."""
    await callback.answer("No puedes comprar este producto en este momento", show_alert=True)
