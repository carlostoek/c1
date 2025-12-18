# INSTRUCCIONES DE TRABAJO - PROYECTO TELEGRAM BOT VIP/FREE

Guía de patrones, convenciones y flujos de desarrollo para el proyecto.

**⚠️ LECTURA INICIAL OBLIGATORIA:**

Antes de empezar cualquier tarea, **debes leer primero** `docs/Referencia_rápida.md` para entender:
- Qué está implementado en el proyecto
- Estructura técnica del sistema
- Servicios disponibles
- Modelos de BD
- Handlers y middlewares
- Arquitectura general

Este documento (CLAUDE.md) contiene **cómo trabajar** (patrones, convenciones, flujos).
El documento `docs/Referencia_rápida.md` contiene **qué está implementado** (detalles técnicos).

**Diferencia clave:**
- 📖 `docs/Referencia_rápida.md` → Lectura para entender el proyecto
- 📝 `CLAUDE.md` → Guía para saber cómo trabajar en el proyecto

═══════════════════════════════════════════════════════════════
# CONVENCIONES DE CÓDIGO
═══════════════════════════════════════════════════════════════

## Naming Conventions

```python
# Clases
PascalCase(VIPSubscriber, SubscriptionService)

# Funciones/métodos
snake_case(generate_token, check_expiry)

# Constantes
UPPER_SNAKE_CASE(DEFAULT_WAIT_TIME, MAX_TOKEN_LENGTH)

# Archivos
snake_case(admin_auth.py, vip_flow.py)
```

## Imports

```python
# Orden:
# 1. Estándar
# 2. Third-party
# 3. Local

# Alfabético dentro de cada grupo
```

## Async/Await

```python
# TODOS los handlers son async def
# TODOS los métodos de services son async def
# Usar await para llamadas DB y API Telegram
```

## Error Handling

```python
# Try-except en handlers (nunca dejar crashear el bot)
# Logger en cada módulo: logger = logging.getLogger(__name__)

# Niveles de logging:
# - DEBUG: Desarrollo y detalles internos
# - INFO: Eventos normales
# - WARNING: Problemas no críticos
# - ERROR: Fallos que interrumpen funcionalidad
# - CRITICAL: Bot no operativo
```

## Type Hints

```python
# OBLIGATORIO en signatures de funciones
def process_token(token_str: str, user_id: int) -> bool:
    pass

# Usar Optional[T] para valores opcionales
Optional[VIPSubscriber]

# Usar Union[T1, T2] cuando hay múltiples tipos
Union[Message, CallbackQuery]
```

## Docstrings

```python
# Usar Google Style
# Obligatorio en todas las clases y funciones públicas

def generate_vip_token(
    generated_by: int,
    duration_hours: int = 24
) -> InvitationToken:
    """Genera un token VIP único y seguro.

    Args:
        generated_by: ID del admin que genera el token
        duration_hours: Duración en horas (default: 24)

    Returns:
        InvitationToken con token generado

    Raises:
        ValueError: Si duration_hours < 1
    """
```

═══════════════════════════════════════════════════════════════
# PATRONES DE DESARROLLO
═══════════════════════════════════════════════════════════════

## Patrón para cada tarea

### 0. Lectura Inicial (ANTES de cualquier tarea)

**Primera vez en el proyecto o necesitas contexto técnico:**

1. Lee `docs/Referencia_rápida.md` completo
   - Entiende stack tecnológico
   - Revisa estructura del proyecto
   - Conoce servicios existentes
   - Aprende sobre modelos de BD
   - Familiarízate con handlers

2. Lee `CLAUDE.md` (este archivo) para saber cómo trabajar

3. Revisa código real de examples similares en el codebase

**En tareas subsecuentes:**
- Consulta Referencia_rápida.md para detalles técnicos específicos
- Usa CLAUDE.md para recordar patrones y convenciones

### 1. Lectura de Prompt

- Entender objetivo y contexto
- Revisar dependencias completadas
- Verificar docs/Referencia_rápida.md para servicios/handlers existentes que necesites

### 2. Planificación (TodoWrite)

```python
# Crear lista de subtareas
# Definir milestones
# Marcar como in_progress mientras trabajas
```

**Estructura de todo:**
```python
{
    "content": "Descripción en infinitivo (Implementar X, Crear Y)",
    "activeForm": "Descripción en gerundio (Implementando X, Creando Y)",
    "status": "pending | in_progress | completed"
}
```

### 3. Implementación

- Crear archivos requeridos
- Implementar métodos siguiendo especificación
- Validaciones de input
- Manejo de errores
- Logging apropiado
- Type hints completos
- Docstrings Google Style

### 4. Validación (Testing)

- Tests unitarios básicos
- Validación de comportamiento
- Manejo de edge cases
- Verificación de persistencia

### 5. Commit

```bash
# Sin referencias a herramientas externas como Claude, Claude Code.

# Mensaje describiendo cambios:
# - Líneas de código
# - Métodos implementados
# - Características clave
# - Patrones utilizados
```

**NO incluir:**
- Referencias a "Claude Code"
- Menciones a herramientas externas
- Instrucciones de trabajo

### 6. Documentación

**Información Técnica → `docs/Referencia_rápida.md`:**
- Nuevos servicios implementados
- Nuevos modelos de BD
- Nuevos handlers
- Cambios arquitectónicos
- Métodos públicos agregados
- Flujos de datos modificados

**Información de Trabajo → `CLAUDE.md` (este archivo):**
- Nuevos patrones de desarrollo
- Cambios en convenciones
- Nuevos flujos de trabajo
- Mejoras en procesos

**NUNCA crear archivos markdown nuevos sin solicitud explícita**

═══════════════════════════════════════════════════════════════
# PATRONES ARQUITECTÓNICOS
═══════════════════════════════════════════════════════════════

## Service Container (DI)

**Patrón:** Dependency Injection + Lazy Loading

```python
# Centralizar instanciación de servicios
# Lazy loading transparente (solo carga lo que usa)
# Inyectar session y bot a todos los servicios

container = ServiceContainer(session, bot)
await container.subscription.generate_vip_token(...)
```

**Usar en:** Handlers, background tasks, cualquier lugar que necesite servicios

## Singleton Pattern

**Patrón:** Una única instancia durante toda la vida de la app

```python
# BotConfig id=1 siempre retorna la misma instancia
# ConfigService gestiona acceso

config = await config_service.get_config()  # Siempre id=1
```

## Pub/Sub (EventBus)

**Patrón:** Fire-and-forget, no-blocking

```python
# Publicar evento (retorna inmediatamente)
event_bus.publish(UserJoinedVIPEvent(user_id=123, ...))

# Handler en background (aislado de errores)
@subscribe(UserJoinedVIPEvent)
async def on_vip_join(event):
    # procesar
```

**Ventajas:**
- Desacoplamiento total
- No bloquea publicador
- Error isolation (fallos en handlers no afectan otros)

## FSM (Finite State Machine)

**Patrón:** Multi-step workflows

```python
# Estados para flujos multi-paso
class ChannelSetupStates(StatesGroup):
    waiting_for_vip_channel = State()

# Handler inicia FSM
await state.set_state(ChannelSetupStates.waiting_for_vip_channel)

# Handler siguiente procesa el estado
@state_handler(ChannelSetupStates.waiting_for_vip_channel)
async def process_channel(message: Message, state: FSMContext):
    await state.clear()
```

## Middleware Pattern

**Patrón:** Pre/post processing de eventos

```python
# DatabaseMiddleware: Inyecta sesión
# AdminAuthMiddleware: Valida permisos

# Orden importa:
# 1. DatabaseMiddleware (setup)
# 2. AdminAuthMiddleware (validación)
```

═══════════════════════════════════════════════════════════════
# FLUJO DE DESARROLLO POR TAREA
═══════════════════════════════════════════════════════════════

## Paso 1: Crear todo con TodoWrite

```python
[
    {"content": "Subtarea 1", "status": "pending", "activeForm": "Haciendo 1"},
    {"content": "Subtarea 2", "status": "pending", "activeForm": "Haciendo 2"},
    {"content": "Tests", "status": "pending", "activeForm": "Escribiendo tests"},
    {"content": "Commit", "status": "pending", "activeForm": "Haciendo commit"},
]
```

## Paso 2: Marcar in_progress

- Antes de empezar trabajo real
- Solo UN todo en in_progress
- Cambiar cuando terminas

## Paso 3: Marcar completed

- INMEDIATAMENTE después de terminar
- No batches de completados
- Pasar al siguiente in_progress

## Paso 4: Commit

git add .
git commit -m "Mensaje descriptivo

- Líneas de código: 150
- Métodos: create_X, delete_X, validate_X
- Características: Feature A, Feature B
- Patrones: Singleton, DI
"

═══════════════════════════════════════════════════════════════
# GUÍA DE TESTING
═══════════════════════════════════════════════════════════════

## Estructura de Tests

```
tests/
├── conftest.py          # Fixtures compartidos
├── test_e2e_*.py        # E2E por feature
├── test_integration_*.py # Integración
├── test_a*.py           # ONDA 3 features
└── test_b*.py           # ONDA 3 features
```

## Fixtures Compartidos

```python
@pytest.fixture
def event_loop():
    """Event loop para tests async"""

@pytest.fixture(autouse=True)
def db_setup():
    """Inicializa/limpia BD automáticamente"""

@pytest.fixture
def mock_bot():
    """Mock del bot con AsyncMocks"""
```

## E2E vs Integration

**E2E:**
- Flujo completo del usuario
- Múltiples servicios integrados
- Simula comportamiento real

**Integration:**
- Servicios interactúan
- Sin interfaz de usuario
- Valida contratos entre servicios

## Ejecución

```bash
# Todos los tests
pytest tests/ -v

# Un archivo específico
pytest tests/test_e2e_vip.py -v

# Con cobertura
pytest tests/ --cov=bot

# Script helper
bash scripts/run_tests.sh
```

═══════════════════════════════════════════════════════════════
# CONVENCIONES DE BASES DE DATOS
═══════════════════════════════════════════════════════════════

## Transacciones

```python
# Usar context managers
async with get_session() as session:
    # Auto commit/rollback
    # Si excepción: rollback automático
```

## Queries

```python
# SQLAlchemy 2.0+ style (select)
from sqlalchemy import select

stmt = select(VIPSubscriber).where(VIPSubscriber.user_id == user_id)
result = await session.execute(stmt)
subscriber = result.scalar_one_or_none()
```

## Validaciones

```python
# Validar en entrada (handlers)
# Validar lógica en services
# Validar persistencia en tests

# Nunca confiar en input del usuario
```

═══════════════════════════════════════════════════════════════
# CONVENCIONES DE HANDLERS
═══════════════════════════════════════════════════════════════

## Estructura

```python
async def handler_name(message: Message, state: FSMContext) -> None:
    """Descripción breve del handler.

    Args:
        message: Mensaje del usuario
        state: FSM context para mantener estado
    """
    try:
        # Obtener sesión inyectada por middleware
        session = state.data["session"]
        container = ServiceContainer(session, state.bot)

        # Lógica
        result = await container.subscription.some_method()

        # Respuesta
        await message.answer(...)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await message.answer("Hubo un error, intenta de nuevo.")
```

## Inyección de Dependencias

```python
# Session inyectada por DatabaseMiddleware
session = state.data["session"]

# Container proporciona servicios
container = ServiceContainer(session, state.bot)

# Usar: await container.service.method()
```

## Manejo de Errores

```python
try:
    # Lógica
except ValueError as e:
    # Error validación
    await message.answer(f"Entrada inválida: {e}")
except ChannelNotConfigured as e:
    # Error específico del dominio
    await message.answer("Canal no configurado")
except Exception as e:
    # Fallback
    logger.error(f"Unexpected error: {e}", exc_info=True)
    await message.answer("Error inesperado")
```

═══════════════════════════════════════════════════════════════
# CONVENCIONES DE SERVICIOS
═══════════════════════════════════════════════════════════════

## Estructura

```python
class MyService:
    """Descripción del servicio."""

    def __init__(self, session: AsyncSession, bot: Bot):
        self._session = session
        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def public_method(self) -> ReturnType:
        """Descripción pública.

        Returns:
            Qué retorna

        Raises:
            Qué excepciones
        """
        # Implementación

    async def _private_method(self) -> None:
        """Métodos privados con _ prefix."""
```

## Responsabilidades

- ONE thing bien definido
- No mezclar lógica de negocio con Telegram API
- Delegar Telegram API a ChannelService

## Logging

```python
logger = logging.getLogger(__name__)

logger.info(f"Token generado: {token}")
logger.warning(f"Canal no configurado")
logger.error(f"Error al expulsar VIP", exc_info=True)
```

═══════════════════════════════════════════════════════════════
# MANEJO DE CONFIGURACIÓN
═══════════════════════════════════════════════════════════════

## Acceso a Config

```python
# SIEMPRE usar ConfigService, nunca acceso directo a BD
config = await config_service.get_config()

# Con validación
if not config_service.is_fully_configured():
    logger.warning("Bot no está completamente configurado")
```

## Validación

```python
# ConfigService valida automáticamente
await config_service.set_wait_time(5)  # OK
await config_service.set_wait_time(0)  # ValueError: >= 1
```

═══════════════════════════════════════════════════════════════
# PATRONES DE KEYBOARD
═══════════════════════════════════════════════════════════════

## Factory Functions

```python
# Factory pattern para reutilización

def create_inline_keyboard(buttons_dict: Dict[str, str]) -> InlineKeyboardMarkup:
    """Crea keyboard desde dict de botones.

    Args:
        buttons_dict: {"Texto": "callback_data"}

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text=text, callback_data=data)]
        for text, data in buttons_dict.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

## Callbacks

```python
# Formato: "namespace:action"
# Ejemplo: "admin:main", "vip:setup", "token:redeem"

# En handler
query.answer(
    text="Confirmado",
    alert=False  # Toast notification
)
```

═══════════════════════════════════════════════════════════════
# PATRONES DE VALIDACIÓN
═══════════════════════════════════════════════════════════════

## Input Validation

```python
# En handlers, SIEMPRE validar entrada

if not message.text:
    await message.answer("Por favor envía texto")
    return

# Validar contenido
if not message.text.isdigit():
    await message.answer("Debe ser un número")
    return
```

## Domain Validation

```python
# En services, validar lógica del dominio

async def create_free_request(self, user_id: int) -> FreeChannelRequest:
    # Validar usuario no tenga solicitud pendiente
    existing = await self.get_free_request(user_id)
    if existing and existing.status == "pending":
        raise DuplicateRequest(f"Usuario {user_id} ya tiene solicitud pendiente")
```

## Custom Exceptions

```python
# Usar excepciones personalizadas del dominio

class DuplicateRequest(Exception):
    """Usuario ya tiene solicitud pendiente"""

class ChannelNotConfigured(Exception):
    """Canal VIP/Free no está configurado"""

class TokenExpired(Exception):
    """Token expiró o no existe"""
```

═══════════════════════════════════════════════════════════════
# PATRONES DE BACKGROUND TASKS
═══════════════════════════════════════════════════════════════

## APScheduler

```python
# IntervalTrigger: cada N minutos/segundos
scheduler.add_job(
    task_function,
    IntervalTrigger(minutes=60),
    max_instances=1  # Prevenir ejecuciones simultáneas
)

# CronTrigger: en hora específica
scheduler.add_job(
    cleanup_task,
    CronTrigger(hour=3, minute=0, timezone="UTC"),
    max_instances=1
)
```

## Error Handling en Tasks

```python
async def background_task():
    try:
        # Lógica
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        # NO crashear scheduler
        # Continuar con siguiente iteración
```

## Lifecycle

```python
# main.py on_startup
start_background_tasks(bot)

# main.py on_shutdown
stop_background_tasks()
```

═══════════════════════════════════════════════════════════════
# PATRONES DE EVENTOS (EVENT BUS)
═══════════════════════════════════════════════════════════════

## Definir Eventos

```python
# bot/events/types.py
@dataclass
class UserJoinedVIPEvent(Event):
    user_id: int
    plan_name: str
    duration_days: int
```

## Suscribir a Eventos

```python
from bot.events import subscribe, UserJoinedVIPEvent

@subscribe(UserJoinedVIPEvent)
async def on_vip_join(event):
    """Handler ejecuta en background, no bloquea."""
    logger.info(f"User {event.user_id} joined VIP")
```

## Publicar Eventos

```python
from bot.events import event_bus

# Fire-and-forget (retorna inmediatamente)
event_bus.publish(UserJoinedVIPEvent(
    user_id=123,
    plan_name="Mensual",
    duration_days=30
))
```

## Ventajas

- Desacoplamiento: servicios no conocen sobre otros
- Escalabilidad: agregar listeners sin modificar código
- Testeable: publishers y subscribers se prueban por separado

═══════════════════════════════════════════════════════════════
# GUÍA DE SEGURIDAD
═══════════════════════════════════════════════════════════════

## Validación de Admin

```python
# SIEMPRE validar antes de operaciones sensibles

if not await config_service.is_admin(user_id):
    logger.warning(f"Non-admin {user_id} tried admin operation")
    return  # No ejecutar
```

## Sanitización de Input

```python
from html import escape

# Escapar HTML para Telegram
safe_text = escape(user_input)
await message.answer(f"Recibido: {safe_text}")
```

## Tokens Seguros

```python
import secrets

# Generar tokens seguros
token = secrets.token_urlsafe(32)  # URL-safe, aleatorio

# Nunca loguear tokens completos
logger.info(f"Token generado: {token[:8]}...")
```

## Expiración de Tokens

```python
# SIEMPRE agregar expiración
expires_at = datetime.now(UTC) + timedelta(hours=24)

# Validar antes de usar
if token.expires_at < datetime.now(UTC):
    raise TokenExpired("Token expiró")
```

═══════════════════════════════════════════════════════════════
# GUÍA DE PERFORMANCE
═══════════════════════════════════════════════════════════════

## Database Queries

```python
# ❌ N+1 problem
for user_id in user_ids:
    stmt = select(VIPSubscriber).where(VIPSubscriber.user_id == user_id)
    result = await session.execute(stmt)  # Query en loop

# ✅ Batch query
stmt = select(VIPSubscriber).where(VIPSubscriber.user_id.in_(user_ids))
results = await session.execute(stmt)
```

## Caching

```python
# Para datos que no cambian frecuentemente
# Usar cache simples o Redis

cached_config = None

async def get_config_cached():
    global cached_config
    if cached_config is None:
        cached_config = await config_service.get_config()
    return cached_config
```

## Lazy Loading

```python
# ServiceContainer solo carga servicios usados
# Evita inicializar todo al startup

container.subscription  # Se carga solo si accedes
```

═══════════════════════════════════════════════════════════════
# GESTIÓN DE ESTADO Y CLEANUP
═══════════════════════════════════════════════════════════════

## State Cleanup

```python
# SIEMPRE limpiar estado después de FSM

async def process_input(message: Message, state: FSMContext):
    # Procesar
    result = await service.do_something()

    # Limpiar
    await state.clear()

    # Responder
    await message.answer("Hecho!")
```

## Error Recovery

```python
# Mantener estado en errores recuperables
# Limpiar solo cuando completa o usuario cancela

try:
    result = await service.do_something()
except RecoverableError:
    await message.answer("Intenta de nuevo")
    # State sigue siendo igual
except FatalError:
    await state.clear()
    await message.answer("Cancelado")
```

═══════════════════════════════════════════════════════════════
# DOCUMENTACIÓN DE CÓDIGO
═══════════════════════════════════════════════════════════════

## Qué Documentar

- **Clases públicas:** Descripción y responsabilidades
- **Métodos públicos:** Args, Returns, Raises
- **Métodos complejos:** Lógica interna en comentarios
- **Excepciones:** Cuándo se lanzan

## Qué NO Documentar

- Código obvio (if/else simple)
- Variables con nombres claros
- Lógica straightforward

## Ejemplo

```python
def redeem_vip_token(self, token_str: str, user_id: int) -> VIPSubscriber:
    """Canjea token y activa suscripción VIP.

    Args:
        token_str: Token generado
        user_id: ID usuario canjeando

    Returns:
        VIPSubscriber con suscripción activa

    Raises:
        TokenExpired: Si token expiró
        TokenAlreadyUsed: Si ya fue canjeado
        ChannelNotConfigured: Si canal VIP no existe
    """
```

═══════════════════════════════════════════════════════════════
# CONVENCIONES DE COMMITS
═══════════════════════════════════════════════════════════════

## Formato

```
feat/fix/refactor: descripción breve

Body con detalles técnicos:
- Archivos modificados
- Métodos agregados
- Cambios arquitectónicos

```

## Tipos de Commit

- **feat**: Nueva característica
- **fix**: Corrección de bug
- **refactor**: Cambio de estructura sin cambiar comportamiento
- **docs**: Cambios en documentación
- **test**: Agregar/modificar tests
- **chore**: Tareas de mantenimiento

## NO Incluir

- Referencias a "Claude Code"
- Instrucciones de trabajo
- "Generated with X tool"
- Mentions a herramientas externas

═══════════════════════════════════════════════════════════════
# GESTIÓN DE DOCUMENTACIÓN
═══════════════════════════════════════════════════════════════

## Responsabilidades de cada documento

### 📖 docs/Referencia_rápida.md (LECTURA OBLIGATORIA INICIAL)

**Propósito:** Referencia técnica del proyecto. QUÉ está implementado.

**Actualizar cuando:**
- Implementes nuevos servicios
- Agregues nuevos modelos de BD
- Crees nuevos handlers
- Modifiques arquitectura
- Agregues métodos públicos
- Cambies flujos de datos

**Incluir:**
- Stack tecnológico y librerías
- Estructura del proyecto
- Modelos de BD
- Servicios y sus métodos
- Middlewares
- States FSM
- Handlers
- Keyboards
- Background tasks
- Formatters y utilities
- Testing
- Flujos principales
- Estadísticas finales

**NO incluir:**
- Instrucciones de trabajo
- Patrones de desarrollo
- Convenciones (ya incluidas)
- Cómo hacer tareas
- Información de procesos

### 📝 CLAUDE.md (este archivo)

**Propósito:** Guía de desarrollo. CÓMO trabajar en el proyecto.

**Actualizar cuando:**
- Cambien patrones de desarrollo
- Modifiques convenciones
- Agregues nuevos flujos de trabajo
- Mejores procesos

**Incluir:**
- Convenciones de código
- Patrones arquitectónicos
- Flujos de desarrollo
- Guías de testing
- Patrones de handlers/servicios
- Validación y seguridad
- Performance
- Best practices
- Resolución de problemas

**NO incluir:**
- Información técnica
- Detalles de implementación
- Stack tecnológico
- Detalles de servicios

## Flujo de Actualización Correcto

```
Después de implementar algo:

1. ✅ Código implementado y testeado
2. ✅ Git commit realizado
3. ✅ Actualizar docs/Referencia_rápida.md (información técnica)
4. ✅ Actualizar CLAUDE.md SOLO si hay cambios en procesos/patrones
```

## Mantener Separación Clara

```
CLAUDE.md = Cómo trabajar (instructor, guía)
docs/Referencia_rápida.md = Qué hay implementado (referencia técnica)
```

Ambos documentos trabajan juntos:
- Lees Referencia_rápida.md → Entiendes qué existe
- Lees CLAUDE.md → Entiendes cómo trabajar con ello

═══════════════════════════════════════════════════════════════
# BEST PRACTICES
═══════════════════════════════════════════════════════════════

## Evitar Over-Engineering

- ✅ Solución simple para problema actual
- ❌ Abstracción para caso hipotético futuro
- ❌ Configurabilidad innecesaria

## Single Responsibility

- ✅ Service hace UNA cosa bien
- ❌ Service hace 5 cosas diferentes

## Don't Repeat Yourself (DRY)

- ✅ Extraer a función reutilizable (cuando se repite 2+ veces)
- ❌ Extraer todo a función (sobre-ingeniería)

## Fail Fast

- ✅ Validar entrada temprano
- ✅ Fallar explícitamente
- ❌ Continuar con datos inválidos

## Async Safety

- ✅ await en llamadas async
- ✅ asyncio.create_task para fire-and-forget
- ❌ Bloquear event loop

═══════════════════════════════════════════════════════════════
# RESOLUCIÓN DE PROBLEMAS
═══════════════════════════════════════════════════════════════

## Tests Fallan

1. Revisar logs completos con `-s`
2. Agregar prints en código
3. Ejecutar test específico con `-k`
4. Verificar fixtures en conftest.py

## Bot Crashea

1. Revisar exception en handler
2. Agregar try-except para capturar
3. Loguear con exc_info=True
4. Nunca silenciar excepciones

## Base de Datos

1. Verificar estado de transacción
2. Validar query con SQL directo
3. Limpiar .db y reiniciar
4. Revisar WAL logs si corrupción

## Performance

1. Usar `pytest --profile` para profiling
2. Identificar N+1 queries
3. Agregar indexes en queries frecuentes
4. Implementar caching si apropiado
