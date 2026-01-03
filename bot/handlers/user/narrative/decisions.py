"""
Decisions Handler - Procesamiento de decisiones del usuario en la narrativa.

Responsabilidades:
- Procesar decisión seleccionada por el usuario
- Verificar/cobrar costos en besitos
- Registrar decisión en historial
- Actualizar arquetipo del usuario
- Otorgar recompensas si aplica
- Avanzar al siguiente fragmento
"""

import logging
from datetime import datetime

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.narrative import narrative_router
from bot.narrative.services.container import NarrativeContainer
from bot.gamification.services.container import GamificationContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


# =============================================================================
# FASE 3: TRACKING DE COMPORTAMIENTO
# =============================================================================

async def _track_decision(
    session: AsyncSession,
    user_id: int,
    decision_id: int,
    time_to_decide: Optional[float],
    options_available: int,
    is_systematic: bool = False,
    is_emotional: bool = False
):
    """
    Registra decisión narrativa para tracking de comportamiento (FASE 3).

    Args:
        session: Sesión de BD
        user_id: ID del usuario
        decision_id: ID de la decisión tomada
        time_to_decide: Segundos para tomar la decisión
        options_available: Cantidad de opciones disponibles
        is_systematic: Si siguió un patrón lógico/ordenado
        is_emotional: Si la elección fue emotiva
    """
    try:
        from bot.gamification.services.behavior_tracking import BehaviorTrackingService

        tracking = BehaviorTrackingService(session)

        # Registrar decisión
        await tracking.track_decision(
            user_id=user_id,
            decision_id=str(decision_id),
            time_to_decide=time_to_decide if time_to_decide else 0.0,
            options_available=options_available,
            decision_type="narrative",
            is_systematic=is_systematic,
            is_emotional=is_emotional
        )

        logger.debug(f"📊 Tracking: Usuario {user_id} tomó decisión {decision_id} en {time_to_decide}s")

    except Exception as e:
        # No fallar el flujo principal por errores de tracking
        logger.warning(f"⚠️ Error en tracking de decisión: {e}")


@narrative_router.callback_query(F.data.startswith("narr:decision:"))
async def callback_process_decision(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Procesa decisión del usuario.

    Flujo:
    1. Obtener decisión de BD
    2. Verificar requisitos (besitos, condiciones)
    3. Cobrar besitos si aplica
    4. Registrar decisión en historial
    5. Incrementar contador de decisiones
    6. Actualizar arquetipo (tiempo de respuesta)
    7. Otorgar besitos/recompensas si aplica
    8. Avanzar al siguiente fragmento

    Args:
        callback: Callback del botón de decisión
        session: Sesión de BD (inyectada por middleware)
    """
    await callback.answer()
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name or "Usuario"

    # Extraer decision_id del callback data
    decision_id = int(callback.data.split(":")[-1])

    logger.info(
        f"🎯 Usuario {user_id} ({user_name}) seleccionó decisión {decision_id}"
    )

    narrative = NarrativeContainer(session, callback.bot)
    gamification = GamificationContainer(session, callback.bot)

    # Obtener decisión de BD
    decision = await narrative.decision.get_decision_by_id(decision_id)
    if not decision:
        await callback.message.edit_text(
            "❌ <b>Error</b>\n\n"
            "Esta decisión no existe o fue eliminada.",
            parse_mode="HTML"
        )
        return

    # Obtener fragmento actual (para calcular tiempo de respuesta)
    progress = await narrative.progress.get_or_create_progress(user_id)
    response_time = None
    if progress.last_interaction:
        delta = datetime.utcnow() - progress.last_interaction
        response_time = int(delta.total_seconds())

    # Procesar decisión
    success, message, next_fragment = await narrative.decision.process_decision(
        user_id=user_id,
        decision_id=decision_id,
        response_time=response_time
    )

    if not success:
        # Error al procesar (ej: besitos insuficientes)
        keyboard = create_inline_keyboard([[
            {"text": "🔙 Volver", "callback_data": "narr:start"}
        ]])
        await callback.message.edit_text(
            f"❌ <b>No puede tomar esta decisión</b>\n\n{message}",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # FASE 3: Tracking de decisión tomada
    # Obtener cantidad de decisiones disponibles para este fragmento
    available_decisions = await narrative.decision.get_available_decisions(
        progress.current_fragment_key if progress.current_fragment_key else "",
        user_id=user_id
    )
    options_count = len(available_decisions) if available_decisions else 1

    # Determinar si fue sistemática/ejecutiva (primera opción = más directo)
    # Esto es una simplificación; podría mejorarse con análisis más profundo
    is_systematic = (decision_id == sorted([d.id for d in available_decisions])[0]) if available_decisions else False

    await _track_decision(
        session=session,
        user_id=user_id,
        decision_id=decision_id,
        time_to_decide=response_time,
        options_available=options_count,
        is_systematic=is_systematic,
        is_emotional=False  # Podría derivarse de tags del fragmento
    )

    # Incrementar contador de decisiones
    await narrative.progress.increment_decisions(user_id)

    # Actualizar arquetipo si hay tiempo de respuesta registrado
    if response_time is not None:
        try:
            archetype, confidence = await narrative.archetype.analyze_and_update(
                user_id=user_id,
                force=False
            )
            logger.debug(
                f"🎭 Arquetipo actualizado: {archetype.value} "
                f"(confianza: {confidence:.2f}, tiempo: {response_time}s)"
            )
        except Exception as e:
            logger.error(f"❌ Error actualizando arquetipo: {e}")

    # Si no hay siguiente fragmento, mostrar mensaje final
    if not next_fragment:
        keyboard = create_inline_keyboard([[
            {"text": "🏁 Finalizar", "callback_data": "profile:back"}
        ]])
        await callback.message.edit_text(
            "🎉 <b>¡Has completado este capítulo!</b>\n\n"
            f"{message}\n\n"
            "Vuelve más tarde para continuar la historia.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # Avanzar al siguiente fragmento
    await narrative.progress.advance_to(
        user_id,
        next_fragment.fragment_key,
        next_fragment.chapter_id
    )

    # Formatear y mostrar siguiente fragmento
    await _show_fragment(callback.message, narrative, user_id, next_fragment)

    logger.info(
        f"✅ Usuario {user_id} avanzó a fragmento: {next_fragment.fragment_key}"
    )


async def _show_fragment(message, narrative: NarrativeContainer, user_id: int, fragment):
    """
    Muestra un fragmento narrativo formateado.

    Duplicado de story.py para evitar imports circulares.

    Args:
        message: Mensaje de Telegram para editar
        narrative: Container de narrativa
        user_id: ID del usuario
        fragment: Fragmento a mostrar
    """
    # Validar requisitos del fragmento
    can_access, rejection_msg = await narrative.requirements.can_access_fragment(
        user_id,
        fragment.fragment_key
    )

    if not can_access:
        # Usuario no cumple requisitos
        keyboard = create_inline_keyboard([[
            {"text": "🔙 Volver", "callback_data": "narr:start"}
        ]])
        await message.edit_text(
            f"🔒 <b>Acceso Restringido</b>\n\n{rejection_msg}",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logger.info(
            f"⛔ Usuario {user_id} no puede acceder a {fragment.fragment_key}: "
            f"{rejection_msg}"
        )
        return

    # Formatear contenido narrativo
    text = await narrative.fragment.format_fragment_message(fragment)

    # Obtener decisiones disponibles
    decisions = await narrative.decision.get_available_decisions(
        fragment.fragment_key,
        user_id=user_id
    )

    # Generar keyboard con decisiones
    keyboard = await _build_decisions_keyboard(decisions)

    # Enviar fragmento (editar mensaje existente)
    try:
        await message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"❌ Error al mostrar fragmento: {e}")
        # Si falla editar, enviar nuevo mensaje
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def _build_decisions_keyboard(decisions):
    """
    Construye keyboard con botones de decisiones.

    Args:
        decisions: Lista de decisiones disponibles

    Returns:
        InlineKeyboardMarkup con botones
    """
    if not decisions:
        # Sin decisiones: fragmento final o sin opciones configuradas
        buttons = [[
            {"text": "🔙 Volver al Menú", "callback_data": "profile:back"}
        ]]
        return create_inline_keyboard(buttons)

    # Construir botones de decisiones (ordenados por 'order')
    buttons = []
    for decision in sorted(decisions, key=lambda d: d.order):
        # Formato: "emoji texto (costo besitos)" si tiene costo
        button_text = decision.button_text
        if decision.besitos_cost > 0:
            button_text = f"{button_text} ({decision.besitos_cost} 💋)"

        buttons.append([{
            "text": button_text,
            "callback_data": f"narr:decision:{decision.id}"
        }])

    # Agregar botón de volver al menú
    buttons.append([
        {"text": "🔙 Volver al Menú", "callback_data": "profile:back"}
    ])

    return create_inline_keyboard(buttons)
