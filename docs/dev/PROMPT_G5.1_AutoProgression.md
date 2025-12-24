# PROMPT G5.1: Auto-Progression Checker - Background Job

---

## ROL

Actúa como Ingeniero de Software Senior especializado en jobs asíncronos, schedulers y procesamiento batch.

---

## TAREA

Implementa el background job `auto_progression_checker.py` en `bot/gamification/background/` que verifica y aplica level-ups automáticos periódicamente.

---

## CONTEXTO

### Problema

Level-ups solo ocurren cuando el usuario interactúa. Si un usuario gana besitos suficientes pero no vuelve al bot, queda en nivel incorrecto hasta su próxima interacción.

**Solución:** Job que ejecuta cada X horas y verifica todos los usuarios.

### Arquitectura
```
bot/gamification/background/
├── auto_progression_checker.py    # ← ESTE ARCHIVO
├── streak_expiration.py            # G5.2
└── __init__.py
```

---

## RESPONSABILIDADES

### 1. Job Principal

```python
async def check_all_users_progression(session: AsyncSession):
    """
    Verifica level-ups pendientes para todos los usuarios.
    
    Flujo:
    1. Obtener todos los UserGamification
    2. Para cada usuario:
       - Llamar level_service.check_and_apply_level_up()
       - Si hubo cambio, notificar al usuario
    3. Log de estadísticas (X usuarios procesados, Y level-ups)
    
    Batch processing: 100 usuarios por lote
    """
```

### 2. Scheduler Setup

```python
def setup_auto_progression_scheduler(scheduler: AsyncIOScheduler, session_maker):
    """
    Configura job en scheduler.
    
    Frecuencia: Cada 6 horas
    Trigger: interval
    """
```

### 3. Notificaciones

```python
async def notify_level_up(bot: Bot, user_id: int, old_level: Level, new_level: Level):
    """
    Envía mensaje privado al usuario informando level-up.
    
    Mensaje:
    🎉 ¡Subiste de nivel!
    
    Nivel anterior: {old_level.name}
    Nivel nuevo: {new_level.name}
    
    Beneficios desbloqueados: ...
    """
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/background/auto_progression_checker.py

"""
Background job: Auto-progression checker.

Verifica periódicamente usuarios que deben subir de nivel
pero no lo han hecho por falta de interacción.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from bot.gamification.database.models import UserGamification
from bot.gamification.services.level import LevelService

logger = logging.getLogger(__name__)


async def check_all_users_progression(session: AsyncSession, bot: Bot):
    """Verifica level-ups pendientes para todos los usuarios."""
    level_service = LevelService(session)
    
    # Obtener todos los usuarios
    stmt = select(UserGamification)
    result = await session.execute(stmt)
    all_users = result.scalars().all()
    
    processed = 0
    level_ups = 0
    
    # Procesar en batch
    BATCH_SIZE = 100
    for i in range(0, len(all_users), BATCH_SIZE):
        batch = all_users[i:i+BATCH_SIZE]
        
        for user_gamif in batch:
            try:
                changed, old_level, new_level = await level_service.check_and_apply_level_up(
                    user_gamif.user_id
                )
                
                if changed:
                    level_ups += 1
                    logger.info(
                        f"Auto level-up: User {user_gamif.user_id} "
                        f"{old_level.name} → {new_level.name}"
                    )
                    
                    # Notificar
                    await notify_level_up(bot, user_gamif.user_id, old_level, new_level)
                
                processed += 1
            
            except Exception as e:
                logger.error(f"Error processing user {user_gamif.user_id}: {e}")
        
        # Commit batch
        await session.commit()
    
    logger.info(
        f"Auto-progression check completed: "
        f"{processed} users processed, {level_ups} level-ups applied"
    )


async def notify_level_up(bot: Bot, user_id: int, old_level, new_level):
    """Notifica level-up al usuario."""
    try:
        message = (
            f"🎉 <b>¡Subiste de nivel!</b>\n\n"
            f"Nivel anterior: {old_level.name}\n"
            f"<b>Nivel nuevo: {new_level.name}</b>\n\n"
            f"Mínimo de besitos: {new_level.min_besitos}"
        )
        
        await bot.send_message(user_id, message, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")


def setup_auto_progression_scheduler(
    scheduler: AsyncIOScheduler,
    session_maker,
    bot: Bot
):
    """Configura job en scheduler."""
    
    async def job():
        async with session_maker() as session:
            await check_all_users_progression(session, bot)
    
    scheduler.add_job(
        job,
        trigger='interval',
        hours=6,
        id='auto_progression_checker',
        replace_existing=True
    )
    
    logger.info("Auto-progression checker scheduled (every 6 hours)")
```

---

## INTEGRACIÓN

```python
# bot/main.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.gamification.background.auto_progression_checker import setup_auto_progression_scheduler

async def main():
    # ... setup bot y session ...
    
    scheduler = AsyncIOScheduler()
    
    # Setup gamification jobs
    setup_auto_progression_scheduler(scheduler, async_session, bot)
    
    scheduler.start()
    
    # ... start polling ...
```

---

## CONFIGURACIÓN

```python
# .env
AUTO_PROGRESSION_ENABLED=true
AUTO_PROGRESSION_INTERVAL_HOURS=6
AUTO_PROGRESSION_BATCH_SIZE=100
NOTIFY_LEVEL_UP=true
```

---

## VALIDACIÓN

- ✅ Procesamiento en batch (100 usuarios)
- ✅ Scheduler configurado (cada 6h)
- ✅ Notificaciones al usuario
- ✅ Logging de estadísticas
- ✅ Manejo de errores por usuario

---

**ENTREGABLE:** Archivo `auto_progression_checker.py` con job completo.
