"""
Handler de reacciones personalizadas para usuarios.

Responsabilidades:
- Procesar callbacks cuando usuario presiona botón de reacción
- Registrar reacción y otorgar besitos
- Actualizar keyboard con contadores y checkmarks personales
- Mostrar feedback inmediato al usuario
"""

import logging
from typing import Dict, List

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import BroadcastMessage
from bot.gamification.database.models import CustomReaction
from bot.gamification.services.container import GamificationContainer
from bot.middlewares import DatabaseMiddleware

logger = logging.getLogger(__name__)

# Router para reacciones de usuario
router = Router(name="gamification_reactions")

# Registrar middleware para inyectar session
router.callback_query.middleware(DatabaseMiddleware())


@router.callback_query(F.data.startswith("react:"))
async def handle_reaction_button(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Maneja cuando usuario presiona botón de reacción.

    Flujo:
    1. Extraer reaction_type_id del callback data
    2. Buscar BroadcastMessage en BD
    3. Registrar reacción via CustomReactionService
    4. Mostrar alert con besitos ganados
    5. Actualizar keyboard con checkmark personal

    Callback data format: "react:{reaction_type_id}"
    """
    try:
        # 1. Extraer reaction_type_id
        reaction_type_id = int(callback.data.split(":")[1])

        # 2. Obtener info del mensaje
        message_id = callback.message.message_id
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id

        logger.info(
            f"User {user_id} pressed reaction button {reaction_type_id} "
            f"on message {message_id} in chat {chat_id}"
        )

        # 3. Buscar BroadcastMessage
        stmt = select(BroadcastMessage).where(
            BroadcastMessage.message_id == message_id,
            BroadcastMessage.chat_id == chat_id
        )
        result = await session.execute(stmt)
        broadcast_msg = result.scalar_one_or_none()

        if not broadcast_msg:
            logger.warning(
                f"BroadcastMessage not found for message_id={message_id}, "
                f"chat_id={chat_id}"
            )
            await callback.answer(
                "⚠️ Mensaje no encontrado",
                show_alert=True
            )
            return

        # Obtener emoji de la configuración del mensaje
        emoji = "❤️"  # Default
        for btn_config in broadcast_msg.reaction_buttons:
            if btn_config.get("reaction_type_id") == reaction_type_id:
                emoji = btn_config.get("emoji", "❤️")
                break

        # =============================================
        # NUEVO: DETECTAR SI ES REACCIÓN NARRATIVA
        # =============================================
        from bot.narrative.services.reaction_narrative import NarrativeReactionService

        narrative_service = NarrativeReactionService(session)

        is_valid, error_msg, wait = await narrative_service.validate_reaction(
            user_id, broadcast_msg.id, emoji
        )

        if wait:
            # Usuario tiene misión narrativa activa
            if not is_valid:
                # Reacción inválida para misión
                await callback.answer(
                    f"⚠️ {error_msg}",
                    show_alert=True
                )
                return

            # Reacción válida: procesar como narrativa
            await _handle_narrative_reaction(
                callback=callback,
                session=session,
                broadcast_msg=broadcast_msg,
                reaction_type_id=reaction_type_id,
                emoji=emoji,
                wait=wait
            )
            return

        # Si no es narrativa, procesar como reacción normal
        # 4. Registrar reacción
        container = GamificationContainer(session, callback.bot)

        # Registrar reacción (el servicio maneja la validación de duplicados)
        result = await container.custom_reaction.register_custom_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user_id,
            reaction_type_id=reaction_type_id,
            emoji=emoji
        )

        # 5. Respuesta al usuario
        if not result["success"]:
            if result.get("already_reacted"):
                await callback.answer(
                    "Ya reaccionaste con este emoji 😊",
                    show_alert=False
                )
            else:
                await callback.answer(
                    "⚠️ Error al registrar reacción",
                    show_alert=True
                )
            return

        # Verificar y aplicar level-up automático
        changed, old_level, new_level = await container.level.check_and_apply_level_up(user_id)
        if changed:
            logger.info(
                f"Auto level-up triggered: User {user_id} "
                f"{old_level.name if old_level else 'None'} → {new_level.name}"
            )
            # Notificar level-up
            await container.notifications.notify_level_up(
                user_id, old_level, new_level
            )

        # Formatear respuesta con besitos ganados
        besitos = result["besitos_earned"]
        total = result["total_besitos"]
        response = f"¡+{besitos} besitos! 🎉\nTotal: {total:,} besitos"

        if result.get("multiplier_applied", 1.0) > 1.0:
            mult = result["multiplier_applied"]
            response += f"\n✨ Multiplicador x{mult} aplicado"

        await callback.answer(response, show_alert=False)

        # 6. Actualizar botones para marcar como reaccionado
        user_reactions = await container.custom_reaction.get_user_reactions_for_message(
            broadcast_msg.id,
            user_id
        )

        updated_keyboard = await build_reaction_keyboard_with_marks(
            session=session,
            broadcast_message_id=broadcast_msg.id,
            reaction_config=broadcast_msg.reaction_buttons,
            user_reacted_ids=user_reactions,
            bot=callback.bot
        )

        try:
            await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
        except TelegramBadRequest as e:
            logger.debug(f"Could not update keyboard: {e}")
            # No pasa nada si falla editar (mensaje no modificado, etc.)

        logger.info(
            f"✅ User {user_id} reacted with {emoji} "
            f"and earned {besitos} besitos"
        )

    except ValueError as e:
        logger.error(f"Invalid callback data: {callback.data} - {e}")
        await callback.answer(
            "⚠️ Formato de datos inválido",
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error handling reaction button: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error al procesar reacción",
            show_alert=True
        )


async def _handle_narrative_reaction(
    callback: CallbackQuery,
    session: AsyncSession,
    broadcast_msg: BroadcastMessage,
    reaction_type_id: int,
    emoji: str,
    wait
):
    """
    Procesa reacción narrativa (NUEVO).

    Flujo:
    1. Calcular tiempo de respuesta
    2. Registrar reacción con tiempo
    3. Analizar arquetipo
    4. Avanzar narrativa
    5. Enviar siguiente fragmento
    6. Notificar usuario

    Args:
        callback: CallbackQuery del usuario
        session: Sesión de BD
        broadcast_msg: Mensaje de broadcasting
        reaction_type_id: ID del tipo de reacción
        emoji: Emoji usado
        wait: NarrativeReactionWait activo
    """
    user_id = callback.from_user.id

    try:
        # 1. Calcular tiempo de respuesta
        from bot.narrative.services.reaction_narrative import NarrativeReactionService

        narrative_service = NarrativeReactionService(session)
        response_time = await narrative_service.calculate_response_time(wait)

        logger.info(
            f"⏱️ Tiempo de respuesta narrativo: user={user_id}, "
            f"time={response_time}s, fragment={wait.fragment_key}"
        )

        # 2. Registrar reacción con tiempo
        from bot.gamification.services.custom_reaction import CustomReactionService

        reaction_service = CustomReactionService(session)

        result = await reaction_service.register_narrative_reaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=user_id,
            reaction_type_id=reaction_type_id,
            emoji=emoji,
            fragment_key=wait.fragment_key,
            response_time_seconds=response_time
        )

        if not result["success"]:
            await callback.answer("⚠️ Error al registrar", show_alert=True)
            return

        # 3. Analizar arquetipo (integrado con decisiones)
        from bot.narrative.services.archetype import ArchetypeService

        archetype_service = ArchetypeService(session)

        archetype, confidence = await archetype_service.analyze_with_reactions(
            user_id=user_id,
            force=False
        )

        # 4. Completar wait
        await narrative_service.complete_reaction_wait(user_id)

        # 5. Avanzar narrativa
        from bot.narrative.services.progress import ProgressService

        progress_service = ProgressService(session)

        await progress_service.advance_after_reaction(
            user_id=user_id,
            current_fragment_key=wait.fragment_key,
            next_fragment_key=wait.next_fragment_key
        )

        # 6. Obtener siguiente fragmento
        from bot.narrative.services.container import NarrativeContainer

        narrative_container = NarrativeContainer(session, callback.bot)

        next_fragment = await narrative_container.fragment.get_fragment_by_key(
            wait.next_fragment_key
        )

        if not next_fragment:
            logger.error(
                f"Fragment not found: {wait.next_fragment_key}"
            )
            await callback.answer(
                "⚠️ Error al avanzar historia",
                show_alert=True
            )
            return

        # 7. Enviar fragmento siguiente al usuario en privado
        from bot.narrative.handlers.user.story import send_fragment_message

        await send_fragment_message(
            bot=callback.bot,
            user_id=user_id,
            fragment=next_fragment,
            session=session
        )

        # 8. Commit explícito
        await session.commit()

        # 9. Respuesta al usuario
        besitos = result["besitos_earned"]
        signal = result["archetype_signal"]

        response = (
            f"✅ ¡Reacción registrada!\n"
            f"+{besitos} besitos 🎉\n\n"
            f"⏱️ Tiempo: {response_time}s\n"
            f"🎭 Señal: {signal.upper()}\n\n"
            f"Continuemos la historia en privado..."
        )

        await callback.answer(response, show_alert=True)

        logger.info(
            f"✅ Reacción narrativa completada: user={user_id}, "
            f"besitos={besitos}, archetype={archetype.value}"
        )

    except Exception as e:
        logger.error(f"Error in narrative reaction: {e}", exc_info=True)
        await callback.answer(
            "⚠️ Error al procesar reacción narrativa",
            show_alert=True
        )


async def build_reaction_keyboard_with_marks(
    session: AsyncSession,
    broadcast_message_id: int,
    reaction_config: List[Dict],
    user_reacted_ids: List[int],
    bot = None
) -> InlineKeyboardMarkup:
    """
    Construye keyboard con contadores públicos y checkmark personal.

    Formato de botones:
    - Usuario NO ha reaccionado: "❤️ 33"
    - Usuario SÍ ha reaccionado: "❤️ 33 ✓"

    Args:
        session: Sesión de BD
        broadcast_message_id: ID del BroadcastMessage
        reaction_config: Lista de configs [{emoji, label, reaction_type_id, besitos}]
        user_reacted_ids: Lista de reaction_type_ids que el usuario ya usó
        bot: Instancia del bot (opcional, requerido para usar servicio)

    Returns:
        InlineKeyboardMarkup con 3 botones por fila
    """
    # Obtener stats de reacciones usando el servicio
    container = GamificationContainer(session, bot)
    stats = await container.custom_reaction.get_message_reaction_stats_by_type(
        broadcast_message_id
    )

    buttons = []
    for config in reaction_config:
        rt_id = config["reaction_type_id"]
        emoji = config["emoji"]

        # Obtener contador público
        count = stats.get(rt_id, 0)

        # Formato: "❤️ 33" o "❤️ 33 ✓"
        if rt_id in user_reacted_ids:
            text = f"{emoji} {count} ✓"
        else:
            text = f"{emoji} {count}"

        buttons.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"react:{rt_id}"
            )
        )

    # 3 botones por fila
    keyboard = []
    for i in range(0, len(buttons), 3):
        keyboard.append(buttons[i:i+3])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
