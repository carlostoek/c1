# FASE A: EXTENSIONES DE WIZARDS - Sistema de Selección de Items Existentes

Este documento contiene 5 prompts para implementar el sistema de selección en wizards.

---
---

# PROMPT G-UTILS: Sistema de Paginación Reutilizable

---

## ROL

Ingeniero de Software Senior especializado en utilidades compartidas y DRY principles.

---

## TAREA

Implementa módulo de paginación genérico en `bot/gamification/utils/pagination.py` reutilizable por todos los handlers que requieran listas paginadas.

---

## CONTEXTO

### Stack
- Python 3.11+
- SQLAlchemy 2.0 (async queries)
- Aiogram 3.4.1 (InlineKeyboard)

### Uso Esperado
```python
# En cualquier handler
from bot.gamification.utils.pagination import paginate_items, build_pagination_keyboard

items = await service.get_all_items()
page_data = paginate_items(items, page=1, per_page=10)
keyboard = build_pagination_keyboard(
    page_data,
    callback_pattern="prefix:page:{page}"
)
```

---

## RESTRICCIONES TÉCNICAS

### Funciones Requeridas

1. **paginate_items()**
   - Input: lista de items, página actual, items por página
   - Output: dict con items paginados, metadata
   - Manejar listas vacías y páginas fuera de rango

2. **build_pagination_keyboard()**
   - Input: page_data dict, patrón de callback
   - Output: InlineKeyboardMarkup con botones [⬅️] [Pág X/Y] [➡️]
   - Solo mostrar botones si has_prev/has_next es True

3. **paginate_query()** (bonus)
   - Input: SQLAlchemy query, página, per_page
   - Output: ejecuta query con offset/limit, retorna page_data
   - Más eficiente que cargar todo en memoria

### Estructura de page_data
```python
{
    'items': [...],           # Items de la página actual
    'page': 1,                # Página actual
    'total_pages': 5,         # Total de páginas
    'total_items': 47,        # Total de items
    'per_page': 10,           # Items por página
    'has_next': True,         # Hay página siguiente
    'has_prev': False,        # Hay página anterior
    'start_index': 0,         # Índice inicio (para offset)
    'end_index': 10           # Índice fin
}
```

---

## FORMATO DE SALIDA

Archivo único `bot/gamification/utils/pagination.py` con:
- Imports necesarios
- Funciones documentadas con docstrings
- Type hints completos
- Manejo de edge cases

---

## CASOS DE PRUEBA

```gherkin
Scenario: Paginar lista normal
  Given 47 items con per_page=10
  When paginate_items(items, page=1)
  Then retorna 10 items, total_pages=5, has_next=True

Scenario: Última página con items parciales
  Given 47 items, página 5
  Then retorna 7 items, has_next=False

Scenario: Página fuera de rango
  Given 10 items, página 99
  Then retorna items vacíos o página 1 (comportamiento definido)
```

---

**ENTREGABLE**: `pagination.py` con utilidades reutilizables.

---
---

# PROMPT G4.1-EXT: Nuevos Estados FSM para Selección

---

## ROL

Ingeniero especializado en Aiogram FSM y flujos de estado complejos.

---

## TAREA

Extiende `bot/gamification/states/admin.py` agregando estados FSM para selección de items existentes en wizards.

---

## CONTEXTO

### Estados Actuales (ya existen)
```python
class MissionWizardStates(StatesGroup):
    select_type = State()
    enter_mission_name = State()
    # ... hasta 11 estados
    confirm = State()

class RewardWizardStates(StatesGroup):
    select_type = State()
    # ... 10 estados
    confirm = State()
```

### Nuevos Flujos Requeridos

**Misión Wizard - Selección de Nivel:**
1. Usuario elige "Seleccionar Nivel Existente"
2. Muestra lista paginada de niveles
3. Usuario selecciona uno o busca por nombre
4. Confirma selección (con warnings si aplica)

**Misión Wizard - Selección de Recompensas:**
1. Muestra lista paginada de rewards
2. Usuario puede seleccionar múltiples
3. Filtrar por tipo de reward
4. Confirmar selección múltiple

---

## RESTRICCIONES TÉCNICAS

### Estados a Agregar

```python
class MissionWizardStates(StatesGroup):
    # ... estados existentes ...
    
    # Selección de nivel
    select_level_mode = State()        # ¿Crear o Seleccionar?
    browse_levels = State()            # Lista paginada
    search_level = State()             # Búsqueda por nombre
    confirm_level = State()            # Confirmar con warnings
    
    # Selección de recompensas
    select_rewards_mode = State()      # ¿Crear o Seleccionar?
    browse_rewards = State()           # Lista paginada
    filter_rewards = State()           # Filtrar por tipo
    confirm_rewards = State()          # Confirmar múltiples

class RewardWizardStates(StatesGroup):
    # ... estados existentes ...
    
    # Selección de misión/nivel para unlock
    select_unlock_type = State()       # ¿Qué tipo de unlock?
    browse_missions = State()          # Lista misiones
    browse_levels_unlock = State()     # Lista niveles
    confirm_unlock = State()           # Confirmar condición
```

### Data Storage en FSM

Usar `state.update_data()` para acumular:
```python
# Ejemplo de data acumulada
{
    'mission_name': 'Racha 7 días',
    'level_selection': {
        'mode': 'select',  # o 'create'
        'level_id': 4,     # si mode=select
        'level_data': {...} # si mode=create
    },
    'rewards_selection': {
        'mode': 'select',
        'reward_ids': [2, 5, 7]  # selección múltiple
    }
}
```

---

## FORMATO DE SALIDA

Actualizar `states/admin.py` agregando nuevos estados a las clases existentes. Mantener organización por secciones con comentarios.

---

## VALIDACIÓN

- ✅ Estados permiten navegación forward/backward
- ✅ Data storage acumula correctamente con update_data()
- ✅ Estados soportan paginación (browse_*)
- ✅ Estados soportan búsqueda (search_*)

---

**ENTREGABLE**: `states/admin.py` actualizado con ~15 estados nuevos.

---
---

# PROMPT G3.4-EXT: ConfigurationOrchestrator - Métodos de Listado y Validación

---

## ROL

Arquitecto de Software especializado en orchestration patterns y validaciones complejas.

---

## TAREA

Extiende `bot/gamification/orchestrators/configuration.py` agregando métodos para listar items seleccionables y validar selecciones con warnings contextuales.

---

## CONTEXTO

### Orchestrator Actual
Ya tiene métodos:
- `create_mission_with_dependencies()`
- `create_complete_mission_system()`
- `apply_system_template()`

### Nuevas Responsabilidades
- Listar niveles/recompensas/misiones disponibles (con paginación)
- Validar selecciones y retornar warnings
- Construir wizard_data con mix de create/select

---

## RESTRICCIONES TÉCNICAS

### Métodos a Agregar

#### 1. Listado con Paginación
```python
async def get_selectable_levels(
    search: str = None,
    page: int = 1,
    per_page: int = 10
) -> dict:
    """
    Retorna niveles para selección en wizard.
    Incluye metadata útil (cuántos usuarios en cada nivel).
    """

async def get_selectable_rewards(
    reward_type: RewardType = None,
    search: str = None,
    available_only: bool = True,
    page: int = 1
) -> dict:
    """
    Retorna rewards con filtros.
    Incluye info de stock, usuarios que lo tienen, etc.
    """

async def get_selectable_missions(
    mission_type: MissionType = None,
    active_only: bool = True,
    page: int = 1
) -> dict:
    """
    Retorna misiones para unlock conditions.
    """
```

#### 2. Validación con Warnings
```python
async def validate_level_selection(
    level_id: int,
    context: dict  # Contiene mission_besitos, etc.
) -> dict:
    """
    Valida coherencia de nivel seleccionado.
    
    Returns:
    {
        'valid': True,
        'warnings': [
            "⚠️ Este nivel requiere 5000 besitos pero misión solo da 500"
        ],
        'level': Level object
    }
    """

async def validate_reward_selection(
    reward_id: int,
    context: dict
) -> dict:
    """
    Valida reward (stock, fechas, etc).
    """

async def validate_multiple_rewards(
    reward_ids: List[int],
    context: dict
) -> dict:
    """
    Valida selección múltiple de rewards.
    Detecta incompatibilidades entre ellos.
    """
```

#### 3. Constructor de wizard_data
```python
async def build_wizard_data_from_selections(
    selections: dict
) -> dict:
    """
    Transforma selecciones del wizard en formato
    para create_mission_with_dependencies().
    
    Input selections:
    {
        'mission': {...},
        'level_selection': {'mode': 'select', 'level_id': 4},
        'rewards_selection': {'mode': 'select', 'reward_ids': [2,5]}
    }
    
    Output wizard_data:
    {
        'mission': {...},
        'level': {'mode': 'select', 'level_id': 4},
        'rewards': [
            {'mode': 'select', 'reward_id': 2},
            {'mode': 'select', 'reward_id': 5}
        ]
    }
    """
```

---

## FORMATO DE SALIDA

Actualizar archivo existente agregando estos métodos. Mantener estructura:
```python
class ConfigurationOrchestrator:
    # ... métodos existentes ...
    
    # ========================================
    # MÉTODOS DE LISTADO PARA SELECCIÓN
    # ========================================
    
    async def get_selectable_levels(...):
        ...
    
    # ========================================
    # VALIDACIÓN DE SELECCIONES
    # ========================================
    
    async def validate_level_selection(...):
        ...
```

---

## CASOS DE PRUEBA

```gherkin
Scenario: Listar niveles con búsqueda
  Given 10 niveles configurados
  When get_selectable_levels(search="Fan")
  Then retorna solo niveles con "Fan" en nombre

Scenario: Validar nivel coherente
  Given misión otorga 500 besitos
  When valida nivel que requiere 1000 besitos
  Then valid=True pero con warning de coherencia

Scenario: Validar reward sin stock
  Given reward con stock_remaining=0
  When validate_reward_selection(reward_id=5)
  Then valid=False, error="Agotado"
```

---

**ENTREGABLE**: `configuration.py` actualizado con ~10 métodos nuevos.

---
---

# PROMPT G4.3-EXT: Wizard Misión - Flujos de Selección

---

## ROL

Ingeniero especializado en flujos conversacionales complejos con FSM en Aiogram.

---

## TAREA

Extiende `bot/gamification/handlers/admin/mission_wizard.py` agregando flujos de selección de niveles y recompensas existentes, integrándolos con el wizard actual.

---

## CONTEXTO

### Wizard Actual
Ya tiene flujo completo de CREAR misión con nivel nuevo y reward nuevo.

### Nueva Funcionalidad
En pasos donde antes solo podía CREAR, ahora ofrecer:
- [➕ Crear Nuevo] [🔍 Seleccionar Existente] [⏭️ Saltar]

---

## RESTRICCIONES TÉCNICAS

### Puntos de Integración

#### Paso 4: Nivel (ya existe)
**Antes:**
```python
@router.callback_query(MissionWizardStates.choose_auto_level)
# Solo opción: crear nuevo o saltar
```

**Después:**
```python
@router.callback_query(MissionWizardStates.choose_auto_level)
# Tres opciones:
# 1. Crear nuevo (mantener flujo existente)
# 2. Seleccionar existente (NUEVO)
# 3. Saltar
```

#### Paso 5: Recompensas
Similar, agregar opción "Seleccionar Existentes".

### Nuevos Handlers Requeridos

```python
# SELECCIÓN DE NIVEL

@router.callback_query(F.data == "wizard:level:select")
async def start_level_selection(callback, state, gamification):
    """
    Muestra lista paginada de niveles.
    Usa orchestrator.get_selectable_levels().
    """

@router.callback_query(F.data.startswith("wizard:level:page:"))
async def change_level_page(callback, state, gamification):
    """Navega páginas de niveles."""

@router.callback_query(F.data == "wizard:level:search")
async def search_level(callback, state):
    """Activa búsqueda por nombre."""

@router.message(MissionWizardStates.search_level)
async def receive_level_search(message, state, gamification):
    """Procesa búsqueda y muestra resultados."""

@router.callback_query(F.data.startswith("wizard:select_level:"))
async def select_level(callback, state, gamification):
    """
    Usuario seleccionó nivel.
    Valida con orchestrator.validate_level_selection().
    Muestra warnings si hay.
    Pide confirmación.
    """

@router.callback_query(MissionWizardStates.confirm_level, F.data == "wizard:level:confirm")
async def confirm_level_selection(callback, state):
    """
    Confirma selección.
    Guarda en state: {'level_selection': {'mode': 'select', 'level_id': X}}
    Continúa a paso de rewards.
    """

# SELECCIÓN DE RECOMPENSAS (similar pero con selección múltiple)

@router.callback_query(F.data == "wizard:rewards:select")
async def start_rewards_selection(callback, state, gamification):
    """Lista rewards con checkboxes."""

@router.callback_query(F.data.startswith("wizard:reward:toggle:"))
async def toggle_reward(callback, state):
    """
    Agrega/quita reward de selección.
    Usa state.get_data() para mantener lista.
    """

@router.callback_query(F.data == "wizard:rewards:done")
async def finish_rewards_selection(callback, state):
    """
    Finaliza selección múltiple.
    Guarda: {'rewards_selection': {'mode': 'select', 'reward_ids': [...]}}
    """
```

### Integración con Confirmación Final

Modificar handler de confirmación para usar nuevo formato:
```python
@router.callback_query(MissionWizardStates.confirm, F.data == "wizard:confirm")
async def confirm_mission(callback, state, gamification):
    data = await state.get_data()
    
    # Construir wizard_data con mix select/create
    wizard_data = await gamification.configuration_orchestrator.build_wizard_data_from_selections(data)
    
    # Crear usando orchestrator
    result = await gamification.configuration_orchestrator.create_mission_with_dependencies(wizard_data)
    
    # Mostrar resumen diferenciando creado vs vinculado
    ...
```

---

## FORMATO DE SALIDA

### Lista Paginada de Niveles
```
⭐ SELECCIONAR NIVEL
━━━━━━━━━━━━━━━━

Página 1/2

🌱 Novato (0-500 besitos)
   └ 150 usuarios

⭐ Regular (500-2000 besitos)
   └ 75 usuarios

[Botones inline por nivel]
[⬅️] [Pág 1/2] [➡️]
[🔍 Buscar] [➕ Crear Nuevo] [🔙 Volver]
```

### Confirmación con Warnings
```
📋 NIVEL SELECCIONADO
━━━━━━━━━━━━━━━━

⭐ Regular (500 besitos mín)

⚠️ ADVERTENCIA:
Este nivel requiere 500 besitos, pero tu
misión solo otorga 200. Los usuarios
necesitarán completar ~3 misiones para
alcanzar este nivel.

[✅ Continuar] [🔄 Elegir Otro]
```

### Resumen Final Diferenciado
```
🎉 CONFIGURACIÓN COMPLETA
━━━━━━━━━━━━━━━━

MISIÓN: Racha de 7 días
━━━━━━━━━━━━━━━━

✨ CREADO:
• Misión: Racha de 7 días

🔗 VINCULADO:
• Nivel: Fanático (ID: 4)
• Recompensas: Badge Racha (ID: 2), Item VIP (ID: 5)

[✅ Confirmar] [✏️ Editar] [❌ Cancelar]
```

---

## CASOS DE PRUEBA

```gherkin
Scenario: Seleccionar nivel existente
  Given wizard en paso de nivel
  When usuario elige "Seleccionar Existente"
  And selecciona nivel ID 4
  Then guarda {'mode': 'select', 'level_id': 4}
  And continúa a siguiente paso

Scenario: Búsqueda de nivel
  Given 10 niveles disponibles
  When usuario busca "Fanático"
  Then muestra solo nivel con nombre matching

Scenario: Selección múltiple de rewards
  Given lista de 20 rewards
  When usuario selecciona IDs 2, 5, 7
  And confirma selección
  Then guarda {'mode': 'select', 'reward_ids': [2,5,7]}
```

---

**ENTREGABLE**: `mission_wizard.py` actualizado con ~15 handlers nuevos para selección.

---
---

# PROMPT G4.4-EXT: Wizard Recompensa - Flujos de Selección

---

## ROL

Ingeniero especializado en wizards multi-paso con validaciones contextuales.

---

## TAREA

Extiende `bot/gamification/handlers/admin/reward_wizard.py` agregando flujos de selección de misiones/niveles existentes para unlock conditions.

---

## CONTEXTO

### Wizard Actual
Permite crear reward con unlock condition básica (un campo).

### Nueva Funcionalidad
En paso de unlock conditions:
- Seleccionar misión existente (lista paginada)
- Seleccionar nivel existente (lista paginada)
- Construir unlock múltiple (varias condiciones)

---

## RESTRICCIONES TÉCNICAS

### Punto de Integración

```python
# ANTES
@router.callback_query(RewardWizardStates.choose_unlock_type)
# Solo opción: crear nueva misión o saltar

# DESPUÉS
@router.callback_query(RewardWizardStates.choose_unlock_type)
# Opciones:
# 1. Por Misión Existente (NUEVO)
# 2. Por Nivel Existente (NUEVO)
# 3. Por Besitos (manual)
# 4. Múltiple (NUEVO - combinar varias)
# 5. Sin condición
```

### Nuevos Handlers

```python
# SELECCIÓN DE MISIÓN PARA UNLOCK

@router.callback_query(F.data == "wizard:unlock:mission_select")
async def select_mission_for_unlock(callback, state, gamification):
    """
    Lista misiones paginadas.
    Filtrar por tipo si es útil.
    """

@router.callback_query(F.data.startswith("wizard:unlock_mission:"))
async def confirm_mission_unlock(callback, state):
    """
    Guarda: {'unlock': {'type': 'mission', 'mission_id': X}}
    """

# SELECCIÓN DE NIVEL PARA UNLOCK

@router.callback_query(F.data == "wizard:unlock:level_select")
async def select_level_for_unlock(callback, state, gamification):
    """Lista niveles."""

@router.callback_query(F.data.startswith("wizard:unlock_level:"))
async def confirm_level_unlock(callback, state):
    """Guarda unlock condition."""

# UNLOCK MÚLTIPLE (combinar condiciones)

@router.callback_query(F.data == "wizard:unlock:multiple")
async def start_multiple_unlock(callback, state):
    """
    Inicia wizard de condiciones múltiples.
    Permite agregar condiciones una por una.
    """

@router.callback_query(F.data == "wizard:unlock:add_condition")
async def add_unlock_condition(callback, state):
    """
    Muestra opciones: [Misión] [Nivel] [Besitos]
    Acumula en lista.
    """

@router.callback_query(F.data == "wizard:unlock:finish_multiple")
async def finish_multiple_unlock(callback, state):
    """
    Construye JSON:
    {
        'type': 'multiple',
        'conditions': [
            {'type': 'mission', 'mission_id': 5},
            {'type': 'level', 'level_id': 3}
        ]
    }
    """
```

### Validación de Unlock

Antes de confirmar reward, validar:
```python
# Pseudocódigo
unlock_data = data.get('unlock')
validation = await orchestrator.validate_unlock_conditions(unlock_data)

if not validation['valid']:
    show_error(validation['error'])
    return

if validation['warnings']:
    show_warnings_and_confirm(validation['warnings'])
```

---

## FORMATO DE SALIDA

### Lista de Misiones para Unlock
```
📋 SELECCIONAR MISIÓN
━━━━━━━━━━━━━━━━

Para desbloquear esta recompensa,
el usuario deberá completar:

🔥 Racha de 7 días
   └ Activa | 45 completadas

📅 Reactor Diario
   └ Activa | Repetible

[Botones inline]
[⬅️] [Pág 1/2] [➡️]
[🔙 Volver]
```

### Constructor de Unlock Múltiple
```
🔓 UNLOCK MÚLTIPLE
━━━━━━━━━━━━━━━━

Condiciones actuales (requiere TODAS):

1. ✅ Completar misión: Racha 7 días
2. ✅ Alcanzar nivel: Fanático

[➕ Agregar Condición]
[🗑️ Eliminar] [✅ Finalizar]
```

---

## CASOS DE PRUEBA

```gherkin
Scenario: Unlock por misión existente
  Given wizard en paso de unlock
  When selecciona "Por Misión"
  And elige misión ID 5
  Then guarda {'type': 'mission', 'mission_id': 5}

Scenario: Unlock múltiple
  Given wizard en unlock múltiple
  When agrega condición misión ID 5
  And agrega condición nivel ID 3
  And finaliza
  Then construye JSON múltiple correcto
```

---

**ENTREGABLE**: `reward_wizard.py` actualizado con ~12 handlers nuevos.

---
---

## RESUMEN DE FASE A

**5 prompts generados:**

1. **G-UTILS**: Paginación reutilizable
2. **G4.1-EXT**: ~15 estados FSM nuevos
3. **G3.4-EXT**: ~10 métodos en Orchestrator
4. **G4.3-EXT**: ~15 handlers en mission_wizard
5. **G4.4-EXT**: ~12 handlers en reward_wizard

**Total estimado:** ~200-300 líneas de código nuevas distribuidas en 5 archivos.

**Funcionalidad final:** Wizards con capacidad de seleccionar items existentes mediante listas paginadas, búsqueda, validaciones contextuales y selección múltiple.
