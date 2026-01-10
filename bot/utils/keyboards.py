"""
Keyboard Factory - Generador de teclados inline.

Centraliza la creación de keyboards para consistencia visual.
"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession


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
    - Dashboard
    - VIP - Free (gestión de canales)
    - Gamificación
    - Gestión Narrativa
    - Gestión de Tienda
    - CMS Journey (Content Sets)
    - Configurar Menús
    - Estadísticas - Configuración

    Returns:
        InlineKeyboardMarkup con menú principal
    """
    return create_inline_keyboard([
        [{"text": "📊 Dashboard", "callback_data": "admin:dashboard"}],
        [
            {"text": "⭐ VIP", "callback_data": "admin:vip"},
            {"text": "🆓 Free", "callback_data": "admin:free"}
        ],
        [{"text": "🎮 Gamificación", "callback_data": "admin:gamification"}],
        [{"text": "📖 Gestión Narrativa", "callback_data": "admin:narrative"}],
        [
            {"text": "🏪 Gestión de Tienda", "callback_data": "admin:shop"},
            {"text": "🎬 CMS Journey", "callback_data": "admin:content"}
        ],
        [{"text": "📋 Configurar Menús", "callback_data": "admin:menus"}],
        [
            {"text": "📊 Estadísticas", "callback_data": "admin:stats"},
            {"text": "⚙️ Configuración", "callback_data": "admin:config"}
        ],
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


def gamification_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard del menú de gamificación.

    ÚNICA FUENTE DE VERDAD para el menú de gamificación.
    Usado por:
    - admin:gamification (desde menú admin)
    - /gamif (comando directo)
    - gamif:menu (callback de regreso)

    Opciones:
    - Misiones
    - Recompensas
    - Niveles
    - Estadísticas
    - Economía (NUEVO)
    - Transacciones
    - Configuración
    - Wizard Creación
    - Panel Central
    - Volver al Menú Principal

    Returns:
        InlineKeyboardMarkup con menú completo de gamificación
    """
    return create_inline_keyboard([
        [
            {"text": "📋 Misiones", "callback_data": "gamif:admin:missions"},
            {"text": "🎁 Recompensas", "callback_data": "gamif:admin:rewards"}
        ],
        [
            {"text": "⭐ Niveles", "callback_data": "gamif:admin:levels"},
            {"text": "📊 Estadísticas", "callback_data": "gamif:admin:stats"}
        ],
        [
            {"text": "💰 Economía", "callback_data": "gamif:admin:economy"},
            {"text": "💳 Transacciones", "callback_data": "gamif:admin:transactions"}
        ],
        [
            {"text": "🔧 Configuración", "callback_data": "gamif:admin:config"}
        ],
        [
            {"text": "🎨 Wizard Creación", "callback_data": "unified:wizard:menu"},
            {"text": "📊 Panel Central", "callback_data": "config_panel:main"}
        ],
        [
            {"text": "🔙 Volver al Menú Principal", "callback_data": "admin:main"}
        ]
    ])


# ========================================
# Keyboards para Wizard de Menús
# ========================================

def action_type_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard para seleccionar tipo de acción en wizard de menús.

    Opciones:
    - Callback (ejecuta callback_data)
    - URL (abre enlace externo)
    - Submenú (navega a submenú)
    - Info (muestra mensaje informativo)
    - Blocked (opción bloqueada)
    - Cancelar

    Returns:
        InlineKeyboardMarkup con opciones
    """
    return create_inline_keyboard([
        [{"text": "🔘 Callback", "callback_data": "wizard:action:callback"}],
        [{"text": "🔗 URL", "callback_data": "wizard:action:url"}],
        [{"text": "📁 Submenú", "callback_data": "wizard:action:submenu"}],
        [{"text": "ℹ️ Info", "callback_data": "wizard:action:info"}],
        [{"text": "🚫 Blocked", "callback_data": "wizard:action:blocked"}],
        [{"text": "❌ Cancelar", "callback_data": "wizard:cancel"}]
    ])


def target_role_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard para seleccionar rol objetivo en wizard de menús.

    Opciones:
    - FREE (usuarios gratuitos)
    - VIP (suscriptores)
    - Admin (administradores)
    - Todos (todos los usuarios)
    - Atrás

    Returns:
        InlineKeyboardMarkup con opciones
    """
    return create_inline_keyboard([
        [{"text": "👥 FREE", "callback_data": "wizard:role:free"}],
        [{"text": "⭐ VIP", "callback_data": "wizard:role:vip"}],
        [{"text": "👑 Admin", "callback_data": "wizard:role:admin"}],
        [{"text": "🌐 Todos", "callback_data": "wizard:role:all"}],
        [{"text": "⬅️ Atrás", "callback_data": "wizard:back"}]
    ])


def boolean_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard para selección Sí/No en wizard de menús.

    Usado para requires_onboarding y otras opciones binarias.

    Returns:
        InlineKeyboardMarkup con opciones
    """
    return create_inline_keyboard([
        [
            {"text": "✅ Sí", "callback_data": "wizard:bool:true"},
            {"text": "❌ No", "callback_data": "wizard:bool:false"}
        ],
        [{"text": "⬅️ Atrás", "callback_data": "wizard:back"}]
    ])


def wizard_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard con solo botón Cancelar para wizard.

    Usado en pasos del wizard donde solo se puede cancelar.

    Returns:
        InlineKeyboardMarkup con botón cancelar
    """
    return create_inline_keyboard([
        [{"text": "❌ Cancelar Wizard", "callback_data": "wizard:cancel"}]
    ])
