"""
Onboarding Handler - Flujo de introducción para nuevos usuarios.

Responsabilidades:
- Enviar mensaje de bienvenida post-aprobación
- Guiar a través de 5 pasos de onboarding
- Detectar arquetipo basado en decisiones
- Otorgar besitos de bienvenida
- Desbloquear acceso a narrativa completa
"""

import json
import logging
from typing import Optional, List, Dict, Any

from aiogram import F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.narrative import narrative_router
from bot.narrative.services.container import NarrativeContainer
from bot.narrative.database.onboarding_models import OnboardingFragment
from bot.narrative.database.enums import ArchetypeType
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


# ============================================================
# FUNCIÓN PRINCIPAL: Enviar mensaje de bienvenida con onboarding
# ============================================================

async def send_onboarding_welcome(
    bot: Bot,
    user_id: int,
    session: AsyncSession
) -> bool:
    """
    Envía mensaje de bienvenida con onboarding después de aprobación Free.

    Esta función es llamada desde approve_ready_free_requests() cuando
    un usuario es aprobado en el canal Free.

    Args:
        bot: Instancia del bot de Telegram
        user_id: ID del usuario aprobado
        session: Sesión de BD

    Returns:
        True si se envió correctamente, False si hubo error
    """
    try:
        narrative = NarrativeContainer(session)

        # Verificar si ya completó onboarding (evitar duplicados)
        if await narrative.onboarding.has_completed_onboarding(user_id):
            logger.info(f"⏭️ Usuario {user_id} ya completó onboarding, saltando")
            return True

        # Otorgar besitos de bienvenida
        besitos_granted = await narrative.onboarding.grant_welcome_besitos(user_id, amount=30)

        # Crear keyboard con un solo botón
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📖 Comenzar Tutorial", callback_data="onboard:start")
        keyboard.adjust(1)

        # Enviar mensaje de bienvenida
        await bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 <b>¡Bienvenido al Canal Free!</b>\n\n"
                "Su solicitud ha sido aprobada y ya tiene acceso al contenido.\n\n"
                f"Como regalo de bienvenida, le otorgamos <b>30 besitos 💋</b>.\n\n"
                "Antes de explorar la narrativa completa, necesita completar "
                "un breve tutorial que le enseñará las mecánicas del sistema.\n\n"
                "<i>Duración: ~4 minutos</i>"
            ),
            parse_mode="HTML",
            reply_markup=keyboard.as_markup()
        )

        logger.info(f"✅ Mensaje de onboarding enviado a usuario {user_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Error enviando onboarding a usuario {user_id}: {e}")
        return False


# ============================================================
# CALLBACK: Iniciar onboarding
# ============================================================

@narrative_router.callback_query(F.data == "onboard:start")
async def callback_start_onboarding(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Inicia el flujo de onboarding.

    Muestra el primer fragmento de onboarding y marca el inicio.

    Args:
        callback: Callback del botón "Comenzar Tutorial"
        session: Sesión de BD
    """
    await callback.answer()
    user_id = callback.from_user.id

    logger.info(f"🎬 Usuario {user_id} inició onboarding")

    narrative = NarrativeContainer(session)

    # Verificar si ya completó
    if await narrative.onboarding.has_completed_onboarding(user_id):
        await callback.message.edit_text(
            "✅ <b>Tutorial Completado</b>\n\n"
            "Ya completaste el tutorial de introducción.\n"
            "Puedes explorar la narrativa completa.",
            parse_mode="HTML",
            reply_markup=_build_completed_keyboard()
        )
        return

    # Marcar onboarding iniciado
    await narrative.onboarding.mark_onboarding_started(user_id)

    # Mostrar paso 1
    await _show_onboarding_step(callback, session, step=1)


# ============================================================
# CALLBACK: Procesar decisión de onboarding
# ============================================================

@narrative_router.callback_query(F.data.startswith("onboard:decision:"))
async def callback_onboarding_decision(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Procesa una decisión tomada durante el onboarding.

    Formato callback_data: onboard:decision:{step}:{choice_index}

    Args:
        callback: Callback del botón de decisión
        session: Sesión de BD
    """
    await callback.answer()
    user_id = callback.from_user.id

    # Parsear callback data
    parts = callback.data.split(":")
    if len(parts) != 4:
        logger.error(f"❌ Formato inválido de callback: {callback.data}")
        return

    try:
        step = int(parts[2])
        choice_index = int(parts[3])
    except ValueError:
        logger.error(f"❌ Error parseando callback: {callback.data}")
        return

    logger.debug(f"📝 Usuario {user_id} decidió en paso {step}: opción {choice_index}")

    narrative = NarrativeContainer(session)

    # Obtener fragmento para determinar archetype_hint
    fragment = await narrative.onboarding.get_fragment(step)
    archetype_hint = None

    if fragment:
        decisions = narrative.onboarding.parse_decisions(fragment)
        if 0 <= choice_index < len(decisions):
            archetype_hint = decisions[choice_index].get("archetype_hint")

    # Registrar decisión
    await narrative.onboarding.record_decision(
        user_id=user_id,
        step=step,
        choice_index=choice_index,
        archetype_hint=archetype_hint
    )

    # Avanzar al siguiente paso
    next_step = step + 1

    if next_step <= 5:
        await _show_onboarding_step(callback, session, step=next_step)
    else:
        await _complete_onboarding(callback, session)


# ============================================================
# CALLBACK: Completar onboarding manualmente (paso 5)
# ============================================================

@narrative_router.callback_query(F.data == "onboard:complete")
async def callback_complete_onboarding(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Completa el onboarding manualmente (desde paso 5).

    Args:
        callback: Callback del botón "Comenzar Historia"
        session: Sesión de BD
    """
    await callback.answer()
    await _complete_onboarding(callback, session)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

async def _show_onboarding_step(
    callback: CallbackQuery,
    session: AsyncSession,
    step: int
):
    """
    Muestra un paso específico del onboarding.

    Args:
        callback: Callback de Telegram
        session: Sesión de BD
        step: Número de paso (1-5)
    """
    user_id = callback.from_user.id
    narrative = NarrativeContainer(session)

    # Actualizar paso actual
    await narrative.onboarding.update_step(user_id, step)

    # Obtener fragmento
    fragment = await narrative.onboarding.get_fragment(step)

    if not fragment:
        logger.error(f"❌ Fragmento de onboarding no encontrado para paso {step}")
        await callback.message.edit_text(
            "❌ <b>Error</b>\n\nNo se pudo cargar el contenido del tutorial.",
            parse_mode="HTML"
        )
        return

    # Formatear contenido
    content = fragment.content

    # Reemplazar variables dinámicas
    progress = await narrative.onboarding.get_or_create_progress(user_id)
    content = content.replace("{besitos}", str(progress.besitos_granted or 30))

    # Si es paso 4, mostrar arquetipo detectado
    if step == 4:
        archetype = await narrative.onboarding.get_detected_archetype(user_id)
        archetype_name = _get_archetype_display_name(archetype)
        archetype_desc = _get_archetype_description(archetype)
        content = content.replace("{archetype}", archetype_name)
        content = content.replace("{archetype_description}", archetype_desc)

    # Construir texto con speaker
    speaker_emoji = _get_speaker_emoji(fragment.speaker)
    text = f"{speaker_emoji} <b>{fragment.title}</b>\n\n{content}"

    # Construir keyboard de decisiones
    keyboard = _build_decisions_keyboard(fragment, step)

    # Mostrar fragmento
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def _complete_onboarding(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Completa el onboarding y muestra mensaje final.

    Args:
        callback: Callback de Telegram
        session: Sesión de BD
    """
    user_id = callback.from_user.id

    logger.info(f"🎉 Usuario {user_id} completó onboarding")

    narrative = NarrativeContainer(session)

    # Marcar como completado
    await narrative.onboarding.mark_onboarding_completed(user_id)

    # Obtener arquetipo detectado
    archetype = await narrative.onboarding.get_detected_archetype(user_id)
    archetype_name = _get_archetype_display_name(archetype)

    # Mensaje final
    text = (
        "✅ <b>¡Tutorial Completado!</b>\n\n"
        f"Su arquetipo detectado: <b>{archetype_name}</b>\n\n"
        "Ahora puede explorar la historia completa de Diana y Lucien.\n\n"
        "<i>Recuerde: cada decisión cuenta, cada camino es único.</i>"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=_build_completed_keyboard()
    )


def _build_decisions_keyboard(
    fragment: OnboardingFragment,
    step: int
) -> InlineKeyboardMarkup:
    """
    Construye keyboard con las decisiones del fragmento.

    Args:
        fragment: Fragmento de onboarding
        step: Paso actual

    Returns:
        InlineKeyboardMarkup con botones de decisión
    """
    keyboard = InlineKeyboardBuilder()

    if not fragment.decisions:
        # Si no hay decisiones, botón para continuar
        keyboard.button(
            text="Continuar ➡️",
            callback_data=f"onboard:decision:{step}:0"
        )
    else:
        try:
            decisions = json.loads(fragment.decisions)
            for i, decision in enumerate(decisions):
                text = decision.get("text", "Opción")

                # Si tiene callback personalizado (paso 5)
                custom_callback = decision.get("callback")
                if custom_callback:
                    keyboard.button(text=text, callback_data=custom_callback)
                else:
                    keyboard.button(
                        text=text,
                        callback_data=f"onboard:decision:{step}:{i}"
                    )
        except json.JSONDecodeError:
            keyboard.button(
                text="Continuar ➡️",
                callback_data=f"onboard:decision:{step}:0"
            )

    keyboard.adjust(1)
    return keyboard.as_markup()


def _build_completed_keyboard() -> InlineKeyboardMarkup:
    """
    Construye keyboard para onboarding completado.

    Returns:
        InlineKeyboardMarkup con opciones post-onboarding
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📖 Comenzar Historia", callback_data="narr:start")
    keyboard.button(text="📚 Ver Diario", callback_data="journal:view")
    keyboard.adjust(1)
    return keyboard.as_markup()


def _get_speaker_emoji(speaker: str) -> str:
    """Obtiene emoji para el speaker."""
    speakers = {
        "diana": "👩‍🦰",
        "lucien": "🧔",
        "narrator": "📜",
        "system": "⚙️"
    }
    return speakers.get(speaker.lower(), "💬")


def _get_archetype_display_name(archetype: Optional[ArchetypeType]) -> str:
    """Obtiene nombre de display para arquetipo."""
    if archetype is None or archetype == ArchetypeType.UNKNOWN:
        return "Explorador"

    names = {
        ArchetypeType.IMPULSIVE: "Impulsivo",
        ArchetypeType.CONTEMPLATIVE: "Contemplativo",
        ArchetypeType.SILENT: "Observador"
    }
    return names.get(archetype, "Explorador")


def _get_archetype_description(archetype: Optional[ArchetypeType]) -> str:
    """Obtiene descripción del arquetipo."""
    if archetype is None or archetype == ArchetypeType.UNKNOWN:
        return "Tu forma de tomar decisiones aún se está revelando."

    descriptions = {
        ArchetypeType.IMPULSIVE: (
            "Actúas con rapidez y confianza. "
            "Prefieres la acción sobre la reflexión, "
            "y no temes asumir riesgos."
        ),
        ArchetypeType.CONTEMPLATIVE: (
            "Analizas antes de actuar. "
            "Valoras la reflexión y consideras las consecuencias "
            "antes de tomar decisiones importantes."
        ),
        ArchetypeType.SILENT: (
            "Observas desde las sombras. "
            "Prefieres entender el panorama completo "
            "antes de revelar tus intenciones."
        )
    }
    return descriptions.get(archetype, "Tu forma de tomar decisiones es única.")
