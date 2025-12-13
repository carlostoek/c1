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

- **T11:** Admin Main Menu Handler
- **T12:** Admin VIP Management Handler
- *T13-T17: Más handlers y features*

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
- [ ] T11: Admin Main Menu Handler
- [ ] T12: Admin VIP Management Handler
- [ ] T13-T17: Más handlers y features

**Status:** 🔄 FASE 1.3 EN PROGRESO
**Próximo:** T11 - Admin Main Menu Handler
