"""
Handler de estadísticas del sistema de gamificación.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer

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
