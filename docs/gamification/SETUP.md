# Guía de Instalación - Módulo de Gamificación

## 📋 Requisitos Previos

Antes de instalar el módulo de gamificación, asegúrate de tener:

- Python 3.11+
- SQLAlchemy 2.0+
- Aiogram 3.4.1+
- SQLite (o PostgreSQL para producción)
- Alembic para migraciones
- Bot de Telegram con permisos adecuados

## 🚀 Instalación Paso a Paso

### 1. Aplicar Migraciones de Base de Datos

El módulo requiere una estructura de base de datos específica. Aplica las migraciones:

```bash
alembic upgrade head
```

Esto creará las 13 tablas necesarias para el sistema de gamificación:

- `users_gamification` - Perfiles de usuarios
- `levels` - Sistema de niveles
- `reactions` - Catálogo de reacciones
- `missions` - Sistema de misiones
- `user_missions` - Progreso de misiones por usuario
- `rewards` - Sistema de recompensas
- `user_rewards` - Recompensas obtenidas por usuario
- `user_streaks` - Sistema de rachas
- `mission_templates` - Plantillas predefinidas
- `gamification_config` - Configuración del sistema
- `besito_transactions` - Auditoría de transacciones
- `user_badges` - Sistema de badges raros
- `reward_unlock_conditions` - Condiciones de desbloqueo

### 2. Configurar Variables de Entorno

Agrega las siguientes variables al archivo `.env`:

```env
# Configuración General
GAMIFICATION_ENABLED=true
AUTO_PROGRESSION_INTERVAL_HOURS=6
STREAK_RESET_HOURS=24

# Configuración de Notificaciones
NOTIFICATIONS_ENABLED=true
NOTIFY_LEVEL_UP=true
NOTIFY_MISSION_COMPLETED=true
NOTIFY_REWARD_UNLOCKED=true
NOTIFY_STREAK_MILESTONE=true
NOTIFY_STREAK_LOST=false

# Configuración de Límites
MAX_DAILY_REACTIONS=50
MAX_DAILY_BESITOS_PER_USER=1000
MAX_BESITOS_MULTIPLIER=2.0
```

### 3. Inicializar Datos Básicos

Después de aplicar migraciones, es recomendable iniciar con una configuración básica:

```python
# Aplicar plantilla inicial
/gamification → Templates → Starter Pack
```

O mediante código:

```python
from bot.gamification.services.container import GamificationContainer
from bot.gamification.utils.templates import apply_template

# Inicializar container
container = GamificationContainer(session)

# Aplicar plantilla de inicio
result = await apply_template("starter_pack", container)
```

### 4. Configurar Reacciones Iniciales

Define los emojis que otorgan besitos:

```python
from bot.gamification.services.reaction import ReactionService

# Crear reacciones iniciales
reactions = [
    {"emoji": "❤️", "name": "Corazón", "besitos_value": 1},
    {"emoji": "🔥", "name": "Fuego", "besitos_value": 2},
    {"emoji": "👍", "name": "Pulgar Arriba", "besitos_value": 1},
    {"emoji": "👏", "name": "Aplausos", "besitos_value": 3},
]

reaction_service = await container.get_reaction_service()
for reaction in reactions:
    await reaction_service.create_reaction(**reaction)
```

### 5. Integrar con el Bot Existente

Asegúrate de registrar los handlers y background jobs en tu bot principal:

```python
# En main.py
from bot.gamification.handlers.admin import get_admin_router
from bot.gamification.handlers.user import get_user_router
from bot.gamification.background import get_background_router

# Registrar routers
dp.include_router(get_admin_router())
dp.include_router(get_user_router())
dp.include_router(get_background_router())

# Iniciar background jobs
from bot.gamification.background import start_background_jobs
await start_background_jobs()
```

## 🔧 Configuración Avanzada

### Configuración Personalizada

Puedes personalizar el comportamiento del sistema creando entradas en la tabla `gamification_config`:

```python
from bot.gamification.database.models import GamificationConfig

config = GamificationConfig(
    auto_progression_interval_hours=6,
    streak_reset_hours=24,
    max_daily_reactions=50,
    notifications_enabled=True,
    # ... otras configuraciones
)

session.add(config)
await session.commit()
```

### Integración con Sistema de Reacciones Existente

Para integrar con el sistema de reacciones existente del bot:

```python
from bot.gamification.background.reaction_hook import process_reaction_event

# En tu handler de reacciones existente
async def on_reaction_updated(message_reaction_updated: MessageReactionUpdated):
    # Procesar evento para gamificación
    await process_reaction_event(
        user_id=message_reaction_updated.user_id,
        emoji=str(message_reaction_updated.new_reaction[0].emoji),
        message_id=message_reaction_updated.message_id,
        chat_id=message_reaction_updated.chat.id
    )
```

## 🧪 Pruebas de Instalación

Después de la instalación, puedes verificar que todo esté funcionando:

1. Verifica que las tablas se hayan creado correctamente
2. Prueba el comando `/gamification` en el bot
3. Verifica que se puedan crear misiones mediante el wizard
4. Prueba una reacción para verificar que se otorgan besitos
5. Confirma que los background jobs están corriendo

## 🔍 Troubleshooting

### Problemas Comunes

**Error en migraciones**: Asegúrate de que alembic esté configurado correctamente con el módulo de gamificación.

**No se otorgan besitos**: Verifica que las reacciones estén correctamente configuradas y activas.

**No se reciben notificaciones**: Confirma que `NOTIFICATIONS_ENABLED=true` y que el usuario no haya bloqueado al bot.

### Verificación de Salud

Puedes verificar el estado del sistema con:

```python
from bot.gamification.services.container import GamificationContainer

container = GamificationContainer(session)
health = await container.health_check()  # Método hipotético
print(health)
```

## 🔄 Actualización de Versiones

Para actualizar a nuevas versiones del módulo:

1. Aplica nuevas migraciones: `alembic upgrade head`
2. Verifica la compatibilidad con tu versión actual de Aiogram
3. Prueba las funcionalidades críticas en un entorno de test

## ✅ Verificación Final

Después de completar la instalación:

- [ ] Migraciones aplicadas correctamente
- [ ] Variables de entorno configuradas
- [ ] Plantilla inicial aplicada
- [ ] Reacciones configuradas
- [ ] Handlers registrados
- [ ] Background jobs iniciados
- [ ] Pruebas básicas pasadas