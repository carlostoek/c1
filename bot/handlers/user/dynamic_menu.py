"""
Dynamic Menu Handler - Procesa callbacks de menús dinámicos.

Maneja las interacciones de usuarios con botones de menú configurados
dinámicamente por los administradores.

IMPORTANTE: Los mensajes se EDITAN (no se envían nuevos) para mantener
la interfaz limpia.
"""
import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.enums import UserRole
from bot.services.container import ServiceContainer
from bot.middlewares import DatabaseMiddleware
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.menu_helpers import build_start_menu

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

    NUEVO: Edita el mensaje actual en lugar de enviar uno nuevo.
    Agrega botón "🔙 Volver" para regresar al menú anterior.

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
        # Mostrar información (editando mensaje)
        emoji = item.button_emoji or "ℹ️"
        text = f"{emoji} <b>{item.button_text}</b>\n\n{item.action_content}"

        # Determinar callback de volver según origen
        back_callback = _get_back_callback(item.target_role)

        keyboard = create_inline_keyboard([
            [{"text": "🔙 Volver", "callback_data": back_callback}]
        ])

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    elif item.action_type == "contact":
        # Mostrar información de contacto (editando mensaje)
        emoji = item.button_emoji or "📞"
        text = f"{emoji} <b>{item.button_text}</b>\n\n{item.action_content}"

        # Determinar callback de volver según origen
        back_callback = _get_back_callback(item.target_role)

        keyboard = create_inline_keyboard([
            [{"text": "🔙 Volver", "callback_data": back_callback}]
        ])

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
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


def _get_back_callback(target_role: str) -> str:
    """
    Determina el callback apropiado para el botón "Volver".

    Args:
        target_role: Rol del item ('vip', 'free', 'profile')

    Returns:
        Callback data para volver al menú correcto
    """
    if target_role == "profile":
        return "start:profile"  # Volver a profile
    else:
        return "dynmenu:back"  # Volver a /start


@dynamic_menu_router.callback_query(F.data == "dynmenu:back")
async def callback_back_to_start_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Regresa al menú principal de /start.

    Detecta automáticamente el rol del usuario (VIP/FREE) y restaura
    el menú correspondiente.

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD
    """
    try:
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "Usuario"

        # Usar helper para construir el menú
        welcome_message, keyboard = await build_start_menu(
            session=session,
            bot=callback.bot,
            user_id=user_id,
            user_name=user_name
        )

        # Editar mensaje para volver a start
        await callback.message.edit_text(
            text=welcome_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error regresando a menú: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al regresar al menú",
            show_alert=True
        )
