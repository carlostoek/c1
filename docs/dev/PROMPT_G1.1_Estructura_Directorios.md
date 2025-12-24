# PROMPT G1.1: Estructura de Directorios del Módulo Gamificación

**Framework:** 4-Layer  
**Complejidad:** Simple  
**LLM Target:** Claude Sonnet / GPT-4

---

## ROL

Actúa como Arquitecto de Software Senior especializado en Python y diseño modular, experto en separación de responsabilidades y arquitectura de microservicios integrados.

---

## TAREA

Crea la estructura completa de directorios para el módulo de gamificación como sistema independiente integrado al bot de Telegram existente.

El módulo debe ser autónomo pero interoperable con el sistema actual mediante un shared container pattern.

---

## CONTEXTO

### Sistema Existente
```
bot/
├── main.py
├── config.py
├── database/
│   ├── __init__.py
│   ├── models.py          # Modelos: User, VIPSubscriber, etc.
│   └── enums.py
├── services/
│   ├── container.py       # ServiceContainer (DI + Lazy Loading)
│   ├── subscription.py
│   ├── channel.py
│   ├── config.py
│   └── stats.py
├── handlers/
│   ├── admin/
│   └── user/
├── middlewares/
├── states/
├── utils/
└── background/
```

### Stack Tecnológico
- Python 3.11+
- Aiogram 3.4.1 (Telegram Bot Framework)
- SQLAlchemy 2.0 + aiosqlite (ORM async)
- SQLite en WAL mode
- Alembic (migraciones)
- APScheduler (background jobs)

### Arquitectura Objetivo
El módulo de gamificación debe:
1. **Vivir en `bot/gamification/`** - Totalmente separado del código core
2. **Tener su propia estructura** - database, services, handlers, background
3. **Compartir infraestructura común** - Usar `bot/services/shared_container.py` para DI
4. **Ser plug-and-play** - Activable/desactivable mediante config

---

## RESTRICCIONES TÉCNICAS

### Principios de Diseño
- **Separación de responsabilidades:** Cada directorio tiene un propósito único
- **Convención sobre configuración:** Nombres de archivos predecibles
- **Inicialización explícita:** Cada subdirectorio tiene `__init__.py`
- **Imports relativos:** Usar `from bot.gamification.services import X`

### Estructura Requerida

El módulo debe contener estos directorios obligatorios:

1. **database/** - Modelos SQLAlchemy del módulo
   - 13 modelos a implementar (ver lista abajo)
   - Enums propios (MissionType, RewardType, etc.)

2. **services/** - Lógica de negocio
   - Servicios individuales (ReactionService, BesitoService, etc.)
   - Subdirectorio `orchestrator/` para orquestadores
   - Container propio que se integra con shared_container

3. **handlers/** - Handlers de Telegram
   - `admin/` - Wizards y configuración
   - `user/` - Perfil, misiones, leaderboard

4. **background/** - Background jobs
   - Auto-progression engine
   - Expiración de rachas

5. **states/** - FSM States para wizards
   - Estados para wizard de misiones
   - Estados para wizard de recompensas

6. **utils/** - Utilidades específicas del módulo
   - Validadores de criterios JSON
   - Formateadores de gamificación

7. **config.py** - Configuración del módulo
   - Parámetros propios (ej: BESITOS_PER_REACTION)
   - Feature flags

### Modelos a Considerar (13 total)
```
1. UserGamification       # Perfil de gamificación del usuario
2. Reaction               # Registro de reacciones
3. UserReaction          # Relación user-reaction (M2M)
4. UserStreak            # Rachas de usuarios
5. Level                 # Niveles disponibles
6. Mission               # Misiones configuradas
7. UserMission           # Progreso de misiones por usuario
8. Reward                # Recompensas disponibles
9. UserReward            # Recompensas obtenidas
10. Badge                # Badges (tipo de recompensa)
11. UserBadge            # Badges obtenidos
12. ConfigTemplate       # Plantillas predefinidas
13. GamificationConfig   # Config del módulo
```

### Archivos Especiales
- `__init__.py` en cada directorio (para imports)
- `README.md` en raíz del módulo (documentación)
- `ARCHITECTURE.md` en raíz del módulo (arquitectura interna)

---

## FORMATO DE SALIDA

Entrega la estructura de directorios en **DOS FORMATOS**:

### Formato 1: Árbol Visual
```
bot/gamification/
├── __init__.py
├── README.md
├── ARCHITECTURE.md
├── config.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   └── enums.py
...
```

### Formato 2: Comandos Bash
Script ejecutable para crear toda la estructura:
```bash
#!/bin/bash
mkdir -p bot/gamification/database
touch bot/gamification/database/__init__.py
...
```

### Formato 3: Descripción de Cada Archivo/Directorio

Para cada elemento de la estructura, explica brevemente:
- **Propósito:** ¿Qué contiene?
- **Contenido inicial:** ¿Qué debe tener en el primer commit?
- **Dependencias:** ¿Importa de dónde?

Ejemplo:
```
bot/gamification/services/besito.py
-----------------------------------
Propósito: Gestión de economía de besitos (otorgar, gastar, auditoría)
Contenido inicial: Clase BesitoService con métodos placeholder
Dependencias: 
  - from bot.gamification.database.models import UserGamification
  - from sqlalchemy.ext.asyncio import AsyncSession
```

---

## VALIDACIÓN

La estructura debe cumplir:
- ✅ Todos los archivos `__init__.py` existen
- ✅ No hay directorios vacíos (cada uno tiene al menos 1 archivo)
- ✅ Nomenclatura consistente (snake_case para archivos)
- ✅ Separación clara entre admin/user en handlers
- ✅ `bot/gamification/` es importable como módulo Python

---

## INTEGRACIÓN CON SISTEMA EXISTENTE

Además de la estructura interna del módulo, indica dónde/cómo modificar el sistema existente:

1. **bot/services/shared_container.py** (NUEVO)
   - Qué debe contener este archivo
   - Cómo ambos módulos lo utilizan

2. **bot/main.py**
   - Qué imports agregar
   - Cómo registrar handlers de gamificación

3. **alembic/**
   - Cómo organizar migraciones del módulo

---

**NOTA IMPORTANTE:** No escribas código completo, solo:
- Estructura de directorios
- Nombres de archivos
- Propósito de cada componente
- Comandos para crear la estructura

El código de implementación se generará en tareas posteriores.
