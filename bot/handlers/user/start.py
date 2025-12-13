"""
User Start Handler - Punto de entrada para usuarios.

Handler del comando /start que detecta si el usuario es admin o usuario normal.
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.utils.keyboards import create_inline_keyboard
from bot.services.container import ServiceContainer
from config import Config

logger = logging.getLogger(__name__)

# Router para handlers de usuario
user_router = Router(name="user")

# Aplicar middleware de database (NO AdminAuth, estos son usuarios normales)
user_router.message.middleware(DatabaseMiddleware())
user_router.callback_query.middleware(DatabaseMiddleware())


@user_router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """
    Handler del comando /start para usuarios.

    Comportamiento:
    - Si es admin → Redirige a /admin
    - Si es VIP activo → Muestra mensaje de bienvenida con días restantes
    - Si no es admin → Muestra menú de usuario (VIP/Free)

    Args:
        message: Mensaje del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Usuario"

    logger.info(f"👋 Usuario {user_id} ({user_name}) ejecutó /start")

    # Verificar si es admin
    if Config.is_admin(user_id):
        await message.answer(
            f"👋 Hola <b>{user_name}</b>!\n\n"
            f"Eres administrador. Usa /admin para gestionar los canales.",
            parse_mode="HTML"
        )
        return

    # Usuario normal: verificar si es VIP activo
    container = ServiceContainer(session, message.bot)

    is_vip = await container.subscription.is_vip_active(user_id)

    if is_vip:
        # Usuario ya tiene acceso VIP
        subscriber = await container.subscription.get_vip_subscriber(user_id)

        # Calcular días restantes
        if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
            from datetime import datetime, timezone

            # Asegurar que expiry_date tiene timezone
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                # Si es naive, asumimos UTC
                expiry = expiry.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)
        else:
            days_remaining = 0

        await message.answer(
            f"👋 Hola <b>{user_name}</b>!\n\n"
            f"✅ Tienes acceso VIP activo\n"
            f"⏱️ Días restantes: <b>{days_remaining}</b>\n\n"
            f"Disfruta del contenido exclusivo! 🎉",
            parse_mode="HTML"
        )
        return

    # Usuario no es VIP: mostrar opciones
    keyboard = create_inline_keyboard([
        [{"text": "🎟️ Canjear Token VIP", "callback_data": "user:redeem_token"}],
        [{"text": "📺 Solicitar Acceso Free", "callback_data": "user:request_free"}],
    ])

    await message.answer(
        f"👋 Hola <b>{user_name}</b>!\n\n"
        f"Bienvenido al bot de acceso a canales.\n\n"
        f"<b>Opciones disponibles:</b>\n\n"
        f"🎟️ <b>Canjear Token VIP</b>\n"
        f"Si tienes un token de invitación, canjéalo para acceso VIP.\n\n"
        f"📺 <b>Solicitar Acceso Free</b>\n"
        f"Solicita acceso al canal gratuito (con tiempo de espera).\n\n"
        f"👉 Selecciona una opción:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
