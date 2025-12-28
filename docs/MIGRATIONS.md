# Guía de Migraciones de Base de Datos

## Problema Detectado (2025-12-28)

### Error Original
```
sqlite3.OperationalError: no such column: narrative_fragments.extra_metadata
```

### Causa Raíz
El proyecto usa `Base.metadata.create_all()` en `bot/database/engine.py` para crear tablas.

**Comportamiento de `create_all()`:**
- ✅ **BD Nueva:** Crea todas las tablas con el esquema actual del modelo (funciona correctamente)
- ❌ **BD Existente:** NO modifica tablas existentes, solo crea las que faltan
- ❌ **NO ejecuta migraciones de Alembic** para cambios en tablas existentes

**Por qué ocurrió el error:**
1. La tabla `narrative_fragments` ya existía en la BD
2. Fue creada con una versión antigua del modelo (sin `extra_metadata`)
3. Se agregó el campo `extra_metadata` al modelo Python
4. `create_all()` no modificó la tabla existente
5. SQLAlchemy esperaba la columna pero no existía en la BD física

### Solución Aplicada
```bash
# Fix manual para bases de datos existentes
sqlite3 bot.db "ALTER TABLE narrative_fragments ADD COLUMN extra_metadata JSON;"
```

### Verificación (BD desde cero)
✅ **Confirmado:** Si borras `bot.db` y reinicias el bot, la columna `extra_metadata` se crea automáticamente.
```bash
# Test realizado 2025-12-28
rm bot.db
python main.py  # Crea BD desde cero
sqlite3 bot.db "PRAGMA table_info(narrative_fragments);"
# Resultado: columna extra_metadata presente (posición 12)
```

## Arquitectura Actual

### Inicialización de Base de Datos
- **Ubicación:** `bot/database/engine.py:init_db()`
- **Método:** `Base.metadata.create_all` (línea 156)
- **Comportamiento:**
  - ✅ Crea tablas nuevas automáticamente
  - ❌ NO ejecuta migraciones de Alembic para cambios en tablas existentes

### Migraciones de Alembic
- **Ubicación:** `alembic/versions/`
- **Estado:** Creadas manualmente pero NO ejecutadas automáticamente
- **Problema:** Las migraciones existen pero no se aplican al iniciar el bot

## Migraciones Pendientes Aplicadas Manualmente

### 015_rename_metadata_to_extra_metadata.py
**Aplicada:** 2025-12-28 12:22
**Método:** SQL directo (ver comando arriba)
**Cambio:** Agregó columna `extra_metadata` a `narrative_fragments`

## Soluciones Futuras

### Opción 1: Ejecutar Migraciones Manualmente (Actual)
Cuando se cree una nueva migración que modifique tablas existentes:

```bash
# 1. Ver esquema actual de tabla afectada
sqlite3 bot.db "PRAGMA table_info(table_name);"

# 2. Aplicar cambio con SQL directo
sqlite3 bot.db "ALTER TABLE ... ADD COLUMN ...;"

# 3. Verificar cambio
sqlite3 bot.db "PRAGMA table_info(table_name);"
```

### Opción 2: Integrar Alembic en init_db() (Recomendado)
Modificar `bot/database/engine.py:init_db()` para ejecutar migraciones automáticamente:

```python
from alembic.config import Config as AlembicConfig
from alembic import command

async def init_db() -> None:
    # ... código existente ...

    # Ejecutar migraciones de Alembic
    alembic_cfg = AlembicConfig("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # ... resto del código ...
```

**Requisitos:**
- Crear `alembic.ini` en raíz del proyecto
- Configurar `sqlalchemy.url` en `alembic.ini`

### Opción 3: Script de Setup Manual
Crear `scripts/run_migrations.sh`:

```bash
#!/bin/bash
# Ejecutar todas las migraciones pendientes
alembic upgrade head
```

## Checklist para Nuevas Migraciones

Cuando se cree una migración de Alembic:

- [ ] Verificar si afecta tablas existentes o crea nuevas
- [ ] Si crea nuevas tablas → ✅ `create_all()` las creará automáticamente
- [ ] Si modifica tablas existentes → ⚠️ Ejecutar migración manualmente:
  ```bash
  # Revisar qué cambios hace la migración
  cat alembic/versions/XXX_migration_name.py

  # Aplicar SQL directamente
  sqlite3 bot.db "ALTER TABLE ... ;"

  # Verificar cambio
  sqlite3 bot.db "PRAGMA table_info(table_name);"
  ```
- [ ] Documentar cambio en este archivo
- [ ] Probar que el sistema funciona después del cambio

## Historial de Migraciones Aplicadas

| Fecha | Migración | Tabla Afectada | Cambio | Método |
|-------|-----------|----------------|---------|--------|
| 2025-12-28 | 015 | narrative_fragments | Agregó `extra_metadata JSON` | SQL directo |

## Comandos Útiles

```bash
# Ver todas las tablas
sqlite3 bot.db ".tables"

# Ver esquema de tabla específica
sqlite3 bot.db "PRAGMA table_info(table_name);"

# Ver SQL de creación de tabla
sqlite3 bot.db ".schema table_name"

# Verificar columnas de todas las tablas narrativas
for table in narrative_chapters narrative_fragments fragment_decisions fragment_requirements user_narrative_progress user_decision_history; do
  echo "=== $table ==="
  sqlite3 bot.db "PRAGMA table_info($table);"
done
```

## FAQ - Preguntas Frecuentes

### ¿Si borro la BD y reinicio el bot, se crea el campo correctamente?

**Respuesta:** ✅ **SÍ**, completamente.

Cuando inicializas la base de datos desde cero:
1. `Base.metadata.create_all()` lee los modelos actuales de SQLAlchemy
2. Crea todas las tablas con todos los campos definidos en los modelos
3. Incluye campos nuevos como `extra_metadata`

**El problema solo ocurre en bases de datos existentes** creadas antes de que se agregara el campo al modelo.

### ¿Cuándo necesito aplicar migraciones manualmente?

Solo cuando:
1. Ya tienes una base de datos con datos
2. Se modifica el esquema de una tabla existente en el modelo
3. Quieres preservar los datos existentes

**No necesitas migraciones manuales si:**
- Empiezas con una BD nueva (el bot la crea correctamente)
- Solo se agregan tablas nuevas (no modificaciones a existentes)

### ¿Cómo saber si necesito aplicar una migración?

Si ves errores como:
```
sqlite3.OperationalError: no such column: table_name.column_name
```

Entonces:
1. Verifica que el campo existe en el modelo Python
2. Verifica que NO existe en la tabla física: `sqlite3 bot.db "PRAGMA table_info(table_name);"`
3. Aplica el cambio con `ALTER TABLE` o ejecuta la migración de Alembic

## Notas Importantes

1. **SQLite y ALTER TABLE:** SQLite tiene limitaciones con `ALTER TABLE`. Solo soporta:
   - ADD COLUMN
   - RENAME COLUMN (desde SQLite 3.25.0)
   - Cambios más complejos requieren recrear la tabla

2. **Migraciones Batch de Alembic:** Para cambios complejos, Alembic usa `batch_alter_table` que:
   - Crea tabla temporal
   - Copia datos
   - Elimina tabla original
   - Renombra temporal

3. **Backup:** Antes de aplicar migraciones manuales:
   ```bash
   cp bot.db bot.db.backup.$(date +%Y%m%d_%H%M%S)
   ```

4. **Verificación después de `create_all()`:** El sistema crea correctamente todas las columnas cuando la BD es nueva. Verificado 2025-12-28.

## Referencias

- [SQLAlchemy create_all()](https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.MetaData.create_all)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLite ALTER TABLE](https://www.sqlite.org/lang_altertable.html)
