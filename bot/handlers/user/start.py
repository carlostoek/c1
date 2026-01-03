"""
User Start Handler - Punto de entrada para usuarios.

Handler del comando /start que implementa flujos diferenciados según el tipo
de usuario usando la voz de Lucien.

Flujos implementados:
- Usuario completamente nuevo (primera vez)
- Usuario que regresa (< 7 días de ausencia)
- Usuario inactivo (7-14 días)
- Usuario muy inactivo (14+ días)
- Usuario VIP activo
- Admin

Deep Link Format: t.me/botname?start=TOKEN
"""
import logging
from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.enums import UserRole
from bot.middlewares import DatabaseMiddleware
from bot.services.container import ServiceContainer
from bot.utils.formatters import format_currency
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.menu_helpers import build_start_menu, build_profile_menu_lucien
from bot.utils.lucien_messages import LucienMessages
from config import Config

logger = logging.getLogger(__name__)

# Router para handlers de usuario
user_router = Router(name="user")

# Aplicar middleware de database (NO AdminAuth, estos son usuarios normales)
user_router.message.middleware(DatabaseMiddleware())
user_router.callback_query.middleware(DatabaseMiddleware())


# =============================================================================
# FUNCIONES AUXILIARES PARA DETECCIÓN DE USUARIO
# =============================================================================

async def _get_user_last_activity(
    container: ServiceContainer,
    user_id: int
) -> datetime | None:
    """
    Obtiene la última actividad del usuario desde UserGamification.

    Args:
        container: ServiceContainer
        user_id: ID del usuario

    Returns:
        Datetime de última actividad o None si no existe
    """
    from bot.gamification.database.models import UserGamification

    user_gamif = await container.session.get(UserGamification, user_id)

    if user_gamif:
        return user_gamif.updated_at
    return None


async def _detect_user_type(
    user,
    container: ServiceContainer
) -> str:
    """
    Detecta el tipo de usuario basado en su actividad y suscripción.

    Args:
        user: Modelo User
        container: ServiceContainer

    Returns:
        str: Tipo de usuario ('new', 'returning', 'inactive', 'long_inactive', 'vip')
    """
    now = datetime.now(timezone.utc)

    # Primero verificar si es VIP activo
    is_vip = await container.subscription.is_vip_active(user.user_id)
    if is_vip:
        return 'vip'

    # Obtener última actividad desde UserGamification
    last_activity = await _get_user_last_activity(container, user.user_id)

    if last_activity is None:
        # No tiene perfil de gamificación = usuario nuevo
        return 'new'

    # Asegurar timezone
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)

    # Calcular días desde última actividad
    days_away = (now - last_activity).days

    if days_away < 7:
        # Regresa después de menos de 7 días
        return 'returning'
    elif days_away < 14:
        # Inactivo: 7-14 días
        return 'inactive'
    else:
        # Muy inactivo: 14+ días
        return 'long_inactive'


# =============================================================================
# HANDLER /start PRINCIPAL
# =============================================================================

@user_router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """
    Handler del comando /start con flujos diferenciados usando voz de Lucien.

    Flujos implementados:
    - Usuario nuevo: Mensaje de bienvenida en 2 partes
    - Usuario regresa (< 7 días): Mensaje de retorno
    - Usuario inactivo (7-14 días): Mensaje de reactivación
    - Usuario muy inactivo (14+ días): Mensaje de bienvenida de vuelta
    - Usuario VIP: Mensaje personalizado con días restantes
    - Admin: Redirección a /admin con mensaje de Lucien

    Deep Link Format:
    - /start → Mensaje de bienvenida según tipo de usuario
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
            LucienMessages.start("ADMIN", user_name=user_name),
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
        # No hay parámetro → Mensaje de bienvenida según tipo de usuario
        await _send_lucien_welcome(
            message=message,
            user=user,
            container=container,
            user_id=user_id,
            session=session
        )

    # FASE 3: Tracking de sesión después de manejar la solicitud
    await _track_session_start(
        session=session,
        user_id=user_id,
        user=user,
        container=container
    )

    # FASE 3: Verificar detección de arquetipo (no bloqueante)
    await _check_archetype_detection(
        session=session,
        user_id=user_id,
        bot=message.bot
    )


# =============================================================================
# FASE 3: TRACKING DE COMPORTAMIENTO
# =============================================================================

async def _track_session_start(
    session: AsyncSession,
    user_id: int,
    user,
    container: ServiceContainer
):
    """
    Registra el inicio de sesión para tracking de comportamiento (FASE 3).

    Detecta si es un retorno después de inactividad y registra la sesión.
    """
    try:
        from bot.gamification.services.behavior_tracking import BehaviorTrackingService

        tracking = BehaviorTrackingService(session)

        # Detectar tipo de usuario
        user_type = await _detect_user_type(user, container)
        last_activity = await _get_user_last_activity(container, user_id)

        # Determinar si es retorno después de inactividad
        is_return = user_type in ['inactive', 'long_inactive']

        # Registrar sesión
        await tracking.track_session(
            user_id=user_id,
            session_type="start",
            is_return=is_return
        )

        # Si es retorno después de inactividad, registrar específicamente
        if is_return and last_activity:
            from datetime import datetime, timezone

            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_away = (now - last_activity).days

            if days_away >= 7:
                await tracking.track_session(
                    user_id=user_id,
                    session_type="return",
                    is_return=True
                )
                logger.debug(f"📊 Tracking: Usuario {user_id} retorno después de {days_away} días")

    except Exception as e:
        # No fallar el flujo principal por errores de tracking
        logger.warning(f"⚠️ Error en tracking de sesión: {e}")


async def _check_archetype_detection(
    session: AsyncSession,
    user_id: int,
    bot
):
    """
    Verifica si se debe detectar/notificar arquetipo y lo hace si corresponde (FASE 3).

    Esta función se ejecuta después del tracking de sesión para activar
    la detección de arquetipos cuando corresponde.

    Args:
        session: Sesión de BD
        user_id: ID del usuario
        bot: Instancia del bot de Telegram
    """
    try:
        from bot.gamification.services.container import GamificationContainer

        gamification = GamificationContainer(session, bot)

        # Verificar y notificar arquetipo si corresponde
        detected = await gamification.notifications.check_and_notify_archetype(user_id)

        if detected:
            logger.info(f"🎭 Arquetipo detectado y notificado para usuario {user_id}")

    except Exception as e:
        # No fallar el flujo principal por errores de detección de arquetipo
        logger.warning(f"⚠️ Error en detección de arquetipo: {e}")


async def _send_lucien_welcome(
    message: Message,
    user,
    container: ServiceContainer,
    user_id: int,
    session: AsyncSession
):
    """
    Envía mensaje de bienvenida de Lucien según el tipo de usuario.

    Args:
        message: Mensaje original
        user: Usuario del sistema
        container: Service container
        user_id: ID del usuario
        session: Sesión de BD
    """
    user_name = message.from_user.first_name or "Usuario"
    user_type = await _detect_user_type(user, container)

    logger.debug(f"🎯 Tipo de usuario detectado: {user_type}")

    # Actualizar última actividad en UserGamification
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session, message.bot)

    # Crear o actualizar perfil de gamificación (esto actualiza updated_at)
    await gamification.user_gamification.get_or_create_user_profile(user_id)

    if user_type == 'new':
        # Usuario nuevo - Mensaje en 2 partes
        await message.answer(
            LucienMessages.start("NEW_USER_1"),
            parse_mode="HTML"
        )

        # Pequeño delay natural entre mensajes
        import asyncio
        await asyncio.sleep(1)

        await message.answer(
            LucienMessages.start("NEW_USER_2"),
            parse_mode="HTML"
        )

        # Mostrar menú principal
        keyboard = await _build_main_keyboard(user_id, session, message.bot, container)
        await message.answer(
            _get_menu_prompt(user_type),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    elif user_type == 'returning':
        # Usuario que regresa (< 7 días)
        last_activity = await _get_user_last_activity(container, user_id)
        if last_activity:
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_away = max(1, (now - last_activity).days)
        else:
            days_away = 1

        await message.answer(
            LucienMessages.start("RETURNING_USER", days_away=days_away),
            parse_mode="HTML"
        )

        keyboard = await _build_main_keyboard(user_id, session, message.bot, container)
        await message.answer(
            _get_menu_prompt(user_type),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    elif user_type == 'inactive':
        # Usuario inactivo (7-14 días)
        await message.answer(
            LucienMessages.start("INACTIVE_USER"),
            parse_mode="HTML"
        )

        keyboard = await _build_main_keyboard(user_id, session, message.bot, container)
        await message.answer(
            _get_menu_prompt(user_type),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    elif user_type == 'long_inactive':
        # Usuario muy inactivo (14+ días)
        await message.answer(
            LucienMessages.start("LONG_INACTIVE_USER"),
            parse_mode="HTML"
        )

        keyboard = await _build_main_keyboard(user_id, session, message.bot, container)
        await message.answer(
            _get_menu_prompt(user_type),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    elif user_type == 'vip':
        # Usuario VIP activo
        subscriber = await container.subscription.get_vip_subscriber(user_id)
        days_remaining = 0

        if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)

        await message.answer(
            LucienMessages.start("VIP_USER", user_name=user_name, days_remaining=days_remaining),
            parse_mode="HTML"
        )

        keyboard = await _build_main_keyboard(user_id, session, message.bot, container, is_vip=True)
        await message.answer(
            _get_menu_prompt('vip'),
            reply_markup=keyboard,
            parse_mode="HTML"
        )


def _get_menu_prompt(user_type: str) -> str:
    """
    Retorna un prompt para mostrar encima del menú según el tipo de usuario.
    """
    prompts = {
        'new': "¿Por dónde deseamos comenzar?",
        'returning': "Continúe donde lo dejó.",
        'inactive': "Póngase al día con lo que ha perdido.",
        'long_inactive': "Mucho ha pasado. Le sugiero revisar.",
        'vip': "El círculo íntimo está a su disposición.",
    }
    return prompts.get(user_type, "Seleccione una opción:")


async def _build_main_keyboard(
    user_id: int,
    session: AsyncSession,
    bot,
    container: ServiceContainer,
    is_vip: bool = False
):
    """
    Construye el menú principal según el rol del usuario.

    Botones para usuario FREE:
    - "📜 Mi Perfil" → callback: start:profile
    - "🎯 Encargos" → callback: user:missions
    - "🏛️ El Gabinete" → callback: shop:main
    - "💋 Mis Besitos" → callback: user:besitos
    - "📖 Mi Historia" → callback: narrative:main
    - "🔑 Acceso VIP" → callback: vip:info

    Botones adicionales para VIP:
    - "⭐ Contenido Premium" → callback: premium:browse
    - "🗺️ Mapa del Deseo" → callback: mapa:info
    """
    from bot.gamification.services.container import GamificationContainer

    # Detectar si es VIP si no se proporcionó
    if not is_vip:
        is_vip = await container.subscription.is_vip_active(user_id)

    buttons = [
        [{"text": "📜 Mi Perfil", "callback_data": "start:profile"}],
        [
            {"text": "🎯 Encargos", "callback_data": "user:missions"},
            {"text": "🏛️ El Gabinete", "callback_data": "shop:main"}
        ],
        [{"text": "💋 Mis Besitos", "callback_data": "user:besitos"}],
        [{"text": "📖 Mi Historia", "callback_data": "narrative:main"}],
    ]

    if is_vip:
        buttons.extend([
            [
                {"text": "⭐ Contenido Premium", "callback_data": "premium:browse"},
                {"text": "🗺️ Mapa del Deseo", "callback_data": "mapa:info"}
            ],
        ])

    buttons.append([{"text": "🔑 Acceso VIP", "callback_data": "vip:info"}])

    return create_inline_keyboard(buttons)


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
    # Los middlewares globales se encargan de:
    # - Typing indicator (TypingIndicatorMiddleware)
    # - Auto-reacción con ❤️ (AutoReactionMiddleware)

    try:
        # Validar token
        is_valid, msg_result, token = await container.subscription.validate_token(token_string)

        if not is_valid:
            await message.answer(
                "❌ <b>Token Inválido</b>\n\n"
                "El token que intenta usar no es válido.\n\n"
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

            # Formatear mensaje de éxito con más detalles
            # Asegurar timezone
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)

            price_str = format_currency(plan.price, symbol=plan.currency)

            success_text = f"""<b>🎉 Suscripción VIP Activada</b>

━━━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Detalles de Su Plan:</b>
<b>Plan:</b> {plan.name}
<b>Precio:</b> {price_str}
<b>Duración:</b> {plan.duration_days} días
<b>Válido hasta:</b> {days_remaining} días

{user.role.emoji} <b>Su rol:</b> <code>{user.role.display_name}</code>

━━━━━━━━━━━━━━━━━━━━━━━━
<b>🔐 Siguiente Paso:</b>

Haga clic en el botón para acceder al canal VIP exclusivo con contenido premium.

<b>⏰ Válido por:</b> 5 horas desde ahora

<b>💡 Importante:</b>
• El acceso es personal
• No comparta el link
• Tendrá acceso a todo el contenido exclusivo
• Si pierde el link, contacte al soporte

Disfrute de su experiencia VIP."""

            await message.answer(
                text=success_text,
                reply_markup=create_inline_keyboard([
                    [{"text": "⭐ Entrar al Canal VIP Exclusivo ⭐", "url": invite_link.invite_link}]
                ]),
                parse_mode="HTML"
            )

        except Exception as e:
            logger.warning(f"⚠️ No se pudo crear invite link: {e}")

            await message.answer(
                "✅ <b>¡Suscripción VIP Activada!</b>\n\n"
                f"<b>Plan:</b> {plan.name}\n"
                f"<b>Duración:</b> {plan.duration_days} días\n\n"
                "⚠️ Ocurrió un problema al crear el link de invitación.\n\n"
                "Su suscripción está activa, pero por favor contacte al administrador para obtener acceso al canal VIP.",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"❌ Error activando token desde deep link: {e}", exc_info=True)

        await message.answer(
            "❌ <b>Error al Activar Token</b>\n\n"
            "Ocurrió un error al procesar su suscripción.\n"
            "Contacte al administrador.",
            parse_mode="HTML"
        )


# =============================================================================
# CALLBACKS DEL MENÚ PRINCIPAL
# =============================================================================

@user_router.callback_query(F.data == "start:profile")
async def callback_show_profile(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el menú de Juego Kinky (perfil de gamificación).

    Activado desde: Botón "📜 Mi Perfil" en menú /start

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD
    """
    try:
        # Usar helper para construir el perfil con voz de Lucien
        summary, keyboard = await build_profile_menu_lucien(
            session=session,
            bot=callback.bot,
            user_id=callback.from_user.id,
            show_back_button=True
        )

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
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "Usuario"

        container = ServiceContainer(session, callback.bot)
        user = await container.user.get_user(user_id)

        # Detectar tipo de usuario y construir menú
        user_type = await _detect_user_type(user, container) if user else 'returning'

        keyboard = await _build_main_keyboard(user_id, session, callback.bot, container)

        # Editar mensaje para volver a start
        await callback.message.edit_text(
            text=_get_menu_prompt(user_type),
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
