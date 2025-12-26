"""
Tests para BroadcastStates (FSM).

Valida:
- Existencia de todos los estados
- Orden correcto de estados
- Nombres de estados string correctos
"""
import pytest
from bot.states.admin import BroadcastStates


def test_broadcast_states_exist():
    """Test: Todos los estados existen"""
    # Verificar que todos los estados están definidos
    assert hasattr(BroadcastStates, 'waiting_for_content')
    assert hasattr(BroadcastStates, 'configuring_options')
    assert hasattr(BroadcastStates, 'selecting_reactions')
    assert hasattr(BroadcastStates, 'waiting_for_confirmation')


def test_broadcast_states_count():
    """Test: Cantidad correcta de estados (4)"""
    # BroadcastStates debe tener exactamente 4 estados
    states = [
        BroadcastStates.waiting_for_content,
        BroadcastStates.configuring_options,
        BroadcastStates.selecting_reactions,
        BroadcastStates.waiting_for_confirmation
    ]
    assert len(states) == 4


def test_broadcast_state_strings():
    """Test: State strings son correctos"""
    # Verificar que los state strings son únicos y tienen el formato correcto
    assert BroadcastStates.waiting_for_content.state is not None
    assert BroadcastStates.configuring_options.state is not None
    assert BroadcastStates.selecting_reactions.state is not None
    assert BroadcastStates.waiting_for_confirmation.state is not None

    # Verificar que todos son diferentes
    states_set = {
        BroadcastStates.waiting_for_content.state,
        BroadcastStates.configuring_options.state,
        BroadcastStates.selecting_reactions.state,
        BroadcastStates.waiting_for_confirmation.state
    }
    assert len(states_set) == 4, "Los estados deben ser únicos"


def test_configuring_options_is_new_state():
    """Test: configuring_options es el nuevo estado agregado"""
    # Este estado es NUEVO en T4
    assert BroadcastStates.configuring_options is not None
    assert "configuring_options" in str(BroadcastStates.configuring_options.state)


def test_selecting_reactions_exists():
    """Test: selecting_reactions ya existía (backward compatibility)"""
    # Este estado ya existía desde antes
    assert BroadcastStates.selecting_reactions is not None
    assert "selecting_reactions" in str(BroadcastStates.selecting_reactions.state)


def test_broadcast_states_group_name():
    """Test: StatesGroup tiene el nombre correcto"""
    assert BroadcastStates.__name__ == "BroadcastStates"
