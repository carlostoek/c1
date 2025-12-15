"""
Keyboard Factory - Generador de teclados inline.

Centraliza la creación de keyboards para consistencia visual.
"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_inline_keyboard(
    buttons: List[List[dict]],
    **kwargs
) -> InlineKeyboardMarkup:
    """
    Crea un inline keyboard a partir de una estructura de botones.

    Args:
        buttons: Lista de filas, cada fila es lista de botones
                 Cada botón es dict con 'text' y ('callback_data' OR 'url')

    Ejemplo:
        keyboard = create_inline_keyboard([
            [{"text": "Botón 1", "callback_data": "btn1"}],
            [
                {"text": "Botón 2", "callback_data": "btn2"},
                {"text": "Botón 3", "url": "https://example.com"}
            ]
        ])

    Returns:
        InlineKeyboardMarkup
    """
    inline_keyboard = []

    for row in buttons:
        keyboard_row = []
        for button in row:
            # Crear botón con callback_data o url
            if "callback_data" in button:
                btn = InlineKeyboardButton(
                    text=button["text"],
                    callback_data=button["callback_data"]
                )
            elif "url" in button:
                btn = InlineKeyboardButton(
                    text=button["text"],
                    url=button["url"]
                )
            else:
                raise ValueError(
                    f"Botón debe tener 'callback_data' o 'url': {button}"
                )
            keyboard_row.append(btn)
        inline_keyboard.append(keyboard_row)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, **kwargs)


def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard del menú principal de admin.

    Opciones:
    - Dashboard completo
    - Gestión VIP
    - Gestión Free
    - Configuración
    - Tarifas
    - Mensajes
    - Estadísticas

    Returns:
        InlineKeyboardMarkup con menú principal
    """
    return create_inline_keyboard([
        [{"text": "📊 Dashboard Completo", "callback_data": "admin:dashboard"}],
        [{"text": "📺 Gestión Canal VIP", "callback_data": "admin:vip"}],
        [{"text": "📺 Gestión Canal Free", "callback_data": "admin:free"}],
        [{"text": "⚙️ Configuración", "callback_data": "admin:config"}],
        [{"text": "⚙️ Configurar Reacciones", "callback_data": "admin:reactions_config"}],
        [{"text": "💰 Tarifas", "callback_data": "admin:pricing"}],
        [{"text": "💬 Mensajes", "callback_data": "admin:messages"}],
        [{"text": "📊 Estadísticas", "callback_data": "admin:stats"}],
    ])


def back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard con solo botón "Volver al menú principal".

    Usado en submenús para regresar.

    Returns:
        InlineKeyboardMarkup con botón volver
    """
    return create_inline_keyboard([
        [{"text": "🔙 Volver al Menú Principal", "callback_data": "admin:main"}]
    ])


def stats_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard del menú de estadísticas.

    Opciones:
    - Ver Stats VIP Detalladas
    - Ver Stats Free Detalladas
    - Ver Stats de Tokens
    - Actualizar Estadísticas (force refresh)
    - Volver al Menú Principal

    Returns:
        InlineKeyboardMarkup con menú de stats
    """
    return create_inline_keyboard([
        [{"text": "📊 Ver Stats VIP Detalladas", "callback_data": "admin:stats:vip"}],
        [{"text": "📊 Ver Stats Free Detalladas", "callback_data": "admin:stats:free"}],
        [{"text": "🎟️ Ver Stats de Tokens", "callback_data": "admin:stats:tokens"}],
        [{"text": "🔄 Actualizar Estadísticas", "callback_data": "admin:stats:refresh"}],
        [{"text": "🔙 Volver al Menú Principal", "callback_data": "admin:main"}],
    ])


def yes_no_keyboard(
    yes_callback: str,
    no_callback: str
) -> InlineKeyboardMarkup:
    """
    Keyboard de confirmación Sí/No.

    Args:
        yes_callback: Callback data para "Sí"
        no_callback: Callback data para "No"

    Returns:
        InlineKeyboardMarkup con botones Sí/No
    """
    return create_inline_keyboard([
        [
            {"text": "✅ Sí", "callback_data": yes_callback},
            {"text": "❌ No", "callback_data": no_callback}
        ]
    ])


def config_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard del menú de configuración.

    Opciones:
    - Ver estado de configuración
    - Configurar reacciones VIP
    - Configurar reacciones Free
    - Volver al menú principal

    Returns:
        InlineKeyboardMarkup con menú de configuración
    """
    return create_inline_keyboard([
        [{"text": "📊 Ver Estado de Configuración", "callback_data": "config:status"}],
        [{"text": "⚙️ Configurar Reacciones VIP", "callback_data": "config:reactions:vip"}],
        [{"text": "⚙️ Configurar Reacciones Free", "callback_data": "config:reactions:free"}],
        [{"text": "🔙 Volver al Menú Principal", "callback_data": "admin:main"}],
    ])


from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_reaction_keyboard(
    reactions: List[tuple],
    channel_id: int,
    message_id: int,
    counts: Optional[dict] = None
) -> InlineKeyboardMarkup:
    """
    Crea keyboard inline con botones de reacción.
    
    Args:
        reactions: Lista de tuplas (reaction_id, emoji, label)
        channel_id: ID del canal de Telegram
        message_id: ID del mensaje de Telegram
        counts: Dict opcional {emoji: count} para mostrar contadores
        
    Returns:
        InlineKeyboardMarkup con botones de reacción
        
    Example:
        >>> reactions = [(1, "❤️", "Me encanta"), (2, "👍", "Me gusta")]
        >>> keyboard = create_reaction_keyboard(
        ...     reactions=reactions,
        ...     channel_id=-1001234567890,
        ...     message_id=12345,
        ...     counts={"❤️": 10, "👍": 5}
        ... )
    
    Format de callback_data: react:{emoji}:{channel_id}:{message_id}
    """
    buttons = []
    
    # Agrupar en filas de máximo 3 botones
    row = []
    for reaction_id, emoji, label in reactions:
        # Construir texto del botón con contador si existe
        count = counts.get(emoji, 0) if counts else 0
        button_text = f"{emoji} {count}" if count > 0 else emoji
        
        # Construir callback_data
        callback_data = f"react:{emoji}:{channel_id}:{message_id}"
        
        button = InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        )
        
        row.append(button)
        
        # Cada 3 botones, crear nueva fila
        if len(row) == 3:
            buttons.append(row)
            row = []
    
    # Agregar última fila si quedaron botones
    if row:
        buttons.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

