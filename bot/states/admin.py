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
    Estados para envío de publicaciones a canales (BROADCASTING AVANZADO).

    Flujo completo:
    1. Admin selecciona canal destino (VIP, Free, o Ambos)
    2. Bot entra en waiting_for_content
    3. Admin envía contenido (texto, foto, o video)
    4. Bot muestra preview y entra en waiting_for_confirmation
    5. Admin confirma o cancela
    6. Si confirma: Bot envía al canal(es) y sale del estado
    7. Si cancela: Bot vuelve a waiting_for_content o sale

    Estados adicionales para reacciones (ONDA 2):
    - selecting_reactions: Admin selecciona reacciones a aplicar

    Tipos de Contenido:
    - Soportar: texto, foto, video
    - Estado waiting_for_content acepta cualquiera
    - Estado waiting_for_confirmation maneja confirmación
    - Estado selecting_reactions permite cambiar reacciones (opcional)
    """

    # Estado 1: Esperando contenido del mensaje a enviar
    waiting_for_content = State()

    # Estado 2: Esperando confirmación de envío (después de preview)
    waiting_for_confirmation = State()

    # Estado 3: Seleccionando reacciones a aplicar (NUEVO - T23)
    selecting_reactions = State()


class ReactionSetupStates(StatesGroup):
    """
    Estados para configuración de reacciones automáticas.

    Flujo:
    1. Admin selecciona "Configurar Reacciones VIP/Free"
    2. Bot entra en waiting_for_vip_reactions o waiting_for_free_reactions
    3. Admin envía lista de emojis separados por espacios
    4. Bot valida (1-10 emojis) y guarda
    5. Bot sale del estado

    Validación de Input:
    - Formato: Emojis separados por espacios
    - Rango válido: 1-10 emojis
    - Si no es válido → Error y mantener estado
    - Si es válido → Guardar en DB y clear state

    NUEVO EN ONDA 2 - T21
    """

    # Esperando lista de emojis para canal VIP
    waiting_for_vip_reactions = State()

    # Esperando lista de emojis para canal Free
    waiting_for_free_reactions = State()


class PricingSetupStates(StatesGroup):
    """
    Estados para configurar planes de suscripción.

    Flujo:
    1. Admin selecciona "Crear Tarifa"
    2. Bot entra en waiting_for_name
    3. Admin envía nombre: "Plan Mensual"
    4. Bot entra en waiting_for_days
    5. Admin envía días: "30"
    6. Bot entra en waiting_for_price
    7. Admin envía precio: "9.99"
    8. Bot confirma y guarda
    9. Bot sale del estado

    Validación:
    - Nombre: No vacío, máximo 100 caracteres
    - Días: Número entero > 0, máximo 3650 (10 años)
    - Precio: Número decimal >= 0, máximo 9999
    - Si no es válido → Error y mantener estado
    - Si es válido → Guardar en DB y clear state
    """

    # Paso 1: Esperando nombre del plan
    waiting_for_name = State()

    # Paso 2: Esperando duración en días
    waiting_for_days = State()

    # Paso 3: Esperando precio del plan
    waiting_for_price = State()


class ContentPackageStates(StatesGroup):
    """
    Estados para creación de paquetes de contenido.

    Flujo de creación:
    1. Admin selecciona "Crear Paquete"
    2. Bot entra en waiting_for_name
    3. Admin envía nombre: "Colección Verano"
    4. Bot entra en waiting_for_type
    5. Admin selecciona tipo con botones: [VIP Premium] [VIP Content] [Free Content]
    6. Bot entra en waiting_for_price
    7. Admin envía precio o /skip: "9.99" o "/skip"
    8. Bot entra en waiting_for_description
    9. Admin envía descripción o /skip: "Contenido exclusivo..."
    10. Bot crea paquete y sale del estado

    Flujo de edición (inline prompt pattern):
    1. Admin abre detalle de paquete existente
    2. Admin selecciona campo a editar: [Editar nombre] [Editar precio] [Editar descripción]
    3. Bot entra en waiting_for_edit
    4. Admin envía nuevo valor o /skip para mantener actual
    5. Bot actualiza campo y vuelve a vista detalle

    Validación:
    - Nombre: No vacío, máximo 200 caracteres
    - Tipo: Debe seleccionar con botones (3 opciones), NO editable post-creación
    - Precio: Opcional, si se envía debe ser número >= 0
    - Descripción: Opcional, texto libre
    - /skip: Permite omitir campos opcionales (creación) o mantener valor actual (edición)
    - Cancelar: Vuelve al menú principal sin guardar

    Estados:
    - waiting_for_name: Esperando nombre del paquete (texto) - CREACIÓN
    - waiting_for_type: Esperando tipo de paquete (botones inline) - CREACIÓN
    - waiting_for_price: Esperando precio (número o /skip) - CREACIÓN
    - waiting_for_description: Esperando descripción (texto o /skip) - CREACIÓN
    - waiting_for_edit: Esperando nuevo valor de campo (inline prompt) - EDICIÓN
    """

    # ===== CREACIÓN (4-step wizard) =====

    # Paso 1: Esperando nombre del paquete (required)
    waiting_for_name = State()

    # Paso 2: Esperando tipo de paquete via botones inline (required)
    waiting_for_type = State()

    # Paso 3: Esperando precio del paquete (optional, /skip to omit)
    waiting_for_price = State()

    # Paso 4: Esperando descripción del paquete (optional, /skip to omit)
    waiting_for_description = State()

    # ===== EDICIÓN (inline prompt pattern) =====

    # Para editar campos de paquetes existentes (name, price, description)
    waiting_for_edit = State()  # For inline prompt editing
