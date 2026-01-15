"""
Profile Handlers - Menú de gamificación para usuarios.

Handlers:
- callback_show_profile: Muestra perfil con puntos, nivel, racha
- callback_daily_gift: Reclama regalo diario
- callback_show_missions: Lista misiones con progreso
- callback_show_badges: Lista badges desbloqueados
- callback_show_leaderboard: Muestra top usuarios
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.main import user_router
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


def create_profile_keyboard() -> InlineKeyboardMarkup:
    """Crea keyboard del perfil de gamificación."""
    builder = InlineKeyboardBuilder()

    # Sección principal
    builder.row(
        InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="user:daily_gift")
    )

    # Sección de info
    builder.row(
        InlineKeyboardButton(text="📋 Misiones", callback_data="user:missions"),
        InlineKeyboardButton(text="🏆 Badges", callback_data="user:badges")
    )

    builder.row(
        InlineKeyboardButton(text="🏅 Leaderboard", callback_data="user:leaderboard")
    )

    # Botón volver
    builder.row(
        InlineKeyboardButton(text="🔙 Volver al Inicio", callback_data="user:start")
    )

    return builder.as_markup()


@user_router.callback_query(F.data == "user:profile")
async def callback_show_profile(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el perfil de gamificación del usuario.

    Incluye:
    - Puntos actuales ("besitos")
    - Nivel actual
    - Racha actual
    - Próximo nivel
    """
    user_id = callback.from_user.id

    logger.debug(f"👤 User {user_id} viendo perfil")

    try:
        container = ServiceContainer(session, callback.bot)

        # Obtener puntos del usuario
        points = await container.points.get_balance(user_id)

        if points is None:
            # Usuario sin puntos aún
            text = (
                "🏆 <b>Mi Perfil</b>\n\n"
                "👋 ¡Bienvenido al sistema de gamificación!\n\n"
                "Comienza a reaccionar en los canales para ganar puntos.\n"
                "• Cada reacción: +1 punto\n"
                "• Regalo diario: +5 puntos\n"
                "• Rachas: multiplicador de puntos"
            )
        else:
            # Obtener nivel actual
            level = await container.levels.get_user_level(user_id)

            if level:
                level_info = f"{level.emoji} Nivel: {level.name}"
            else:
                level_info = "🔰 Sin nivel"

            # Calcular próximo nivel
            # TODO: Implementar en SPRINT 3
            next_level_info = "\n\n"

            # Obtener posición en leaderboard
            position = await container.points.get_user_leaderboard_position(user_id)
            if position:
                leaderboard_info = f"🏅 Posición: #{position}"
            else:
                leaderboard_info = "🏅 Sin posición aún"

            text = (
                f"🏆 <b>Mi Perfil</b>\n\n"
                f"💰 <b>Puntos:</b> {points.balance} besitos\n"
                f"📊 <b>Total Ganado:</b> {points.total_earned}\n"
                f"💸 <b>Total Gastado:</b> {points.total_spent}\n\n"
                f"{level_info}{next_level_info}"
                f"🔥 <b>Racha Actual:</b> {points.current_streak}\n"
                f"🏆 <b>Mejor Racha:</b> {points.max_streak}\n\n"
                f"{leaderboard_info}"
            )

        await callback.message.edit_text(
            text=text,
            reply_markup=create_profile_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error mostrando perfil: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar perfil", show_alert=True)


@user_router.callback_query(F.data == "user:daily_gift")
async def callback_daily_gift(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Procesa el reclamo del regalo diario.

    El usuario puede reclamar puntos adicionales cada 24 horas.
    """
    user_id = callback.from_user.id

    logger.debug(f"🎁 User {user_id} reclamando regalo diario")

    try:
        container = ServiceContainer(session, callback.bot)

        # Intentar reclamar regalo diario
        success, points, msg = await container.points.claim_daily_gift(user_id)

        if success:
            # Regalo otorgado
            text = (
                f"🎁 <b>Regalo Diario Reclamado</b>\n\n"
                f"¡Has recibido <b>+{points} puntos</b>!\n\n"
                f"Vuelve mañana para reclamar tu próximo regalo.\n"
                f"Balance actual: <b>{await _get_balance_display(container, user_id)}</b> besitos"
            )
            await callback.message.edit_text(
                text=text,
                reply_markup=create_profile_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer(msg)
        else:
            # No disponible aún
            await callback.answer(msg, show_alert=True)

    except Exception as e:
        logger.error(f"❌ Error en regalo diario: {e}", exc_info=True)
        await callback.answer("❌ Error al procesar regalo", show_alert=True)


@user_router.callback_query(F.data == "user:missions")
async def callback_show_missions(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra las misiones disponibles y su progreso.

    TODO: Implementar en SPRINT 4
    """
    user_id = callback.from_user.id

    logger.debug(f"📋 User {user_id} viendo misiones")

    text = (
        "📋 <b>Misiones</b>\n\n"
        "🚧 Las misiones estarán disponibles próximamente.\n\n"
        "Completa misiones para ganar recompensas extras:\n"
        "• Reaccionar N veces\n"
        "• Alcanzar racha de N\n"
        "• Reclamar regalo diario N veces"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver al Perfil", "callback_data": "user:profile"}]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data == "user:badges")
async def callback_show_badges(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra los badges desbloqueados por el usuario.

    TODO: Implementar display completo en SPRINT 3
    """
    user_id = callback.from_user.id

    logger.debug(f"🏆 User {user_id} viendo badges")

    try:
        container = ServiceContainer(session, callback.bot)

        # Obtener badges del usuario
        user_badges = await container.badges.get_user_badges(user_id)

        if not user_badges:
            text = (
                "🏆 <b>Mis Badges</b>\n\n"
                "Aún no has desbloqueado badges.\n\n"
                "¡Sigue participando para desbloquear tu primera insignia!"
            )
        else:
            # TODO: Implementar display completo en SPRINT 3
            badge_list = "\n".join([
                f"{ub.badge.emoji} {ub.badge.name} ({ub.badge.rarity.value})"
                for ub in user_badges
            ])
            text = (
                f"🏆 <b>Mis Badges</b>\n\n"
                f"Badges desbloqueados: {len(user_badges)}\n\n"
                f"{badge_list}"
            )

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver al Perfil", "callback_data": "user:profile"}]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error mostrando badges: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar badges", show_alert=True)


@user_router.callback_query(F.data == "user:leaderboard")
async def callback_show_leaderboard(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el leaderboard de usuarios con más puntos.
    """
    logger.debug("🏅 Mostrando leaderboard")

    try:
        container = ServiceContainer(session, callback.bot)

        # Obtener top 10
        leaderboard = await container.points.get_leaderboard(limit=10)

        if not leaderboard:
            text = (
                "🏅 <b>Leaderboard</b>\n\n"
                "Aún no hay usuarios en el ranking.\n\n"
                "¡Sé el primero en ganar puntos!"
            )
        else:
            # Formatear leaderboard
            lines = ["🏅 <b>Top 10 Usuarios</b>\n"]

            for position, points_obj in leaderboard:
                user = points_obj.user
                medal = ""

                if position == 1:
                    medal = "🥇 "
                elif position == 2:
                    medal = "🥈 "
                elif position == 3:
                    medal = "🥉 "
                else:
                    medal = f"{position}. "

                if user:
                    name = user.full_name or f"User{user.user_id}"
                else:
                    name = f"User{points_obj.user_id}"

                lines.append(f"{medal}<b>{name}</b>: {points_obj.balance} besitos 🔥{points_obj.current_streak}")

            text = "\n".join(lines)

        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver al Perfil", "callback_data": "user:profile"}]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error en leaderboard: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar leaderboard", show_alert=True)


# ===== HELPER =====

async def _get_balance_display(container: ServiceContainer, user_id: int) -> int:
    """Helper para obtener balance actual."""
    points = await container.points.get_balance(user_id)
    return points.balance if points else 0
