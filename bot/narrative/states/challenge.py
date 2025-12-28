"""
Estados FSM para desafíos narrativos.

Define los estados del flujo de desafíos interactivos
donde el usuario debe responder acertijos o preguntas.
"""
from aiogram.fsm.state import State, StatesGroup


class ChallengeStates(StatesGroup):
    """
    Estados para el flujo de desafíos narrativos.

    Flujo típico:
    1. Usuario llega a fragmento con desafío
    2. Se muestra el desafío (waiting_for_answer)
    3. Usuario envía respuesta de texto
    4. Se valida y muestra resultado
    5. Se continúa o redirige según resultado

    Estados:
    - waiting_for_answer: Esperando respuesta del usuario
    - showing_hint: Mostrando pista, esperando continuar
    - showing_result: Mostrando resultado del intento
    """

    # Esperando respuesta de texto del usuario
    waiting_for_answer = State()

    # Mostrando pista al usuario
    showing_hint = State()

    # Mostrando resultado del intento
    showing_result = State()
