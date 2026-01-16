"""
Shop Handler - Tienda de gamificación para usuarios.

Handlers:
- Menú de tienda por categorías
- Listado de items por categoría
- Vista de detalle de item
- Confirmación de compra
- Ejecución de compra
"""
import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.main import user_router
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from bot.database.enums import ShopItemType

logger = logging.getLogger(__name__)


def create_shop_menu_keyboard() -> InlineKeyboardMarkup:
    """Crea keyboard del menú de tienda."""
    builder = InlineKeyboardBuilder()

    # Categorías
    builder.row(
        InlineKeyboardButton(text="🏅 Badges", callback_data="shop:cat:badge"),
        InlineKeyboardButton(text="🏆 Niveles", callback_data="shop:cat:level")
    )

    builder.row(
        InlineKeyboardButton(text="⭐ Días VIP", callback_data="shop:cat:vip_days"),
        InlineKeyboardButton(text="📦 Media Sets", callback_data="shop:cat:media_set")
    )

    # Volver
    builder.row(
        InlineKeyboardButton(text="🔙 Volver al Perfil", callback_data="user:profile")
    )

    return builder.as_markup()


@user_router.callback_query(F.data == "user:shop")
async def callback_shop_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el menú de la tienda.

    Categorías:
    - Badges
    - Niveles (solo info, no se compran)
    - Días VIP
    - Media Sets
    """
    logger.debug(f"🛒 Usuario {callback.from_user.id} abriendo tienda")

    container = ServiceContainer(session, callback.bot)

    # Obtener puntos del usuario
    points = await container.points.get_balance(callback.from_user.id)
    user_points = points.balance if points else 0

    text = (
        f"🛒 <b>Tienda de Gamificación</b>\n\n"
        f"💰 <b>Tus Puntos:</b> {user_points} besitos\n\n"
        f"Selecciona una categoría:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_shop_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("shop:cat:"))
async def callback_shop_category(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra items de una categoría.

    Args:
        callback_data: shop:cat:{item_type}
    """
    callback_data = callback.data
    item_type_str = callback_data.split(":")[-1]

    # Mapear string a enum
    item_type_map = {
        "badge": ShopItemType.BADGE,
        "level": ShopItemType.LEVEL,
        "vip_days": ShopItemType.VIP_DAYS,
        "media_set": ShopItemType.MEDIA_SET
    }

    item_type = item_type_map.get(item_type_str)

    if item_type is None:
        await callback.answer("Categoría inválida", show_alert=True)
        return

    container = ServiceContainer(session, callback.bot)

    # Niveles no se compran
    if item_type == ShopItemType.LEVEL:
        await callback.answer(
            "⚠️ Los niveles se obtienen automáticamente acumulando puntos",
            show_alert=True
        )
        return

    # Obtener items de la categoría
    items = await container.shop.get_active_items(item_type)

    if not items:
        await callback.answer("No hay items disponibles en esta categoría", show_alert=True)
        return

    # Crear keyboard con items
    keyboard_buttons = []
    for item in items:
        stock_text = f"({item.stock})" if item.stock >= 0 else "∞"

        keyboard_buttons.append([{
            "text": f"{item.name} - {item.price_points} pts {stock_text}",
            "callback_data": f"shop:view:{item.id}"
        }])

    keyboard_buttons.append([{
        "text": "🔙 Volver a la Tienda",
        "callback_data": "user:shop"
    }])

    category_names = {
        ShopItemType.BADGE: "🏅 Badges",
        ShopItemType.VIP_DAYS: "⭐ Días VIP",
        ShopItemType.MEDIA_SET: "📦 Media Sets"
    }

    text = (
        f"{category_names.get(item_type, 'Categoría')}\n\n"
        f"Selecciona un item para ver detalles:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("shop:view:"))
async def callback_shop_view_item(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra detalles de un item.

    Args:
        callback_data: shop:view:{item_id}
    """
    item_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    item = await container.shop.get_item(item_id)

    if item is None:
        await callback.answer("Item no encontrado", show_alert=True)
        return

    # Obtener puntos del usuario
    points = await container.points.get_balance(callback.from_user.id)
    user_points = points.balance if points else 0

    can_afford = user_points >= item.price_points
    stock_text = f"{item.stock} disponibles" if item.stock >= 0 else "Ilimitado"

    # Nombre del tipo
    type_names = {
        ShopItemType.BADGE: "🏅 Badge",
        ShopItemType.LEVEL: "🏆 Nivel",
        ShopItemType.VIP_DAYS: "⭐ Días VIP",
        ShopItemType.MEDIA_SET: "📦 Media Set"
    }

    text = (
        f"<b>{item.name}</b>\n\n"
        f"{type_names.get(item.item_type, 'Item')}\n\n"
        f"{item.description}\n\n"
        f"💰 <b>Precio:</b> {item.price_points} puntos\n"
        f"📦 <b>Stock:</b> {stock_text}\n\n"
    )

    if not can_afford:
        text += f"⚠️ <b>Te faltan {item.price_points - user_points} puntos</b>\n\n"

    keyboard_buttons = []

    # Botón de comprar si puede pagar
    if can_afford and item.active:
        if item.stock == 0:
            keyboard_buttons.append([{
                "text": "❌ Agotado",
                "callback_data": "shop:cancel"
            }])
        else:
            keyboard_buttons.append([{
                "text": f"✅ Comprar ({item.price_points} pts)",
                "callback_data": f"shop:buy:{item.id}"
            }])

    keyboard_buttons.append([{
        "text": "🔙 Volver",
        "callback_data": f"shop:cat:{item.item_type.value}"
    }])

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("shop:buy:"))
async def callback_shop_buy(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Confirma y ejecuta la compra de un item.

    Args:
        callback_data: shop:buy:{item_id}
    """
    item_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)

    # Ejecutar compra
    success, msg, purchase = await container.shop.purchase_item(
        user_id=callback.from_user.id,
        item_id=item_id
    )

    if success:
        await callback.answer(
            f"✅ {msg}",
            show_alert=True
        )

        # Volver al menú de tienda
        await callback.message.edit_text(
            text="✅ <b>¡Compra realizada!</b>\n\n" + msg,
            reply_markup=create_shop_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer(
            f"❌ {msg}",
            show_alert=True
        )


@user_router.callback_query(F.data == "shop:cancel")
async def callback_shop_cancel(callback: CallbackQuery):
    """Cancela la compra y vuelve atrás."""
    await callback.answer("Compra cancelada")
