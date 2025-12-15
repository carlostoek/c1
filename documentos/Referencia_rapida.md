# REFERENCIA RÁPIDA - Telegram Bot VIP/FREE

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
```

---

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
├── bot/
│   ├── database/                # Modelos y engine
│   │   ├── base.py
│   │   ├── engine.py
│   │   └── models.py
│   ├── services/                # Lógica de negocio
│   │   ├── container.py         # DI Container
│   │   ├── subscription.py      # VIP/Free/Tokens
│   │   ├── channel.py           # Canales Telegram
│   │   └── config.py            # Config global
│   ├── handlers/                # Handlers de eventos
│   │   ├── admin/               # Rutas admin
│   │   └── user/                # Rutas usuario
│   ├── middlewares/             # Middlewares (Auth, DB)
│   ├── states/                  # FSM states
│   ├── utils/                   # Utilidades
│   ├── background/              # Tareas programadas
│   └── events/                  # Event Bus
│
└── tests/                       # Tests E2E e integración
```

---

## 🎨 CONVENCIONES DE CÓDIGO

```python
# Naming:
# - Clases: PascalCase (VIPSubscriber, SubscriptionService)
# - Funciones: snake_case (generate_token, check_expiry)
# - Constantes: UPPER_SNAKE_CASE
# - Archivos: snake_case

# Async:
# - TODOS los handlers: async def
# - TODOS los métodos services: async def
# - Usar await para llamadas DB/API

# Error Handling:
# - Try-except en handlers
# - Logger en cada módulo: logger = logging.getLogger(__name__)
# - Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Type Hints:
# - Obligatorio en signatures
# - Optional[T], Union[T1, T2]

# Docstrings:
# - Google Style
# - En clases y funciones públicas
```

---

## 📚 SERVICIOS CORE

### ServiceContainer (DI + Lazy Loading)
- `container.subscription` → SubscriptionService
- `container.channel` → ChannelService
- `container.config` → ConfigService
- `container.stats` → StatsService (future)

### SubscriptionService
**Tokens VIP:**
- `generate_vip_token(generated_by, duration_hours, plan_id=None)`
- `validate_token(token_str)`
- `redeem_vip_token(token_str, user_id)`
- `activate_vip_subscription(user_id, token_id, duration_hours)`

**Gestión VIP:**
- `get_vip_subscriber(user_id)`
- `is_vip_active(user_id)`
- `expire_vip_subscribers()` (background task)
- `get_all_vip_subscribers(status, limit, offset)`

**Gestión Free:**
- `create_free_request(user_id)`
- `get_free_request(user_id)`
- `process_free_queue(wait_time_minutes)` (background task)
- `cleanup_old_free_requests(days_old)`

**Invite Links:**
- `create_invite_link(channel_id, user_id, expire_hours)`

### ChannelService
- `setup_vip_channel(channel_id)`
- `setup_free_channel(channel_id)`
- `verify_bot_permissions(channel_id)`
- `is_vip_channel_configured()`
- `is_free_channel_configured()`
- `send_to_channel(channel_id, text, photo, video, **kwargs)`
- `forward_to_channel(channel_id, from_chat_id, message_id)`
- `copy_to_channel(channel_id, from_chat_id, message_id)`
- `get_channel_info(channel_id)`
- `get_channel_member_count(channel_id)`

### ConfigService (Singleton)
**Getters:**
- `get_config()`
- `get_wait_time()`
- `get_vip_channel_id()` / `get_free_channel_id()`
- `get_vip_reactions()` / `get_free_reactions()`
- `get_subscription_fees()`

**Setters (con validación):**
- `set_wait_time(minutes)`
- `set_vip_reactions(reactions)`
- `set_free_reactions(reactions)`
- `set_subscription_fees(fees)`

**Validación:**
- `is_fully_configured()`
- `get_config_status()`
- `get_config_summary()`

---

## 🔄 MIDDLEWARES

### AdminAuthMiddleware
- Verifica `Config.is_admin(user.id)`
- Envía error si no es admin
- No ejecuta handler si no autorizado
- Logging: WARNING (denegados), DEBUG (autorizados)

### DatabaseMiddleware
- Inyecta sesión en `data["session"]`
- Context manager automático
- Commit/rollback automático
- Logging: ERROR en excepciones

---

## 📊 ESTADOS FSM

### Admin States
- **ChannelSetupStates:** waiting_for_vip_channel, waiting_for_free_channel
- **WaitTimeSetupStates:** waiting_for_minutes
- **BroadcastStates:** waiting_for_content, waiting_for_confirmation

### User States
- **TokenRedemptionStates:** waiting_for_token
- **FreeAccessStates:** waiting_for_approval

---

## 🎯 FLUJOS PRINCIPALES

### VIP Token Redeem
```
1. User: /start → Canjear Token
2. Bot: waiting_for_token state
3. User: Envía token
4. Bot: Valida → Crea link → Envía → state.clear()
```

### Free Channel Request
```
1. User: /start → Solicitar Free
2. Bot: Crea solicitud (sin FSM)
3. Background task procesará después
```

### Deep Link VIP Activation
```
1. Admin: /admin → Generar Token → Selecciona plan
2. Bot: Genera token + deep link (https://t.me/bot?start=TOKEN)
3. User: Click en link
4. Bot: Activa automáticamente, cambia rol FREE → VIP
```

### Setup Canal VIP/Free
```
1. User: Click "Configurar"
2. Bot: Entra estado waiting_for_vip/free_channel
3. User: Reenvía forward del canal
4. Bot: Extrae forward_from_chat.id → Configura → state.clear()
```

---

## ⏰ BACKGROUND TASKS (APScheduler)

- **Expulsión VIP:** Cada 60 min → expire_and_kick_vip_subscribers()
- **Procesamiento Free:** Cada 5 min → process_free_queue()
- **Limpieza:** Diariamente 3 AM UTC → cleanup_old_data()

**Características:**
- max_instances=1 (previene ejecuciones simultáneas)
- replace_existing=True (reemplaza al reiniciar)
- Error isolation (fallos aislados)
- Logging completo

---

## 🎪 EVENT BUS (B1)

### Publicación
```python
from bot.events import event_bus, UserJoinedVIPEvent

event_bus.publish(UserJoinedVIPEvent(
    user_id=123,
    plan_name="Mensual",
    duration_days=30
))
```

### Suscripción
```python
from bot.events import subscribe, UserJoinedVIPEvent

@subscribe(UserJoinedVIPEvent)
async def on_vip_join(event):
    print(f"User {event.user_id} joined VIP!")
```

### Event Types (15+)
- **User:** UserStartedBotEvent, UserRoleChangedEvent
- **VIP:** UserJoinedVIPEvent, UserVIPExpiredEvent, TokenGeneratedEvent
- **Free:** UserRequestedFreeChannelEvent, UserJoinedFreeChannelEvent
- **Interaction:** MessageReactedEvent, DailyLoginEvent, UserReferredEvent
- **Gamification:** PointsAwardedEvent, BadgeUnlockedEvent, RankUpEvent
- **Broadcast:** MessageBroadcastedEvent

**Características:**
- Fire-and-forget (no-bloqueant)
- Error isolation (handlers aislados)
- Type-safe (type hints completos)
- UUID + timestamps automáticos

---

## ✅ FASES COMPLETADAS

### FASE 1.1: Base de Datos ✅
- SQLAlchemy base + engine async
- 4 modelos: BotConfig, VIPSubscriber, InvitationToken, FreeChannelRequest
- Fixtures testing

### FASE 1.2: Servicios Core ✅
- ServiceContainer (DI + Lazy Loading)
- SubscriptionService (1,526 líneas)
- ChannelService (420 líneas)
- ConfigService (349 líneas)

### FASE 1.3: Handlers ✅
- Middlewares (AdminAuth + Database)
- FSM States (7 estados)
- Admin handlers (/admin, VIP, Free)
- User handlers (/start, Token redeem, Free request)

### FASE 1.4: Background Tasks ✅
- APScheduler integrado
- Expulsión VIP, Procesamiento Free, Limpieza
- Error handling robusto

### FASE 1.5: Testing E2E ✅
- 9 tests E2E + integración
- conftest.py con fixtures compartidos
- Cobertura completa

### ONDA 2: Enhancements ✅
- Dashboard estado completo
- 19 formatters reutilizables
- 12 tests E2E ONDA 2

### ONDA 3: Features Avanzadas ✅
- A1: Sistema de Tarifas/Planes
- A2: Sistema de Roles de Usuario
- A3: Tokens con Deep Links + Activación Automática
- B1: Event Bus Pub/Sub

---

## 📈 ESTADÍSTICAS FINALES

| Métrica | Valor |
|---------|-------|
| Archivos Backend | 25+ |
| Líneas de Código | 5,000+ |
| Métodos Async | 60+ |
| Event Types | 15+ |
| Tests Implementados | 50+ |
| Tests Pasando | 100% ✅ |
| Type Hints | 100% |
| Docstrings | 100% |
| Patrones | DI, Singleton, Pub/Sub, FSM |

---

## 🚀 INTEGRACIÓN GENERAL

```
main.py
  ↓
ServiceContainer (DI + Lazy Loading)
  ├─ SubscriptionService
  ├─ ChannelService
  ├─ ConfigService
  └─ PricingService
    ↓
Database (SQLAlchemy Async + SQLite WAL)
    ↓
Event Bus (Pub/Sub Fire-and-forget)
    ↓
Background Tasks (APScheduler)
```

---

## 📋 CHECKLIST FEATURES

- [x] Generación tokens VIP
- [x] Canje de tokens
- [x] Invite links automáticos
- [x] Setup canales VIP/Free
- [x] Cola de espera Free
- [x] Expulsión automática de VIPs expirados
- [x] Procesamiento automático de cola Free
- [x] Deep links con activación automática
- [x] Sistema de tarifas/planes
- [x] Sistema de roles de usuario
- [x] Event Bus pub/sub
- [x] Dashboard con estadísticas
- [x] Formatters reutilizables
- [x] Testing E2E completo

---

## 📖 PRÓXIMOS PASOS

- **A4:** Broadcasting avanzado
- **B2:** Gamificación con Event Bus
- **Optimización:** Performance y escalabilidad
- **Deployment:** Documentación de deploy

---

*Documento generado automáticamente desde análisis del proyecto*
