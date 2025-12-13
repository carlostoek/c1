"""
FSM States para handlers de usuarios.

Estados para flujos de usuarios (canje de tokens, solicitud Free).
"""
from aiogram.fsm.state import State, StatesGroup


class TokenRedemptionStates(StatesGroup):
    """
    Estados para canje de tokens VIP.

    Flujo:
    1. Usuario envía /start
    2. Bot pregunta por token
    3. Bot entra en estado waiting_for_token
    4. Usuario envía token
    5. Bot valida y canjea
    6. Bot sale del estado

    Validación de Token:
    - Usuario envía texto → Bot valida formato y existe en BD
    - Token debe estar vigente (no expirado)
    - Token debe no estar ya canjeado
    - Si token es inválido → Error claro y mantener estado
    """

    # Esperando que usuario envíe token
    waiting_for_token = State()


class FreeAccessStates(StatesGroup):
    """
    Estados para solicitud de acceso Free.

    Flujo:
    1. Usuario solicita acceso Free
    2. Bot crea solicitud
    3. Bot puede usar estado para tracking (opcional)

    Nota: Este flujo es mayormente automático (background task),
    pero el estado se puede usar para prevenir spam de solicitudes.

    Estados:
    - waiting_for_approval: Usuario tiene solicitud pendiente de aprobación
    """

    # Usuario tiene solicitud pendiente
    waiting_for_approval = State()
