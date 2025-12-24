# PROMPT G6.2: Sistema de Estadísticas

---

## ROL

Ingeniero de Software Senior especializado en analytics, dashboards y métricas de sistemas.

---

## TAREA

Implementa el sistema de estadísticas en `bot/gamification/services/stats.py` y handlers para visualización de métricas del sistema.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/services/
├── stats.py              # ← Servicio de estadísticas
└── container.py

bot/gamification/handlers/admin/
└── stats.py              # ← Handler visualización
```

---

## RESPONSABILIDADES DEL SERVICIO

### 1. Estadísticas Generales del Sistema

```python
async def get_system_overview() -> dict:
    """
    Métricas generales.
    
    Returns:
        {
            'total_users': int,
            'active_users_7d': int,
            'total_besitos_distributed': int,
            'total_missions': int,
            'total_rewards': int,
            'missions_completed': int,
            'rewards_claimed': int
        }
    """
```

### 2. Estadísticas de Usuarios

```python
async def get_user_distribution() -> dict:
    """
    Distribución por nivel.
    
    Returns:
        {
            'by_level': {'Novato': 150, 'Regular': 75, ...},
            'top_users': List[{user_id, besitos, level_name}],
            'avg_besitos': float
        }
    """
```

### 3. Estadísticas de Misiones

```python
async def get_mission_stats() -> dict:
    """
    Métricas de misiones.
    
    Returns:
        {
            'total_starts': int,
            'total_completions': int,
            'completion_rate': float,
            'by_type': {'daily': 45, 'streak': 30, ...},
            'top_missions': List[{mission_name, completions}]
        }
    """
```

### 4. Estadísticas de Engagement

```python
async def get_engagement_stats() -> dict:
    """
    Métricas de engagement.
    
    Returns:
        {
            'total_reactions': int,
            'reactions_7d': int,
            'avg_reactions_per_user': float,
            'top_emojis': {'❤️': 500, '🔥': 300, ...},
            'active_streaks': int,
            'longest_streak': int
        }
    """
```

### 5. Evolución Temporal

```python
async def get_timeline_stats(days: int = 30) -> dict:
    """
    Estadísticas por día.
    
    Returns:
        {
            'daily_reactions': [{date, count}, ...],
            'daily_completions': [{date, count}, ...],
            'daily_besitos': [{date, total}, ...]
        }
    """
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/stats.py

"""
Servicio de estadísticas y métricas del sistema de gamificación.
"""

from datetime import datetime, timedelta, UTC
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from bot.gamification.database.models import (
    UserGamification, UserMission, UserReward, UserReaction,
    UserStreak, Mission, Level
)
from bot.gamification.database.enums import MissionStatus

import logging
logger = logging.getLogger(__name__)


class StatsService:
    """Servicio de estadísticas del sistema."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_system_overview(self) -> dict:
        """Métricas generales del sistema."""
        # Total usuarios
        stmt = select(func.count()).select_from(UserGamification)
        total_users = (await self.session.execute(stmt)).scalar()
        
        # Usuarios activos últimos 7 días
        week_ago = datetime.now(UTC) - timedelta(days=7)
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.reacted_at >= week_ago
        ).distinct(UserReaction.user_id)
        active_7d = (await self.session.execute(stmt)).scalar()
        
        # Total besitos distribuidos
        stmt = select(func.sum(UserGamification.besitos_earned))
        total_besitos = (await self.session.execute(stmt)).scalar() or 0
        
        # Misiones y recompensas
        stmt = select(func.count()).select_from(Mission).where(Mission.active == True)
        total_missions = (await self.session.execute(stmt)).scalar()
        
        stmt = select(func.count()).select_from(UserMission).where(
            UserMission.status == MissionStatus.CLAIMED
        )
        missions_completed = (await self.session.execute(stmt)).scalar()
        
        stmt = select(func.count()).select_from(UserReward)
        rewards_claimed = (await self.session.execute(stmt)).scalar()
        
        return {
            'total_users': total_users,
            'active_users_7d': active_7d,
            'total_besitos_distributed': total_besitos,
            'total_missions': total_missions,
            'missions_completed': missions_completed,
            'rewards_claimed': rewards_claimed
        }
    
    async def get_user_distribution(self) -> dict:
        """Distribución de usuarios por nivel."""
        # Por nivel
        stmt = (
            select(Level.name, func.count(UserGamification.user_id))
            .join(UserGamification, UserGamification.current_level_id == Level.id)
            .group_by(Level.name)
        )
        result = await self.session.execute(stmt)
        by_level = {name: count for name, count in result}
        
        # Top 10
        stmt = (
            select(UserGamification, Level.name)
            .join(Level, UserGamification.current_level_id == Level.id)
            .order_by(UserGamification.total_besitos.desc())
            .limit(10)
        )
        result = await self.session.execute(stmt)
        top_users = [
            {
                'user_id': ug.user_id,
                'besitos': ug.total_besitos,
                'level_name': level_name
            }
            for ug, level_name in result
        ]
        
        # Promedio
        stmt = select(func.avg(UserGamification.total_besitos))
        avg_besitos = (await self.session.execute(stmt)).scalar() or 0
        
        return {
            'by_level': by_level,
            'top_users': top_users,
            'avg_besitos': round(avg_besitos, 2)
        }
    
    async def get_mission_stats(self) -> dict:
        """Estadísticas de misiones."""
        # Total starts
        stmt = select(func.count()).select_from(UserMission)
        total_starts = (await self.session.execute(stmt)).scalar()
        
        # Completions
        stmt = select(func.count()).select_from(UserMission).where(
            UserMission.status.in_([MissionStatus.COMPLETED, MissionStatus.CLAIMED])
        )
        total_completions = (await self.session.execute(stmt)).scalar()
        
        # Rate
        completion_rate = (total_completions / total_starts * 100) if total_starts > 0 else 0
        
        # Por tipo
        stmt = (
            select(Mission.mission_type, func.count(UserMission.id))
            .join(UserMission)
            .where(UserMission.status == MissionStatus.CLAIMED)
            .group_by(Mission.mission_type)
        )
        result = await self.session.execute(stmt)
        by_type = {mtype: count for mtype, count in result}
        
        # Top misiones
        stmt = (
            select(Mission.name, func.count(UserMission.id))
            .join(UserMission)
            .where(UserMission.status == MissionStatus.CLAIMED)
            .group_by(Mission.id, Mission.name)
            .order_by(func.count(UserMission.id).desc())
            .limit(5)
        )
        result = await self.session.execute(stmt)
        top_missions = [
            {'mission_name': name, 'completions': count}
            for name, count in result
        ]
        
        return {
            'total_starts': total_starts,
            'total_completions': total_completions,
            'completion_rate': round(completion_rate, 2),
            'by_type': by_type,
            'top_missions': top_missions
        }
    
    async def get_engagement_stats(self) -> dict:
        """Estadísticas de engagement."""
        # Total reacciones
        stmt = select(func.count()).select_from(UserReaction)
        total_reactions = (await self.session.execute(stmt)).scalar()
        
        # Últimos 7 días
        week_ago = datetime.now(UTC) - timedelta(days=7)
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.reacted_at >= week_ago
        )
        reactions_7d = (await self.session.execute(stmt)).scalar()
        
        # Promedio por usuario
        stmt = select(func.count(UserGamification.user_id))
        total_users = (await self.session.execute(stmt)).scalar()
        avg_reactions = (total_reactions / total_users) if total_users > 0 else 0
        
        # Top emojis
        stmt = (
            select(UserReaction.emoji, func.count(UserReaction.id))
            .group_by(UserReaction.emoji)
            .order_by(func.count(UserReaction.id).desc())
            .limit(5)
        )
        result = await self.session.execute(stmt)
        top_emojis = {emoji: count for emoji, count in result}
        
        # Rachas activas
        stmt = select(func.count()).select_from(UserStreak).where(
            UserStreak.current_streak > 0
        )
        active_streaks = (await self.session.execute(stmt)).scalar()
        
        # Racha más larga
        stmt = select(func.max(UserStreak.longest_streak))
        longest_streak = (await self.session.execute(stmt)).scalar() or 0
        
        return {
            'total_reactions': total_reactions,
            'reactions_7d': reactions_7d,
            'avg_reactions_per_user': round(avg_reactions, 2),
            'top_emojis': top_emojis,
            'active_streaks': active_streaks,
            'longest_streak': longest_streak
        }
```

---

## HANDLER

```python
# bot/gamification/handlers/admin/stats.py

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.filters.admin import IsAdmin
from bot.gamification.services.container import GamificationContainer

router = Router()
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "gamif:admin:stats")
async def show_stats(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra estadísticas del sistema."""
    
    overview = await gamification.stats.get_system_overview()
    user_dist = await gamification.stats.get_user_distribution()
    mission_stats = await gamification.stats.get_mission_stats()
    engagement = await gamification.stats.get_engagement_stats()
    
    text = f"""📊 <b>Estadísticas del Sistema</b>

<b>👥 Usuarios</b>
• Total: {overview['total_users']:,}
• Activos (7d): {overview['active_users_7d']:,}
• Besitos promedio: {user_dist['avg_besitos']:,.0f}

<b>📋 Misiones</b>
• Configuradas: {overview['total_missions']}
• Completadas: {overview['missions_completed']:,}
• Tasa completitud: {mission_stats['completion_rate']:.1f}%

<b>🎁 Recompensas</b>
• Obtenidas: {overview['rewards_claimed']:,}

<b>📈 Engagement</b>
• Reacciones totales: {engagement['total_reactions']:,}
• Reacciones (7d): {engagement['reactions_7d']:,}
• Rachas activas: {engagement['active_streaks']}
• Racha más larga: {engagement['longest_streak']} días

<b>💰 Economía</b>
• Besitos distribuidos: {overview['total_besitos_distributed']:,}
"""
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()
```

---

## INTEGRACIÓN

```python
# bot/gamification/services/container.py

@property
def stats(self) -> StatsService:
    if self._stats_service is None:
        self._stats_service = StatsService(self._session)
    return self._stats_service
```

---

## VALIDACIÓN

- ✅ 5 métodos de estadísticas
- ✅ Queries optimizadas con agregaciones
- ✅ Handler formateado para Telegram
- ✅ Métricas clave: usuarios, misiones, engagement, economía

---

**ENTREGABLES:** 
- `stats.py` (servicio)
- `stats.py` (handler)
