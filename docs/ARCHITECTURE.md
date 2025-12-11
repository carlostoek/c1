# Arquitectura del Bot VIP/Free

Documento técnico que describe la arquitectura, componentes y flujo de datos del bot de administración de canales para Telegram.

## Resumen Arquitectónico

El bot implementa una arquitectura modular y asincrónica optimizada para Termux (Android), con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT API                          │
└────────────────────────┬────────────────────────────────────┘
                         │ (polling)
┌────────────────────────▼────────────────────────────────────┐
│              AIOGRAM DISPATCHER (async)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Middlewares                                             ││
│  │ • AdminAuthMiddleware: Validación de permisos           ││
│  │ • DatabaseMiddleware: Inyección de sesión BD            ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Handlers                                                ││
│  │ ├── Admin: Gestión de canales, tokens, suscriptores    ││
│  │ └── User: Canje de tokens, solicitud Free              ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ FSM States (Memory Storage)                             ││
│  │ • AdminStates: Máquina de estado para admin             ││
│  │ • UserStates: Máquina de estado para usuarios           ││
│  └─────────────────────────────────────────────────────────┘│
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌────────────────┐  ┌─────────────────┐
│  DATABASE    │  │  SERVICES      │  │  BACKGROUND     │
│              │  │                │  │  TASKS          │
│ • BotConfig  │  │ • Subscription │  │                 │
│ • VIPTokens  │  │ • Channel      │  │ • Cleanup       │
│ • VIPSubs    │  │ • Config       │  │ • Processing    │
│ • FreeReqs   │  │                │  │                 │
└──────────────┘  └────────────────┘  └─────────────────┘
     (SQLite)        (Business Logic)   (APScheduler)
```

## Componentes Principales

### 1. Entry Point (main.py)

**Responsabilidad:** Gestionar el ciclo de vida completo del bot

```python
asyncio.run(main())
    ├── on_startup()
    │   ├── Validar configuración
    │   ├── Inicializar base de datos
    │   ├── Registrar handlers y middlewares
    │   └── Notificar a admins que está online
    ├── dp.start_polling()
    │   └── Procesar mensajes en bucle continuo
    └── on_shutdown()
        ├── Detener background tasks
        ├── Cerrar base de datos
        └── Notificar a admins que está offline
```

**Características:**
- Manejo de errores críticos con try-except
- Keyboard interrupt (Ctrl+C) para shutdown graceful
- Logging en todos los pasos
- Drop de updates pendientes del pasado

### 2. Configuración (config.py)

**Responsabilidad:** Gestión centralizada de variables de entorno

**Componentes:**
- `Config.BOT_TOKEN` - Token de Telegram Bot API
- `Config.ADMIN_USER_IDS` - Lista de IDs de administradores
- `Config.DATABASE_URL` - URL de conexión SQLite
- `Config.DEFAULT_WAIT_TIME_MINUTES` - Tiempo espera canal Free
- `Config.LOG_LEVEL` - Nivel de logging (DEBUG, INFO, WARNING, ERROR)
- `Config.TOKEN_LENGTH` - Longitud de tokens (16 caracteres)
- `Config.DEFAULT_TOKEN_DURATION_HOURS` - Duración de tokens (24h)

**Métodos:**
- `validate()` - Valida configuración mínima requerida
- `setup_logging()` - Configura logging según nivel
- `is_admin(user_id)` - Verifica si usuario es admin
- `load_admin_ids()` - Parsea ADMIN_USER_IDS desde .env
- `get_summary()` - Retorna resumen para logging

### 3. Database Layer

**Responsabilidad:** Gestión de persistencia de datos

#### Modelos (models.py)

**BotConfig (Singleton)**
- `id` - Siempre 1 (singleton)
- `vip_channel_id` - ID del canal VIP
- `free_channel_id` - ID del canal Free
- `wait_time_minutes` - Tiempo espera para Free
- `vip_reactions` - JSON array de emojis para VIP
- `free_reactions` - JSON array de emojis para Free
- `subscription_fees` - JSON object con tarifas
- `created_at`, `updated_at` - Timestamps

**InvitationToken**
- `token` - Único, 16 caracteres, indexed
- `generated_by` - User ID del admin que creó
- `created_at` - Timestamp de creación
- `duration_hours` - Duración en horas (default 24)
- `used` - Boolean, indexed
- `used_by` - User ID que canjeó (null si no usado)
- `used_at` - Timestamp de uso (null si no usado)
- **Relación:** 1 Token → Many VIPSubscribers
- **Métodos:**
  - `is_expired()` - Verifica si token expiró
  - `is_valid()` - Verifica si puede usarse (no usado y no expirado)

**VIPSubscriber**
- `user_id` - ID Telegram, unique, indexed
- `join_date` - Timestamp de suscripción
- `expiry_date` - Fecha de expiración
- `status` - "active" o "expired", indexed
- `token_id` - FK a InvitationToken
- **Métodos:**
  - `is_expired()` - Verifica si suscripción expiró
  - `days_remaining()` - Retorna días restantes (negativo si expirado)

**FreeChannelRequest**
- `user_id` - ID Telegram, indexed
- `request_date` - Timestamp de solicitud
- `processed` - Boolean, indexed
- `processed_at` - Timestamp de procesamiento (null si no procesado)
- **Métodos:**
  - `minutes_since_request()` - Minutos desde solicitud
  - `is_ready(wait_time_minutes)` - Verifica si cumplió tiempo espera

#### Engine y Sesiones (engine.py)

**Inicialización:**
```python
init_db()
├── Crear engine con aiosqlite
├── Configurar SQLite (WAL mode, cache 64MB, PRAGMA)
├── Crear tablas
├── Crear session factory
└── Crear BotConfig inicial
```

**Context Manager:**
```python
async with get_session() as session:
    # Usar session
    # commit automático si éxito
    # rollback automático si error
```

**Configuración SQLite para Termux:**
- `PRAGMA journal_mode=WAL` - Write-Ahead Logging para concurrencia
- `PRAGMA synchronous=NORMAL` - Balance performance/seguridad
- `PRAGMA cache_size=-64000` - Cache de 64MB
- `PRAGMA foreign_keys=ON` - Integridad referencial

### 4. Handlers

**Responsabilidad:** Procesar comandos y callbacks de usuarios

**Estructura:**
```
handlers/
├── admin/
│   ├── __init__.py
│   ├── main.py         # /admin - Menú principal (pendiente)
│   ├── vip.py          # Gestión VIP (pendiente)
│   └── free.py         # Gestión Free (pendiente)
└── user/
    ├── __init__.py
    ├── start.py        # /start - Bienvenida (pendiente)
    ├── vip_flow.py     # Flujo canje token (pendiente)
    └── free_flow.py    # Flujo solicitud Free (pendiente)
```

**Patrón de Handler (será usado en fases siguientes):**
```python
@router.message.command("command")
async def command_handler(message: Message, session: AsyncSession) -> None:
    """
    Descripción del handler.

    Args:
        message: Objeto Message de Aiogram
        session: AsyncSession inyectada por middleware
    """
    try:
        # Validar permisos si es necesario
        if not Config.is_admin(message.from_user.id):
            await message.answer("No tienes permisos")
            return

        # Procesar lógica
        # Usar servicios para consultar/actualizar BD

        # Responder usuario
        await message.answer("Respuesta")
    except Exception as e:
        logger.error(f"Error en command_handler: {e}")
        await message.answer("Error procesando comando")
```

### 5. Middlewares

**Responsabilidad:** Interceptar y procesar updates antes de handlers

**Middlewares Planeados:**
- `AdminAuthMiddleware` - Validar que usuario es admin
- `DatabaseMiddleware` - Inyectar AsyncSession en contexto

**Patrón (Fase 1.4):**
```python
class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with get_session() as session:
            data["session"] = session
            return await handler(event, data)
```

### 6. States (FSM)

**Responsabilidad:** Gestionar estado de conversación de usuarios

**Storage:** MemoryStorage (ligero para Termux)

**Estados Planeados:**

**AdminStates:**
- `admin_menu` - Menú principal
- `selecting_token_type` - Eligiendo tipo de token
- `entering_token_duration` - Ingresando duración
- `confirming_token_creation` - Confirmando creación
- `viewing_token_list` - Visualizando tokens
- etc.

**UserStates:**
- `user_menu` - Menú principal
- `entering_vip_token` - Ingresando token VIP
- `requesting_free_access` - Solicitando acceso Free
- etc.

### 7. Services

**Responsabilidad:** Lógica de negocio reutilizable

**Servicios Disponibles:**

```
services/
├── container.py        # Contenedor de servicios (DI + Lazy Loading)
├── subscription.py     # Gestión de suscripciones VIP/Free
├── channel.py          # Gestión de canales Telegram
├── config.py           # Config service
└── stats.py            # Estadísticas
```

#### Service Container (T6)

Implementación del patrón Dependency Injection + Lazy Loading para reducir consumo de memoria en Termux:

**Arquitectura:**
```python
class ServiceContainer:
    def __init__(self, session: AsyncSession, bot: Bot):
        self._session = session
        self._bot = bot

        # Servicios (cargados lazy)
        self._subscription_service = None
        self._channel_service = None
        self._config_service = None
        self._stats_service = None

    @property
    def subscription(self):
        """Carga lazy el servicio de suscripciones"""
        if self._subscription_service is None:
            from bot.services.subscription import SubscriptionService
            self._subscription_service = SubscriptionService(self._session, self._bot)
        return self._subscription_service

    # Similar para otros servicios...

    def get_loaded_services(self) -> list[str]:
        """Retorna lista de servicios ya cargados en memoria"""
        # Útil para debugging y monitoreo de uso de memoria
```

**Características:**
- **Lazy Loading:** servicios se instancian solo cuando se acceden por primera vez
- **Optimización de Memoria:** reduce el consumo inicial de memoria en Termux
- **4 servicios disponibles:** subscription, channel, config, stats
- **Monitoreo:** método `get_loaded_services()` para tracking de uso de memoria
- **Precarga opcional:** `preload_critical_services()` para servicios críticos

**Uso:**
```python
container = ServiceContainer(session, bot)

# Primera vez: carga el servicio (lazy loading)
token = await container.subscription.generate_token(...)

# Segunda vez: reutiliza instancia ya cargada
result = await container.subscription.validate_token(...)
```

#### Subscription Service (T7)

Gestión completa de suscripciones VIP y Free con 14 métodos asíncronos:

**Responsabilidades:**
- Generación de tokens de invitación VIP
- Validación y canje de tokens
- Gestión de suscriptores VIP (crear, extender, expirar)
- Gestión de solicitudes Free (crear, procesar)
- Limpieza automática de datos antiguos

**Flujos Implementados:**

**VIP Flow:**
```
1. Admin genera token → generate_vip_token()
2. Usuario canjea token → redeem_vip_token()
3. Usuario recibe invite link → create_invite_link()
4. Suscripción expira automáticamente → expire_vip_subscribers() (background)
```

**Free Flow:**
```
1. Usuario solicita acceso → create_free_request()
2. Espera N minutos
3. Sistema procesa cola → process_free_queue() (background)
4. Usuario recibe invite link
```

**Características principales:**
- **Tokens VIP:** 16 caracteres alfanuméricos, únicos, expiran después de N horas
- **Cola Free:** sistema de espera configurable con `wait_time`
- **Invite links únicos:** enlaces de un solo uso (`member_limit=1`)
- **Gestión de usuarios:** creación, extensión y expiración automática de suscripciones
- **Limpieza automática:** elimina datos antiguos para mantener rendimiento

**Ejemplo de uso:**
```python
# Generar token VIP
token = await container.subscription.generate_vip_token(
    generated_by=admin_user_id,
    duration_hours=24
)

# Validar token
is_valid, message, token_obj = await container.subscription.validate_token("token_string")

# Canjear token VIP
success, message, subscriber = await container.subscription.redeem_vip_token(
    token_str="token_string",
    user_id=user_id
)

# Crear solicitud Free
request = await container.subscription.create_free_request(user_id)

# Procesar cola Free
processed_requests = await container.subscription.process_free_queue(
    wait_time_minutes=Config.WAIT_TIME_MINUTES
)

# Crear invite link único
invite_link = await container.subscription.create_invite_link(
    channel_id="-1001234567890",
    user_id=user_id,
    expire_hours=1
)
```

#### Channel Service (T8)

Gestión completa de canales VIP y Free con verificación de permisos y envío de publicaciones:

**Responsabilidades:**
- Configuración de canales VIP y Free con validación de existencia
- Verificación de permisos del bot (can_invite_users, can_post_messages)
- Envío de contenido a canales (texto, fotos, videos)
- Reenvío y copia de mensajes entre chats y canales
- Validación de configuración de canales

**Flujos Implementados:**

**Setup Channel Flow:**
```
1. Admin configura canal → setup_vip_channel() o setup_free_channel()
2. Bot verifica que el canal existe
3. Bot verifica que es admin del canal
4. Bot verifica permisos necesarios (can_invite_users, can_post_messages)
5. Canal guardado en BotConfig
```

**Send to Channel Flow:**
```
1. Admin/envío automático → send_to_channel()
2. Bot determina tipo de contenido (texto, foto, video)
3. Bot envía mensaje al canal
4. Retorno de resultado exitoso/error
```

**Permissions Verification Flow:**
```
1. Bot obtiene información del miembro → get_chat_member()
2. Verifica que sea admin o creador
3. Verifica permisos específicos (can_invite_users, can_post_messages)
4. Retorna mensaje detallado de permisos faltantes
```

**Características principales:**
- **Configuración segura:** verificación de existencia y permisos antes de guardar
- **Permisos completos:** verifica can_invite_users y can_post_messages
- **Soporte multimedia:** envío de texto, fotos y videos
- **Operaciones avanzadas:** reenvío y copia de mensajes
- **Validación robusta:** verificaciones de formato e ID de canal

**Ejemplos de uso:**
```python
# Configuración de canal VIP
success, message = await container.channel.setup_vip_channel("-1001234567890")
if success:
    print(f"Canal VIP configurado: {message}")
else:
    print(f"Error en configuración: {message}")

# Configuración de canal Free
success, message = await container.channel.setup_free_channel("-1009876543210")
if success:
    print(f"Canal Free configurado: {message}")
else:
    print(f"Error en configuración: {message}")

# Verificación de permisos del bot
is_valid, perm_message = await container.channel.verify_bot_permissions("-1001234567890")
if is_valid:
    print("Bot tiene todos los permisos necesarios")
else:
    print(f"Permisos insuficientes: {perm_message}")

# Envío de mensaje de texto al canal
sent_success, sent_message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="¡Nueva publicación en el canal VIP!",
    parse_mode="HTML"
)
if sent_success:
    print(f"Mensaje enviado: {sent_message}")
else:
    print(f"Error al enviar: {sent_message}")

# Envío de foto con texto al canal
sent_success, sent_message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="Foto destacada del día",
    photo="AgACAgQAAxkBAA...",
    parse_mode="HTML"
)

# Envío de video con descripción
sent_success, sent_message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="Video promocional",
    video="BAACAgQAAxkBAA...",
    parse_mode="HTML"
)

# Reenvío de mensaje a canal
forward_success, forward_message = await container.channel.forward_to_channel(
    channel_id="-1001234567890",
    from_chat_id=-1009876543210,
    message_id=123
)

# Copia de mensaje a canal (sin firma de origen)
copy_success, copy_message = await container.channel.copy_to_channel(
    channel_id="-1001234567890",
    from_chat_id=-1009876543210,
    message_id=123
)

# Verificación de configuración de canales
is_vip_configured = await container.channel.is_vip_channel_configured()
is_free_configured = await container.channel.is_free_channel_configured()
print(f"Canales configurados - VIP: {is_vip_configured}, Free: {is_free_configured}")

# Obtención de IDs de canales
vip_channel_id = await container.channel.get_vip_channel_id()
free_channel_id = await container.channel.get_free_channel_id()

if vip_channel_id:
    print(f"Canal VIP ID: {vip_channel_id}")
if free_channel_id:
    print(f"Canal Free ID: {free_channel_id}")

# Obtención de información del canal
channel_info = await container.channel.get_channel_info("-1001234567890")
if channel_info:
    print(f"Nombre del canal: {channel_info.title}")
    print(f"Tipo de canal: {channel_info.type}")

member_count = await container.channel.get_channel_member_count("-1001234567890")
if member_count:
    print(f"Número de miembros: {member_count}")
```

#### Config Service (T9)

Gestión de configuración global del bot con funcionalidades clave para administrar la configuración centralizada:

**Responsabilidades:**
- Obtener/actualizar configuración de BotConfig (singleton)
- Gestionar tiempo de espera Free
- Gestionar reacciones de canales
- Validar que la configuración está completa
- Configurar tarifas de suscripción
- Proporcionar resumen de configuración

**Características principales:**
- **Singleton Pattern:** BotConfig es un registro único (id=1) que almacena toda la configuración global
- **Tiempo de espera configurable:** Gestión flexible del tiempo de espera para acceso al canal Free
- **Reacciones personalizables:** Configuración de emojis para reacciones en canales VIP y Free
- **Validación integral:** Verificación completa de la configuración para asegurar funcionamiento óptimo
- **Tarifas de suscripción:** Soporte para múltiples tipos de tarifas (mensual, anual, etc.)
- **Resumen de configuración:** Información detallada del estado de la configuración para administradores

**Flujos Implementados:**

**Get Configuration Flow:**
```
1. Servicio solicita configuración → get_config()
2. Consulta a BD por registro con id=1
3. Retorna objeto BotConfig
4. Validación de existencia (debe existir siempre)
```

**Set Wait Time Flow:**
```
1. Admin define tiempo de espera → set_wait_time(minutes)
2. Validación: minutos >= 1
3. Actualiza campo wait_time_minutes en BotConfig
4. Guarda cambios en BD
5. Log de cambio realizado
```

**Set Channel Reactions Flow:**
```
1. Admin define reacciones → set_vip_reactions() o set_free_reactions()
2. Validación: lista no vacía, máximo 10 elementos
3. Actualiza campo correspondiente (vip_reactions o free_reactions)
4. Guarda cambios en BD
5. Log de reacciones actualizadas
```

**Validation Flow:**
```
1. Verificación de configuración completa → is_fully_configured()
2. Valida:
   - Canal VIP configurado (vip_channel_id != null)
   - Canal Free configurado (free_channel_id != null)
   - Tiempo de espera >= 1 minuto
3. Retorna booleano indicando estado
```

**Ejemplos de uso:**
```python
# Obtención de configuración global
config = await container.config.get_config()
print(f"Canal VIP: {config.vip_channel_id}")
print(f"Canal Free: {config.free_channel_id}")
print(f"Tiempo de espera: {config.wait_time_minutes} minutos")

# Configuración de tiempos de espera
current_wait_time = await container.config.get_wait_time()
print(f"Tiempo actual de espera: {current_wait_time} minutos")
await container.config.set_wait_time(15)  # 15 minutos de espera

# Gestión de reacciones de canales
current_vip_reactions = await container.config.get_vip_reactions()
print(f"Reacciones VIP actuales: {current_vip_reactions}")

# Actualizar reacciones VIP
await container.config.set_vip_reactions(["👍", "❤️", "🔥", "🎉"])
await container.config.set_free_reactions(["✅", "✔️", "☑️"])

# Configuración de tarifas de suscripción
current_fees = await container.config.get_subscription_fees()
print(f"Tarifas actuales: {current_fees}")

# Actualizar tarifas de suscripción
await container.config.set_subscription_fees({
    "monthly": 10.0,
    "yearly": 100.0,
    "lifetime": 500.0
})

# Validación de configuración completa
is_configured = await container.config.is_fully_configured()
if is_configured:
    print("Bot completamente configurado")
else:
    status = await container.config.get_config_status()
    print(f"Faltan elementos: {', '.join(status['missing'])}")

# Obtención de resumen de configuración
summary = await container.config.get_config_summary()
print(summary)

# Resetear a valores por defecto (advertencia: borra configuración de canales)
await container.config.reset_to_defaults()
```

### 8. Background Tasks

**Responsabilidad:** Tareas programadas asincrónicas

**Tareas Planeadas:**
- `cleanup_expired_subscriptions()` - Marcar VIPs como expirados
- `process_free_queue()` - Procesar cola de Free requests
- `cleanup_expired_tokens()` - Eliminar tokens expirados

**Patrón:**
```python
@scheduler.scheduled_job('interval', minutes=60)
async def cleanup_task():
    async with get_session() as session:
        # Procesar
        pass
```

### 9. Utilities

**Responsabilidad:** Funciones y utilidades comunes

**Módulos Planeados:**
- `keyboards.py` - Factory de inline/reply keyboards
- `validators.py` - Funciones de validación (token format, user_id, etc.)

## Flujo de Datos

### Flujo de Comando Admin

```
1. Admin envía /admin
   └→ Handler recibe Update

2. Dispatcher procesa update
   ├→ AdminAuthMiddleware valida permisos
   ├→ DatabaseMiddleware inyecta session
   └→ Dispatcher routea a handler

3. Handler procesa comando
   ├→ Consulta datos con session
   ├→ Llama servicios si es necesario
   ├→ Responde con keyboard inline
   └→ Transición de estado FSM

4. Usuario hace click en botón
   └→ CallbackQuery enviado

5. CallbackHandler procesa callback
   ├→ Valida acción
   ├→ Actualiza BD
   └→ Responde usuario
```

### Flujo de Creación de Token

```
Sequence: Admin → Bot → Database → Telegram API

1. Admin: /admin → "Generar Token"
   │
2. Bot: ¿Token para 24h? [Si] [No] [Cancelar]
   │
3. Admin: Presiona [Si]
   │
4. Bot:
   ├→ Generar token único (16 caracteres)
   ├→ Insertar en BD: InvitationToken
   └→ Responder: "Token: ABC123XYZ456 - Válido por 24h"
```

### Flujo de Canje de Token

```
Sequence: Usuario → Bot → Database → VIP Channel

1. Usuario: /vip
   │
2. Bot: "Ingresa tu token VIP:"
   │ [FSM: waiting_for_token]
   │
3. Usuario: "ABC123XYZ456"
   │
4. Bot:
   ├→ Buscar token en BD
   ├→ Validar: no usado, no expirado
   ├→ Si válido:
   │  ├→ Crear VIPSubscriber
   │  ├→ Marcar token como usado
   │  ├→ Invitar usuario a canal VIP
   │  └→ "Bienvenido! Acceso VIP válido por 24h"
   └→ Si inválido:
      └→ "Token inválido o expirado"
```

### Flujo de Solicitud Free

```
Sequence: Usuario → Bot → Database → Queue → Timer → Invite

1. Usuario: /free
   │
2. Bot:
   ├→ Crear FreeChannelRequest
   ├→ Iniciar timer (DEFAULT_WAIT_TIME_MINUTES)
   └→ "Esperando... [5 minutos]"

3. [Background Task: Cada 5 minutos]
   ├→ Buscar requests "ready"
   ├→ Invitar usuarios a Free channel
   ├→ Marcar como processed
   └→ Log: "Usuario X invitado a Free"
```

## Modelos de Datos

### Diagrama Entidad-Relación

```
┌──────────────────────────┐
│     BotConfig (1)        │
│──────────────────────────│
│ id: int (1)              │
│ vip_channel_id: str      │
│ free_channel_id: str     │
│ wait_time_minutes: int   │
│ vip_reactions: JSON      │
│ free_reactions: JSON     │
│ subscription_fees: JSON  │
│ created_at: datetime     │
│ updated_at: datetime     │
└──────────────────────────┘

┌──────────────────────────┐       1:N       ┌────────────────────┐
│  InvitationToken         │◄──────────────┼─│  VIPSubscriber     │
│──────────────────────────│                 │────────────────────│
│ id: int (PK)             │                 │ id: int (PK)       │
│ token: str (UNIQUE)      │                 │ user_id: int (UQ)  │
│ generated_by: int        │                 │ join_date: dt      │
│ created_at: datetime     │                 │ expiry_date: dt    │
│ duration_hours: int      │                 │ status: str        │
│ used: bool               │                 │ token_id: int (FK) │
│ used_by: int (null)      │                 └────────────────────┘
│ used_at: datetime (null) │
└──────────────────────────┘

┌────────────────────────────────────┐
│    FreeChannelRequest              │
│────────────────────────────────────│
│ id: int (PK)                       │
│ user_id: int                       │
│ request_date: datetime             │
│ processed: bool                    │
│ processed_at: datetime (null)      │
└────────────────────────────────────┘
```

### Índices Implementados

Para optimizar queries comunes:

```sql
-- InvitationToken
CREATE INDEX idx_token_used_created
ON invitation_tokens(used, created_at);

-- VIPSubscriber
CREATE INDEX idx_status_expiry
ON vip_subscribers(status, expiry_date);

-- FreeChannelRequest
CREATE INDEX idx_user_date
ON free_channel_requests(user_id, request_date);

CREATE INDEX idx_processed_date
ON free_channel_requests(processed, request_date);
```

## Patrones de Arquitectura

### 1. Dependency Injection

Los handlers reciben dependencias inyectadas vía middlewares:

```python
async def handler(message: Message, session: AsyncSession):
    # session inyectada por DatabaseMiddleware
    pass
```

### 2. Service Layer

La lógica de negocio reside en servicios, no en handlers:

```python
# Handler: Orquesta y responde
async def handler(message: Message, session: AsyncSession):
    service = TokenService(session)
    token = await service.generate_token(24)
    await message.answer(f"Token: {token}")

# Service: Implementa lógica
class TokenService:
    async def generate_token(self, duration_hours: int) -> str:
        # Lógica de generación
        pass
```

### 3. Repository Pattern (planeado)

Para aislar lógica de acceso a datos:

```python
class TokenRepository:
    async def find_by_token(self, token: str) -> InvitationToken:
        pass

    async def find_valid_tokens(self) -> List[InvitationToken]:
        pass
```

### 4. Context Managers

Para garantizar limpieza de recursos:

```python
async with get_session() as session:
    # Auto-commit si éxito
    # Auto-rollback si error
    # Auto-close al salir
```

## Flujo de Inicialización

```
main.py
├─ Config.setup_logging()
│  └─ Configura logging según LOG_LEVEL
│
├─ asyncio.run(main())
│  ├─ Bot(token, parse_mode="HTML")
│  ├─ MemoryStorage()
│  ├─ Dispatcher(storage)
│  │
│  ├─ on_startup()
│  │  ├─ Config.validate()
│  │  ├─ init_db()
│  │  │  ├─ create_async_engine()
│  │  │  ├─ PRAGMA journal_mode=WAL
│  │  │  ├─ create_all(Base.metadata)
│  │  │  ├─ async_sessionmaker()
│  │  │  └─ _ensure_bot_config_exists()
│  │  ├─ register_handlers()
│  │  ├─ register_middlewares()
│  │  └─ notify_admins("Bot online")
│  │
│  ├─ dp.start_polling()
│  │  └─ [Loop: Procesar updates]
│  │
│  └─ on_shutdown()
│     ├─ stop_background_tasks()
│     ├─ close_db()
│     └─ notify_admins("Bot offline")
```

## Consideraciones de Rendimiento

### Para Termux (Android)

1. **MemoryStorage vs RedisStorage** - MemoryStorage es ligero pero se pierde al reiniciar
2. **Polling vs Webhook** - Polling es más simple pero consume más energía
3. **Database Connection Pool** - NullPool para SQLite (sin pooling)
4. **Logging Level** - INFO en producción, DEBUG solo en desarrollo
5. **Task Scheduling** - APScheduler con intervalos razonables (no < 5 min)

### Índices de Búsqueda

Se implementaron índices compuestos para queries comunes:
- Buscar tokens válidos: `(used, created_at)`
- Buscar suscriptores por estado: `(status, expiry_date)`
- Buscar requests pendientes: `(processed, request_date)`

## Seguridad

### 1. Autenticación

- Validación de ADMIN_USER_IDS en config.py
- AdminAuthMiddleware valida permisos antes de handlers

### 2. Base de Datos

- Foreign keys habilitadas
- SQLite con WAL mode para integridad
- Índices en columnas sensibles (user_id, status)

### 3. Tokens

- 16 caracteres alfanuméricos (192 bits de entropía)
- Duración limitada (expiran después de X horas)
- Marca de "usado" previene reutilización

### 4. Secretos

- BOT_TOKEN en .env (NO commitear)
- Logging con preview de token (primeros 10 caracteres)

## Escalabilidad Futura

### ONDA 2+

1. **Servicios Microservicios** - Separar en múltiples bots
2. **Redis Cache** - Cache de sesiones y config
3. **Webhook Updates** - Reemplazar polling
4. **PostgreSQL** - Reemplazar SQLite para múltiples conexiones
5. **Container + Kubernetes** - Deploy en producción

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
