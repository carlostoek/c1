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

## UserProgress (B3)
- `user_id`: ID usuario (PK)
- `total_besitos`: Total acumulado
- `current_rank`: Rango actual ('Novato' | 'Bronce' | 'Plata')
- `total_reactions`: Total de reacciones (lifetime)
- `reactions_today`: Reacciones hoy (reset diario)
- `last_reaction_at`: Última reacción
- `created_at`, `updated_at`: Timestamps

## UserBadge (B3)
- `id`: Auto PK
- `user_id`: FK a UserProgress
- `badge_id`: Identificador del badge
- `unlocked_at`: Timestamp de desbloqueo

## DailyStreak (B3)
- `user_id`: FK a UserProgress (PK)
- `current_streak`: Días consecutivos actuales
- `longest_streak`: Récord personal
- `last_login_date`: Última fecha de login
- `total_logins`: Total lifetime

## BesitosTransaction (B3)
- `id`: Auto PK
- `user_id`: ID usuario
- `amount`: Cantidad (+/-)
- `reason`: Razón de la transacción
- `created_at`: Timestamp

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

## GamificationService (B3)
**Besitos y Puntos:**
- `award_besitos(user_id, action, custom_amount=None, custom_reason=None)` → (int, bool, Optional[str])
- `get_or_create_progress(user_id)` → UserProgress
- `can_react_to_message(user_id)` → bool
- `record_reaction(user_id)` → None

**Badges:**
- `check_and_unlock_badges(user_id)` → List[str]
- `_check_badge_requirement(user_id, progress, badge_def)` → bool

**Daily Login:**
- `claim_daily_login(user_id)` → (int, int, bool) - (besitos, streak, is_record)

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

**daily.py (B3):**
- `callback_claim_daily`: Reclamación de regalo diario
  - Valida que no haya reclamado hoy
  - Actualiza racha de login
  - Otorga Besitos base + bonus por racha
  - Verifica badges (ej: streak_7, streak_30)
  - Envía RewardBatch unificado

**reactions.py (B3):**
- `callback_reaction`: Manejo de reacciones inline
  - Parsea callback: react:TYPE:MESSAGE_ID:CHANNEL_ID
  - Publica MessageReactedEvent
  - Listener otorga Besitos automáticamente

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

**Reaction System (B3):**
- `ReactionButton`: Clase para botón de reacción
  - Propiedades: emoji, type, callback_prefix
  - Métodos: `to_callback_data()`, `to_inline_button()`
- `ReactionSystem`: Sistema completo de reacciones
  - `create_reaction_keyboard()`: Crea keyboard con botones
  - `parse_reaction_callback()`: Parsea formato "react:TYPE:MESSAGE_ID:CHANNEL_ID"
  - `get_reactions_from_config()`: Convierte lista de emojis a ReactionButton
  - Default reactions: 👍❤️🔥😂😮

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
# GAMIFICACIÓN (B3)
═══════════════════════════════════════════════════════════════

## Configuración
**Recompensas de Besitos:**
- `user_started`: 10 Besitos (bienvenida)
- `joined_vip`: 100 Besitos (activación VIP)
- `joined_free_channel`: 25 Besitos (ingreso canal Free)
- `message_reacted`: 5 Besitos (reacción a mensaje)
- `first_reaction_of_day`: 10 Besitos (bonus primer reacción)
- `daily_login_base`: 20 Besitos (gift diario)
- `daily_login_streak_bonus`: 5 Besitos por día (racha)
- `referral_success`: 50 Besitos (referido)

**Rangos (por Besitos acumulados):**
- 🌱 **Novato**: 0-499 Besitos
- 🥉 **Bronce**: 500-1999 Besitos
- 🥈 **Plata**: 2000+ Besitos

**Badges (5 totales):**
- 🔥 **Constante**: 7 días de login consecutivos
- 💪 **Dedicado**: 30 días de login consecutivos
- ❤️ **Reactor**: 100 reacciones totales
- ⭐ **VIP**: Suscripción VIP activa
- 💋 **Coleccionista**: 1000 Besitos acumulados

## Rate Limiting
- Max 50 reacciones/día
- Mínimo 5 segundos entre reacciones
- Daily login: 1 vez por día (reset a medianoche UTC)

## Event Listeners (5)
Automáticamente otorgan Besitos:
1. `on_user_started_bot`: Usuario nuevo → 10 Besitos
2. `on_user_joined_vip`: VIP activado → 100 Besitos + badges
3. `on_user_joined_free_channel`: Free ingreso → 25 Besitos
4. `on_message_reacted`: Reacción a mensaje → 5-15 Besitos
5. `on_user_referred`: Referido exitoso → 50 Besitos

## Endpoints
- **Daily Login**: `callback_claim_daily` (Button)
- **Reactions**: `callback_reaction` (Inline buttons)

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
# NOTIFICATION SERVICE (B2)
═══════════════════════════════════════════════════════════════

## Módulo: bot/notifications/

**Propósito:** Sistema centralizado de notificaciones con templates personalizables
y RewardBatch para agrupar múltiples recompensas.

### Componentes

**1. NotificationType (types.py)**
```python
# Enum de tipos de notificaciones
class NotificationType(str, Enum):
    WELCOME                  # Bienvenida al usuario
    POINTS_EARNED           # Besitos ganados
    BADGE_UNLOCKED          # Insignia desbloqueada
    RANK_UP                 # Cambio de rango
    VIP_ACTIVATED           # VIP activado
    VIP_EXPIRING_SOON       # VIP por expirar
    VIP_EXPIRED             # VIP expirado
    DAILY_LOGIN             # Login diario
    STREAK_MILESTONE        # Hito de racha
    REFERRAL_SUCCESS        # Referido exitoso
    INFO / WARNING / ERROR  # Informativos
```

**2. RewardBatch (batch.py)**
- **Reward:** Una recompensa individual (puntos, badge, rank)
- **RewardBatch:** Agrupa múltiples recompensas en una sola notificación

```python
# Ejemplo de uso:
batch = RewardBatch(user_id=123, action="Reaccionaste a un mensaje")
batch.add_besitos(50, "Reacción")
batch.add_badge("🔥 Hot Streak", "10 días")
batch.add_rank_up("Novato", "Bronce")
await notifications.send_reward_batch(batch)  # Una sola notificación
```

**Ventajas:**
- Reduce spam de notificaciones
- Agrupa recompensas relacionadas
- Mejor UX: información consolidada
- Soporta emojis y HTML

**3. NotificationTemplates (templates.py)**
- 13+ templates HTML predefinidos
- Placeholders: {variable} se reemplazan dinámicamente
- Soporta emojis y HTML formatting
- Renderizado con método `.render()`

Ejemplos:
- `WELCOME_DEFAULT` → Bienvenida personalizada
- `BESITOS_EARNED` → Notificación de puntos
- `BADGE_UNLOCKED` → Insignia ganada
- `RANK_UP` → Cambio de rango
- `VIP_ACTIVATED` → VIP activado

**4. NotificationService (service.py)**
- Servicio centralizado de envío de notificaciones
- Lazy loaded en ServiceContainer
- Busca templates personalizados en BD primero, luego defaults

Métodos principales:
```python
async def send(user_id, notification_type, context, keyboard)
    # Envía notificación genérica

async def send_reward_batch(batch, keyboard)
    # Envía lote de recompensas

async def send_welcome(user_id, first_name, role_name, role_emoji)
    # Envía bienvenida personalizada

async def send_besitos(user_id, amount, reason, total_besitos)
    # Envía notificación de Besitos
```

**5. NotificationTemplate (modelo BD)**
```python
class NotificationTemplate:
    id          # ID único
    type        # NotificationType (unique)
    name        # Nombre descriptivo
    content     # HTML del template
    active      # Si está en uso
    created_at  # Fecha creación
    updated_at  # Última actualización
```

### Admin Interface (handlers/admin/notifications.py)

Menu: **💬 Mensajes** en panel admin

Funcionalidades:
- Listar templates personalizados
- Editar templates (mostrar contenido actual)
- Activar/Desactivar templates

Flujo:
```
/admin
  → ⚙️ Configuración
    → 💬 Mensajes
      → ✏️ Editar Template
        → 🔄 Activar/Desactivar
```

### Integración

**Uso en handlers:**
```python
container = ServiceContainer(session, bot)

# Notificación simple
await container.notifications.send(
    user_id=123,
    notification_type=NotificationType.WELCOME,
    context={"first_name": "Juan", "role_name": "Free", "role_emoji": "👤"}
)

# Lote de recompensas
batch = RewardBatch(user_id=123, action="Acción")
batch.add_besitos(50)
await container.notifications.send_reward_batch(batch)
```

**Uso en listeners de eventos:**
```python
@subscribe(MessageReactedEvent)
async def on_message_reacted(event):
    batch = RewardBatch(user_id=event.user_id, action="Reaccionaste")
    batch.add_besitos(10)
    if user_unlocked_badge:
        batch.add_badge("Badge name")
    await notifications.send_reward_batch(batch)
```

### Características

✅ Templates personalizables sin tocar código
✅ RewardBatch para unificar notificaciones
✅ Soporte de emojis y HTML
✅ Logging automático
✅ Manejo de errores (no crashea el bot)
✅ Type hints completos
✅ 36 tests (batch + templates)

### Testing

```bash
# Tests de RewardBatch
pytest tests/test_notification_batch.py -v  # 19 tests

# Tests de Templates
pytest tests/test_notification_templates.py -v  # 17 tests

# Casos cubiertos:
# - Agrupación de recompensas
# - Formateo de mensajes
# - Renderizado de templates
# - Manejo de variables
# - Caracteres especiales
# - Emojis
```

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
- B2: Notification Service + RewardBatch ✅

**Total:**
- Archivos: ~48
- Líneas código productivo: ~5,300+
- Módulos: 8 (database, services, handlers, middlewares, states, utils, events, notifications)
- Tests E2E + Unit: 36 nuevos (batch, templates)
- Type hints: 100%
- Docstrings: 100%
