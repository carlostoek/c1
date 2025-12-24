# PROMPT G1.5: Configuración del Módulo - Gamificación

---

## ROL

Actúa como Ingeniero de Software Senior especializado en gestión de configuración, environment variables y feature flags en sistemas Python modulares.

---

## TAREA

Implementa el archivo de configuración del módulo de gamificación en `bot/gamification/config.py`, que gestione parámetros propios del módulo, feature flags y configuración dinámica desde base de datos.

---

## CONTEXTO

### Sistema de Configuración Existente
```python
# bot/config.py (REFERENCIA - sistema core)
from dotenv import load_dotenv
import os

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",")]
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")
    
    @classmethod
    def validate(cls) -> bool:
        """Valida que configuración mínima exista"""
        return bool(cls.BOT_TOKEN and cls.ADMIN_USER_IDS)
```

### Stack Tecnológico
- Python 3.11+
- python-dotenv para variables de entorno
- SQLAlchemy async para config dinámica desde BD

### Arquitectura
```
bot/gamification/
├── config.py          # ← ESTE ARCHIVO
├── database/
│   └── models.py      # GamificationConfig model
└── __init__.py
```

---

## RESTRICCIONES TÉCNICAS

### Configuración Híbrida

El módulo usa **dos fuentes de configuración**:

1. **Variables de entorno** (.env) - Valores estáticos, instalación
2. **Base de datos** (GamificationConfig) - Valores dinámicos, admin

```python
# Variables de entorno (.env)
GAMIFICATION_ENABLED=true
GAMIFICATION_MAX_BESITOS_PER_DAY=1000

# Base de datos (GamificationConfig, id=1)
besitos_per_reaction = 1
streak_reset_hours = 24
notifications_enabled = True
```

### Principios
- **Lazy loading:** Config desde BD se carga on-demand
- **Caching:** Valores de BD se cachean por 5 minutos
- **Fallbacks:** Si BD falla, usar defaults razonables
- **Validación:** Validar rangos (ej: besitos_per_reaction > 0)

---

## CONFIGURACIÓN REQUERIDA

### Variables de Entorno (.env)

```bash
# Activación del módulo
GAMIFICATION_ENABLED=true

# Límites globales
GAMIFICATION_MAX_BESITOS_PER_DAY=1000        # Anti-spam
GAMIFICATION_MAX_STREAK_DAYS=365             # Máximo de racha
GAMIFICATION_MIN_LEVEL_BESITOS=0             # Mínimo para crear nivel

# Features opcionales
GAMIFICATION_NOTIFICATIONS_ENABLED=true      # Notificaciones automáticas
GAMIFICATION_LEADERBOARD_ENABLED=true        # Mostrar leaderboards
GAMIFICATION_TRANSFERS_ENABLED=false         # Transferencias entre usuarios

# Performance
GAMIFICATION_CACHE_TTL_SECONDS=300           # 5 minutos de cache
GAMIFICATION_BATCH_SIZE=100                  # Procesamiento por lotes
```

### Clase GamificationConfig

```python
class GamificationConfig:
    """
    Configuración del módulo de gamificación.
    
    Combina variables de entorno (estáticas) con configuración
    de base de datos (dinámica, editable por admin).
    """
    
    # ========================================
    # ENVIRONMENT VARIABLES (estáticas)
    # ========================================
    
    ENABLED: bool
    MAX_BESITOS_PER_DAY: int
    MAX_STREAK_DAYS: int
    MIN_LEVEL_BESITOS: int
    
    NOTIFICATIONS_ENABLED: bool
    LEADERBOARD_ENABLED: bool
    TRANSFERS_ENABLED: bool
    
    CACHE_TTL_SECONDS: int
    BATCH_SIZE: int
    
    # ========================================
    # DATABASE CONFIG (dinámica)
    # ========================================
    
    # Cache de valores de BD
    _db_config_cache: dict = {}
    _cache_timestamp: float = 0
    
    @classmethod
    async def get_besitos_per_reaction(cls, session) -> int:
        """Obtiene besitos por reacción desde BD (con cache)"""
        pass
    
    @classmethod
    async def get_streak_reset_hours(cls, session) -> int:
        """Obtiene horas para resetear racha desde BD (con cache)"""
        pass
    
    @classmethod
    async def refresh_db_config(cls, session):
        """Refresca cache de configuración desde BD"""
        pass
    
    # ========================================
    # VALIDACIÓN
    # ========================================
    
    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """
        Valida configuración del módulo.
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @classmethod
    def get_summary(cls) -> str:
        """Resumen de configuración para logging"""
        pass
```

---

## LÓGICA DE CACHE

Implementar patrón de cache con TTL:

```python
from time import time

@classmethod
async def _get_db_value(cls, session, key: str, default):
    """Helper genérico para obtener valores de BD con cache"""
    
    # Si cache expiró, refrescar
    if time() - cls._cache_timestamp > cls.CACHE_TTL_SECONDS:
        await cls.refresh_db_config(session)
    
    # Retornar valor cacheado o default
    return cls._db_config_cache.get(key, default)

@classmethod
async def refresh_db_config(cls, session):
    """Carga config desde GamificationConfig (id=1) en BD"""
    try:
        from bot.gamification.database.models import GamificationConfig as DBConfig
        config = await session.get(DBConfig, 1)
        
        if config:
            cls._db_config_cache = {
                'besitos_per_reaction': config.besitos_per_reaction,
                'streak_reset_hours': config.streak_reset_hours,
                'notifications_enabled': config.notifications_enabled,
                # ...
            }
            cls._cache_timestamp = time()
    except Exception as e:
        logger.warning(f"Failed to load DB config: {e}, using defaults")
```

---

## VALIDACIONES

```python
@classmethod
def validate(cls) -> tuple[bool, str]:
    """Valida configuración"""
    
    # Validar rangos
    if cls.MAX_BESITOS_PER_DAY < 1:
        return False, "MAX_BESITOS_PER_DAY must be > 0"
    
    if cls.CACHE_TTL_SECONDS < 60:
        return False, "CACHE_TTL_SECONDS must be >= 60"
    
    if cls.BATCH_SIZE < 10 or cls.BATCH_SIZE > 1000:
        return False, "BATCH_SIZE must be between 10-1000"
    
    return True, "OK"
```

---

## FORMATO DE SALIDA

Entrega el archivo completo `bot/gamification/config.py`:

```python
# bot/gamification/config.py

"""
Configuración del módulo de gamificación.

Gestiona:
- Variables de entorno (.env)
- Configuración dinámica desde BD
- Cache de configuración
- Validación de parámetros
"""

from dotenv import load_dotenv
import os
import logging
from time import time
from typing import Optional

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class GamificationConfig:
    """Configuración híbrida del módulo de gamificación."""
    
    # Environment variables
    ENABLED = os.getenv("GAMIFICATION_ENABLED", "false").lower() == "true"
    # ... resto de variables
    
    # Cache
    _db_config_cache: dict = {}
    _cache_timestamp: float = 0
    
    @classmethod
    async def get_besitos_per_reaction(cls, session) -> int:
        """..."""
        pass
    
    # ... resto de métodos
```

---

## INTEGRACIÓN

### Uso en servicios

```python
# bot/gamification/services/reaction.py
from bot.gamification.config import GamificationConfig

async def record_reaction(session, user_id, emoji):
    # Obtener besitos por reacción desde config
    besitos = await GamificationConfig.get_besitos_per_reaction(session)
    
    # Otorgar besitos
    await besito_service.grant_besitos(user_id, besitos, ...)
```

### Uso en main.py

```python
# bot/main.py
from bot.gamification.config import GamificationConfig

async def on_startup():
    # Validar config del módulo
    is_valid, error = GamificationConfig.validate()
    if not is_valid:
        logger.error(f"Gamification config error: {error}")
    
    # Log resumen
    if GamificationConfig.ENABLED:
        logger.info(GamificationConfig.get_summary())
```

---

## VALIDACIÓN

El archivo debe cumplir:
- ✅ Carga variables de entorno en inicialización
- ✅ Cache de config BD con TTL
- ✅ Fallbacks si BD no disponible
- ✅ Método `validate()` con chequeos de rangos
- ✅ Método `get_summary()` para logging
- ✅ Type hints completos
- ✅ Docstrings en métodos públicos

---

**ENTREGABLE:** Archivo `config.py` completo con configuración híbrida (env + BD) y cache.
