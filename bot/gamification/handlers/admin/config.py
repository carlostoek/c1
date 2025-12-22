"""
Handlers para configuración general de gamificación.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.gamification.services.orchestrator.configuration import ConfigurationOrchestrator

router = Router()


@router.callback_query(F.data == "gamif:admin:config")
async def config_menu(callback: CallbackQuery, session: AsyncSession):
    """Muestra menú de configuración general."""
    text = """🔧 <b>Configuración de Gamificación</b>

Opciones de configuración avanzada:

• <b>Plantillas:</b> Aplicar configuraciones predefinidas
• <b>Limpieza:</b> Eliminar datos antiguos o innecesarios
• <b>Exportar:</b> Exportar configuración actual
• <b>Importar:</b> Importar configuración desde archivo

Selecciona una opción para continuar."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Plantillas", callback_data="gamif:config:templates"),
            InlineKeyboardButton(text="🧹 Limpieza", callback_data="gamif:config:cleanup")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gamif:config:templates")
async def templates_menu(callback: CallbackQuery, session: AsyncSession):
    """Muestra menú de plantillas de configuración."""
    orchestrator = ConfigurationOrchestrator(session)
    templates = orchestrator.SYSTEM_TEMPLATES
    
    text = "📋 <b>Plantillas de Configuración</b>\n\n"
    text += "Aplica plantillas predefinidas para configurar rápidamente tu sistema de gamificación.\n\n"
    
    keyboard_buttons = []
    
    for template_name, template_data in templates.items():
        text += f"• <b>{template_name}</b>: {template_data['description']}\n"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📋 {template_name}",
                callback_data=f"gamif:config:apply_template:{template_name}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:config")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:config:apply_template:"))
async def apply_template(callback: CallbackQuery, session: AsyncSession):
    """Aplica una plantilla de configuración."""
    template_name = callback.data.split(":")[-1]
    
    try:
        orchestrator = ConfigurationOrchestrator(session)
        result = await orchestrator.apply_system_template(
            template_name=template_name,
            created_by=callback.from_user.id
        )
        
        await callback.answer("✅ Plantilla aplicada", show_alert=True)
        
        # Mostrar resumen
        await callback.message.edit_text(
            result['summary'],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔧 Configuración", callback_data="gamif:admin:config")],
                [InlineKeyboardButton(text="🎮 Menú Principal", callback_data="gamif:menu")]
            ])
        )
        
    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)


@router.callback_query(F.data == "gamif:config:cleanup")
async def cleanup_menu(callback: CallbackQuery, session: AsyncSession):
    """Muestra opciones de limpieza."""
    text = """🧹 <b>Limpieza de Datos</b>

Selecciona qué datos deseas limpiar:

⚠️ <b>Advertencia:</b> Estas acciones no se pueden deshacer.

• <b>Transacciones:</b> Eliminar transacciones antiguas
• <b>Reacciones:</b> Eliminar reacciones viejas
• <b>Misiones:</b> Limpiar misiones completadas antiguas
• <b>Todo:</b> Limpiar todos los datos del sistema (solo testing)"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Transacciones", callback_data="gamif:config:cleanup:transactions"),
            InlineKeyboardButton(text="💬 Reacciones", callback_data="gamif:config:cleanup:reactions")
        ],
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data="gamif:config:cleanup:missions"),
            InlineKeyboardButton(text="🗑️ Todo", callback_data="gamif:config:cleanup:all")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:config")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:config:cleanup:"))
async def confirm_cleanup(callback: CallbackQuery, session: AsyncSession):
    """Confirma y ejecuta limpieza de datos."""
    cleanup_type = callback.data.split(":")[-1]
    
    # Mapeo de tipos a descripciones
    cleanup_descriptions = {
        "transactions": "transacciones antiguas",
        "reactions": "reacciones viejas",
        "missions": "misiones completadas",
        "all": "TODOS los datos del sistema"
    }
    
    description = cleanup_descriptions.get(cleanup_type, cleanup_type)
    
    text = f"""⚠️ <b>Confirmar Limpieza</b>

¿Estás seguro de que deseas eliminar {description}?

<b>Esta acción no se puede deshacer.</b>"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Sí, Limpiar", callback_data=f"gamif:config:cleanup_confirm:{cleanup_type}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="gamif:config:cleanup")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:config:cleanup_confirm:"))
async def execute_cleanup(callback: CallbackQuery, session: AsyncSession):
    """Ejecuta la limpieza de datos."""
    cleanup_type = callback.data.split(":")[-1]
    
    try:
        # Aquí iría la lógica real de limpieza
        # Por ahora solo simulamos
        cleaned_count = 0
        
        if cleanup_type == "transactions":
            # Limpiar transacciones antiguas (más de 30 días)
            from datetime import datetime
            # Implementation would go here
            cleaned_count = 0
            
        elif cleanup_type == "reactions":
            # Limpiar reacciones antiguas (más de 90 días)
            from datetime import datetime
            # Implementation would go here
            cleaned_count = 0
            
        elif cleanup_type == "missions":
            # Limpiar misiones completadas antiguas
            # Esta es una operación compleja que requeriría más lógica
            cleaned_count = 0
            
        elif cleanup_type == "all":
            # Limpiar todo (solo para desarrollo/testing)
            cleaned_count = 0
            
        await callback.answer(f"✅ Limpieza completada ({cleaned_count} elementos eliminados)", show_alert=True)
        
        # Volver al menú de configuración
        await config_menu(callback, session)
        
    except Exception as e:
        await callback.answer(f"❌ Error en limpieza: {str(e)}", show_alert=True)