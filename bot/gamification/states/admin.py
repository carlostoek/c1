"""Estados FSM para handlers de admin de gamificación."""

from aiogram.fsm.state import State, StatesGroup


class ReactionConfigStates(StatesGroup):
    """Estados para configuración de reacciones en gamificación.

    Flujo de creación:
    1. Admin selecciona "Crear Reacción"
    2. Bot pide emoji → waiting_for_emoji
    3. Admin envía emoji
    4. Bot pide valor de besitos → waiting_for_besitos
    5. Admin envía número
    6. Bot confirma → confirm
    7. Crea reacción en BD

    Flujo de edición:
    1. Admin selecciona reacción existente
    2. Bot muestra opciones (editar besitos, activar/desactivar)
    3. Si edita besitos → waiting_for_edit_besitos
    4. Actualiza en BD
    """

    # Creación de nueva reacción
    waiting_for_emoji = State()
    waiting_for_besitos = State()
    confirm_create = State()

    # Edición de reacción existente
    waiting_for_edit_besitos = State()
    waiting_for_button_emoji = State()
    waiting_for_button_label = State()
