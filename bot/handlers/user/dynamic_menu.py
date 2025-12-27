"""
Dynamic Menu Handler - Procesa callbacks de menús dinámicos.

Maneja las interacciones de usuarios con botones de menú configurados
dinámicamente por los administradores.
"""
import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.container import ServiceContainer
from bot.middlewares import DatabaseMiddleware

logger = logging.getLogger(__name__)

dynamic_menu_router = Router(name="dynamic_menu")

# Aplicar middleware de database
dynamic_menu_router.callback_query.middleware(DatabaseMiddleware())


@dynamic_menu_router.callback_query(F.data.startswith("menu:"))
async def callback_dynamic_menu_item(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Procesa clicks en botones de menú dinámico.

    Callback format: menu:{item_key}

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    item_key = callback.data.replace("menu:", "")

    container = ServiceContainer(session, callback.bot)
    item = await container.menu.get_menu_item(item_key)

    if not item:
        await callback.answer("❌ Opción no disponible", show_alert=True)
        return

    # Verificar que el item esté activo
    if not item.is_active:
        await callback.answer("❌ Esta opción no está disponible actualmente", show_alert=True)
        return

    # Procesar según el tipo de acción
    if item.action_type == "info":
        # Mostrar información
        emoji = item.button_emoji or "ℹ️"
        await callback.message.answer(
            f"{emoji} <b>{item.button_text}</b>\n\n"
            f"{item.action_content}",
            parse_mode="HTML"
        )
        await callback.answer()

    elif item.action_type == "contact":
        # Mostrar información de contacto
        await callback.message.answer(
            f"📞 <b>Contacto</b>\n\n"
            f"{item.action_content}",
            parse_mode="HTML"
        )
        await callback.answer()

    elif item.action_type == "callback":
        # Callback personalizado (futuro: podría invocar otros handlers)
        logger.info(f"🔔 Callback personalizado ejecutado: {item.action_content}")
        await callback.answer("✅ Acción ejecutada", show_alert=False)

    else:
        # action_type == "url" se maneja automáticamente por Telegram
        # (el botón tiene url en lugar de callback_data)
        logger.warning(f"⚠️ Tipo de acción no manejado: {item.action_type}")
        await callback.answer("❌ Error al procesar acción", show_alert=True)
