"""
Handlers de admin para sistema de arquetipos (FASE 3).

Comandos de administración para ver y gestionar arquetipos de usuario.

Author: Sistema de Gamificación
Version: 1.0
"""

import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.services.archetype_detection import ArchetypeDetectionService
from bot.gamification.services.behavior_tracking import BehaviorTrackingService

router = Router()
router.callback_query.filter(IsAdmin())
router.message.filter(IsAdmin())

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# COMANDOS DE ADMIN
# ========================================

@router.message(Command("archetype"))
async def cmd_archetype_info(message: Message, session):
    """
    Muestra información del arquetipo de un usuario.

    Usage: /archetype <user_id>
    """
    # Parse user_id from command args
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    if not args:
        await message.answer(
            "❌ Uso: /archetype <user_id>\n\n"
            "Ejemplo: /archetype 123456789"
        )
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await message.answer("❌ El ID de usuario debe ser un número.")
        return

    # Detect archetype
    detection_service = ArchetypeDetectionService(session)
    result = await detection_service.detect_archetype(user_id)

    # Format response
    text = f"🎭 <b>Arquetipo del Usuario {user_id}</b>\n\n"

    if result.archetype:
        emoji_map = {
            "EXPLORER": "🔍",
            "DIRECT": "⚡",
            "ROMANTIC": "💝",
            "ANALYTICAL": "🧠",
            "PERSISTENT": "🔄",
            "PATIENT": "⏳",
        }
        emoji = emoji_map.get(result.archetype, "❓")

        text += f"<b>Arquetipo:</b> {emoji} {result.archetype}\n"
        text += f"<b>Confianza:</b> {result.confidence * 100:.1f}%\n"
        text += f"<b>Interacciones:</b> {result.interactions_count}\n"
        text += f"<b>Detectado:</b> {result.detected_at or 'N/A'}\n\n"

        # Top scores
        text += "<b>Scores:</b>\n"
        sorted_scores = sorted(result.scores.items(), key=lambda x: x[1], reverse=True)
        for archetype, score in sorted_scores:
            text += f"  • {archetype}: {score:.1f}%\n"
    else:
        text += f"<b>Estado:</b> No detectado\n"
        text += f"<b>Razón:</b> {result.reason}\n"
        text += f"<b>Interacciones:</b> {result.interactions_count}\n\n"
        text += "<i>Se necesitan más interacciones para detectar el arquetipo.</i>"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("archetype_stats"))
async def cmd_archetype_stats(message: Message, session):
    """
    Muestra estadísticas de distribución de arquetipos.

    Usage: /archetype_stats
    """
    # TODO: Implement statistics query
    text = "📊 <b>Estadísticas de Arquetipos</b>\n\n"
    text += "<i>Funcionalidad pendiente de implementar.</i>"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("archetype_refresh"))
async def cmd_archetype_refresh(message: Message, session):
    """
    Fuerza re-evaluación del arquetipo de un usuario.

    Usage: /archetype_refresh <user_id>
    """
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    if not args:
        await message.answer(
            "❌ Uso: /archetype_refresh <user_id>\n\n"
            "Ejemplo: /archetype_refresh 123456789"
        )
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await message.answer("❌ El ID de usuario debe ser un número.")
        return

    # Force re-evaluation
    detection_service = ArchetypeDetectionService(session)
    result = await detection_service.force_reevaluation(user_id)

    # Format response
    text = f"🔄 <b>Re-evaluación forzada: {user_id}</b>\n\n"

    if result.archetype:
        text += f"<b>Arquetipo detectado:</b> {result.archetype}\n"
        text += f"<b>Confianza:</b> {result.confidence * 100:.1f}%\n"
        text += f"<b>Interacciones:</b> {result.interactions_count}\n"
    else:
        text += f"<b>Estado:</b> No detectado\n"
        text += f"<b>Razón:</b> {result.reason}\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("behavior_signals"))
async def cmd_behavior_signals(message: Message, session):
    """
    Muestra las señales de comportamiento de un usuario.

    Usage: /behavior_signals <user_id>
    """
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    if not args:
        await message.answer(
            "❌ Uso: /behavior_signals <user_id>\n\n"
            "Ejemplo: /behavior_signals 123456789"
        )
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await message.answer("❌ El ID de usuario debe ser un número.")
        return

    # Get signals
    tracking_service = BehaviorTrackingService(session)
    signals_dict = await tracking_service.get_signals_as_dict(user_id)

    if not signals_dict:
        await message.answer(
            f"❌ No hay señales de comportamiento para el usuario {user_id}.\n\n"
            f"<i>El usuario aún no ha interactuado con el sistema.</i>",
            parse_mode="HTML"
        )
        return

    # Format response
    text = f"📊 <b>Señales de Comportamiento: {user_id}</b>\n\n"

    # Exploration
    text += "🔍 <b>Exploración:</b>\n"
    text += f"  • Secciones visitadas: {signals_dict.get('content_sections_visited', 0)}\n"
    text += f"  • Tasa de completación: {signals_dict.get('content_completion_rate', 0):.1f}%\n"
    text += f"  • Easter eggs: {signals_dict.get('easter_eggs_found', 0)}\n"
    text += f"  • Revisitas: {signals_dict.get('revisits_old_content', 0)}\n\n"

    # Speed/Efficiency
    text += "⚡ <b>Velocidad/Eficiencia:</b>\n"
    text += f"  • Tiempo promedio de click: {signals_dict.get('avg_time_to_click', 0):.2f}s\n"
    text += f"  • Tiempo de decisión: {signals_dict.get('avg_decision_time', 0):.2f}s\n"
    text += f"  • Acciones por sesión: {signals_dict.get('actions_per_session', 0):.1f}\n"
    text += f"  • Navegación directa: {signals_dict.get('direct_navigation_ratio', 0):.1f}%\n\n"

    # Emotional
    text += "💝 <b>Emocional:</b>\n"
    text += f"  • Vistas emotivas: {signals_dict.get('emotional_content_views', 0)}\n"
    text += f"  • Historias personales: {signals_dict.get('personal_stories_accessed', 0)}\n"
    text += f"  • Revisitas emotivas: {signals_dict.get('repeat_emotional_visits', 0)}\n\n"

    # Persistence
    text += "🔄 <b>Persistencia:</b>\n"
    text += f"  • Retornos: {signals_dict.get('return_after_inactivity', 0)}\n"
    text += f"  • Reintentos: {signals_dict.get('retry_failed_actions', 0)}\n"
    text += f"  • Antigüedad: {signals_dict.get('account_age_days', 0)} días\n\n"

    # Patience
    text += "⏳ <b>Paciencia:</b>\n"
    text += f"  • Skip usados: {signals_dict.get('skip_actions_used', 0)}\n"
    text += f"  • Racha actual: {signals_dict.get('current_streak', 0)} días\n"
    text += f"  • Mejor racha: {signals_dict.get('best_streak', 0)} días\n\n"

    # General
    text += "📈 <b>General:</b>\n"
    text += f"  • Total interacciones: {signals_dict.get('total_interactions', 0)}\n"
    text += f"  • Total sesiones: {signals_dict.get('total_sessions', 0)}\n"

    await message.answer(text, parse_mode="HTML")


# ========================================
# CALLBACKS DEL MENÚ ADMIN
# ========================================

@router.callback_query(F.data == "gamif:admin:archetypes")
async def callback_archetypes_menu(callback: CallbackQuery, session):
    """Muestra el menú de administración de arquetipos."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Ver Estadísticas", callback_data="gamif:archetype:stats")],
        [InlineKeyboardButton(text="🔄 Ejecutar Detección Masiva", callback_data="gamif:archetype:mass_detect")],
        [InlineKeyboardButton(text="🏆 Ver Badges", callback_data="gamif:archetype:badges")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
    ])

    text = """🎭 <b>Administración de Arquetipos</b>

Gestiona el sistema de detección de arquetipos de usuario.

<b>Comandos disponibles:</b>
• <code>/archetype &lt;user_id&gt;</code> - Ver arquetipo de usuario
• <code>/archetype_stats</code> - Estadísticas globales
• <code>/archetype_refresh &lt;user_id&gt;</code> - Forzar re-evaluación
• <code>/behavior_signals &lt;user_id&gt;</code> - Ver señales de comportamiento"""

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:archetype:stats")
async def callback_archetype_stats(callback: CallbackQuery, session):
    """Muestra estadísticas de distribución de arquetipos."""
    # TODO: Implement actual statistics query
    text = """📊 <b>Estadísticas de Arquetipos</b>

<i>Funcionalidad pendiente de implementar.</i>

Esta sección mostrará:
• Distribución de arquetipos (% de usuarios)
• Arquetipo con mejor conversión a VIP
• Arquetipo con mejor retención
• Arquetipos por nivel"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:archetypes")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:archetype:badges")
async def callback_archetype_badges(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra los badges de arquetipo disponibles."""
    badges = await gamification.reward.get_all_rewards(reward_type="badge")

    # Filter archetype badges
    archetype_badges = []
    for badge in badges:
        if badge.badges and any(
            badge.name in ["El Explorador", "El Directo", "El Romántico",
                          "El Analítico", "El Persistente", "El Paciente"]
            for badge in [badge]
        ):
            archetype_badges.append(badge)

    text = "🏆 <b>Badges de Arquetipo</b>\n\n"

    if archetype_badges:
        for badge in archetype_badges:
            icon = badge.badges[0].icon if badge.badges else "🏅"
            text += f"{icon} <b>{badge.name}</b>\n"
            text += f"   {badge.description}\n\n"
    else:
        text += "<i>No hay badges de arquetipo creados aún.</i>\n\n"
        text += "<i>Ejecute: python scripts/seed_archetype_badges.py</i>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:archetypes")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:archetype:mass_detect")
async def callback_mass_detect(callback: CallbackQuery, session):
    """Ejecuta detección masiva de arquetipos para usuarios sin arquetipo."""
    # TODO: Implement mass detection
    text = """🔄 <b>Detección Masiva de Arquetipos</b>

<i>Funcionalidad pendiente de implementar.</i>

Esta sección ejecutará:
• Detección para usuarios sin arquetipo
• Re-evaluación para usuarios con baja confianza
• Actualización de badges"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:archetypes")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
