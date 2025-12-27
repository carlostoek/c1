"""
Estados FSM para administración de la Tienda.

Define los estados para los wizards de creación y edición de:
- Categorías de productos
- Productos de la tienda
"""

from aiogram.fsm.state import State, StatesGroup


class CategoryCreationStates(StatesGroup):
    """
    Estados para el wizard de creación de categorías.

    Flujo:
    1. waiting_for_name: Admin ingresa nombre
    2. waiting_for_description: Admin ingresa descripción
    3. waiting_for_emoji: Admin selecciona emoji
    4. confirming: Admin confirma creación
    """
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_emoji = State()
    confirming = State()


class CategoryEditStates(StatesGroup):
    """
    Estados para edición de categorías.

    Flujo:
    1. selecting_field: Admin selecciona qué editar
    2. waiting_for_value: Admin ingresa nuevo valor
    3. confirming: Admin confirma cambio
    """
    selecting_field = State()
    waiting_for_value = State()
    confirming = State()


class ItemCreationStates(StatesGroup):
    """
    Estados para el wizard de creación de productos.

    Flujo:
    1. selecting_category: Admin selecciona categoría
    2. selecting_type: Admin selecciona tipo de item
    3. waiting_for_name: Admin ingresa nombre
    4. waiting_for_description: Admin ingresa descripción corta
    5. waiting_for_long_description: Admin ingresa descripción larga (opcional)
    6. waiting_for_price: Admin ingresa precio en besitos
    7. waiting_for_icon: Admin selecciona icono/emoji
    8. waiting_for_image: Admin envía imagen (opcional)
    9. configuring_options: Admin configura opciones adicionales
    10. waiting_for_metadata: Admin configura metadata específica del tipo
    11. confirming: Admin confirma creación
    """
    selecting_category = State()
    selecting_type = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_long_description = State()
    waiting_for_price = State()
    waiting_for_icon = State()
    waiting_for_image = State()
    configuring_options = State()
    waiting_for_metadata = State()
    confirming = State()


class ItemEditStates(StatesGroup):
    """
    Estados para edición de productos.

    Flujo:
    1. selecting_field: Admin selecciona qué editar
    2. waiting_for_value: Admin ingresa nuevo valor
    3. confirming: Admin confirma cambio
    """
    selecting_field = State()
    waiting_for_value = State()
    confirming = State()


class NarrativeItemConfigStates(StatesGroup):
    """
    Estados para configurar metadata de items narrativos.

    Flujo:
    1. selecting_unlock_type: Selecciona qué desbloquea (fragmento o capítulo)
    2. waiting_for_fragment_key: Admin ingresa fragment_key
    3. waiting_for_chapter_slug: Admin ingresa chapter_slug
    4. waiting_for_lore: Admin ingresa texto de lore (opcional)
    """
    selecting_unlock_type = State()
    waiting_for_fragment_key = State()
    waiting_for_chapter_slug = State()
    waiting_for_lore = State()
