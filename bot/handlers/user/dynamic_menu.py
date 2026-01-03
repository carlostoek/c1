"""
Dynamic Menu Handler - Procesa callbacks de menús dinámicos.

Maneja las interacciones de usuarios con botones de menú configurados
dinámicamente por los administradores, usando la voz de Lucien.

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
from bot.utils.lucien_messages import LucienMessages
from bot.handlers.user.start import _detect_user_type, _get_menu_prompt

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
    Procesa clicks en botones de menú dinámico con voz de Lucien.

    Callback format: menu:{item_key}

    NUEVO: Edita el mensaje actual en lugar de enviar uno nuevo.
    Agrega botón "🔙 Volver" para regresar al menú anterior.
    Usa mensajes de Lucien para respuestas y errores.

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    item_key = callback.data.replace("menu:", "")

    container = ServiceContainer(session, callback.bot)
    item = await container.menu.get_menu_item(item_key)

    if not item:
        # Item no encontrado - usar mensaje de Lucien (versión corta)
        await callback.answer(
            LucienMessages.errors("NOT_FOUND_SHORT"),
            show_alert=True
        )
        return

    # Verificar que el item esté activo
    if not item.is_active:
        # Item inactivo - usar mensaje de Lucien (versión corta)
        await callback.answer(
            LucienMessages.errors("INACTIVE_SHORT"),
            show_alert=True
        )
        return

    # Procesar según el tipo de acción
    if item.action_type == "info":
        # Mostrar información con formato de Lucien
        emoji = item.button_emoji or "ℹ️"
        text = (
            f"{LucienMessages.menu('ITEM_INFO_HEADER')}\n\n"
            f"{emoji} <b>{item.button_text}</b>\n\n{item.action_content}"
        )

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
        # Mostrar información de contacto con formato de Lucien
        emoji = item.button_emoji or "📞"
        text = (
            f"{LucienMessages.menu('ITEM_CONTACT_HEADER')}\n\n"
            f"{emoji} <b>{item.button_text}</b>\n\n{item.action_content}"
        )

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
        await callback.answer("Acción ejecutada", show_alert=False)

    else:
        # action_type == "url" se maneja automáticamente por Telegram
        # (el botón tiene url en lugar de callback_data)
        logger.warning(f"⚠️ Tipo de acción no manejado: {item.action_type}")
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )


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
    Regresa al menú principal de /start con mensaje de Lucien.

    Detecta automáticamente el rol del usuario (VIP/FREE) y restaura
    el menú correspondiente con un mensaje contextual de Lucien.

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD
    """
    try:
        from bot.gamification.services.container import GamificationContainer

        user_id = callback.from_user.id

        # Obtener usuario para detectar tipo
        container = ServiceContainer(session, callback.bot)
        user = await container.user.get_user(user_id)

        if not user:
            await callback.answer(
                LucienMessages.errors("NOT_FOUND_SHORT"),
                show_alert=True
            )
            return

        # Detectar tipo de usuario
        user_type = await _detect_user_type(user, container)

        # Construir keyboard según rol
        from bot.handlers.user.start import _build_main_keyboard
        keyboard = await _build_main_keyboard(user_id, session, callback.bot, container)

        # Mensaje de Lucien al regresar + prompt contextual
        prompt = LucienMessages.menu("BACK_TO_START") + "\n\n" + _get_menu_prompt(user_type)

        # Editar mensaje para volver a start
        await callback.message.edit_text(
            text=prompt,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error regresando a menú: {e}", exc_info=True)
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )
