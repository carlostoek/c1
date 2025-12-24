# PROMPTS G8.4 y G8.5 - CRUD Recompensas y Sistema de Transacciones

---
---

# PROMPT G8.4: CRUD de Recompensas

---

## ROL

Actúa como Ingeniero de Software Senior especializado en:
- Aiogram 3.4.1 (callbacks complejos, selección múltiple)
- SQLAlchemy 2.0 (herencia joined table, queries con joins)
- Validación de unlock conditions multinivel

---

## TAREA

Implementa módulo CRUD para gestión de recompensas en `bot/gamification/handlers/admin/reward_config.py`, incluyendo manejo especial de Badges (herencia) y gestión de unlock conditions complejas.

---

## CONTEXTO

### Modelos Existentes
```python
class Reward(Base):
    id: Mapped[int]
    name: Mapped[str]
    description: Mapped[str]
    reward_type: Mapped[str]           # RewardType enum
    cost_besitos: Mapped[int]          # nullable
    unlock_conditions: Mapped[str]     # JSON nullable
    metadata: Mapped[str]              # JSON
    active: Mapped[bool]

class Badge(Base):  # Herencia joined table
    id: Mapped[int]  # FK → Reward.id
    icon: Mapped[str]
    rarity: Mapped[str]  # BadgeRarity enum

class UserBadge(Base):
    id: Mapped[int]  # FK → UserReward.id
    displayed: Mapped[bool]
```

### Servicio Disponible
```python
class RewardService:
    async def get_all_rewards(reward_type: Optional[RewardType]) -> List[Reward]
    async def create_reward(...) -> Reward
    async def create_badge(...) -> tuple[Reward, Badge]
    async def update_reward(reward_id, **kwargs) -> Reward
    async def delete_reward(reward_id) -> bool
    async def get_users_with_reward(reward_id) -> int
```

### Unlock Conditions (Ejemplos)
```python
# Simple
{"type": "mission", "mission_id": 5}
{"type": "level", "level_id": 3}
{"type": "besitos", "min_besitos": 1000}

# Múltiple (AND)
{
    "type": "multiple",
    "conditions": [
        {"type": "mission", "mission_id": 5},
        {"type": "level", "level_id": 2}
    ]
}
```

---

## RESTRICCIONES TÉCNICAS

### Validaciones
1. **Metadata por tipo**: Validar con `validate_reward_metadata()` según reward_type
2. **Unlock conditions**: Validar con `validate_unlock_conditions()`
3. **IDs referenciados**: Si unlock menciona mission_id/level_id, validar que existan
4. **Stock**: Si reward tiene stock, mostrar remaining y warning si < 10

### Estados FSM
```python
class RewardConfigStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_type = State()
    # Badge specific
    waiting_badge_icon = State()
    waiting_badge_rarity = State()
    # Conditions
    editing_conditions = State()
```

### Callbacks
```
"gamif:admin:rewards"                     # Lista con filtro por tipo
"gamif:rewards:filter:{type}"             # Filtrar por RewardType
"gamif:reward:view:{id}"                  # Vista detallada
"gamif:reward:edit:{id}"                  # Menú edición
"gamif:reward:edit_conditions:{id}"       # Wizard de conditions
"gamif:reward:toggle:{id}"                # Activar/desactivar
"gamif:reward:delete:{id}"                # Eliminar
```

### Manejo de Badges (Especial)
Al crear/editar Badge:
1. Crear/actualizar Reward base
2. Crear/actualizar Badge con icon y rarity
3. Validar emoji con `is_valid_emoji()`

---

## FORMATO DE SALIDA

### Lista con Filtros
```
🎁 RECOMPENSAS CONFIGURADAS
━━━━━━━━━━━━━━━━

[🏆 Badges] [🎁 Items] [🔓 Permisos] [💰 Besitos] [Todos]

📊 Mostrando: Badges (12)

1. ✅ 🏆 Primer Paso (Común)
   → Unlock: Completar misión "Bienvenida"
   → 45 usuarios lo tienen

2. ✅ 🔥 Maestro de Racha (Épico)
   → Unlock: Nivel 4 + 7 días racha
   → 8 usuarios lo tienen

[Ver más...] [➕ Crear] [🔙 Volver]
```

### Vista Detallada
```
🎁 RECOMPENSA: Maestro de Racha

🏆 Tipo: Badge
⭐ Rareza: Épico
💰 Costo: No se puede comprar

🔓 UNLOCK CONDITIONS
━━━━━━━━━━━━━━━━
Requiere TODO lo siguiente:
• Completar misión ID: 5
• Alcanzar nivel ID: 4

👥 ESTADÍSTICAS
• Usuarios que lo tienen: 8
• Tasa de obtención: 2.5%

[✏️ Editar] [🔓 Ver Conditions] [🔙 Volver]
```

---

## CASOS DE PRUEBA

### Happy Path
1. Crear Badge con icon ✅, rarity "epic" → Reward + Badge creados
2. Editar unlock_conditions de simple a múltiple → JSON actualizado

### Validaciones
3. Crear Badge con icon "abc" (no emoji) → rechazado
4. Crear reward con unlock que requiere mission_id=999 (no existe) → error
5. Editar metadata con JSON inválido → rechazado

### Eliminación
6. Eliminar reward sin usuarios → eliminado
7. Eliminar reward con 50 usuarios → warning + confirmación

---

## ESPECIFICACIÓN GHERKIN

```gherkin
Feature: CRUD de Recompensas

Scenario: Crear Badge válido
  Given admin en formulario de crear recompensa
  When selecciona tipo "Badge"
  And proporciona icon "🏆", rarity "epic"
  And valida metadata
  Then crea Reward con reward_type=badge
  And crea Badge asociado con icon y rarity

Scenario: Validar unlock conditions complejas
  Given reward con unlock múltiple
  When admin edita conditions
  And agrega mission_id=5 y level_id=3
  Then valida que ambos IDs existan
  And construye JSON {"type":"multiple","conditions":[...]}

Scenario: Filtrar por tipo de recompensa
  Given 20 rewards (10 badges, 5 items, 5 permisos)
  When admin selecciona filtro "Badges"
  Then muestra solo los 10 badges
```

---

## INTEGRACIÓN

### Edición de Unlock Conditions (Wizard)
Implementar mini-wizard:
1. ¿Tipo de condition? [Misión] [Nivel] [Besitos] [Múltiple]
2. Si Misión: mostrar lista de misiones para seleccionar
3. Si Nivel: mostrar lista de niveles
4. Si Múltiple: permitir agregar condiciones una por una
5. Validar JSON final con `validate_unlock_conditions()`

### Listado de Badges con Icons
En lista, mostrar icon del badge junto al nombre:
```
1. 🏆 Primer Paso (Común)
2. 🔥 Maestro de Racha (Épico)
```

---

**ENTREGABLE**: Archivo `reward_config.py` con CRUD completo, manejo de herencia Badge y validación de unlock conditions.

---
---

# PROMPT G8.5: Modelo BesitoTransaction y Handler de Historial

---

## ROL

Actúa como Ingeniero de Software Senior especializado en:
- SQLAlchemy 2.0 (modelos con auditoría, índices compuestos)
- Alembic (migraciones con datos sensibles)
- Patrones de auditoría y logging de transacciones

---

## TAREA

Implementa:
1. Modelo `BesitoTransaction` en `bot/gamification/database/models.py`
2. Migración Alembic `005_add_besito_transaction.py`
3. Handler de historial en `bot/gamification/handlers/admin/transaction_history.py`

---

## CONTEXTO

### Propósito
Actualmente BesitoService modifica `total_besitos` pero no hay auditoría. Se requiere:
- Registrar TODA operación de besitos (grants, gastos, transferencias, ajustes admin)
- Historial completo por usuario
- Balance after transaction para detectar inconsistencias
- Filtrado por tipo de transacción

### Stack
- SQLAlchemy 2.0 (async)
- Alembic
- SQLite/PostgreSQL

---

## RESTRICCIONES TÉCNICAS

### Modelo BesitoTransaction
```python
# Especificación
class BesitoTransaction(Base):
    __tablename__ = 'besito_transactions'
    
    # Campos requeridos:
    id: int PK
    user_id: int FK → User.id (indexed)
    amount: int (puede ser negativo para gastos)
    transaction_type: str  # TransactionType enum
    description: str
    reference_id: int nullable  # ID del origen (mission_id, reward_id, etc)
    balance_after: int  # Balance después de esta tx
    created_at: datetime (UTC, indexed)
    
    # Índices compuestos:
    - (user_id, created_at DESC)
    - (user_id, transaction_type)
    - (reference_id, transaction_type)
```

### TransactionType Enum
```python
class TransactionType(str, Enum):
    REACTION = "reaction"
    MISSION_REWARD = "mission_reward"
    PURCHASE = "purchase"
    ADMIN_GRANT = "admin_grant"
    ADMIN_DEDUCT = "admin_deduct"
    REFUND = "refund"
    STREAK_BONUS = "streak_bonus"
    LEVEL_UP_BONUS = "level_up_bonus"
```

### Integración con BesitoService
Modificar métodos existentes para crear transaction:
```python
# Pseudocódigo
async def grant_besitos(...):
    # 1. UPDATE UserGamification besitos
    # 2. GET nuevo balance
    # 3. CREATE BesitoTransaction con balance_after
    # 4. COMMIT
```

---

## MIGRACIÓN ALEMBIC

### Archivo: 005_add_besito_transaction.py

#### Upgrade
1. Crear tabla besito_transactions
2. Crear índices compuestos
3. Agregar FK constraint con ondelete='CASCADE'
4. Crear enum TransactionType (si BD soporta)

#### Downgrade
1. DROP table besito_transactions
2. DROP enum si se creó

#### Validación
- Migration debe ser reversible
- No afectar datos existentes
- Indexes deben optimizar queries por user_id + created_at

---

## HANDLER DE HISTORIAL

### Archivo: transaction_history.py

#### Funcionalidades
1. **Ver historial de usuario específico**: Admin busca por user_id
2. **Filtrar por tipo**: Mostrar solo MISSION_REWARD, solo PURCHASE, etc.
3. **Paginación**: 20 transacciones por página
4. **Exportar**: Generar CSV de transacciones (bonus)

#### Callbacks
```
"gamif:admin:transactions"                 # Pedir user_id
"gamif:transactions:user:{user_id}"        # Historial de usuario
"gamif:transactions:filter:{user_id}:{type}"  # Filtrar
"gamif:transactions:page:{user_id}:{page}" # Paginar
```

---

## FORMATO DE SALIDA

### Vista de Historial
```
💰 HISTORIAL DE BESITOS
Usuario ID: 12345
━━━━━━━━━━━━━━━━

Filtro: Todos | [📋 Misiones] [🛒 Compras] [⚙️ Admin]

Página 1/5

🟢 +500 | Misión completada
   Ref: Misión #8
   Balance: 1,250 → 1,750
   2024-01-15 14:30

🔴 -200 | Compra de recompensa
   Ref: Reward #5
   Balance: 1,750 → 1,550
   2024-01-14 10:15

...

[⬅️] [Página 1/5] [➡️]
[🔙 Volver]
```

### Resumen Estadístico
```
📊 RESUMEN
━━━━━━━━━━━━━━━━

Total ganado: +5,420
Total gastado: -1,200
Balance actual: 4,220

Por tipo:
• Reacciones: +2,100
• Misiones: +2,500
• Compras: -1,200
• Admin: +820
```

---

## CASOS DE PRUEBA

### Integridad
1. Crear transaction con amount=+500 → balance_after debe ser old_balance + 500
2. Crear 10 transactions → query por user_id debe retornar ordenado por created_at DESC

### Validación
3. Intentar crear transaction sin user_id → error de FK
4. Query con filtro MISSION_REWARD → solo retorna ese tipo

### Migración
5. Ejecutar `alembic upgrade head` → tabla creada con índices
6. Ejecutar `alembic downgrade -1` → tabla eliminada sin errores

---

## ESPECIFICACIÓN GHERKIN

```gherkin
Feature: Sistema de Transacciones

Scenario: Registrar transacción al otorgar besitos
  Given usuario con balance 1000
  When BesitoService.grant_besitos(user_id=123, amount=500)
  Then crea UserGamification con total_besitos=1500
  And crea BesitoTransaction con amount=500, balance_after=1500

Scenario: Filtrar historial por tipo
  Given usuario con 10 transactions de tipos variados
  When admin filtra por "MISSION_REWARD"
  Then muestra solo transactions con transaction_type=MISSION_REWARD

Scenario: Paginación de historial
  Given usuario con 50 transactions
  When admin ve página 1
  Then muestra transactions 1-20 ordenadas por created_at DESC
```

---

## INTEGRACIÓN

### Modificar BesitoService
Actualizar métodos existentes:
```python
# En grant_besitos(), después de UPDATE UserGamification:
transaction = BesitoTransaction(
    user_id=user_id,
    amount=amount,
    transaction_type=transaction_type,
    description=description,
    reference_id=reference_id,
    balance_after=new_balance,  # Leer después de UPDATE
    created_at=datetime.now(UTC)
)
session.add(transaction)
```

### Agregar en Container
```python
# bot/gamification/services/container.py
@property
def transaction_service(self):
    if not self._transaction_service:
        self._transaction_service = TransactionService(self._session)
    return self._transaction_service
```

---

## NOTAS ADICIONALES

1. **Balance_after como verificación**: Usar para detectar race conditions. Si balance esperado != balance real, log error
2. **Soft-delete opcional**: Si se requiere, agregar `deleted_at` nullable
3. **Timezone UTC**: Todos los timestamps en UTC, convertir a local solo en UI
4. **Performance**: Índice compuesto (user_id, created_at DESC) es crítico para queries de historial

---

**ENTREGABLES**:
1. Modelo en `models.py`
2. Migración `005_add_besito_transaction.py`
3. Handler `transaction_history.py`
4. Actualización de BesitoService
