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
from bot.services.container import ServiceContainer
from bot.handlers.admin import content as admin_content

logger = logging.getLogger(__name__)

# Router para handlers de admin
admin_router = Router(name="admin")

# Include content management router
admin_router.include_router(admin_content.content_router)

# Aplicar middlewares (Database ya está global, solo AdminAuth para este router)
admin_router.message.middleware(AdminAuthMiddleware())
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

    # Obtener mensaje del provider
    session_history = container.session_history
    text, keyboard = container.message.admin.main.admin_menu_greeting(
        is_configured=config_status["is_configured"],
        missing_items=config_status.get("missing", []),
        user_id=message.from_user.id,
        session_history=session_history
    )

    await message.answer(
        text=text,
        reply_markup=keyboard,
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

    # Obtener mensaje del provider
    session_history = container.session_history
    text, keyboard = container.message.admin.main.admin_menu_greeting(
        is_configured=config_status["is_configured"],
        missing_items=config_status.get("missing", []),
        user_id=callback.from_user.id,
        session_history=session_history
    )

    # Editar mensaje existente (no enviar nuevo)
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
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
    Handler para mostrar menú de configuración.

    Muestra opciones para configurar reacciones y ver estado de config.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.debug(f"⚙️ Usuario {callback.from_user.id} abrió menú de configuración")

    # Crear container de services
    container = ServiceContainer(session, callback.bot)

    # Obtener mensaje del provider
    text, keyboard = container.message.admin.main.config_menu()

    # Editar mensaje con menú de config
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje de config: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    await callback.answer()


@admin_router.callback_query(F.data == "config:status")
async def callback_config_status(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el estado completo de la configuración.

    Incluye reacciones configuradas para VIP y Free.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.debug(f"📊 Usuario {callback.from_user.id} consultando estado de config")

    container = ServiceContainer(session, callback.bot)

    # Obtener datos de configuración
    vip_reactions = await container.config.get_vip_reactions()
    free_reactions = await container.config.get_free_reactions()
    is_vip_configured = await container.channel.is_vip_channel_configured()
    is_free_configured = await container.channel.is_free_channel_configured()
    wait_time = await container.config.get_wait_time()

    # Obtener mensaje del provider
    text, keyboard = container.message.admin.main.config_status(
        vip_reactions=vip_reactions,
        free_reactions=free_reactions,
        is_vip_configured=is_vip_configured,
        is_free_configured=is_free_configured,
        wait_time=wait_time
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje de estado: {e}")
        else:
            logger.debug("ℹ️ Mensaje sin cambios, ignorando")

    await callback.answer()
