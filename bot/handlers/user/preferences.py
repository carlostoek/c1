"""
Handler for user notification preferences (/preferences).
"""
import logging
from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.start import user_router
from bot.services.notification_preferences import NotificationPreferencesService
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

PREFERENCES_CALLBACK_PREFIX = "prefs:toggle:"


async def get_preferences_text_and_keyboard(service: NotificationPreferencesService, user_id: int):
    """Helper to build the preferences message and keyboard."""
    prefs = await service.get_preferences(user_id)
    
    text = "⚙️ Tus Preferencias de Notificación\n\n"
    text += "Aquí puedes controlar qué tipo de mensajes recibes."

    def get_emoji(value: bool) -> str:
        return "✅" if value else "❌"

    keyboard_layout = [
        [{'text': f"{get_emoji(prefs.content_notifications)} Contenido Nuevo", 'callback_data': f"{PREFERENCES_CALLBACK_PREFIX}content_notifications"}],
        [{'text': f"{get_emoji(prefs.streak_reminders)} Recordatorios de Streak", 'callback_data': f"{PREFERENCES_CALLBACK_PREFIX}streak_reminders"}],
        [{'text': f"{get_emoji(prefs.offer_notifications)} Ofertas y Descuentos", 'callback_data': f"{PREFERENCES_CALLBACK_PREFIX}offer_notifications"}],
        [{'text': f"{get_emoji(prefs.reengagement_messages)} Mensajes de Re-enganche", 'callback_data': f"{PREFERENCES_CALLBACK_PREFIX}reengagement_messages"}],
        # TODO: Add buttons for quiet hours and timezone
        [{"text": "Done", "callback_data": "prefs:done"}]
    ]
    
    keyboard = create_inline_keyboard(keyboard_layout)
    return text, keyboard


@user_router.message(Command("preferences"))
async def cmd_preferences(message: Message, session: AsyncSession):
    """Displays the notification preferences menu."""
    user_id = message.from_user.id
    service = NotificationPreferencesService(session)
    
    text, keyboard = await get_preferences_text_and_keyboard(service, user_id)
    
    await message.answer(text, reply_markup=keyboard)


@user_router.callback_query(F.data.startswith(PREFERENCES_CALLBACK_PREFIX))
async def callback_toggle_preference(callback: CallbackQuery, session: AsyncSession):
    """Handles toggling a boolean notification preference."""
    user_id = callback.from_user.id
    pref_key = callback.data[len(PREFERENCES_CALLBACK_PREFIX):]
    
    service = NotificationPreferencesService(session)
    prefs = await service.get_preferences(user_id)
    
    # Toggle the value
    current_value = getattr(prefs, pref_key, False)
    await service.update_preferences(user_id, {pref_key: not current_value})
    
    # Re-generate the message and keyboard
    text, keyboard = await get_preferences_text_and_keyboard(service, user_id)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.debug(f"Error editing preferences message, probably unchanged: {e}")

    await callback.answer()


@user_router.callback_query(F.data == "prefs:done")
async def callback_prefs_done(callback: CallbackQuery):
    """Handles the 'Done' button, deleting the preferences message."""
    await callback.message.delete()
    await callback.answer("Preferencias guardadas.")
