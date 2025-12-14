"""
VIP Handlers - Gestión del canal VIP.

Handlers para:
- Submenú VIP
- Configuración del canal VIP
- Generación de tokens de invitación con deep links
"""
import logging
from datetime import timedelta

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.services.container import ServiceContainer
from bot.states.admin import ChannelSetupStates
from bot.utils.formatters import format_currency, format_datetime
from bot.utils.keyboards import create_inline_keyboard
from config import Config

logger = logging.getLogger(__name__)


def vip_menu_keyboard(is_configured: bool) -> "InlineKeyboardMarkup":
    """
    Keyboard del submenú VIP.

    Args:
        is_configured: Si el canal VIP está configurado

    Returns:
        InlineKeyboardMarkup con opciones VIP
    """
    buttons = []

    if is_configured:
        buttons.extend([
            [{"text": "🎟️ Generar Token de Invitación", "callback_data": "vip:generate_token"}],
            [{"text": "📤 Enviar Publicación", "callback_data": "vip:broadcast"}],
            [{"text": "👥 Ver Suscriptores VIP", "callback_data": "vip:list_subscribers"}],
            [{"text": "🔧 Reconfigurar Canal", "callback_data": "vip:setup"}],
        ])
    else:
        buttons.append([{"text": "⚙️ Configurar Canal VIP", "callback_data": "vip:setup"}])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:main"}])

    return create_inline_keyboard(buttons)


@admin_router.callback_query(F.data == "admin:vip")
async def callback_vip_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el submenú de gestión VIP.

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.debug(f"📺 Usuario {callback.from_user.id} abrió menú VIP")

    container = ServiceContainer(session, callback.bot)

    # Verificar si canal VIP está configurado
    is_configured = await container.channel.is_vip_channel_configured()

    if is_configured:
        vip_channel_id = await container.channel.get_vip_channel_id()

        # Obtener info del canal
        channel_info = await container.channel.get_channel_info(vip_channel_id)
        channel_name = channel_info.title if channel_info else "Canal VIP"

        text = (
            f"📺 <b>Gestión Canal VIP</b>\n\n"
            f"✅ Canal configurado: <b>{channel_name}</b>\n"
            f"ID: <code>{vip_channel_id}</code>\n\n"
            f"Selecciona una opción:"
        )
    else:
        text = (
            "📺 <b>Gestión Canal VIP</b>\n\n"
            "⚠️ Canal VIP no configurado\n\n"
            "Configura el canal para comenzar a generar tokens de invitación."
        )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=vip_menu_keyboard(is_configured),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje VIP: {e}")

    await callback.answer()


@admin_router.callback_query(F.data == "vip:setup")
async def callback_vip_setup(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el proceso de configuración del canal VIP.

    Entra en estado FSM esperando que el admin reenvíe un mensaje del canal.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} iniciando setup VIP")

    # Entrar en estado FSM
    await state.set_state(ChannelSetupStates.waiting_for_vip_channel)

    text = (
        "⚙️ <b>Configurar Canal VIP</b>\n\n"
        "Para configurar el canal VIP, necesito que:\n\n"
        "1️⃣ Vayas al canal VIP\n"
        "2️⃣ Reenvíes cualquier mensaje del canal a este chat\n"
        "3️⃣ Yo extraeré el ID automáticamente\n\n"
        "⚠️ <b>Importante:</b>\n"
        "- El bot debe ser administrador del canal\n"
        "- El bot debe tener permiso para invitar usuarios\n\n"
        "👉 Reenvía un mensaje del canal ahora..."
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "❌ Cancelar", "callback_data": "admin:vip"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje setup VIP: {e}")

    await callback.answer()


@admin_router.message(ChannelSetupStates.waiting_for_vip_channel)
async def process_vip_channel_forward(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el mensaje reenviado para configurar el canal VIP.

    Extrae el ID del canal del forward y lo configura.

    Args:
        message: Mensaje reenviado del canal
        session: Sesión de BD
        state: FSM context
    """
    # Verificar que es un forward de un canal
    if not message.forward_from_chat:
        await message.answer(
            "❌ Debes <b>reenviar</b> un mensaje del canal VIP.\n\n"
            "No me envíes el ID manualmente, reenvía un mensaje.",
            parse_mode="HTML"
        )
        return

    forward_chat = message.forward_from_chat

    # Verificar que es un canal (no grupo ni usuario)
    if forward_chat.type not in ["channel", "supergroup"]:
        await message.answer(
            "❌ El mensaje debe ser de un <b>canal</b> o <b>supergrupo</b>.\n\n"
            "Reenvía un mensaje del canal VIP.",
            parse_mode="HTML"
        )
        return

    channel_id = str(forward_chat.id)
    channel_title = forward_chat.title

    logger.info(f"📺 Configurando canal VIP: {channel_id} ({channel_title})")

    container = ServiceContainer(session, message.bot)

    # Intentar configurar el canal
    success, msg = await container.channel.setup_vip_channel(channel_id)

    if success:
        # Configuración exitosa
        await message.answer(
            f"✅ <b>Canal VIP Configurado</b>\n\n"
            f"Canal: <b>{channel_title}</b>\n"
            f"ID: <code>{channel_id}</code>\n\n"
            f"Ya puedes generar tokens de invitación.",
            parse_mode="HTML",
            reply_markup=vip_menu_keyboard(True)
        )

        # Limpiar estado FSM
        await state.clear()
    else:
        # Error en configuración
        await message.answer(
            f"{msg}\n\n"
            f"Verifica que:\n"
            f"• El bot es administrador del canal\n"
            f"• El bot tiene permiso para invitar usuarios\n\n"
            f"Intenta nuevamente reenviando un mensaje del canal.",
            parse_mode="HTML"
        )
        # Mantener estado FSM para reintentar


@admin_router.callback_query(F.data == "vip:generate_token")
async def callback_generate_token_select_plan(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra menú de selección de tarifa para generar token.

    MODIFICADO: Ahora muestra tarifas configuradas en lugar de pedir duración.
    El admin selecciona un plan y el token se genera vinculado a ese plan.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"🎟️ Usuario {callback.from_user.id} generando token VIP")

    container = ServiceContainer(session, callback.bot)

    # Verificar que canal VIP está configurado
    if not await container.channel.is_vip_channel_configured():
        await callback.answer(
            "❌ Debes configurar el canal VIP primero",
            show_alert=True
        )
        return

    try:
        # Obtener planes activos
        plans = await container.pricing.get_all_plans(active_only=True)

        if not plans:
            await callback.message.edit_text(
                "❌ <b>No Hay Tarifas Configuradas</b>\n\n"
                "Debes configurar al menos una tarifa antes de generar tokens.\n\n"
                "Ve a: Configuración → Tarifas → Crear Nueva Tarifa",
                reply_markup=create_inline_keyboard([
                    [{"text": "💰 Configurar Tarifas", "callback_data": "admin:pricing"}],
                    [{"text": "🔙 Volver", "callback_data": "admin:vip"}]
                ]),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        # Construir texto con info de planes
        text = (
            "🎟️ <b>Generar Token de Invitación VIP</b>\n\n"
            "Selecciona la tarifa para el token:\n\n"
        )

        # Agregar info de cada plan
        for plan in plans:
            price_str = format_currency(plan.price, symbol=plan.currency)
            text += f"• <b>{plan.name}</b>: {plan.duration_days} días • {price_str}\n"

        # Construir keyboard con botones de planes
        buttons = []
        for plan in plans:
            price_str = format_currency(plan.price, symbol=plan.currency)

            buttons.append([{
                "text": f"{plan.name} - {price_str}",
                "callback_data": f"vip:generate:plan:{plan.id}"
            }])

        buttons.append([{"text": "🔙 Volver", "callback_data": "admin:vip"}])

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(buttons),
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error mostrando planes: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar tarifas. Intenta nuevamente.",
            show_alert=True
        )


@admin_router.callback_query(F.data.startswith("vip:generate:plan:"))
async def callback_generate_token_with_plan(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Genera token VIP vinculado a una tarifa específica con deep link.

    NUEVO: Genera token con deep link profesional (t.me/bot?start=TOKEN).

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    # Extraer plan_id del callback
    try:
        plan_id = int(callback.data.split(":")[3])
    except (IndexError, ValueError) as e:
        logger.error(f"❌ Error parseando plan_id: {callback.data} - {e}")
        await callback.answer("❌ Error al generar token", show_alert=True)
        return

    container = ServiceContainer(session, callback.bot)

    # Obtener plan
    plan = await container.pricing.get_plan_by_id(plan_id)

    if not plan or not plan.active:
        await callback.answer("❌ Tarifa no disponible", show_alert=True)
        return

    logger.info(
        f"🎟️ Admin {callback.from_user.id} generando token con plan: "
        f"{plan.name} (ID: {plan_id})"
    )

    await callback.answer("🎟️ Generando token...", show_alert=False)

    try:
        # Generar token vinculado al plan
        # La duración se toma del plan automáticamente
        token = await container.subscription.generate_vip_token(
            generated_by=callback.from_user.id,
            duration_hours=plan.duration_days * 24,  # Convertir días a horas
            plan_id=plan.id  # NUEVO: Vincular con plan
        )

        # Commit la transacción
        await session.commit()
        await session.refresh(token)

        # GENERAR DEEP LINK
        bot_username = (await callback.bot.me()).username
        deep_link = f"https://t.me/{bot_username}?start={token.token}"

        # Formatear mensaje con deep link
        price_str = format_currency(plan.price, symbol=plan.currency)
        expiry_str = format_datetime(token.created_at + timedelta(hours=24), include_time=False)

        text = f"""🎟️ <b>Token VIP Generado</b>

<b>Plan:</b> {plan.name}
<b>Duración:</b> {plan.duration_days} días
<b>Precio:</b> {price_str}

<b>Token:</b> <code>{token.token}</code>

<b>🔗 Link de Activación:</b>
<code>{deep_link}</code>

<b>Válido hasta:</b> {expiry_str}

━━━━━━━━━━━━━━━━━━━━
<b>Instrucciones:</b>

1. Copia el link de arriba
2. Envíalo al usuario
3. Al hacer click, se activará automáticamente su suscripción VIP

⚠️ El link expira en 24 horas."""

        await callback.message.answer(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "🔗 Copiar Link", "url": deep_link}],
                [{"text": "🎟️ Generar Otro Token", "callback_data": "vip:generate_token"}],
                [{"text": "🔙 Volver", "callback_data": "admin:vip"}]
            ]),
            parse_mode="HTML"
        )

        logger.info(
            f"✅ Token generado: {token.token} | Plan: {plan.name} | "
            f"Deep link: {deep_link}"
        )

    except Exception as e:
        logger.error(f"❌ Error generando token: {e}", exc_info=True)

        await callback.message.edit_text(
            "❌ <b>Error al Generar Token</b>\n\n"
            "Ocurrió un error inesperado. Intenta nuevamente.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔄 Reintentar", "callback_data": "vip:generate_token"}],
                [{"text": "🔙 Volver", "callback_data": "admin:vip"}]
            ]),
            parse_mode="HTML"
        )
