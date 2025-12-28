"""
Story Handler - Navegación de la narrativa para usuarios.

Responsabilidades:
- Iniciar/continuar historia
- Mostrar fragmento actual con formato narrativo
- Generar botones de decisiones disponibles
- Verificar requisitos de acceso (VIP/Free)
"""

import logging
from typing import Optional, List, Tuple

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.narrative import narrative_router
from bot.narrative.database import NarrativeFragment, FragmentDecision, ChapterType
from bot.narrative.services.container import NarrativeContainer
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@narrative_router.callback_query(F.data == "narr:start")
async def callback_start_story(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Inicia o continúa la historia del usuario.

    Flujo:
    1. Obtener progreso del usuario
    2. Si tiene progreso → Continuar desde fragmento actual
    3. Si no tiene progreso → Iniciar con entry point del primer capítulo FREE
    4. Verificar requisitos de acceso
    5. Mostrar fragmento con botones de decisiones

    Args:
        callback: Callback del botón "📖 Historia"
        session: Sesión de BD (inyectada por middleware)
    """
    await callback.answer()
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name or "Usuario"

    logger.info(f"📖 Usuario {user_id} ({user_name}) inició navegación de historia")

    narrative = NarrativeContainer(session, callback.bot)
    container = ServiceContainer(session, callback.bot)

    # Verificar si completó onboarding (obligatorio para acceder a la historia)
    if not await narrative.onboarding.has_completed_onboarding(user_id):
        logger.info(f"🚫 Usuario {user_id} no ha completado onboarding, bloqueando acceso")
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📖 Iniciar Tutorial", callback_data="onboard:start")
        keyboard.button(text="🔙 Volver", callback_data="profile:back")
        keyboard.adjust(1)
        await callback.message.edit_text(
            "🔒 <b>Tutorial Pendiente</b>\n\n"
            "Debes completar el tutorial de introducción antes de acceder a la historia.\n\n"
            "<i>El tutorial te enseñará las mecánicas del sistema y te otorgará besitos de bienvenida.</i>",
            parse_mode="HTML",
            reply_markup=keyboard.as_markup()
        )
        return

    # Obtener o crear progreso
    progress = await narrative.progress.get_or_create_progress(user_id)

    # Determinar fragmento a mostrar
    if progress.current_fragment_key:
        # Continuar desde donde quedó
        fragment = await narrative.fragment.get_fragment(
            progress.current_fragment_key,
            load_decisions=True
        )
        if not fragment:
            # Error: fragmento no existe, resetear progreso
            logger.error(
                f"⚠️ Fragmento '{progress.current_fragment_key}' no existe para usuario {user_id}"
            )
            await callback.message.edit_text(
                "❌ <b>Error en el progreso</b>\n\n"
                "Tu progreso está desincronizado. Contacta al administrador.",
                parse_mode="HTML"
            )
            return
    else:
        # Primera vez: iniciar con entry point del primer capítulo FREE
        fragment = await narrative.fragment.get_entry_point_by_type(ChapterType.FREE)
        if not fragment:
            await callback.message.edit_text(
                "❌ <b>Historia no disponible</b>\n\n"
                "La historia aún no ha sido configurada. Vuelve más tarde.",
                parse_mode="HTML"
            )
            return

    # Verificar requisitos de acceso al capítulo
    can_access, reason = await _check_chapter_access(
        narrative,
        container,
        user_id,
        fragment.chapter_id
    )

    if not can_access:
        keyboard = create_inline_keyboard([[
            {"text": "🔙 Volver", "callback_data": "profile:back"}
        ]])
        await callback.message.edit_text(
            f"🔒 <b>Acceso Restringido</b>\n\n{reason}",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # Actualizar progreso (avanzar a este fragmento)
    await narrative.progress.advance_to(
        user_id,
        fragment.fragment_key,
        fragment.chapter_id
    )

    # Formatear y mostrar fragmento
    await _show_fragment(callback.message, narrative, user_id, fragment)


async def _check_chapter_access(
    narrative: NarrativeContainer,
    container: ServiceContainer,
    user_id: int,
    chapter_id: int
) -> Tuple[bool, str]:
    """
    Verifica si usuario puede acceder a un capítulo.

    Args:
        narrative: Container de narrativa
        container: Container de servicios
        user_id: ID del usuario
        chapter_id: ID del capítulo

    Returns:
        (can_access, reason)
    """
    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)
    if not chapter:
        return False, "Capítulo no encontrado."

    # Capítulos FREE: acceso para todos
    if chapter.chapter_type == ChapterType.FREE:
        return True, ""

    # Capítulos VIP: verificar suscripción
    if chapter.chapter_type == ChapterType.VIP:
        is_vip = await container.subscription.is_vip_active(user_id)
        if not is_vip:
            return False, (
                "Este capítulo es exclusivo para suscriptores VIP.\n\n"
                "Para acceder, canjea un token VIP o solicita acceso."
            )

    return True, ""


async def _show_fragment(
    message,
    narrative: NarrativeContainer,
    user_id: int,
    fragment: NarrativeFragment
):
    """
    Muestra un fragmento narrativo formateado.

    Args:
        message: Mensaje de Telegram para editar
        narrative: Container de narrativa
        user_id: ID del usuario
        fragment: Fragmento a mostrar
    """
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


async def _build_decisions_keyboard(
    decisions: List[FragmentDecision]
) -> InlineKeyboardMarkup:
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
