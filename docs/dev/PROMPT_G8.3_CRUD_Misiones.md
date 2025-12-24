# PROMPT G8.3: CRUD de Misiones

---

## ROL

Actúa como Ingeniero de Software Senior especializado en:
- Aiogram 3.4.1 (handlers async, FSM, paginación de listas)
- SQLAlchemy 2.0 (queries complejas con joins)
- Validación de estructuras JSON dinámicas

---

## TAREA

Implementa módulo CRUD para gestión administrativa de misiones en `bot/gamification/handlers/admin/mission_config.py`, incluyendo listado paginado, edición de campos individuales y gestión del ciclo de vida de misiones.

---

## CONTEXTO

### Modelo Existente
```python
class Mission(Base):
    id: Mapped[int]
    name: Mapped[str]
    description: Mapped[str]
    mission_type: Mapped[str]          # MissionType enum
    criteria: Mapped[str]              # JSON
    besitos_reward: Mapped[int]
    auto_level_up_id: Mapped[int]      # FK nullable
    unlock_rewards: Mapped[str]        # JSON array de IDs
    repeatable: Mapped[bool]
    active: Mapped[bool]
    created_by: Mapped[int]
```

### Servicio Disponible
```python
class MissionService:
    async def get_all_missions(active_only: bool) -> List[Mission]
    async def get_mission_by_id(mission_id: int) -> Optional[Mission]
    async def create_mission(...) -> Mission
    async def update_mission(mission_id: int, **kwargs) -> Mission
    async def delete_mission(mission_id: int) -> bool
    async def get_mission_stats(mission_id: int) -> dict  # completions, active users
```

### Tipos de Criterios (JSON dinámico)
```python
# STREAK
{"type": "streak", "days": 7, "require_consecutive": true}

# DAILY
{"type": "daily", "count": 5, "specific_reaction": "❤️"}

# WEEKLY
{"type": "weekly", "target": 50, "specific_days": [1,3,5]}

# ONE_TIME
{"type": "one_time"}
```

---

## RESTRICCIONES TÉCNICAS

### Paginación Obligatoria
- Lista debe paginar de 10 en 10 misiones
- Usar offset/limit en query
- Botones: [⬅️ Anterior] [Página X/Y] [Siguiente ➡️]

### Validaciones
1. **Criterios JSON**: Validar con `validate_mission_criteria()` de validators.py antes de guardar
2. **Besitos reward**: Debe ser > 0
3. **Auto level-up**: Si se especifica, validar que level_id exista
4. **Unlock rewards**: Si se especifican IDs, validar que rewards existan

### Estados FSM
```python
class MissionConfigStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    editing_field = State()
    editing_criteria = State()
```

### Callbacks
```
"gamif:admin:missions"                    # Lista paginada
"gamif:missions:page:{N}"                 # Cambiar página
"gamif:mission:view:{id}"                 # Ver detalles + stats
"gamif:mission:edit:{id}"                 # Menú edición
"gamif:mission:edit_field:{id}:{field}"   # Editar campo
"gamif:mission:toggle:{id}"               # Activar/desactivar
"gamif:mission:delete:{id}"               # Eliminar
```

### Mostrar Estadísticas
En vista detallada incluir:
- Usuarios con misión in_progress
- Usuarios que completaron
- Tasa de completación
- Besitos totales distribuidos

---

## FORMATO DE SALIDA

### Vista de Lista (Paginada)
```
📋 MISIONES CONFIGURADAS
━━━━━━━━━━━━━━━━

Página 1/3

1. ✅ Racha de 7 días (🔥 Streak)
   → 500 besitos | 45 completadas

2. ✅ Reactor Diario (📅 Daily)
   → 200 besitos | Repetible

3. ❌ Misión Especial (⭐ One-time)
   → 1000 besitos | Inactiva

[Botones inline por misión]
[⬅️] [Página 1/3] [➡️]
[➕ Crear] [🔙 Volver]
```

### Vista Detallada
```
📊 MISIÓN: Racha de 7 días
━━━━━━━━━━━━━━━━

🔥 Tipo: Streak
📝 Descripción: [...]

⚙️ CONFIGURACIÓN
• Criterio: 7 días consecutivos
• Recompensa: 500 besitos
• Nivel auto: Fanático (ID: 4)
• Repetible: ✅

📈 ESTADÍSTICAS
• En progreso: 12 usuarios
• Completadas: 45 veces
• Tasa completación: 78%
• Besitos distribuidos: 22,500

[✏️ Editar] [🔄 Toggle] [🗑️ Eliminar]
[🔙 Volver]
```

---

## CASOS DE PRUEBA

### Happy Path
1. Listar misiones → muestra paginado correctamente
2. Ver misión → stats actualizadas en tiempo real
3. Editar besitos_reward de 500 a 600 → actualizado

### Validaciones
4. Editar criteria con JSON inválido → rechazado con error específico
5. Crear misión con auto_level_up_id=999 (no existe) → error "Nivel no encontrado"

### Eliminación
6. Eliminar misión sin usuarios activos → eliminada
7. Eliminar misión con 10 usuarios in_progress → warning + confirmación

---

## ESPECIFICACIÓN GHERKIN

```gherkin
Feature: CRUD de Misiones

Scenario: Listar misiones paginadas
  Given 25 misiones configuradas
  When admin accede a lista de misiones
  Then muestra página 1 con 10 misiones
  And botón "Siguiente" habilitado

Scenario: Editar criteria de misión
  Given misión tipo DAILY con criteria {"type":"daily","count":5}
  When admin edita count a 10
  And valida JSON
  Then criteria actualizado a {"type":"daily","count":10}

Scenario: Eliminar misión con usuarios activos
  Given misión con 5 usuarios in_progress
  When admin intenta eliminar
  Then muestra warning con count de usuarios
  And requiere confirmación explícita
```

---

## INTEGRACIÓN

### Edición de Criteria (Complejo)
Dado que criteria es JSON dinámico por tipo, implementar:
1. Detectar mission_type
2. Mostrar formulario específico según tipo:
   - STREAK: pedir "días" y "consecutivo sí/no"
   - DAILY: pedir "count" y "emoji específico (opcional)"
   - Etc.
3. Construir JSON con estructura correcta
4. Validar con `validate_mission_criteria()`

### Paginación Helper
```python
# Pseudocódigo
def paginate(items: List, page: int, per_page: int = 10):
    total_pages = ceil(len(items) / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    return {
        'items': items[start:end],
        'page': page,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }
```

---

## NOTAS ADICIONALES

1. **Edición de unlock_rewards**: Si admin edita este campo, mostrar lista de rewards disponibles con checkboxes para selección múltiple
2. **Duplicar misión**: Bonus - botón "Duplicar" que crea copia con nombre "Copia de [nombre]"
3. **Filtros**: Agregar callback para filtrar por tipo: `"gamif:missions:filter:{type}"`

---

**ENTREGABLE**: Archivo único `mission_config.py` con CRUD completo, paginación funcional y validaciones de JSON.
