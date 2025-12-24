# PROMPT G2.4: MissionService - Gestión de Misiones

---

## ROL

Actúa como Ingeniero de Software Senior especializado en sistemas de misiones, criterios dinámicos y tracking de progreso en gamificación.

---

## TAREA

Implementa el servicio `MissionService` en `bot/gamification/services/mission.py` que gestiona misiones configuradas por admins, tracking de progreso de usuarios, validación de criterios y otorgamiento de recompensas.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/services/
├── mission.py         # ← ESTE ARCHIVO
├── besito.py          # Para otorgar recompensas
├── level.py           # Para auto level-up
└── container.py
```

### Modelos Relevantes
```python
class Mission(Base):
    id: Mapped[int]
    name: Mapped[str]
    description: Mapped[str]
    mission_type: Mapped[str]          # MissionType enum
    criteria: Mapped[str]              # JSON con criterios
    besitos_reward: Mapped[int]
    auto_level_up_id: Mapped[int]      # Nivel que otorga (nullable)
    unlock_rewards: Mapped[str]        # JSON array de reward_ids (nullable)
    active: Mapped[bool]
    repeatable: Mapped[bool]
    created_by: Mapped[int]

class UserMission(Base):
    id: Mapped[int]
    user_id: Mapped[int]
    mission_id: Mapped[int]
    progress: Mapped[str]              # JSON con progreso actual
    status: Mapped[str]                # MissionStatus enum
    started_at: Mapped[datetime]
    completed_at: Mapped[datetime]     # nullable
    claimed_at: Mapped[datetime]       # nullable
```

### Enums
```python
class MissionType(str, Enum):
    ONE_TIME = "one_time"    # Completar una vez
    DAILY = "daily"          # Diaria (resetea cada día)
    WEEKLY = "weekly"        # Semanal
    STREAK = "streak"        # Racha de días consecutivos

class MissionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"     # Completada, no reclamada
    CLAIMED = "claimed"         # Recompensa reclamada
    EXPIRED = "expired"
```

---

## RESTRICCIONES TÉCNICAS

### Criterios Dinámicos (JSON)

```python
# Ejemplos de criterios por tipo:

# STREAK
{
    "type": "streak",
    "days": 7,
    "require_consecutive": true
}

# DAILY
{
    "type": "daily",
    "count": 5,                    # 5 reacciones
    "specific_reaction": "❤️"      # Emoji específico o null
}

# WEEKLY
{
    "type": "weekly",
    "target": 50,                  # 50 reacciones en semana
    "specific_days": [1, 3, 5]     # Lunes, miércoles, viernes (0=domingo)
}

# ONE_TIME
{
    "type": "one_time"
    # Sin criterios adicionales
}
```

### Progreso (JSON)

```python
# Ejemplos de progreso por tipo:

# STREAK
{
    "days_completed": 3,
    "last_reaction_date": "2024-12-20"
}

# DAILY
{
    "reactions_today": 3,
    "date": "2024-12-20"
}

# WEEKLY
{
    "reactions_this_week": 25,
    "week_start": "2024-12-18"
}
```

---

## RESPONSABILIDADES DEL SERVICIO

### 1. CRUD de Misiones (Admin)

```python
async def create_mission(
    name: str,
    description: str,
    mission_type: MissionType,
    criteria: dict,
    besitos_reward: int,
    auto_level_up_id: Optional[int] = None,
    unlock_rewards: Optional[List[int]] = None,
    repeatable: bool = False,
    created_by: int = 0
) -> Mission

async def update_mission(mission_id: int, **kwargs) -> Mission

async def delete_mission(mission_id: int) -> bool
"""Soft-delete (active=False)"""

async def get_all_missions(active_only: bool = True) -> List[Mission]

async def get_mission_by_id(mission_id: int) -> Optional[Mission]
```

### 2. Gestión de UserMission

```python
async def start_mission(user_id: int, mission_id: int) -> UserMission
"""
Inicia misión para usuario.

Validaciones:
- Misión existe y está activa
- Usuario no tiene misión activa si no es repeatable
- Crea UserMission con status=IN_PROGRESS
"""

async def get_user_missions(
    user_id: int,
    status: Optional[MissionStatus] = None
) -> List[UserMission]

async def get_available_missions(user_id: int) -> List[Mission]
"""Misiones que usuario puede iniciar (no completadas o repeatables)"""
```

### 3. Tracking de Progreso

```python
async def update_progress(
    user_id: int,
    mission_id: int,
    new_data: dict
) -> UserMission
"""
Actualiza progreso de misión.

Ejemplo:
    await update_progress(
        user_id=123,
        mission_id=5,
        new_data={"days_completed": 4}
    )
"""

async def check_completion(
    user_id: int,
    mission_id: int
) -> tuple[bool, UserMission]
"""
Verifica si misión está completa según criterios.

Returns:
    (is_complete, user_mission)
    
Si está completa, actualiza status a COMPLETED
"""
```

### 4. Hook para Reacciones

```python
async def on_user_reaction(user_id: int, emoji: str, reacted_at: datetime):
    """
    Hook llamado cuando usuario reacciona.
    Actualiza progreso de todas las misiones activas del usuario.
    
    Flujo:
    1. Obtener misiones IN_PROGRESS del usuario
    2. Para cada misión:
       - Actualizar progreso según tipo
       - Verificar si se completó
       - Si se completó, marcar como COMPLETED
    """
```

### 5. Reclamar Recompensa

```python
async def claim_reward(
    user_id: int,
    mission_id: int
) -> tuple[bool, str, dict]
"""
Reclama recompensa de misión completada.

Validaciones:
- UserMission existe
- Status == COMPLETED
- No ha sido reclamada (claimed_at == None)

Acciones:
1. Otorgar besitos (via BesitoService)
2. Si tiene auto_level_up_id, aplicar nivel
3. Si tiene unlock_rewards, desbloquear recompensas
4. Actualizar status a CLAIMED
5. Actualizar claimed_at

Returns:
    (success, message, rewards_info)
    
    rewards_info = {
        'besitos': int,
        'level_up': Optional[Level],
        'unlocked_rewards': List[Reward]
    }
"""
```

---

## LÓGICA DE ACTUALIZACIÓN DE PROGRESO

### Misión STREAK

```python
async def _update_streak_progress(
    user_mission: UserMission,
    user_streak: UserStreak
) -> bool:
    """
    Actualiza progreso de misión tipo streak.
    
    Lógica:
    - Leer criteria.days (días requeridos)
    - Comparar con user_streak.current_streak
    - Si current_streak >= días requeridos → completada
    
    Returns:
        True si se completó
    """
    criteria = json.loads(user_mission.mission.criteria)
    required_days = criteria['days']
    
    progress = json.loads(user_mission.progress) if user_mission.progress else {}
    progress['days_completed'] = user_streak.current_streak
    progress['last_reaction_date'] = user_streak.last_reaction_date.isoformat()
    
    user_mission.progress = json.dumps(progress)
    
    if user_streak.current_streak >= required_days:
        user_mission.status = MissionStatus.COMPLETED
        user_mission.completed_at = datetime.now(UTC)
        return True
    
    return False
```

### Misión DAILY

```python
async def _update_daily_progress(
    user_mission: UserMission,
    emoji: str,
    reacted_at: datetime
) -> bool:
    """
    Actualiza progreso de misión diaria.
    
    Lógica:
    - Si es un nuevo día, resetear contador
    - Incrementar contador de reacciones
    - Validar specific_reaction si aplica
    - Comparar con criteria.count
    """
    criteria = json.loads(user_mission.mission.criteria)
    required_count = criteria['count']
    specific_reaction = criteria.get('specific_reaction')
    
    # Si requiere emoji específico y no coincide, ignorar
    if specific_reaction and emoji != specific_reaction:
        return False
    
    progress = json.loads(user_mission.progress) if user_mission.progress else {
        'reactions_today': 0,
        'date': None
    }
    
    today = reacted_at.date().isoformat()
    
    # Si cambió el día, resetear
    if progress.get('date') != today:
        progress['reactions_today'] = 0
        progress['date'] = today
    
    progress['reactions_today'] += 1
    user_mission.progress = json.dumps(progress)
    
    if progress['reactions_today'] >= required_count:
        user_mission.status = MissionStatus.COMPLETED
        user_mission.completed_at = datetime.now(UTC)
        return True
    
    return False
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/mission.py

"""
Servicio de gestión de misiones.

Responsabilidades:
- CRUD de misiones
- Tracking de progreso por usuario
- Validación de criterios dinámicos
- Otorgamiento de recompensas
"""

from typing import Optional, List, Tuple
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from bot.gamification.database.models import Mission, UserMission, UserStreak
from bot.gamification.database.enums import MissionType, MissionStatus, TransactionType

logger = logging.getLogger(__name__)


class MissionService:
    """Servicio de gestión de misiones y progreso."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ========================================
    # CRUD MISIONES
    # ========================================
    
    async def create_mission(
        self,
        name: str,
        description: str,
        mission_type: MissionType,
        criteria: dict,
        besitos_reward: int,
        auto_level_up_id: Optional[int] = None,
        unlock_rewards: Optional[List[int]] = None,
        repeatable: bool = False,
        created_by: int = 0
    ) -> Mission:
        """Crea nueva misión."""
        mission = Mission(
            name=name,
            description=description,
            mission_type=mission_type,
            criteria=json.dumps(criteria),
            besitos_reward=besitos_reward,
            auto_level_up_id=auto_level_up_id,
            unlock_rewards=json.dumps(unlock_rewards) if unlock_rewards else None,
            active=True,
            repeatable=repeatable,
            created_by=created_by
        )
        self.session.add(mission)
        await self.session.commit()
        await self.session.refresh(mission)
        
        logger.info(f"Created mission: {name} (type: {mission_type})")
        return mission
    
    async def get_all_missions(self, active_only: bool = True) -> List[Mission]:
        """Obtiene todas las misiones."""
        stmt = select(Mission)
        if active_only:
            stmt = stmt.where(Mission.active == True)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    # ========================================
    # USER MISSIONS
    # ========================================
    
    async def start_mission(self, user_id: int, mission_id: int) -> UserMission:
        """Inicia misión para usuario."""
        mission = await self.session.get(Mission, mission_id)
        if not mission or not mission.active:
            raise ValueError("Mission not found or inactive")
        
        # Verificar si ya tiene esta misión activa (si no es repeatable)
        if not mission.repeatable:
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission_id,
                UserMission.status.in_([MissionStatus.IN_PROGRESS, MissionStatus.COMPLETED])
            )
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("Mission already in progress or completed")
        
        user_mission = UserMission(
            user_id=user_id,
            mission_id=mission_id,
            status=MissionStatus.IN_PROGRESS,
            progress=json.dumps({}),
            started_at=datetime.now(UTC)
        )
        self.session.add(user_mission)
        await self.session.commit()
        await self.session.refresh(user_mission)
        
        logger.info(f"User {user_id} started mission {mission_id}")
        return user_mission
    
    async def get_user_missions(
        self,
        user_id: int,
        status: Optional[MissionStatus] = None
    ) -> List[UserMission]:
        """Obtiene misiones de usuario."""
        stmt = select(UserMission).where(UserMission.user_id == user_id)
        if status:
            stmt = stmt.where(UserMission.status == status)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    # ========================================
    # PROGRESO
    # ========================================
    
    async def on_user_reaction(
        self,
        user_id: int,
        emoji: str,
        reacted_at: datetime
    ):
        """Hook para actualizar progreso cuando usuario reacciona."""
        # Obtener misiones IN_PROGRESS
        active_missions = await self.get_user_missions(
            user_id, 
            status=MissionStatus.IN_PROGRESS
        )
        
        # Obtener racha del usuario (para misiones tipo STREAK)
        from bot.gamification.services.container import gamification_container
        user_streak = await gamification_container.reaction.get_user_streak(user_id)
        
        for user_mission in active_missions:
            mission = await self.session.get(Mission, user_mission.mission_id)
            
            # Actualizar según tipo
            if mission.mission_type == MissionType.STREAK:
                if user_streak:
                    await self._update_streak_progress(user_mission, user_streak)
            
            elif mission.mission_type == MissionType.DAILY:
                await self._update_daily_progress(user_mission, emoji, reacted_at)
            
            # ... otros tipos
        
        await self.session.commit()
    
    async def _update_streak_progress(
        self,
        user_mission: UserMission,
        user_streak: UserStreak
    ) -> bool:
        """Actualiza progreso de misión streak."""
        # Implementar lógica descrita arriba
        pass
    
    async def _update_daily_progress(
        self,
        user_mission: UserMission,
        emoji: str,
        reacted_at: datetime
    ) -> bool:
        """Actualiza progreso de misión daily."""
        # Implementar lógica descrita arriba
        pass
    
    # ========================================
    # RECLAMAR RECOMPENSA
    # ========================================
    
    async def claim_reward(
        self,
        user_id: int,
        mission_id: int
    ) -> Tuple[bool, str, dict]:
        """Reclama recompensa de misión completada."""
        # Obtener user_mission
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(stmt)
        user_mission = result.scalar_one_or_none()
        
        if not user_mission:
            return False, "Mission not found", {}
        
        if user_mission.status != MissionStatus.COMPLETED:
            return False, "Mission not completed", {}
        
        if user_mission.claimed_at:
            return False, "Reward already claimed", {}
        
        # Obtener misión
        mission = await self.session.get(Mission, mission_id)
        
        rewards_info = {
            'besitos': 0,
            'level_up': None,
            'unlocked_rewards': []
        }
        
        # 1. Otorgar besitos
        from bot.gamification.services.container import gamification_container
        besitos_granted = await gamification_container.besito.grant_besitos(
            user_id=user_id,
            amount=mission.besitos_reward,
            transaction_type=TransactionType.MISSION_REWARD,
            description=f"Misión completada: {mission.name}",
            reference_id=user_mission.id
        )
        rewards_info['besitos'] = besitos_granted
        
        # 2. Auto level-up
        if mission.auto_level_up_id:
            await gamification_container.level.set_user_level(
                user_id, 
                mission.auto_level_up_id
            )
            level = await self.session.get(Level, mission.auto_level_up_id)
            rewards_info['level_up'] = level
        
        # 3. Unlock rewards (si aplica)
        # TODO: Integrar con RewardService cuando exista
        
        # 4. Marcar como reclamada
        user_mission.status = MissionStatus.CLAIMED
        user_mission.claimed_at = datetime.now(UTC)
        await self.session.commit()
        
        logger.info(f"User {user_id} claimed mission {mission_id}: +{besitos_granted} besitos")
        
        return True, f"Recompensa reclamada: +{besitos_granted} besitos", rewards_info
```

---

## INTEGRACIÓN

### En ReactionService

```python
# bot/gamification/services/reaction.py

async def record_reaction(...):
    # ... código existente ...
    
    # Hook para misiones
    from bot.gamification.services.container import gamification_container
    await gamification_container.mission.on_user_reaction(
        user_id=user_id,
        emoji=emoji,
        reacted_at=datetime.now(UTC)
    )
```

### En Container

```python
# bot/gamification/services/container.py

@property
def mission(self) -> MissionService:
    if self._mission_service is None:
        self._mission_service = MissionService(self._session)
    return self._mission_service
```

---

## VALIDACIÓN

- ✅ CRUD de misiones con criterios dinámicos
- ✅ Tracking de progreso por tipo de misión
- ✅ Hook integrado con reacciones
- ✅ Sistema de reclamar recompensas
- ✅ Validaciones (no duplicar, solo completadas)
- ✅ Type hints y docstrings

---

**ENTREGABLE:** Archivo `mission.py` completo con gestión de misiones y progreso dinámico.
