"""
Handlers de usuario para el Gabinete (Tienda).

Permite a los usuarios:
- Ver catálogo de artículos del Gabinete
- Ver detalles de artículos
- Adquirir artículos con voz de Lucien
"""

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.services.container import ShopContainer
from bot.shop.database.enums import ItemType, ItemRarity
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)

# Router para handlers de tienda de usuario
shop_user_router = Router(name="shop_user")

# Aplicar middleware de database
from bot.middlewares import DatabaseMiddleware
shop_user_router.message.middleware(DatabaseMiddleware())
shop_user_router.callback_query.middleware(DatabaseMiddleware())


# =============================================================================
# FASE 3: TRACKING DE COMPORTAMIENTO
# =============================================================================

async def _track_shop_action(
    session: AsyncSession,
    user_id: int,
    action_type: str,
    item_id: Optional[int] = None,
    item_category: Optional[str] = None
):
    """
    Registra acciones en la tienda para tracking de comportamiento (FASE 3).

    Args:
        session: Sesión de BD
        user_id: ID del usuario
        action_type: Tipo de acción (view_category, view_item, purchase)
        item_id: ID del item (opcional)
        item_category: Categoría del item (opcional)
    """
    try:
        from bot.gamification.services.behavior_tracking import BehaviorTrackingService

        tracking = BehaviorTrackingService(session)

        if action_type == "view_category":
            # Exploración de categoría
            await tracking.track_button_click(
                user_id=user_id,
                button_id=f"shop:cat:{item_category}",
                context="shop_category",
                time_to_click=0.0,  # No tenemos tiempo exacto
                is_exploration=True,
                is_direct_action=False
            )

        elif action_type == "view_item":
            # Ver detalles de item (exploración)
            await tracking.track_button_click(
                user_id=user_id,
                button_id=f"shop:item:{item_id}",
                context="shop_item_detail",
                time_to_click=0.0,
                is_exploration=True,
                is_direct_action=False
            )

        elif action_type == "purchase":
            # Compra (acción directa)
            await tracking.track_button_click(
                user_id=user_id,
                button_id=f"shop:buy:{item_id}",
                context="shop_purchase",
                time_to_click=0.0,
                is_exploration=False,
                is_direct_action=True
            )

        logger.debug(f"📊 Tracking: Usuario {user_id} acción shop: {action_type}")

    except Exception as e:
        # No fallar el flujo principal por errores de tracking
        logger.warning(f"⚠️ Error en tracking de shop: {e}")


def _build_cabinet_main_keyboard() -> InlineKeyboardMarkup:
    """Construye teclado principal del Gabinete con categorías FASE 4."""
    buttons = [
        [InlineKeyboardButton(text="⚡ Efímeros", callback_data="shop:cat:efimeros")],
        [InlineKeyboardButton(text="🎖️ Distintivos", callback_data="shop:cat:distintivos")],
        [InlineKeyboardButton(text="🔑 Llaves", callback_data="shop:cat:llaves")],
        [InlineKeyboardButton(text="💎 Reliquias", callback_data="shop:cat:reliquias")],
        [InlineKeyboardButton(text="⭐ Destacados", callback_data="shop:featured")],
        [InlineKeyboardButton(text="🎒 Mi Mochila", callback_data="backpack:main")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="profile:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_category_keyboard(
    items: list,
    category_slug: str,
    page: int = 0,
    items_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Construye teclado de artículos de una categoría."""
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
    buttons.append([InlineKeyboardButton(text="🔙 Volver al Gabinete", callback_data="shop:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_item_detail_keyboard(
    item_id: int,
    can_purchase: bool,
    reason: str = ""
) -> InlineKeyboardMarkup:
    """Construye teclado de detalle de artículo."""
    buttons = []

    if can_purchase:
        buttons.append([
            InlineKeyboardButton(text="💎 Adquirir", callback_data=f"shop:buy:{item_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text=f"❌ {reason[:30]}", callback_data="shop:cannot_buy")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@shop_user_router.message(Command("tienda", "shop", "store", "gabinete"))
async def cmd_shop(message: Message, session: AsyncSession):
    """Handler para /tienda - Muestra el Gabinete principal."""
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
        f"🏛️ <b>El Gabinete</b>\n\n"
        f"{LucienMessages.shop('SHOP_MAIN_HEADER')}\n\n"
        f"{LucienMessages.shop('SHOP_SALDO_HEADER')} <b>{user_besitos}</b> Besitos\n\n"
        f"📦 {summary['total_items']} artículos disponibles\n"
        f"📁 {summary['total_categories']} categorías\n\n"
        "Seleccione una categoría para explorar:"
    )

    await message.answer(
        text,
        reply_markup=_build_cabinet_main_keyboard(),
        parse_mode="HTML"
    )


@shop_user_router.callback_query(F.data == "shop:main")
async def callback_shop_main(callback: CallbackQuery, session: AsyncSession):
    """Callback para volver al menú principal del Gabinete."""
    container = ShopContainer(session)

    summary = await container.shop.get_shop_summary()

    try:
        from bot.gamification.database.models import UserGamification
        user_gamif = await session.get(UserGamification, callback.from_user.id)
        user_besitos = user_gamif.total_besitos if user_gamif else 0
    except Exception:
        user_besitos = 0

    text = (
        f"🏛️ <b>El Gabinete</b>\n\n"
        f"{LucienMessages.shop('SHOP_MAIN_HEADER')}\n\n"
        f"{LucienMessages.shop('SHOP_SALDO_HEADER')} <b>{user_besitos}</b> Besitos\n\n"
        f"📦 {summary['total_items']} artículos disponibles\n"
        f"📁 {summary['total_categories']} categorías\n\n"
        "Seleccione una categoría para explorar:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=_build_cabinet_main_keyboard(),
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

    # Obtener categoría
    category = await container.shop.get_category_by_slug(category_slug)
    if not category:
        await callback.answer(
            LucienMessages.errors("NOT_FOUND_SHORT"),
            show_alert=True
        )
        return

    # Obtener items
    items = await container.shop.get_items_by_category(category.id)

    if not items:
        text = (
            f"{category.emoji} <b>{category.name}</b>\n\n"
            f"{LucienMessages.shop('SHOP_CATEGORY_EMPTY')}"
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
        f"📦 {len(items)} artículos disponibles"
    )

    # FASE 3: Tracking de vista de categoría
    await _track_shop_action(session, callback.from_user.id, "view_category", item_category=category_slug)

    await callback.message.edit_text(
        text,
        reply_markup=_build_category_keyboard(items, category_slug, page),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data == "shop:featured")
async def callback_shop_featured(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver artículos destacados."""
    container = ShopContainer(session)

    items = await container.shop.get_featured_items(limit=10)

    if not items:
        text = (
            "⭐ <b>Artículos Destacados</b>\n\n"
            f"{LucienMessages.shop('SHOP_CATEGORY_EMPTY')}"
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
        "⭐ <b>Artículos Destacados</b>\n\n"
        f"{LucienMessages.shop('SHOP_FEATURED_HEADER')}"
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
    """Callback para ver detalle de un artículo."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    item_id = int(callback.data.split(":")[2])
    item = await container.shop.get_item(item_id)

    if not item:
        await callback.answer(
            LucienMessages.errors("NOT_FOUND_SHORT"),
            show_alert=True
        )
        return

    # Verificar si puede adquirir
    can_buy, reason = await container.shop.can_purchase_item(user_id, item_id)

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

    # FASE 4: Precio con descuento
    pricing = await container.discounts.calculate_price_with_discount(user_id, item)
    discount_pct = pricing["discount_percentage"]

    if discount_pct > 0:
        text += (
            f"\n💋 <b>Precio:</b> <s>{pricing['original_price']}</s> → "
            f"<b>{pricing['final_price']}</b> Besitos\n"
            f"✨ <b>Descuento:</b> {discount_pct}% (ahorras {pricing['savings']} Besitos)\n"
        )
    else:
        text += f"\n💋 <b>Precio:</b> {item.price_besitos} Besitos\n"

    text += f"💰 <b>Su saldo:</b> {user_besitos} Besitos\n"

    if item.stock is not None:
        text += f"📦 <b>Disponibles:</b> {item.stock}\n"

    if item.requires_vip:
        text += "⭐ <b>Requiere:</b> Suscripción VIP\n"

    # FASE 4: Información de item temporal
    if item.is_temporal:
        if item.time_until_expiry:
            hours_left = item.time_until_expiry // 3600
            text += f"⏰ <b>Expira en:</b> {hours_left} horas\n"
        if item.event_name:
            text += f"🎉 <b>Evento:</b> {item.event_name}\n"

    # Verificar si ya lo tiene
    has_item = await container.inventory.has_item(user_id, item_id)
    if has_item:
        text += f"\n{LucienMessages.shop('SHOP_ALREADY_OWNED')}"

    # FASE 3: Tracking de vista de item
    await _track_shop_action(session, user_id, "view_item", item_id=item_id)

    await callback.message.edit_text(
        text,
        reply_markup=_build_item_detail_keyboard(item_id, can_buy, reason),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data.startswith("shop:buy:"))
async def callback_shop_buy(callback: CallbackQuery, session: AsyncSession):
    """Callback para adquirir un artículo."""
    container = ShopContainer(session)
    user_id = callback.from_user.id

    item_id = int(callback.data.split(":")[2])

    # Intentar adquirir
    success, message, purchase = await container.shop.purchase_item(user_id, item_id)

    if success:
        # FASE 3: Tracking de compra exitosa
        await _track_shop_action(session, user_id, "purchase", item_id=item_id)

        item = await container.shop.get_item(item_id)
        text = (
            f"🎉 <b>Adquisición Exitosa</b>\n\n"
            f"{LucienMessages.shop('SHOP_PURCHASE_SUCCESS', item_name=item.name)}\n\n"
            f"💋 Pagó: {purchase.price_paid} Besitos"
        )
        buttons = [
            [InlineKeyboardButton(text="🎒 Ver Mochila", callback_data="backpack:main")],
            [InlineKeyboardButton(text="🏛️ Seguir Explorando", callback_data="shop:main")],
        ]
    else:
        # Usar mensaje de Lucien según el error
        if "insufficiente" in message.lower() or "besitos" in message.lower():
            error_msg = LucienMessages.shop("SHOP_INSUFFICIENT_FUNDS")
        elif "vip" in message.lower():
            error_msg = LucienMessages.shop("SHOP_REQUIRES_VIP")
        elif "stock" in message.lower():
            error_msg = LucienMessages.shop("SHOP_NO_STOCK")
        elif "ya tiene" in message.lower() or "owned" in message.lower():
            error_msg = LucienMessages.shop("SHOP_ALREADY_OWNED")
        else:
            error_msg = message

        text = f"❌ <b>Adquisición No Completada</b>\n\n{error_msg}"
        buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="shop:main")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_user_router.callback_query(F.data == "shop:cannot_buy")
async def callback_cannot_buy(callback: CallbackQuery):
    """Callback cuando no se puede adquirir."""
    await callback.answer(
        "No puede adquirir este artículo en este momento",
        show_alert=True
    )
