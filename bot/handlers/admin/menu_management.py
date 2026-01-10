"""
Admin Menu Management - Panel de gestión de menús dinámicos.

Permite a los admins:
- Ver todos los menús configurados
- Crear nuevos items de menú
- Editar items existentes
- Activar/desactivar items
- Organizar jerarquía (parent_key)
"""
import logging

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


class MenuEditStates(StatesGroup):
    """Estados para edición de menús."""
    waiting_for_item_key = State()
    waiting_for_button_text = State()
    waiting_for_action_content = State()


@admin_router.callback_query(F.data == "admin:menus")
async def callback_admin_menus(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra panel de gestión de menús.

    Opciones:
    - Ver menús por rol (FREE/VIP)
    - Crear nuevo item
    - Editar items existentes

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD
    """
    logger.info(f"📋 Admin {callback.from_user.id} accediendo a gestión de menús")

    text = (
        "📋 <b>Gestión de Menús Dinámicos</b>\n\n"
        "Administra los menús que ven los usuarios según su rol.\n\n"
        "Seleccione una opción:"
    )

    keyboard = create_inline_keyboard([
        [{"text": "👥 Ver Menú FREE", "callback_data": "admin:menu_list:free"}],
        [{"text": "⭐ Ver Menú VIP", "callback_data": "admin:menu_list:vip"}],
        [{"text": "➕ Crear Nuevo Item", "callback_data": "admin:menu_create"}],
        [{"text": "🔙 Volver", "callback_data": "admin:main"}]
    ])

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:menu_list:"))
async def callback_admin_menu_list(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra lista de items de menú por rol.

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD
    """
    # Parsear: admin:menu_list:free
    parts = callback.data.split(":")
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    role = parts[2]

    logger.info(f"📋 Admin {callback.from_user.id} viendo menú de rol: {role}")

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener items de menú para el rol
        items = await container.menu.get_menu_for_role(
            role=role,
            user_completed_onboarding=True,  # Mostrar todos
            parent_key=None  # Solo menú principal
        )

        if not items:
            text = f"📋 <b>Menú {role.upper()}</b>\n\n<i>No hay items configurados.</i>"
        else:
            text = f"📋 <b>Menú {role.upper()}</b>\n\n"

            for item in items:
                emoji = item.button_emoji or ""
                active_icon = "✅" if item.is_active else "❌"
                parent_info = f" → {item.parent_key}" if item.parent_key else ""

                text += (
                    f"\n{active_icon} {emoji} <b>{item.button_text}</b>\n"
                    f"   🔑 Key: <code>{item.item_key}</code>\n"
                    f"   🎯 Action: {item.action_type}{parent_info}\n"
                )

        keyboard = create_inline_keyboard([
            [{"text": "📝 Ver Detalles", "callback_data": f"admin:menu_details:{role}"}],
            [{"text": "🔙 Volver", "callback_data": "admin:menus"}]
        ])

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error listando menú: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error al cargar menú",
            show_alert=True
        )


@admin_router.callback_query(F.data.startswith("admin:menu_details:"))
async def callback_admin_menu_details(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra detalles completos de todos los items de un rol.

    Incluye items principales y submenús.

    Args:
        callback: CallbackQuery del admin
        session: Sesión de BD
    """
    # Parsear: admin:menu_details:free
    parts = callback.data.split(":")
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    role = parts[2]

    logger.info(f"📋 Admin {callback.from_user.id} viendo detalles de rol: {role}")

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener TODOS los items del rol (incluyendo submenús)
        from sqlalchemy import select
        from bot.database.models_menu import MenuItem

        stmt = (
            select(MenuItem)
            .where(MenuItem.target_role == role)
            .order_by(MenuItem.display_order, MenuItem.row_number)
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        if not items:
            text = f"📋 <b>Detalles Menú {role.upper()}</b>\n\n<i>No hay items configurados.</i>"
        else:
            text = f"📋 <b>Detalles Menú {role.upper()}</b>\n\n"
            text += f"Total de items: {len(items)}\n\n"

            # Agrupar por parent_key
            main_items = [i for i in items if not i.parent_key]
            submenu_items = [i for i in items if i.parent_key]

            text += "<b>📌 Items Principales:</b>\n"
            for item in main_items:
                emoji = item.button_emoji or ""
                active = "✅" if item.is_active else "❌"
                text += f"{active} {emoji} {item.button_text} (<code>{item.item_key}</code>)\n"

            if submenu_items:
                text += "\n<b>📁 Items de Submenús:</b>\n"
                for item in submenu_items:
                    emoji = item.button_emoji or ""
                    active = "✅" if item.is_active else "❌"
                    text += f"{active} {emoji} {item.button_text} → {item.parent_key}\n"

        keyboard = create_inline_keyboard([
            [{"text": "🔙 Volver", "callback_data": "admin:menus"}]
        ])

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error mostrando detalles: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error al cargar detalles",
            show_alert=True
        )


@admin_router.callback_query(F.data == "admin:menu_create")
async def callback_admin_menu_create(callback: CallbackQuery):
    """
    Muestra instrucciones para crear un nuevo item de menú.

    Por ahora, indica al admin que use el script de seed
    o cree items manualmente en la BD.

    Args:
        callback: CallbackQuery del admin
    """
    text = (
        "➕ <b>Crear Nuevo Item de Menú</b>\n\n"
        "Para crear nuevos items de menú, puede:\n\n"
        "<b>Opción 1: Script de Seed</b>\n"
        "Edite <code>scripts/seed_menus.py</code> y agregue sus items.\n"
        "Luego ejecute:\n"
        "<code>python scripts/seed_menus.py</code>\n\n"
        "<b>Opción 2: Base de Datos</b>\n"
        "Inserte directamente en la tabla <code>menu_items</code>.\n\n"
        "<b>Campos requeridos:</b>\n"
        "• <code>item_key</code>: Identificador único\n"
        "• <code>button_text</code>: Texto del botón\n"
        "• <code>action_type</code>: callback, submenu, url, etc.\n"
        "• <code>action_content</code>: Callback data o URL\n"
        "• <code>target_role</code>: free, vip, all, admin\n"
        "• <code>display_order</code>: Orden de aparición\n"
        "• <code>row_number</code>: Fila en el keyboard\n\n"
        "<i>Próximamente: Editor visual de menús</i>"
    )

    keyboard = create_inline_keyboard([
        [{"text": "📖 Ver Documentación", "url": "https://github.com/tu-repo"}],
        [{"text": "🔙 Volver", "callback_data": "admin:menus"}]
    ])

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
