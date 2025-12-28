"""
Wizard Unificado para creación de objetos cross-module.

Panel central para crear:
- Misiones (redirige a mission_wizard)
- Recompensas (redirige a reward_wizard)
- Items de Tienda (wizard inline)
- Capítulos Narrativos (wizard inline)

Fase 4 de la integración cross-module.
"""

import re
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.states.admin import UnifiedWizardStates
from bot.gamification.services.container import GamificationContainer

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


def slugify(text: str) -> str:
    """Convierte texto a slug URL-friendly."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


# ========================================
# MENÚ PRINCIPAL - WIZARD UNIFICADO
# ========================================

@router.message(Command("crear"))
@router.message(Command("create"))
async def cmd_unified_wizard(message: Message, state: FSMContext):
    """Comando para abrir wizard unificado."""
    await state.clear()
    await _show_unified_menu(message, is_edit=False)


@router.callback_query(F.data == "unified:wizard:menu")
async def show_unified_wizard_menu(callback: CallbackQuery, state: FSMContext):
    """Muestra menú principal del wizard unificado."""
    await state.clear()
    await _show_unified_menu(callback.message, is_edit=True)
    await callback.answer()


async def _show_unified_menu(message: Message, is_edit: bool = False):
    """Helper para mostrar menú unificado."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎯 Crear Misión",
                callback_data="unified:create:mission"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎁 Crear Recompensa",
                callback_data="unified:create:reward"
            )
        ],
        [
            InlineKeyboardButton(
                text="🛒 Crear Item Tienda",
                callback_data="unified:create:shop_item"
            )
        ],
        [
            InlineKeyboardButton(
                text="📖 Crear Capítulo Narrativo",
                callback_data="unified:create:chapter"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Volver al Panel",
                callback_data="gamif:menu"
            )
        ]
    ])

    text = (
        "🎨 <b>Wizard de Creación Unificado</b>\n\n"
        "Crea objetos para cualquier módulo del sistema:\n\n"
        "• <b>Misión:</b> Objetivos con recompensas de besitos\n"
        "• <b>Recompensa:</b> Badges, permisos, items unlock\n"
        "• <b>Item Tienda:</b> Productos comprables con besitos\n"
        "• <b>Capítulo:</b> Contenido narrativo interactivo\n\n"
        "<i>Selecciona qué deseas crear:</i>"
    )

    if is_edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# REDIRECCION A WIZARDS EXISTENTES
# ========================================

@router.callback_query(F.data == "unified:create:mission")
async def redirect_to_mission_wizard(callback: CallbackQuery, state: FSMContext):
    """Redirige al wizard de misiones existente."""
    await state.clear()

    # Importamos y llamamos al handler de mission_wizard
    from bot.gamification.handlers.admin.mission_wizard import start_mission_wizard

    # Simulamos el callback con el data correcto
    callback.data = "gamif:wizard:mission"
    await start_mission_wizard(callback, state)


@router.callback_query(F.data == "unified:create:reward")
async def redirect_to_reward_wizard(callback: CallbackQuery, state: FSMContext):
    """Redirige al wizard de recompensas existente."""
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 Badge", callback_data="gamif:reward:wizard:type:badge"),
            InlineKeyboardButton(text="🔑 Permiso", callback_data="gamif:reward:wizard:type:permission")
        ],
        [
            InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:reward:wizard:type:besitos"),
            InlineKeyboardButton(text="🎁 Item", callback_data="gamif:reward:wizard:type:item")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="unified:wizard:menu")
        ]
    ])

    await callback.message.edit_text(
        "🎁 <b>Wizard: Crear Recompensa</b>\n\n"
        "Selecciona el tipo de recompensa:\n\n"
        "• <b>Badge:</b> Insignia coleccionable\n"
        "• <b>Permiso:</b> Acceso a funciones especiales\n"
        "• <b>Besitos:</b> Moneda del sistema\n"
        "• <b>Item:</b> Objeto genérico",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# WIZARD ITEM DE TIENDA (INLINE)
# ========================================

@router.callback_query(F.data == "unified:create:shop_item")
async def start_shop_item_wizard(callback: CallbackQuery, state: FSMContext, session):
    """Inicia wizard de creación de item de tienda."""
    await state.clear()

    # Obtener categorías de la tienda
    from bot.shop.services.shop import ShopService
    shop_service = ShopService(session)
    categories = await shop_service.get_all_categories()

    if not categories:
        await callback.answer(
            "⚠️ No hay categorías de tienda. Crea una primero.",
            show_alert=True
        )
        return

    keyboard_rows = []
    for cat in categories:
        if cat.is_active:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"{cat.emoji} {cat.name}",
                    callback_data=f"unified:shop:cat:{cat.id}"
                )
            ])

    keyboard_rows.append([
        InlineKeyboardButton(text="❌ Cancelar", callback_data="unified:wizard:menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        "🛒 <b>Wizard: Crear Item de Tienda</b>\n\n"
        "Paso 1/7: Selecciona la categoría del producto:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.shop_select_category)
    await callback.answer()


@router.callback_query(
    UnifiedWizardStates.shop_select_category,
    F.data.startswith("unified:shop:cat:")
)
async def shop_select_category(callback: CallbackQuery, state: FSMContext, session):
    """Procesa selección de categoría."""
    category_id = int(callback.data.split(":")[-1])

    from bot.shop.services.shop import ShopService
    shop_service = ShopService(session)
    category = await shop_service.get_category(category_id)

    if not category:
        await callback.answer("❌ Categoría no encontrada", show_alert=True)
        return

    await state.update_data(
        shop_category_id=category_id,
        shop_category_name=category.name
    )

    await callback.message.edit_text(
        f"✅ Categoría: <b>{category.emoji} {category.name}</b>\n\n"
        f"Paso 2/7: Escribe el nombre del producto:\n\n"
        f"Ejemplo: \"Poción de Energía\"",
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.shop_enter_name)
    await callback.answer()


@router.message(UnifiedWizardStates.shop_enter_name)
async def shop_enter_name(message: Message, state: FSMContext):
    """Recibe nombre del item."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    await state.update_data(shop_item_name=message.text.strip())

    await message.answer(
        f"✅ Nombre: <b>{message.text}</b>\n\n"
        f"Paso 3/7: Escribe una descripción corta:\n\n"
        f"Ejemplo: \"Restaura 50 puntos de energía\"",
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.shop_enter_description)


@router.message(UnifiedWizardStates.shop_enter_description)
async def shop_enter_description(message: Message, state: FSMContext):
    """Recibe descripción del item."""
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres")
        return

    await state.update_data(shop_item_description=message.text.strip())

    await message.answer(
        f"✅ Descripción guardada\n\n"
        f"Paso 4/7: ¿Cuántos besitos costará?\n\n"
        f"Ejemplo: 100",
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.shop_enter_price)


@router.message(UnifiedWizardStates.shop_enter_price)
async def shop_enter_price(message: Message, state: FSMContext):
    """Recibe precio en besitos."""
    try:
        price = int(message.text)
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo (0 para gratis)")
        return

    await state.update_data(shop_item_price=price)

    from bot.shop.database.enums import ItemType

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁 Consumible", callback_data="unified:shop:type:consumable"),
            InlineKeyboardButton(text="🏆 Coleccionable", callback_data="unified:shop:type:collectible")
        ],
        [
            InlineKeyboardButton(text="💎 Cosméticos", callback_data="unified:shop:type:cosmetic"),
            InlineKeyboardButton(text="⚡ Boost", callback_data="unified:shop:type:boost")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="unified:wizard:menu")
        ]
    ])

    await message.answer(
        f"✅ Precio: <b>{price} besitos</b>\n\n"
        f"Paso 5/7: Selecciona el tipo de item:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.shop_select_type)


@router.callback_query(
    UnifiedWizardStates.shop_select_type,
    F.data.startswith("unified:shop:type:")
)
async def shop_select_type(callback: CallbackQuery, state: FSMContext):
    """Procesa selección de tipo."""
    item_type = callback.data.split(":")[-1]
    await state.update_data(shop_item_type=item_type)

    from bot.shop.database.enums import ItemRarity

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚪ Común", callback_data="unified:shop:rarity:common"),
            InlineKeyboardButton(text="🟢 Poco Común", callback_data="unified:shop:rarity:uncommon")
        ],
        [
            InlineKeyboardButton(text="🔵 Raro", callback_data="unified:shop:rarity:rare"),
            InlineKeyboardButton(text="🟣 Épico", callback_data="unified:shop:rarity:epic")
        ],
        [
            InlineKeyboardButton(text="🟡 Legendario", callback_data="unified:shop:rarity:legendary")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="unified:wizard:menu")
        ]
    ])

    type_names = {
        'consumable': 'Consumible 🎁',
        'collectible': 'Coleccionable 🏆',
        'cosmetic': 'Cosmético 💎',
        'boost': 'Boost ⚡'
    }

    await callback.message.edit_text(
        f"✅ Tipo: <b>{type_names.get(item_type, item_type)}</b>\n\n"
        f"Paso 6/7: Selecciona la rareza:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.shop_select_rarity)
    await callback.answer()


@router.callback_query(
    UnifiedWizardStates.shop_select_rarity,
    F.data.startswith("unified:shop:rarity:")
)
async def shop_select_rarity(callback: CallbackQuery, state: FSMContext):
    """Procesa selección de rareza y pide icono."""
    rarity = callback.data.split(":")[-1]
    await state.update_data(shop_item_rarity=rarity)

    rarity_names = {
        'common': 'Común ⚪',
        'uncommon': 'Poco Común 🟢',
        'rare': 'Raro 🔵',
        'epic': 'Épico 🟣',
        'legendary': 'Legendario 🟡'
    }

    await callback.message.edit_text(
        f"✅ Rareza: <b>{rarity_names.get(rarity, rarity)}</b>\n\n"
        f"Paso 7/7: Envía un emoji para el icono del producto:\n\n"
        f"Ejemplo: 🍺 🎁 💎 ⚡",
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.shop_enter_icon)
    await callback.answer()


@router.message(UnifiedWizardStates.shop_enter_icon)
async def shop_enter_icon(message: Message, state: FSMContext):
    """Recibe icono y muestra confirmación."""
    icon = message.text.strip() if message.text else "📦"

    # Limitar a máximo 2 caracteres (un emoji)
    if len(icon) > 4:
        icon = icon[:4]

    await state.update_data(shop_item_icon=icon)

    data = await state.get_data()

    rarity_names = {
        'common': 'Común ⚪',
        'uncommon': 'Poco Común 🟢',
        'rare': 'Raro 🔵',
        'epic': 'Épico 🟣',
        'legendary': 'Legendario 🟡'
    }

    type_names = {
        'consumable': 'Consumible',
        'collectible': 'Coleccionable',
        'cosmetic': 'Cosmético',
        'boost': 'Boost'
    }

    summary = f"""📋 <b>RESUMEN DEL PRODUCTO</b>

<b>Categoría:</b> {data.get('shop_category_name', 'N/A')}
<b>Nombre:</b> {icon} {data.get('shop_item_name', 'N/A')}
<b>Descripción:</b> {data.get('shop_item_description', 'N/A')}
<b>Precio:</b> {data.get('shop_item_price', 0)} besitos
<b>Tipo:</b> {type_names.get(data.get('shop_item_type', ''), 'N/A')}
<b>Rareza:</b> {rarity_names.get(data.get('shop_item_rarity', ''), 'N/A')}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="unified:shop:confirm"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="unified:wizard:menu")
        ]
    ])

    await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(UnifiedWizardStates.shop_confirm)


@router.callback_query(UnifiedWizardStates.shop_confirm, F.data == "unified:shop:confirm")
async def shop_confirm_creation(callback: CallbackQuery, state: FSMContext, session):
    """Crea el item de tienda."""
    data = await state.get_data()

    await callback.message.edit_text("⚙️ Creando producto...", parse_mode="HTML")

    try:
        from bot.shop.services.shop import ShopService
        from bot.shop.database.enums import ItemType, ItemRarity

        shop_service = ShopService(session)

        # Mapear tipos
        type_map = {
            'consumable': ItemType.CONSUMABLE,
            'collectible': ItemType.COLLECTIBLE,
            'cosmetic': ItemType.COSMETIC,
            'boost': ItemType.BOOST
        }

        rarity_map = {
            'common': ItemRarity.COMMON,
            'uncommon': ItemRarity.UNCOMMON,
            'rare': ItemRarity.RARE,
            'epic': ItemRarity.EPIC,
            'legendary': ItemRarity.LEGENDARY
        }

        item_type = type_map.get(data.get('shop_item_type', 'consumable'), ItemType.CONSUMABLE)
        rarity = rarity_map.get(data.get('shop_item_rarity', 'common'), ItemRarity.COMMON)

        success, msg, item = await shop_service.create_item(
            category_id=data['shop_category_id'],
            name=data['shop_item_name'],
            description=data['shop_item_description'],
            item_type=item_type,
            price_besitos=data['shop_item_price'],
            created_by=callback.from_user.id,
            rarity=rarity,
            icon=data.get('shop_item_icon', '📦')
        )

        if success:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Crear Otro", callback_data="unified:create:shop_item")],
                [InlineKeyboardButton(text="🔙 Menú Principal", callback_data="unified:wizard:menu")]
            ])

            await callback.message.edit_text(
                f"✅ <b>Producto Creado Exitosamente</b>\n\n"
                f"<b>{data.get('shop_item_icon', '📦')} {data['shop_item_name']}</b>\n"
                f"ID: {item.id}\n"
                f"Slug: <code>{item.slug}</code>\n\n"
                f"El producto ya está disponible en la tienda.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Error al crear producto:</b>\n\n{msg}",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error creating shop item: {e}")
        await callback.message.edit_text(
            f"❌ <b>Error inesperado:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )

    await state.clear()
    await callback.answer()


# ========================================
# WIZARD CAPÍTULO NARRATIVO (INLINE)
# ========================================

@router.callback_query(F.data == "unified:create:chapter")
async def start_chapter_wizard(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creación de capítulo narrativo."""
    await state.clear()

    await callback.message.edit_text(
        "📖 <b>Wizard: Crear Capítulo Narrativo</b>\n\n"
        "Paso 1/5: Escribe el nombre del capítulo:\n\n"
        "Ejemplo: \"Los Kinkys\"",
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.chapter_enter_name)
    await callback.answer()


@router.message(UnifiedWizardStates.chapter_enter_name)
async def chapter_enter_name(message: Message, state: FSMContext):
    """Recibe nombre del capítulo."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    name = message.text.strip()
    suggested_slug = slugify(name)

    await state.update_data(chapter_name=name, chapter_slug=suggested_slug)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Usar: {suggested_slug}", callback_data="unified:chapter:slug:auto")],
        [InlineKeyboardButton(text="✏️ Escribir otro", callback_data="unified:chapter:slug:custom")]
    ])

    await message.answer(
        f"✅ Nombre: <b>{name}</b>\n\n"
        f"Paso 2/5: Slug sugerido: <code>{suggested_slug}</code>\n\n"
        f"El slug es un identificador único para URLs.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.chapter_enter_slug)


@router.callback_query(
    UnifiedWizardStates.chapter_enter_slug,
    F.data == "unified:chapter:slug:auto"
)
async def chapter_use_auto_slug(callback: CallbackQuery, state: FSMContext):
    """Usa slug automático."""
    await _ask_chapter_description(callback.message, state, is_edit=True)
    await callback.answer()


@router.callback_query(
    UnifiedWizardStates.chapter_enter_slug,
    F.data == "unified:chapter:slug:custom"
)
async def chapter_ask_custom_slug(callback: CallbackQuery, state: FSMContext):
    """Pide slug personalizado."""
    await callback.message.edit_text(
        "✏️ Escribe el slug personalizado:\n\n"
        "Solo letras minúsculas, números y guiones.\n"
        "Ejemplo: <code>los-kinkys</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(UnifiedWizardStates.chapter_enter_slug)
async def chapter_enter_custom_slug(message: Message, state: FSMContext):
    """Recibe slug personalizado."""
    if not message.text:
        return

    slug = slugify(message.text.strip())

    if len(slug) < 2:
        await message.answer("❌ El slug debe tener al menos 2 caracteres")
        return

    await state.update_data(chapter_slug=slug)
    await _ask_chapter_description(message, state, is_edit=False)


async def _ask_chapter_description(message: Message, state: FSMContext, is_edit: bool):
    """Helper para pedir descripción del capítulo."""
    text = (
        "Paso 3/5: Escribe una descripción del capítulo:\n\n"
        "Ejemplo: \"Una aventura en el mundo de los kinkys\""
    )

    if is_edit:
        await message.edit_text(text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")

    await state.set_state(UnifiedWizardStates.chapter_enter_description)


@router.message(UnifiedWizardStates.chapter_enter_description)
async def chapter_enter_description(message: Message, state: FSMContext):
    """Recibe descripción del capítulo."""
    description = message.text.strip() if message.text else ""

    await state.update_data(chapter_description=description)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🆓 FREE", callback_data="unified:chapter:type:FREE"),
            InlineKeyboardButton(text="⭐ VIP", callback_data="unified:chapter:type:VIP")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="unified:wizard:menu")
        ]
    ])

    await message.answer(
        "✅ Descripción guardada\n\n"
        "Paso 4/5: ¿Este capítulo es FREE o VIP?\n\n"
        "• <b>FREE:</b> Disponible para todos los usuarios\n"
        "• <b>VIP:</b> Solo para suscriptores VIP",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.chapter_select_type)


@router.callback_query(
    UnifiedWizardStates.chapter_select_type,
    F.data.startswith("unified:chapter:type:")
)
async def chapter_select_type(callback: CallbackQuery, state: FSMContext):
    """Procesa selección de tipo de capítulo."""
    chapter_type = callback.data.split(":")[-1]
    await state.update_data(chapter_type=chapter_type)

    await callback.message.edit_text(
        f"✅ Tipo: <b>{'🆓 FREE' if chapter_type == 'FREE' else '⭐ VIP'}</b>\n\n"
        f"Paso 5/5: ¿Qué orden tendrá este capítulo?\n\n"
        f"Ejemplo: 1 (primer capítulo)",
        parse_mode="HTML"
    )
    await state.set_state(UnifiedWizardStates.chapter_enter_order)
    await callback.answer()


@router.message(UnifiedWizardStates.chapter_enter_order)
async def chapter_enter_order(message: Message, state: FSMContext):
    """Recibe orden del capítulo y muestra confirmación."""
    try:
        order = int(message.text)
        if order < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    await state.update_data(chapter_order=order)

    data = await state.get_data()

    summary = f"""📋 <b>RESUMEN DEL CAPÍTULO</b>

<b>Nombre:</b> {data.get('chapter_name', 'N/A')}
<b>Slug:</b> <code>{data.get('chapter_slug', 'N/A')}</code>
<b>Descripción:</b> {data.get('chapter_description', 'Sin descripción')}
<b>Tipo:</b> {'🆓 FREE' if data.get('chapter_type') == 'FREE' else '⭐ VIP'}
<b>Orden:</b> {order}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="unified:chapter:confirm"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="unified:wizard:menu")
        ]
    ])

    await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(UnifiedWizardStates.chapter_confirm)


@router.callback_query(UnifiedWizardStates.chapter_confirm, F.data == "unified:chapter:confirm")
async def chapter_confirm_creation(callback: CallbackQuery, state: FSMContext, session):
    """Crea el capítulo narrativo."""
    data = await state.get_data()

    await callback.message.edit_text("⚙️ Creando capítulo...", parse_mode="HTML")

    try:
        from bot.narrative.services.chapter import ChapterService
        from bot.narrative.database import ChapterType

        chapter_service = ChapterService(session)

        chapter_type = ChapterType.VIP if data.get('chapter_type') == 'VIP' else ChapterType.FREE

        chapter = await chapter_service.create_chapter(
            name=data['chapter_name'],
            slug=data['chapter_slug'],
            chapter_type=chapter_type,
            description=data.get('chapter_description'),
            order=data.get('chapter_order', 0)
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Crear Otro", callback_data="unified:create:chapter")],
            [InlineKeyboardButton(text="🔙 Menú Principal", callback_data="unified:wizard:menu")]
        ])

        await callback.message.edit_text(
            f"✅ <b>Capítulo Creado Exitosamente</b>\n\n"
            f"<b>📖 {chapter.name}</b>\n"
            f"ID: {chapter.id}\n"
            f"Slug: <code>{chapter.slug}</code>\n"
            f"Tipo: {'🆓 FREE' if chapter.chapter_type == ChapterType.FREE else '⭐ VIP'}\n\n"
            f"Ahora puedes agregar fragmentos a este capítulo.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        # Commit si es necesario
        await session.commit()

    except ValueError as e:
        await callback.message.edit_text(
            f"❌ <b>Error de validación:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error creating chapter: {e}")
        await callback.message.edit_text(
            f"❌ <b>Error inesperado:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )

    await state.clear()
    await callback.answer()


# ========================================
# CANCELAR WIZARD
# ========================================

@router.callback_query(F.data == "unified:cancel")
async def cancel_unified_wizard(callback: CallbackQuery, state: FSMContext):
    """Cancela el wizard unificado."""
    await state.clear()
    await callback.message.edit_text("❌ Wizard cancelado", parse_mode="HTML")
    await callback.answer()
