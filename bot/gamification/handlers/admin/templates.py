"""
Handler de plantillas de configuración predefinidas.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.gamification.utils.templates import list_templates, apply_template

router = Router()
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "gamif:missions:templates")
async def show_templates(callback: CallbackQuery):
    """Muestra plantillas disponibles."""
    templates = list_templates()

    keyboard_buttons = []
    for template in templates:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{template['name']} ({template['missions_count']} misiones)",
                callback_data=f"gamif:template:apply:{template['key']}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:missions")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        "📄 <b>Plantillas Predefinidas</b>\n\n"
        "Selecciona una plantilla para aplicar:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:template:apply:"))
async def apply_template_handler(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Aplica plantilla seleccionada."""
    template_name = callback.data.split(":")[-1]

    await callback.message.edit_text("⚙️ Aplicando plantilla...")

    try:
        result = await apply_template(
            template_name,
            session,
            created_by=callback.from_user.id
        )

        await callback.message.edit_text(
            result['summary'],
            parse_mode="HTML"
        )

    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {e}")

    await callback.answer()
