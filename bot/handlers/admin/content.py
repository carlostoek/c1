"""
Content Management Handlers - Admin interface for managing content packages.

Handlers for listing, viewing, creating, editing, and deactivating content packages.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.services.container import ServiceContainer
from bot.utils.pagination import Paginator, create_pagination_keyboard, format_page_header, format_items_list

logger = logging.getLogger(__name__)

# Router for content management handlers
content_router = Router(name="admin_content")

# Apply middleware (AdminAuth already on admin_router, this integrates into it)
content_router.callback_query.middleware(DatabaseMiddleware())


# ===== MENU NAVIGATION =====

@content_router.callback_query(F.data == "admin:content")
async def callback_content_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Show content management submenu.

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.debug(f"📦 Usuario {callback.from_user.id} abrió menú de contenido")

    container = ServiceContainer(session, callback.bot)

    # Obtener mensaje del provider
    text, keyboard = container.message.admin.content.content_menu()

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje de menú contenido: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    await callback.answer()


# ===== LIST PACKAGES =====

@content_router.callback_query(F.data == "admin:content:list")
async def callback_content_list(callback: CallbackQuery, session: AsyncSession):
    """
    Show first page of content packages.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.debug(f"📦 Usuario {callback.from_user.id} listando paquetes (página 1)")

    container = ServiceContainer(session, callback.bot)

    # Get all packages (in-memory pagination per RESEARCH.md recommendation)
    all_packages = await container.content.list_packages(is_active=None)

    # Check if empty
    if not all_packages:
        text, keyboard = container.message.admin.content.content_list_empty()
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                logger.error(f"❌ Error editando mensaje lista vacía: {e}")

        await callback.answer()
        return

    # Paginate
    paginator = Paginator(items=all_packages, page_size=10)
    page = paginator.get_first_page()

    # Format display using AdminContentMessages
    text, keyboard = container.message.admin.content.content_list_header()

    # Add package summaries to text
    packages_text = format_items_list(
        page.items,
        lambda pkg, idx: container.message.admin.content.package_summary(pkg),
        separator="\n\n"
    )

    # Combine header with packages
    full_text = f"{text}\n\n{packages_text}"

    # Create pagination keyboard
    keyboard = create_pagination_keyboard(
        page=page,
        callback_pattern="admin:content:page:{page}",
        back_callback="admin:content"
    )

    try:
        await callback.message.edit_text(
            text=full_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje lista: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    await callback.answer()


@content_router.callback_query(F.data.startswith("admin:content:page:"))
async def callback_content_page(callback: CallbackQuery, session: AsyncSession):
    """
    Show specific page of content packages.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    # Extract page number from callback
    try:
        page_num = int(callback.data.split(":")[-1])
    except (ValueError, IndexError):
        logger.warning(f"⚠️ Callback data inválido: {callback.data}")
        await callback.answer("❌ Página inválida", show_alert=True)
        return

    logger.debug(f"📦 Usuario {callback.from_user.id} viendo página {page_num}")

    container = ServiceContainer(session, callback.bot)

    # Get all packages (in-memory pagination per RESEARCH.md recommendation)
    all_packages = await container.content.list_packages(is_active=None)
    paginator = Paginator(items=all_packages, page_size=10)

    # Validate page number
    if page_num < 1 or page_num > paginator.total_pages:
        logger.warning(f"⚠️ Número de página fuera de rango: {page_num}")
        await callback.answer("❌ Página fuera de rango", show_alert=True)
        return

    page = paginator.get_page(page_num)

    # Format display using AdminContentMessages
    text, keyboard = container.message.admin.content.content_list_header()

    # Add package summaries to text
    packages_text = format_items_list(
        page.items,
        lambda pkg, idx: container.message.admin.content.package_summary(pkg),
        separator="\n\n"
    )

    # Combine header with packages
    full_text = f"{text}\n\n{packages_text}"

    # Create pagination keyboard
    keyboard = create_pagination_keyboard(
        page=page,
        callback_pattern="admin:content:page:{page}",
        back_callback="admin:content"
    )

    try:
        await callback.message.edit_text(
            text=full_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje página: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    await callback.answer()


# ===== PACKAGE DETAIL VIEW =====

@content_router.callback_query(F.data.startswith("admin:content:view:"))
async def callback_content_view(callback: CallbackQuery, session: AsyncSession):
    """
    Show package details with action buttons.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    # Extract package_id from callback
    try:
        package_id = int(callback.data.split(":")[-1])
    except (ValueError, IndexError):
        logger.warning(f"⚠️ Callback data inválido: {callback.data}")
        await callback.answer("❌ ID de paquete inválido", show_alert=True)
        return

    logger.debug(f"📦 Usuario {callback.from_user.id} viendo paquete {package_id}")

    container = ServiceContainer(session, callback.bot)

    package = await container.content.get_package(package_id)
    if not package:
        await callback.answer("❌ Paquete no encontrado", show_alert=True)
        return

    # Get package detail with action buttons
    text, keyboard = container.message.admin.content.package_detail(package)

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje detalle: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    await callback.answer()
