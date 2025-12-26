# REFERENCIA RÁPIDA - Bot VIP/Free Telegram

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

## 🔄 ARQUITECTURA DE SERVICIOS

Todas las capas se comunican a través de **ServiceContainer**:

```
main.py
  ↓
ServiceContainer (DI + Lazy Loading)
  ├─ SubscriptionService (VIP/Free/Tokens)
  ├─ ChannelService (Canales Telegram)
  ├─ ConfigService (Configuración global)
  └─ StatsService (Future)
    ↓
  Database (SQLAlchemy Async)
    ↓
  SQLite WAL Mode
```

## 📚 ARCHIVOS CORE

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

## 🎯 INTEGRACIÓN CON SERVICIOS

Ejemplo de uso en handlers:
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

5. **Documentación (Optional)**
   - Actualizar README.md si aplica
   - Actualizar documentos si hay cambios arquitectónicos

## ✅ CHECKLIST FASE 1.2 - Servicios Core

- [ ] T6: ServiceContainer con lazy loading
- [ ] T7: SubscriptionService (VIP/Free/Tokens)
- [ ] T8: ChannelService (Gestión canales)
- [ ] T9: ConfigService (Configuración global)

### T6: Service Container (Dependency Injection)
- Archivo: `bot/services/container.py`
- Patrón: DI + Lazy Loading
- Responsabilidades: Centralizar instanciación de servicios, Lazy loading transparente, Inyectar session y bot a todos los servicios

### T7: Subscription Service (VIP/Free/Tokens)
- Archivo: `bot/services/subscription.py`
- Responsabilidades: Generación de tokens únicos y seguros, Validación y canje de tokens, Gestión de suscriptores VIP, Gestión de solicitudes Free

### T8: Channel Service (Gestión de Canales)
- Archivo: `bot/services/channel.py`
- Responsabilidades: Configuración de canales VIP y Free, Verificación de permisos del bot, Envío de mensajes/publicaciones

### T9: Config Service (Configuración Global)
- Archivo: `bot/services/config.py`
- Patrón: Singleton (BotConfig id=1)
- Responsabilidades: Gestión centralizada de configuración, Validación de configuración completa

## ✅ CHECKLIST FASE 1.3 - Handlers Admin

- [ ] T10: Middlewares (AdminAuth + Database)
- [ ] T11: Estados FSM para Admin y User
- [ ] T12: Handler /admin (Menú Principal)
- [ ] T13: Handlers VIP y Free (Submenús)

### T10: Middlewares
- AdminAuthMiddleware: Validación de permisos de administrador
- DatabaseMiddleware: Inyección de sesión de base de datos

### T11: Estados FSM
- ChannelSetupStates: 2 estados
- WaitTimeSetupStates: 1 estado
- BroadcastStates: 2 estados
- TokenRedemptionStates: 1 estado
- FreeAccessStates: 1 estado

### T12: Handler /admin
- Menú principal de administración
- Navegar entre submenús
- Mostrar estado de configuración

### T13: Handlers VIP y Free
- Submenús VIP y Free adaptables al estado de configuración
- Flujos FSM para setup de canales
- Generación de tokens VIP
- Configuración de tiempo de espera Free

## ✅ CHECKLIST FASE 1.4 - Background Tasks

- [ ] T15: Background Tasks (Expulsión VIP + Procesamiento Free)
- [ ] Tareas implementadas: expire_and_kick_vip_subscribers(), process_free_queue(), cleanup_old_data()

## ✅ CHECKLIST FASE 1.5 - Testing E2E

- [ ] T16: Integración Final y Testing E2E
- [ ] 5 tests E2E implementados
- [ ] 4 tests integración implementados
- [ ] 9 tests total pasando

## 🎯 ONDA 2 - FEATURES AVANZADOS

### T27: Dashboard Estado Completo
- Panel visual con health checks
- Estadísticas en tiempo real
- Status de background tasks
- Acciones rápidas

### T28: Formatters y Helpers Reutilizables
- 19 funciones de formateo
- 100% type hints
- 100% docstrings
- Emojis consistentes (🟢🟡🔴)

### T29: Testing E2E ONDA 2
- 12 tests E2E completos
- Coverage >85% ONDA 2
- Validación de stats, paginación, formatters

## 🎯 ONDA 3 - FEATURES AVANZADAS

### A1: Sistema Completo de Tarifas/Planes
- Crear, actualizar, eliminar planes
- Activar/desactivar planes
- Validación de duración y precio

### A2: Sistema Completo de Roles de Usuario
- Cambio de roles con historial
- Promoted/Demoted events
- Validación de permisos por rol

### A3: GENERACIÓN DE TOKENS CON DEEP LINKS Y ACTIVACIÓN AUTOMÁTICA
- Tokens vinculados a planes de suscripción
- Activación automática vía deep links
- Cambio automático de rol usuario
- 7 tests E2E completados (100% pasando)

## ✅ CHECKLIST TAREA 11 - SISTEMA DE REACCIONES PERSONALIZADAS

### T1-T9: Sistema de Reacciones Personalizadas + Broadcasting Gamificado

#### T1: Modelos de Base de Datos
- Archivo: `bot/database/models.py` - Modelo `BroadcastMessage` con:
  - Campos básicos: id, message_id, chat_id, content_type, content_text, media_file_id
  - Campos de auditoría: sent_by, sent_at
  - Campos de gamificación: gamification_enabled, reaction_buttons, content_protected
  - Cache de stats: total_reactions, unique_reactors
  - Índices: idx_chat_message (unique), idx_sent_at
- Archivo: `bot/gamification/database/models.py` - Modelo `CustomReaction` con:
  - Campos: id, broadcast_message_id, user_id, reaction_type_id, emoji, besitos_earned, created_at
  - Relaciones: broadcast_message, user, reaction_type
  - Índices: idx_unique_reaction (unique), idx_user_created
- Modificación: Modelo `Reaction` con campos UI: button_emoji, button_label, sort_order
- Migración Alembic: `alembic/versions/005_add_custom_reactions_system.py`

#### T2: CustomReactionService
- Archivo: `bot/gamification/services/custom_reaction.py`
- Responsabilidades:
  - Registrar reacciones personalizadas con validación de duplicados
  - Calcular y otorgar besitos por reaccionar
  - Obtener reacciones de usuarios por mensaje
  - Obtener estadísticas de reacciones por mensaje

#### T3: BroadcastService
- Archivo: `bot/services/broadcast.py`
- Responsabilidades:
  - Enviar mensajes con gamificación a canales VIP/Free
  - Construir teclados de reacciones personalizadas
  - Registrar mensajes en BD con opciones de gamificación

#### T4: Extensión de Estados FSM
- Archivo: `bot/states/admin.py` - Nuevo estado `configuring_options` en `BroadcastStates`
- Reorganización de estados: waiting_for_content → configuring_options → selecting_reactions → waiting_for_confirmation

#### T5: Extensión de broadcast.py - Paso de Configuración
- Archivo: `bot/handlers/admin/broadcast.py`
- Responsabilidades:
  - Interfaz de configuración de gamificación en broadcasting
  - Selección de reacciones para mensajes
  - Activación/desactivación de protección de contenido
  - Integración con BroadcastService

#### T6: Handler de Callbacks de Reacciones
- Archivo: `bot/gamification/handlers/user/reactions.py`
- Responsabilidades:
  - Procesar reacciones de usuarios a mensajes de broadcasting
  - Validar mensajes con gamificación activa
  - Registrar reacciones y otorgar besitos
  - Actualizar teclados con marcas personales

#### T7: Protección de Contenido
- Implementación de `protect_content=True` en envío de mensajes
- Toggle en UI de configuración de broadcasting

#### T8: Estadísticas de Broadcasting
- Archivo: `bot/gamification/services/stats.py` - Métodos para estadísticas de reacciones
- Responsabilidades: Obtener stats por mensaje y top broadcasts por engagement

#### T9: Seed de Datos Iniciales
- Archivo: `scripts/seed_reactions.py` - Script para crear reacciones predeterminadas
- 5 reacciones predeterminadas: "👍", "❤️", "🔥", "😂", "😮" con diferentes valores de besitos

#### T10-T11: Tests E2E y Documentación
- Tests E2E completos para el sistema de reacciones personalizadas
- Documentación completa del sistema en `docs/gamification/CUSTOM_REACTIONS.md`

**Características del sistema:**
- Botones de reacción personalizados con emojis configurables
- Gamificación: usuarios ganan besitos por reaccionar
- Prevención de duplicados: un usuario no puede reaccionar dos veces con mismo emoji
- Contadores públicos: muestra cantidad total de reacciones por emoji
- Marca personal: checkmark que indica al usuario sus propias reacciones
- Protección de contenido: opción anti-forward/copiar
- Estadísticas: métricas de engagement por mensaje
- Backward compatibility: broadcasting sin gamificación sigue funcionando igual