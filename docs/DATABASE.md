# Documentación de Base de Datos

Guía completa sobre modelos de datos, relaciones, esquema y operaciones de base de datos.

## Resumen de Modelos

El bot utiliza 4 modelos principales en SQLite 3.x con SQLAlchemy 2.0.25:

| Modelo | Propósito | Registros por día (estimado) |
|--------|----------|------------------------------|
| `BotConfig` | Singleton con configuración global | 1 (siempre) |
| `InvitationToken` | Tokens VIP generados por admins | 10-100 |
| `VIPSubscriber` | Usuarios con suscripción VIP activa | 5-50 |
| `FreeChannelRequest` | Cola de espera para acceso Free | 50-500 |

## Modelo 1: BotConfig

**Descripción:** Tabla singleton que almacena configuración global del bot.

**Tabla:** `bot_config`

### Estructura

```python
class BotConfig(Base):
    __tablename__ = "bot_config"

    # Identificador (siempre 1)
    id: int = Column(Integer, primary_key=True, default=1)

    # IDs de canales
    vip_channel_id: Optional[str] = Column(String(50), nullable=True)
    free_channel_id: Optional[str] = Column(String(50), nullable=True)

    # Configuración
    wait_time_minutes: int = Column(Integer, default=5)
    vip_reactions: List[str] = Column(JSON, default=list)
    free_reactions: List[str] = Column(JSON, default=list)
    subscription_fees: Dict = Column(JSON, default={"monthly": 10, "yearly": 100})

    # Metadata
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Campos Detallados

| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `id` | INTEGER | 1 | PK, siempre 1 (singleton) |
| `vip_channel_id` | VARCHAR(50) | NULL | ID del canal VIP (@canal_vip) |
| `free_channel_id` | VARCHAR(50) | NULL | ID del canal Free (@canal_free) |
| `wait_time_minutes` | INTEGER | 5 | Minutos de espera para Free |
| `vip_reactions` | JSON | [] | Array de reacciones VIP |
| `free_reactions` | JSON | [] | Array de reacciones Free |
| `subscription_fees` | JSON | {...} | Tarifas de suscripción |
| `created_at` | DATETIME | NOW | Timestamp de creación |
| `updated_at` | DATETIME | NOW | Timestamp de última actualización |

### Ejemplo de Dato

```json
{
    "id": 1,
    "vip_channel_id": "-1001234567890",
    "free_channel_id": "-1001234567891",
    "wait_time_minutes": 5,
    "vip_reactions": ["👍", "❤️", "🔥"],
    "free_reactions": ["👍", "👎"],
    "subscription_fees": {
        "monthly": 10,
        "yearly": 100
    },
    "created_at": "2025-12-10T22:30:45.123456",
    "updated_at": "2025-12-11T10:15:30.654321"
}
```

### Operaciones Comunes

```python
# Obtener configuración global
async with get_session() as session:
    config = await session.get(BotConfig, 1)

    # Acceder campos
    vip_channel = config.vip_channel_id
    wait_minutes = config.wait_time_minutes

# Actualizar configuración
async with get_session() as session:
    config = await session.get(BotConfig, 1)
    config.vip_channel_id = "-1001234567890"
    config.wait_time_minutes = 10
    await session.commit()

# Actualizar reacciones
async with get_session() as session:
    config = await session.get(BotConfig, 1)
    config.vip_reactions = ["👍", "❤️", "🔥", "🎉"]
    await session.commit()
```

## Modelo 2: InvitationToken

**Descripción:** Tokens de invitación generados por administradores para acceso VIP.

**Tabla:** `invitation_tokens`

### Estructura

```python
class InvitationToken(Base):
    __tablename__ = "invitation_tokens"

    # Identificador
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # Token único
    token: str = Column(String(16), unique=True, nullable=False, index=True)

    # Generación
    generated_by: int = Column(BigInteger, nullable=False)  # User ID del admin
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_hours: int = Column(Integer, default=24, nullable=False)

    # Uso
    used: bool = Column(Boolean, default=False, nullable=False, index=True)
    used_by: Optional[int] = Column(BigInteger, nullable=True)  # User ID que usó
    used_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relación
    subscribers: List[VIPSubscriber] = relationship(
        "VIPSubscriber",
        back_populates="token",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index('idx_token_used_created', 'used', 'created_at'),
    )

    # Métodos
    def is_expired(self) -> bool:
        """Verifica si el token expiró"""
        expiry_time = self.created_at + timedelta(hours=self.duration_hours)
        return datetime.utcnow() > expiry_time

    def is_valid(self) -> bool:
        """Verifica si el token puede usarse (no usado y no expirado)"""
        return not self.used and not self.is_expired()
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único |
| `token` | VARCHAR(16) | UNIQUE, INDEX | Token alfanumérico único |
| `generated_by` | BIGINT | NOT NULL | User ID del admin que creó |
| `created_at` | DATETIME | NOT NULL | Timestamp de creación |
| `duration_hours` | INTEGER | NOT NULL, DEFAULT 24 | Horas de validez |
| `used` | BOOLEAN | NOT NULL, DEFAULT FALSE, INDEX | Si fue canjeado |
| `used_by` | BIGINT | NULL | User ID que canjeó |
| `used_at` | DATETIME | NULL | Timestamp de canje |

### Índices

```sql
-- Búsqueda de tokens válidos (no usados, recientes)
CREATE INDEX idx_token_used_created
ON invitation_tokens(used, created_at);

-- Búsqueda por token
CREATE UNIQUE INDEX idx_token
ON invitation_tokens(token);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "token": "ABC123XYZ456789",
    "generated_by": 123456789,
    "created_at": "2025-12-11T10:00:00.000000",
    "duration_hours": 24,
    "used": false,
    "used_by": null,
    "used_at": null
}
```

Token usado:
```json
{
    "id": 2,
    "token": "DEF456UVW789ABC",
    "generated_by": 123456789,
    "created_at": "2025-12-11T10:00:00.000000",
    "duration_hours": 24,
    "used": true,
    "used_by": 987654321,
    "used_at": "2025-12-11T11:30:45.123456"
}
```

### Operaciones Comunes

```python
# Generar token único
import secrets
import string

def generate_token() -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))

# Crear token
async with get_session() as session:
    token = InvitationToken(
        token=generate_token(),
        generated_by=admin_user_id,
        duration_hours=24
    )
    session.add(token)
    await session.commit()

# Buscar token por valor
from sqlalchemy import select

async with get_session() as session:
    query = select(InvitationToken).where(
        InvitationToken.token == "ABC123XYZ456789"
    )
    result = await session.execute(query)
    token = result.scalar_one_or_none()

# Buscar tokens válidos (no usados y no expirados)
async with get_session() as session:
    query = select(InvitationToken).where(
        InvitationToken.used == False
    ).order_by(InvitationToken.created_at.desc())
    result = await session.execute(query)
    tokens = result.scalars().all()

    valid_tokens = [t for t in tokens if not t.is_expired()]

# Marcar token como usado
async with get_session() as session:
    token = await session.get(InvitationToken, 1)
    token.used = True
    token.used_by = user_id
    token.used_at = datetime.utcnow()
    await session.commit()
```

## Modelo 3: VIPSubscriber

**Descripción:** Usuarios con suscripción VIP activa (canjearon token).

**Tabla:** `vip_subscribers`

### Estructura

```python
class VIPSubscriber(Base):
    __tablename__ = "vip_subscribers"

    # Identificador
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario
    user_id: int = Column(BigInteger, unique=True, nullable=False, index=True)

    # Suscripción
    join_date: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    expiry_date: datetime = Column(DateTime, nullable=False)
    status: str = Column(
        String(20),
        default="active",
        nullable=False,
        index=True
    )  # "active" o "expired"

    # Token usado
    token_id: int = Column(Integer, ForeignKey("invitation_tokens.id"), nullable=False)
    token: InvitationToken = relationship("InvitationToken", back_populates="subscribers")

    # Índices
    __table_args__ = (
        Index('idx_status_expiry', 'status', 'expiry_date'),
    )

    # Métodos
    def is_expired(self) -> bool:
        """Verifica si la suscripción expiró"""
        return datetime.utcnow() > self.expiry_date

    def days_remaining(self) -> int:
        """Retorna días restantes (negativo si expirado)"""
        delta = self.expiry_date - datetime.utcnow()
        return delta.days
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único |
| `user_id` | BIGINT | UNIQUE, INDEX, NOT NULL | User ID de Telegram |
| `join_date` | DATETIME | NOT NULL | Timestamp de suscripción |
| `expiry_date` | DATETIME | NOT NULL | Fecha de expiración |
| `status` | VARCHAR(20) | NOT NULL, INDEX, DEFAULT "active" | "active" o "expired" |
| `token_id` | INTEGER | FK, NOT NULL | Referencia a InvitationToken |

### Índices

```sql
-- Búsqueda de suscriptores próximos a expirar
CREATE INDEX idx_status_expiry
ON vip_subscribers(status, expiry_date);

-- Búsqueda por user_id (único)
CREATE UNIQUE INDEX idx_user_id
ON vip_subscribers(user_id);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "user_id": 987654321,
    "join_date": "2025-12-11T11:30:45.123456",
    "expiry_date": "2025-12-12T11:30:45.123456",
    "status": "active",
    "token_id": 2
}
```

Suscriptor expirado:
```json
{
    "id": 2,
    "user_id": 555555555,
    "join_date": "2025-12-10T11:30:45.123456",
    "expiry_date": "2025-12-11T11:30:45.123456",
    "status": "expired",
    "token_id": 1
}
```

### Operaciones Comunes

```python
# Crear suscriptor VIP
async with get_session() as session:
    from datetime import timedelta

    subscriber = VIPSubscriber(
        user_id=user_id,
        token_id=token.id,
        expiry_date=datetime.utcnow() + timedelta(hours=24)
    )
    session.add(subscriber)
    await session.commit()

# Buscar suscriptor activo
async with get_session() as session:
    subscriber = await session.get(VIPSubscriber, user_id, index_col=user_id)
    # O con query
    query = select(VIPSubscriber).where(VIPSubscriber.user_id == user_id)
    result = await session.execute(query)
    subscriber = result.scalar_one_or_none()

# Verificar si usuario es VIP
async with get_session() as session:
    query = select(VIPSubscriber).where(
        (VIPSubscriber.user_id == user_id) &
        (VIPSubscriber.status == "active")
    )
    result = await session.execute(query)
    is_vip = result.scalar_one_or_none() is not None

# Obtener días restantes
async with get_session() as session:
    subscriber = await session.get(VIPSubscriber, user_id, index_col=user_id)
    if subscriber:
        days_left = subscriber.days_remaining()
        # days_left > 0: aún válido
        # days_left <= 0: expirado

# Buscar suscriptores próximos a expirar (próximos 7 días)
from sqlalchemy import and_

async with get_session() as session:
    soon = datetime.utcnow() + timedelta(days=7)
    query = select(VIPSubscriber).where(
        and_(
            VIPSubscriber.status == "active",
            VIPSubscriber.expiry_date <= soon,
            VIPSubscriber.expiry_date > datetime.utcnow()
        )
    ).order_by(VIPSubscriber.expiry_date)
    result = await session.execute(query)
    expiring = result.scalars().all()

# Marcar como expirado (background task)
async with get_session() as session:
    query = select(VIPSubscriber).where(
        and_(
            VIPSubscriber.status == "active",
            VIPSubscriber.expiry_date <= datetime.utcnow()
        )
    )
    result = await session.execute(query)
    expired = result.scalars().all()

    for sub in expired:
        sub.status = "expired"

    await session.commit()
```

## Modelo 4: FreeChannelRequest

**Descripción:** Cola de solicitudes para acceso al canal Free (con tiempo de espera).

**Tabla:** `free_channel_requests`

### Estructura

```python
class FreeChannelRequest(Base):
    __tablename__ = "free_channel_requests"

    # Identificador
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario
    user_id: int = Column(BigInteger, nullable=False, index=True)

    # Solicitud
    request_date: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed: bool = Column(Boolean, default=False, nullable=False, index=True)
    processed_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Índices
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'request_date'),
        Index('idx_processed_date', 'processed', 'request_date'),
    )

    # Métodos
    def minutes_since_request(self) -> int:
        """Retorna minutos desde la solicitud"""
        delta = datetime.utcnow() - self.request_date
        return int(delta.total_seconds() / 60)

    def is_ready(self, wait_time_minutes: int) -> bool:
        """Verifica si cumplió el tiempo de espera"""
        return self.minutes_since_request() >= wait_time_minutes
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único |
| `user_id` | BIGINT | NOT NULL, INDEX | User ID de Telegram |
| `request_date` | DATETIME | NOT NULL | Timestamp de solicitud |
| `processed` | BOOLEAN | NOT NULL, DEFAULT FALSE, INDEX | Si fue procesada |
| `processed_at` | DATETIME | NULL | Timestamp de procesamiento |

### Índices

```sql
-- Búsqueda de solicitudes pendientes por usuario
CREATE INDEX idx_user_date
ON free_channel_requests(user_id, request_date);

-- Búsqueda de solicitudes listas para procesar
CREATE INDEX idx_processed_date
ON free_channel_requests(processed, request_date);
```

### Ejemplo de Dato

Solicitud pendiente:
```json
{
    "id": 1,
    "user_id": 111111111,
    "request_date": "2025-12-11T10:00:00.000000",
    "processed": false,
    "processed_at": null
}
```

Solicitud procesada:
```json
{
    "id": 2,
    "user_id": 222222222,
    "request_date": "2025-12-11T10:00:00.000000",
    "processed": true,
    "processed_at": "2025-12-11T10:05:30.123456"
}
```

### Operaciones Comunes

```python
# Crear solicitud
async with get_session() as session:
    request = FreeChannelRequest(user_id=user_id)
    session.add(request)
    await session.commit()

# Verificar si usuario ya solicitó Free
async with get_session() as session:
    query = select(FreeChannelRequest).where(
        (FreeChannelRequest.user_id == user_id) &
        (FreeChannelRequest.processed == False)
    )
    result = await session.execute(query)
    exists = result.scalar_one_or_none() is not None

# Buscar solicitudes listas para procesar
async with get_session() as session:
    from config import Config

    query = select(FreeChannelRequest).where(
        FreeChannelRequest.processed == False
    ).order_by(FreeChannelRequest.request_date)
    result = await session.execute(query)
    requests = result.scalars().all()

    ready_requests = [
        r for r in requests
        if r.is_ready(Config.DEFAULT_WAIT_TIME_MINUTES)
    ]

# Procesar solicitud
async with get_session() as session:
    request = await session.get(FreeChannelRequest, request_id)
    request.processed = True
    request.processed_at = datetime.utcnow()
    await session.commit()

    # Invitar usuario a canal Free
    # await bot.add_chat_member(...)

# Obtener tiempo de espera restante
async with get_session() as session:
    request = await session.get(FreeChannelRequest, request_id)
    if request and not request.processed:
        from config import Config
        wait_total = Config.DEFAULT_WAIT_TIME_MINUTES
        wait_elapsed = request.minutes_since_request()
        wait_remaining = max(0, wait_total - wait_elapsed)
```

## Relaciones Entre Modelos

### Diagrama de Relaciones

```
BotConfig (1)
    ├─ Configuración global singleton
    └─ No tiene relaciones FK

InvitationToken (*)
    ├─ Generado por admin (user_id en generated_by)
    └─ Puede ser canjeado por usuario (user_id en used_by)
    └─ Relación 1:N con VIPSubscriber

VIPSubscriber (*)
    ├─ Usuario único (user_id unique)
    ├─ Relación N:1 con InvitationToken
    └─ Relación 1:1 con usuario Telegram

FreeChannelRequest (*)
    ├─ Usuario puede tener múltiples requests
    ├─ Último request no procesado se considera "actual"
    └─ No tiene relaciones FK (independiente)
```

### Relación InvitationToken - VIPSubscriber

```python
# Token 1:N Subscribers (un token → muchos suscriptores)
token.subscribers  # Todos los usuarios que canjearon este token

# Subscriber N:1 Token (un suscriptor → 1 token)
subscriber.token  # Token que usó para acceso VIP

# Ejemplo de uso
async with get_session() as session:
    token = await session.get(InvitationToken, 1)
    # Cargar relación
    from sqlalchemy.orm import selectinload
    query = select(InvitationToken).where(...).options(
        selectinload(InvitationToken.subscribers)
    )
    result = await session.execute(query)
    token = result.scalar_one()

    # Acceder subscribers
    for subscriber in token.subscribers:
        print(f"Usuario {subscriber.user_id} canjeó este token")
```

## Cascadas y Limpieza

### Cascade Delete

Cuando se elimina un token, sus suscriptores relacionados se eliminan:

```python
subscribers = relationship(
    "VIPSubscriber",
    back_populates="token",
    cascade="all, delete-orphan"  # Elimina huérfanos
)
```

**Uso:**
```python
async with get_session() as session:
    token = await session.get(InvitationToken, 1)
    await session.delete(token)
    await session.commit()
    # Todos los VIPSubscriber con este token se eliminan automáticamente
```

## Migraciones (No implementadas en MVP)

En ONDA 2+, se usará Alembic para migraciones:

```bash
# Inicializar Alembic
alembic init alembic

# Crear migración automática
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migración
alembic upgrade head
```

## Performance y Optimización

### Índices Actuales

1. **InvitationToken:**
   - `idx_token_used_created(used, created_at)` - Para buscar tokens válidos
   - `token` UNIQUE - Para búsqueda por valor

2. **VIPSubscriber:**
   - `idx_status_expiry(status, expiry_date)` - Para buscar suscriptores a expirar
   - `user_id` UNIQUE - Para búsqueda rápida por usuario

3. **FreeChannelRequest:**
   - `idx_user_date(user_id, request_date)` - Para historial de usuario
   - `idx_processed_date(processed, request_date)` - Para procesamiento en cola

### Queries Optimizadas

```python
# BUENO: Usa índice
query = select(VIPSubscriber).where(
    VIPSubscriber.status == "active"
).order_by(VIPSubscriber.expiry_date)

# MALO: No usa índice eficientemente
query = select(VIPSubscriber).where(
    VIPSubscriber.status == "active"
).order_by(VIPSubscriber.user_id)  # No en índice

# BUENO: Carga relaciones eficientemente
query = select(InvitationToken).options(
    selectinload(InvitationToken.subscribers)
)

# MALO: N+1 query (lenta)
tokens = select(InvitationToken).execute()
for token in tokens:
    print(token.subscribers)  # Query para cada token
```

## Backup y Recovery

### Backup Manual

```bash
# Copiar archivo base de datos
cp bot.db bot.db.backup

# Backup con timestamp
cp bot.db "bot.db.$(date +%Y%m%d_%H%M%S).backup"
```

### Restore

```bash
# Restaurar backup
cp bot.db.backup bot.db

# Reiniciar bot
python main.py
```

### Backup Automatizado (Futuro)

En ONDA 2+, se implementará backup automático:

```python
# Background task diario
@scheduler.scheduled_job('cron', day_of_week='*', hour=2, minute=0)
async def daily_backup():
    shutil.copy('bot.db', f'backups/bot.db.{date.today()}')
```

## Consultas de Ejemplo

### Estadísticas

```python
# Contar VIP activos
from sqlalchemy import func

async with get_session() as session:
    query = select(func.count(VIPSubscriber.id)).where(
        VIPSubscriber.status == "active"
    )
    result = await session.execute(query)
    active_count = result.scalar()

# Contar tokens válidos
query = select(func.count(InvitationToken.id)).where(
    InvitationToken.used == False
)
result = await session.execute(query)
valid_tokens = result.scalar()

# Solicitudes Free en cola
query = select(func.count(FreeChannelRequest.id)).where(
    FreeChannelRequest.processed == False
)
result = await session.execute(query)
pending_requests = result.scalar()
```

### Reportes

```python
# Usuarios que se unieron hoy
from datetime import date

today = date.today()
query = select(VIPSubscriber).where(
    func.date(VIPSubscriber.join_date) == today
)
result = await session.execute(query)
new_vips = result.scalars().all()

# Token más usado
query = select(InvitationToken).where(
    InvitationToken.used == True
).order_by(
    func.count(InvitationToken.subscribers).desc()
).limit(1)
result = await session.execute(query)
most_used = result.scalar()
```

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
