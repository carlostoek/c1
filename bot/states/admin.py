"""
FSM States para handlers de administración.

Estados para flujos de configuración que requieren múltiples pasos.
"""
from aiogram.fsm.state import State, StatesGroup


class ChannelSetupStates(StatesGroup):
    """
    Estados para configurar canales VIP y Free.

    Flujo típico:
    1. Admin selecciona "Configurar Canal VIP"
    2. Bot entra en estado waiting_for_vip_channel
    3. Admin reenvía mensaje del canal
    4. Bot extrae ID del canal y configura
    5. Bot sale del estado (clear state)

    Extracción de ID:
    - Usuario reenvía mensaje del canal → Bot extrae forward_from_chat.id
    - ID extraído es negativo y empieza con -100
    - Si no es forward o no es de canal → Error claro
    """

    # Esperando que admin reenvíe mensaje del canal para extraer ID
    waiting_for_vip_channel = State()
    waiting_for_free_channel = State()


class WaitTimeSetupStates(StatesGroup):
    """
    Estados para configurar tiempo de espera del canal Free.

    Flujo:
    1. Admin selecciona "Configurar Tiempo de Espera"
    2. Bot entra en estado waiting_for_minutes
    3. Admin envía número de minutos
    4. Bot valida y guarda
    5. Bot sale del estado

    Validación de Minutos:
    - Usuario envía texto → Bot intenta convertir a int
    - Valor debe ser >= 1
    - Si no es número o es inválido → Error y mantener estado
    """

    # Esperando que admin envíe número de minutos
    waiting_for_minutes = State()


class BroadcastStates(StatesGroup):
    """
    Estados para envío de publicaciones a canales.

    Flujo:
    1. Admin selecciona "Enviar a Canal VIP"
    2. Bot entra en estado waiting_for_content
    3. Admin envía mensaje (texto, foto o video)
    4. Bot pide confirmación (opcional)
    5. Bot envía al canal y sale del estado

    Tipos de Contenido:
    - Soportar: texto, foto, video
    - Estado waiting_for_content acepta cualquiera
    - Estado waiting_for_confirmation es opcional (puede omitirse)
    """

    # Esperando contenido del mensaje a enviar
    waiting_for_content = State()

    # Esperando confirmación de envío (opcional)
    waiting_for_confirmation = State()
