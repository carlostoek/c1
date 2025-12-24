# PROMPT G1.3: Migraciones Alembic - Gamificación

**Framework:** 4-Layer  
**Complejidad:** Moderada  
**LLM Target:** Claude Sonnet / GPT-4

---

## ROL

Actúa como Ingeniero de Bases de Datos especializado en Alembic y migraciones de esquemas SQLAlchemy, con enfoque en integridad referencial y versionado de cambios.

---

## TAREA

Crea la migración inicial de Alembic para el módulo de gamificación que incluya los 13 modelos implementados en G1.2, respetando el orden de dependencias y las foreign keys.

---

## CONTEXTO

### Sistema de Migraciones Existente
```
alembic/
├── alembic.ini
├── env.py
├── script.py.mako
└── versions/
    ├── 001_initial.py              # Sistema core
    ├── 002_add_subscription_plans.py
    └── 003_add_users_and_roles.py
```

### Stack Tecnológico
- Alembic 1.13+
- SQLAlchemy 2.0
- SQLite con WAL mode

### Modelos a Migrar (Orden de Dependencias)
```
NIVEL 1 (sin FKs):
1. GamificationConfig
2. Reaction
3. Level
4. ConfigTemplate

NIVEL 2 (FK a User del core + NIVEL 1):
5. UserGamification (FK: user_id, current_level_id)
6. UserStreak (FK: user_id)

NIVEL 3 (FK a NIVEL 2):
7. UserReaction (FK: user_id, reaction_id)
8. Mission (FK: auto_level_up_id)
9. Reward (sin FKs adicionales)

NIVEL 4 (FK a NIVEL 3):
10. UserMission (FK: user_id, mission_id)
11. UserReward (FK: user_id, reward_id)

NIVEL 5 (Herencia de NIVEL 4):
12. Badge (FK: id → rewards.id)
13. UserBadge (FK: id → user_rewards.id)
```

### Convención de Nombres
- Archivo: `004_add_gamification_module.py`
- Revision ID: Auto-generado por Alembic
- Message: "Add gamification module with 13 tables"

---

## RESTRICCIONES TÉCNICAS

### Integridad Referencial
```python
# TODAS las FKs deben incluir ondelete
op.create_foreign_key(
    'fk_user_gamification_user_id',
    'user_gamification', 'users',
    ['user_id'], ['user_id'],
    ondelete='CASCADE'  # ← OBLIGATORIO
)
```

### Índices
Crear índices para:
- `user_gamification.total_besitos` (leaderboard)
- `user_reactions.user_id, user_reactions.reacted_at` (rachas)
- `user_missions.user_id, user_missions.status` (filtros)
- `levels.min_besitos` (level-ups)
- `levels.order` (progresión)

### Orden de Creación
1. Tablas sin FKs primero
2. Tablas con FKs después (respetando niveles)
3. Índices al final de cada tabla
4. FK constraints después de crear todas las tablas

### Datos Iniciales (Seed Data)
Incluir en `upgrade()`:
```python
# GamificationConfig (singleton)
op.execute("""
    INSERT INTO gamification_config (id, besitos_per_reaction, streak_reset_hours, notifications_enabled)
    VALUES (1, 1, 24, 1)
""")

# Reacciones por defecto
op.execute("""
    INSERT INTO reactions (emoji, besitos_value, active)
    VALUES 
        ('❤️', 1, 1),
        ('🔥', 1, 1),
        ('👍', 1, 1)
""")

# Niveles iniciales
op.execute("""
    INSERT INTO levels (name, min_besitos, "order", active)
    VALUES
        ('Novato', 0, 1, 1),
        ('Regular', 500, 2, 1),
        ('Entusiasta', 2000, 3, 1),
        ('Fanático', 5000, 4, 1),
        ('Leyenda', 10000, 5, 1)
""")
```

---

## FORMATO DE SALIDA

Entrega el archivo completo:

```python
# alembic/versions/004_add_gamification_module.py

"""Add gamification module with 13 tables

Revision ID: [auto-generado]
Revises: 003_add_users_and_roles
Create Date: [timestamp]
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC

# revision identifiers, used by Alembic.
revision = '[auto-generado por alembic]'
down_revision = '003_add_users_and_roles'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """
    Crea todas las tablas del módulo de gamificación.
    
    Orden:
    1. Tablas independientes
    2. Tablas con FKs
    3. Índices
    4. Seed data inicial
    """
    
    # NIVEL 1: Tablas sin FKs
    # -----------------------
    
    # 1. gamification_config
    op.create_table(
        'gamification_config',
        sa.Column('id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('besitos_per_reaction', sa.Integer(), nullable=False, server_default='1'),
        # ... resto de columnas
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. reactions
    op.create_table(
        'reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        # ... resto de columnas
        sa.PrimaryKeyConstraint('id')
    )
    # Índice
    op.create_index('ix_reactions_emoji', 'reactions', ['emoji'], unique=True)
    
    # ... resto de tablas siguiendo NIVELES 1-5
    
    # SEED DATA
    # ---------
    # Insertar datos iniciales aquí
    
    pass


def downgrade() -> None:
    """
    Elimina todas las tablas del módulo.
    
    Orden inverso a upgrade (NIVEL 5 → NIVEL 1)
    """
    
    # NIVEL 5
    op.drop_table('user_badges')
    op.drop_table('badges')
    
    # NIVEL 4
    op.drop_table('user_rewards')
    op.drop_table('user_missions')
    
    # ... resto en orden inverso
    
    pass
```

---

## VALIDACIÓN

La migración debe cumplir:
- ✅ Crear exactamente 13 tablas
- ✅ Todas las FKs tienen `ondelete`
- ✅ Índices creados según especificación
- ✅ Seed data incluido (config, reacciones, niveles)
- ✅ `downgrade()` elimina en orden inverso
- ✅ Ejecutable sin errores: `alembic upgrade head`

---

## COMANDOS DE TESTING

```bash
# Generar migración (si usas autogenerate)
alembic revision --autogenerate -m "Add gamification module"

# Aplicar migración
alembic upgrade head

# Verificar
sqlite3 bot.db ".tables"  # Debe mostrar las 13 tablas nuevas

# Rollback
alembic downgrade -1
```

---

**ENTREGABLE:** Archivo de migración completo listo para `alembic upgrade head`.
