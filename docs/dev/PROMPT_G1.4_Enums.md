# PROMPT G1.4: Enums y Tipos Personalizados - Gamificación

---

## ROL

Actúa como Ingeniero de Software Senior especializado en Python type safety, enums y diseño de tipos personalizados para validación estricta.

---

## TAREA

Implementa todos los enums y tipos personalizados necesarios para el módulo de gamificación en `bot/gamification/database/enums.py`, garantizando type safety y validaciones claras.

---

## CONTEXTO

### Stack Tecnológico
- Python 3.11+ con type hints
- Enum (standard library)
- Typing (Optional, Literal, etc.)

### Arquitectura
```
bot/gamification/database/
├── models.py          # Usa estos enums
├── enums.py          # ← ESTE ARCHIVO
└── __init__.py
```

### Enums Requeridos

Los modelos en `models.py` referencian estos enums:

```python
# En Mission.mission_type
mission_type: Mapped[str]  # → MissionType enum

# En Mission.criteria
criteria: Mapped[str]  # JSON validado con MissionCriteriaType

# En UserMission.status
status: Mapped[str]  # → MissionStatus enum

# En Reward.reward_type
reward_type: Mapped[str]  # → RewardType enum

# En UserReward.obtained_via
obtained_via: Mapped[str]  # → ObtainedVia enum

# En Badge.rarity
rarity: Mapped[str]  # → BadgeRarity enum

# En ConfigTemplate.category
category: Mapped[str]  # → TemplateCategory enum

# En BesitoTransaction.transaction_type
transaction_type: Mapped[str]  # → TransactionType enum
```

---

## RESTRICCIONES TÉCNICAS

### Principios de Diseño
- **Enums como str:** Heredar de `str, Enum` para compatibilidad SQLAlchemy
- **Valores explícitos:** Usar snake_case (ej: `ONE_TIME = "one_time"`)
- **Docstrings:** Documentar cada enum y sus valores
- **No valores mágicos:** Todo string debe estar en un enum

### Formato de Enum
```python
class MissionType(str, Enum):
    """Tipos de misión disponibles."""
    
    ONE_TIME = "one_time"        # Misión única (ej: bienvenida)
    DAILY = "daily"              # Se repite diariamente
    WEEKLY = "weekly"            # Se repite semanalmente
    STREAK = "streak"            # Basada en rachas consecutivas
    
    def __str__(self) -> str:
        return self.value
```

### Validación de JSON
Para campos JSON como `Mission.criteria`, definir tipos auxiliares:

```python
from typing import TypedDict, Literal

class StreakCriteria(TypedDict):
    """Criterios para misión tipo streak."""
    type: Literal["streak"]
    days: int
    require_consecutive: bool

class DailyCriteria(TypedDict):
    """Criterios para misión tipo daily."""
    type: Literal["daily"]
    count: int
    specific_reaction: str | None
```

---

## ENUMS A IMPLEMENTAR

### 1. MissionType
**Valores:**
- `ONE_TIME` - Misión única (completar una vez)
- `DAILY` - Misión diaria (resetea cada día)
- `WEEKLY` - Misión semanal (resetea cada semana)
- `STREAK` - Misión de racha (días consecutivos)

---

### 2. MissionStatus
**Valores:**
- `NOT_STARTED` - Usuario no ha iniciado la misión
- `IN_PROGRESS` - Misión activa pero no completada
- `COMPLETED` - Completada pero recompensa no reclamada
- `CLAIMED` - Recompensa reclamada
- `EXPIRED` - Misión expiró sin completarse (para temporales)

---

### 3. RewardType
**Valores:**
- `BADGE` - Badge/logro
- `ITEM` - Item virtual (futuro: stickers, etc.)
- `PERMISSION` - Permiso especial (ej: cambiar nombre, emoji custom)
- `TITLE` - Título especial para perfil
- `BESITOS` - Besitos extra (bonus)

---

### 4. BadgeRarity
**Valores:**
- `COMMON` - Común (fácil de obtener)
- `RARE` - Raro (requiere esfuerzo)
- `EPIC` - Épico (difícil)
- `LEGENDARY` - Legendario (muy difícil)

**Uso:** Define color/emoji en UI según rareza

---

### 5. ObtainedVia
**Valores:**
- `MISSION` - Obtenido completando misión
- `PURCHASE` - Comprado con besitos
- `ADMIN_GRANT` - Otorgado por admin
- `EVENT` - Evento especial (futuro)
- `LEVEL_UP` - Al subir de nivel

---

### 6. TransactionType
**Valores:**
- `MISSION_REWARD` - Recompensa de misión
- `REACTION` - Por reaccionar en canal
- `PURCHASE` - Compra de recompensa
- `ADMIN_GRANT` - Admin otorgó besitos
- `ADMIN_DEDUCT` - Admin quitó besitos
- `REFUND` - Devolución por error
- `STREAK_BONUS` - Bonus por racha
- `LEVEL_UP_BONUS` - Bonus por subir nivel

---

### 7. TemplateCategory
**Valores:**
- `MISSION` - Plantilla de misión
- `REWARD` - Plantilla de recompensa
- `LEVEL_PROGRESSION` - Plantilla de niveles completos
- `FULL_SYSTEM` - Sistema completo (misiones + recompensas + niveles)

---

## TIPOS AUXILIARES (TypedDict)

### Para Mission.criteria (JSON)

```python
# Definir estructuras para cada tipo de criterio
class StreakCriteria(TypedDict):
    type: Literal["streak"]
    days: int
    require_consecutive: bool

class DailyCriteria(TypedDict):
    type: Literal["daily"]
    count: int
    specific_reaction: str | None  # Emoji o None

class WeeklyCriteria(TypedDict):
    type: Literal["weekly"]
    target: int
    specific_days: list[int] | None  # [0-6] o None

class OneTimeCriteria(TypedDict):
    type: Literal["one_time"]
    # No necesita criterios adicionales
```

### Para Reward.metadata (JSON)

```python
class BadgeMetadata(TypedDict):
    icon: str  # Emoji
    rarity: str  # BadgeRarity value

class PermissionMetadata(TypedDict):
    permission_key: str  # ej: "custom_emoji", "change_username"
    expires_at: str | None  # ISO datetime o None (permanente)
```

---

## FORMATO DE SALIDA

Entrega el archivo completo `bot/gamification/database/enums.py`:

```python
# bot/gamification/database/enums.py

"""
Enums y tipos personalizados para el módulo de gamificación.

Contiene:
- Enums para campos de modelos (MissionType, RewardType, etc.)
- TypedDicts para validación de JSON (Criterias, Metadata)
"""

from enum import Enum
from typing import TypedDict, Literal

# ============================================================
# ENUMS PRINCIPALES
# ============================================================

class MissionType(str, Enum):
    """Tipos de misión disponibles en el sistema."""
    
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    STREAK = "streak"
    
    def __str__(self) -> str:
        return self.value

# ... resto de enums

# ============================================================
# TYPEDDICTS PARA JSON
# ============================================================

class StreakCriteria(TypedDict):
    """Estructura de criterios para misiones tipo streak."""
    type: Literal["streak"]
    days: int
    require_consecutive: bool

# ... resto de TypedDicts
```

---

## VALIDACIÓN

El archivo debe cumplir:
- ✅ Todos los enums heredan de `str, Enum`
- ✅ Valores en snake_case
- ✅ Docstrings en cada enum
- ✅ TypedDicts para estructuras JSON complejas
- ✅ Type hints completos
- ✅ Importable sin errores: `from bot.gamification.database.enums import MissionType`

---

## INTEGRACIÓN

Los servicios usarán estos enums así:

```python
# bot/gamification/services/mission.py
from bot.gamification.database.enums import MissionType, MissionStatus

async def create_mission(mission_type: MissionType, ...):
    if mission_type == MissionType.STREAK:
        # lógica específica
        pass
```

---

**ENTREGABLE:** Archivo `enums.py` completo con 7 enums + TypedDicts auxiliares.
