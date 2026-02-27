"""
Broadcast Handlers - Envío de publicaciones a canales.

Handlers para:
- Iniciar flujo de broadcasting
- Recibir contenido multimedia
- Mostrar preview del mensaje
- Confirmar y enviar a canal(es)
- Cancelar broadcasting
"""
import logging
from typing import Optional

from aiogram import F
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import BroadcastStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


# ===== INICIO DE BROADCASTING =====

@admin_router.callback_query(F.data == "vip:broadcast")
async def callback_broadcast_to_vip(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Inicia broadcasting al canal VIP.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"📤 Usuario {callback.from_user.id} iniciando broadcast a VIP")

    # Guardar canal destino en FSM data
    await state.set_data({"target_channel": "vip"})

    # Entrar en estado FSM
    await state.set_state(BroadcastStates.waiting_for_content)

    text = (
        "📤 <b>Enviar Publicación a Canal VIP</b>\n\n"
        "Envía el contenido que quieres publicar:\n\n"
        "• <b>Texto:</b> Envía un mensaje de texto\n"
        "• <b>Foto:</b> Envía una foto (con caption opcional)\n"
        "• <b>Video:</b> Envía un video (con caption opcional)\n\n"
        "El mensaje será enviado exactamente como lo envíes.\n\n"
        "👁️ Verás un preview antes de confirmar el envío."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


@admin_router.callback_query(F.data == "free:broadcast")
async def callback_broadcast_to_free(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Inicia broadcasting al canal Free.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"📤 Usuario {callback.from_user.id} iniciando broadcast a Free")

    await state.set_data({"target_channel": "free"})
    await state.set_state(BroadcastStates.waiting_for_content)

    text = (
        "📤 <b>Enviar Publicación a Canal Free</b>\n\n"
        "Envía el contenido que quieres publicar:\n\n"
        "• <b>Texto:</b> Envía un mensaje de texto\n"
        "• <b>Foto:</b> Envía una foto (con caption opcional)\n"
        "• <b>Video:</b> Envía un video (con caption opcional)\n\n"
        "El mensaje será enviado exactamente como lo envíes.\n\n"
        "👁️ Verás un preview antes de confirmar el envío."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


# ===== RECEPCIÓN DE CONTENIDO =====

@admin_router.message(
    BroadcastStates.waiting_for_content,
    F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO])
)
async def process_broadcast_content(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el contenido enviado para broadcasting.

    Guarda el contenido en FSM data y muestra preview.

    Args:
        message: Mensaje con el contenido
        state: FSM context
        session: Sesión de BD
    """
    user_id = message.from_user.id

    # Obtener data del FSM
    data = await state.get_data()
    target_channel = data.get("target_channel", "vip")

    logger.info(
        f"📥 Usuario {user_id} envió contenido para broadcast a {target_channel}"
    )

    # Determinar tipo de contenido
    content_type = message.content_type
    caption = None

    if content_type == ContentType.PHOTO:
        # Guardar file_id de la foto más grande
        photo = message.photo[-1]  # Última foto es la más grande
        file_id = photo.file_id
        caption = message.caption

    elif content_type == ContentType.VIDEO:
        file_id = message.video.file_id
        caption = message.caption

    else:  # TEXT
        file_id = None
        caption = message.text

    # Actualizar FSM data con contenido
    await state.update_data({
        "content_type": content_type,
        "file_id": file_id,
        "caption": caption,
        "original_message_id": message.message_id,
    })

    # Mostrar preview
    preview_text = await _generate_preview_text(target_channel, content_type, caption)

    # Enviar preview al admin
    await message.answer(
        text=preview_text,
        reply_markup=create_inline_keyboard([
            [
                {"text": "✅ Confirmar y Enviar", "callback_data": "broadcast:confirm"},
                {"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}
            ],
            [{"text": "🔄 Enviar Otro Contenido", "callback_data": "broadcast:change"}]
        ]),
        parse_mode="HTML"
    )

    # Reenviar el contenido como preview visual
    if content_type == ContentType.PHOTO:
        await message.answer_photo(
            photo=file_id,
            caption="👁️ <i>Preview del mensaje</i>",
            parse_mode="HTML"
        )
    elif content_type == ContentType.VIDEO:
        await message.answer_video(
            video=file_id,
            caption="👁️ <i>Preview del mensaje</i>",
            parse_mode="HTML"
        )

    # Cambiar a estado de confirmación
    await state.set_state(BroadcastStates.waiting_for_confirmation)

    logger.debug(f"✅ Preview generado para user {user_id}")


@admin_router.message(BroadcastStates.waiting_for_content)
async def process_invalid_content_type(message: Message, state: FSMContext):
    """
    Maneja contenido de tipo no soportado.

    Args:
        message: Mensaje con contenido inválido
        state: FSM context
    """
    logger.warning(
        f"⚠️ Usuario {message.from_user.id} envió tipo no soportado: {message.content_type}"
    )

    await message.answer(
        "❌ <b>Tipo de Contenido No Soportado</b>\n\n"
        "Por favor, envía:\n"
        "• Texto\n"
        "• Foto\n"
        "• Video\n\n"
        "Otros tipos (documentos, audios, etc) no están soportados.",
        parse_mode="HTML"
    )


# ===== CONFIRMACIÓN Y ENVÍO =====

@admin_router.callback_query(
    BroadcastStates.waiting_for_confirmation,
    F.data == "broadcast:confirm"
)
async def callback_broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Confirma y envía el mensaje al canal(es).

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    user_id = callback.from_user.id

    # Obtener data del FSM
    data = await state.get_data()
    target_channel = data["target_channel"]
    content_type = data["content_type"]
    file_id = data.get("file_id")
    caption = data.get("caption")

    logger.info(f"📤 Usuario {user_id} confirmó broadcast a {target_channel}")

    # Notificar que se está enviando
    await callback.answer("📤 Enviando publicación...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    # Determinar canales destino
    channels_to_send = []

    if target_channel == "vip":
        vip_channel = await container.channel.get_vip_channel_id()
        if vip_channel:
            channels_to_send.append(("VIP", vip_channel))

    elif target_channel == "free":
        free_channel = await container.channel.get_free_channel_id()
        if free_channel:
            channels_to_send.append(("Free", free_channel))

    # Validar que hay canales configurados
    if not channels_to_send:
        await callback.message.edit_text(
            "❌ <b>Error: Canales No Configurados</b>\n\n"
            "Debes configurar los canales antes de enviar publicaciones.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver", "callback_data": "admin:main"}]
            ]),
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Enviar a cada canal
    results = []

    for channel_name, channel_id in channels_to_send:
        try:
            if content_type == ContentType.PHOTO:
                success, msg, _ = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or "",
                    photo=file_id
                )

            elif content_type == ContentType.VIDEO:
                success, msg, _ = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or "",
                    video=file_id
                )

            else:  # TEXT
                success, msg, _ = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or ""
                )

            if success:
                results.append(f"✅ Canal {channel_name}")
                logger.info(f"✅ Publicación enviada a canal {channel_name}")
            else:
                results.append(f"❌ Canal {channel_name}: {msg}")
                logger.error(f"❌ Error enviando a {channel_name}: {msg}")

        except Exception as e:
            results.append(f"❌ Canal {channel_name}: Error inesperado")
            logger.error(f"❌ Excepción enviando a {channel_name}: {e}", exc_info=True)

    # Mostrar resultados
    results_text = "\n".join(results)

    await callback.message.edit_text(
        f"📤 <b>Resultado del Envío</b>\n\n{results_text}\n\n"
        f"La publicación ha sido procesada.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "admin:main"}]
        ]),
        parse_mode="HTML"
    )

    # Limpiar estado FSM
    await state.clear()

    logger.info(f"✅ Broadcasting completado para user {user_id}")


@admin_router.callback_query(
    BroadcastStates.waiting_for_confirmation,
    F.data == "broadcast:change"
)
async def callback_broadcast_change(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Permite cambiar el contenido (volver a waiting_for_content).

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.debug(f"🔄 Usuario {callback.from_user.id} cambiando contenido de broadcast")

    # Volver al estado de espera de contenido
    await state.set_state(BroadcastStates.waiting_for_content)

    data = await state.get_data()
    target_channel = data.get("target_channel", "vip")

    channel_name = {
        "vip": "VIP",
        "free": "Free",
    }.get(target_channel, "VIP")

    await callback.message.edit_text(
        f"📤 <b>Enviar Publicación a Canal {channel_name}</b>\n\n"
        f"Envía el nuevo contenido que quieres publicar.\n\n"
        f"El contenido anterior será descartado.",
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer("🔄 Envía nuevo contenido")


@admin_router.callback_query(F.data == "broadcast:cancel")
async def callback_broadcast_cancel(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Cancela el broadcasting y limpia estado.

    Funciona en cualquier estado de broadcasting.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"❌ Usuario {callback.from_user.id} canceló broadcasting")

    # Limpiar estado FSM
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Broadcasting Cancelado</b>\n\n"
        "La publicación no fue enviada.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "admin:main"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


# ===== HELPERS =====

async def _generate_preview_text(
    target_channel: str,
    content_type: str,
    caption: Optional[str]
) -> str:
    """
    Genera el texto de preview antes de enviar.

    Args:
        target_channel: "vip" o "free"
        content_type: Tipo de contenido (photo, video, text)
        caption: Caption o texto del mensaje

    Returns:
        String HTML formateado
    """
    channel_name = {
        "vip": "Canal VIP",
        "free": "Canal Free",
    }.get(target_channel, "Canal")

    content_name = {
        ContentType.PHOTO: "Foto",
        ContentType.VIDEO: "Video",
        ContentType.TEXT: "Texto"
    }.get(content_type, "Contenido")

    text = f"""
👁️ <b>Preview de Publicación</b>

<b>Destino:</b> {channel_name}
<b>Tipo:</b> {content_name}
    """.strip()

    if caption and content_type != ContentType.TEXT:
        text += f"\n\n<b>Caption:</b>\n{caption[:200]}"  # Primeros 200 chars
        if len(caption) > 200:
            text += "..."
    elif caption:
        text += f"\n\n<b>Texto:</b>\n{caption[:500]}"  # Primeros 500 chars
        if len(caption) > 500:
            text += "..."

    text += "\n\n⚠️ Verifica que el contenido sea correcto antes de confirmar."

    return text
