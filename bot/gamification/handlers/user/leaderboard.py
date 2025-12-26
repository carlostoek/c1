"""
Handler para visualización de leaderboard/rankings.

Funcionalidades:
- Ver top 10 usuarios por besitos
- Ver posición del usuario actual
- Rankings con medallas para los primeros lugares
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer

router = Router()

# Registrar middleware para inyectar session y gamification
router.callback_query.middleware(DatabaseMiddleware())


@router.callback_query(F.data == "user:leaderboard")
async def show_leaderboard(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra el leaderboard con el top 10 de usuarios.

    Incluye:
    - Top 10 usuarios por besitos
    - Medallas para los primeros 3 lugares
    - Posición del usuario actual
    - Besitos de cada usuario

    Args:
        callback: Callback query del usuario
        gamification: Container de servicios de gamificación
    """
    try:
        user_id = callback.from_user.id

        # Obtener top 10 usuarios
        top_users = await gamification.user_gamification.get_leaderboard(limit=10)

        # Obtener posición del usuario actual
        position_info = await gamification.user_gamification.get_leaderboard_position(user_id)

        text = "🏆 <b>Leaderboard - Top 10</b>\n\n"

        # Mostrar top 10
        if top_users:
            for idx, user_data in enumerate(top_users, 1):
                # Medallas para los primeros 3
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx}.")

                # Formatear nombre de usuario (si existe)
                user_id_display = user_data.get('user_id', 'Unknown')
                besitos = user_data.get('total_besitos', 0)

                text += f"{medal} <b>Usuario {user_id_display}</b>\n"
                text += f"    💰 {besitos:,} besitos\n"

            # Posición del usuario actual
            if position_info:
                besitos_rank = position_info.get('besitos_rank', 'N/A')
                user_besitos = position_info.get('total_besitos', 0)

                text += f"\n<b>━━━━━━━━━━━━━━━━━</b>\n"
                text += f"<b>Tu Posición:</b>\n"
                text += f"#{besitos_rank} • {user_besitos:,} besitos"
        else:
            text += "No hay datos de leaderboard disponibles."

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
