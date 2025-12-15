"""
User Reactions Handlers - Reacciones de usuarios a publicaciones.

Handlers para:
- Procesar clicks en botones de reacción
- Validar rate limiting
- Otorgar besitos
- Actualizar contadores
- Emitir eventos
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import MessageReaction
from bot.services.container import ServiceContainer
from bot.events.bus import event_bus
from bot.events.types import MessageReactedEvent
from bot.utils.keyboards import create_reaction_keyboard

logger = logging.getLogger(__name__)

# Router para handlers de reacciones de usuarios
user_reactions_router = Router(name="user_reactions")


# ===== HANDLER PRINCIPAL DE REACCIÓN =====

@user_reactions_router.callback_query(F.data.startswith("react:"))
async def callback_user_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Handler cuando un usuario hace click en un botón de reacción.

    Callback format: react:{emoji}:{channel_id}:{message_id}

    Flujo:
    1. Parse callback data (emoji, channel_id, message_id)
    2. Validar rate limiting (se implementará en Prompt 5.2)
    3. Registrar reacción en BD
    4. Otorgar besitos (se implementará en Prompt 5.3)
    5. Actualizar contador (se implementará en Prompt 5.4)
    6. Responder con feedback

    Args:
        callback: Callback query del botón de reacción
        session: Sesión de BD
    """
    user_id = callback.from_user.id

    try:
        # Paso 1: Parse callback data
        parts = callback.data.split(":")

        if len(parts) != 4:
            logger.error(f"❌ Callback data malformado: {callback.data}")
            await callback.answer("❌ Error procesando reacción", show_alert=True)
            return

        emoji = parts[1]
        channel_id = int(parts[2])
        message_id = int(parts[3])

        logger.info(
            f"💬 Usuario {user_id} reaccionando con '{emoji}' "
            f"a mensaje {message_id} en canal {channel_id}"
        )

        # Paso 2: Validar rate limiting
        # TODO: Implementar en Prompt 5.2
        # Por ahora, placeholder que siempre permite
        can_react, reason = await _validate_rate_limiting(
            user_id=user_id,
            session=session
        )

        if not can_react:
            await callback.answer(f"⏳ {reason}", show_alert=True)
            logger.warning(f"⚠️ Rate limit para user {user_id}: {reason}")
            return

        # Paso 3: Registrar reacción en BD
        container = ServiceContainer(session, callback.bot)

        reaction = await container.reactions.record_user_reaction(
            channel_id=channel_id,
            message_id=message_id,
            user_id=user_id,
            emoji=emoji
        )

        if not reaction:
            await callback.answer(
                "❌ Error al registrar reacción",
                show_alert=True
            )
            logger.error(f"❌ No se pudo registrar reacción para user {user_id}")
            return

        # Paso 4: Otorgar besitos
        # TODO: Implementar en Prompt 5.3
        besitos_awarded = await _award_besitos_for_reaction(
            user_id=user_id,
            reaction=reaction,
            session=session,
            bot=callback.bot
        )

        # Paso 5: Actualizar contador en botón
        # TODO: Implementar en Prompt 5.4
        await _update_reaction_counter(
            callback=callback,
            channel_id=channel_id,
            message_id=message_id,
            session=session
        )

        # Paso 6: Responder con feedback
        await callback.answer(
            f"✅ {emoji} +{besitos_awarded} 💋",
            show_alert=False
        )

        logger.info(
            f"✅ Reacción registrada: user {user_id} → '{emoji}' "
            f"(+{besitos_awarded} besitos)"
        )

    except ValueError as e:
        logger.error(f"❌ Error parseando callback data: {e}")
        await callback.answer("❌ Error procesando reacción", show_alert=True)

    except Exception as e:
        logger.error(
            f"❌ Error inesperado procesando reacción de user {user_id}: {e}",
            exc_info=True
        )
        await callback.answer("❌ Error inesperado", show_alert=True)


# ===== FUNCIONES HELPER (PLACEHOLDERS PARA PROMPTS SIGUIENTES) =====

async def _validate_rate_limiting(
    user_id: int,
    session: AsyncSession
) -> tuple[bool, str]:
    """
    Valida rate limiting de reacciones para un usuario.

    Reglas:
    1. Máximo 50 reacciones por día (últimas 24 horas)
    2. Mínimo 5 segundos desde la última reacción

    Args:
        user_id: ID del usuario
        session: Sesión de BD

    Returns:
        Tupla (can_react, reason):
        - can_react: True si puede reaccionar, False si no
        - reason: Mensaje explicando por qué no puede (vacío si puede)

    Example:
        >>> can_react, reason = await _validate_rate_limiting(123, session)
        >>> if not can_react:
        ...     print(f"No puede reaccionar: {reason}")
    """
    try:
        # Límites de rate limiting
        MAX_REACTIONS_PER_DAY = 50
        MIN_SECONDS_BETWEEN_REACTIONS = 5

        # Tiempo actual - usar datetime.utcnow() para consistencia con el modelo de BD
        # que usa datetime.utcnow() como default
        now = datetime.utcnow()

        # === VALIDACIÓN 1: Mínimo 5 segundos desde última reacción ===

        # Obtener la última reacción del usuario (cualquier mensaje)
        result_last = await session.execute(
            select(MessageReaction)
            .where(MessageReaction.user_id == user_id)
            .order_by(MessageReaction.created_at.desc())
            .limit(1)
        )
        last_reaction = result_last.scalar_one_or_none()

        if last_reaction:
            # Calcular tiempo desde última reacción
            time_since_last = (now - last_reaction.created_at).total_seconds()

            if time_since_last < MIN_SECONDS_BETWEEN_REACTIONS:
                wait_seconds = int(MIN_SECONDS_BETWEEN_REACTIONS - time_since_last) + 1
                reason = f"Espera {wait_seconds} segundos para reaccionar de nuevo"

                logger.debug(
                    f"⏳ User {user_id} bloqueado por rate limit: "
                    f"{time_since_last:.1f}s desde última reacción"
                )

                return (False, reason)

        # === VALIDACIÓN 2: Máximo 50 reacciones en últimas 24 horas ===

        # Calcular timestamp de hace 24 horas
        yesterday = now - timedelta(hours=24)

        # Contar reacciones del usuario en las últimas 24 horas
        result_count = await session.execute(
            select(func.count(MessageReaction.id))
            .where(
                and_(
                    MessageReaction.user_id == user_id,
                    MessageReaction.created_at >= yesterday
                )
            )
        )
        reactions_today = result_count.scalar()

        if reactions_today >= MAX_REACTIONS_PER_DAY:
            reason = f"Límite diario alcanzado ({MAX_REACTIONS_PER_DAY} reacciones)"

            logger.debug(
                f"⏳ User {user_id} bloqueado por límite diario: "
                f"{reactions_today}/{MAX_REACTIONS_PER_DAY}"
            )

            return (False, reason)

        # === VALIDACIONES PASADAS ===

        logger.debug(
            f"✅ Rate limiting OK para user {user_id}: "
            f"{reactions_today}/{MAX_REACTIONS_PER_DAY} hoy, "
            f"{time_since_last:.1f}s desde última" if last_reaction else "primera reacción"
        )

        return (True, "")

    except Exception as e:
        logger.error(
            f"❌ Error validando rate limiting para user {user_id}: {e}",
            exc_info=True
        )
        # En caso de error, permitir reacción (fail-open)
        return (True, "")


async def _award_besitos_for_reaction(
    user_id: int,
    reaction,
    session: AsyncSession,
    bot
) -> int:
    """
    Otorga besitos al usuario por reaccionar y emite evento.

    Flujo:
    1. Obtener GamificationService
    2. Usar award_besitos() para otorgar puntos
    3. Emitir MessageReactedEvent al event bus
    4. Retornar cantidad otorgada

    Args:
        user_id: ID del usuario
        reaction: MessageReaction registrada en BD
        session: Sesión de BD
        bot: Instancia del bot

    Returns:
        Cantidad de besitos otorgados (considerando multiplicadores)

    Example:
        >>> besitos = await _award_besitos_for_reaction(
        ...     user_id=123,
        ...     reaction=reaction_obj,
        ...     session=session,
        ...     bot=bot
        ... )
        >>> print(f"Otorgados: {besitos} besitos")
    """
    try:
        if not reaction:
            logger.warning(f"⚠️ No se puede otorgar besitos: reaction es None")
            return 0

        # Paso 1: Obtener GamificationService
        container = ServiceContainer(session, bot)
        gamification = container.gamification

        # Paso 2: Otorgar besitos usando el servicio
        # GamificationService.award_besitos() ya aplica multiplicadores automáticamente
        amount_awarded, ranked_up, new_rank = await gamification.award_besitos(
            user_id=user_id,
            action="message_reacted",
            custom_amount=reaction.besitos_awarded,
            custom_reason="Reacción a publicación"
        )

        if amount_awarded == 0:
            logger.warning(
                f"⚠️ No se pudieron otorgar besitos a user {user_id}"
            )
            return 0

        logger.info(
            f"💋 Besitos otorgados: user {user_id} → {amount_awarded} besitos "
            f"(puede haber multiplicador aplicado)"
        )

        # Paso 3: Emitir evento MessageReactedEvent
        try:
            event = MessageReactedEvent(
                user_id=user_id,
                channel_id=reaction.channel_id,
                message_id=reaction.message_id,
                emoji=reaction.emoji,
                besitos_awarded=reaction.besitos_awarded,
                timestamp=datetime.now(timezone.utc)
            )

            await event_bus.emit(event)

            logger.debug(
                f"📡 Evento MessageReactedEvent emitido: "
                f"user {user_id} → '{reaction.emoji}'"
            )
        except Exception as e:
            # No fallar el flujo si el evento no se puede emitir
            logger.error(
                f"❌ Error emitiendo MessageReactedEvent: {e}",
                exc_info=True
            )

        # Paso 4: Retornar cantidad base (sin multiplicador)
        # Note: GamificationService puede haber aplicado multiplicador,
        # pero retornamos la cantidad base configurada
        return reaction.besitos_awarded

    except Exception as e:
        logger.error(
            f"❌ Error otorgando besitos a user {user_id}: {e}",
            exc_info=True
        )
        return 0


async def _update_reaction_counter(
    callback: CallbackQuery,
    channel_id: int,
    message_id: int,
    session: AsyncSession
):
    """
    Actualiza el contador en el botón de reacción en tiempo real.

    Flujo:
    1. Obtener todas las reacciones activas (configs)
    2. Obtener contadores actuales del mensaje
    3. Regenerar keyboard con contadores actualizados
    4. Editar mensaje para actualizar keyboard

    Args:
        callback: Callback query original
        channel_id: ID del canal
        message_id: ID del mensaje
        session: Sesión de BD

    Note:
        Si falla la actualización, NO propaga error al handler.
        La reacción ya fue registrada, el contador es secundario.
    """
    try:
        container = ServiceContainer(session, callback.bot)

        # Paso 1: Obtener reacciones activas (configs)
        active_reactions = await container.reactions.get_active_reactions()

        if not active_reactions:
            logger.warning(
                f"⚠️ No hay reacciones activas para actualizar contador "
                f"en mensaje {message_id}"
            )
            return

        # Paso 2: Obtener contadores actuales del mensaje
        counts = await container.reactions.get_message_reaction_counts(
            channel_id=channel_id,
            message_id=message_id
        )

        logger.debug(
            f"📊 Contadores actuales de mensaje {message_id}: {counts}"
        )

        # Paso 3: Convertir reacciones a formato para keyboard
        reactions_data = [
            (r.id, r.emoji, r.label)
            for r in active_reactions
        ]

        # Paso 4: Regenerar keyboard con contadores actualizados
        updated_keyboard = create_reaction_keyboard(
            reactions=reactions_data,
            channel_id=channel_id,
            message_id=message_id,
            counts=counts  # Ahora con contadores reales
        )

        # Paso 5: Editar mensaje del canal para actualizar keyboard
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=channel_id,
                message_id=message_id,
                reply_markup=updated_keyboard
            )

            logger.debug(
                f"✅ Contador actualizado en mensaje {message_id}: {counts}"
            )

        except Exception as e:
            # Telegram puede fallar por rate limiting o mensaje ya no existe
            logger.warning(
                f"⚠️ No se pudo actualizar keyboard de mensaje {message_id}: {e}"
            )
            # No propagar: la reacción ya fue registrada

    except Exception as e:
        logger.error(
            f"❌ Error actualizando contador de mensaje {message_id}: {e}",
            exc_info=True
        )
        # No propagar: la reacción ya fue registrada, contador es secundario