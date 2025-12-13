# PROYECTO TELEGRAM BOT VIP/FREE - ONDA 1
## Bot de gestión de canales VIP y Free con cola de espera

Proyecto en desarrollo activo siguiendo flujo ONDA 1.

═══════════════════════════════════════════════════════════════
# CONTEXTO TÉCNICO UNIFICADO - ONDA 1
═══════════════════════════════════════════════════════════════

## 🛠️ STACK TECNOLÓGICO

```yaml
Backend: Python 3.11+
Framework: Aiogram 3.4.1 (async)
Base de Datos: SQLite 3.x con WAL mode
ORM: SQLAlchemy 2.0.25 (Async engine)
Driver DB: aiosqlite 0.19.0
Scheduler: APScheduler 3.10.4
Environment: python-dotenv 1.0.0
Testing: pytest 7.4+ + pytest-asyncio 0.21+

Librerías Clave:
  - aiogram: 3.4.1 - Framework bot Telegram async
  - sqlalchemy: 2.0.25 - ORM con soporte async/await
  - aiosqlite: 0.19.0 - Driver SQLite async
  - APScheduler: 3.10.4 - Tareas programadas en background
  - python-dotenv: 1.0.0 - Gestión de variables de entorno
```

## 📁 ESTRUCTURA DE PROYECTO

```
/
├── main.py                      # Entry point del bot
├── config.py                    # Configuración centralizada
├── requirements.txt             # Dependencias pip
├── .env                         # Variables de entorno (NO commitear)
├── .env.example                 # Template para .env
├── README.md                    # Documentación
├── bot.db                       # SQLite database (generado)
│
└── bot/
    ├── __init__.py
    │
    ├── database/
    │   ├── __init__.py
    │   ├── base.py             # Base declarativa SQLAlchemy
    │   ├── engine.py           # Factory de engine y sesiones
    │   └── models.py           # Modelos: BotConfig, VIPSubscriber, etc.
    │
    ├── services/
    │   ├── __init__.py
    │   ├── container.py        # Dependency Injection Container
    │   ├── subscription.py     # Lógica VIP/Free/Tokens
    │   ├── channel.py          # Gestión canales Telegram
    │   └── config.py           # Configuración del bot
    │
    ├── handlers/
    │   ├── __init__.py
    │   ├── admin/
    │   │   ├── __init__.py
    │   │   ├── main.py         # /admin - Menú principal
    │   │   ├── vip.py          # Submenú gestión VIP
    │   │   └── free.py         # Submenú gestión Free
    │   └── user/
    │       ├── __init__.py
    │       ├── start.py        # /start - Bienvenida
    │       ├── vip_flow.py     # Flujo canje token
    │       └── free_flow.py    # Flujo solicitud Free
    │
    ├── middlewares/
    │   ├── __init__.py
    │   ├── admin_auth.py       # Validación permisos admin
    │   └── database.py         # Inyección de sesión DB
    │
    ├── states/
    │   ├── __init__.py
    │   ├── admin.py            # FSM states para admin
    │   └── user.py             # FSM states para usuarios
    │
    ├── utils/
    │   ├── __init__.py
    │   ├── keyboards.py        # Factory de inline keyboards
    │   └── validators.py       # Funciones de validación
    │
    └── background/
        ├── __init__.py
        └── tasks.py            # Tareas programadas (cleanup, expiración)
```

## 🎨 CONVENCIONES

```python
# Naming:
# - Clases: PascalCase (VIPSubscriber, SubscriptionService)
# - Funciones/métodos: snake_case (generate_token, check_expiry)
# - Constantes: UPPER_SNAKE_CASE (DEFAULT_WAIT_TIME, MAX_TOKEN_LENGTH)
# - Archivos: snake_case (admin_auth.py, vip_flow.py)

# Imports:
# - Estándar → Third-party → Local
# - Ordenados alfabéticamente en cada grupo

# Async:
# - TODOS los handlers son async def
# - TODOS los métodos de services son async def
# - Usar await para llamadas DB y API Telegram

# Error Handling:
# - Try-except en handlers (nunca dejar crashear el bot)
# - Logger en cada módulo: logger = logging.getLogger(__name__)
# - Niveles: DEBUG (desarrollo), INFO (eventos), WARNING (problemas no críticos), ERROR (fallos), CRITICAL (bot no operativo)

# Type Hints:
# - Obligatorio en signatures de funciones
# - Usar Optional[T] para valores opcionales
# - Usar Union[T1, T2] cuando hay múltiples tipos

# Docstrings:
# - Google Style
# - En todas las clases y funciones públicas
```

═══════════════════════════════════════════════════════════════
# FLUJO DE DESARROLLO - ONDA 1
═══════════════════════════════════════════════════════════════

## 📋 FASES Y TAREAS

### FASE 1.1: Base de Datos (T1-T5) ✅ COMPLETADA
Base de datos con modelos y configuración inicial.

- **T1:** Base declarativa SQLAlchemy
- **T2:** Models (BotConfig, VIPSubscriber, InvitationToken, FreeChannelRequest)
- **T3:** Engine async y factory de sesiones
- **T4:** Inicialización automática de BD
- **T5:** Fixtures de testing

Status: ✅ Completado - 5 tareas, ~250 líneas

---

### FASE 1.2: SERVICIOS CORE (T6-T9) ✅ COMPLETADA
Capa de servicios con lógica de negocio centralizada.

#### T6: Service Container (Dependency Injection)
**Archivo:** `bot/services/container.py` (171 líneas)
**Patrón:** DI + Lazy Loading
**Responsabilidades:**
- Centralizar instanciación de servicios
- Lazy loading transparente (solo carga lo que usa)
- Inyectar session y bot a todos los servicios
- Monitoreo de memoria (get_loaded_services)

**Métodos:**
```
@property subscription     → SubscriptionService
@property channel         → ChannelService
@property config          → ConfigService
@property stats           → StatsService (future)
get_loaded_services()     → List[str]
preload_critical_services() → None (async)
```

**Integración:**
```python
container = ServiceContainer(session, bot)
await container.subscription.generate_vip_token(...)
await container.channel.setup_vip_channel(...)
```

---

#### T7: Subscription Service (VIP/Free/Tokens)
**Archivo:** `bot/services/subscription.py` (586 líneas)
**Responsabilidades:**
- Generación de tokens únicos y seguros
- Validación y canje de tokens
- Gestión de suscriptores VIP (crear, extender, expirar)
- Gestión de solicitudes Free (crear, procesar, limpiar)
- Invite links de un solo uso

**Métodos Tokens VIP:**
```
generate_vip_token(generated_by, duration_hours) → InvitationToken
validate_token(token_str) → (bool, str, Optional[InvitationToken])
redeem_vip_token(token_str, user_id) → (bool, str, Optional[VIPSubscriber])
```

**Métodos VIP:**
```
get_vip_subscriber(user_id) → Optional[VIPSubscriber]
is_vip_active(user_id) → bool
expire_vip_subscribers() → int (background task)
kick_expired_vip_from_channel(channel_id) → int (background task)
get_all_vip_subscribers(status, limit, offset) → List[VIPSubscriber]
```

**Métodos Free:**
```
create_free_request(user_id) → FreeChannelRequest
get_free_request(user_id) → Optional[FreeChannelRequest]
process_free_queue(wait_time_minutes) → List[FreeChannelRequest] (background)
cleanup_old_free_requests(days_old) → int
```

**Métodos Invite:**
```
create_invite_link(channel_id, user_id, expire_hours) → ChatInviteLink
```

---

#### T8: Channel Service (Gestión de Canales)
**Archivo:** `bot/services/channel.py` (420 líneas)
**Responsabilidades:**
- Configuración de canales VIP y Free
- Verificación de permisos del bot
- Envío de mensajes/publicaciones
- Validación de existencia de canales

**Métodos Setup:**
```
setup_vip_channel(channel_id) → (bool, str)
setup_free_channel(channel_id) → (bool, str)
verify_bot_permissions(channel_id) → (bool, str)
```

**Métodos Verificación:**
```
is_vip_channel_configured() → bool
is_free_channel_configured() → bool
get_vip_channel_id() → Optional[str]
get_free_channel_id() → Optional[str]
```

**Métodos Envío:**
```
send_to_channel(channel_id, text, photo, video, **kwargs) → (bool, str, Optional[Message])
forward_to_channel(channel_id, from_chat_id, message_id) → (bool, str)
copy_to_channel(channel_id, from_chat_id, message_id) → (bool, str)
```

**Métodos Info:**
```
get_channel_info(channel_id) → Optional[Chat]
get_channel_member_count(channel_id) → Optional[int]
```

---

#### T9: Config Service (Configuración Global)
**Archivo:** `bot/services/config.py` (349 líneas)
**Patrón:** Singleton (BotConfig id=1)
**Responsabilidades:**
- Gestión centralizada de configuración
- Validación de configuración completa
- Getters/setters con persistencia inmediata

**Métodos Getters:**
```
get_config() → BotConfig
get_wait_time() → int
get_vip_channel_id() → Optional[str]
get_free_channel_id() → Optional[str]
get_vip_reactions() → List[str]
get_free_reactions() → List[str]
get_subscription_fees() → Dict[str, float]
```

**Métodos Setters (con validación):**
```
set_wait_time(minutes: int) → None  # Valida >= 1
set_vip_reactions(reactions: List[str]) → None  # Valida 1-10
set_free_reactions(reactions: List[str]) → None  # Valida 1-10
set_subscription_fees(fees: Dict) → None  # Valida positivos
```

**Métodos Validación:**
```
is_fully_configured() → bool
get_config_status() → Dict[str, any]
get_config_summary() → str  # HTML para Telegram
```

**Utilidades:**
```
reset_to_defaults() → None
```

---

**FASE 1.2 ESTADÍSTICAS:**
- Archivos creados: 4 services + 1 __init__.py
- Líneas de código: ~1,526
- Métodos async: 39
- Tests validación: 39+
- Patrón: DI + Singleton + Lazy Loading

---

### FASE 1.3: HANDLERS ADMIN BÁSICOS (T10-T12) 🔄 EN PROGRESO

#### T10: Middlewares (AdminAuth + Database) ✅ COMPLETADO
**Archivo:** `bot/middlewares/` (155 líneas + tests)
**Patrón:** BaseMiddleware + DI
**Responsabilidades:**
- AdminAuthMiddleware: Validación de permisos de administrador
- DatabaseMiddleware: Inyección de sesión de base de datos

**Implementación:**
```
bot/middlewares/
├── admin_auth.py       → AdminAuthMiddleware (87 líneas)
├── database.py         → DatabaseMiddleware (68 líneas)
└── __init__.py         → Exports
```

**AdminAuthMiddleware:**
- Verifica `Config.is_admin(user.id)` para Message y CallbackQuery
- Envía mensaje de error si no es admin (HTML para Message, alert para CallbackQuery)
- No ejecuta handler si no es admin (retorna None)
- Logging: WARNING para intentos denegados, DEBUG para admins verificados

**DatabaseMiddleware:**
- Crea AsyncSession usando `get_session()` (context manager)
- Inyecta sesión en `data["session"]` para que handlers accedan automáticamente
- Manejo automático de commit/rollback vía SessionContextManager
- Logging: ERROR si ocurre excepción en handler

**Tests Validación:** ✅ 3 tests funcionales
- Admin pass test ✅
- Non-admin blocked test ✅
- Session injection test ✅

---

#### T11: Estados FSM para Admin y User ✅ COMPLETADO
**Archivo:** `bot/states/` (107 líneas + tests)
**Patrón:** StatesGroup + State + Docstrings explicando flujo
**Responsabilidades:**
- Definir estados FSM para flujos multi-paso
- Agrupar lógicamente estados relacionados
- Documentar el flujo completo en docstrings

**Implementación:**
```
bot/states/
├── admin.py         → ChannelSetupStates, WaitTimeSetupStates, BroadcastStates
├── user.py         → TokenRedemptionStates, FreeAccessStates
└── __init__.py     → Exports
```

**Estados Admin:**
- ChannelSetupStates: 2 estados
  * waiting_for_vip_channel: Admin reenvía mensaje del canal VIP
  * waiting_for_free_channel: Admin reenvía mensaje del canal Free

- WaitTimeSetupStates: 1 estado
  * waiting_for_minutes: Admin envía número de minutos

- BroadcastStates: 2 estados
  * waiting_for_content: Admin envía contenido (texto, foto, video)
  * waiting_for_confirmation: Admin confirma envío (opcional)

**Estados User:**
- TokenRedemptionStates: 1 estado
  * waiting_for_token: Usuario envía token a canjear

- FreeAccessStates: 1 estado
  * waiting_for_approval: Usuario con solicitud pendiente

**Tests Validación:** ✅ Todos pasaron
- ✅ Admin states (ChannelSetupStates, WaitTimeSetupStates, BroadcastStates)
- ✅ User states (TokenRedemptionStates, FreeAccessStates)
- ✅ Exports en __init__.py
- ✅ State strings correctos
- Total: 5 StatesGroup, 7 States

---

#### T12: Handler /admin (Menú Principal) ✅ COMPLETADO
**Archivo:** `bot/handlers/admin/main.py` (157 líneas) + `bot/utils/keyboards.py` (95 líneas)
**Patrón:** Router + Middlewares + Magic Filters + InlineKeyboards
**Responsabilidades:**
- Crear menú principal de administración
- Navegar entre submenús
- Mostrar estado de configuración

**Implementación:**
```
bot/handlers/admin/
├── main.py              → cmd_admin, callback_admin_main, callback_admin_config
└── __init__.py          → Export de admin_router

bot/utils/
├── keyboards.py         → Factory functions para keyboards
└── __init__.py          → (ya existe)
```

**Keyboards Factory:**
- `create_inline_keyboard()`: Función base para crear keyboards
- `admin_main_menu_keyboard()`: Menú principal (3 opciones)
- `back_to_main_menu_keyboard()`: Botón volver
- `yes_no_keyboard()`: Confirmación Sí/No

**Handlers Admin:**
- `cmd_admin`: Handler /admin
  * Verifica estado de configuración
  * Muestra advertencia si faltan elementos
  * Envía nuevo mensaje (no edita)

- `callback_admin_main`: Volver al menú
  * Callback "admin:main"
  * Edita mensaje existente (eficiente)
  * Maneja error "message is not modified"

- `callback_admin_config`: Mostrar configuración
  * Callback "admin:config"
  * Usa get_config_summary() del service
  * Edita mensaje con resumen

**Router Configuration:**
- Nombre: "admin"
- Middlewares en orden correcto:
  * DatabaseMiddleware (inyecta session)
  * AdminAuthMiddleware (valida permisos)
- Aplicados a message y callback_query

**Tests Validación:** ✅ Todos pasaron
- ✅ Keyboards: estructura y callbacks correctos
- ✅ Router: configurado con nombre "admin"
- ✅ Middlewares: registrados en orden
- ✅ Handlers: importables y compilables
- ✅ Manejo de errores de edición

---

- *T13: Handlers VIP y Free (Submenús)*
- *T14-T17: Más handlers y features*

---

### FASE 2: FRONTEND Y DEPLOYMENT (T18+)
Handlers para usuarios, testing completo, y deployment.

---

## 🔄 FLUJO DE DESARROLLO POR TAREA

### Patrón para cada tarea:

1. **Lectura de Prompt**
   - Entender objetivo y contexto
   - Revisar dependencias completadas

2. **Planificación (TodoWrite)**
   - Crear lista de subtareas
   - Definir milestones

3. **Implementación**
   - Crear archivos requeridos
   - Implementar métodos siguiendo especificación
   - Validaciones de input
   - Manejo de errores
   - Logging apropiado
   - Type hints completos
   - Docstrings Google Style

4. **Validación (Testing)**
   - Tests unitarios básicos
   - Validación de comportamiento
   - Manejo de edge cases
   - Verificación de persistencia

5. **Commit sin referencias externas**
   - Mensaje describiendo cambios
   - Listas de métodos implementados
   - Características clave
   - Sin referencias a herramientas externas como Claude code

6. **Documentación (Optional)**
   - Actualizar README.md si aplica
   - Actualizar CLAUDE.md si hay cambios arquitectónicos

---

## 📚 ARCHIVOS CORE COMPLETADOS

### Database (T1-T5)
```
bot/database/
├── base.py           → Base declarativa SQLAlchemy
├── engine.py         → Engine async y SessionFactory
├── models.py         → 4 modelos: BotConfig, VIPSubscriber, InvitationToken, FreeChannelRequest
└── __init__.py       → Exports
```

### Services (T6-T9)
```
bot/services/
├── container.py      → ServiceContainer con DI + Lazy Loading
├── subscription.py   → VIP/Free/Tokens logic
├── channel.py        → Gestión de canales Telegram
├── config.py         → Configuración global (singleton)
└── __init__.py       → Exports de todos los services
```

### Middlewares (T10)
```
bot/middlewares/
├── admin_auth.py     → AdminAuthMiddleware (validación de admin)
├── database.py       → DatabaseMiddleware (inyección de sesión)
└── __init__.py       → Exports de middlewares
```

### States (T11)
```
bot/states/
├── admin.py          → ChannelSetupStates, WaitTimeSetupStates, BroadcastStates
├── user.py           → TokenRedemptionStates, FreeAccessStates
└── __init__.py       → Exports de estados
```

### Handlers (T12-T13)
```
bot/handlers/admin/
├── main.py           → cmd_admin, callback_admin_main, callback_admin_config
├── vip.py            → VIP submenú, setup canal, generación tokens
├── free.py           → Free submenú, setup canal, wait time config
└── __init__.py       → Exports de routers

bot/utils/
├── keyboards.py      → Factory functions para inline keyboards
└── __init__.py       → Exports (si existe)
```

---

## 🎯 INTEGRACIÓN CON SERVICIOS

Todas las capas se comunican a través de **ServiceContainer**:

```
main.py
  ↓
ServiceContainer (DI + Lazy Loading)
  ├─ SubscriptionService (VIP/Free/Tokens)
  ├─ ChannelService (Canales Telegram)
  ├─ ConfigService (Config global)
  └─ StatsService (Future)
    ↓
  Database (SQLAlchemy Async)
    ↓
  SQLite WAL Mode
```

Ejemplo de uso en handlers (próximas fases):
```python
async def handle_setup_vip(message: Message, state: FSMContext):
    # Inyectado por middleware
    container: ServiceContainer = state.context['container']

    # Usar servicios
    success, msg = await container.channel.setup_vip_channel(channel_id)
    if success:
        await container.config.get_config_summary()
        await container.subscription.get_all_vip_subscribers()
```

---

## ✅ CHECKLIST FASE 1.2

- [x] T6: ServiceContainer con lazy loading
- [x] T7: SubscriptionService (VIP/Free/Tokens)
- [x] T8: ChannelService (Gestión canales)
- [x] T9: ConfigService (Configuración global)
- [x] Commits sin referencias externas
- [x] 39+ tests validación
- [x] Documentación técnica

**Status:** ✅ FASE 1.2 COMPLETADA

## ✅ CHECKLIST FASE 1.3

- [x] T10: Middlewares (AdminAuth + Database)
  - [x] AdminAuthMiddleware verifica Config.is_admin()
  - [x] AdminAuthMiddleware envía mensaje de error a no-admins
  - [x] AdminAuthMiddleware NO ejecuta handler si no es admin
  - [x] DatabaseMiddleware inyecta sesión en data["session"]
  - [x] DatabaseMiddleware usa context manager correctamente
  - [x] 3 tests funcionales validación

- [x] T11: Estados FSM para Admin y User
  - [x] ChannelSetupStates (2 estados)
  - [x] WaitTimeSetupStates (1 estado)
  - [x] BroadcastStates (2 estados)
  - [x] TokenRedemptionStates (1 estado)
  - [x] FreeAccessStates (1 estado)
  - [x] Exports en __init__.py
  - [x] Tests validación completos

- [x] T12: Handler /admin (Menú Principal)
  - [x] Keyboard factory (create_inline_keyboard)
  - [x] admin_main_menu_keyboard (3 opciones)
  - [x] back_to_main_menu_keyboard
  - [x] yes_no_keyboard
  - [x] cmd_admin handler
  - [x] callback_admin_main handler
  - [x] callback_admin_config handler
  - [x] Admin router configurado
  - [x] Middlewares en orden correcto
  - [x] Tests validación completos

- [x] T13: Handlers VIP y Free (Setup + Token Generation)
  - [x] Submenú VIP con estado de configuración
  - [x] FSM setup canal VIP (forward → extrae ID → configura)
  - [x] Generación de tokens VIP (24h)
  - [x] Submenú Free con estado de configuración
  - [x] FSM setup canal Free (forward → extrae ID → configura)
  - [x] FSM configuración tiempo de espera (validación >= 1 minuto)
  - [x] Keyboards dinámicos
  - [x] Error handling y validaciones
  - [x] Tests validación completos

#### T13: Handlers VIP y Free (Setup + Token Generation) ✅ COMPLETADO
**Archivo:** `bot/handlers/admin/vip.py` (232 líneas) + `bot/handlers/admin/free.py` (297 líneas)
**Patrón:** FSM + Callbacks + Message Handlers
**Responsabilidades:**
- Submenús VIP y Free adaptables al estado de configuración
- Flujos FSM para setup de canales (forward → extrae ID → configura)
- Generación de tokens VIP
- Configuración de tiempo de espera Free

**Implementación VIP:**
- `callback_vip_menu`: Muestra submenú VIP
- `callback_vip_setup`: Inicia FSM waiting_for_vip_channel
- `process_vip_channel_forward`: Procesa forward, extrae ID, configura
- `callback_generate_vip_token`: Genera token válido 24h
- `vip_menu_keyboard()`: Keyboard dinámico

**Implementación Free:**
- `callback_free_menu`: Muestra submenú Free
- `callback_free_setup`: Inicia FSM waiting_for_free_channel
- `process_free_channel_forward`: Procesa forward, extrae ID, configura
- `callback_set_wait_time`: Inicia FSM waiting_for_minutes
- `process_wait_time_input`: Procesa minutos, valida (>= 1), actualiza
- `free_menu_keyboard()`: Keyboard dinámico

**Flujos FSM:**
```
Setup Canal VIP/Free:
  User: Click "Configurar"
  Bot: Entra estado waiting_for_vip/free_channel
  User: Reenvía forward del canal
  Bot: Extrae forward_from_chat.id → Configura → state.clear()

Setup Wait Time (Free):
  User: Click "Configurar Tiempo"
  Bot: Entra estado waiting_for_minutes
  User: Envía número (ej: 5)
  Bot: Valida >= 1 → Configura → state.clear()
```

**Validaciones:**
- ✅ Forward validation (rechaza texto, requiere canal/supergrupo)
- ✅ Channel type check (channel o supergroup)
- ✅ Token generation (solo si canal VIP configurado)
- ✅ Wait time >= 1 minuto
- ✅ Error recovery (mantener FSM state en errores recuperables)

**Tests Validación:** ✅ Todos pasaron
- ✅ Keyboards VIP y Free (ambos estados)
- ✅ Handlers importables
- ✅ admin_router compartido
- ✅ Callback data correctos
- ✅ FSM States disponibles

---

#### T14: Handlers User (/start, Canje Token, Solicitud Free) ✅ COMPLETADO
**Archivo:** `bot/handlers/user/start.py` (104 líneas) + `bot/handlers/user/vip_flow.py` (173 líneas) + `bot/handlers/user/free_flow.py` (107 líneas)
**Patrón:** FSM + Callbacks + Message Handlers
**Responsabilidades:**
- Punto de entrada para usuarios (/start)
- Detección de rol (admin/VIP/usuario)
- Flujo de canje de tokens VIP
- Flujo de solicitud de acceso Free

**Implementación Start:**
- `cmd_start`: Detecta rol y adapta mensaje
  * Admin → Redirige a /admin
  * VIP activo → Muestra días restantes
  * Usuario normal → Muestra opciones

**Implementación VIP Flow:**
- `callback_redeem_token`: Inicia FSM
- `process_token_input`: Procesa token, crea link (1h, 1 uso)
- `callback_cancel`: Cancela flujo en cualquier momento

**Implementación Free Flow:**
- `callback_request_free`: Crea solicitud Free
  * Verifica que no haya solicitud pendiente
  * Si existe → Muestra tiempo restante
  * Si no → Crea nueva, muestra tiempo de espera

**Flujos Completos:**
```
VIP Token Redeem:
  User: /start → Canjear Token
  Bot: waiting_for_token
  User: Envía token
  Bot: Valida → Crea link → Envía → state.clear()

Free Request:
  User: /start → Solicitar Free
  Bot: Crea solicitud (sin FSM)
  Background task procesará después
```

**Validaciones:**
- ✅ Admin detection (Config.is_admin)
- ✅ VIP active check (días restantes)
- ✅ Canal VIP/Free configured
- ✅ Token validation (redeem_vip_token)
- ✅ Duplicate free request prevention
- ✅ Error handling con mensajes claros

**Tests Validación:** ✅ Todos pasaron
- ✅ Router 'user' configurado
- ✅ Handler /start implementado
- ✅ VIP flow completo
- ✅ Free flow completo
- ✅ Callback data correctos
- ✅ FSM States importables
- ✅ user_router compartido

---


  - [x] Handler /start con detección de rol (admin/VIP/usuario)
  - [x] Flujo VIP: redeem_token → process_token → create_link
  - [x] Flujo Free: request_free con check de duplicados
  - [x] FSM waiting_for_token para validación de tokens
  - [x] Invite links con expiración (1h)
  - [x] Mensajes descriptivos y amigables
  - [x] Manejo de solicitudes duplicadas
  - [x] Tests validación completos

- [ ] T15: Background Tasks (Expulsión VIP, Procesamiento Free)
- [ ] T16-T17: Features finales y deployment

**Status:** ✅ FASE 1.3 COMPLETA (5/5 tareas handlers)
**Próximo:** T15 - Background Tasks (Expulsión VIP, Procesamiento Free)

---

## ✅ CHECKLIST FASE 1.4

- [x] T15: Background Tasks (Expulsión VIP + Procesamiento Free)
  - [x] APScheduler integrado correctamente
  - [x] expire_and_kick_vip_subscribers() implementado
  - [x] process_free_queue() implementado
  - [x] cleanup_old_data() implementado
  - [x] start_background_tasks() inicia scheduler
  - [x] stop_background_tasks() detiene scheduler gracefully
  - [x] get_scheduler_status() retorna estado correcto
  - [x] max_instances=1 previene ejecuciones simultáneas
  - [x] Manejo de canales no configurados (WARNING, no crash)
  - [x] Error handling robusto (no crashea scheduler)
  - [x] Logging completo (INFO, WARNING, ERROR)
  - [x] Frecuencias configurables en config.py
  - [x] Integración en main.py (on_startup, on_shutdown)
  - [x] 4 tests de error handling (todos pasaron)

---

#### T15: Background Tasks (Expulsión VIP + Procesamiento Free) ✅ COMPLETADO
**Archivo:** `bot/background/tasks.py` (280 líneas) + `main.py` (integración)
**Patrón:** APScheduler + AsyncIOScheduler + Error Handling
**Responsabilidades:**
- Expulsión automática de suscriptores VIP expirados
- Procesamiento automático de cola Free
- Limpieza automática de datos antiguos

**Implementación Tareas:**
- `expire_and_kick_vip_subscribers()`: Expulsa VIPs expirados cada 60 min
- `process_free_queue()`: Procesa cola Free cada 5 min
- `cleanup_old_data()`: Limpia datos antiguos diariamente (3 AM UTC)
- `start_background_tasks()`: Inicia scheduler con 3 tareas
- `stop_background_tasks()`: Detiene scheduler gracefully
- `get_scheduler_status()`: Obtiene estado del scheduler

**Configuración Scheduler:**
- Expulsión VIP: IntervalTrigger(minutes=60)
- Procesamiento Free: IntervalTrigger(minutes=5)
- Limpieza: CronTrigger(hour=3, minute=0, timezone="UTC")
- max_instances=1: Previene ejecuciones simultáneas
- replace_existing=True: Reemplaza jobs al reiniciar

**Validaciones:**
- ✅ Canales VIP/Free no configurados (WARNING, return early)
- ✅ Usuario bloquea bot (ERROR, continúa con siguiente)
- ✅ Scheduler ya corre (WARNING, ignora segundo inicio)
- ✅ Stop sin start (WARNING, manejo graceful)
- ✅ max_instances=1 previene race conditions

**Flujos Completos:**
```
Expulsión VIP:
  • Busca VIPs con expiry_date <= now
  • Marca como "expired" (status='expired')
  • Expulsa del canal VIP
  • Loguea resultados

Procesamiento Free:
  • Busca solicitudes con request_date + wait_time <= now
  • Para cada solicitud:
    - Crea invite link (24h, 1 uso)
    - Envía link por mensaje privado
    - Si falla: loguea ERROR, continúa siguiente
  • Resumen: éxitos y errores

Limpieza:
  • Elimina solicitudes Free procesadas >30 días
  • Ejecuta diariamente a las 3 AM UTC
```

**Integración main.py:**
```python
# on_startup: Iniciar background tasks
start_background_tasks(bot)

# on_shutdown: Detener background tasks
stop_background_tasks()
```

**Tests Validación:** ✅ Todos pasaron (4 tests)
- ✅ Test 1: Scheduler lifecycle (start/stop)
- ✅ Test 2: Manejo de canales no configurados
- ✅ Test 3: Idempotencia (start dos veces)
- ✅ Test 4: Stop sin start

**Logging:**
- INFO: Inicio/fin de tareas, éxitos
- WARNING: Canal no configurado, scheduler ya corre
- ERROR: Errores en envío de mensajes, excepciones
- DEBUG: No hay datos procesables

**Configuración en config.py:**
```python
CLEANUP_INTERVAL_MINUTES: int = 60        # Expulsión VIP
PROCESS_FREE_QUEUE_MINUTES: int = 5       # Procesamiento Free
```

---

**Status:** ✅ FASE 1.4 COMPLETADA (T15)
**Próximo:** T16 - Integración Final y Testing E2E

---

## ✅ CHECKLIST FASE 1.5

- [x] T16: Integración Final y Testing E2E
  - [x] conftest.py con fixtures compartidos
  - [x] 5 tests E2E implementados y pasando
  - [x] 4 tests integración implementados y pasando
  - [x] event_loop fixture para tests async
  - [x] db_setup fixture (autouse) para setup/teardown
  - [x] mock_bot fixture con AsyncMocks
  - [x] tests/README.md con documentación completa
  - [x] scripts/run_tests.sh ejecutable
  - [x] Requirements.txt actualizado (pytest, pytest-asyncio)
  - [x] README.md con sección Testing
  - [x] Todos los 9 tests pasando sin errores
  - [x] Tests independientes (orden no importa)
  - [x] BD limpia entre tests
  - [x] Fixtures configurados correctamente

---

#### T16: Integración Final y Testing E2E ✅ COMPLETADO
**Archivos:** `tests/` (estructura completa con 9 tests)
**Patrón:** pytest + pytest-asyncio + fixtures compartidos
**Responsabilidades:**
- Suite de tests E2E para flujos completos
- Tests de integración entre servicios
- Validación de funcionalidad del bot

**Implementación Tests:**

**E2E Tests (5 tests):**
1. `test_vip_flow_complete`: Flujo VIP completo
   - Admin genera token → Usuario canjea → Acceso activo
   - Valida: token generado, suscriptor creado, token marcado usado

2. `test_free_flow_complete`: Flujo Free completo
   - Usuario solicita → Espera tiempo configurado → Procesa cola
   - Valida: solicitud pendiente, no procesa inmediatamente, no duplica

3. `test_vip_expiration`: Expulsión automática de VIP
   - Crear VIP expirado → Ejecutar tarea expiration → Verificar expirado
   - Valida: is_expired() detecta, marca como expired, is_vip_active() retorna False

4. `test_token_validation_edge_cases`: Validación de tokens
   - Token no existe, usado, expirado, válido
   - Cada caso valida retorno correcto de is_valid y mensaje claro

5. `test_duplicate_free_request_prevention`: Prevención de duplicados
   - Primera solicitud crea, segunda retorna existente (no duplica)

**Integration Tests (4 tests):**
1. `test_service_container_lazy_loading`: Lazy loading de servicios
   - Container vacío → Acceder subscription → Se carga
   - Verificar reutilización de instancia

2. `test_config_service_singleton`: BotConfig como singleton
   - Ambos gets retornan id=1
   - Cambios persisten en BD

3. `test_database_session_management`: Manejo de sesiones
   - Múltiples sesiones ven cambios recíprocos
   - Transacciones se aplican correctamente

4. `test_error_handling_across_services`: Error handling robusto
   - Token inválido rechazado
   - Token inexistente detectado
   - No crashes ante errores

**Fixtures Compartidos (conftest.py):**
- `event_loop`: Event loop para tests async
- `db_setup` (autouse): Init/close BD automáticamente
- `mock_bot`: Mock del bot de Telegram

**Documentación:**
- `tests/README.md`: Guía completa de tests y ejecución
- `scripts/run_tests.sh`: Helper script ejecutable

**Ejecución:**
```bash
# Instalar dependencias
pip install pytest==7.4.3 pytest-asyncio==0.21.1 --break-system-packages

# Ejecutar tests
pytest tests/ -v

# O usar script helper
bash scripts/run_tests.sh
```

**Output Esperado:**
```
======================== 9 passed in 5.99s ========================
```

**Validaciones:**
- ✅ 9 tests E2E e integración (todos pasando)
- ✅ Fixtures funcionales (autouse, setup/teardown)
- ✅ Mocks del bot configurados correctamente
- ✅ Tests independientes (orden no importa)
- ✅ BD limpia entre tests
- ✅ Documentación completa
- ✅ Script helper ejecutable

---

**Status:** ✅ FASE 1.5 COMPLETADA (T16)
**Próximo:** T17 - Features Finales y Deployment
