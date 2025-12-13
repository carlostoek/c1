"""
Admin Main Handler - Menú principal de administración.

Handler del comando /admin y navegación del menú principal.
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import AdminAuthMiddleware, DatabaseMiddleware
from bot.utils.keyboards import admin_main_menu_keyboard, back_to_main_menu_keyboard
from bot.services.container import ServiceContainer

logger = logging.getLogger(__name__)

# Router para handlers de admin
admin_router = Router(name="admin")

# Aplicar middlewares (orden correcto: Database primero, AdminAuth después)
admin_router.message.middleware(DatabaseMiddleware())
admin_router.message.middleware(AdminAuthMiddleware())
admin_router.callback_query.middleware(DatabaseMiddleware())
admin_router.callback_query.middleware(AdminAuthMiddleware())


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession):
    """
    Handler del comando /admin.

    Muestra el menú principal de administración con estado de configuración.

    Args:
        message: Mensaje del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"📋 Admin panel abierto por user {message.from_user.id}")

    # Crear container de services
    container = ServiceContainer(session, message.bot)

    # Verificar estado de configuración
    config_status = await container.config.get_config_status()

    # Construir texto del menú
    if config_status["is_configured"]:
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            "✅ Bot configurado correctamente\n\n"
            "Selecciona una opción:"
        )
    else:
        missing_items = ", ".join(config_status["missing"])
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            f"⚠️ <b>Configuración incompleta</b>\n"
            f"Faltante: {missing_items}\n\n"
            "Selecciona una opción para configurar:"
        )

    await message.answer(
        text=text,
        reply_markup=admin_main_menu_keyboard(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "admin:main")
async def callback_admin_main(callback: CallbackQuery, session: AsyncSession):
    """
    Handler del callback para volver al menú principal.

    Se activa cuando usuario presiona "🔙 Volver al Menú Principal"
    desde cualquier submenú.

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.debug(f"↩️ Usuario {callback.from_user.id} volvió al menú principal")

    # Crear container de services
    container = ServiceContainer(session, callback.bot)

    # Verificar estado de configuración
    config_status = await container.config.get_config_status()

    # Construir texto del menú (mismo que cmd_admin)
    if config_status["is_configured"]:
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            "✅ Bot configurado correctamente\n\n"
            "Selecciona una opción:"
        )
    else:
        missing_items = ", ".join(config_status["missing"])
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            f"⚠️ <b>Configuración incompleta</b>\n"
            f"Faltante: {missing_items}\n\n"
            "Selecciona una opción para configurar:"
        )

    # Editar mensaje existente (no enviar nuevo)
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=admin_main_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        # Si el mensaje es igual, Telegram lanza error (es esperado)
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    # Responder al callback (quitar "loading" del botón)
    await callback.answer()


@admin_router.callback_query(F.data == "admin:config")
async def callback_admin_config(callback: CallbackQuery, session: AsyncSession):
    """
    Handler para mostrar estado de configuración.

    Muestra resumen detallado de la configuración actual del bot.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.debug(f"⚙️ Usuario {callback.from_user.id} abrió configuración")

    # Crear container de services
    container = ServiceContainer(session, callback.bot)

    # Obtener resumen de configuración
    summary = await container.config.get_config_summary()

    # Editar mensaje con resumen
    try:
        await callback.message.edit_text(
            text=summary,
            reply_markup=back_to_main_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje de config: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    await callback.answer()
