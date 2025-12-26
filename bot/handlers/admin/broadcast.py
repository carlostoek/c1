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
        # Inicializar configuración de gamificación
        "gamification_enabled": False,
        "selected_reactions": [],
        "content_protected": False,
    })

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

    # Cambiar a estado de configuración de opciones (NUEVO)
    await state.set_state(BroadcastStates.configuring_options)

    # Mostrar opciones de configuración
    await show_broadcast_options(message, state, session)

    logger.debug(f"✅ Contenido guardado, mostrando opciones para user {user_id}")


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


# ===== CONFIGURACIÓN DE OPCIONES (NUEVO) =====

async def show_broadcast_options(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Muestra opciones de gamificación y protección.

    Args:
        message: Mensaje original
        state: FSM context
        session: Sesión de BD
    """
    data = await state.get_data()
    gamif_enabled = data.get("gamification_enabled", False)
    protected = data.get("content_protected", False)
    selected_reactions = data.get("selected_reactions", [])

    # Construir texto con status
    status_text = "⚙️ <b>Configurar Opciones de Publicación</b>\n\n"

    # Estado de gamificación
    if gamif_enabled and selected_reactions:
        status_text += f"🎮 <b>Gamificación:</b> Activada ({len(selected_reactions)} reacciones)\n"
    else:
        status_text += "🎮 <b>Gamificación:</b> Desactivada\n"

    # Estado de protección
    if protected:
        status_text += "🔒 <b>Protección:</b> Activada (anti-forward)\n"
    else:
        status_text += "🔓 <b>Protección:</b> Desactivada\n"

    status_text += "\n<i>Configura las opciones antes de enviar.</i>"

    # Construir keyboard dinámico
    keyboard = []

    # Fila 1: Gamificación
    if gamif_enabled:
        keyboard.append([
            {"text": f"🎮 Reacciones ({len(selected_reactions)})", "callback_data": "broadcast:config:reactions"},
            {"text": "❌ Desactivar", "callback_data": "broadcast:config:gamif_off"}
        ])
    else:
        keyboard.append([
            {"text": "🎮 Activar Gamificación", "callback_data": "broadcast:config:reactions"}
        ])

    # Fila 2: Protección
    if protected:
        keyboard.append([
            {"text": "🔓 Desactivar Protección", "callback_data": "broadcast:config:protection_off"}
        ])
    else:
        keyboard.append([
            {"text": "🔒 Activar Protección", "callback_data": "broadcast:config:protection_on"}
        ])

    # Fila 3: Continuar o Cancelar
    keyboard.append([
        {"text": "✅ Continuar", "callback_data": "broadcast:config:continue"},
        {"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}
    ])

    await message.answer(
        text=status_text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )


@admin_router.callback_query(
    BroadcastStates.configuring_options,
    F.data == "broadcast:config:reactions"
)
async def show_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Muestra selector de reacciones.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    from sqlalchemy import select
    from bot.gamification.database.models import Reaction

    logger.debug(f"📝 Usuario {callback.from_user.id} seleccionando reacciones")

    # Obtener todas las reacciones disponibles
    stmt = select(Reaction).where(Reaction.active == True).order_by(Reaction.sort_order)
    result = await session.execute(stmt)
    reactions = result.scalars().all()

    if not reactions:
        await callback.answer("⚠️ No hay reacciones configuradas", show_alert=True)
        return

    # Obtener seleccionadas
    data = await state.get_data()
    selected = data.get("selected_reactions", [])

    # Cambiar a estado de selección
    await state.set_state(BroadcastStates.selecting_reactions)

    # Construir keyboard con checkboxes
    keyboard = []
    for reaction in reactions:
        emoji = reaction.button_emoji or reaction.emoji
        label = reaction.button_label or f"{reaction.besitos_value} besitos"
        check = "✓" if reaction.id in selected else ""

        keyboard.append([{
            "text": f"{emoji} {label} {check}",
            "callback_data": f"broadcast:react:toggle:{reaction.id}"
        }])

    # Botones de acción
    keyboard.append([
        {"text": "✅ Confirmar", "callback_data": "broadcast:react:confirm"},
        {"text": "❌ Cancelar", "callback_data": "broadcast:react:cancel"}
    ])

    text = (
        "🎮 <b>Seleccionar Reacciones</b>\n\n"
        "Toca los emojis para activar/desactivar.\n"
        "Los usuarios ganarán besitos al reaccionar.\n\n"
        f"<b>Seleccionadas:</b> {len(selected)}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )

    await callback.answer()


@admin_router.callback_query(
    BroadcastStates.selecting_reactions,
    F.data.startswith("broadcast:react:toggle:")
)
async def toggle_reaction(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Toggle selección de reacción.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])

    # Obtener seleccionadas
    data = await state.get_data()
    selected = data.get("selected_reactions", [])

    # Toggle
    if reaction_id in selected:
        selected.remove(reaction_id)
    else:
        selected.append(reaction_id)

    # Guardar
    await state.update_data(selected_reactions=selected)

    # Refrescar display
    await show_reaction_selection(callback, state, session)


@admin_router.callback_query(
    BroadcastStates.selecting_reactions,
    F.data == "broadcast:react:confirm"
)
async def confirm_reactions(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Confirma selección de reacciones.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    data = await state.get_data()
    selected = data.get("selected_reactions", [])

    # Validar que hay al menos una
    if not selected:
        await callback.answer("⚠️ Selecciona al menos una reacción", show_alert=True)
        return

    # Marcar gamificación como habilitada
    await state.update_data(gamification_enabled=True)

    # Volver a configuring_options
    await state.set_state(BroadcastStates.configuring_options)

    await callback.answer(f"✅ {len(selected)} reacciones seleccionadas")

    # Mostrar opciones nuevamente
    # Crear un mensaje ficticio para reutilizar la función
    class FakeMessage:
        def __init__(self, callback):
            self.from_user = callback.from_user
            self.chat = callback.message.chat

        async def answer(self, *args, **kwargs):
            # Editar el mensaje actual en lugar de enviar nuevo
            await callback.message.edit_text(*args, **kwargs)

    fake_msg = FakeMessage(callback)
    await show_broadcast_options(fake_msg, state, session)


@admin_router.callback_query(
    BroadcastStates.selecting_reactions,
    F.data == "broadcast:react:cancel"
)
async def cancel_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Cancela selección de reacciones.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    # Volver a configuring_options
    await state.set_state(BroadcastStates.configuring_options)

    await callback.answer("❌ Selección cancelada")

    # Mostrar opciones nuevamente
    class FakeMessage:
        def __init__(self, callback):
            self.from_user = callback.from_user
            self.chat = callback.message.chat

        async def answer(self, *args, **kwargs):
            await callback.message.edit_text(*args, **kwargs)

    fake_msg = FakeMessage(callback)
    await show_broadcast_options(fake_msg, state, session)


@admin_router.callback_query(
    BroadcastStates.configuring_options,
    F.data == "broadcast:config:gamif_off"
)
async def disable_gamification(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Desactiva gamificación.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    await state.update_data(
        gamification_enabled=False,
        selected_reactions=[]
    )

    await callback.answer("❌ Gamificación desactivada")

    # Refrescar opciones
    class FakeMessage:
        def __init__(self, callback):
            self.from_user = callback.from_user
            self.chat = callback.message.chat

        async def answer(self, *args, **kwargs):
            await callback.message.edit_text(*args, **kwargs)

    fake_msg = FakeMessage(callback)
    await show_broadcast_options(fake_msg, state, session)


@admin_router.callback_query(
    BroadcastStates.configuring_options,
    F.data.startswith("broadcast:config:protection_")
)
async def toggle_protection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Toggle protección de contenido.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    action = callback.data.split("_")[-1]  # "on" o "off"
    protected = (action == "on")

    await state.update_data(content_protected=protected)

    msg = "🔒 Protección activada" if protected else "🔓 Protección desactivada"
    await callback.answer(msg)

    # Refrescar opciones
    class FakeMessage:
        def __init__(self, callback):
            self.from_user = callback.from_user
            self.chat = callback.message.chat

        async def answer(self, *args, **kwargs):
            await callback.message.edit_text(*args, **kwargs)

    fake_msg = FakeMessage(callback)
    await show_broadcast_options(fake_msg, state, session)


@admin_router.callback_query(
    BroadcastStates.configuring_options,
    F.data == "broadcast:config:continue"
)
async def continue_to_confirmation(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Continúa a confirmación final.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.debug(f"▶️ Usuario {callback.from_user.id} continuando a confirmación")

    # Obtener data
    data = await state.get_data()
    target_channel = data.get("target_channel", "vip")
    content_type = data.get("content_type")
    caption = data.get("caption")
    gamif_enabled = data.get("gamification_enabled", False)
    protected = data.get("content_protected", False)
    selected_reactions = data.get("selected_reactions", [])

    # Cambiar a waiting_for_confirmation
    await state.set_state(BroadcastStates.waiting_for_confirmation)

    # Generar preview final
    preview_text = await _generate_preview_text(target_channel, content_type, caption)

    # Agregar info de configuración
    preview_text += "\n\n<b>⚙️ Configuración:</b>\n"
    if gamif_enabled and selected_reactions:
        preview_text += f"🎮 Gamificación: {len(selected_reactions)} reacciones\n"
    else:
        preview_text += "🎮 Gamificación: Desactivada\n"

    if protected:
        preview_text += "🔒 Protección: Activada\n"
    else:
        preview_text += "🔓 Protección: Desactivada\n"

    preview_text += "\n✅ ¿Confirmar envío?"

    await callback.message.edit_text(
        text=preview_text,
        reply_markup=create_inline_keyboard([
            [
                {"text": "✅ Confirmar y Enviar", "callback_data": "broadcast:confirm"},
                {"text": "🔙 Volver a Opciones", "callback_data": "broadcast:back_to_options"}
            ],
            [{"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


@admin_router.callback_query(
    BroadcastStates.waiting_for_confirmation,
    F.data == "broadcast:back_to_options"
)
async def back_to_options(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Vuelve a pantalla de opciones.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    await state.set_state(BroadcastStates.configuring_options)

    await callback.answer("🔙 Volviendo a opciones")

    # Mostrar opciones
    class FakeMessage:
        def __init__(self, callback):
            self.from_user = callback.from_user
            self.chat = callback.message.chat

        async def answer(self, *args, **kwargs):
            await callback.message.edit_text(*args, **kwargs)

    fake_msg = FakeMessage(callback)
    await show_broadcast_options(fake_msg, state, session)


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
    Confirma y envía el mensaje al canal(es) usando BroadcastService.

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
    gamif_enabled = data.get("gamification_enabled", False)
    selected_reactions = data.get("selected_reactions", [])
    content_protected = data.get("content_protected", False)

    logger.info(
        f"📤 Usuario {user_id} confirmó broadcast a {target_channel} "
        f"(gamif={gamif_enabled}, protected={content_protected})"
    )

    # Notificar que se está enviando
    await callback.answer("📤 Enviando publicación...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    # Preparar configuración de gamificación
    gamification_config = None
    if gamif_enabled and selected_reactions:
        gamification_config = {
            "enabled": True,
            "reaction_types": selected_reactions
        }

    # Determinar tipo de contenido para BroadcastService
    content_type_str = {
        ContentType.PHOTO: "photo",
        ContentType.VIDEO: "video",
        ContentType.TEXT: "text"
    }.get(content_type, "text")

    # Enviar usando BroadcastService
    try:
        result = await container.broadcast.send_broadcast_with_gamification(
            target=target_channel,
            content_type=content_type_str,
            content_text=caption,
            media_file_id=file_id,
            sent_by=user_id,
            gamification_config=gamification_config,
            content_protected=content_protected
        )

        # Procesar resultados
        if result["success"]:
            # Éxito
            channels_sent = ", ".join(result["channels_sent"])
            results_text = f"✅ <b>Publicación enviada exitosamente</b>\n\n"
            results_text += f"📡 Canales: {channels_sent}\n"

            if result["broadcast_message_ids"]:
                results_text += f"🎮 Gamificación: Activada ({len(selected_reactions)} reacciones)\n"
                results_text += f"🗄️ Registrado en BD: {len(result['broadcast_message_ids'])} mensajes\n"

            if content_protected:
                results_text += "🔒 Protección: Activada\n"

            logger.info(f"✅ Broadcasting exitoso para user {user_id}")

        else:
            # Error
            errors_text = "\n".join([f"• {err}" for err in result["errors"]])
            results_text = f"❌ <b>Error al Enviar</b>\n\n{errors_text}"

            logger.error(f"❌ Broadcasting fallido para user {user_id}: {result['errors']}")

    except Exception as e:
        results_text = f"❌ <b>Error Inesperado</b>\n\n{str(e)}"
        logger.error(f"❌ Excepción en broadcasting para user {user_id}: {e}", exc_info=True)

    # Mostrar resultados
    await callback.message.edit_text(
        f"📤 <b>Resultado del Envío</b>\n\n{results_text}",
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
