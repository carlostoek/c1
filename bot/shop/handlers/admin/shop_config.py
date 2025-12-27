"""
Handlers de administración de la Tienda.

Permite a los administradores:
- Gestionar categorías
- Crear/editar/eliminar productos
- Ver estadísticas de ventas
- Otorgar items a usuarios
"""

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.shop.services.container import ShopContainer
from bot.shop.database.enums import ItemType, ItemRarity
from bot.shop.states.admin import ItemCreationStates, CategoryCreationStates

logger = logging.getLogger(__name__)

# Router para handlers de admin de tienda
shop_admin_router = Router(name="shop_admin")


def _build_shop_admin_keyboard() -> InlineKeyboardMarkup:
    """Construye teclado principal de admin de tienda."""
    buttons = [
        [InlineKeyboardButton(text="📦 Ver Productos", callback_data="shop_admin:products")],
        [InlineKeyboardButton(text="➕ Crear Producto", callback_data="shop_admin:create_item")],
        [InlineKeyboardButton(text="📁 Gestionar Categorías", callback_data="shop_admin:categories")],
        [InlineKeyboardButton(text="📊 Estadísticas", callback_data="shop_admin:stats")],
        [InlineKeyboardButton(text="🎁 Otorgar Item", callback_data="shop_admin:grant")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@shop_admin_router.callback_query(F.data == "admin:shop")
async def callback_shop_admin_main(callback: CallbackQuery, session: AsyncSession):
    """Menú principal de administración de tienda."""
    container = ShopContainer(session)

    summary = await container.shop.get_shop_summary()

    text = (
        "🏪 <b>Administración de Tienda</b>\n\n"
        f"📦 Productos activos: {summary['total_items']}\n"
        f"📁 Categorías: {summary['total_categories']}\n"
        f"🛒 Ventas totales: {summary['total_purchases']}\n"
        f"💋 Ingresos: {summary['total_revenue']} besitos\n\n"
        "Selecciona una opción:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=_build_shop_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.callback_query(F.data == "shop_admin:products")
async def callback_list_products(callback: CallbackQuery, session: AsyncSession):
    """Lista todos los productos."""
    container = ShopContainer(session)

    items = await container.shop.get_all_items(active_only=False)

    if not items:
        text = "📦 <b>Productos</b>\n\nNo hay productos creados."
        buttons = [
            [InlineKeyboardButton(text="➕ Crear Producto", callback_data="shop_admin:create_item")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin:shop")],
        ]
    else:
        text = f"📦 <b>Productos ({len(items)})</b>\n\n"
        buttons = []

        for item in items[:10]:  # Limitar a 10
            status = "🟢" if item.is_active else "🔴"
            text_btn = f"{status} {item.icon} {item.name} - {item.price_besitos}💋"
            buttons.append([
                InlineKeyboardButton(
                    text=text_btn,
                    callback_data=f"shop_admin:edit_item:{item.id}"
                )
            ])

        if len(items) > 10:
            text += f"\n<i>Mostrando 10 de {len(items)}</i>"

        buttons.append([InlineKeyboardButton(text="➕ Crear Nuevo", callback_data="shop_admin:create_item")])
        buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin:shop")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.callback_query(F.data == "shop_admin:categories")
async def callback_list_categories(callback: CallbackQuery, session: AsyncSession):
    """Lista todas las categorías."""
    container = ShopContainer(session)

    categories = await container.shop.get_all_categories(active_only=False)

    text = f"📁 <b>Categorías ({len(categories)})</b>\n\n"
    buttons = []

    for cat in categories:
        status = "🟢" if cat.is_active else "🔴"
        items = await container.shop.get_items_by_category(cat.id)
        text_btn = f"{status} {cat.emoji} {cat.name} ({len(items)} items)"
        buttons.append([
            InlineKeyboardButton(
                text=text_btn,
                callback_data=f"shop_admin:edit_cat:{cat.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="➕ Nueva Categoría", callback_data="shop_admin:create_cat")])
    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin:shop")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.callback_query(F.data == "shop_admin:stats")
async def callback_shop_stats(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas de la tienda."""
    container = ShopContainer(session)

    summary = await container.shop.get_shop_summary()

    # Top productos más vendidos
    items = await container.shop.get_all_items()
    top_items = []
    for item in items[:5]:
        stats = await container.shop.get_item_stats(item.id)
        if stats.get('total_sold', 0) > 0:
            top_items.append(stats)

    top_items.sort(key=lambda x: x.get('total_sold', 0), reverse=True)

    text = (
        "📊 <b>Estadísticas de Tienda</b>\n\n"
        f"📦 Productos activos: {summary['total_items']}\n"
        f"🛒 Ventas totales: {summary['total_purchases']}\n"
        f"💋 Ingresos totales: {summary['total_revenue']} besitos\n\n"
    )

    if top_items:
        text += "<b>🏆 Top productos:</b>\n"
        for i, stats in enumerate(top_items[:5], 1):
            text += f"{i}. {stats['name']}: {stats['total_sold']} vendidos\n"

    buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="admin:shop")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# CREAR CATEGORÍA
# ========================================

@shop_admin_router.callback_query(F.data == "shop_admin:create_cat")
async def callback_create_category_start(callback: CallbackQuery, state: FSMContext):
    """Inicia el wizard de creación de categoría."""
    await state.set_state(CategoryCreationStates.waiting_for_name)

    text = (
        "📁 <b>Crear Nueva Categoría</b>\n\n"
        "Paso 1/3: Ingresa el <b>nombre</b> de la categoría:\n\n"
        "<i>Ejemplo: Artefactos Mágicos</i>"
    )

    buttons = [[InlineKeyboardButton(text="❌ Cancelar", callback_data="admin:shop")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.message(CategoryCreationStates.waiting_for_name)
async def process_category_name(message: Message, state: FSMContext, session: AsyncSession):
    """Procesa el nombre de la categoría."""
    name = message.text.strip()

    if len(name) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres.")
        return

    if len(name) > 100:
        await message.answer("❌ El nombre no puede tener más de 100 caracteres.")
        return

    await state.update_data(name=name)
    await state.set_state(CategoryCreationStates.waiting_for_description)

    text = (
        f"📁 <b>Crear Categoría: {name}</b>\n\n"
        "Paso 2/3: Ingresa una <b>descripción</b> (opcional):\n\n"
        "<i>Envía '.' para omitir</i>"
    )

    await message.answer(text, parse_mode="HTML")


@shop_admin_router.message(CategoryCreationStates.waiting_for_description)
async def process_category_description(message: Message, state: FSMContext, session: AsyncSession):
    """Procesa la descripción de la categoría."""
    description = message.text.strip()

    if description == ".":
        description = None

    await state.update_data(description=description)
    await state.set_state(CategoryCreationStates.waiting_for_emoji)

    text = (
        "📁 <b>Crear Categoría</b>\n\n"
        "Paso 3/3: Envía un <b>emoji</b> para la categoría:\n\n"
        "<i>Ejemplo: 📜 🔮 ⚔️</i>"
    )

    await message.answer(text, parse_mode="HTML")


@shop_admin_router.message(CategoryCreationStates.waiting_for_emoji)
async def process_category_emoji(message: Message, state: FSMContext, session: AsyncSession):
    """Procesa el emoji y crea la categoría."""
    emoji = message.text.strip()[:10]  # Limitar a 10 chars

    data = await state.get_data()
    name = data.get("name")
    description = data.get("description")

    container = ShopContainer(session)
    category = await container.shop.create_category(
        name=name,
        description=description,
        emoji=emoji
    )

    await state.clear()

    text = (
        f"✅ <b>Categoría creada exitosamente</b>\n\n"
        f"{category.emoji} <b>{category.name}</b>\n"
        f"Slug: {category.slug}\n"
    )
    if category.description:
        text += f"\n{category.description}"

    buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="admin:shop")]]

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


# ========================================
# CREAR PRODUCTO
# ========================================

@shop_admin_router.callback_query(F.data == "shop_admin:create_item")
async def callback_create_item_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Inicia el wizard de creación de producto."""
    container = ShopContainer(session)
    categories = await container.shop.get_all_categories()

    if not categories:
        await callback.answer("Primero debes crear al menos una categoría", show_alert=True)
        return

    await state.set_state(ItemCreationStates.selecting_category)

    text = (
        "📦 <b>Crear Nuevo Producto</b>\n\n"
        "Paso 1/6: Selecciona la <b>categoría</b>:"
    )

    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"{cat.emoji} {cat.name}",
                callback_data=f"item_create:cat:{cat.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Cancelar", callback_data="admin:shop")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.callback_query(
    ItemCreationStates.selecting_category,
    F.data.startswith("item_create:cat:")
)
async def process_item_category(callback: CallbackQuery, state: FSMContext):
    """Procesa la selección de categoría."""
    category_id = int(callback.data.split(":")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(ItemCreationStates.selecting_type)

    text = (
        "📦 <b>Crear Producto</b>\n\n"
        "Paso 2/6: Selecciona el <b>tipo de producto</b>:"
    )

    buttons = [
        [InlineKeyboardButton(text="📜 Narrativo (desbloquea historia)", callback_data="item_create:type:narrative")],
        [InlineKeyboardButton(text="💾 Digital (contenido extra)", callback_data="item_create:type:digital")],
        [InlineKeyboardButton(text="🧪 Consumible (uso único)", callback_data="item_create:type:consumable")],
        [InlineKeyboardButton(text="✨ Cosmético (personalización)", callback_data="item_create:type:cosmetic")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin:shop")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.callback_query(
    ItemCreationStates.selecting_type,
    F.data.startswith("item_create:type:")
)
async def process_item_type(callback: CallbackQuery, state: FSMContext):
    """Procesa la selección de tipo."""
    item_type = callback.data.split(":")[2]
    await state.update_data(item_type=item_type)
    await state.set_state(ItemCreationStates.waiting_for_name)

    text = (
        "📦 <b>Crear Producto</b>\n\n"
        "Paso 3/6: Ingresa el <b>nombre</b> del producto:\n\n"
        "<i>Ejemplo: Llave del Diván Secreto</i>"
    )

    buttons = [[InlineKeyboardButton(text="❌ Cancelar", callback_data="admin:shop")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.message(ItemCreationStates.waiting_for_name)
async def process_item_name(message: Message, state: FSMContext):
    """Procesa el nombre del producto."""
    name = message.text.strip()

    if len(name) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres.")
        return

    if len(name) > 200:
        await message.answer("❌ El nombre no puede tener más de 200 caracteres.")
        return

    await state.update_data(name=name)
    await state.set_state(ItemCreationStates.waiting_for_description)

    text = (
        f"📦 <b>Crear: {name}</b>\n\n"
        "Paso 4/6: Ingresa una <b>descripción corta</b> (máx 500 chars):"
    )

    await message.answer(text, parse_mode="HTML")


@shop_admin_router.message(ItemCreationStates.waiting_for_description)
async def process_item_description(message: Message, state: FSMContext):
    """Procesa la descripción del producto."""
    description = message.text.strip()

    if len(description) > 500:
        await message.answer("❌ La descripción no puede tener más de 500 caracteres.")
        return

    await state.update_data(description=description)
    await state.set_state(ItemCreationStates.waiting_for_price)

    text = (
        "📦 <b>Crear Producto</b>\n\n"
        "Paso 5/6: Ingresa el <b>precio en besitos</b>:\n\n"
        "<i>Ejemplo: 100</i>"
    )

    await message.answer(text, parse_mode="HTML")


@shop_admin_router.message(ItemCreationStates.waiting_for_price)
async def process_item_price(message: Message, state: FSMContext):
    """Procesa el precio del producto."""
    try:
        price = int(message.text.strip())
        if price < 0:
            raise ValueError("Precio negativo")
    except ValueError:
        await message.answer("❌ Ingresa un número válido (ej: 100)")
        return

    await state.update_data(price=price)
    await state.set_state(ItemCreationStates.waiting_for_icon)

    text = (
        "📦 <b>Crear Producto</b>\n\n"
        "Paso 6/6: Envía un <b>emoji/icono</b> para el producto:\n\n"
        "<i>Ejemplo: 🔑 📜 💎</i>"
    )

    await message.answer(text, parse_mode="HTML")


@shop_admin_router.message(ItemCreationStates.waiting_for_icon)
async def process_item_icon(message: Message, state: FSMContext, session: AsyncSession):
    """Procesa el icono y crea el producto."""
    icon = message.text.strip()[:10]

    data = await state.get_data()

    container = ShopContainer(session)

    # Mapear tipo
    type_map = {
        "narrative": ItemType.NARRATIVE,
        "digital": ItemType.DIGITAL,
        "consumable": ItemType.CONSUMABLE,
        "cosmetic": ItemType.COSMETIC,
    }
    item_type = type_map.get(data.get("item_type"), ItemType.DIGITAL)

    success, msg, item = await container.shop.create_item(
        category_id=data.get("category_id"),
        name=data.get("name"),
        description=data.get("description"),
        item_type=item_type,
        price_besitos=data.get("price"),
        icon=icon,
        created_by=message.from_user.id
    )

    await state.clear()

    if success:
        text = (
            f"✅ <b>Producto creado exitosamente</b>\n\n"
            f"{item.icon} <b>{item.name}</b>\n"
            f"Slug: {item.slug}\n"
            f"Tipo: {item_type.display_name}\n"
            f"Precio: {item.price_besitos} besitos"
        )
    else:
        text = f"❌ <b>Error</b>\n\n{msg}"

    buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="admin:shop")]]

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


# ========================================
# EDITAR PRODUCTO
# ========================================

@shop_admin_router.callback_query(F.data.startswith("shop_admin:edit_item:"))
async def callback_edit_item(callback: CallbackQuery, session: AsyncSession):
    """Muestra opciones de edición de un producto."""
    container = ShopContainer(session)

    item_id = int(callback.data.split(":")[2])
    item = await container.shop.get_item(item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    stats = await container.shop.get_item_stats(item_id)

    text = (
        f"{item.icon} <b>{item.name}</b>\n\n"
        f"📁 Categoría: {item.category_id}\n"
        f"💋 Precio: {item.price_besitos}\n"
        f"📦 Stock: {item.stock or 'Ilimitado'}\n"
        f"⭐ Destacado: {'Sí' if item.is_featured else 'No'}\n"
        f"🟢 Activo: {'Sí' if item.is_active else 'No'}\n\n"
        f"📊 Vendidos: {stats.get('total_sold', 0)}\n"
        f"👥 Propietarios: {stats.get('unique_owners', 0)}"
    )

    buttons = [
        [
            InlineKeyboardButton(
                text="⭐ Destacar" if not item.is_featured else "⭐ Quitar Destacado",
                callback_data=f"shop_admin:toggle_featured:{item_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🟢 Activar" if not item.is_active else "🔴 Desactivar",
                callback_data=f"shop_admin:toggle_active:{item_id}"
            )
        ],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="shop_admin:products")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.callback_query(F.data.startswith("shop_admin:toggle_featured:"))
async def callback_toggle_featured(callback: CallbackQuery, session: AsyncSession):
    """Alterna estado destacado de un producto."""
    container = ShopContainer(session)

    item_id = int(callback.data.split(":")[2])
    item = await container.shop.get_item(item_id)

    if item:
        await container.shop.update_item(item_id, is_featured=not item.is_featured)
        await callback.answer("Estado actualizado")
        # Refrescar vista
        await callback_edit_item(callback, session)
    else:
        await callback.answer("Producto no encontrado", show_alert=True)


@shop_admin_router.callback_query(F.data.startswith("shop_admin:toggle_active:"))
async def callback_toggle_active(callback: CallbackQuery, session: AsyncSession):
    """Alterna estado activo de un producto."""
    container = ShopContainer(session)

    item_id = int(callback.data.split(":")[2])
    item = await container.shop.get_item(item_id)

    if item:
        await container.shop.update_item(item_id, is_active=not item.is_active)
        await callback.answer("Estado actualizado")
        # Refrescar vista
        await callback_edit_item(callback, session)
    else:
        await callback.answer("Producto no encontrado", show_alert=True)


# ========================================
# OTORGAR ITEM
# ========================================

@shop_admin_router.callback_query(F.data == "shop_admin:grant")
async def callback_grant_item_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Inicia el proceso de otorgar un item."""
    container = ShopContainer(session)
    items = await container.shop.get_all_items()

    if not items:
        await callback.answer("No hay productos disponibles", show_alert=True)
        return

    text = (
        "🎁 <b>Otorgar Item a Usuario</b>\n\n"
        "Selecciona el producto a otorgar:"
    )

    buttons = []
    for item in items[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{item.icon} {item.name}",
                callback_data=f"shop_admin:grant_select:{item.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Cancelar", callback_data="admin:shop")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@shop_admin_router.callback_query(F.data.startswith("shop_admin:grant_select:"))
async def callback_grant_item_select(callback: CallbackQuery, state: FSMContext):
    """Selecciona el item a otorgar."""
    item_id = int(callback.data.split(":")[2])
    await state.update_data(grant_item_id=item_id)

    text = (
        "🎁 <b>Otorgar Item</b>\n\n"
        "Envía el <b>ID del usuario</b> que recibirá el item:\n\n"
        "<i>Ejemplo: 123456789</i>"
    )

    buttons = [[InlineKeyboardButton(text="❌ Cancelar", callback_data="admin:shop")]]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

    # Estado simple - esperando user_id
    await state.set_state("waiting_grant_user_id")
    await callback.answer()


@shop_admin_router.message(F.text.regexp(r"^\d+$"))
async def process_grant_user_id(message: Message, state: FSMContext, session: AsyncSession):
    """Procesa el ID del usuario y otorga el item."""
    current_state = await state.get_state()
    if current_state != "waiting_grant_user_id":
        return

    user_id = int(message.text.strip())
    data = await state.get_data()
    item_id = data.get("grant_item_id")

    if not item_id:
        await message.answer("❌ Error: No hay item seleccionado")
        await state.clear()
        return

    container = ShopContainer(session)
    success, msg = await container.inventory.grant_item(
        user_id=user_id,
        item_id=item_id,
        obtained_via="admin_grant"
    )

    await state.clear()

    if success:
        item = await container.shop.get_item(item_id)
        text = (
            f"✅ <b>Item otorgado exitosamente</b>\n\n"
            f"{item.icon} {item.name} → Usuario {user_id}"
        )
    else:
        text = f"❌ <b>Error</b>\n\n{msg}"

    buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="admin:shop")]]

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
