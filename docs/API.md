# Referencia de API Interna

Guía de métodos, funciones públicas y puntos de integración del bot.

## Tabla de Contenidos

1. [Configuración (Config)](#configuración)
2. [Base de Datos (Database)](#base-de-datos)
3. [Modelos (Models)](#modelos)
4. [Servicios (Services)](#servicios-planeados)
5. [Aiogram API](#aiogram-api-telegram)

## Configuración

### Módulo: `config.py`

#### Clase: `Config`

Configuración global del bot con validación.

**Variables de Clase:**

```python
# Telegram
Config.BOT_TOKEN: str
Config.ADMIN_USER_IDS: List[int]

# Database
Config.DATABASE_URL: str

# Canales
Config.VIP_CHANNEL_ID: Optional[str]
Config.FREE_CHANNEL_ID: Optional[str]

# Tiempos
Config.DEFAULT_WAIT_TIME_MINUTES: int
Config.DEFAULT_TOKEN_DURATION_HOURS: int
Config.TOKEN_LENGTH: int

# Limpieza
Config.CLEANUP_INTERVAL_MINUTES: int
Config.PROCESS_FREE_QUEUE_MINUTES: int

# Logging
Config.LOG_LEVEL: str
Config.MAX_VIP_SUBSCRIBERS: int
```

**Métodos de Clase:**

```python
@classmethod
def validate() -> bool:
    """
    Valida configuración mínima.

    Requerido:
    - BOT_TOKEN (longitud > 20)
    - ADMIN_USER_IDS (al menos 1)
    - DATABASE_URL

    Returns:
        True si válida, False en error
    """

@classmethod
def load_admin_ids() -> List[int]:
    """
    Carga y parsea IDs de admins desde ADMIN_USER_IDS.

    Formato en .env: "123456,789012,345678"

    Returns:
        Lista de IDs de administradores
    """

@classmethod
def is_admin(user_id: int) -> bool:
    """
    Verifica si usuario es administrador.

    Args:
        user_id: ID de Telegram

    Returns:
        True si es admin, False en caso contrario
    """

@classmethod
def setup_logging() -> None:
    """
    Configura logging según LOG_LEVEL.

    Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """

@classmethod
def get_summary() -> str:
    """
    Retorna resumen de configuración (para logging).

    Oculta información sensible (token truncado).

    Returns:
        String formateado con resumen
    """
```

**Ejemplo de Uso:**

```python
from config import Config

# Validar
if not Config.validate():
    print("Configuración inválida")
    exit(1)

# Verificar permisos
if not Config.is_admin(user_id):
    print("Usuario no es admin")

# Obtener valor
wait_time = Config.DEFAULT_WAIT_TIME_MINUTES
```

## Base de Datos

### Módulo: `bot/database/engine.py`

#### Funciones de Engine

```python
def get_engine() -> AsyncEngine:
    """
    Retorna engine de SQLAlchemy.

    Debe estar inicializado con init_db() primero.

    Returns:
        AsyncEngine configurado

    Raises:
        RuntimeError: Si init_db() no fue llamado
    """

def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Retorna factory de sesiones async.

    Debe estar inicializado con init_db() primero.

    Returns:
        async_sessionmaker[AsyncSession]

    Raises:
        RuntimeError: Si init_db() no fue llamado
    """

def get_session() -> SessionContextManager:
    """
    Context manager para sesión de BD.

    Uso:
        async with get_session() as session:
            # Operaciones
            # Auto-commit si éxito
            # Auto-rollback si error

    Returns:
        SessionContextManager para usar en async with

    Example:
        async with get_session() as session:
            query = select(User)
            result = await session.execute(query)
            users = result.scalars().all()
    """

async def init_db() -> None:
    """
    Inicializa base de datos.

    Tareas:
    1. Crear engine async
    2. Configurar SQLite (WAL, pragmas)
    3. Crear tablas
    4. Crear session factory
    5. Crear BotConfig initial (singleton)

    Raises:
        Exception: Si hay error en inicialización
    """

async def close_db() -> None:
    """
    Cierra conexiones de base de datos.

    Debe llamarse en on_shutdown de main.py.

    Limpiar recursos correctamente.
    """
```

**Contexto Manager:**

```python
class SessionContextManager:
    """Context manager para AsyncSession con auto-commit/rollback"""

    async def __aenter__(self) -> AsyncSession:
        """Retorna la sesión"""

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit si éxito, rollback si error, siempre cierra"""
```

**Ejemplo de Uso:**

```python
from bot.database import init_db, close_db, get_session, BotConfig

# En on_startup
await init_db()

# En handler/servicio
async with get_session() as session:
    config = await session.get(BotConfig, 1)
    config.vip_channel_id = "-100123456789"
    await session.commit()

# En on_shutdown
await close_db()
```

## Modelos

### Módulo: `bot/database/models.py`

#### BotConfig

Tabla singleton de configuración global.

**Atributos:**

```python
id: int                              # Primary key (siempre 1)
vip_channel_id: Optional[str]       # ID del canal VIP
free_channel_id: Optional[str]      # ID del canal Free
wait_time_minutes: int              # Minutos espera Free
vip_reactions: List[str]            # Emojis reacciones VIP
free_reactions: List[str]           # Emojis reacciones Free
subscription_fees: Dict             # Tarifas {"monthly": 10, "yearly": 100}
created_at: datetime                # Timestamp creación
updated_at: datetime                # Timestamp actualización
```

**Métodos:**

```python
def __repr__(self) -> str:
    """Representación string del objeto"""
```

**Ejemplo de Uso:**

```python
async with get_session() as session:
    # Obtener
    config = await session.get(BotConfig, 1)

    # Actualizar
    config.wait_time_minutes = 10
    await session.commit()

    # Acceder campos
    vip_id = config.vip_channel_id
    fees = config.subscription_fees
```

#### InvitationToken

Tokens de invitación VIP.

**Atributos:**

```python
id: int                             # Primary key
token: str                          # Token único (16 chars)
generated_by: int                   # User ID admin que creó
created_at: datetime                # Timestamp creación
duration_hours: int                 # Horas de validez
used: bool                          # Si fue canjeado
used_by: Optional[int]              # User ID que canjeó
used_at: Optional[datetime]         # Timestamp uso
subscribers: List[VIPSubscriber]    # Relación 1:N
```

**Métodos:**

```python
def is_expired(self) -> bool:
    """Verifica si token expiró"""

def is_valid(self) -> bool:
    """Verifica si puede usarse (no usado y no expirado)"""

def __repr__(self) -> str:
    """Representación string"""
```

**Índices:**

```
idx_token_used_created: (used, created_at)
idx_token: UNIQUE(token)
```

**Ejemplo de Uso:**

```python
from sqlalchemy import select

async with get_session() as session:
    # Crear token
    token = InvitationToken(
        token="ABC123XYZ456789",
        generated_by=admin_id,
        duration_hours=24
    )
    session.add(token)
    await session.commit()

    # Buscar por valor
    query = select(InvitationToken).where(
        InvitationToken.token == "ABC123XYZ456789"
    )
    result = await session.execute(query)
    token = result.scalar_one_or_none()

    # Validar
    if token and token.is_valid():
        # Usar token
        pass

    # Marcar como usado
    token.used = True
    token.used_by = user_id
    token.used_at = datetime.utcnow()
    await session.commit()
```

#### VIPSubscriber

Suscriptores VIP.

**Atributos:**

```python
id: int                             # Primary key
user_id: int                        # User ID (UNIQUE)
join_date: datetime                 # Timestamp suscripción
expiry_date: datetime               # Fecha expiración
status: str                         # "active" o "expired"
token_id: int                       # FK a InvitationToken
token: InvitationToken              # Relación N:1
```

**Métodos:**

```python
def is_expired(self) -> bool:
    """Verifica si suscripción expiró"""

def days_remaining(self) -> int:
    """Retorna días restantes (negativo si expirado)"""

def __repr__(self) -> str:
    """Representación string"""
```

**Índices:**

```
idx_status_expiry: (status, expiry_date)
idx_user_id: UNIQUE(user_id)
```

**Ejemplo de Uso:**

```python
async with get_session() as session:
    # Crear
    from datetime import timedelta
    subscriber = VIPSubscriber(
        user_id=987654321,
        token_id=token.id,
        expiry_date=datetime.utcnow() + timedelta(hours=24),
        status="active"
    )
    session.add(subscriber)
    await session.commit()

    # Buscar activo
    query = select(VIPSubscriber).where(
        VIPSubscriber.user_id == user_id
    )
    result = await session.execute(query)
    sub = result.scalar_one_or_none()

    # Verificar estado
    if sub and not sub.is_expired():
        days = sub.days_remaining()
        print(f"Válido {days} días")
```

#### FreeChannelRequest

Solicitudes de acceso Free.

**Atributos:**

```python
id: int                             # Primary key
user_id: int                        # User ID
request_date: datetime              # Timestamp solicitud
processed: bool                     # Si fue procesada
processed_at: Optional[datetime]    # Timestamp procesamiento
```

**Métodos:**

```python
def minutes_since_request(self) -> int:
    """Retorna minutos desde solicitud"""

def is_ready(self, wait_time_minutes: int) -> bool:
    """Verifica si cumplió tiempo espera"""

def __repr__(self) -> str:
    """Representación string"""
```

**Índices:**

```
idx_user_date: (user_id, request_date)
idx_processed_date: (processed, request_date)
```

**Ejemplo de Uso:**

```python
async with get_session() as session:
    # Crear solicitud
    request = FreeChannelRequest(user_id=111111111)
    session.add(request)
    await session.commit()

    # Buscar pendientes listas
    query = select(FreeChannelRequest).where(
        FreeChannelRequest.processed == False
    ).order_by(FreeChannelRequest.request_date)
    result = await session.execute(query)
    requests = result.scalars().all()

    ready = [
        r for r in requests
        if r.is_ready(Config.DEFAULT_WAIT_TIME_MINUTES)
    ]

    # Procesar
    for req in ready:
        await invite_to_free_channel(req.user_id)
        req.processed = True
        req.processed_at = datetime.utcnow()

    await session.commit()
```

## Servicios (Planeados)

### Módulo: `bot/services/subscription.py`

Ver [SERVICES.md](./SERVICES.md) para referencia completa.

**Métodos principales:**

```python
class SubscriptionService:
    async def generate_token(admin_id: int, duration_hours: int) -> str
    async def validate_token(token: str) -> bool
    async def redeem_token(user_id: int, token: str) -> VIPSubscriber
    async def get_active_subscriber(user_id: int) -> Optional[VIPSubscriber]
    async def renew_subscription(user_id: int, duration_hours: int) -> VIPSubscriber
    async def list_expiring_subscribers(days: int) -> List[VIPSubscriber]
    async def cleanup_expired_subscriptions() -> int
    async def create_free_request(user_id: int) -> FreeChannelRequest
    async def get_pending_free_requests(ready_only: bool) -> List[FreeChannelRequest]
    async def process_free_request(request_id: int) -> FreeChannelRequest
```

### Módulo: `bot/services/channel.py`

Ver [SERVICES.md](./SERVICES.md) para referencia completa.

**Métodos principales:**

```python
class ChannelService:
    async def invite_to_vip_channel(user_id: int) -> bool
    async def invite_to_free_channel(user_id: int) -> bool
    async def remove_from_channel(channel_id: str, user_id: int) -> bool
    async def get_channel_info(channel_id: str) -> Optional[dict]
```

### Módulo: `bot/services/config.py`

Ver [SERVICES.md](./SERVICES.md) para referencia completa.

**Métodos principales:**

```python
class ConfigService:
    async def get_config() -> BotConfig
    async def set_vip_channel(channel_id: str) -> None
    async def set_free_channel(channel_id: str) -> None
    async def set_wait_time(minutes: int) -> None
    async def set_reactions(vip_reactions: List[str], free_reactions: List[str]) -> None
    async def set_subscription_fees(monthly: float, yearly: float) -> None
```

## Aiogram API (Telegram)

### Bot API

```python
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

bot = Bot(token=Config.BOT_TOKEN, parse_mode="HTML")

# Enviar mensaje
await bot.send_message(
    chat_id=user_id,
    text="<b>Mensaje</b>",
    parse_mode="HTML",
    reply_markup=teclado
)

# Responder mensaje
await message.answer(
    "Respuesta",
    reply_markup=teclado
)

# Editar mensaje
await callback.message.edit_text(
    "Texto actualizado",
    reply_markup=new_keyboard
)

# Responder callback
await callback.answer("Notificación", show_alert=False)

# Invitar a canal
await bot.add_chat_member(
    chat_id=channel_id,
    user_id=user_id
)

# Remover de canal
await bot.ban_chat_member(
    chat_id=channel_id,
    user_id=user_id
)

# Obtener info del bot
bot_info = await bot.get_me()

# Obtener info del canal
chat = await bot.get_chat(channel_id)
member_count = await bot.get_chat_member_count(channel_id)
```

### Dispatcher

```python
from aiogram import Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

# Crear storage y dispatcher
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Registrar router
router = Router()
dp.include_router(router)

# Registrar handlers
@router.message.command("comando")
async def handler(message: Message):
    await message.answer("Respuesta")

# Registrar middleware
dp.message.middleware(SomeMiddleware())

# Registrar callbacks
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)
```

### Types

```python
from aiogram.types import (
    Message,        # Mensaje de usuario
    CallbackQuery,  # Click en botón inline
    User,          # Información del usuario
    Chat,          # Información del chat
    Update,        # Update general de Telegram
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

# Message
message.text               # Texto del mensaje
message.from_user          # Usuario que envió
message.from_user.id       # User ID
message.from_user.username # @username
message.from_user.first_name
message.chat.id            # Chat ID
message.message_id         # ID del mensaje
message.date               # Timestamp

# CallbackQuery
callback.from_user         # Usuario que presionó botón
callback.data              # Datos del botón presionado
callback.message           # Mensaje del botón
callback.answer()          # Responder (notificación)

# Crear teclado
keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Botón 1", callback_data="btn1"),
        InlineKeyboardButton(text="Botón 2", callback_data="btn2"),
    ],
    [
        InlineKeyboardButton(text="Botón 3", callback_data="btn3"),
    ],
])
```

### FSM

```python
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class MyStates(StatesGroup):
    state1 = State()
    state2 = State()

# Usar en handler
async def handler(message: Message, state: FSMContext):
    # Cambiar estado
    await state.set_state(MyStates.state1)

    # Guardar datos
    await state.update_data(valor="datos")

    # Obtener datos
    data = await state.get_data()
    valor = data.get("valor")

    # Limpiar
    await state.clear()
```

## Estructuras de Datos Comunes

### Respuesta de Consulta

```python
from sqlalchemy import select

query = select(Model).where(condition)
result = await session.execute(query)

# Un resultado
obj = result.scalar_one_or_none()  # None si no existe

# Múltiples resultados
objs = result.scalars().all()       # Lista (vacía si ninguno)

# Con offset/limit
query = query.offset(10).limit(5)
```

### Error Handling

```python
try:
    # Operación
    pass
except ValueError as e:
    # Error de validación
    logger.warning(f"Validación: {e}")
except Exception as e:
    # Error inesperado
    logger.error(f"Error: {e}", exc_info=True)
```

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
