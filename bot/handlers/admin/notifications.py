"""
Notification Handlers - Configuración de mensajes del bot.

Permite a los admins personalizar templates de notificaciones.
"""
import logging

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import NotificationTemplate
from bot.handlers.admin.main import admin_router
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@admin_router.callback_query(F.data == "admin:messages")
async def callback_messages_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Muestra menú de gestión de mensajes.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"💬 Usuario {callback.from_user.id} abrió menú de mensajes")

    # Obtener templates
    result = await session.execute(select(NotificationTemplate))
    templates = result.scalars().all()

    # Formatear mensaje
    text = "💬 <b>Gestión de Mensajes</b>\n\n"

    if templates:
        text += "Templates configurados:\n\n"
        for template in templates:
            status = "🟢" if template.active else "⚪"
            text += f"{status} <b>{template.name}</b>\n"
            text += f"   └─ Tipo: {template.type}\n\n"
    else:
        text += "<i>No hay templates personalizados aún.</i>\n\n"

    text += "Los mensajes se pueden personalizar desde aquí."

    # Keyboard
    buttons = []

    if templates:
        for template in templates:
            buttons.append(
                [
                    {
                        "text": f"✏️ {template.name[:20]}",
                        "callback_data": f"msg:edit:{template.id}",
                    }
                ]
            )

    buttons.append([{"text": "🔙 Volver a Configuración", "callback_data": "admin:config"}])

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML",
    )

    await callback.answer()


@admin_router.callback_query(F.data.startswith("msg:edit:"))
async def callback_edit_template(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Muestra template para edición.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    try:
        template_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Error al cargar template", show_alert=True)
        return

    # Obtener template
    result = await session.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        await callback.answer("❌ Template no encontrado", show_alert=True)
        return

    # Mostrar contenido actual
    content_preview = template.content[:300]
    if len(template.content) > 300:
        content_preview += "..."

    text = f"""✏️ <b>Editar Template: {template.name}</b>

<b>Tipo:</b> {template.type}
<b>Estado:</b> {'🟢 Activo' if template.active else '⚪ Inactivo'}

<b>Contenido actual:</b>
<code>{content_preview}</code>

<i>Para editar el contenido directamente, contacta al desarrollador.</i>"""

    # Keyboard
    buttons = [
        [
            {
                "text": "🔄 Activar" if not template.active else "🔄 Desactivar",
                "callback_data": f"msg:toggle:{template.id}",
            }
        ],
        [{"text": "🔙 Volver", "callback_data": "admin:messages"}],
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML",
    )

    await callback.answer()


@admin_router.callback_query(F.data.startswith("msg:toggle:"))
async def callback_toggle_template(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Activa/desactiva un template.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    try:
        template_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Error", show_alert=True)
        return

    # Obtener y cambiar estado
    result = await session.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        await callback.answer("❌ Template no encontrado", show_alert=True)
        return

    template.active = not template.active
    await session.commit()

    status = "activado" if template.active else "desactivado"
    await callback.answer(f"✅ Template {status}", show_alert=False)

    # Volver a mostrar template
    await callback_edit_template(callback, session)
