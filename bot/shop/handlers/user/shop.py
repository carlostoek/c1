"""
Handlers de usuario para El Gabinete de Lucien.

Permite a los usuarios:
- Explorar el catálogo de artículos
- Ver detalles de un artículo
- Adquirir artículos usando Besitos
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.shop.services.container import ShopContainer
from bot.shop.database.enums import ItemRarity, ItemType, PurchaseErrorCode
from bot.middlewares import DatabaseMiddleware
from bot.utils.lucien_messages import Lucien

logger = logging.getLogger(__name__)

shop_user_router = Router(name="shop_user")
shop_user_router.message.middleware(DatabaseMiddleware())
shop_user_router.callback_query.middleware(DatabaseMiddleware())


def _build_gabinete_main_keyboard() -> InlineKeyboardMarkup:
    """Construye el teclado principal del Gabinete."""
    buttons = [
        [InlineKeyboardButton(text="📜 Artefactos Narrativos", callback_data="shop:cat:artefactos-narrativos")],
        [InlineKeyboardButton(text="💾 Contenido Digital", callback_data="shop:cat:contenido-digital")],
        [InlineKeyboardButton(text="🧪 Consumibles", callback_data="shop:cat:consumibles")],
        [InlineKeyboardButton(text="✨ Cosméticos", callback_data="shop:cat:cosmeticos")],
        [InlineKeyboardButton(text="🎒 Mi Mochila", callback_data="backpack:main")],
        [InlineKeyboardButton(text="🔙 Salir del Gabinete", callback_data="profile:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_category_keyboard(items: list, category_slug: str, page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Construye el teclado de artículos de una categoría."""
    buttons = []
    start, end = page * items_per_page, (page + 1) * items_per_page
    page_items = items[start:end]

    for item in page_items:
        text = f"{item.icon} {item.name} - {item.price_besitos} 💋"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"shop:item:{item.id}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"shop:cat:{category_slug}:{page-1}"))
    if end < len(items):
        nav_buttons.append(InlineKeyboardButton(text="Siguiente ➡️", callback_data=f"shop:cat:{category_slug}:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton(text="🔙 Volver al Gabinete", callback_data="shop:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_item_detail_keyboard(item_id: int, can_purchase: bool, reason: str = "") -> InlineKeyboardMarkup:
    """Construye el teclado de detalle de un artículo."""
    buttons = []
    if can_purchase:
        buttons.append([InlineKeyboardButton(text="💎 Adquirir", callback_data=f"shop:confirm:{item_id}")])
    else:
        buttons.append([InlineKeyboardButton(text=f"❌ {reason[:30]}", callback_data="shop:cannot_buy")])
    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _get_user_besitos(session: AsyncSession, user_id: int) -> int:
    """Obtiene el balance de besitos de un usuario."""
    try:
        from bot.gamification.database.models import UserGamification
        user_gamif = await session.get(UserGamification, user_id)
        return user_gamif.total_besitos if user_gamif else 0
    except Exception:
        logger.warning(f"No se pudo obtener el balance de besitos para el usuario {user_id}")
        return 0


@shop_user_router.message(Command("tienda", "shop", "gabinete"))
async def cmd_shop(message: Message, session: AsyncSession):
    """Handler para /gabinete - Muestra la entrada al Gabinete de Lucien."""
    await message.answer(
        Lucien.CABINET_WELCOME,
        reply_markup=_build_gabinete_main_keyboard(),
        parse_mode="HTML"
    )


@shop_user_router.callback_query(F.data == "shop:main")
async def callback_shop_main(callback: CallbackQuery, session: AsyncSession):
    """Callback para volver al menú principal del Gabinete."""
    await callback.message.edit_text(
        Lucien.CABINET_WELCOME,
        reply_markup=_build_gabinete_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:cat:"))
async def callback_shop_category(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver artículos de una categoría."""
    container = ShopContainer(session)
    parts = callback.data.split(":")
    category_slug = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 0

    category = await container.shop.get_category_by_slug(category_slug)
    if not category:
        await callback.answer(Lucien.ERROR_NOT_FOUND, show_alert=True)
        return

    items = await container.shop.get_items_by_category(category.id)
    # TODO: Usar descripciones de Lucien para categorías
    text = f"{category.emoji} <b>{category.name}</b>\n\n{category.description or ''}"
    
    if not items:
        text += "\n\nNo hay artículos disponibles en esta categoría."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")]])
    else:
        text += f"\n\n📦 {len(items)} artículos disponibles."
        keyboard = _build_category_keyboard(items, category_slug, page)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:item:"))
async def callback_shop_item_detail(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver detalle de un artículo."""
    container = ShopContainer(session)
    user_id = callback.from_user.id
    item_id = int(callback.data.split(":")[2])
    item = await container.shop.get_item(item_id)

    if not item:
        await callback.answer(Lucien.ERROR_NOT_FOUND, show_alert=True)
        return

    can_buy, reason, error_code = await container.shop.can_purchase(user_id, item_id)
    user_besitos = await _get_user_besitos(session, user_id)
    
    description = getattr(item, 'description_lucien', item.description)
    if not description: description = "Este artículo no cuenta con una descripción detallada."

    rarity = ItemRarity(item.rarity)
    item_type = ItemType(item.item_type)

    text = (
        f"{item.icon} <b>{item.name}</b>\n"
        f"{rarity.emoji} {rarity.display_name} | {item_type.emoji} {item_type.display_name}\n\n"
        f"<i>{description}</i>\n\n"
        f"💋 <b>Precio:</b> {item.price_besitos} Besitos\n"
        f"💰 <b>Su saldo:</b> {user_besitos} Besitos\n"
    )
    
    has_item = await container.inventory.has_item(user_id, item_id)
    if has_item:
        text += "\n✅ <i>Ya posee este artículo en su inventario.</i>"

    await callback.message.edit_text(
        text,
        reply_markup=_build_item_detail_keyboard(item_id, can_buy, reason),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:confirm:"))
async def callback_shop_confirm_buy(callback: CallbackQuery, session: AsyncSession):
    """Muestra la confirmación antes de adquirir un artículo."""
    container = ShopContainer(session)
    item_id = int(callback.data.split(":")[2])
    item = await container.shop.get_item(item_id)

    if not item:
        await callback.answer(Lucien.ERROR_NOT_FOUND, show_alert=True)
        return
        
    text = Lucien.CABINET_CONFIRM_PURCHASE.format(item_name=item.name, price=item.price_besitos)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar Adquisición", callback_data=f"shop:acquire:{item_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"shop:item:{item_id}")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:acquire:"))
async def callback_shop_acquire(callback: CallbackQuery, session: AsyncSession):
    """Procesa la adquisición de un artículo."""
    container = ShopContainer(session)
    user_id = callback.from_user.id
    item_id = int(callback.data.split(":")[2])

    success, reason_message, _, error_code = await container.shop.purchase_item(user_id, item_id)
    item = await container.shop.get_item(item_id) # needed for name

    if success:
        text = Lucien.CABINET_PURCHASE_SUCCESS.format(item_name=item.name)
        buttons = [
            [InlineKeyboardButton(text="🎒 Ver Inventario", callback_data="backpack:main")],
            [InlineKeyboardButton(text="🏛️ Volver al Gabinete", callback_data="shop:main")],
        ]
    else:
        # Usar error code en lugar de string matching
        if error_code == PurchaseErrorCode.INSUFFICIENT_FUNDS:
            user_besitos = await _get_user_besitos(session, user_id)
            text = Lucien.CABINET_INSUFFICIENT_FUNDS.format(required=item.price_besitos, current=user_besitos)
        else:
            text = f"{Lucien.ERROR_GENERIC}\n\n<i>Motivo: {reason_message}</i>"
        buttons = [[InlineKeyboardButton(text="🔙 Volver al Gabinete", callback_data="shop:main")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data == "shop:cannot_buy")
async def callback_cannot_buy(callback: CallbackQuery):
    """Callback informativo cuando un artículo no se puede comprar."""
    await callback.answer("Hay un motivo por el cual no puede adquirir este artículo en este momento.", show_alert=True)
