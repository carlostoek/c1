"""
Keyboards para el wizard de configuración.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional


def config_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard del menú principal de configuración."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📊 Puntos y Acciones",
            callback_data="config:actions"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📈 Niveles",
            callback_data="config:levels"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏆 Badges",
            callback_data="config:badges"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎁 Recompensas",
            callback_data="config:rewards"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎯 Misiones",
            callback_data="config:missions"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Cerrar",
            callback_data="config:close"
        )
    )
    
    return builder.as_markup()


def config_list_keyboard(
    items: List[tuple],  # [(id, name), ...]
    prefix: str,
    show_create: bool = True,
    show_back: bool = True
) -> InlineKeyboardMarkup:
    """
    Keyboard genérico para listas de configuración.
    
    Args:
        items: Lista de tuplas (id, name)
        prefix: Prefijo para callbacks (ej: "config:actions")
        show_create: Mostrar botón de crear
        show_back: Mostrar botón de volver
    """
    builder = InlineKeyboardBuilder()
    
    # Items
    for item_id, name in items:
        builder.row(
            InlineKeyboardButton(
                text=name,
                callback_data=f"{prefix}:view:{item_id}"
            )
        )
    
    # Botones de acción
    buttons = []
    if show_create:
        buttons.append(
            InlineKeyboardButton(text="➕ Crear", callback_data=f"{prefix}:create")
        )
    if show_back:
        buttons.append(
            InlineKeyboardButton(text="◀️ Volver", callback_data="config:main")
        )
    
    if buttons:
        builder.row(*buttons)
    
    return builder.as_markup()


def config_item_keyboard(
    item_id: int,
    prefix: str,
    can_delete: bool = True
) -> InlineKeyboardMarkup:
    """Keyboard para ver/editar un item específico."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Editar",
            callback_data=f"{prefix}:edit:{item_id}"
        )
    )
    
    if can_delete:
        builder.row(
            InlineKeyboardButton(
                text="🗑️ Eliminar",
                callback_data=f"{prefix}:delete:{item_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Volver a lista",
            callback_data=f"{prefix}:list"
        )
    )
    
    return builder.as_markup()


def confirm_keyboard(
    confirm_callback: str,
    cancel_callback: str
) -> InlineKeyboardMarkup:
    """Keyboard de confirmación."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Confirmar", callback_data=confirm_callback),
        InlineKeyboardButton(text="❌ Cancelar", callback_data=cancel_callback)
    )
    
    return builder.as_markup()


def nested_choice_keyboard(
    existing_callback: str,
    create_callback: str,
    none_callback: Optional[str] = None,
    back_callback: str = "config:main"
) -> InlineKeyboardMarkup:
    """
    Keyboard para elegir entre usar existente o crear nuevo.
    
    Args:
        existing_callback: Callback para seleccionar existente
        create_callback: Callback para crear nuevo
        none_callback: Callback para "ninguno" (opcional)
        back_callback: Callback para volver
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 Usar existente", callback_data=existing_callback)
    )
    builder.row(
        InlineKeyboardButton(text="➕ Crear nuevo", callback_data=create_callback)
    )
    
    if none_callback:
        builder.row(
            InlineKeyboardButton(text="⏭️ Sin recompensa", callback_data=none_callback)
        )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Volver", callback_data=back_callback)
    )
    
    return builder.as_markup()


def skip_keyboard(
    skip_callback: str,
    back_callback: str
) -> InlineKeyboardMarkup:
    """Keyboard para campos opcionales."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⏭️ Omitir", callback_data=skip_callback),
        InlineKeyboardButton(text="◀️ Volver", callback_data=back_callback)
    )
    
    return builder.as_markup()