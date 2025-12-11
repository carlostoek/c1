# Guía de Testing

Referencia de estrategia de testing, framework y ejemplos para el bot.

## Estado de Testing en MVP

En ONDA 1 Fase 1.1:
- **Testing:** No implementado aún
- **Fase planeada:** ONDA 1 Fase 1.5+ o ONDA 2

## Framework de Testing

El proyecto usa **pytest** con **pytest-asyncio** para testing.

### Instalación

```bash
pip install pytest pytest-asyncio
```

Para development:
```bash
pip install -r requirements.txt
# Descomentar pytest y pytest-asyncio en requirements.txt
```

## Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py              # Fixtures globales
├── unit/
│   ├── test_models.py       # Tests de modelos
│   ├── test_services.py     # Tests de servicios
│   └── test_config.py       # Tests de configuración
├── integration/
│   ├── test_handlers.py     # Tests de handlers
│   ├── test_database.py     # Tests de BD
│   └── test_workflows.py    # Tests de flujos completos
└── fixtures/
    └── data.py              # Datos mock
```

## Fixtures Comunes

### conftest.py

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from bot.database.base import Base
from bot.database.models import BotConfig, InvitationToken, VIPSubscriber, FreeChannelRequest

@pytest.fixture(scope="session")
def event_loop():
    """Crea event loop para tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_engine():
    """Engine de BD en memoria para tests"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()

@pytest.fixture
async def async_session(async_engine):
    """Sesión de BD para tests"""
    SessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def bot_config(async_session):
    """BotConfig para tests"""
    config = BotConfig(
        id=1,
        vip_channel_id="-1001234567890",
        free_channel_id="-1001234567891",
        wait_time_minutes=5,
    )
    async_session.add(config)
    await async_session.commit()
    return config

@pytest.fixture
async def valid_token(async_session):
    """Token válido para tests"""
    from datetime import datetime, timedelta

    token = InvitationToken(
        token="TESTABC1234567X",
        generated_by=123456789,
        duration_hours=24,
        created_at=datetime.utcnow(),
        used=False
    )
    async_session.add(token)
    await async_session.commit()
    return token

@pytest.fixture
async def vip_subscriber(async_session, valid_token):
    """Suscriptor VIP para tests"""
    from datetime import datetime, timedelta

    subscriber = VIPSubscriber(
        user_id=987654321,
        token_id=valid_token.id,
        join_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(hours=24),
        status="active"
    )
    async_session.add(subscriber)
    await async_session.commit()
    return subscriber
```

## Ejemplos de Tests

### Test de Modelos

```python
import pytest
from datetime import datetime, timedelta
from bot.database.models import InvitationToken

@pytest.mark.asyncio
async def test_token_is_valid(valid_token):
    """Test que token válido se valida correctamente"""
    assert valid_token.is_valid() is True
    assert valid_token.used is False
    assert valid_token.is_expired() is False

@pytest.mark.asyncio
async def test_token_is_expired(async_session):
    """Test que token expirado no es válido"""
    expired_token = InvitationToken(
        token="EXPIRED12345678",
        generated_by=123456789,
        duration_hours=1,
        created_at=datetime.utcnow() - timedelta(hours=2),
        used=False
    )
    async_session.add(expired_token)
    await async_session.commit()

    assert expired_token.is_valid() is False
    assert expired_token.is_expired() is True

@pytest.mark.asyncio
async def test_token_is_used(async_session, valid_token):
    """Test que token usado no es válido"""
    valid_token.used = True
    valid_token.used_by = 987654321
    valid_token.used_at = datetime.utcnow()
    await async_session.commit()

    assert valid_token.is_valid() is False

@pytest.mark.asyncio
async def test_subscriber_days_remaining(vip_subscriber):
    """Test cálculo de días restantes"""
    days = vip_subscriber.days_remaining()
    assert days > 0
    assert days <= 1  # Fue creado hace segundos, máximo 1 día

@pytest.mark.asyncio
async def test_subscriber_is_expired(async_session):
    """Test que suscriptor expirado se detecta"""
    from bot.database.models import VIPSubscriber

    expired_sub = VIPSubscriber(
        user_id=111111111,
        token_id=1,
        join_date=datetime.utcnow() - timedelta(days=2),
        expiry_date=datetime.utcnow() - timedelta(days=1),
        status="active"
    )
    async_session.add(expired_sub)
    await async_session.commit()

    assert expired_sub.is_expired() is True
```

### Test de Servicios

```python
import pytest
from bot.services.subscription import SubscriptionService
from bot.database.models import VIPSubscriber, InvitationToken

@pytest.mark.asyncio
async def test_generate_token(async_session):
    """Test generación de token"""
    service = SubscriptionService(async_session)

    token = await service.generate_token(
        admin_id=123456789,
        duration_hours=24
    )

    assert len(token) == 16
    assert all(c.isalnum() for c in token)

    # Verificar que se guardó en BD
    db_token = await service.get_token(token)
    assert db_token is not None
    assert db_token.token == token

@pytest.mark.asyncio
async def test_validate_token_valid(valid_token, async_session):
    """Test validación de token válido"""
    service = SubscriptionService(async_session)

    is_valid = await service.validate_token(valid_token.token)
    assert is_valid is True

@pytest.mark.asyncio
async def test_validate_token_invalid(async_session):
    """Test validación de token inválido"""
    service = SubscriptionService(async_session)

    is_valid = await service.validate_token("INVALID1234567")
    assert is_valid is False

@pytest.mark.asyncio
async def test_redeem_token_success(valid_token, async_session):
    """Test canje exitoso de token"""
    service = SubscriptionService(async_session)

    user_id = 987654321
    subscriber = await service.redeem_token(
        user_id=user_id,
        token=valid_token.token
    )

    assert subscriber.user_id == user_id
    assert subscriber.status == "active"
    assert subscriber.token_id == valid_token.id

    # Verificar token marcado como usado
    db_token = await service.get_token(valid_token.token)
    assert db_token.used is True
    assert db_token.used_by == user_id

@pytest.mark.asyncio
async def test_redeem_token_already_used(valid_token, async_session):
    """Test canje de token ya usado"""
    service = SubscriptionService(async_session)

    # Marcar como usado
    valid_token.used = True
    valid_token.used_by = 111111111
    await async_session.commit()

    # Intentar canjear
    with pytest.raises(ValueError):
        await service.redeem_token(
            user_id=987654321,
            token=valid_token.token
        )

@pytest.mark.asyncio
async def test_get_active_subscriber_exists(vip_subscriber, async_session):
    """Test obtener suscriptor activo existente"""
    service = SubscriptionService(async_session)

    subscriber = await service.get_active_subscriber(vip_subscriber.user_id)

    assert subscriber is not None
    assert subscriber.user_id == vip_subscriber.user_id
    assert subscriber.status == "active"

@pytest.mark.asyncio
async def test_get_active_subscriber_not_exists(async_session):
    """Test obtener suscriptor que no existe"""
    service = SubscriptionService(async_session)

    subscriber = await service.get_active_subscriber(999999999)

    assert subscriber is None

@pytest.mark.asyncio
async def test_list_expiring_subscribers(async_session, valid_token):
    """Test listar suscriptores próximos a expirar"""
    from datetime import timedelta
    from bot.database.models import VIPSubscriber

    service = SubscriptionService(async_session)

    # Crear suscriptor que expira en 3 días
    subscriber = VIPSubscriber(
        user_id=111111111,
        token_id=valid_token.id,
        expiry_date=datetime.utcnow() + timedelta(days=3),
        status="active"
    )
    async_session.add(subscriber)
    await async_session.commit()

    # Buscar expirando en próximos 7 días
    expiring = await service.list_expiring_subscribers(days=7)

    assert len(expiring) == 1
    assert expiring[0].user_id == 111111111

@pytest.mark.asyncio
async def test_create_free_request_success(async_session):
    """Test crear solicitud Free exitosamente"""
    service = SubscriptionService(async_session)

    user_id = 555555555
    request = await service.create_free_request(user_id)

    assert request.user_id == user_id
    assert request.processed is False

@pytest.mark.asyncio
async def test_create_free_request_duplicate(async_session):
    """Test crear solicitud Free cuando ya existe pendiente"""
    service = SubscriptionService(async_session)

    user_id = 555555555
    await service.create_free_request(user_id)

    # Intentar crear otra
    with pytest.raises(ValueError):
        await service.create_free_request(user_id)
```

### Test de Handlers

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat, CallbackQuery
from aiogram.fsm.context import FSMContext

@pytest.mark.asyncio
async def test_start_handler(async_session):
    """Test handler de /start"""
    from bot.handlers.user.start import start

    # Mock message
    message = AsyncMock()
    message.from_user = MagicMock(first_name="TestUser")
    message.answer = AsyncMock()

    state = AsyncMock()
    state.clear = AsyncMock()

    await start(message, state)

    # Verificar que se envió respuesta
    message.answer.assert_called_once()

    # Verificar que se limpió estado
    state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_vip_handler_valid_token(async_session, valid_token):
    """Test handler de token VIP válido"""
    from bot.handlers.user.vip_flow import process_vip_token

    # Mock message
    message = AsyncMock()
    message.text = valid_token.token
    message.from_user = MagicMock(id=987654321)
    message.answer = AsyncMock()

    state = AsyncMock()
    state.clear = AsyncMock()

    await process_vip_token(message, state, async_session)

    # Verificar respuesta positiva
    message.answer.assert_called()
    assert "✅" in str(message.answer.call_args)

    # Verificar que se limpió estado
    state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_free_request_handler(async_session):
    """Test handler de solicitud Free"""
    from bot.handlers.user.free_flow import request_free_access

    # Mock callback
    callback = AsyncMock()
    callback.from_user = MagicMock(id=555555555)
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    state = AsyncMock()
    state.clear = AsyncMock()

    await request_free_access(callback, state, async_session)

    # Verificar respuesta
    callback.message.edit_text.assert_called()

    # Verificar que se limpió estado
    state.clear.assert_called_once()
```

### Test de Configuración

```python
import pytest
from config import Config

def test_validate_config():
    """Test validación de config"""
    # Esto requiere .env válido, ver SETUP.md
    assert Config.validate() is True

def test_is_admin():
    """Test verificación de admin"""
    admin_id = Config.ADMIN_USER_IDS[0] if Config.ADMIN_USER_IDS else 0

    if admin_id:
        assert Config.is_admin(admin_id) is True
        assert Config.is_admin(999999999) is False

def test_load_admin_ids():
    """Test carga de IDs admin"""
    admin_ids = Config.load_admin_ids()

    assert isinstance(admin_ids, list)
    assert len(admin_ids) > 0
    assert all(isinstance(id, int) for id in admin_ids)
```

## Ejecución de Tests

### Ejecutar todos los tests

```bash
pytest
```

### Ejecutar tests de un archivo

```bash
pytest tests/unit/test_models.py
```

### Ejecutar tests con verbose

```bash
pytest -v
```

### Ejecutar con cobertura

```bash
pip install pytest-cov
pytest --cov=bot --cov-report=html
```

### Ejecutar tests específicos por nombre

```bash
pytest -k "test_token_is_valid"
```

### Ejecutar con debugging

```bash
pytest -s --tb=short
```

## Mocking

Ejemplos comunes de mocking:

```python
from unittest.mock import AsyncMock, MagicMock, patch

# Mock async function
mock_func = AsyncMock(return_value=42)
result = await mock_func()  # returns 42

# Mock attributes
mock_obj = MagicMock()
mock_obj.user_id = 123
mock_obj.method.return_value = "valor"

# Patch función
with patch("bot.services.subscription.generate_token") as mock_gen:
    mock_gen.return_value = "MOCK_TOKEN"
    # Usar la función que será mockeada

# Verificar llamadas
mock_func.assert_called_once()
mock_func.assert_called_with(arg1, arg2)
mock_func.assert_not_called()
```

## Buenas Prácticas

1. **Organizar tests por módulo** - Estructura paralela a código
2. **Usar fixtures** - Reutilizar setup común
3. **Nombres descriptivos** - `test_token_is_valid_when_fresh` mejor que `test_token`
4. **Un assert principal por test** - Facilita debugging
5. **Mockar dependencias externas** - BD, Telegram API, etc.
6. **Test casos positivos y negativos** - Success y error paths
7. **Usar pytest markers** - Agrupar tests por categoría

Ejemplo:
```python
@pytest.mark.asyncio
@pytest.mark.slow
def test_heavy_operation():
    """Test operación pesada"""
    pass

# Ejecutar solo tests rápidos
pytest -m "not slow"
```

## Testing en CI/CD (Futuro)

En ONDA 2+, integrar con GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest --cov=bot
      - run: codecov
```

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
**Estado:** Framework de testing preparado, implementación en Fase 1.5+
