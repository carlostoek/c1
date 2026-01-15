"""
Publish Handler - Publicar contenido con botones de reacción.

Handlers:
- callback_start_publish: Inicia flujo de publicación
- FSM handlers para contenido y confirmación
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import PublishWithReactionsStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from bot.database.enums import ChannelType

logger = logging.getLogger(__name__)


@admin_router.callback_query(F.data == "admin:gamification:publish")
async def callback_start_publish(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el flujo para publicar contenido con botones de reacción.

    Flujo:
    1. Mostrar selección de canal destino
    2. Admin selecciona canal (VIP/Free)
    3. Bot entra en waiting_for_content
    4. Admin envía contenido
    5. Bot muestra preview
    6. Bot entra en waiting_for_confirmation
    7. Admin confirma → Publica + crea Publication
    """
    logger.debug("📝 Admin iniciando publicación con reacciones")

    container = ServiceContainer(session, callback.bot)

    # Obtener estado de canales
    vip_channel_id = await container.channel.get_vip_channel_id()
    free_channel_id = await container.channel.get_free_channel_id()

    # Verificar que hay canales configurados
    if not vip_channel_id and not free_channel_id:
        await callback.answer(
            "❌ No hay canales configurados",
            show_alert=True
        )
        return

    # Crear keyboard con canales disponibles
    keyboard_buttons = []
    if vip_channel_id:
        keyboard_buttons.append([{
            "text": f"⭐ Canal VIP",
            "callback_data": "admin:publish:select:vip"
        }])
    if free_channel_id:
        keyboard_buttons.append([{
            "text": f"🆓 Canal Free",
            "callback_data": "admin:publish:select:free"
        }])

    keyboard_buttons.append([{
        "text": "❌ Cancelar",
        "callback_data": "admin:gamification"
    }])

    text = (
        "📝 <b>Publicar con Reacciones</b>\n\n"
        "Selecciona el canal destino:\n\n"
        "La publicación incluirá botones de reacción "
        "con los emojis predeterminados."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:publish:select:"))
async def callback_select_channel(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa la selección del canal y solicita contenido.

    Args:
        callback_data: admin:publish:select:{channel_type}
    """
    callback_data = callback.data
    channel_type_str = callback_data.split(":")[-1]

    # Guardar tipo de canal en FSM
    await state.update_data({"channel_type": channel_type_str})
    await state.set_state(PublishWithReactionsStates.waiting_for_content)

    channel_name = "Canal VIP" if channel_type_str == "vip" else "Canal Free"

    text = (
        f"📝 <b>Publicar en {channel_name}</b>\n\n"
        f"Envía el contenido que deseas publicar.\n\n"
        f"<b>Formatos soportados:</b>\n"
        f"• Texto plano\n"
        f"• Foto\n"
        f"• Video\n\n"
        f"El contenido se publicará con botones de reacción "
        f"usando los emojis predeterminados."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:gamification"}]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(PublishWithReactionsStates.waiting_for_content)
async def process_publish_content(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el contenido enviado por el admin.

    Soporta:
    - Texto plano
    - Foto
    - Video

    Guarda el contenido en FSM data y muestra preview.
    """
    user_id = message.from_user.id
    content_type = None
    content_id = None
    caption = None
    text = None

    logger.debug(f"📝 Admin {user_id} enviando contenido para publicar")

    # Detectar tipo de contenido
    if message.photo:
        content_type = "photo"
        content_id = message.photo[-1].file_id  # Usar la foto de mayor resolución
        caption = message.caption
        if message.text and not caption:
            caption = message.text
    elif message.video:
        content_type = "video"
        content_id = message.video.file_id
        caption = message.caption
        if message.text and not caption:
            caption = message.text
    elif message.text:
        content_type = "text"
        text = message.text
    else:
        await message.answer(
            "❌ <b>Formato No Soportado</b>\n\n"
            "Por favor envía:\n"
            "• Texto\n"
            "• Foto\n"
            "• Video",
            parse_mode="HTML"
        )
        return

    # Guardar contenido en FSM data
    await state.update_data({
        "content_type": content_type,
        "content_id": content_id,
        "caption": caption,
        "text": text,
        "channel_type": (await state.get_data()).get("channel_type")
    })

    # Mostrar preview
    preview_text = _generate_preview_text(content_type, text, caption)

    await state.set_state(PublishWithReactionsStates.waiting_for_confirmation)

    await message.answer(
        f"📝 <b>Preview de Publicación</b>\n\n"
        f"{preview_text}\n\n"
        f"<b>Canal:</b> {(await state.get_data()).get('channel_type').title()}\n\n"
        f"¿Confirmar publicación?",
        reply_markup=create_inline_keyboard([
            [{"text": "✅ Confirmar y Publicar", "callback_data": "admin:publish:confirm"}],
            [{"text": "❌ Cancelar", "callback_data": "admin:publish:cancel"}]
        ]),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "admin:publish:confirm")
async def callback_confirm_publish(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Confirma y publica el contenido con botones de reacción.

    Flujo:
    1. Recuperar contenido de FSM data
    2. Publicar en el canal
    3. Crear registro Publication en BD
    4. Adjuntar keyboard con botones de reacción
    5. Limpiar estado FSM
    """
    user_id = callback.from_user.id

    logger.debug(f"✅ Admin {user_id} confirmando publicación")

    try:
        container = ServiceContainer(session, callback.bot)
        data = await state.get_data()

        content_type = data.get("content_type")
        content_id = data.get("content_id")
        caption = data.get("caption")
        text = data.get("text")
        channel_type_str = data.get("channel_type")

        # Determinar canal destino
        channel_type = ChannelType.VIP if channel_type_str == "vip" else ChannelType.FREE
        if channel_type == ChannelType.VIP:
            channel_id = await container.channel.get_vip_channel_id()
        else:
            channel_id = await container.channel.get_free_channel_id()

        if not channel_id:
            await callback.answer(
                "❌ Canal no configurado",
                show_alert=True
            )
            await state.clear()
            return

        # Publicar contenido
        success, msg, sent_message = await container.channel.send_to_channel(
            channel_id=channel_id,
            text=text,
            photo=content_id if content_type == "photo" else None,
            video=content_id if content_type == "video" else None,
            caption=caption
        )

        if not success:
            await callback.answer(
                f"❌ Error al publicar: {msg}",
                show_alert=True
            )
            await state.clear()
            return

        # Obtener emojis predeterminados
        default_emojis = await container.reactions.get_default_emojis()
        if not default_emojis:
            default_emojis = ["👍", "❤️", "🔥"]

        # Crear registro Publication
        publication = await container.reactions.create_publication(
            channel_id=channel_id,
            message_id=sent_message.message_id,
            channel_type=channel_type,
            emojis=default_emojis
        )

        # Generar keyboard con botones de reacción
        keyboard = container.reactions.generate_reaction_keyboard(
            publication_id=publication.id,
            emojis=default_emojis,
            counts={}  # Vacío al inicio
        )

        # Actualizar mensaje con keyboard
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=channel_id,
                message_id=sent_message.message_id,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.warning(f"⚠️ No se pudo añadir keyboard: {e}")

        await callback.answer(
            f"✅ Publicación creada con {len(default_emojis)} botones de reacción",
            show_alert=True
        )

        # Volver al menú de gamificación
        # TODO: Actualizar mensaje a menú gamificación
        await state.clear()

    except Exception as e:
        logger.error(f"❌ Error publicando: {e}", exc_info=True)
        await callback.answer(
            f"❌ Error: {str(e)}",
            show_alert=True
        )
        await state.clear()


@admin_router.callback_query(F.data == "admin:publish:cancel")
async def callback_cancel_publish(
    callback: CallbackQuery,
    state: FSMContext
):
    """Cancela la publicación y limpia estado."""
    await state.clear()
    await callback.answer("Publicación cancelada")

    # Volver al menú
    # TODO: Actualizar mensaje a menú gamificación


# ===== HELPER =====

def _generate_preview_text(content_type: str, text: str, caption: str) -> str:
    """Genera texto de preview del contenido."""
    if content_type == "text":
        return f"📄 <b>Texto:</b>\n{text or '(vacío)'}"
    elif content_type == "photo":
        return (
            f"🖼️ <b>Foto</b>\n"
            f"{caption or text or '(sin caption)'}"
        )
    elif content_type == "video":
        return (
            f"🎥 <b>Video</b>\n"
            f"{caption or text or '(sin caption)'}"
        )
    return "(Contenido)"
