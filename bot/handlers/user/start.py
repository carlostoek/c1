"""
User Start Handler - Punto de entrada para usuarios.

Handler del comando /start que detecta si el usuario es admin o usuario normal.
También maneja deep links para activación automática de tokens VIP.

Deep Link Format: t.me/botname?start=TOKEN
"""
import logging
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.enums import UserRole
from bot.middlewares import DatabaseMiddleware
from bot.services.container import ServiceContainer
from bot.services.lucien_voice import LucienVoiceService
from bot.utils.formatters import format_currency
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.menu_helpers import build_start_menu
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
    - Si hay parámetro (deep link) → Activa token automáticamente
    - Si es admin → Redirige a /admin
    - Si es VIP activo → Muestra mensaje de bienvenida con días restantes
    - Si no es admin → Muestra menú de usuario (VIP/Free)

    Deep Link Format:
    - /start → Mensaje de bienvenida normal
    - /start TOKEN → Activa token VIP automáticamente (deep link)

    Args:
        message: Mensaje del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Usuario"

    logger.info(f"👋 Usuario {user_id} ({user_name}) ejecutó /start")

    # Crear/obtener usuario con rol FREE si no existe
    container = ServiceContainer(session, message.bot)
    user = await container.user.get_or_create_user(
        telegram_user=message.from_user,
        default_role=UserRole.FREE
    )
    logger.debug(f"👤 Usuario en sistema: {user.user_id} - Rol: {user.role.value}")

    # Verificar si es admin PRIMERO
    if Config.is_admin(user_id):
        lucien = LucienVoiceService()
        welcome_msg = await lucien.get_welcome_message("admin")
        await message.answer(
            welcome_msg,
            parse_mode="HTML"
        )
        return

    # Verificar si hay parámetro (deep link)
    # Formato: /start TOKEN
    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        # Hay parámetro → Es un deep link con token
        token_string = args[1].strip()

        logger.info(f"🔗 Deep link detectado: Token={token_string} | User={user_id}")

        # Activar token automáticamente
        await _activate_token_from_deeplink(
            message=message,
            session=session,
            container=container,
            user=user,
            token_string=token_string
        )
    else:
        # No hay parámetro → Mensaje de bienvenida normal
        await _send_welcome_message(message, user, container, user_id, session)


async def _activate_token_from_deeplink(
    message: Message,
    session: AsyncSession,
    container: ServiceContainer,
    user,  # User model
    token_string: str
):
    """
    Activa un token VIP desde un deep link.

    NUEVO: Maneja la activación automática cuando el usuario hace click en el deep link.

    Args:
        message: Mensaje original
        session: Sesión de BD
        container: Service container
        user: Usuario del sistema
        token_string: String del token a activar
    """
    lucien = LucienVoiceService()

    try:
        # Validar token
        is_valid, msg_result, token = await container.subscription.validate_token(token_string)

        if not is_valid:
            error_msg = await lucien.format_error("token_invalid")
            await message.answer(
                error_msg,
                parse_mode="HTML"
            )
            return

        # Obtener info del plan (si existe)
        plan = token.plan if hasattr(token, 'plan') else None

        if not plan:
            # Token antiguo sin plan asociado (compatibilidad)
            error_msg = await lucien.format_error("not_configured", {"element": "plan de suscripción"})
            await message.answer(
                error_msg,
                parse_mode="HTML"
            )
            return

        # Marcar token como usado
        token.used = True
        token.used_by = user.user_id
        token.used_at = datetime.utcnow()

        # Activar suscripción VIP (sin commit en service)
        subscriber = await container.subscription.activate_vip_subscription(
            user_id=user.user_id,
            token_id=token.id,
            duration_hours=plan.duration_days * 24
        )

        # Actualizar rol del usuario a VIP en BD
        user.role = UserRole.VIP

        # Commit único de toda la transacción
        await session.commit()
        await session.refresh(subscriber)

        logger.info(
            f"✅ Usuario {user.user_id} activado como VIP vía deep link | "
            f"Plan: {plan.name}"
        )

        # Generar link de invitación al canal VIP
        vip_channel_id = await container.channel.get_vip_channel_id()

        if not vip_channel_id:
            error_msg = await lucien.format_error("vip_not_configured")
            await message.answer(
                error_msg,
                parse_mode="HTML"
            )
            return

        try:
            invite_link = await container.subscription.create_invite_link(
                channel_id=vip_channel_id,
                user_id=user.user_id,
                expire_hours=5  # Link válido 5 horas
            )

            # Formatear mensaje de éxito con más detalles
            # Asegurar timezone
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)

            price_str = format_currency(plan.price, symbol=plan.currency)

            success_text = f"""<b>Suscripción Activada</b>

━━━━━━━━━━━━━━━━━━━━━━━━
<b>Su Plan:</b> {plan.name}
<b>Precio:</b> {price_str}
<b>Duración:</b> {plan.duration_days} días
<b>Válido por:</b> {days_remaining} días

{user.role.emoji} <b>Su rol:</b> <code>{user.role.display_name}</code>

━━━━━━━━━━━━━━━━━━━━━━━━
Diana ha autorizado su acceso al canal VIP.

Pulse el botón para ingresar."""

            await message.answer(
                text=success_text,
                reply_markup=create_inline_keyboard([
                    [{"text": "⭐ Ingresar al Canal VIP", "url": invite_link.invite_link}]
                ]),
                parse_mode="HTML"
            )

        except Exception as e:
            logger.warning(f"⚠️ No se pudo crear invite link: {e}")

            await message.answer(
                "<b>Suscripción VIP Activada</b>\n\n"
                f"<b>Plan:</b> {plan.name}\n"
                f"<b>Duración:</b> {plan.duration_days} días\n\n"
                "Ocurrió un problema al crear el link de invitación.\n\n"
                "Su suscripción está activa. Contacte al administrador para obtener acceso al canal VIP.",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"❌ Error activando token desde deep link: {e}", exc_info=True)

        error_msg = await lucien.format_error("token_invalid")
        await message.answer(
            error_msg,
            parse_mode="HTML"
        )


async def _send_welcome_message(
    message: Message,
    user,  # User model
    container: ServiceContainer,
    user_id: int,
    session: AsyncSession
):
    """
    Envía mensaje de bienvenida normal.

    Args:
        message: Mensaje original
        user: Usuario del sistema
        container: Service container
        user_id: ID del usuario
        session: Sesión de BD
    """
    user_name = message.from_user.first_name or "Usuario"

    # Usar helper para construir el menú
    welcome_message, keyboard = await build_start_menu(
        session=session,
        bot=message.bot,
        user_id=user_id,
        user_name=user_name,
        container=container
    )

    await message.answer(
        welcome_message,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@user_router.callback_query(F.data == "profile:back")
async def callback_back_to_start(callback: CallbackQuery, session: AsyncSession):
    """
    Regresa al menú principal de /start desde el perfil.

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
        lucien = LucienVoiceService()
        error_msg = await lucien.format_error("invalid_input")
        await callback.answer(
            error_msg,
            show_alert=True
        )
