"""
Handler de desafíos narrativos.

Gestiona el flujo de desafíos interactivos donde el usuario
debe resolver acertijos, responder preguntas o completar tareas.
"""
import logging
from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.services.container import NarrativeContainer
from bot.narrative.states.challenge import ChallengeStates
from bot.narrative.config import NarrativeConfig
from bot.narrative.database.enums import CooldownType

logger = logging.getLogger(__name__)

challenge_router = Router(name="narrative_challenge")


# ========================================
# HELPERS
# ========================================

def format_challenge_message(
    question: str,
    attempts_remaining: int,
    hints_available: int,
    hints_used: int
) -> str:
    """
    Formatea el mensaje del desafío.

    Args:
        question: Pregunta del desafío
        attempts_remaining: Intentos restantes
        hints_available: Pistas disponibles
        hints_used: Pistas ya usadas

    Returns:
        Mensaje formateado
    """
    message = "🧩 <b>Desafío</b>\n\n"
    message += f"{question}\n\n"
    message += f"📊 Intentos restantes: {attempts_remaining}\n"

    if hints_available > 0:
        hints_left = hints_available - hints_used
        message += f"💡 Pistas disponibles: {hints_left}/{hints_available}\n"

    message += "\n<i>Escribe tu respuesta...</i>"

    return message


def build_challenge_keyboard(
    challenge_id: int,
    can_get_hint: bool = True,
    can_skip: bool = False
) -> InlineKeyboardMarkup:
    """
    Construye teclado para el desafío.
    """
    buttons = []

    if can_get_hint:
        buttons.append([
            InlineKeyboardButton(
                text="💡 Pedir pista",
                callback_data=f"challenge:hint:{challenge_id}"
            )
        ])

    if can_skip:
        buttons.append([
            InlineKeyboardButton(
                text="⏭️ Saltar desafío",
                callback_data=f"challenge:skip:{challenge_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="❌ Cancelar",
            callback_data="challenge:cancel"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_result_keyboard(
    success: bool,
    next_fragment_key: Optional[str] = None,
    can_retry: bool = False,
    challenge_id: Optional[int] = None
) -> InlineKeyboardMarkup:
    """
    Construye teclado para el resultado.
    """
    buttons = []

    if success and next_fragment_key:
        buttons.append([
            InlineKeyboardButton(
                text="➡️ Continuar",
                callback_data=f"story:goto:{next_fragment_key}"
            )
        ])
    elif can_retry and challenge_id:
        buttons.append([
            InlineKeyboardButton(
                text="🔄 Intentar de nuevo",
                callback_data=f"challenge:retry:{challenge_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="📔 Ver diario",
            callback_data="journal:main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========================================
# HANDLERS
# ========================================

@challenge_router.callback_query(F.data.startswith("challenge:start:"))
async def callback_start_challenge(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Iniciar un desafío.
    """
    challenge_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Obtener desafío
    challenge = await container.challenge.get_challenge_by_id(challenge_id)
    if not challenge:
        await callback.answer("Desafío no encontrado", show_alert=True)
        return

    # Verificar si puede intentar
    can_attempt, block_message, remaining = await container.challenge.can_attempt(
        user_id, challenge_id
    )
    if not can_attempt:
        await callback.answer(block_message, show_alert=True)
        return

    # Verificar cooldown
    is_on_cooldown, cooldown = await container.cooldown.check_cooldown(
        user_id, CooldownType.CHALLENGE, str(challenge_id)
    )
    if is_on_cooldown:
        await callback.answer(
            f"⏳ {cooldown.narrative_message}\n({cooldown.remaining_seconds}s)",
            show_alert=True
        )
        return

    # Obtener pistas disponibles
    hints = await container.challenge.get_available_hints(challenge_id)

    # Guardar estado
    await state.set_state(ChallengeStates.waiting_for_answer)
    await state.update_data(
        challenge_id=challenge_id,
        fragment_key=challenge.fragment_key,
        hints_used=0,
        start_time=datetime.utcnow().isoformat()
    )

    # Mostrar desafío
    message = format_challenge_message(
        question=challenge.question,
        attempts_remaining=remaining,
        hints_available=len(hints),
        hints_used=0
    )

    keyboard = build_challenge_keyboard(
        challenge_id=challenge_id,
        can_get_hint=len(hints) > 0
    )

    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@challenge_router.message(ChallengeStates.waiting_for_answer)
async def process_challenge_answer(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesar respuesta del usuario al desafío.
    """
    user_id = message.from_user.id
    user_answer = message.text.strip()

    # Obtener datos del estado
    data = await state.get_data()
    challenge_id = data.get("challenge_id")
    hints_used = data.get("hints_used", 0)
    start_time_str = data.get("start_time")

    if not challenge_id:
        await state.clear()
        await message.answer("❌ Error: desafío no encontrado. Intenta de nuevo.")
        return

    container = NarrativeContainer(session)

    # Calcular tiempo de respuesta
    response_time = None
    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
        response_time = int((datetime.utcnow() - start_time).total_seconds())

    # Procesar intento
    result = await container.challenge.process_challenge_attempt(
        user_id=user_id,
        challenge_id=challenge_id,
        user_answer=user_answer,
        response_time_seconds=response_time,
        hints_used=hints_used
    )

    # Construir mensaje de resultado
    if result["success"]:
        response_msg = "✅ <b>¡Correcto!</b>\n\n"
        response_msg += f"{result['message']}\n"

        # Otorgar recompensas si las hay
        if result.get("reward_besitos", 0) > 0:
            response_msg += f"\n💋 +{result['reward_besitos']} besitos"

        if result.get("reward_clue_slug"):
            clue_result = await container.clue.grant_clue(
                user_id, result["reward_clue_slug"]
            )
            if clue_result[0]:
                response_msg += f"\n{clue_result[1]}"

        # Limpiar estado
        await state.clear()

        # Obtener fragmento de destino (continuar historia)
        challenge = await container.challenge.get_challenge_by_id(challenge_id)
        next_key = None
        if challenge:
            # Usar success_redirect_key si está definido, sino buscar primera decisión (fallback)
            if challenge.success_redirect_key:
                next_key = challenge.success_redirect_key
            else:
                # Fallback: buscar primera decisión disponible
                decisions = await container.decision.get_available_decisions(
                    challenge.fragment_key
                )
                if decisions:
                    next_key = decisions[0].target_fragment_key

        keyboard = build_result_keyboard(
            success=True,
            next_fragment_key=next_key
        )

    else:
        response_msg = "❌ <b>Incorrecto</b>\n\n"
        response_msg += f"{result['message']}\n"

        if result.get("can_retry"):
            response_msg += f"\n📊 Intentos restantes: {result.get('attempts_remaining', 0)}"

            # Actualizar tiempo de inicio para nuevo intento
            await state.update_data(start_time=datetime.utcnow().isoformat())

            keyboard = build_challenge_keyboard(
                challenge_id=challenge_id,
                can_get_hint=True
            )
        else:
            # No puede reintentar
            await state.clear()

            # Establecer cooldown
            await container.cooldown.set_challenge_cooldown(
                user_id=user_id,
                challenge_id=challenge_id,
                duration_seconds=NarrativeConfig.CHALLENGE_RETRY_COOLDOWN_SECONDS
            )

            keyboard = build_result_keyboard(
                success=False,
                can_retry=False
            )

            # Redirigir si hay fragmento de fallo
            if result.get("redirect_key"):
                response_msg += f"\n\n<i>Serás redirigido...</i>"

    await message.answer(
        response_msg,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@challenge_router.callback_query(F.data.startswith("challenge:hint:"))
async def callback_get_hint(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Mostrar pista del desafío.
    """
    challenge_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Obtener datos del estado
    data = await state.get_data()
    hints_used = data.get("hints_used", 0)

    # Obtener siguiente pista
    hint, hint_index, total_hints = await container.challenge.get_next_hint(
        user_id, challenge_id
    )

    if hint is None:
        await callback.answer("No hay más pistas disponibles", show_alert=True)
        return

    # Actualizar contador de pistas usadas
    await state.update_data(hints_used=hint_index)

    # Mostrar pista
    hint_msg = f"💡 <b>Pista {hint_index}/{total_hints}</b>\n\n"
    hint_msg += f"<i>{hint}</i>"

    await callback.answer()
    await callback.message.answer(hint_msg, parse_mode="HTML")


@challenge_router.callback_query(F.data.startswith("challenge:retry:"))
async def callback_retry_challenge(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Reintentar desafío.
    """
    challenge_id = int(callback.data.split(":")[2])

    # Redirigir a iniciar desafío
    callback.data = f"challenge:start:{challenge_id}"
    await callback_start_challenge(callback, session, state)


@challenge_router.callback_query(F.data.startswith("challenge:skip:"))
async def callback_skip_challenge(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Saltar desafío (si está permitido).
    """
    challenge_id = int(callback.data.split(":")[2])
    container = NarrativeContainer(session)

    # Obtener desafío
    challenge = await container.challenge.get_challenge_by_id(challenge_id)
    if not challenge:
        await callback.answer("Desafío no encontrado", show_alert=True)
        return

    # Limpiar estado
    await state.clear()

    # Si hay fragmento de redirección por fallo, ir ahí
    if challenge.failure_redirect_key:
        await callback.answer("Desafío saltado")
        # Redirigir al fragmento de fallo
        callback.data = f"story:goto:{challenge.failure_redirect_key}"
        from bot.narrative.handlers.user.story import show_fragment
        await show_fragment(
            message=callback.message,
            session=session,
            fragment_key=challenge.failure_redirect_key,
            user_id=callback.from_user.id,
            is_new_message=False
        )
    else:
        await callback.answer(
            "No puedes saltar este desafío",
            show_alert=True
        )


@challenge_router.callback_query(F.data == "challenge:cancel")
async def callback_cancel_challenge(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Cancelar desafío y volver.
    """
    await state.clear()

    await callback.message.edit_text(
        "❌ Desafío cancelado.\n\n"
        "<i>Puedes volver a intentarlo más tarde.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Continuar historia",
                    callback_data="story:continue"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📔 Ver diario",
                    callback_data="journal:main"
                )
            ]
        ])
    )
    await callback.answer()
