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
from aiogram.types import CallbackQuery, Message, ContentType, InlineKeyboardMarkup
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
    Handler cuando admin confirma el contenido.
    
    CAMBIO: Ahora en lugar de enviar directamente, muestra opciones.
    
    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    
    logger.info(f"✅ Usuario {user_id} confirmó contenido, mostrando opciones")
    
    # Cambiar a estado de opciones
    await state.set_state(BroadcastStates.choosing_options)
    
    # Inicializar opciones en FSM data (ambas en False por defecto)
    await state.update_data(
        attach_reactions=False,
        protect_content=False
    )
    
    # Obtener data del contenido
    data = await state.get_data()
    target_channel = data.get("target_channel", "vip")
    channel_name = {"vip": "VIP", "free": "Free"}.get(target_channel, "VIP")
    
    # Construir mensaje de opciones
    text = (
        f"📤 <b>Opciones de Publicación - Canal {channel_name}</b>\n\n"
        f"Selecciona las opciones que deseas aplicar:\n\n"
        f"<b>Opciones disponibles:</b>\n"
        f"❌ Adjuntar botones de reacción\n"
        f"❌ Proteger contenido (sin reenvío/guardado)\n\n"
        f"Haz click en las opciones para activarlas/desactivarlas.\n"
        f"Cuando estés listo, confirma para enviar."
    )
    
    # Keyboard con opciones
    keyboard_buttons = [
        [{
            "text": "❌ Adjuntar Reacciones",
            "callback_data": "broadcast:toggle:reactions"
        }],
        [{
            "text": "❌ Proteger Contenido",
            "callback_data": "broadcast:toggle:protect"
        }],
        [{
            "text": "✅ Confirmar y Enviar",
            "callback_data": "broadcast:confirm_options"
        }],
        [{
            "text": "❌ Cancelar",
            "callback_data": "broadcast:cancel"
        }]
    ]
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    
    await callback.answer()


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


@admin_router.callback_query(
    BroadcastStates.choosing_options,
    F.data.startswith("broadcast:toggle:")
)
async def callback_toggle_option(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Toggle (activar/desactivar) una opción.
    
    Opciones:
    - broadcast:toggle:reactions → Toggle attach_reactions
    - broadcast:toggle:protect → Toggle protect_content
    
    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    # Extraer qué opción se está toggleando
    option = callback.data.split(":")[-1]  # "reactions" o "protect"
    
    logger.debug(f"🔄 Usuario {callback.from_user.id} toggleando opción: {option}")
    
    # Obtener estado actual de opciones
    data = await state.get_data()
    attach_reactions = data.get("attach_reactions", False)
    protect_content = data.get("protect_content", False)
    target_channel = data.get("target_channel", "vip")
    
    # Toggle la opción correspondiente
    if option == "reactions":
        attach_reactions = not attach_reactions
        await state.update_data(attach_reactions=attach_reactions)
        
        # Validar que hay reacciones configuradas
        if attach_reactions:
            container = ServiceContainer(session, callback.bot)
            active_reactions = await container.reactions.get_active_reactions()
            
            if not active_reactions:
                # No hay reacciones configuradas, revertir
                await state.update_data(attach_reactions=False)
                attach_reactions = False
                
                await callback.answer(
                    "❌ No hay reacciones configuradas.\n"
                    "Configúralas primero en el menú admin.",
                    show_alert=True
                )
                return
    
    elif option == "protect":
        protect_content = not protect_content
        await state.update_data(protect_content=protect_content)
    
    # Actualizar el mensaje con el nuevo estado
    channel_name = {"vip": "VIP", "free": "Free"}.get(target_channel, "VIP")
    
    reactions_icon = "✅" if attach_reactions else "❌"
    protect_icon = "✅" if protect_content else "❌"
    
    text = (
        f"📤 <b>Opciones de Publicación - Canal {channel_name}</b>\n\n"
        f"Selecciona las opciones que deseas aplicar:\n\n"
        f"<b>Opciones disponibles:</b>\n"
        f"{reactions_icon} Adjuntar botones de reacción\n"
        f"{protect_icon} Proteger contenido (sin reenvío/guardado)\n\n"
        f"Haz click en las opciones para activarlas/desactivarlas.\n"
        f"Cuando estés listo, confirma para enviar."
    )
    
    # Actualizar keyboard con iconos actualizados
    keyboard_buttons = [
        [{
            "text": f"{reactions_icon} Adjuntar Reacciones",
            "callback_data": "broadcast:toggle:reactions"
        }],
        [{
            "text": f"{protect_icon} Proteger Contenido",
            "callback_data": "broadcast:toggle:protect"
        }],
        [{
            "text": "✅ Confirmar y Enviar",
            "callback_data": "broadcast:confirm_options"
        }],
        [{
            "text": "❌ Cancelar",
            "callback_data": "broadcast:cancel"
        }]
    ]
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    
    # Feedback al usuario
    option_name = "Reacciones" if option == "reactions" else "Protección"
    status = "activada" if (attach_reactions if option == "reactions" else protect_content) else "desactivada"
    
    await callback.answer(f"✅ {option_name} {status}", show_alert=False)


@admin_router.callback_query(
    BroadcastStates.choosing_options,
    F.data == "broadcast:confirm_options"
)
async def callback_confirm_options(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Confirma opciones y envía el mensaje al canal.
    
    Este handler contiene el código de envío que antes estaba
    en callback_broadcast_confirm.
    
    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    
    # Obtener data del FSM (contenido + opciones)
    data = await state.get_data()
    target_channel = data["target_channel"]
    content_type = data["content_type"]
    file_id = data.get("file_id")
    caption = data.get("caption")
    attach_reactions = data.get("attach_reactions", False)
    protect_content = data.get("protect_content", False)
    
    logger.info(
        f"📤 Usuario {user_id} confirmó envío a {target_channel} "
        f"[reacciones: {attach_reactions}, protección: {protect_content}]"
    )
    
    # Notificar que se está enviando
    await callback.answer("📤 Enviando publicación...", show_alert=False)
    
    container = ServiceContainer(session, callback.bot)
    
    # Determinar canales destino (CÓDIGO EXISTENTE)
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
    
    # Generar keyboard de reacciones si se activó la opción
    reaction_keyboard = None
    if attach_reactions:
        # Obtener reacciones activas
        active_reactions = await container.reactions.get_active_reactions()
        
        if active_reactions:
            # Generar keyboard (se implementará en Prompt 4.3)
            # Por ahora, placeholder
            reaction_keyboard = await _generate_reaction_keyboard(
                active_reactions,
                channel_id=channels_to_send[0][1],  # ID del canal
                message_id=0  # Se actualizará después de enviar
            )
    
    # Enviar a cada canal (CÓDIGO EXISTENTE CON MODIFICACIONES)
    results = []
    
    for channel_name, channel_id in channels_to_send:
        try:
            # Preparar kwargs para envío
            send_kwargs = {
                "protect_content": protect_content  # NUEVO: aplicar protección
            }
            
            # Enviar según tipo de contenido
            if content_type == "photo":
                success, msg, sent_message = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or "",
                    photo=file_id,
                    **send_kwargs
                )
            
            elif content_type == "video":
                success, msg, sent_message = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or "",
                    video=file_id,
                    **send_kwargs
                )
            
            else:  # TEXT
                success, msg, sent_message = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or "",
                    **send_kwargs
                )
            
            if success:
                results.append(f"✅ Canal {channel_name}")
                logger.info(f"✅ Publicación enviada a canal {channel_name}")
                
                # AGREGAR: Si se activaron reacciones, editar mensaje con keyboard
                if attach_reactions and sent_message:
                    try:
                        # Generar keyboard con el message_id real
                        reaction_keyboard = await _generate_reaction_keyboard(
                            reactions=active_reactions,
                            channel_id=channel_id,
                            message_id=sent_message.message_id
                        )
                        
                        if reaction_keyboard:
                            # Editar mensaje para agregar keyboard
                            await callback.bot.edit_message_reply_markup(
                                chat_id=channel_id,
                                message_id=sent_message.message_id,
                                reply_markup=reaction_keyboard
                            )
                            
                            logger.info(
                                f"✅ Keyboard de reacciones agregado a mensaje {sent_message.message_id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"⚠️ Error agregando keyboard a mensaje {sent_message.message_id}: {e}"
                        )
                        # No fallar el flujo completo, solo loguear
            else:
                results.append(f"❌ Canal {channel_name}: {msg}")
                logger.error(f"❌ Error enviando a {channel_name}: {msg}")
        
        except Exception as e:
            results.append(f"❌ Canal {channel_name}: Error inesperado")
            logger.error(f"❌ Excepción enviando a {channel_name}: {e}", exc_info=True)
    
    # Mostrar resultados
    results_text = "\n".join(results)
    
    # Construir resumen de opciones aplicadas
    options_summary = ""
    if attach_reactions:
        options_summary += "✅ Reacciones adjuntadas\n"
    if protect_content:
        options_summary += "✅ Contenido protegido\n"
    
    if options_summary:
        options_summary = f"\n<b>Opciones aplicadas:</b>\n{options_summary}"
    
    await callback.message.edit_text(
        f"📤 <b>Resultado del Envío</b>\n\n{results_text}\n"
        f"{options_summary}\n"
        f"La publicación ha sido procesada.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "admin:main"}]
        ]),
        parse_mode="HTML"
    )
    
    # Limpiar estado FSM
    await state.clear()
    
    logger.info(f"✅ Broadcasting completado para user {user_id}")


async def _generate_reaction_keyboard(
    reactions: list,
    channel_id: int,
    message_id: int
) -> Optional[InlineKeyboardMarkup]:
    """
    Genera keyboard con botones de reacción para una publicación.
    
    Args:
        reactions: Lista de ReactionConfig activas
        channel_id: ID del canal de Telegram
        message_id: ID del mensaje de Telegram
        
    Returns:
        InlineKeyboardMarkup o None si no hay reacciones
    """
    if not reactions:
        return None
    
    # Convertir ReactionConfig a tuplas (id, emoji, label)
    reactions_data = [
        (r.id, r.emoji, r.label)
        for r in reactions
    ]
    
    # Crear keyboard sin contadores (es mensaje nuevo)
    keyboard = create_reaction_keyboard(
        reactions=reactions_data,
        channel_id=channel_id,
        message_id=message_id,
        counts=None  # Sin contadores inicialmente
    )
    
    logger.debug(
        f"📊 Keyboard de reacciones generado: {len(reactions)} reacciones, "
        f"mensaje {message_id} en canal {channel_id}"
    )
    
    return keyboard
