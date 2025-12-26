"""
Handler para sistema de regalo diario.

Permite a los usuarios:
- Reclamar su regalo diario de besitos
- Ver su racha actual de días consecutivos
- Ver cuándo podrán reclamar nuevamente
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import logging

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer

router = Router()
logger = logging.getLogger(__name__)

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


@router.message(Command("gift"))
@router.message(Command("regalo"))
async def cmd_daily_gift(message: Message, gamification: GamificationContainer):
    """
    Comando para reclamar regalo diario.

    Accesible mediante:
    - /gift
    - /regalo

    Args:
        message: Mensaje del usuario
        gamification: Container de servicios de gamificación
    """
    user_id = message.from_user.id

    try:
        # Intentar reclamar el regalo
        success, msg, details = await gamification.daily_gift.claim_daily_gift(user_id)

        if success:
            # Éxito - Mostrar detalles con botón de perfil
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Ver Perfil", callback_data="user:profile")]
            ])
            await message.answer(msg, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Error o ya reclamó hoy
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Volver", callback_data="user:profile")]
            ])
            await message.answer(msg, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in cmd_daily_gift for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Error al procesar el regalo diario. Intenta nuevamente.",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:daily_gift")
async def callback_daily_gift(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Callback para mostrar estado y reclamar regalo diario.

    Args:
        callback: Callback query del usuario
        gamification: Container de servicios de gamificación
    """
    user_id = callback.from_user.id

    try:
        # Obtener estado del regalo diario
        status = await gamification.daily_gift.get_daily_gift_status(user_id)

        if not status['system_enabled']:
            # Sistema desactivado
            await callback.answer(
                "❌ El sistema de regalo diario está desactivado actualmente.",
                show_alert=True
            )
            return

        if status['can_claim']:
            # Puede reclamar - Mostrar botón para reclamar
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Reclamar Regalo", callback_data="user:claim_daily_gift")],
                [InlineKeyboardButton(text="🔙 Volver", callback_data="user:profile")]
            ])

            text = (
                "🎁 <b>Regalo Diario Disponible</b>\n\n"
                f"💋 Recibirás: <b>{status['besitos_amount']} besitos</b>\n"
                f"🔥 Racha actual: <b>{status['current_streak']} día(s)</b>\n"
                f"🏆 Récord: <b>{status['longest_streak']} día(s)</b>\n"
                f"📊 Total reclamados: <b>{status['total_claims']}</b>\n\n"
                "👆 Presiona el botón para reclamar tu regalo"
            )

        else:
            # Ya reclamó hoy
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Volver", callback_data="user:profile")]
            ])

            text = (
                "✅ <b>Regalo Diario Reclamado</b>\n\n"
                f"🔥 Racha actual: <b>{status['current_streak']} día(s)</b>\n"
                f"🏆 Récord: <b>{status['longest_streak']} día(s)</b>\n"
                f"📊 Total reclamados: <b>{status['total_claims']}</b>\n\n"
                f"⏰ Próximo regalo: <b>{status.get('next_claim_time', 'mañana')}</b>"
            )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in callback_daily_gift for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar el regalo diario.",
            show_alert=True
        )


@router.callback_query(F.data == "user:claim_daily_gift")
async def callback_claim_daily_gift(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Callback para reclamar el regalo diario.

    Args:
        callback: Callback query del usuario
        gamification: Container de servicios de gamificación
    """
    user_id = callback.from_user.id

    try:
        # Reclamar el regalo
        success, msg, details = await gamification.daily_gift.claim_daily_gift(user_id)

        if success:
            # Éxito - Actualizar mensaje con detalles
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Ver Perfil", callback_data="user:profile")],
                [InlineKeyboardButton(text="🔙 Volver", callback_data="user:daily_gift")]
            ])

            text = (
                "🎉 <b>¡Regalo Diario Reclamado!</b>\n\n"
                f"💋 +{details['besitos_earned']} besitos\n"
                f"🔥 Racha: {details['current_streak']} día(s)\n"
                f"🏆 Récord: {details['longest_streak']} día(s)\n"
                f"📊 Total reclamados: {details['total_claims']}"
            )

            if details['current_streak'] == details['longest_streak'] and details['current_streak'] > 1:
                text += "\n\n🎊 ¡Nuevo récord personal!"

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer("✅ Regalo reclamado exitosamente", show_alert=False)

        else:
            # Error o ya reclamó
            await callback.answer(msg, show_alert=True)

    except Exception as e:
        logger.error(f"Error in callback_claim_daily_gift for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al reclamar el regalo. Intenta nuevamente.",
            show_alert=True
        )
