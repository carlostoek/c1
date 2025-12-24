# PROMPT G8.2: CRUD de Niveles

---

## ROL

Actúa como Ingeniero de Software Senior especializado en:
- Aiogram 3.4.1 (async handlers y FSM)
- SQLAlchemy 2.0 (async session, operaciones CRUD)
- Patrones CRUD con validaciones de integridad referencial

---

## TAREA

Implementa un módulo CRUD completo para gestión administrativa de niveles de gamificación en `bot/gamification/handlers/admin/level_config.py`, permitiendo crear, listar, editar y eliminar niveles con validaciones de coherencia en la progresión.

---

## CONTEXTO

### Stack Tecnológico
- Python 3.11+
- Aiogram 3.4.1 (handlers async, FSM, InlineKeyboard)
- SQLAlchemy 2.0 (async ORM)
- SQLite/PostgreSQL

### Modelo Existente
```python
# bot/gamification/database/models.py
class Level(Base):
    id: Mapped[int]
    name: Mapped[str]              # UNIQUE
    min_besitos: Mapped[int]       # Mínimo de besitos
    order: Mapped[int]             # UNIQUE - orden de progresión
    benefits: Mapped[str]          # JSON nullable
    active: Mapped[bool]
    created_at: Mapped[datetime]
```

### Servicio Disponible
```python
# bot/gamification/services/level.py (ya existe)
class LevelService:
    async def get_all_levels(active_only: bool) -> List[Level]
    async def get_level_by_id(level_id: int) -> Optional[Level]
    async def create_level(name, min_besitos, order, benefits) -> Level
    async def update_level(level_id, **kwargs) -> Level
    async def delete_level(level_id) -> bool
    async def get_level_distribution() -> dict  # Usuarios por nivel
```

### Integración con Sistema
- Entry point: Callback `"gamif:admin:levels"` (ya definido en menu.py)
- Debe actualizar UserGamification.current_level_id si usuarios están en nivel eliminado
- Validar que no se rompan progresiones (ej: no puede haber order=3 sin order=2)

---

## RESTRICCIONES TÉCNICAS

### Validaciones Obligatorias
1. **Nombre único**: No permitir duplicados
2. **Order único**: No dos niveles con mismo order
3. **Min_besitos único**: No dos niveles con mismo mínimo
4. **Progresión secuencial**: 
   - Si se crea order=5, deben existir orders 1,2,3,4
   - Si se elimina order=3, advertir que rompe secuencia
5. **Integridad referencial**: 
   - Si nivel tiene usuarios asignados, no permitir eliminación directa
   - Ofrecer reasignar usuarios a otro nivel antes de eliminar

### Estados FSM Requeridos
```python
class LevelConfigStates(StatesGroup):
    waiting_name = State()
    waiting_min_besitos = State()
    waiting_order = State()
    editing_field = State()
```

### Patrones de Callback
```
"gamif:admin:levels"              # Lista todos los niveles
"gamif:level:add"                 # Inicia creación
"gamif:level:view:{level_id}"     # Ver detalles + opciones
"gamif:level:edit:{level_id}"     # Menú de edición
"gamif:level:edit_field:{level_id}:{field}"  # Editar campo específico
"gamif:level:toggle:{level_id}"   # Activar/desactivar
"gamif:level:delete:{level_id}"   # Eliminar (con validaciones)
```

### Manejo de Errores
- Si usuario ingresa texto no numérico en min_besitos/order → mensaje claro, retry
- Si nombre duplicado → mostrar nivel existente, pedir otro nombre
- Si rompe progresión → explicar el problema, sugerir order correcto

---

## FORMATO DE SALIDA

### Estructura del Archivo
Genera un archivo Python único `bot/gamification/handlers/admin/level_config.py` con:

1. **Imports necesarios**
2. **Router con filtros admin**
3. **Estados FSM**
4. **Handler de lista** (menú principal con todos los niveles)
5. **Handler de creación** (wizard con FSM)
6. **Handler de vista detallada** (nivel individual + stats)
7. **Handlers de edición** (por campo)
8. **Handler de eliminación** (con validaciones)
9. **Funciones auxiliares de validación**

### Formato de Mensajes
Usa texto estructurado con Markdown HTML:
```
📊 <b>NIVELES CONFIGURADOS</b>
━━━━━━━━━━━━━━━━

1. 🌱 Novato (0-500 besitos)
2. ⭐ Regular (500-2000 besitos)
...

Total: 5 niveles | Usuarios distribuidos: [ver detalles]
```

### Validación de Implementación
El código debe:
- ✅ Listar niveles ordenados por `order` ASC
- ✅ Mostrar cuántos usuarios hay en cada nivel (via `get_level_distribution()`)
- ✅ Prevenir creación de niveles con order que rompa secuencia
- ✅ Advertir si se intenta eliminar nivel con usuarios asignados
- ✅ Usar FSM para entrada de datos multi-paso
- ✅ Confirmar eliminaciones con callback de confirmación

---

## CASOS DE PRUEBA ESPERADOS

### Happy Path
1. Admin crea nivel "Experto" con min_besitos=5000, order=4 (existiendo 1,2,3) → ✅ Creado
2. Admin edita min_besitos de nivel 2 de 500 a 600 → ✅ Actualizado
3. Admin desactiva nivel sin usuarios → ✅ Desactivado

### Casos Límite
4. Admin intenta crear nivel con order=10 cuando solo existe hasta order=3 → ❌ Error + sugerencia de usar order=4
5. Admin intenta nombre duplicado "Novato" → ❌ Rechazado con mensaje "Ya existe nivel 'Novato' (ID: 1)"

### Error Handling
6. Admin intenta eliminar nivel con 150 usuarios asignados → ⚠️ Warning + opción de reasignar usuarios a otro nivel
7. Admin ingresa "abc" en min_besitos → ❌ "Debe ser número positivo"

---

## ESPECIFICACIÓN GHERKIN (Referencia)

```gherkin
Feature: Gestión CRUD de Niveles

Scenario: Crear nivel nuevo válido
  Given niveles existentes con orders [1,2,3]
  When admin crea nivel "Experto" con min_besitos=5000 y order=4
  Then nivel se crea exitosamente
  And aparece en lista ordenado por order

Scenario: Prevenir creación con order que rompe secuencia
  Given niveles existentes con orders [1,2,3]
  When admin intenta crear nivel con order=10
  Then sistema rechaza con error
  And sugiere usar order=4

Scenario: Eliminar nivel con usuarios asignados
  Given nivel "Regular" (ID: 2) con 50 usuarios
  When admin intenta eliminar nivel 2
  Then sistema muestra warning
  And ofrece reasignar usuarios a otro nivel
  And solo elimina después de confirmación y reasignación
```

---

## INTEGRACIÓN

### Registro en Main
```python
# bot/main.py
from bot.gamification.handlers.admin import level_config
dp.include_router(level_config.router)
```

### Acceso desde Menú Admin
El callback `"gamif:admin:levels"` ya está definido en `handlers/admin/main.py` (G4.2). Este handler debe responder a ese callback.

---

## NOTAS DE IMPLEMENTACIÓN

1. **Reasignación de usuarios**: Si nivel tiene usuarios y se elimina, ejecutar:
   ```python
   # Pseudocódigo
   users_in_level = get_users_in_level(level_id)
   if users_in_level > 0:
       show_reassign_menu(other_levels)
       await update_users_level(from_level_id, to_level_id)
   delete_level(level_id)
   ```

2. **Validación de progresión**: Antes de crear/editar order, verificar:
   ```python
   existing_orders = [level.order for level in all_levels]
   if new_order > max(existing_orders) + 1:
       raise ValueError(f"Debe usar order {max(existing_orders) + 1}")
   ```

3. **JSON benefits**: Si admin quiere editar benefits, permitir entrada de JSON válido o usar wizard estructurado

---

**ENTREGABLE**: Archivo único `level_config.py` con CRUD completo, validaciones de integridad y manejo robusto de errores.
