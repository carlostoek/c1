"""
VIP Menu Handler - Opciones para usuarios VIP activos.

Handlers para el menú VIP:
- Acceder al Canal VIP (generar invite link)
- Ver detalles de suscripción actual
- Renovar suscripción
"""
import logging
from datetime import datetime, timezone

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.start import user_router
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard, vip_user_menu_keyboard
from bot.utils.formatters import format_currency, format_datetime

logger = logging.getLogger(__name__)


@user_router.callback_query(F.data == "user:vip_access")
async def callback_vip_access(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Genera y envía invite link al canal VIP.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    logger.info(f"📺 Usuario VIP {user_id} solicitando acceso al canal")

    container = ServiceContainer(session, callback.bot)

    # Verificar que es VIP activo
    if not await container.subscription.is_vip_active(user_id):
        await callback.answer(
            "❌ No tiene acceso VIP activo.",
            show_alert=True
        )
        return

    # Verificar que canal VIP está configurado
    vip_channel_id = await container.channel.get_vip_channel_id()

    if not vip_channel_id:
        await callback.answer(
            "⚠️ Canal VIP no está configurado. Contacta al administrador.",
            show_alert=True
        )
        return

    try:
        # Crear invite link (5 horas de validez)
        invite_link = await container.subscription.create_invite_link(
            channel_id=vip_channel_id,
            user_id=user_id,
            expire_hours=5
        )

        await callback.message.edit_text(
            "📺 <b>Acceso al Canal VIP</b>\n\n"
            "Haga clic en el botón de abajo para unirse al canal VIP.\n\n"
            "⚠️ <b>Importante:</b>\n"
            "• El link expira en 5 horas\n"
            "• Solo puede usarlo 1 vez\n"
            "• No lo comparta con otros",
            reply_markup=create_inline_keyboard([
                [{"text": "⭐ Unirse al Canal VIP", "url": invite_link.invite_link}],
                [{"text": "🔙 Volver al Menú", "callback_data": "user:vip_menu"}]
            ]),
            parse_mode="HTML"
        )

        logger.info(f"✅ Invite link generado para usuario VIP {user_id}")

    except Exception as e:
        logger.error(f"❌ Error generando invite link para user {user_id}: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al generar el link. Intenta nuevamente.",
            show_alert=True
        )
        return

    await callback.answer()


@user_router.callback_query(F.data == "user:vip_status")
async def callback_vip_status(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra detalles de la suscripción VIP actual.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    logger.info(f"⏱️ Usuario VIP {user_id} consultando estado de suscripción")

    container = ServiceContainer(session, callback.bot)

    # Obtener datos del suscriptor
    subscriber = await container.subscription.get_vip_subscriber(user_id)

    if not subscriber:
        await callback.answer(
            "❌ No tiene suscripción VIP activa.",
            show_alert=True
        )
        return

    # Calcular días restantes
    expiry = subscriber.expiry_date
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_remaining = max(0, (expiry - now).days)
    hours_remaining = max(0, int((expiry - now).total_seconds() / 3600))

    # Formatear fechas
    join_date_str = format_datetime(subscriber.join_date, include_time=False)
    expiry_date_str = format_datetime(expiry, include_time=True)

    # Obtener info del plan si existe
    plan_info = ""
    if subscriber.token and hasattr(subscriber.token, 'plan') and subscriber.token.plan:
        plan = subscriber.token.plan
        price_str = format_currency(plan.price, symbol=plan.currency)
        plan_info = (
            f"<b>Plan:</b> {plan.name}\n"
            f"<b>Precio Pagado:</b> {price_str}\n\n"
        )

    # Determinar emoji de estado
    if days_remaining > 7:
        status_emoji = "🟢"
        status_text = "Activa"
    elif days_remaining > 3:
        status_emoji = "🟡"
        status_text = "Próxima a expirar"
    else:
        status_emoji = "🔴"
        status_text = "Expira pronto"

    await callback.message.edit_text(
        f"{status_emoji} <b>Estado de Suscripción VIP</b>\n\n"
        f"{plan_info}"
        f"<b>Estado:</b> {status_text}\n"
        f"<b>Inicio:</b> {join_date_str}\n"
        f"<b>Vencimiento:</b> {expiry_date_str}\n\n"
        f"⏱️ <b>Tiempo Restante:</b>\n"
        f"• <b>{days_remaining}</b> días\n"
        f"• <b>{hours_remaining}</b> horas\n\n"
        f"{'⚠️ <b>Renueva pronto para no perder acceso</b>' if days_remaining <= 3 else 'Disfruta del contenido exclusivo! 🎉'}",
        reply_markup=create_inline_keyboard([
            [{"text": "🎁 Renovar Suscripción", "callback_data": "user:vip_renew"}],
            [{"text": "🔙 Volver al Menú", "callback_data": "user:vip_menu"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


@user_router.callback_query(F.data == "user:vip_renew")
async def callback_vip_renew(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra información sobre cómo renovar la suscripción VIP.

    Opcionalmente puede mostrar planes disponibles para compra.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    logger.info(f"🎁 Usuario VIP {user_id} consultando renovación")

    container = ServiceContainer(session, callback.bot)

    # Obtener planes activos disponibles
    plans = await container.pricing.get_all_plans(active_only=True)

    if not plans:
        # No hay planes configurados
        await callback.message.edit_text(
            "🎁 <b>Renovar Suscripción VIP</b>\n\n"
            "Contacte al administrador para obtener un nuevo token VIP.\n\n"
            "Le proporcionará un deep link para activar su renovación automáticamente.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver al Menú", "callback_data": "user:vip_menu"}]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Mostrar planes disponibles
    plans_text = ""
    for plan in plans:
        price_str = format_currency(plan.price, symbol=plan.currency)
        plans_text += (
            f"\n<b>• {plan.name}</b>\n"
            f"  Precio: {price_str}\n"
            f"  Duración: {plan.duration_days} días\n"
        )

    await callback.message.edit_text(
        f"🎁 <b>Renovar Suscripción VIP</b>\n\n"
        f"<b>Planes Disponibles:</b>{plans_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>¿Cómo renovar?</b>\n\n"
        f"1. Contacte al administrador\n"
        f"2. Seleccione el plan que desea\n"
        f"3. Recibirá un deep link de activación\n"
        f"4. Haga clic y su suscripción se extenderá automáticamente\n\n"
        f"💡 Los días restantes de su suscripción actual se <b>sumarán</b> a la nueva.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "user:vip_menu"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


@user_router.callback_query(F.data == "user:vip_menu")
async def callback_vip_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Vuelve al menú principal VIP.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name or "Usuario"

    container = ServiceContainer(session, callback.bot)

    # Obtener días restantes
    subscriber = await container.subscription.get_vip_subscriber(user_id)

    if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
        expiry = subscriber.expiry_date
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        days_remaining = max(0, (expiry - now).days)
    else:
        days_remaining = 0

    await callback.message.edit_text(
        f"👋 Hola <b>{user_name}</b>!\n\n"
        f"✅ Tienes acceso VIP activo\n"
        f"⏱️ Días restantes: <b>{days_remaining}</b>\n\n"
        f"<b>¿Qué deseas hacer?</b>",
        reply_markup=vip_user_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()
