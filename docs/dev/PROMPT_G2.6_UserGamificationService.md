# PROMPT G2.6: UserGamificationService - Perfil de Usuario

---

## ROL

Actúa como Ingeniero de Software Senior especializado en gestión de perfiles de usuario, agregación de datos y APIs unificadas.

---

## TAREA

Implementa el servicio `UserGamificationService` en `bot/gamification/services/user_gamification.py` que actúa como fachada unificada para obtener el perfil completo de gamificación de un usuario, agregando datos de múltiples servicios.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/services/
├── user_gamification.py   # ← ESTE ARCHIVO (fachada)
├── besito.py
├── level.py
├── mission.py
├── reward.py
├── reaction.py
└── container.py
```

### Propósito

Este servicio NO gestiona datos directamente. Es una **fachada** que:
1. Coordina llamadas a otros servicios
2. Agrega información de múltiples fuentes
3. Provee una API simple para handlers/UI

---

## RESPONSABILIDADES

### 1. Perfil Completo del Usuario

```python
async def get_user_profile(user_id: int) -> dict
"""
Retorna perfil completo de gamificación.

Agrega datos de:
- UserGamification (besitos, nivel)
- UserStreak (racha actual/récord)
- Misiones (activas, completadas, disponibles)
- Recompensas (obtenidas, disponibles)
- Badges (displayed)

Returns:
    {
        'user_id': int,
        'besitos': {
            'total': int,
            'earned': int,
            'spent': int
        },
        'level': {
            'current': Level,
            'next': Optional[Level],
            'progress_percentage': float,
            'besitos_to_next': Optional[int]
        },
        'streak': {
            'current': int,
            'longest': int,
            'last_reaction_date': datetime
        },
        'missions': {
            'in_progress': List[UserMission],
            'completed': List[UserMission],
            'available_count': int
        },
        'rewards': {
            'total_obtained': int,
            'badges': List[Badge],
            'displayed_badges': List[Badge]
        },
        'stats': {
            'total_reactions': int,
            'favorite_emoji': str,
            'days_active': int
        }
    }
"""
```

### 2. Inicialización de Usuario

```python
async def ensure_user_exists(user_id: int) -> UserGamification
"""
Crea UserGamification si no existe.

Defaults:
- total_besitos = 0
- current_level_id = nivel inicial (order=1)

Returns:
    UserGamification
"""

async def initialize_new_user(
    user_id: int,
    username: Optional[str] = None
) -> dict
"""
Inicializa usuario nuevo con:
- UserGamification
- UserStreak
- Misión de bienvenida (si existe)

Returns:
    Perfil completo del usuario
"""
```

### 3. Resumen para UI

```python
async def get_profile_summary(user_id: int) -> str
"""
Genera resumen formateado para Telegram.

Ejemplo:
    👤 Perfil de Usuario
    
    💰 Besitos: 1,250
    ⭐ Nivel: Fanático (75% al siguiente)
    🔥 Racha: 15 días (récord: 20)
    
    📋 Misiones: 3 activas, 12 completadas
    🏆 Recompensas: 8 obtenidas
    
    Badges mostrados:
    🏆 Primer Paso
    🔥 Racha de Fuego
    ⭐ Nivel 5
"""

async def get_leaderboard_position(user_id: int) -> dict
"""
Posición del usuario en leaderboards.

Returns:
    {
        'besitos_rank': int,
        'level_rank': int,
        'streak_rank': int,
        'total_users': int
    }
"""
```

### 4. Estadísticas Agregadas

```python
async def get_user_stats(user_id: int) -> dict
"""
Estadísticas detalladas.

Returns:
    {
        'reactions': {
            'total': int,
            'by_emoji': {'❤️': 50, '🔥': 30},
            'by_channel': {-1001234: 40},
            'avg_per_day': float
        },
        'besitos': {
            'total_earned': int,
            'total_spent': int,
            'from_reactions': int,
            'from_missions': int
        },
        'missions': {
            'total_completed': int,
            'completion_rate': float,
            'favorite_type': str
        },
        'activity': {
            'first_seen': datetime,
            'last_active': datetime,
            'days_since_start': int,
            'active_days': int
        }
    }
"""
```

---

## INTEGRACIÓN CON OTROS SERVICIOS

```python
class UserGamificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Acceso a otros servicios via container
        from bot.gamification.services.container import gamification_container
        self.container = gamification_container
    
    async def get_user_profile(self, user_id: int) -> dict:
        # Obtener datos de múltiples servicios
        user_gamif = await self.ensure_user_exists(user_id)
        
        # Nivel y progresión
        level_progress = await self.container.level.get_user_level_progress(user_id)
        
        # Racha
        streak = await self.container.reaction.get_user_streak(user_id)
        
        # Misiones
        active_missions = await self.container.mission.get_user_missions(
            user_id, 
            status=MissionStatus.IN_PROGRESS
        )
        completed_missions = await self.container.mission.get_user_missions(
            user_id,
            status=MissionStatus.CLAIMED
        )
        available_missions = await self.container.mission.get_available_missions(user_id)
        
        # Recompensas
        user_rewards = await self.container.reward.get_user_rewards(user_id)
        user_badges = await self.container.reward.get_user_badges(user_id)
        displayed_badges = [b for b, ub in user_badges if ub.displayed]
        
        # Estadísticas de reacciones
        reaction_stats = await self.container.reaction.get_reaction_stats(user_id)
        
        # Agregar todo
        return {
            'user_id': user_id,
            'besitos': {
                'total': user_gamif.total_besitos,
                'earned': user_gamif.besitos_earned,
                'spent': user_gamif.besitos_spent
            },
            'level': level_progress,
            'streak': {
                'current': streak.current_streak if streak else 0,
                'longest': streak.longest_streak if streak else 0,
                'last_reaction_date': streak.last_reaction_date if streak else None
            },
            'missions': {
                'in_progress': active_missions,
                'completed': completed_missions,
                'available_count': len(available_missions)
            },
            'rewards': {
                'total_obtained': len(user_rewards),
                'badges': [b for b, _ in user_badges],
                'displayed_badges': displayed_badges
            },
            'stats': reaction_stats
        }
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/user_gamification.py

"""
Servicio de perfil de usuario (fachada).

Responsabilidades:
- Agregar datos de múltiples servicios
- Proveer API unificada para UI
- Inicialización de usuarios nuevos
- Resúmenes formateados
"""

from typing import Optional
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import UserGamification, Level
from bot.gamification.database.enums import MissionStatus

logger = logging.getLogger(__name__)


class UserGamificationService:
    """Servicio de perfil de usuario (fachada)."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ========================================
    # INICIALIZACIÓN
    # ========================================
    
    async def ensure_user_exists(self, user_id: int) -> UserGamification:
        """Crea UserGamification si no existe."""
        user = await self.session.get(UserGamification, user_id)
        
        if not user:
            # Obtener nivel inicial (order=1)
            stmt = select(Level).where(Level.active == True).order_by(Level.order.asc()).limit(1)
            result = await self.session.execute(stmt)
            initial_level = result.scalar_one_or_none()
            
            user = UserGamification(
                user_id=user_id,
                total_besitos=0,
                besitos_earned=0,
                besitos_spent=0,
                current_level_id=initial_level.id if initial_level else None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            
            logger.info(f"Created UserGamification for user {user_id}")
        
        return user
    
    async def initialize_new_user(
        self,
        user_id: int,
        username: Optional[str] = None
    ) -> dict:
        """Inicializa usuario nuevo completamente."""
        # Crear perfil base
        user_gamif = await self.ensure_user_exists(user_id)
        
        # Crear racha
        from bot.gamification.database.models import UserStreak
        streak = UserStreak(user_id=user_id)
        self.session.add(streak)
        await self.session.commit()
        
        logger.info(f"Initialized new user {user_id}")
        
        # Retornar perfil completo
        return await self.get_user_profile(user_id)
    
    # ========================================
    # PERFIL COMPLETO
    # ========================================
    
    async def get_user_profile(self, user_id: int) -> dict:
        """Retorna perfil completo."""
        # Implementar lógica descrita arriba
        pass
    
    # ========================================
    # RESÚMENES
    # ========================================
    
    async def get_profile_summary(self, user_id: int) -> str:
        """Genera resumen formateado."""
        profile = await self.get_user_profile(user_id)
        
        # Formatear
        level_name = profile['level']['current'].name if profile['level']['current'] else 'Sin nivel'
        progress = profile['level']['progress_percentage']
        
        summary = f"""👤 <b>Perfil de Usuario</b>

💰 Besitos: <b>{profile['besitos']['total']:,}</b>
⭐ Nivel: <b>{level_name}</b> ({progress:.0f}% al siguiente)
🔥 Racha: <b>{profile['streak']['current']}</b> días (récord: {profile['streak']['longest']})

📋 Misiones: {len(profile['missions']['in_progress'])} activas, {len(profile['missions']['completed'])} completadas
🏆 Recompensas: {profile['rewards']['total_obtained']} obtenidas
"""
        
        # Badges mostrados
        if profile['rewards']['displayed_badges']:
            summary += "\n<b>Badges mostrados:</b>\n"
            for badge in profile['rewards']['displayed_badges']:
                summary += f"{badge.icon} {badge.name}\n"
        
        return summary
    
    async def get_leaderboard_position(self, user_id: int) -> dict:
        """Posición en leaderboards."""
        # Contar usuarios con más besitos
        user = await self.session.get(UserGamification, user_id)
        if not user:
            return {}
        
        stmt = select(func.count()).select_from(UserGamification).where(
            UserGamification.total_besitos > user.total_besitos
        )
        result = await self.session.execute(stmt)
        besitos_rank = result.scalar() + 1
        
        # Total de usuarios
        stmt = select(func.count()).select_from(UserGamification)
        result = await self.session.execute(stmt)
        total_users = result.scalar()
        
        return {
            'besitos_rank': besitos_rank,
            'total_users': total_users
        }
    
    # ========================================
    # ESTADÍSTICAS
    # ========================================
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Estadísticas detalladas."""
        # Implementar agregación de stats
        pass
```

---

## INTEGRACIÓN

```python
# bot/gamification/services/container.py

@property
def user_gamification(self) -> UserGamificationService:
    if self._user_gamification_service is None:
        self._user_gamification_service = UserGamificationService(self._session)
    return self._user_gamification_service
```

### Uso en handlers

```python
# bot/gamification/handlers/user/profile.py

@user_router.message(Command("profile"))
async def show_profile(message: Message, session: AsyncSession):
    from bot.gamification.services.container import gamification_container
    
    summary = await gamification_container.user_gamification.get_profile_summary(
        message.from_user.id
    )
    
    await message.answer(summary, parse_mode="HTML")
```

---

## VALIDACIÓN

- ✅ Fachada que coordina otros servicios
- ✅ Inicialización de usuarios nuevos
- ✅ Perfil completo agregado
- ✅ Resúmenes formateados para Telegram
- ✅ Estadísticas agregadas
- ✅ Type hints completos

---

**ENTREGABLE:** Archivo `user_gamification.py` completo con API unificada de perfil.
