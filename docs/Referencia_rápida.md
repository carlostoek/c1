# PROYECTO TELEGRAM BOT VIP/FREE - REFERENCIA TÉCNICA

Bot de gestión de canales VIP y Free con cola de espera.

═══════════════════════════════════════════════════════════════
# STACK TECNOLÓGICO
═══════════════════════════════════════════════════════════════

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

═══════════════════════════════════════════════════════════════
# ESTRUCTURA DE PROYECTO
═══════════════════════════════════════════════════════════════

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
    │   └── models.py           # Modelos SQLAlchemy
    │
    ├── services/
    │   ├── __init__.py
    │   ├── container.py        # Dependency Injection Container
    │   ├── subscription.py     # Lógica VIP/Free/Tokens
    │   ├── channel.py          # Gestión canales Telegram
    │   ├── config.py           # Configuración del bot
    │   ├── pricing.py          # Gestión de tarifas/planes
    │   ├── user.py             # Gestión de usuarios y roles
    │   └── stats.py            # Estadísticas
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
    │   ├── validators.py       # Funciones de validación
    │   ├── formatters.py       # Formateo de datos para Telegram
    │   └── helpers.py          # Funciones auxiliares
    │
    ├── events/
    │   ├── __init__.py
    │   ├── base.py             # Event base class
    │   ├── bus.py              # EventBus singleton
    │   ├── decorators.py       # @subscribe decorators
    │   └── types.py            # Event types definidos
    │
    └── background/
        ├── __init__.py
        └── tasks.py            # Tareas programadas con APScheduler
```

═══════════════════════════════════════════════════════════════
# CONVENCIONES DE CÓDIGO
═══════════════════════════════════════════════════════════════

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
# MODELOS DE BASE DE DATOS
═══════════════════════════════════════════════════════════════

## BotConfig (Singleton id=1)
- `wait_time_minutes`: Tiempo espera Free (>= 1)
- `vip_channel_id`: ID canal VIP
- `free_channel_id`: ID canal Free
- `vip_reactions`: Lista de reacciones VIP
- `free_reactions`: Lista de reacciones Free
- `subscription_fees`: Dict precios planes

## VIPSubscriber
- `user_id`: ID usuario Telegram (PK)
- `status`: 'active' | 'expired' | 'kicked'
- `join_date`: Timestamp creación
- `expiry_date`: Timestamp expiración
- `duration_hours`: Duración suscripción
- `is_expired()`: bool

## InvitationToken
- `id`: UUID único
- `token`: String aleatorio único
- `generated_by`: ID admin que lo creó
- `created_at`: Timestamp creación
- `expires_at`: Timestamp expiración (24h)
- `is_used`: bool
- `used_by`: ID usuario que lo canjeó (nullable)
- `used_at`: Timestamp canje (nullable)
- `plan_id`: ID plan vinculado (nullable)

## FreeChannelRequest
- `user_id`: ID usuario (PK)
- `request_date`: Timestamp solicitud
- `status`: 'pending' | 'processed' | 'failed'
- `processed_date`: Timestamp procesamiento (nullable)

## Plan
- `id`: Auto PK
- `name`: Nombre del plan
- `duration_days`: Días de duración
- `price`: Precio en USD
- `is_active`: bool

## User (A2)
- `user_id`: ID Telegram (PK)
- `role`: 'FREE' | 'VIP' | 'ADMIN'
- `joined_date`: Timestamp
- `updated_at`: Timestamp actualización

═══════════════════════════════════════════════════════════════
# SERVICIOS CORE
═══════════════════════════════════════════════════════════════

## ServiceContainer (DI + Lazy Loading)
```python
container = ServiceContainer(session, bot)
container.subscription    # SubscriptionService
container.channel        # ChannelService
container.config         # ConfigService
container.pricing        # PricingService
container.user_service   # UserService
container.stats          # StatsService
```

**Métodos:**
- `get_loaded_services()` → List[str]
- `preload_critical_services()` → None (async)

---

## SubscriptionService
**Tokens VIP:**
- `generate_vip_token(generated_by, duration_hours, plan_id=None)` → InvitationToken
- `validate_token(token_str)` → (bool, str, Optional[InvitationToken])
- `redeem_vip_token(token_str, user_id)` → (bool, str, Optional[VIPSubscriber])
- `activate_vip_subscription(user_id, token_id, duration_hours)` → VIPSubscriber

**VIP:**
- `get_vip_subscriber(user_id)` → Optional[VIPSubscriber]
- `is_vip_active(user_id)` → bool
- `expire_vip_subscribers()` → int (background task)
- `kick_expired_vip_from_channel(channel_id)` → int (background task)
- `get_all_vip_subscribers(status, limit, offset)` → List[VIPSubscriber]

**Free:**
- `create_free_request(user_id)` → FreeChannelRequest
- `get_free_request(user_id)` → Optional[FreeChannelRequest]
- `process_free_queue(wait_time_minutes)` → List[FreeChannelRequest] (background)
- `cleanup_old_free_requests(days_old)` → int

**Invite Links:**
- `create_invite_link(channel_id, user_id, expire_hours)` → ChatInviteLink

---

## ChannelService
**Setup:**
- `setup_vip_channel(channel_id)` → (bool, str)
- `setup_free_channel(channel_id)` → (bool, str)
- `verify_bot_permissions(channel_id)` → (bool, str)

**Verificación:**
- `is_vip_channel_configured()` → bool
- `is_free_channel_configured()` → bool
- `get_vip_channel_id()` → Optional[str]
- `get_free_channel_id()` → Optional[str]

**Envío:**
- `send_to_channel(channel_id, text, photo, video, **kwargs)` → (bool, str, Optional[Message])
- `forward_to_channel(channel_id, from_chat_id, message_id)` → (bool, str)
- `copy_to_channel(channel_id, from_chat_id, message_id)` → (bool, str)

**Info:**
- `get_channel_info(channel_id)` → Optional[Chat]
- `get_channel_member_count(channel_id)` → Optional[int]

---

## ConfigService (Singleton)
**Getters:**
- `get_config()` → BotConfig
- `get_wait_time()` → int
- `get_vip_channel_id()` → Optional[str]
- `get_free_channel_id()` → Optional[str]
- `get_vip_reactions()` → List[str]
- `get_free_reactions()` → List[str]
- `get_subscription_fees()` → Dict[str, float]

**Setters (con validación):**
- `set_wait_time(minutes: int)` → None
- `set_vip_reactions(reactions: List[str])` → None
- `set_free_reactions(reactions: List[str])` → None
- `set_subscription_fees(fees: Dict)` → None

**Validación:**
- `is_fully_configured()` → bool
- `get_config_status()` → Dict[str, any]
- `get_config_summary()` → str (HTML para Telegram)
- `reset_to_defaults()` → None

---

## PricingService (A1)
**Planes:**
- `create_plan(name, duration_days, price)` → Plan
- `get_plan(plan_id)` → Optional[Plan]
- `get_all_plans(include_inactive)` → List[Plan]
- `update_plan(plan_id, name, duration_days, price)` → Plan
- `delete_plan(plan_id)` → bool
- `activate_plan(plan_id)` → Plan
- `deactivate_plan(plan_id)` → Plan

---

## UserService (A2)
**Roles:**
- `get_user(user_id)` → Optional[User]
- `create_user(user_id, role='FREE')` → User
- `promote_to_vip(user_id)` → User
- `demote_to_free(user_id)` → User
- `get_user_role(user_id)` → 'FREE' | 'VIP' | 'ADMIN'

---

## StatsService
**Overall:**
- `get_overall_stats()` → Dict

**Usuarios:**
- `get_vip_count()` → int
- `get_free_count()` → int
- `get_active_vip()` → int

**Tokens:**
- `get_token_stats()` → Dict

---

## EventBus (B1 - Pub/Sub)
**Tipos de Eventos:**
- `UserStartedBotEvent`
- `UserRoleChangedEvent`
- `UserJoinedVIPEvent`
- `UserVIPExpiredEvent`
- `TokenGeneratedEvent`
- `UserRequestedFreeChannelEvent`
- `UserJoinedFreeChannelEvent`
- `MessageReactedEvent`
- `DailyLoginEvent`
- `UserReferredEvent`
- `PointsAwardedEvent`
- `BadgeUnlockedEvent`
- `RankUpEvent`
- `MessageBroadcastedEvent`

**Métodos:**
- `subscribe(event_type, handler)` → None
- `subscribe_all(handler)` → Decorador
- `publish(event)` → None (fire-and-forget)
- `get_subscribers_count(event_type)` → int
- `clear_subscribers()` → None

═══════════════════════════════════════════════════════════════
# MIDDLEWARES
═══════════════════════════════════════════════════════════════

## AdminAuthMiddleware
- Verifica `Config.is_admin(user.id)` para Message y CallbackQuery
- Envía mensaje de error si no es admin
- No ejecuta handler si no autorizado
- Logging: WARNING para intentos denegados

## DatabaseMiddleware
- Crea AsyncSession usando `get_session()`
- Inyecta sesión en `data["session"]`
- Manejo automático de commit/rollback
- Logging: ERROR si excepción en handler

═══════════════════════════════════════════════════════════════
# ESTADOS FSM
═══════════════════════════════════════════════════════════════

## Admin States
- `ChannelSetupStates`: waiting_for_vip_channel, waiting_for_free_channel
- `WaitTimeSetupStates`: waiting_for_minutes
- `BroadcastStates`: waiting_for_content, waiting_for_confirmation

## User States
- `TokenRedemptionStates`: waiting_for_token
- `FreeAccessStates`: waiting_for_approval

═══════════════════════════════════════════════════════════════
# HANDLERS
═══════════════════════════════════════════════════════════════

## Admin Handlers
**main.py:**
- `cmd_admin`: Menú principal
- `callback_admin_main`: Volver al menú
- `callback_admin_config`: Ver configuración

**vip.py:**
- `callback_vip_menu`: Submenú VIP
- `callback_vip_setup`: Setup canal VIP (FSM)
- `process_vip_channel_forward`: Procesa forward
- `callback_generate_token_select_plan`: Seleccionar plan
- `callback_generate_token_with_plan`: Generar token con deep link
- `vip_menu_keyboard()`: Keyboard dinámico

**free.py:**
- `callback_free_menu`: Submenú Free
- `callback_free_setup`: Setup canal Free (FSM)
- `process_free_channel_forward`: Procesa forward
- `callback_set_wait_time`: Configurar espera (FSM)
- `process_wait_time_input`: Procesa minutos
- `free_menu_keyboard()`: Keyboard dinámico

## User Handlers
**start.py:**
- `cmd_start`: Bienvenida, detección de rol, deep links
- `_activate_token_from_deeplink`: Activación automática (A3)
- `_send_welcome_message`: Mensaje personalizado por rol

**vip_flow.py:**
- `callback_redeem_token`: Inicia canje token (FSM)
- `process_token_input`: Procesa token
- `callback_cancel`: Cancela flujo

**free_flow.py:**
- `callback_request_free`: Crea solicitud Free

═══════════════════════════════════════════════════════════════
# KEYBOARDS
═══════════════════════════════════════════════════════════════

**Factory Functions:**
- `create_inline_keyboard(buttons_dict)` → InlineKeyboardMarkup
- `admin_main_menu_keyboard()` → Menú principal (3 opciones)
- `back_to_main_menu_keyboard()` → Botón volver
- `yes_no_keyboard()` → Confirmación Sí/No
- `vip_menu_keyboard(is_configured)` → Menú VIP dinámico
- `free_menu_keyboard(is_configured)` → Menú Free dinámico

═══════════════════════════════════════════════════════════════
# TAREAS DE BACKGROUND (APScheduler)
═══════════════════════════════════════════════════════════════

**Tareas:**
- `expire_and_kick_vip_subscribers()`: Cada 60 minutos
- `process_free_queue()`: Cada 5 minutos
- `cleanup_old_data()`: Diariamente a las 3 AM UTC

**Control:**
- `start_background_tasks(bot)`: Inicia scheduler
- `stop_background_tasks()`: Detiene scheduler
- `get_scheduler_status()` → Dict

═══════════════════════════════════════════════════════════════
# FORMATTERS Y UTILITIES
═══════════════════════════════════════════════════════════════

**Formatters (bot/utils/formatters.py - T28):**
- `format_date_iso()`: Fecha ISO 8601
- `format_datetime_iso()`: Fecha/hora ISO 8601
- `format_timestamp_iso()`: Timestamp ISO 8601
- `format_currency()`: Moneda USD
- `format_percentage()`: Porcentaje
- `format_relative_time()`: Tiempo relativo (ej: "hace 2h")
- `format_duration_human()`: Duración legible (ej: "2d 3h")
- `format_phone_number()`: Teléfono formateado
- `format_emoji_status()`: Emoji de estado (🟢🟡🔴)
- `escape_html()`: Escaping HTML para Telegram
- `truncate_text()`: Truncado de texto
- `paginate_list()`: Paginación de listas
- Y más... (19 funciones totales)

═══════════════════════════════════════════════════════════════
# TESTING
═══════════════════════════════════════════════════════════════

**Test Files:**
- `tests/conftest.py`: Fixtures compartidos
- `tests/test_e2e_*.py`: Tests E2E por feature
- `tests/test_integration_*.py`: Tests de integración
- `tests/test_a*.py`: Tests ONDA 3 features
- `tests/test_b*.py`: Tests ONDA 3 features

**Fixtures:**
- `event_loop`: Event loop async
- `db_setup`: Setup/teardown DB
- `mock_bot`: Bot mock con AsyncMocks

**Ejecución:**
```bash
pytest tests/ -v
bash scripts/run_tests.sh
```

═══════════════════════════════════════════════════════════════
# FLUJOS PRINCIPALES
═══════════════════════════════════════════════════════════════

## Flujo VIP Completo
1. Admin genera token (`/admin → VIP → Generar Token`)
2. Usuario accede deep link: `https://t.me/botname?start=TOKEN`
3. Handler `/start` detecta parámetro, activa suscripción automáticamente
4. Usuario recibe invite link y acceso al canal

## Flujo Free
1. Usuario solicita acceso (`/start → Solicitar Free`)
2. Sistema crea `FreeChannelRequest` en estado "pending"
3. Background task espera tiempo configurado
4. Después de esperar, procesa: crea invite link, envía por DM
5. Sistema marca como "processed"

## Flujo Expulsión VIP
1. Background task busca VIPs con `expiry_date <= now`
2. Marca como "expired" en BD
3. Expulsa del canal mediante Telegram API
4. Loguea resultados

═══════════════════════════════════════════════════════════════
# INTEGRACIÓN Y ARQUITECTURA
═══════════════════════════════════════════════════════════════

```
main.py
  ↓
ServiceContainer (DI + Lazy Loading)
  ├─ SubscriptionService
  ├─ ChannelService
  ├─ ConfigService
  ├─ PricingService
  ├─ UserService
  ├─ StatsService
  └─ EventBus (Pub/Sub)
    ↓
  Database (SQLAlchemy Async)
    ↓
  SQLite WAL Mode
```

**Handlers acceden a servicios mediante:**
```python
session = state.data["session"]  # Inyectado por DatabaseMiddleware
container = ServiceContainer(session, bot)
await container.subscription.generate_vip_token(...)
```

**Eventos se publican automáticamente en:**
- Generación de tokens
- Canje de tokens
- Activación VIP
- Expiración VIP
- Solicitud Free
- Procesamiento Free

═══════════════════════════════════════════════════════════════
# ESTADÍSTICAS FINALES
═══════════════════════════════════════════════════════════════

**ONDA 1 (Base):**
- Líneas de código: ~1,526 (services)
- Métodos async: 39+
- Modelos DB: 4

**ONDA 2 (Enhancements):**
- Funciones formatters: 19
- Tests E2E: 12
- Coverage: >85%

**ONDA 3 (Features Avanzadas):**
- A1: Sistema de Tarifas/Planes ✅
- A2: Sistema de Roles de Usuario ✅
- A3: Tokens con Deep Links + Activación Automática ✅
- B1: Event Bus (Pub/Sub) ✅

**Total:**
- Archivos: ~40
- Líneas código productivo: ~4,000+
- Tests E2E: 20+
- Type hints: 100%
- Docstrings: 100%
