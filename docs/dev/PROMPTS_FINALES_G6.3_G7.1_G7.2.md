# PROMPTS FINALES - MÓDULO GAMIFICACIÓN

Este documento contiene los 3 prompts finales del módulo de gamificación.

---
---

# PROMPT G6.3: Sistema de Notificaciones

---

## ROL

Ingeniero de Software Senior especializado en sistemas de notificaciones y messaging asíncrono.

---

## TAREA

Implementa el sistema de notificaciones en `bot/gamification/services/notifications.py` que envía alertas a usuarios sobre eventos de gamificación.

---

## CONTEXTO

### Eventos Notificables

1. **Level-up** - Subiste de nivel
2. **Mission completed** - Misión completada, reclama tu recompensa
3. **Reward unlocked** - Nueva recompensa disponible
4. **Streak milestone** - Alcanzaste X días de racha
5. **Streak lost** - Perdiste tu racha

---

## RESPONSABILIDADES

### 1. Servicio de Notificaciones

```python
class NotificationService:
    """Gestión de notificaciones del sistema."""
    
    async def notify_level_up(self, user_id: int, old_level: Level, new_level: Level)
    async def notify_mission_completed(self, user_id: int, mission: Mission)
    async def notify_reward_unlocked(self, user_id: int, reward: Reward)
    async def notify_streak_milestone(self, user_id: int, days: int)
    async def notify_streak_lost(self, user_id: int, days: int)
```

### 2. Configuración

```python
# .env
NOTIFICATIONS_ENABLED=true
NOTIFY_LEVEL_UP=true
NOTIFY_MISSION_COMPLETED=true
NOTIFY_REWARD_UNLOCKED=true
NOTIFY_STREAK_MILESTONE=true
NOTIFY_STREAK_LOST=false
```

### 3. Templates de Mensajes

```python
NOTIFICATION_TEMPLATES = {
    'level_up': """
🎉 <b>¡Subiste de nivel!</b>

{old_level.name} → <b>{new_level.name}</b>

Beneficios desbloqueados:
{benefits}
""",
    
    'mission_completed': """
✅ <b>Misión Completada</b>

<b>{mission.name}</b>
Recompensa: {mission.besitos_reward} besitos

Usa /profile para reclamarla
""",
    
    'reward_unlocked': """
🎁 <b>Nueva Recompensa Disponible</b>

<b>{reward.name}</b>
{reward.description}

Visita /profile para verla
""",
    
    'streak_milestone': """
🔥 <b>¡Racha Épica!</b>

Has reaccionado {days} días consecutivos

¡Sigue así!
""",
    
    'streak_lost': """
💔 <b>Racha Perdida</b>

Tu racha de {days} días expiró

Reacciona hoy para empezar una nueva
"""
}
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/notifications.py

"""
Sistema de notificaciones del módulo de gamificación.
"""

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import Mission, Reward, Level
from bot.gamification.config import GamificationConfig

logger = logging.getLogger(__name__)


NOTIFICATION_TEMPLATES = {
    'level_up': (
        "🎉 <b>¡Subiste de nivel!</b>\n\n"
        "{old_level} → <b>{new_level}</b>\n\n"
        "Mínimo de besitos: {min_besitos}"
    ),
    
    'mission_completed': (
        "✅ <b>Misión Completada</b>\n\n"
        "<b>{mission_name}</b>\n"
        "Recompensa: {besitos} besitos\n\n"
        "Usa /profile para reclamarla"
    ),
    
    'reward_unlocked': (
        "🎁 <b>Nueva Recompensa Disponible</b>\n\n"
        "<b>{reward_name}</b>\n"
        "{description}\n\n"
        "Visita /profile para verla"
    ),
    
    'streak_milestone': (
        "🔥 <b>¡Racha Épica!</b>\n\n"
        "Has reaccionado {days} días consecutivos\n\n"
        "¡Sigue así!"
    ),
    
    'streak_lost': (
        "💔 <b>Racha Perdida</b>\n\n"
        "Tu racha de {days} días expiró\n\n"
        "Reacciona hoy para empezar una nueva"
    )
}


class NotificationService:
    """Servicio de notificaciones."""
    
    def __init__(self, bot: Bot, session: AsyncSession):
        self.bot = bot
        self.session = session
    
    async def _send_notification(self, user_id: int, message: str):
        """Envía notificación si está habilitado."""
        config = await self.session.get(GamificationConfig, 1)
        if not config or not config.notifications_enabled:
            return
        
        try:
            await self.bot.send_message(user_id, message, parse_mode="HTML")
            logger.info(f"Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")
    
    async def notify_level_up(self, user_id: int, old_level: Level, new_level: Level):
        """Notifica level-up."""
        message = NOTIFICATION_TEMPLATES['level_up'].format(
            old_level=old_level.name,
            new_level=new_level.name,
            min_besitos=new_level.min_besitos
        )
        await self._send_notification(user_id, message)
    
    async def notify_mission_completed(self, user_id: int, mission: Mission):
        """Notifica misión completada."""
        message = NOTIFICATION_TEMPLATES['mission_completed'].format(
            mission_name=mission.name,
            besitos=mission.besitos_reward
        )
        await self._send_notification(user_id, message)
    
    async def notify_reward_unlocked(self, user_id: int, reward: Reward):
        """Notifica recompensa desbloqueada."""
        message = NOTIFICATION_TEMPLATES['reward_unlocked'].format(
            reward_name=reward.name,
            description=reward.description
        )
        await self._send_notification(user_id, message)
    
    async def notify_streak_milestone(self, user_id: int, days: int):
        """Notifica milestone de racha."""
        # Solo notificar en milestones específicos
        milestones = [7, 14, 30, 60, 100]
        if days not in milestones:
            return
        
        message = NOTIFICATION_TEMPLATES['streak_milestone'].format(days=days)
        await self._send_notification(user_id, message)
    
    async def notify_streak_lost(self, user_id: int, days: int):
        """Notifica racha perdida."""
        # Solo notificar si racha era significativa
        if days < 7:
            return
        
        message = NOTIFICATION_TEMPLATES['streak_lost'].format(days=days)
        await self._send_notification(user_id, message)
```

---

## INTEGRACIÓN

```python
# En reaction_hook.py
if changed:
    await gamification.notifications.notify_level_up(user_id, old_level, new_level)

# En auto_progression_checker.py
await notify_service.notify_level_up(user_id, old_level, new_level)

# En mission_service.py (al completar)
await gamification.notifications.notify_mission_completed(user_id, mission)
```

---

## VALIDACIÓN

- ✅ Configuración por tipo de notificación
- ✅ Templates formateados
- ✅ Milestones inteligentes (no spam)
- ✅ Manejo de errores
- ✅ Logging de envíos

---
---

# PROMPT G7.1: Tests End-to-End

---

## ROL

Ingeniero de Software Senior especializado en testing, QA y pytest.

---

## TAREA

Implementa tests end-to-end en `tests/gamification/test_integration.py` que validan flujos completos del sistema.

---

## CONTEXTO

### Objetivo

Validar que todos los componentes funcionan juntos correctamente, desde reacciones hasta level-ups y recompensas.

---

## TESTS REQUERIDOS

### 1. Test de Flujo Completo

```python
@pytest.mark.asyncio
async def test_complete_gamification_flow(session, sample_user):
    """
    Flujo: Usuario reacciona → gana besitos → sube nivel → completa misión → obtiene recompensa
    """
```

### 2. Test de Racha

```python
@pytest.mark.asyncio
async def test_streak_progression(session, sample_user):
    """
    Simula 7 días de reacciones consecutivas.
    Verifica: current_streak incrementa, longest_streak se actualiza
    """
```

### 3. Test de Misión Diaria

```python
@pytest.mark.asyncio
async def test_daily_mission_completion(session, sample_user, daily_mission):
    """
    Usuario reacciona 5 veces en un día → misión se completa
    """
```

### 4. Test de Unlock Condition

```python
@pytest.mark.asyncio
async def test_reward_unlock_by_level(session, sample_user):
    """
    Recompensa bloqueada por nivel → usuario sube nivel → se desbloquea
    """
```

### 5. Test de Orchestrator

```python
@pytest.mark.asyncio
async def test_configuration_orchestrator(session):
    """
    Aplica configuración completa → verifica que todo se creó correctamente
    """
```

---

## FORMATO DE SALIDA

```python
# tests/gamification/test_integration.py

"""
Tests de integración end-to-end del módulo de gamificación.
"""

import pytest
from datetime import datetime, timedelta, UTC

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.models import (
    UserGamification, UserStreak, Mission, Level, Reward
)
from bot.gamification.database.enums import MissionType, MissionStatus, RewardType


@pytest.mark.asyncio
async def test_complete_gamification_flow(session):
    """Test flujo completo: reacción → besitos → level-up → misión → recompensa."""
    container = GamificationContainer(session)
    
    # Setup: crear usuario
    user_id = 12345
    await container.user_gamification.initialize_new_user(user_id)
    
    # Setup: crear nivel
    level_2 = await container.level.create_level(
        name="Nivel 2",
        min_besitos=100,
        order=2
    )
    
    # Setup: crear misión
    mission = await container.mission.create_mission(
        name="Test Mission",
        description="Test",
        mission_type=MissionType.DAILY,
        criteria={"type": "daily", "count": 1},
        besitos_reward=50
    )
    
    # Setup: crear recompensa
    reward = await container.reward.create_reward(
        name="Test Reward",
        description="Test",
        reward_type=RewardType.BADGE,
        metadata={"icon": "🏆", "rarity": "common"},
        unlock_conditions={"type": "level", "level_id": level_2.id}
    )
    
    # 1. Usuario reacciona
    success, msg, besitos = await container.reaction.record_reaction(
        user_id=user_id,
        emoji="❤️",
        message_id=1,
        channel_id=-1001234,
        reacted_at=datetime.now(UTC)
    )
    assert success
    assert besitos > 0
    
    # 2. Verificar besitos
    user = await session.get(UserGamification, user_id)
    assert user.total_besitos > 0
    
    # 3. Dar más besitos para level-up
    await container.besito.grant_besitos(user_id, 100, "test", "test")
    
    # 4. Verificar level-up
    changed, old, new = await container.level.check_and_apply_level_up(user_id)
    assert changed
    assert new.id == level_2.id
    
    # 5. Verificar recompensa desbloqueada
    can_unlock, reason = await container.reward.check_unlock_conditions(user_id, reward.id)
    assert can_unlock
    
    # 6. Iniciar y completar misión
    user_mission = await container.mission.start_mission(user_id, mission.id)
    assert user_mission.status == MissionStatus.IN_PROGRESS
    
    # Simular completar
    user_mission.status = MissionStatus.COMPLETED
    await session.commit()
    
    # 7. Reclamar recompensa
    success, msg, info = await container.mission.claim_reward(user_id, mission.id)
    assert success


@pytest.mark.asyncio
async def test_streak_progression(session):
    """Test progresión de racha."""
    container = GamificationContainer(session)
    user_id = 12345
    
    await container.user_gamification.initialize_new_user(user_id)
    
    # Simular 7 días de reacciones
    for day in range(7):
        date = datetime.now(UTC) - timedelta(days=6-day)
        
        await container.reaction.record_reaction(
            user_id=user_id,
            emoji="🔥",
            message_id=100+day,
            channel_id=-1001234,
            reacted_at=date
        )
    
    # Verificar racha
    streak = await session.get(UserStreak, user_id)
    assert streak.current_streak == 7
    assert streak.longest_streak == 7


@pytest.mark.asyncio
async def test_daily_mission_completion(session):
    """Test completar misión diaria."""
    container = GamificationContainer(session)
    user_id = 12345
    
    await container.user_gamification.initialize_new_user(user_id)
    
    # Crear misión diaria (5 reacciones)
    mission = await container.mission.create_mission(
        name="Reactor Diario",
        description="5 reacciones",
        mission_type=MissionType.DAILY,
        criteria={"type": "daily", "count": 5},
        besitos_reward=200
    )
    
    # Iniciar
    user_mission = await container.mission.start_mission(user_id, mission.id)
    
    # Reaccionar 5 veces
    for i in range(5):
        await container.reaction.record_reaction(
            user_id=user_id,
            emoji="❤️",
            message_id=200+i,
            channel_id=-1001234,
            reacted_at=datetime.now(UTC)
        )
        
        # Actualizar progreso
        await container.mission.on_user_reaction(
            user_id=user_id,
            emoji="❤️",
            reacted_at=datetime.now(UTC)
        )
    
    # Verificar completada
    await session.refresh(user_mission)
    assert user_mission.status == MissionStatus.COMPLETED


@pytest.mark.asyncio
async def test_configuration_orchestrator(session):
    """Test orchestrator crea configuración completa."""
    container = GamificationContainer(session)
    
    config = {
        'mission': {
            'name': "Test Complete",
            'description': "Test",
            'mission_type': MissionType.ONE_TIME,
            'criteria': {"type": "one_time"},
            'besitos_reward': 100
        },
        'auto_level': {
            'name': "Test Level",
            'min_besitos': 1000,
            'order': 10
        },
        'rewards': [
            {
                'name': "Test Badge",
                'description': "Test",
                'reward_type': RewardType.BADGE,
                'metadata': {"icon": "🎯", "rarity": "common"}
            }
        ]
    }
    
    result = await container.configuration_orchestrator.create_complete_mission_system(
        config=config,
        created_by=1
    )
    
    assert result['mission'] is not None
    assert result['created_level'] is not None
    assert len(result['created_rewards']) == 1
    assert len(result['validation_errors']) == 0


@pytest.mark.asyncio
async def test_atomic_rollback_on_error(session):
    """Test que errores hacen rollback completo."""
    container = GamificationContainer(session)
    
    # Intentar crear con datos inválidos
    with pytest.raises(Exception):
        await container.mission.create_mission(
            name="Test",
            description="Test",
            mission_type=MissionType.DAILY,
            criteria={"type": "daily", "count": -5},  # Invalid
            besitos_reward=100
        )
    
    # Verificar que no se creó nada
    stmt = select(Mission).where(Mission.name == "Test")
    result = await session.execute(stmt)
    assert result.scalar_one_or_none() is None
```

---

## VALIDACIÓN

- ✅ Flujo completo funciona
- ✅ Rachas se calculan correctamente
- ✅ Misiones se completan según criterios
- ✅ Unlock conditions funcionan
- ✅ Orchestrator crea todo atómicamente
- ✅ Rollback en errores

---
---

# PROMPT G7.2: Documentación

---

## ROL

Ingeniero de Software Senior especializado en documentación técnica y onboarding.

---

## TAREA

Crea documentación completa del módulo en `docs/gamification/` con README, guías de uso y arquitectura.

---

## DOCUMENTOS REQUERIDOS

### 1. README.md - Overview

```markdown
# Módulo de Gamificación

Sistema completo de gamificación para bots de Telegram.

## Features

- ✅ Sistema de besitos (moneda virtual)
- ✅ Niveles y progresión automática
- ✅ Misiones (diarias, semanales, rachas)
- ✅ Recompensas con unlock conditions
- ✅ Badges coleccionables
- ✅ Leaderboards
- ✅ Wizards de configuración
- ✅ Plantillas predefinidas
- ✅ Background jobs automáticos

## Quick Start

1. Aplicar migración
2. Aplicar plantilla inicial
3. Configurar reacciones
4. ¡Listo!
```

### 2. ARCHITECTURE.md - Diseño Técnico

```markdown
# Arquitectura del Módulo

## Capas

1. **Database Layer**: 13 modelos SQLAlchemy
2. **Services Layer**: 7 servicios + Container DI
3. **Orchestrators Layer**: 3 orchestrators para workflows complejos
4. **Handlers Layer**: Admin + User handlers
5. **Background Jobs**: Auto-progression + Streak expiration

## Flujo de Datos

Usuario reacciona → ReactionHook → ReactionService → BesitoService → LevelService → MissionService
```

### 3. SETUP.md - Guía de Instalación

```markdown
# Setup del Módulo

## 1. Migraciones

```bash
alembic upgrade head
```

## 2. Seed Data

```python
# Aplicar plantilla inicial
/gamification → Templates → Starter Pack
```

## 3. Configuración

```env
GAMIFICATION_ENABLED=true
AUTO_PROGRESSION_INTERVAL_HOURS=6
STREAK_RESET_HOURS=24
NOTIFICATIONS_ENABLED=true
```
```

### 4. API.md - Referencia de Servicios

```markdown
# API Reference

## ReactionService

### `record_reaction(user_id, emoji, message_id, channel_id, reacted_at)`

Registra reacción de usuario.

**Validaciones:**
- Anti-spam (no duplicar en mismo mensaje)
- Límite diario
- Emoji válido

**Efectos:**
- Otorga besitos
- Actualiza racha
- Actualiza progreso de misiones
```

### 5. ADMIN_GUIDE.md - Guía para Admins

```markdown
# Guía de Administración

## Crear Misión con Wizard

1. `/gamification`
2. Misiones → Wizard
3. Seguir pasos:
   - Tipo
   - Criterios
   - Recompensa
   - Auto level (opcional)
   - Recompensas unlock (opcional)
4. Confirmar

## Aplicar Plantilla

Menú → Misiones → Plantillas → Seleccionar

Plantillas disponibles:
- **Starter Pack**: Sistema inicial
- **Engagement**: Misiones diarias/semanales
- **Progression**: 6 niveles completos
```

---

## FORMATO DE SALIDA

```
docs/gamification/
├── README.md              # Overview general
├── ARCHITECTURE.md        # Diseño técnico
├── SETUP.md              # Instalación
├── API.md                # Referencia servicios
└── ADMIN_GUIDE.md        # Guía para admins
```

Cada archivo debe tener:
- ✅ Tabla de contenidos
- ✅ Ejemplos de código
- ✅ Diagramas (mermaid cuando aplique)
- ✅ Screenshots/ejemplos de UI
- ✅ FAQ común

---

## VALIDACIÓN

- ✅ 5 documentos completos
- ✅ Quick start funcional
- ✅ Referencias de API claras
- ✅ Guías paso a paso

---

**FIN DE PROMPTS DEL MÓDULO DE GAMIFICACIÓN**

Total: 28 prompts generados
