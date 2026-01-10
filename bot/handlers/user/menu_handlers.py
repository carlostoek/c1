"""
Menu Handlers - Handlers de menús dinámicos para usuarios.

Maneja:
- Opciones bloqueadas (requieren onboarding)
- Navegación de submenús
- Registro de interés en productos comerciales
"""
import logging
from datetime import datetime

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.start import user_router
from bot.services.lucien_voice import LucienVoiceService
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from config import Config

logger = logging.getLogger(__name__)


@user_router.callback_query(F.data.startswith("blocked:"))
async def callback_blocked_option(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra mensaje de Lucien cuando usuario intenta acceder a opción bloqueada.

    Las opciones bloqueadas requieren que el usuario complete el onboarding
    antes de poder acceder a la narrativa, juegos, o perfil completo.

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    user_id = callback.from_user.id

    logger.info(f"🚫 Usuario {user_id} intentó acceder a opción bloqueada: {callback.data}")

    # Mensaje de Lucien explicando que necesita completar onboarding
    lucien = LucienVoiceService()
    message = await lucien.format_error("onboarding_required")

    # Keyboard con botón para iniciar tutorial
    keyboard = create_inline_keyboard([
        [{"text": "📖 Iniciar Tutorial", "callback_data": "narr:start"}],
        [{"text": "🔙 Volver al Menú", "callback_data": "profile:back"}]
    ])

    await callback.message.edit_text(
        message,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("submenu:"))
async def callback_submenu(callback: CallbackQuery, session: AsyncSession):
    """
    Navega hacia un submenú dinámico.

    Los submenús son items de menú con parent_key != None.
    Ejemplo: submenu:free_sets → Muestra items con parent_key='free_sets'

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    user_id = callback.from_user.id

    # Parsear: submenu:free_sets
    parts = callback.data.split(":", 1)
    if len(parts) < 2:
        logger.warning(f"⚠️ Formato inválido de submenu: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    parent_key = parts[1]

    logger.info(f"📂 Usuario {user_id} navegando a submenú: {parent_key}")

    from bot.services.container import ServiceContainer
    from bot.narrative.services.container import NarrativeContainer

    container = ServiceContainer(session, callback.bot)
    narrative = NarrativeContainer(session, callback.bot)

    # Obtener usuario y verificar onboarding
    user = await container.user.get_user(user_id)
    role = user.role.value if user else "free"
    completed_onboarding = await narrative.onboarding.has_completed_onboarding(user_id)

    # Construir keyboard de submenú
    keyboard_buttons = await container.menu.build_keyboard_for_role(
        role=role,
        user_id=user_id,
        completed_onboarding=completed_onboarding,
        parent_key=parent_key
    )

    # Agregar botón de volver
    keyboard_buttons.append([{"text": "🔙 Volver", "callback_data": "profile:back"}])

    keyboard = create_inline_keyboard(keyboard_buttons)

    # Obtener item de menú para el título
    menu_item = await container.menu.get_menu_item_by_key(parent_key)

    if menu_item:
        title = f"{menu_item.button_emoji} {menu_item.button_text}" if menu_item.button_emoji else menu_item.button_text
        message_text = f"<b>{title}</b>\n\n<i>Seleccione una opción:</i>"
    else:
        message_text = "<b>Menú</b>\n\n<i>Seleccione una opción:</i>"

    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("set_info:"))
async def callback_set_info(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra información detallada de un set antes de expresar interés.

    Pantalla intermedia que presenta el set con:
    - Descripción del set
    - Botón "Me interesa"
    - Botón "Regresar"

    Formato del callback_data: set_info:set_key
    Ejemplo: set_info:encanto_inicial

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    # Parsear: set_info:encanto_inicial
    parts = callback.data.split(":", 1)
    if len(parts) < 2:
        logger.warning(f"⚠️ Formato inválido de set_info: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    set_key = parts[1]

    logger.info(f"ℹ️ Usuario {callback.from_user.id} viendo info de set: {set_key}")

    # Catálogo de información de sets
    sets_info = {
        "encanto_inicial": {
            "title": "🌸 Encanto Inicial",
            "description": (
                "<b>Set Encanto Inicial</b>\n\n"
                "El comienzo de un viaje sensorial. Este set incluye:\n\n"
                "• 10 fotografías exclusivas\n"
                "• Temática: Elegancia y sutileza\n"
                "• Ambiente: Íntimo y delicado\n\n"
                "<i>Un primer acercamiento a la belleza sin filtros.</i>"
            )
        },
        "sensualidad_revelada": {
            "title": "💃 Sensualidad Revelada",
            "description": (
                "<b>Set Sensualidad Revelada</b>\n\n"
                "Donde la sutileza da paso a la sugerencia. Este set incluye:\n\n"
                "• 15 fotografías exclusivas\n"
                "• Temática: Sensualidad y confianza\n"
                "• Ambiente: Cálido y provocador\n\n"
                "<i>La expresión auténtica de la feminidad.</i>"
            )
        },
        "pasion_desbordante": {
            "title": "🔥 Pasión Desbordante",
            "description": (
                "<b>Set Pasión Desbordante</b>\n\n"
                "Intensidad sin reservas. Este set incluye:\n\n"
                "• 20 fotografías exclusivas\n"
                "• Temática: Pasión y deseo\n"
                "• Ambiente: Ardiente e intenso\n\n"
                "<i>Donde las inhibiciones se desvanecen.</i>"
            )
        },
        "intimidad_explosiva": {
            "title": "💥 Intimidad Explosiva",
            "description": (
                "<b>Set Intimidad Explosiva</b>\n\n"
                "El nivel más profundo de conexión visual. Este set incluye:\n\n"
                "• 25 fotografías exclusivas\n"
                "• Temática: Intimidad total\n"
                "• Ambiente: Sin límites\n\n"
                "<i>La experiencia más completa y auténtica.</i>"
            )
        }
    }

    # Obtener información del set
    set_info = sets_info.get(set_key)

    if not set_info:
        logger.warning(f"⚠️ Set no encontrado: {set_key}")
        await callback.answer("Set no encontrado", show_alert=True)
        return

    # Keyboard con "Me interesa" y "Regresar"
    keyboard = create_inline_keyboard([
        [{"text": "💝 Me Interesa", "callback_data": f"interest:set:{set_key}"}],
        [{"text": "🔙 Regresar", "callback_data": "submenu:free_sets"}]
    ])

    await callback.message.edit_text(
        set_info["description"],
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("customized_info:"))
async def callback_customized_info(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra información detallada de contenido personalizado antes de expresar interés.

    Pantalla intermedia que presenta el servicio personalizado con:
    - Descripción del servicio
    - Botón "Me interesa"
    - Botón "Regresar"

    Formato del callback_data: customized_info:service_key
    Ejemplo: customized_info:consulta_general

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    # Parsear: customized_info:consulta_general
    parts = callback.data.split(":", 1)
    if len(parts) < 2:
        logger.warning(f"⚠️ Formato inválido de customized_info: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    service_key = parts[1]

    logger.info(f"✨ Usuario {callback.from_user.id} viendo info de personalizado: {service_key}")

    # Catálogo de información de servicios personalizados
    customized_info = {
        "consulta_general": {
            "title": "✨ Consulta General",
            "description": (
                "<b>Servicio Personalizado General</b>\n\n"
                "Un espacio dedicado para explorar sus deseos más profundos.\n\n"
                "Este servicio incluye:\n\n"
                "• Sesión personalizada 1 a 1\n"
                "• Asesoría completa según sus necesidades\n"
                "• Confidencialidad absoluta\n"
                "• Atención exclusiva y detallada\n\n"
                "<i>Una experiencia diseñada especialmente para usted.</i>"
            )
        }
    }

    # Obtener información del servicio
    info = customized_info.get(service_key)

    if not info:
        logger.warning(f"⚠️ Servicio personalizado no encontrado: {service_key}")
        await callback.answer("Servicio no encontrado", show_alert=True)
        return

    # Keyboard con "Me interesa" y "Regresar"
    keyboard = create_inline_keyboard([
        [{"text": "💝 Me Interesa", "callback_data": f"interest:personalizado:{service_key}"}],
        [{"text": "🔙 Regresar", "callback_data": "submenu:free_content"}]
    ])

    await callback.message.edit_text(
        info["description"],
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("interest:"))
async def callback_interest(callback: CallbackQuery, session: AsyncSession):
    """
    Usuario expresa interés en un producto comercial.

    Registra el interés en BD y notifica a admins para seguimiento.

    Formato del callback_data: interest:product_type:product_key
    Ejemplo: interest:set:encanto_inicial

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD (inyectada por middleware)
    """
    user_id = callback.from_user.id

    # Parsear: interest:set:encanto_inicial
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        logger.warning(f"⚠️ Formato inválido de interest: {callback.data}")
        await callback.answer("Error: formato inválido", show_alert=True)
        return

    product_type = parts[1]
    product_key = parts[2]

    logger.info(
        f"💝 Usuario {user_id} expresó interés en: "
        f"{product_type}:{product_key}"
    )

    container = ServiceContainer(session, callback.bot)

    try:
        # Registrar interés en BD
        interest = await container.interest.register_interest(
            user_id=user_id,
            product_type=product_type,
            product_key=product_key
        )

        # Commit para persistir antes de notificar
        await session.commit()
        await session.refresh(interest)

        # Notificar a admins
        await _notify_admin_interest(
            bot=callback.bot,
            interest=interest,
            user=callback.from_user
        )

        # Responder al usuario con mensaje de Diana
        message_text = (
            "💋 <b>¡Gracias por tu interés!</b>\n\n"
            f"<i>He recibido tu solicitud sobre <b>{product_key}</b>.</i>\n\n"
            "Me pondré en contacto contigo lo antes posible "
            "para brindarte todos los detalles.\n\n"
            "<i>— Diana</i>"
        )

        keyboard = create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "profile:back"}]
        ])

        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Interés registrado")

    except Exception as e:
        logger.error(f"❌ Error registrando interés: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error al registrar interés. Intente nuevamente.",
            show_alert=True
        )


async def _notify_admin_interest(bot, interest, user):
    """
    Notifica a todos los admins sobre un nuevo interés de usuario.

    Envía mensaje con información del usuario y botones de acción rápida:
    - Responder (contacto directo)
    - Marcar como contactado
    - Bloquear usuario
    - Expulsar del bot

    Args:
        bot: Instancia del bot de Telegram
        interest: UserInterest registrado
        user: Usuario de Telegram (from_user)
    """
    # Formatear fecha en formato legible
    created_at_str = interest.created_at.strftime("%d/%m/%Y %H:%M")

    # Construir mensaje de notificación
    text = (
        f"🔔 <b>Nuevo Interés Registrado</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Usuario:</b> {user.first_name}"
    )

    if user.last_name:
        text += f" {user.last_name}"

    if user.username:
        text += f"\n📱 <b>Username:</b> @{user.username}"

    text += (
        f"\n🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 <b>Producto:</b> {interest.product_type}\n"
        f"🔑 <b>Clave:</b> {interest.product_key}\n"
        f"🕐 <b>Fecha:</b> {created_at_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    # Keyboard con acciones rápidas
    keyboard = create_inline_keyboard([
        [
            {"text": "💬 Responder", "callback_data": f"admin:contact:{interest.id}"},
            {"text": "✅ Contactado", "callback_data": f"admin:contacted:{interest.id}"}
        ],
        [
            {"text": "🚫 Bloquear", "callback_data": f"admin:block:{user.id}"},
            {"text": "👋 Expulsar", "callback_data": f"admin:kick:{user.id}"}
        ]
    ])

    # Enviar notificación a todos los admins
    for admin_id in Config.ADMIN_USER_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            logger.info(f"📤 Notificación de interés enviada a admin {admin_id}")
        except Exception as e:
            logger.error(
                f"❌ Error enviando notificación a admin {admin_id}: {e}",
                exc_info=True
            )
