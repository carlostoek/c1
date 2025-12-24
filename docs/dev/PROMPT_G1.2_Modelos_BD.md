# PROMPT G1.2: Modelos de Base de Datos - Gamificación

**Framework:** 4-Layer  
**Complejidad:** Moderada  
**LLM Target:** Claude Sonnet / GPT-4

---

## ROL

Actúa como Ingeniero de Bases de Datos especializado en SQLAlchemy 2.0, diseño de esquemas relacionales y modelado de datos para sistemas de gamificación.

---

## TAREA

Implementa los 13 modelos de base de datos del módulo de gamificación en `bot/gamification/database/models.py`, siguiendo las convenciones del sistema existente y las mejores prácticas de SQLAlchemy 2.0 con type hints.

---

## CONTEXTO

### Stack Tecnológico
- SQLAlchemy 2.0+ (ORM async con Mapped, mapped_column)
- SQLite con WAL mode
- Python 3.11+ con type hints obligatorios
- aiosqlite para operaciones async

### Convenciones del Sistema Existente
```python
# bot/database/models.py (REFERENCIA)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, DateTime, Boolean, ForeignKey, Integer
from datetime import datetime, UTC

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
```

### Arquitectura de Gamificación
```
Flujo de datos:
1. Usuario reacciona → se crea Reaction y UserReaction
2. UserReaction actualiza UserStreak (racha)
3. Reacciones otorgan besitos → actualiza UserGamification.total_besitos
4. Besitos permiten subir de Level
5. Completar Mission otorga besitos/recompensas
6. UserMission trackea progreso de misiones
7. Reward puede desbloquearse por misiones/niveles
8. Badge es tipo especial de Reward
```

---

## RESTRICCIONES TÉCNICAS

### Principios de Diseño
- **Type hints obligatorios:** Usar `Mapped[tipo]` en todas las columnas
- **Defaults explícitos:** created_at, updated_at con UTC
- **Foreign Keys:** Definir relaciones bidireccionales con `relationship()`
- **JSON fields:** Usar String + validación en servicio (no JSON nativo)
- **Indexes:** Agregar donde haya búsquedas frecuentes
- **Nullable:** Explicitar `nullable=True` cuando aplique

### Tipos de Columnas Permitidos
```python
BigInteger  # Para user_id (Telegram IDs son grandes)
Integer     # Para IDs auto-incrementales
String(N)   # Textos con límite
Boolean     # Flags
DateTime    # Timestamps en UTC
Float       # Para futuros puntos decimales (opcional)
```

### Nomenclatura
- Tablas: `snake_case` plural (ej: `user_gamifications`)
- Columnas: `snake_case` singular
- Relaciones: `snake_case` descriptivo (ej: `user_missions`)
- FKs: `{tabla}_id` (ej: `mission_id`)

---

## MODELOS REQUERIDOS (13 total)

### 1. UserGamification
**Propósito:** Perfil de gamificación del usuario (1-to-1 con User del sistema core)

**Campos:**
- `user_id` (BigInteger, PK, FK a users.user_id)
- `total_besitos` (Integer, default=0) - Balance actual
- `besitos_earned` (Integer, default=0) - Total histórico ganado
- `besitos_spent` (Integer, default=0) - Total histórico gastado
- `current_level_id` (Integer, FK a levels.id, nullable)
- `created_at`, `updated_at`

**Relaciones:**
- `user` → User (sistema core)
- `current_level` → Level
- `missions` → UserMission (1-to-many)
- `rewards` → UserReward (1-to-many)

**Índices:**
- `user_id` (unique, PK)
- `total_besitos` (para leaderboard)

---

### 2. Reaction
**Propósito:** Catálogo de reacciones configuradas (emojis)

**Campos:**
- `id` (Integer, PK, autoincrement)
- `emoji` (String(10), unique) - ej: "❤️", "🔥"
- `besitos_value` (Integer, default=1) - Cuántos besitos otorga
- `active` (Boolean, default=True)
- `created_at`

**Relaciones:**
- `user_reactions` → UserReaction (1-to-many)

---

### 3. UserReaction
**Propósito:** Registro de cada reacción que hace un usuario (M2M User-Reaction)

**Campos:**
- `id` (Integer, PK, autoincrement)
- `user_id` (BigInteger, FK a user_gamification.user_id)
- `reaction_id` (Integer, FK a reactions.id)
- `channel_id` (BigInteger) - ID del canal donde reaccionó
- `message_id` (BigInteger) - ID del mensaje
- `reacted_at` (DateTime) - Timestamp de la reacción

**Relaciones:**
- `user_gamification` → UserGamification
- `reaction` → Reaction

**Índices:**
- `user_id, reacted_at` (para rachas)
- `user_id, channel_id` (para stats por canal)

---

### 4. UserStreak
**Propósito:** Rachas de reacciones consecutivas por usuario

**Campos:**
- `id` (Integer, PK, autoincrement)
- `user_id` (BigInteger, FK a user_gamification.user_id, unique)
- `current_streak` (Integer, default=0) - Días consecutivos actual
- `longest_streak` (Integer, default=0) - Récord histórico
- `last_reaction_date` (DateTime, nullable) - Último día que reaccionó
- `updated_at`

**Relaciones:**
- `user_gamification` → UserGamification (1-to-1)

**Lógica:**
- Si usuario reacciona hoy y ayer → current_streak += 1
- Si saltó un día → current_streak = 1
- Si current_streak > longest_streak → actualizar récord

---

### 5. Level
**Propósito:** Niveles disponibles en el sistema

**Campos:**
- `id` (Integer, PK, autoincrement)
- `name` (String(100), unique) - ej: "Novato", "Fanático"
- `min_besitos` (Integer) - Mínimo de besitos para alcanzar
- `order` (Integer) - Orden de progresión (1, 2, 3...)
- `benefits` (String(500), nullable) - JSON con beneficios (ej: permisos extra)
- `active` (Boolean, default=True)
- `created_at`

**Relaciones:**
- `users` → UserGamification (1-to-many via current_level_id)
- `missions` → Mission (1-to-many via auto_level_up_id)

**Índices:**
- `min_besitos` (para calcular level-ups)
- `order` (para mostrar progresión)

---

### 6. Mission
**Propósito:** Misiones configuradas por admins

**Campos:**
- `id` (Integer, PK, autoincrement)
- `name` (String(200))
- `description` (String(500))
- `mission_type` (String(50)) - Enum: "one_time", "daily", "weekly", "streak"
- `criteria` (String(1000)) - JSON con criterios (ej: {"type": "streak", "days": 7})
- `besitos_reward` (Integer) - Cuántos besitos otorga al completar
- `auto_level_up_id` (Integer, FK a levels.id, nullable) - Nivel que otorga automáticamente
- `unlock_rewards` (String(200), nullable) - JSON array de reward_ids
- `active` (Boolean, default=True)
- `repeatable` (Boolean, default=False) - Si se puede repetir
- `created_by` (BigInteger) - Admin que la creó
- `created_at`

**Relaciones:**
- `auto_level_up` → Level (nullable)
- `user_missions` → UserMission (1-to-many)

---

### 7. UserMission
**Propósito:** Progreso de cada usuario en misiones

**Campos:**
- `id` (Integer, PK, autoincrement)
- `user_id` (BigInteger, FK a user_gamification.user_id)
- `mission_id` (Integer, FK a missions.id)
- `progress` (String(500)) - JSON con progreso actual (ej: {"days_completed": 3})
- `status` (String(20)) - Enum: "in_progress", "completed", "claimed"
- `started_at` (DateTime)
- `completed_at` (DateTime, nullable)
- `claimed_at` (DateTime, nullable)

**Relaciones:**
- `user_gamification` → UserGamification
- `mission` → Mission

**Índices:**
- `user_id, mission_id` (unique composite - usuario no puede tener misión duplicada si no es repeatable)
- `user_id, status` (para filtrar misiones activas/completadas)

---

### 8. Reward
**Propósito:** Recompensas disponibles en el sistema

**Campos:**
- `id` (Integer, PK, autoincrement)
- `name` (String(200))
- `description` (String(500))
- `reward_type` (String(50)) - Enum: "badge", "item", "permission"
- `cost_besitos` (Integer, nullable) - Si se puede comprar con besitos
- `unlock_conditions` (String(1000), nullable) - JSON (ej: {"mission_id": 5})
- `metadata` (String(1000), nullable) - JSON con datos específicos del tipo
- `active` (Boolean, default=True)
- `created_by` (BigInteger)
- `created_at`

**Relaciones:**
- `user_rewards` → UserReward (1-to-many)

---

### 9. UserReward
**Propósito:** Recompensas obtenidas por usuarios

**Campos:**
- `id` (Integer, PK, autoincrement)
- `user_id` (BigInteger, FK a user_gamification.user_id)
- `reward_id` (Integer, FK a rewards.id)
- `obtained_at` (DateTime)
- `obtained_via` (String(50)) - Enum: "mission", "purchase", "admin_grant"
- `reference_id` (Integer, nullable) - ID de misión/transacción relacionada

**Relaciones:**
- `user_gamification` → UserGamification
- `reward` → Reward

**Índices:**
- `user_id, reward_id` (unique composite - evitar recompensas duplicadas)

---

### 10. Badge
**Propósito:** Tipo especial de recompensa (badges/logros)

**Campos:**
- `id` (Integer, PK, FK a rewards.id)
- `icon` (String(10)) - Emoji del badge (ej: "🏆")
- `rarity` (String(20)) - Enum: "common", "rare", "epic", "legendary"

**Relaciones:**
- `reward` → Reward (1-to-1, herencia)

**Nota:** Este modelo extiende Reward (joined table inheritance)

---

### 11. UserBadge
**Propósito:** Badges específicos obtenidos por usuarios (vista especializada)

**Campos:**
- `id` (Integer, PK, FK a user_rewards.id)
- `displayed` (Boolean, default=False) - Si se muestra en perfil

**Relaciones:**
- `user_reward` → UserReward (1-to-1)

**Nota:** También herencia de UserReward

---

### 12. ConfigTemplate
**Propósito:** Plantillas predefinidas para configuraciones comunes

**Campos:**
- `id` (Integer, PK, autoincrement)
- `name` (String(200))
- `description` (String(500))
- `template_data` (String(5000)) - JSON con configuración completa
- `category` (String(50)) - Enum: "mission", "reward", "level_progression"
- `created_by` (BigInteger)
- `created_at`

**Relaciones:** Ninguna (standalone)

---

### 13. GamificationConfig
**Propósito:** Configuración global del módulo (singleton, id=1)

**Campos:**
- `id` (Integer, PK, default=1)
- `besitos_per_reaction` (Integer, default=1)
- `max_besitos_per_day` (Integer, nullable) - Límite diario (anti-spam)
- `streak_reset_hours` (Integer, default=24) - Horas para romper racha
- `notifications_enabled` (Boolean, default=True)
- `updated_at`

**Relaciones:** Ninguna (singleton)

---

## FORMATO DE SALIDA

Entrega el archivo completo `bot/gamification/database/models.py` con:

1. **Imports** (SQLAlchemy, datetime, etc.)
2. **Base declarativa** (puede importarse de bot.database.models o redefinirse)
3. **Los 13 modelos** en el orden listado
4. **Relaciones bidireccionales** usando `relationship()` con `back_populates`
5. **Docstrings** en cada modelo explicando su propósito
6. **Type hints** completos (`Mapped[tipo]`)
7. **Índices** donde se especificaron

NO incluyas:
- Migraciones Alembic (van en G1.3)
- Servicios (van en Fase 2)
- Validadores (van en G3.1)

---

## EJEMPLO DE ESTRUCTURA

```python
# bot/gamification/database/models.py

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, DateTime, Boolean, ForeignKey, Integer, Index
from datetime import datetime, UTC
from typing import Optional, List

# Importar Base del sistema core o redefinir
from bot.database.models import Base

class UserGamification(Base):
    """
    Perfil de gamificación del usuario.
    
    Almacena balance de besitos, nivel actual y relaciones
    con misiones/recompensas.
    """
    __tablename__ = "user_gamification"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    total_besitos: Mapped[int] = mapped_column(Integer, default=0)
    # ... resto de campos
    
    # Relaciones
    current_level: Mapped[Optional["Level"]] = relationship(
        "Level",
        foreign_keys=[current_level_id],
        back_populates="users"
    )
    # ... resto de relaciones
    
    # Índices
    __table_args__ = (
        Index('ix_user_gamification_total_besitos', 'total_besitos'),
    )

# ... resto de modelos
```

---

## VALIDACIÓN

El archivo debe cumplir:
- ✅ Todos los modelos tienen docstrings
- ✅ Todas las columnas tienen type hints `Mapped[tipo]`
- ✅ ForeignKeys apuntan a tablas/columnas correctas
- ✅ Relaciones bidireccionales con `back_populates`
- ✅ Defaults explícitos donde aplica
- ✅ No hay imports circulares
- ✅ JSON fields como String (validación en servicios)

---

**ENTREGABLE:** Archivo `models.py` completo con 13 modelos SQLAlchemy 2.0, listo para crear migraciones.
