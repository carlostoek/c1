"""
Handler de estadísticas del sistema de gamificación.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.utils.keyboards import create_inline_keyboard

router = Router()
router.callback_query.filter(IsAdmin())

# Registrar middleware para inyectar session y gamification
router.callback_query.middleware(DatabaseMiddleware())


@router.callback_query(F.data == "gamif:admin:stats")
async def show_stats(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra estadísticas del sistema."""

    overview = await gamification.stats.get_system_overview()
    user_dist = await gamification.stats.get_user_distribution()
    mission_stats = await gamification.stats.get_mission_stats()
    engagement = await gamification.stats.get_engagement_stats()

    text = f"""📊 <b>Estadísticas del Sistema</b>

<b>👥 Usuarios</b>
• Total: {overview['total_users']:,}
• Activos (7d): {overview['active_users_7d']:,}
• Besitos promedio: {user_dist['avg_besitos']:,.0f}

<b>📋 Misiones</b>
• Configuradas: {overview['total_missions']}
• Completadas: {overview['missions_completed']:,}
• Tasa completitud: {mission_stats['completion_rate']:.1f}%

<b>🎁 Recompensas</b>
• Obtenidas: {overview['rewards_claimed']:,}

<b>📈 Engagement</b>
• Reacciones totales: {engagement['total_reactions']:,}
• Reacciones (7d): {engagement['reactions_7d']:,}
• Rachas activas: {engagement['active_streaks']}
• Racha más larga: {engagement['longest_streak']} días

<b>💰 Economía</b>
• Besitos distribuidos: {overview['total_besitos_distributed']:,}
"""

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:admin:economy")
async def show_economy_panel(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra panel de economía con top usuarios."""

    # Obtener top usuarios
    top_users = await gamification.stats.get_top_users_by_besitos(limit=10)

    # Obtener overview de economía
    overview = await gamification.stats.get_system_overview()

    text = f"""💰 <b>Panel de Economía</b>

<b>📊 Estadísticas Generales</b>
• Besitos totales distribuidos: {overview['total_besitos_distributed']:,}
• Usuarios en sistema: {overview['total_users']:,}

<b>🏆 Top 10 Usuarios por Besitos</b>
━━━━━━━━━━━━━━━━
"""

    if not top_users:
        text += "<i>No hay usuarios con besitos aún.</i>"
    else:
        for i, user in enumerate(top_users, 1):
            medal = ""
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"

            username = user['username']
            besitos = user['total_besitos']
            level = user['level']

            text += f"{medal} #{i}. <code>{username}</code>\n"
            text += f"   💰 {besitos:,} besitos • {level}\n\n"

    # Teclado con opciones
    keyboard = [
        [{"text": "🔄 Actualizar", "callback_data": "gamif:admin:economy"}],
        [{"text": "🔙 Volver", "callback_data": "gamif:menu"}]
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()
