# Setup del Módulo de Gamificación

## Índice
- [Prerrequisitos](#prerrequisitos)
- [Migraciones](#migraciones)
- [Seed Data](#seed-data)
- [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
- [Configuración Inicial](#configuración-inicial)
- [Verificación de Instalación](#verificación-de-instalación)
- [Solución de Problemas](#solución-de-problemas)

## Prerrequisitos

Antes de instalar el módulo de gamificación, asegúrate de tener:

- Python 3.8+
- PostgreSQL o SQLite para persistencia
- Redis para cache y background jobs
- Telegram Bot Token
- Sistema de migraciones Alembic activo
- Paquetes requeridos en `requirements.txt`

## Migraciones

Primero, aplica las migraciones de base de datos necesarias para el módulo de gamificación:

```bash
# Aplica todas las migraciones pendientes
alembic upgrade head

# O si deseas aplicar solo las relacionadas con gamificación
alembic upgrade $(alembic heads | grep gamification)
```

Después de aplicar las migraciones, deberías ver las siguientes tablas creadas:
- `users`
- `user_profiles`
- `besito_transactions`
- `levels`
- `user_levels`
- `missions`
- `user_mission_progress`
- `rewards`
- Y otras tablas relacionadas con gamificación

## Seed Data

### 1. Plantilla Inicial

Para aplicar la plantilla inicial del sistema de gamificación:

```python
# En el bot, como administrador:
/gamification → Templates → Starter Pack
```

O alternativamente, puedes aplicar manualmente la plantilla:

```bash
# Aplicar plantilla inicial por comando
python -c "
from bot.container import Container
from bot.services.templates.mission_template_service import MissionTemplateService

container = Container()
template_service = container.mission_template_service()
template = template_service.get_by_name('starter_pack')
template_service.apply_template(template.id)
"
```

### 2. Configurar Reacciones

Necesitas configurar qué emojis otorgan besitos:

```python
# Ejemplo de configuración de reacciones
reaction_config = {
    '❤️': {'besitos': 1, 'daily_limit': 10},
    '👍': {'besitos': 1, 'daily_limit': 10},
    '🎉': {'besitos': 2, 'daily_limit': 5},
    '🔥': {'besitos': 3, 'daily_limit': 3},
}
```

## Configuración de Variables de Entorno

Agrega las siguientes variables al archivo `.env`:

```env
# Habilitar módulo de gamificación
GAMIFICATION_ENABLED=true

# Intervalo de auto-progresión (en horas)
AUTO_PROGRESSION_INTERVAL_HOURS=6

# Tiempo de reset de streaks (en horas)
STREAK_RESET_HOURS=24

# Notificaciones del sistema
NOTIFICATIONS_ENABLED=true

# Límites diarios
MAX_BESITOS_PER_USER_PER_DAY=50
MAX_REACTIONS_PER_MESSAGE=5

# Configuración de niveles
LEVEL_UP_NOTIFICATION_ENABLED=true

# Configuración de misiones
DAILY_MISSIONS_ENABLED=true
WEEKLY_MISSIONS_ENABLED=true

# Configuración de recompensas
REWARD_UNLOCK_NOTIFICATIONS=true

# Canal de notificaciones (opcional)
GAMIFICATION_ANNOUNCEMENT_CHANNEL=

# Configuración de cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600

# Configuración de backgrounds workers
BACKGROUND_JOBS_ENABLED=true
WORKER_QUEUE_NAME=gamification_queue
```

## Configuración Inicial

### 1. Activar el Hook de Reacciones

Asegúrate de que el hook de reacciones está registrado:

```python
# En la configuración del bot
from bot.hooks.reaction_hook import ReactionHook

# Registrar el hook
bot.add_hook(ReactionHook())
```

### 2. Iniciar Background Jobs

Si usas Celery o similar para background jobs:

```bash
# Iniciar worker de gamificación
celery -A bot.background_workers.gamification_worker worker --loglevel=info

# Alternativamente, iniciar scheduler
celery -A bot.background_workers.gamification_worker beat --loglevel=info
```

### 3. Configurar Canales Soportados

Agrega los canales donde se aplicará el sistema de gamificación:

```python
# Configurar canales
from bot.services.channel_service import ChannelService

channel_service = container.channel_service()
channel_service.register_channel(
    channel_id=-1001234567890,
    name="Canal Principal",
    gamification_enabled=True
)
```

## Verificación de Instalación

### 1. Verificar Servicios Activos

```python
# Verificar que los servicios están correctamente instanciados
from bot.container import Container

container = Container()

# Probar servicios
print("ReactionService:", container.reaction_service())
print("BesitoService:", container.besito_service())
print("LevelService:", container.level_service())
print("MissionService:", container.mission_service())
print("RewardService:", container.reward_service())
```

### 2. Probar Funcionalidades Básicas

Realiza pruebas básicas para verificar que todo funciona:

```python
# Probar registro de reacción
reaction_service = container.reaction_service()
result = reaction_service.record_reaction(
    user_id=123456789,  # ID del usuario que mandó el mensaje
    emoji='❤️',
    message_id=123,
    channel_id=-1001234567890,
    reacted_at=datetime.utcnow()
)
print("Reacción registrada:", result)
```

### 3. Verificar Base de Datos

Confirma que los modelos se conectan correctamente:

```python
from bot.models.user import User
from bot.database.session import SessionLocal

db = SessionLocal()
users_count = db.query(User).count()
print(f"Número de usuarios registrados: {users_count}")
db.close()
```

## Solución de Problemas

### Error: Table doesn't exist
**Solución:** Asegúrate de haber aplicado todas las migraciones:
```bash
alembic upgrade head
```

### Error: Service not found in container
**Solución:** Verifica que los servicios estén correctamente registrados en el contenedor DI.

### Error: Hook not registered
**Solución:** Confirma que el ReactionHook esté registrado antes de iniciar el bot.

### Error: No reactions being recorded
**Posibles causas:**
- El hook de reacciones no está funcionando
- Las reacciones no están configuradas correctamente
- El canal no está habilitado para gamificación

### Error: Background jobs not running
**Solución:**
1. Verifica que Redis esté corriendo
2. Asegúrate de haber iniciado el worker
3. Revisa el log de errores del worker