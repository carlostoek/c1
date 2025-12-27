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
from bot.utils.formatters import format_currency
from bot.utils.keyboards import create_inline_keyboard, dynamic_user_menu_keyboard
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
        await message.answer(
            f"👋 Hola <b>{user_name}</b>!\n\n"
            f"Eres administrador. Usa /admin para gestionar los canales.",
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
    try:
        # Validar token
        is_valid, msg_result, token = await container.subscription.validate_token(token_string)

        if not is_valid:
            await message.answer(
                "❌ <b>Token Inválido</b>\n\n"
                "El token que intentas usar no es válido.\n\n"
                "Posibles causas:\n"
                "• Token incorrecto\n"
                "• Token ya usado\n"
                "• Token expirado",
                parse_mode="HTML"
            )
            return

        # Obtener info del plan (si existe)
        plan = token.plan if hasattr(token, 'plan') else None

        if not plan:
            # Token antiguo sin plan asociado (compatibilidad)
            await message.answer(
                "❌ <b>Token Sin Plan Asociado</b>\n\n"
                "Este token no tiene un plan de suscripción válido.",
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
            await message.answer(
                "⚠️ <b>Canal VIP No Configurado</b>\n\n"
                "Tu suscripción fue activada pero el canal VIP no está configurado.\n"
                "Contacta al administrador.",
                parse_mode="HTML"
            )
            return

        try:
            invite_link = await container.subscription.create_invite_link(
                channel_id=vip_channel_id,
                user_id=user.user_id,
                expire_hours=5  # Link válido 5 horas
            )

            # Formatear mensaje de éxito
            # Asegurar timezone
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)

            price_str = format_currency(plan.price, symbol=plan.currency)

            success_text = f"""🎉 <b>¡Suscripción VIP Activada!</b>

<b>Plan:</b> {plan.name}
<b>Precio:</b> {price_str}
<b>Duración:</b> {plan.duration_days} días
<b>Días Restantes:</b> {days_remaining}

{user.role.emoji} Tu rol ha sido actualizado a: <b>{user.role.display_name}</b>

━━━━━━━━━━━━━━━━━━━━
<b>Siguiente Paso:</b>

Haz click en el botón de abajo para unirte al canal VIP exclusivo.

⚠️ El link expira en 5 horas."""

            await message.answer(
                text=success_text,
                reply_markup=create_inline_keyboard([
                    [{"text": "⭐ Unirse al Canal VIP", "url": invite_link.invite_link}]
                ]),
                parse_mode="HTML"
            )

        except Exception as e:
            logger.warning(f"⚠️ No se pudo crear invite link: {e}")
            await message.answer(
                "✅ <b>¡Suscripción VIP Activada!</b>\n\n"
                f"<b>Plan:</b> {plan.name}\n"
                f"<b>Duración:</b> {plan.duration_days} días\n\n"
                "Contacta al administrador para acceder al canal VIP.",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"❌ Error activando token desde deep link: {e}", exc_info=True)

        await message.answer(
            "❌ <b>Error al Activar Token</b>\n\n"
            "Ocurrió un error al procesar tu suscripción.\n"
            "Contacta al administrador.",
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
    Envía mensaje de bienvenida normal usando sistema de menús dinámicos.

    Args:
        message: Mensaje original
        user: Usuario del sistema
        container: Service container
        user_id: ID del usuario
        session: Sesión de BD
    """
    user_name = message.from_user.first_name or "Usuario"

    # Usuario normal: verificar si es VIP activo
    is_vip = await container.subscription.is_vip_active(user_id)

    # Determinar rol para el menú dinámico
    role = "vip" if is_vip else "free"
    subscription_type = "VIP" if is_vip else "FREE"

    # Calcular días restantes (solo VIP)
    days_remaining = 0
    if is_vip:
        subscriber = await container.subscription.get_vip_subscriber(user_id)
        if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
            # Asegurar que expiry_date tiene timezone
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)

    # Obtener configuración de menú dinámico para el rol
    menu_config = await container.menu.get_or_create_menu_config(role)

    # Interpolar variables en el mensaje de bienvenida
    welcome_message = menu_config.welcome_message.format(
        user_name=user_name,
        days_remaining=days_remaining,
        subscription_type=subscription_type
    )

    # Obtener keyboard dinámico
    keyboard = await dynamic_user_menu_keyboard(session, role)

    await message.answer(
        text=welcome_message,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@user_router.callback_query(F.data == "start:profile")
async def callback_show_profile(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el menú de Juego Kinky (perfil de gamificación).

    Activado desde: Botón "🎮 Juego Kinky" en menú /start

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD
    """
    try:
        # Importar aquí para evitar dependencia circular
        from bot.gamification.services.container import GamificationContainer

        container = ServiceContainer(session, callback.bot)
        gamification = GamificationContainer(session, callback.bot)

        # Obtener resumen de perfil
        summary = await gamification.user_gamification.get_profile_summary(
            callback.from_user.id
        )

        # Verificar estado del regalo diario
        daily_gift_status = await gamification.daily_gift.get_daily_gift_status(
            callback.from_user.id
        )

        # Texto del botón de regalo diario con indicador visual
        if daily_gift_status['can_claim'] and daily_gift_status['system_enabled']:
            daily_gift_text = "🎁 Regalo Diario ⭐"
        else:
            daily_gift_text = "🎁 Regalo Diario ✅"

        # Construir keyboard con botones de gamificación
        keyboard_buttons = [
            [{"text": daily_gift_text, "callback_data": "user:daily_gift"}],
            [
                {"text": "📋 Mis Misiones", "callback_data": "user:missions"},
                {"text": "🎁 Recompensas", "callback_data": "user:rewards"}
            ],
            [{"text": "🏆 Leaderboard", "callback_data": "user:leaderboard"}]
        ]

        # Obtener botones dinámicos configurados para "profile"
        profile_buttons = await container.menu.build_keyboard_for_role("profile")
        if profile_buttons:
            keyboard_buttons.extend(profile_buttons)

        # Agregar botón de volver al menú
        keyboard_buttons.append([{"text": "🔙 Volver al Menú", "callback_data": "profile:back"}])

        keyboard = create_inline_keyboard(keyboard_buttons)

        # Editar mensaje existente
        await callback.message.edit_text(
            text=summary,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error mostrando profile: {e}", exc_info=True)
        await callback.answer(
            f"❌ Error al cargar perfil: {str(e)}",
            show_alert=True
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
        container = ServiceContainer(session, callback.bot)
        user = await container.user.get_or_create_user(
            telegram_user=callback.from_user,
            default_role=UserRole.FREE
        )

        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "Usuario"

        # Verificar si es VIP
        is_vip = await container.subscription.is_vip_active(user_id)
        role = "vip" if is_vip else "free"
        subscription_type = "VIP" if is_vip else "FREE"

        # Calcular días restantes
        days_remaining = 0
        if is_vip:
            subscriber = await container.subscription.get_vip_subscriber(user_id)
            if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
                expiry = subscriber.expiry_date
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_remaining = max(0, (expiry - now).days)

        # Obtener mensaje de bienvenida
        menu_config = await container.menu.get_or_create_menu_config(role)
        welcome_message = menu_config.welcome_message.format(
            user_name=user_name,
            days_remaining=days_remaining,
            subscription_type=subscription_type
        )

        # Obtener keyboard dinámico
        keyboard = await dynamic_user_menu_keyboard(session, role)

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
