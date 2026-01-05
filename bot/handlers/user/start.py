"""
User Start Handler - Punto de entrada para usuarios.

Handler del comando /start que detecta si el usuario es admin o usuario normal.
También maneja deep links para activación automática de tokens VIP.

Deep Link Format: t.me/botname?start=TOKEN
"""
import logging
import asyncio
from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User
from bot.database.enums import UserRole
from bot.middlewares import DatabaseMiddleware
from bot.services.container import ServiceContainer
from bot.utils.formatters import format_currency
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.menu_helpers import build_start_menu
from bot.utils.lucien_messages import Lucien
from config import Config

logger = logging.getLogger(__name__)

# Router para handlers de usuario
user_router = Router(name="user")

# Aplicar middleware de database (NO AdminAuth, estos son usuarios normales)
user_router.message.middleware(DatabaseMiddleware())
user_router.callback_query.middleware(DatabaseMiddleware())


@user_router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, container: ServiceContainer):
    """
    Handler del comando /start para usuarios.

    Implementa la voz de Lucien y flujos diferenciados según el tipo de usuario.
    - Maneja deep links para activación de tokens.
    - Determina si el usuario es nuevo, recurrente, inactivo, VIP o admin.
    - Envía el mensaje de bienvenida apropiado.
    - Actualiza la última actividad del usuario.
    """
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Usuario"
    logger.info(f"Lucien ve a {user_id} ({user_name}) ejecutando /start")

    # Crear/obtener usuario con rol FREE si no existe
    user = await container.user.get_or_create_user(
        telegram_user=message.from_user,
        default_role=UserRole.FREE
    )
    logger.debug(f"👤 Usuario en sistema: {user.user_id} - Rol: {user.role.value}")

    # --- Flujo de Deep Link (tiene prioridad sobre el saludo normal) ---
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        token_string = args[1].strip()
        logger.info(f"🔗 Deep link detectado: Token={token_string} | User={user_id}")
        await _activate_token_from_deeplink(message, session, container, user, token_string)
        return

    # --- Flujo de Saludo Normal (sin deep link) ---
    
    # 1. Determinar el mensaje de bienvenida correcto
    welcome_message = await _get_lucien_welcome_message(user, user_name, container)

    # 2. Construir el menú
    _, keyboard = await build_start_menu(session, message.bot, user_id, user_name, container)
    
    # 3. Enviar mensajes y menú
    await message.answer(welcome_message, parse_mode="HTML", reply_markup=keyboard)

    # Si es usuario nuevo, enviar segundo mensaje con delay
    if user.last_activity is None:
        await asyncio.sleep(2)
        await message.answer(Lucien.START_NEW_USER_2, parse_mode="HTML")
        await message.answer(Lucien.CONFIRM_REGISTRATION, parse_mode="HTML")

    # 4. Actualizar última actividad del usuario
    user.last_activity = datetime.now(timezone.utc)
    await session.commit()
    logger.debug(f"📝 Actualizada last_activity para usuario {user.user_id}")


async def _get_lucien_welcome_message(user: User, user_name: str, container: ServiceContainer) -> str:
    """
    Determina qué mensaje de bienvenida de Lucien enviar basado en el estado del usuario.
    """
    # Flujo 1: Admin
    if Config.is_admin(user.user_id):
        return Lucien.START_ADMIN.format(user_name=user_name)

    # Flujo 2: VIP
    subscription = await container.subscription.get_user_subscription(user.user_id)
    if subscription and subscription.is_active:
        days_remaining = (subscription.expiry_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
        level_name = "Placeholder" # TODO: Obtener el nivel del usuario
        return Lucien.START_VIP_USER.format(
            user_name=user_name,
            days_remaining=days_remaining,
            level_name=level_name
        )
        
    # Flujo 3: Usuario nuevo (primera vez que ejecuta /start sin token)
    # Usamos created_at para distinguir de la primera interacción (last_activity es None)
    if user.last_activity is None or (datetime.now(timezone.utc) - user.created_at).total_seconds() < 60:
        return Lucien.START_NEW_USER_1

    # Flujo 4: Usuarios que regresan (ya han interactuado antes)
    days_away = (datetime.now(timezone.utc) - user.last_activity).days
    
    if days_away < 7:
        return Lucien.START_RETURNING_USER.format(user_name=user_name, days_away=days_away)
    elif 7 <= days_away <= 14:
        return Lucien.START_INACTIVE_USER.format(user_name=user_name)
    else: # > 14 días
        return Lucien.START_LONG_INACTIVE_USER.format(user_name=user_name)


async def _activate_token_from_deeplink(
    message: Message,
    session: AsyncSession,
    container: ServiceContainer,
    user,  # User model
    token_string: str
):
    """
    Activa un token VIP desde un deep link.
    """
    try:
        is_valid, _, token = await container.subscription.validate_token(token_string)

        if not is_valid:
            await message.answer(Lucien.ERROR_NOT_FOUND, parse_mode="HTML")
            return

        plan = token.plan if hasattr(token, 'plan') and token.plan else None
        if not plan:
            await message.answer(Lucien.ERROR_GENERIC, parse_mode="HTML")
            return

        # Marcar token como usado y activar suscripción
        token.used = True
        token.used_by = user.user_id
        token.used_at = datetime.utcnow()
        subscriber = await container.subscription.activate_vip_subscription(
            user_id=user.user_id,
            token_id=token.id,
            duration_hours=plan.duration_days * 24
        )
        user.role = UserRole.VIP
        await session.commit()
        await session.refresh(subscriber)

        logger.info(f"✅ Usuario {user.user_id} activado como VIP vía deep link | Plan: {plan.name}")

        vip_channel_id = await container.channel.get_vip_channel_id()
        if not vip_channel_id:
            await message.answer(Lucien.ERROR_MAINTENANCE, parse_mode="HTML")
            return

        try:
            invite_link = await container.subscription.create_invite_link(
                channel_id=vip_channel_id, user_id=user.user_id, expire_hours=5
            )

            expiry = subscriber.expiry_date.replace(tzinfo=timezone.utc)
            days_remaining = max(0, (expiry - datetime.now(timezone.utc)).days)
            price_str = format_currency(plan.price, symbol=plan.currency)

            success_text = Lucien.CONFIRM_VIP_ACTIVATION.format(
                plan_name=plan.name,
                plan_duration_days=plan.duration_days,
                price_str=price_str,
                days_remaining=days_remaining,
                user_role_display_name=user.role.display_name,
                user_role_emoji=user.role.emoji
            )
            await message.answer(
                text=success_text,
                reply_markup=create_inline_keyboard(
                    [[{"text": "⭐ Entrar al Canal VIP Exclusivo ⭐", "url": invite_link.invite_link}]]
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"⚠️ No se pudo crear invite link: {e}")
            await message.answer(Lucien.ERROR_GENERIC, parse_mode="HTML")

    except Exception as e:
        logger.error(f"❌ Error activando token desde deep link: {e}", exc_info=True)
        await message.answer(Lucien.ERROR_GENERIC, parse_mode="HTML")


@user_router.callback_query(F.data == "profile:back")
async def callback_back_to_start(callback: CallbackQuery, session: AsyncSession, container: ServiceContainer):
    """
    Regresa al menú principal de /start desde el perfil.
    """
    try:
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "Usuario"
        user = await container.user.get_user_by_id(user_id)

        # Usar helper para construir el menú y obtener el mensaje de bienvenida
        welcome_message = await _get_lucien_welcome_message(user, user_name, container)
        _, keyboard = await build_start_menu(session, callback.bot, user_id, user_name, container)

        await callback.message.edit_text(
            text=welcome_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error regresando a menú: {e}", exc_info=True)
        await callback.answer(Lucien.ERROR_GENERIC, show_alert=True)
