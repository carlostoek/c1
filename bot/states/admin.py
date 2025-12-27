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


class MenuConfigStates(StatesGroup):
    """
    Estados para configuración de menús dinámicos.

    Flujos soportados:
    1. Crear nuevo botón (5 pasos)
    2. Editar botón existente (2 pasos)
    3. Configurar mensajes del menú (2 pasos)

    Flujo 1: Crear Botón Nuevo
    1. Admin selecciona "Crear Nuevo Botón"
    2. Bot entra en waiting_for_button_text
    3. Admin envía texto del botón: "Información de Contacto"
    4. Bot entra en waiting_for_button_emoji
    5. Admin envía emoji: "📞" (o "-" para omitir)
    6. Bot entra en waiting_for_action_type
    7. Admin selecciona tipo: info/url/contact
    8. Bot entra en waiting_for_action_content
    9. Admin envía contenido según tipo seleccionado
    10. Bot entra en waiting_for_target_role
    11. Admin selecciona rol: vip/free/all
    12. Bot crea el botón y sale del estado

    Flujo 2: Editar Botón
    1. Admin selecciona botón existente
    2. Admin selecciona "Editar Texto" o "Editar Contenido"
    3. Bot entra en editing_button_text o editing_action_content
    4. Admin envía nuevo valor
    5. Bot actualiza y sale del estado

    Flujo 3: Configurar Mensajes
    1. Admin selecciona "Configurar Mensaje VIP/FREE"
    2. Bot entra en editing_welcome_message o editing_footer_message
    3. Admin envía nuevo mensaje
    4. Bot actualiza y sale del estado

    Validaciones:
    - button_text: 1-100 caracteres
    - button_emoji: Máximo 10 caracteres (o "-" para omitir)
    - action_type: 'info', 'url', 'contact'
    - action_content: No vacío, si URL debe empezar con http/https
    - target_role: 'vip', 'free', 'all'
    - welcome_message: No vacío
    """

    # ═══════ Crear Nuevo Botón (5 estados) ═══════
    # Paso 1: Esperando texto del botón
    waiting_for_button_text = State()

    # Paso 2: Esperando emoji del botón (opcional)
    waiting_for_button_emoji = State()

    # Paso 3: Esperando tipo de acción (info/url/contact)
    waiting_for_action_type = State()

    # Paso 4: Esperando contenido de la acción
    waiting_for_action_content = State()

    # Paso 5: Esperando rol target (vip/free/all)
    waiting_for_target_role = State()

    # ═══════ Editar Botón (2 estados) ═══════
    # Editando texto del botón
    editing_button_text = State()

    # Editando contenido de acción
    editing_action_content = State()

    # ═══════ Configurar Menú (2 estados) ═══════
    # Editando mensaje de bienvenida
    editing_welcome_message = State()

    # Editando mensaje de footer
    editing_footer_message = State()


class JsonImportStates(StatesGroup):
    """
    Estados para el wizard de importación de fragmentos narrativos desde JSON.

    Flujo completo:
    1. Admin accede a menú narrativa -> "Importar JSON"
       -> Bot muestra opciones: Capítulo completo o Solo fragmentos
       -> Admin selecciona tipo de importación

    2. Bot entra en waiting_for_json_file
       -> Admin sube documento .json
       -> Bot parsea y valida estructura
       -> Si hay errores de formato: muestra error, mantiene estado
       -> Si válido: detecta conflictos

    3. Si hay conflictos (fragment_key ya existe):
       -> Bot entra en resolving_conflicts
       -> Muestra opciones: Actualizar todos, Omitir todos,
          Revisar uno por uno, Cancelar

    4. Si admin elige "Revisar uno por uno":
       -> Bot entra en reviewing_single_conflict
       -> Muestra cada fragmento conflictivo
       -> Admin decide: Actualizar / Omitir para cada uno
       -> Cuando termina todos: pasa a confirmación

    5. Confirmación final (waiting_for_confirmation):
       -> Bot muestra resumen de operaciones a realizar
       -> Si confirma: procesa JSON
       -> Si cancela: limpia FSM

    FSM Data esperada:
    - json_content: dict           # JSON parseado
    - import_type: str             # "chapter" o "fragments"
    - chapter_slug: str            # Slug del capítulo destino
    - chapter_data: dict           # Datos del capítulo (si aplica)
    - fragments: list[dict]        # Lista de fragmentos a procesar
    - conflicts: list[dict]        # Fragment keys con conflicto
    - conflict_resolutions: dict   # {fragment_key: "update"|"skip"}
    - current_conflict_idx: int    # Índice del conflicto actual
    """

    # Paso 1: Esperando archivo JSON del admin
    waiting_for_json_file = State()

    # Paso 2: Resolviendo conflictos (opción global)
    resolving_conflicts = State()

    # Paso 3: Revisando conflicto individual
    reviewing_single_conflict = State()

    # Paso 4: Esperando confirmación final
    waiting_for_confirmation = State()
