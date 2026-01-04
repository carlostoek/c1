"""
Handler de historia narrativa para usuarios.

Gestiona la experiencia de lectura inmersiva con:
- Contenido dinámico por contexto (variantes)
- Tracking de visitas y tiempo
- Cooldowns narrativos
- Decisiones del usuario
- Otorgamiento de pistas
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.services.container import NarrativeContainer
from bot.narrative.database.enums import CooldownType
from bot.narrative.config import NarrativeConfig

logger = logging.getLogger(__name__)

story_router = Router(name="narrative_story")


# ========================================
# HELPERS
# ========================================

async def build_full_user_context(
    container: NarrativeContainer,
    user_id: int,
    fragment_key: str
) -> Dict[str, Any]:
    """
    Construye el contexto completo del usuario para evaluación de variantes.

    Args:
        container: Contenedor de servicios narrativos
        user_id: ID del usuario
        fragment_key: Key del fragmento actual

    Returns:
        Contexto completo del usuario
    """
    context = {
        "user_id": user_id,
        "visit_count": 0,
        "clues": [],
        "archetype": "unknown",
        "decisions": [],
        "completed_chapters": [],
        "started_at": None,
    }

    # Obtener progreso del usuario
    progress = await container.progress.get_or_create_progress(user_id)
    if progress:
        context["archetype"] = progress.detected_archetype.value if progress.detected_archetype else "unknown"
        # Nota: started_at no está en el modelo actual, sería la primera interacción

    # Obtener conteo de visitas a este fragmento
    visit_count = await container.engagement.get_visit_count(user_id, fragment_key)
    context["visit_count"] = visit_count

    # Obtener pistas del usuario
    user_clues = await container.clue.get_user_clues(user_id)
    context["clues"] = [clue.get("slug", "") for clue in user_clues]

    # Obtener capítulos completados
    completed = await container.engagement.get_completed_chapters(user_id)
    context["completed_chapters"] = [c.chapter_slug for c in completed]

    # Obtener decisiones tomadas (fragment_keys donde tomó decisiones)
    # Por ahora usamos has_visited_fragment como proxy
    # TODO: Mejorar con tabla específica de decisiones

    return context


def format_fragment_content(
    fragment_data: Dict[str, Any],
    is_return_visit: bool = False
) -> str:
    """
    Formatea el contenido del fragmento para mostrar.

    Args:
        fragment_data: Datos del fragmento (con variante aplicada)
        is_return_visit: Si es visita de retorno

    Returns:
        Contenido formateado en HTML
    """
    speaker_emojis = {
        "diana": "🌸",
        "lucien": "🎩",
        "narrator": "📖",
        "system": "💬"
    }
    speaker = fragment_data.get("speaker", "narrator")
    emoji = speaker_emojis.get(speaker.lower(), "💬")

    # Construir mensaje
    message = f"{emoji} <b>{speaker.title()}</b>\n\n"
    message += fragment_data.get("content", "")

    # Agregar visual hint si existe
    visual_hint = fragment_data.get("visual_hint")
    if visual_hint:
        message += f"\n\n<i>{visual_hint}</i>"

    # Indicador de variante (solo en desarrollo/debug)
    variant = fragment_data.get("variant_applied")
    if variant:
        message += f"\n\n<code>[Variante: {variant}]</code>"

    return message


def build_decisions_keyboard(
    decisions: List[Any],
    additional_decisions: Optional[List[Dict]] = None,
    show_navigation: bool = True,
    fragment_key: str = ""
) -> InlineKeyboardMarkup:
    """
    Construye teclado con decisiones disponibles.

    Args:
        decisions: Lista de FragmentDecision
        additional_decisions: Decisiones adicionales de variante
        show_navigation: Si mostrar botones de navegación
        fragment_key: Key del fragmento actual

    Returns:
        Teclado inline
    """
    buttons = []

    # Decisiones normales del fragmento
    for decision in decisions:
        if decision.is_active:
            text = decision.button_text
            if decision.button_emoji:
                text = f"{decision.button_emoji} {text}"
            if decision.besitos_cost > 0:
                text = f"{text} ({decision.besitos_cost} 💋)"

            buttons.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"story:decide:{decision.id}"
                )
            ])

    # Decisiones adicionales de variante
    if additional_decisions:
        for add_dec in additional_decisions:
            text = add_dec.get("text", "Opción")
            target = add_dec.get("target", "")
            emoji = add_dec.get("emoji", "")
            if emoji:
                text = f"{emoji} {text}"

            buttons.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"story:goto:{target}"
                )
            ])

    # Botones de navegación
    if show_navigation:
        nav_row = []
        nav_row.append(
            InlineKeyboardButton(
                text="📔 Diario",
                callback_data="story:journal"
            )
        )
        nav_row.append(
            InlineKeyboardButton(
                text="🎒 Mochila",
                callback_data="backpack:main"
            )
        )
        if nav_row:
            buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========================================
# HANDLERS
# ========================================

@story_router.message(Command("historia", "story"))
async def cmd_start_story(message: Message, session: AsyncSession):
    """
    Comando para iniciar o continuar la historia.
    """
    user_id = message.from_user.id
    container = NarrativeContainer(session)

    # Obtener progreso del usuario
    progress = await container.progress.get_or_create_progress(user_id)

    if progress.current_fragment_key:
        # Tiene progreso - mostrar fragmento actual
        await show_fragment(
            message=message,
            session=session,
            fragment_key=progress.current_fragment_key,
            user_id=user_id,
            is_new_message=True
        )
    else:
        # No tiene progreso - mostrar bienvenida y opciones
        await message.answer(
            "📖 <b>Bienvenido a la Historia</b>\n\n"
            "Aún no has comenzado tu viaje narrativo.\n"
            "Selecciona un capítulo para empezar:",
            parse_mode="HTML",
            reply_markup=await _build_chapter_selection_keyboard(container)
        )


@story_router.callback_query(F.data == "narr:start")
async def callback_start_story(callback: CallbackQuery, session: AsyncSession):
    """
    Callback para iniciar o continuar la historia desde botón del menú.
    Igual que cmd_start_story pero edita el mensaje en lugar de enviar uno nuevo.
    """
    await callback.answer()
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Obtener progreso del usuario
    progress = await container.progress.get_or_create_progress(user_id)

    if progress.current_fragment_key:
        # Tiene progreso - mostrar fragmento actual
        await show_fragment(
            message=callback.message,
            session=session,
            fragment_key=progress.current_fragment_key,
            user_id=user_id,
            is_new_message=False
        )
    else:
        # No tiene progreso - mostrar bienvenida y opciones
        await callback.message.edit_text(
            "📖 <b>Bienvenido a la Historia</b>\n\n"
            "Aún no has comenzado tu viaje narrativo.\n"
            "Selecciona un capítulo para empezar:",
            parse_mode="HTML",
            reply_markup=await _build_chapter_selection_keyboard(container)
        )


@story_router.callback_query(F.data.startswith("story:chapter:"))
async def callback_select_chapter(callback: CallbackQuery, session: AsyncSession):
    """
    Seleccionar capítulo para empezar.
    """
    chapter_slug = callback.data.split(":")[2]
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Obtener capítulo
    chapter = await container.fragment.get_chapter_by_slug(chapter_slug)
    if not chapter:
        await callback.answer("Capítulo no encontrado", show_alert=True)
        return

    # Obtener entry point del capítulo
    entry_point = await container.fragment.get_entry_point(chapter.id)
    if not entry_point:
        await callback.answer("Este capítulo no tiene fragmento inicial", show_alert=True)
        return

    # Avanzar usuario al entry point
    await container.progress.advance_to(
        user_id=user_id,
        fragment_key=entry_point.fragment_key,
        chapter_id=chapter.id
    )

    # Mostrar fragmento inicial
    await show_fragment(
        message=callback.message,
        session=session,
        fragment_key=entry_point.fragment_key,
        user_id=user_id,
        is_new_message=False
    )
    await callback.answer()


@story_router.callback_query(F.data.startswith("story:decide:"))
async def callback_process_decision(callback: CallbackQuery, session: AsyncSession):
    """
    Procesar decisión del usuario.
    """
    decision_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Verificar límite diario de decisiones
    can_continue, used, max_limit = await container.engagement.check_daily_limit(
        user_id, "decisions"
    )
    if not can_continue:
        await callback.answer(
            f"📊 Has alcanzado tu límite diario de decisiones ({max_limit}). "
            "Vuelve mañana para continuar.",
            show_alert=True
        )
        return

    # Verificar cooldown de decisiones
    can_decide, remaining = await container.cooldown.can_take_decision(user_id)
    if not can_decide:
        cooldown_msg = NarrativeConfig.get_cooldown_message("decision")
        await callback.answer(
            f"⏳ {cooldown_msg}\n({remaining} segundos)",
            show_alert=True
        )
        return

    # Procesar la decisión
    success, message_text, next_fragment = await container.decision.process_decision(
        user_id=user_id,
        decision_id=decision_id
    )

    if not success:
        await callback.answer(message_text, show_alert=True)
        return

    # Incrementar contador diario de decisiones
    await container.engagement.increment_decisions_made(user_id)

    # Establecer cooldown de decisión usando configuración
    cooldown_msg = NarrativeConfig.get_cooldown_message("decision")
    await container.cooldown.set_decision_cooldown(
        user_id=user_id,
        duration_seconds=NarrativeConfig.DECISION_COOLDOWN_SECONDS,
        message=cooldown_msg
    )

    # Mostrar siguiente fragmento
    await show_fragment(
        message=callback.message,
        session=session,
        fragment_key=next_fragment.fragment_key,
        user_id=user_id,
        is_new_message=False
    )
    await callback.answer()


@story_router.callback_query(F.data.startswith("story:goto:"))
async def callback_goto_fragment(callback: CallbackQuery, session: AsyncSession):
    """
    Ir directamente a un fragmento (desde variantes o navegación).
    """
    fragment_key = callback.data.split(":")[2]
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Verificar cooldown del fragmento
    can_access, remaining, cd_message = await container.cooldown.can_access_fragment(
        user_id=user_id,
        fragment_key=fragment_key
    )

    if not can_access:
        await callback.answer(
            f"⏳ {cd_message}\n({remaining} segundos restantes)",
            show_alert=True
        )
        return

    # Verificar requisitos del fragmento
    fragment = await container.fragment.get_fragment(
        fragment_key,
        load_requirements=True
    )
    if not fragment:
        await callback.answer("Fragmento no encontrado", show_alert=True)
        return

    # Verificar requisitos si tiene
    if fragment.requirements:
        is_met, block_message = await container.requirements.check_requirements(
            user_id=user_id,
            fragment=fragment
        )
        if not is_met:
            await callback.answer(f"🔒 {block_message}", show_alert=True)
            return

    # Actualizar progreso
    await container.progress.advance_to(
        user_id=user_id,
        fragment_key=fragment_key,
        chapter_id=fragment.chapter_id
    )

    # Mostrar fragmento
    await show_fragment(
        message=callback.message,
        session=session,
        fragment_key=fragment_key,
        user_id=user_id,
        is_new_message=False
    )
    await callback.answer()


@story_router.callback_query(F.data == "story:journal")
async def callback_show_journal(callback: CallbackQuery, session: AsyncSession):
    """
    Mostrar diario de viaje (implementación básica).
    """
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Obtener estadísticas del usuario
    stats = await container.engagement.get_user_stats(user_id)

    # Construir mensaje de diario
    message = "📔 <b>Tu Diario de Viaje</b>\n\n"

    if stats:
        message += f"📊 <b>Estadísticas</b>\n"
        message += f"• Fragmentos visitados: {stats.get('total_visits', 0)}\n"
        message += f"• Capítulos completados: {stats.get('chapters_completed', 0)}\n"
        message += f"• Pistas encontradas: {stats.get('clues_count', 0)}\n\n"

    # Obtener pistas
    clues = await container.clue.get_user_clues(user_id)
    if clues:
        message += "🔍 <b>Pistas Encontradas</b>\n"
        for clue in clues[:5]:  # Mostrar solo las 5 primeras
            icon = clue.get("icon", "📌")
            name = clue.get("name", "Pista")
            message += f"• {icon} {name}\n"

        if len(clues) > 5:
            message += f"<i>...y {len(clues) - 5} más en tu mochila</i>\n"

    message += "\n💡 <i>Usa la mochila para ver todas tus pistas</i>"

    # Botón para volver
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Volver a la historia",
                callback_data="story:continue"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎒 Ver mochila",
                callback_data="backpack:main"
            )
        ]
    ])

    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@story_router.callback_query(F.data == "story:continue")
async def callback_continue_story(callback: CallbackQuery, session: AsyncSession):
    """
    Continuar la historia desde el último punto.
    """
    user_id = callback.from_user.id
    container = NarrativeContainer(session)

    # Obtener progreso
    progress = await container.progress.get_or_create_progress(user_id)

    if not progress.current_fragment_key:
        await callback.answer("No tienes progreso guardado", show_alert=True)
        return

    await show_fragment(
        message=callback.message,
        session=session,
        fragment_key=progress.current_fragment_key,
        user_id=user_id,
        is_new_message=False
    )
    await callback.answer()


# ========================================
# FUNCIÓN PRINCIPAL DE MOSTRAR FRAGMENTO
# ========================================

async def show_fragment(
    message: Message,
    session: AsyncSession,
    fragment_key: str,
    user_id: int,
    is_new_message: bool = False
):
    """
    Muestra un fragmento narrativo con variantes y tracking.

    Args:
        message: Mensaje de Telegram (para responder o editar)
        session: Sesión de base de datos
        fragment_key: Key del fragmento a mostrar
        user_id: ID del usuario
        is_new_message: Si enviar como nuevo mensaje o editar
    """
    container = NarrativeContainer(session)

    # 0. Verificar límite diario de fragmentos
    can_continue, used, max_limit = await container.engagement.check_daily_limit(
        user_id, "fragments"
    )
    if not can_continue:
        limit_message = (
            f"📊 <b>Límite Diario Alcanzado</b>\n\n"
            f"Has explorado {max_limit} fragmentos hoy.\n"
            f"Vuelve mañana para continuar tu viaje.\n\n"
            f"<i>A veces pausar es parte de la historia...</i>"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📔 Ver Diario", callback_data="journal:main")],
            [InlineKeyboardButton(text="🎒 Ver Mochila", callback_data="backpack:main")]
        ])
        if is_new_message:
            await message.answer(limit_message, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.edit_text(limit_message, parse_mode="HTML", reply_markup=keyboard)
        return

    # 1. Construir contexto del usuario
    user_context = await build_full_user_context(container, user_id, fragment_key)

    # 2. Obtener fragmento con variante aplicada
    fragment_data = await container.variant.get_fragment_with_variant(
        fragment_key=fragment_key,
        user_context=user_context
    )

    if not fragment_data:
        error_message = "❌ Fragmento no encontrado"
        if is_new_message:
            await message.answer(error_message)
        else:
            await message.edit_text(error_message)
        return

    # 3. Registrar visita e incrementar contador diario
    is_first_visit = user_context.get("visit_count", 0) == 0
    await container.engagement.record_visit(user_id, fragment_key)
    await container.engagement.increment_fragments_viewed(user_id)

    # 4. Verificar si el fragmento otorga pista
    fragment = await container.fragment.get_fragment(fragment_key)
    if fragment and fragment.extra_metadata:
        try:
            if fragment.extra_metadata.get("grants_clue"):
                clue_slug = fragment.extra_metadata.get("grants_clue")
                await container.clue.grant_clue_from_fragment(
                    user_id=user_id,
                    clue_slug=clue_slug,
                    fragment_key=fragment_key
                )
        except Exception as e:
            logger.warning(f"Error procesando extra_metadata de fragmento: {e}")

    # 5. Obtener decisiones disponibles
    decisions = await container.decision.get_available_decisions(fragment_key, user_id)

    # 6. Formatear contenido
    content = format_fragment_content(
        fragment_data,
        is_return_visit=not is_first_visit
    )

    # 7. Construir teclado
    keyboard = build_decisions_keyboard(
        decisions=decisions,
        additional_decisions=fragment_data.get("additional_decisions"),
        show_navigation=True,
        fragment_key=fragment_key
    )

    # 8. Enviar o editar mensaje
    if is_new_message:
        await message.answer(
            content,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        try:
            await message.edit_text(
                content,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception as e:
            # Si falla editar, enviar nuevo mensaje
            logger.warning(f"Error editando mensaje: {e}")
            await message.answer(
                content,
                parse_mode="HTML",
                reply_markup=keyboard
            )


async def _build_chapter_selection_keyboard(
    container: NarrativeContainer
) -> InlineKeyboardMarkup:
    """
    Construye teclado de selección de capítulos.
    """
    from bot.narrative.database.enums import ChapterType

    buttons = []

    # Obtener capítulos FREE activos
    chapters = await container.chapter.get_chapters_by_type(ChapterType.FREE)

    for chapter in chapters[:5]:  # Máximo 5 capítulos
        buttons.append([
            InlineKeyboardButton(
                text=f"📖 {chapter.name}",
                callback_data=f"story:chapter:{chapter.slug}"
            )
        ])

    if not buttons:
        buttons.append([
            InlineKeyboardButton(
                text="⚠️ No hay capítulos disponibles",
                callback_data="story:no_chapters"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
