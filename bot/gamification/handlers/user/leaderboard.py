"""
Handlers del leaderboard para usuarios finales.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()


@router.callback_query(F.data == "user:leaderboard")
async def show_leaderboard(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra top 10 por besitos.
    
    Tabs:
    [💰 Besitos] [⭐ Nivel] [🔥 Racha]
    
    Incluye posición del usuario actual.
    """
    user_id = callback.from_user.id
    
    # Obtener top 10 por besitos
    top_users = await gamification.level.get_leaderboard(limit=10)
    
    # Obtener posición del usuario
    user_position = await gamification.user_gamification.get_leaderboard_position(user_id)
    
    text = "🏆 <b>Leaderboard - Top 10</b>\n\n"
    
    if top_users:
        for idx, user_data in enumerate(top_users, 1):
            user_info = user_data['user']
            total_besitos = user_data['total_besitos']
            
            # Asignar medallas para los primeros 3
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx:2d}.")
            
            # Mostrar solo los primeros 15 caracteres del nombre o el ID si no hay nombre
            display_name = (user_info.get('full_name', str(user_info.get('user_id', 'Anónimo'))) or str(user_info.get('user_id', 'Anónimo'))).strip()
            display_name = display_name[:15] + "..." if len(display_name) > 15 else display_name
            
            text += f"{medal} <code>{display_name}</code> - {total_besitos:,} besitos\n"
    else:
        text += "No hay usuarios en el leaderboard aún.\n\n"
    
    # Mostrar posición del usuario actual
    current_user_rank = user_position.get('besitos_rank', 'N/A')
    if current_user_rank != 'N/A':
        text += f"\n<b>Tu posición:</b> #{current_user_rank}"
        
        # También mostrar los besitos del usuario
        user_besitos = user_position.get('user_besitos', 0)
        text += f" con {user_besitos:,} besitos"
    else:
        text += f"\n<b>Tu posición:</b> No estás en el leaderboard"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Besitos", callback_data="leaderboard:besitos"),
            InlineKeyboardButton(text="⭐ Nivel", callback_data="leaderboard:level")
        ],
        [
            InlineKeyboardButton(text="🔥 Racha", callback_data="leaderboard:streak")
        ],
        [
            InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "leaderboard:besitos")
async def show_besitos_leaderboard(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra leaderboard por cantidad de besitos."""
    await show_leaderboard(callback, gamification)


@router.callback_query(F.data == "leaderboard:level")
async def show_level_leaderboard(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra leaderboard por nivel."""
    user_id = callback.from_user.id
    
    # Obtener top 10 por nivel
    top_users = await gamification.level.get_level_leaderboard(limit=10)
    
    # Obtener posición del usuario
    user_position = await gamification.user_gamification.get_leaderboard_position(user_id)
    
    text = "⭐ <b>Leaderboard - Nivel</b>\n\n"
    
    if top_users:
        for idx, user_data in enumerate(top_users, 1):
            user_info = user_data['user']
            level_info = user_data['level']
            
            # Asignar medallas para los primeros 3
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx:2d}.")
            
            # Mostrar solo los primeros 15 caracteres del nombre o el ID si no hay nombre
            display_name = (user_info.get('full_name', str(user_info.get('user_id', 'Anónimo'))) or str(user_info.get('user_id', 'Anónimo'))).strip()
            display_name = display_name[:15] + "..." if len(display_name) > 15 else display_name
            
            text += f"{medal} <code>{display_name}</code> - Nivel {level_info['order']} ({level_info['name']})\n"
    else:
        text += "No hay usuarios en el leaderboard aún.\n\n"
    
    # Información del usuario actual
    user_level_info = user_position.get('user_level', {})
    if user_level_info:
        user_level_order = user_level_info.get('order', 'N/A')
        user_level_name = user_level_info.get('name', 'Sin nivel')
        text += f"\n<b>Tu nivel:</b> #{user_level_order} ({user_level_name})"
    else:
        text += f"\n<b>Tu nivel:</b> No tienes nivel aún"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Besitos", callback_data="leaderboard:besitos"),
            InlineKeyboardButton(text="⭐ Nivel", callback_data="leaderboard:level")
        ],
        [
            InlineKeyboardButton(text="🔥 Racha", callback_data="leaderboard:streak")
        ],
        [
            InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "leaderboard:streak")
async def show_streak_leaderboard(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra leaderboard por racha (días consecutivos)."""
    user_id = callback.from_user.id
    
    # Obtener top 10 por racha
    top_users = await gamification.besito.get_streak_leaderboard(limit=10)
    
    # Obtener información de racha del usuario
    user_streak_info = await gamification.user_gamification.get_user_streak(user_id)
    
    text = "🔥 <b>Leaderboard - Racha</b>\n\n"
    
    if top_users:
        for idx, user_data in enumerate(top_users, 1):
            user_info = user_data['user']
            streak_days = user_data['streak_days']
            
            # Asignar medallas para los primeros 3
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx:2d}.")
            
            # Mostrar solo los primeros 15 caracteres del nombre o el ID si no hay nombre
            display_name = (user_info.get('full_name', str(user_info.get('user_id', 'Anónimo'))) or str(user_info.get('user_id', 'Anónimo'))).strip()
            display_name = display_name[:15] + "..." if len(display_name) > 15 else display_name
            
            text += f"{medal} <code>{display_name}</code> - {streak_days} días\n"
    else:
        text += "No hay usuarios en el leaderboard aún.\n\n"
    
    # Información de racha del usuario actual
    current_user_streak = user_streak_info.get('current_streak', 0)
    text += f"\n<b>Tu racha:</b> {current_user_streak} días consecutivos"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Besitos", callback_data="leaderboard:besitos"),
            InlineKeyboardButton(text="⭐ Nivel", callback_data="leaderboard:level")
        ],
        [
            InlineKeyboardButton(text="🔥 Racha", callback_data="leaderboard:streak")
        ],
        [
            InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()