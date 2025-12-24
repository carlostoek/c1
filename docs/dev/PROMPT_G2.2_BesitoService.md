# PROMPT G2.2: BesitoService - Gestión de Economía de Besitos

**Framework:** 4-Layer + Screaming Protocol (validación crítica)  
**Complejidad:** Compleja (race conditions, atomic updates)  
**LLM Target:** Claude Sonnet / GPT-4

---

## ROL

Actúa como Ingeniero de Software Senior especializado en sistemas concurrentes, transacciones atómicas y economías virtuales en aplicaciones Python async.

---

## TAREA

Implementa el servicio `BesitoService` que gestiona la economía de "besitos" (moneda virtual) del sistema de gamificación, con énfasis en operaciones atómicas para prevenir race conditions y auditoría completa de transacciones.

---

## CONTEXTO

### Stack Tecnológico
- Python 3.11+ con async/await
- SQLAlchemy 2.0 (ORM async)
- SQLite con WAL mode (permite concurrencia)
- aiosqlite para operaciones async

### Arquitectura del Módulo
```
bot/gamification/
├── database/
│   ├── models.py         # UserGamification, BesitoTransaction
│   └── enums.py          # TransactionType
├── services/
│   ├── container.py      # GamificationContainer
│   └── besito.py         # ← ESTE ARCHIVO
```

### Modelos Relevantes
```python
# bot/gamification/database/models.py

class UserGamification(Base):
    __tablename__ = "user_gamification"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    total_besitos: Mapped[int] = mapped_column(default=0)  # ⚠️ CRÍTICO: atomic updates
    besitos_spent: Mapped[int] = mapped_column(default=0)
    besitos_earned: Mapped[int] = mapped_column(default=0)
    current_level_id: Mapped[int] = mapped_column(ForeignKey("levels.id"), nullable=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

class BesitoTransaction(Base):
    __tablename__ = "besito_transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_gamification.user_id"))
    amount: Mapped[int]  # Positivo=ganado, Negativo=gastado
    transaction_type: Mapped[str]  # Enum: MISSION_REWARD, REACTION, PURCHASE, ADMIN_GRANT, etc.
    description: Mapped[str]
    reference_id: Mapped[int] = mapped_column(nullable=True)  # ID de misión/recompensa relacionada
    created_at: Mapped[datetime]

# Enums
class TransactionType(str, Enum):
    MISSION_REWARD = "mission_reward"
    REACTION = "reaction"
    PURCHASE = "purchase"
    ADMIN_GRANT = "admin_grant"
    ADMIN_DEDUCT = "admin_deduct"
    REFUND = "refund"
```

### Problema Crítico: Race Conditions
```python
# ❌ INCORRECTO (puede perder transacciones)
user = await session.get(UserGamification, user_id)
user.total_besitos += 100
await session.commit()

# ✅ CORRECTO (atomic update)
await session.execute(
    update(UserGamification)
    .where(UserGamification.user_id == user_id)
    .values(total_besitos=UserGamification.total_besitos + 100)
)
```

---

## RESTRICCIONES TÉCNICAS

### Operaciones Atómicas Obligatorias
- **NUNCA** hacer read-modify-write en `total_besitos`
- **SIEMPRE** usar `UPDATE ... SET total_besitos = total_besitos + X`
- Todas las operaciones deben ser transaccionales
- Si una transacción falla, rollback completo

### Auditoría Completa
- **TODA** modificación de besitos debe crear registro en `BesitoTransaction`
- Incluir descripción legible humana
- Guardar `reference_id` cuando aplique (ej: mission_id)
- Timestamp con timezone UTC

### Validaciones
- **No permitir** saldo negativo (excepto con flag `allow_negative=True` para admin)
- Validar `amount > 0` en operaciones de gasto
- Verificar existencia del usuario antes de operar
- Registrar intentos fallidos para debugging

### Manejo de Errores
```python
# Errores específicos a manejar:
- InsufficientBesitosError(amount_needed, current_balance)
- UserNotFoundError(user_id)
- InvalidTransactionError(reason)
```

---

## FASE 1: PLANIFICACIÓN

Antes de escribir código, diseña la estructura del servicio:

### Métodos Públicos Requeridos

1. **grant_besitos(user_id, amount, transaction_type, description, reference_id=None)**
   - Otorga besitos a usuario
   - Crea transacción positiva
   - Actualiza `besitos_earned`
   - Return: nuevo balance total

2. **spend_besitos(user_id, amount, transaction_type, description, reference_id=None)**
   - Deduce besitos (valida saldo suficiente)
   - Crea transacción negativa
   - Actualiza `besitos_spent`
   - Return: nuevo balance restante

3. **get_balance(user_id)**
   - Return: balance actual (sin modificar)

4. **get_transaction_history(user_id, limit=50, transaction_type=None)**
   - Return: lista de transacciones ordenadas por fecha desc
   - Filtro opcional por tipo

5. **transfer_besitos(from_user_id, to_user_id, amount, description)**
   - Transfiere entre usuarios (opcional para MVP)
   - Atomic: ambas operaciones en misma transacción

6. **get_leaderboard(limit=10)**
   - Return: top usuarios por total_besitos

### Métodos Privados

- `_ensure_user_exists(user_id)` - Crea perfil si no existe
- `_create_transaction(user_id, amount, type, desc, ref_id)` - Helper transacción
- `_update_balance_atomic(user_id, delta)` - Update atómico

---

## FASE 2: CASOS DE PRUEBA

Define casos de prueba que cubran:

### Happy Path
```python
# Test 1: Otorgar besitos a nuevo usuario
user_id = 12345
balance = await besito_service.grant_besitos(
    user_id=user_id,
    amount=100,
    transaction_type=TransactionType.MISSION_REWARD,
    description="Completó misión de bienvenida",
    reference_id=1
)
# Esperado: balance == 100
```

### Boundary Testing
```python
# Test 2: Gastar exactamente todo el balance
await besito_service.grant_besitos(user_id, 500, ...)
await besito_service.spend_besitos(user_id, 500, ...)
# Esperado: balance == 0
```

### Negative Testing
```python
# Test 3: Intentar gastar más de lo disponible
await besito_service.grant_besitos(user_id, 100, ...)
# Debe lanzar InsufficientBesitosError
await besito_service.spend_besitos(user_id, 200, ...)
```

### Concurrency Testing
```python
# Test 4: Dos transacciones simultáneas
import asyncio

async def add_100():
    await besito_service.grant_besitos(user_id, 100, ...)

async def add_200():
    await besito_service.grant_besitos(user_id, 200, ...)

await asyncio.gather(add_100(), add_200())
# Esperado: balance == 300 (no 100 o 200)
```

---

## FASE 3: VALIDACIÓN

Verifica que el pseudocódigo cumple:

- ✅ Todas las operaciones usan atomic updates
- ✅ Cada modificación crea transacción en `BesitoTransaction`
- ✅ Manejo de race conditions con `UPDATE ... SET col = col + delta`
- ✅ Validación de saldo antes de gastar
- ✅ Creación automática de `UserGamification` si no existe
- ✅ Excepciones custom con mensajes claros
- ✅ Métodos async (await session.execute, etc.)

---

## FASE 4: IMPLEMENTACIÓN

Traduce el diseño validado a código Python siguiendo:

### Estructura del Archivo
```python
# bot/gamification/services/besito.py

from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, UTC

from bot.gamification.database.models import UserGamification, BesitoTransaction
from bot.gamification.database.enums import TransactionType

# Excepciones custom
class InsufficientBesitosError(Exception):
    """Se lanza cuando usuario intenta gastar más besitos de los disponibles"""
    pass

class BesitoService:
    """
    Servicio de gestión de economía de besitos.
    
    Características:
    - Operaciones atómicas para prevenir race conditions
    - Auditoría completa de transacciones
    - Validación de saldo
    - Leaderboards
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def grant_besitos(...) -> int:
        """Otorga besitos a usuario"""
        ...
    
    async def spend_besitos(...) -> int:
        """Gasta besitos (valida saldo)"""
        ...
    
    # ... resto de métodos
```

### Patrón de Atomic Update
```python
# SIEMPRE usar este patrón para modificar total_besitos
stmt = (
    update(UserGamification)
    .where(UserGamification.user_id == user_id)
    .values(
        total_besitos=UserGamification.total_besitos + delta,
        besitos_earned=UserGamification.besitos_earned + delta if delta > 0 else UserGamification.besitos_earned,
        updated_at=datetime.now(UTC)
    )
)
await self.session.execute(stmt)
await self.session.commit()
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

# Log todas las operaciones importantes
logger.info(f"Granted {amount} besitos to user {user_id}: {description}")
logger.error(f"Insufficient besitos for user {user_id}: needs {amount}, has {balance}")
```

---

## FORMATO DE SALIDA

Entrega el archivo completo `bot/gamification/services/besito.py` con:

1. **Imports y excepciones** (primeras 30 líneas)
2. **Clase BesitoService completa** con todos los métodos implementados
3. **Docstrings** en cada método (formato Google Style)
4. **Type hints** completos (typing.Optional, List, etc.)
5. **Comentarios** explicando secciones críticas (atomic updates)

NO incluyas:
- Tests (van en archivo separado)
- Configuración (va en config.py)
- Código del contenedor (va en container.py)

---

## INTEGRACIÓN

Indica cómo este servicio se integrará:

```python
# bot/gamification/services/container.py
from bot.gamification.services.besito import BesitoService

class GamificationContainer:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._besito_service = None
    
    @property
    def besito(self) -> BesitoService:
        if self._besito_service is None:
            self._besito_service = BesitoService(self._session)
        return self._besito_service
```

---

**ENTREGABLE FINAL:** Archivo `besito.py` completo, listo para integrar, con operaciones atómicas implementadas correctamente.
