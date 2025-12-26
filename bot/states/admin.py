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


class FreeMessageSetupStates(StatesGroup):
    """
    Estados para configurar mensaje de bienvenida Free.

    Flujo:
    1. Admin selecciona "Configurar Mensaje de Bienvenida"
    2. Bot entra en estado waiting_for_message
    3. Admin envía mensaje personalizado
    4. Bot valida (10-1000 chars) y guarda
    5. Bot sale del estado

    Variables soportadas en el mensaje:
    - {user_name}: Nombre del usuario
    - {channel_name}: Nombre del canal
    - {wait_time}: Tiempo de espera en minutos

    Validación:
    - Longitud: 10-1000 caracteres
    - Si no es válido → Error y mantener estado
    - Si es válido → Guardar en DB y clear state
    """

    # Esperando que admin envíe mensaje personalizado
    waiting_for_message = State()


class BroadcastStates(StatesGroup):
    """
    Estados para envío de publicaciones a canales con gamificación.

    Flujo completo (4 pasos):
    1. Admin selecciona canal destino (VIP, Free, o Ambos)
       → Bot entra en waiting_for_content

    2. Admin envía contenido (texto, foto, o video)
       → Bot guarda contenido en FSM data
       → Bot entra en configuring_options

    3. Admin configura opciones de gamificación (NUEVO):
       a. Activar/desactivar gamificación
       b. Seleccionar reacciones (entra en selecting_reactions)
       c. Activar/desactivar protección de contenido
       → Bot entra en waiting_for_confirmation cuando admin confirma

    4. Admin confirma envío
       → Bot muestra preview final
       → Admin confirma o cancela
       → Si confirma: Bot envía al canal(es) con config de gamificación
       → Si cancela: Bot puede volver a configuring_options o salir

    Estados del flujo:
    - waiting_for_content: Esperando contenido multimedia del admin
    - configuring_options: Configurando opciones de gamificación y protección
    - selecting_reactions: Sub-estado para seleccionar reacciones específicas
    - waiting_for_confirmation: Confirmación final antes de enviar

    Opciones de Gamificación:
    - Reacciones personalizadas: Admin selecciona qué emojis mostrar como botones
    - Protección de contenido: Prevenir forwards/copias del mensaje
    - Besitos por reacción: Configurados en los ReactionTypes

    Callbacks de configuración:
    - broadcast:config:reactions → Activar/configurar reacciones
    - broadcast:config:gamif_off → Desactivar gamificación
    - broadcast:config:protection_on → Activar protección
    - broadcast:config:protection_off → Desactivar protección
    - broadcast:react:toggle:{id} → Toggle reacción específica
    - broadcast:react:confirm → Confirmar selección de reacciones
    - broadcast:react:cancel → Cancelar selección de reacciones

    Tipos de Contenido Soportados:
    - Texto plano
    - Foto (con caption opcional)
    - Video (con caption opcional)
    """

    # Paso 1: Esperando contenido del mensaje a enviar
    waiting_for_content = State()

    # Paso 2: Configurando opciones de gamificación y protección (NUEVO)
    configuring_options = State()

    # Paso 3: Seleccionando reacciones específicas a aplicar (sub-estado)
    selecting_reactions = State()

    # Paso 4: Esperando confirmación final de envío (después de configuración)
    waiting_for_confirmation = State()


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
