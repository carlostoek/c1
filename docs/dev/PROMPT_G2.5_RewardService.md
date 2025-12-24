# PROMPT G2.5: RewardService - Gestión de Recompensas

---

## ROL

Actúa como Ingeniero de Software Senior especializado en sistemas de recompensas, desbloqueos condicionales y economías virtuales.

---

## TAREA

Implementa el servicio `RewardService` en `bot/gamification/services/reward.py` que gestiona recompensas configurables, condiciones de desbloqueo, compra con besitos, y tracking de recompensas obtenidas por usuarios.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/services/
├── reward.py          # ← ESTE ARCHIVO
├── besito.py          # Para compras
├── mission.py         # Para unlock conditions
└── container.py
```

### Modelos Relevantes
```python
class Reward(Base):
    id: Mapped[int]
    name: Mapped[str]
    description: Mapped[str]
    reward_type: Mapped[str]           # RewardType enum
    cost_besitos: Mapped[int]          # nullable - si se puede comprar
    unlock_conditions: Mapped[str]     # JSON con condiciones
    metadata: Mapped[str]              # JSON con datos específicos
    active: Mapped[bool]
    created_by: Mapped[int]

class UserReward(Base):
    id: Mapped[int]
    user_id: Mapped[int]
    reward_id: Mapped[int]
    obtained_at: Mapped[datetime]
    obtained_via: Mapped[str]          # ObtainedVia enum

class Badge(Base):
    id: Mapped[int]  # FK a rewards.id
    icon: Mapped[str]
    rarity: Mapped[str]                # BadgeRarity enum

class UserBadge(Base):
    id: Mapped[int]  # FK a user_rewards.id
    displayed: Mapped[bool]
```

### Enums
```python
class RewardType(str, Enum):
    BADGE = "badge"
    ITEM = "item"
    PERMISSION = "permission"
    TITLE = "title"
    BESITOS = "besitos"

class ObtainedVia(str, Enum):
    MISSION = "mission"
    PURCHASE = "purchase"
    ADMIN_GRANT = "admin_grant"
    EVENT = "event"
    LEVEL_UP = "level_up"

class BadgeRarity(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
```

---

## RESTRICCIONES TÉCNICAS

### Unlock Conditions (JSON)

```python
# Ejemplos de condiciones:

# Por misión
{
    "type": "mission",
    "mission_id": 5
}

# Por nivel
{
    "type": "level",
    "level_id": 3
}

# Por besitos totales
{
    "type": "besitos",
    "min_besitos": 5000
}

# Múltiples condiciones (AND)
{
    "type": "multiple",
    "conditions": [
        {"type": "mission", "mission_id": 5},
        {"type": "level", "level_id": 2}
    ]
}

# Sin condiciones (disponible para todos)
null
```

### Metadata por Tipo

```python
# BADGE
{
    "icon": "🏆",
    "rarity": "epic"
}

# PERMISSION
{
    "permission_key": "custom_emoji",
    "duration_days": 30  # null = permanente
}

# BESITOS (bonus extra)
{
    "amount": 500
}
```

---

## RESPONSABILIDADES DEL SERVICIO

### 1. CRUD de Recompensas

```python
async def create_reward(
    name: str,
    description: str,
    reward_type: RewardType,
    cost_besitos: Optional[int] = None,
    unlock_conditions: Optional[dict] = None,
    metadata: Optional[dict] = None,
    created_by: int = 0
) -> Reward

async def create_badge(
    name: str,
    description: str,
    icon: str,
    rarity: BadgeRarity,
    cost_besitos: Optional[int] = None,
    unlock_conditions: Optional[dict] = None,
    created_by: int = 0
) -> tuple[Reward, Badge]
"""Crea reward + badge en una transacción"""

async def update_reward(reward_id: int, **kwargs) -> Reward

async def delete_reward(reward_id: int) -> bool

async def get_all_rewards(
    active_only: bool = True,
    reward_type: Optional[RewardType] = None
) -> List[Reward]

async def get_reward_by_id(reward_id: int) -> Optional[Reward]
```

### 2. Validación de Desbloqueo

```python
async def check_unlock_conditions(
    user_id: int,
    reward_id: int
) -> tuple[bool, str]
"""
Verifica si usuario cumple condiciones para desbloquear recompensa.

Returns:
    (can_unlock, reason)
    
Valida:
- unlock_conditions del reward
- Si user ya tiene la recompensa
"""

async def _validate_single_condition(
    user_id: int,
    condition: dict
) -> bool
"""
Valida condición individual.

Tipos soportados:
- mission: UserMission con status=CLAIMED
- level: current_level_id >= level_id
- besitos: total_besitos >= min_besitos
"""
```

### 3. Obtención de Recompensas

```python
async def grant_reward(
    user_id: int,
    reward_id: int,
    obtained_via: ObtainedVia,
    reference_id: Optional[int] = None
) -> tuple[bool, str, UserReward]
"""
Otorga recompensa a usuario.

Validaciones:
- Reward existe y activo
- Usuario no tiene ya esta recompensa
- Cumple unlock_conditions (si las tiene)

Acciones:
1. Crear UserReward
2. Si es BADGE, crear UserBadge
3. Si es BESITOS, otorgar besitos extra
4. Log de la operación

Returns:
    (success, message, user_reward)
"""

async def purchase_reward(
    user_id: int,
    reward_id: int
) -> tuple[bool, str, Optional[UserReward]]
"""
Compra recompensa con besitos.

Validaciones:
- Reward tiene cost_besitos (se puede comprar)
- Usuario tiene besitos suficientes
- Cumple unlock_conditions
- No la tiene ya

Acciones:
1. Gastar besitos (BesitoService.spend_besitos)
2. Otorgar recompensa (grant_reward)

Returns:
    (success, message, user_reward)
"""
```

### 4. Consultas de Usuario

```python
async def get_user_rewards(
    user_id: int,
    reward_type: Optional[RewardType] = None
) -> List[UserReward]

async def get_available_rewards(user_id: int) -> List[Reward]
"""Recompensas que usuario puede obtener (unlock conditions cumplidas)"""

async def get_locked_rewards(user_id: int) -> List[tuple[Reward, str]]
"""
Recompensas bloqueadas con razón.

Returns:
    List[(reward, reason)]
    reason ejemplos: "Requiere nivel 5", "Requiere completar misión X"
"""

async def has_reward(user_id: int, reward_id: int) -> bool
```

### 5. Badges Específicos

```python
async def get_user_badges(user_id: int) -> List[tuple[Badge, UserBadge]]
"""Obtiene badges del usuario con info de displayed"""

async def set_displayed_badges(
    user_id: int,
    badge_ids: List[int]
) -> bool
"""
Configura badges mostrados en perfil.

Máximo 3 badges displayed simultáneos
"""
```

---

## LÓGICA DE VALIDACIÓN

### Validar Condiciones

```python
async def _validate_single_condition(
    self,
    user_id: int,
    condition: dict
) -> bool:
    """Valida condición individual."""
    condition_type = condition.get('type')
    
    if condition_type == 'mission':
        # Verificar que misión está claimed
        mission_id = condition['mission_id']
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id,
            UserMission.status == MissionStatus.CLAIMED
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    elif condition_type == 'level':
        # Verificar nivel actual
        level_id = condition['level_id']
        user_gamif = await self.session.get(UserGamification, user_id)
        if not user_gamif:
            return False
        
        # Usuario debe estar en este nivel o superior
        current_level = await self.session.get(Level, user_gamif.current_level_id)
        target_level = await self.session.get(Level, level_id)
        
        if not current_level or not target_level:
            return False
        
        return current_level.order >= target_level.order
    
    elif condition_type == 'besitos':
        # Verificar besitos totales
        min_besitos = condition['min_besitos']
        user_gamif = await self.session.get(UserGamification, user_id)
        return user_gamif.total_besitos >= min_besitos if user_gamif else False
    
    elif condition_type == 'multiple':
        # Todas las condiciones deben cumplirse (AND)
        conditions = condition['conditions']
        for cond in conditions:
            if not await self._validate_single_condition(user_id, cond):
                return False
        return True
    
    return False
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/reward.py

"""
Servicio de gestión de recompensas.

Responsabilidades:
- CRUD de recompensas (general y badges)
- Validación de unlock conditions
- Otorgamiento y compra de recompensas
- Tracking de recompensas de usuarios
"""

from typing import Optional, List, Tuple
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from bot.gamification.database.models import (
    Reward, UserReward, Badge, UserBadge,
    UserGamification, Level, UserMission
)
from bot.gamification.database.enums import (
    RewardType, ObtainedVia, BadgeRarity, 
    MissionStatus, TransactionType
)

logger = logging.getLogger(__name__)


class RewardService:
    """Servicio de gestión de recompensas."""
    
    MAX_DISPLAYED_BADGES = 3
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ========================================
    # CRUD RECOMPENSAS
    # ========================================
    
    async def create_reward(
        self,
        name: str,
        description: str,
        reward_type: RewardType,
        cost_besitos: Optional[int] = None,
        unlock_conditions: Optional[dict] = None,
        metadata: Optional[dict] = None,
        created_by: int = 0
    ) -> Reward:
        """Crea nueva recompensa."""
        reward = Reward(
            name=name,
            description=description,
            reward_type=reward_type,
            cost_besitos=cost_besitos,
            unlock_conditions=json.dumps(unlock_conditions) if unlock_conditions else None,
            metadata=json.dumps(metadata) if metadata else None,
            active=True,
            created_by=created_by
        )
        self.session.add(reward)
        await self.session.commit()
        await self.session.refresh(reward)
        
        logger.info(f"Created reward: {name} (type: {reward_type})")
        return reward
    
    async def create_badge(
        self,
        name: str,
        description: str,
        icon: str,
        rarity: BadgeRarity,
        cost_besitos: Optional[int] = None,
        unlock_conditions: Optional[dict] = None,
        created_by: int = 0
    ) -> Tuple[Reward, Badge]:
        """Crea reward + badge."""
        # Crear reward base
        metadata = {"icon": icon, "rarity": rarity}
        reward = await self.create_reward(
            name=name,
            description=description,
            reward_type=RewardType.BADGE,
            cost_besitos=cost_besitos,
            unlock_conditions=unlock_conditions,
            metadata=metadata,
            created_by=created_by
        )
        
        # Crear badge
        badge = Badge(
            id=reward.id,
            icon=icon,
            rarity=rarity
        )
        self.session.add(badge)
        await self.session.commit()
        await self.session.refresh(badge)
        
        logger.info(f"Created badge: {name} ({rarity})")
        return reward, badge
    
    async def get_all_rewards(
        self,
        active_only: bool = True,
        reward_type: Optional[RewardType] = None
    ) -> List[Reward]:
        """Obtiene recompensas."""
        stmt = select(Reward)
        if active_only:
            stmt = stmt.where(Reward.active == True)
        if reward_type:
            stmt = stmt.where(Reward.reward_type == reward_type)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    # ========================================
    # UNLOCK CONDITIONS
    # ========================================
    
    async def check_unlock_conditions(
        self,
        user_id: int,
        reward_id: int
    ) -> Tuple[bool, str]:
        """Verifica si usuario puede desbloquear recompensa."""
        reward = await self.session.get(Reward, reward_id)
        if not reward or not reward.active:
            return False, "Reward not found or inactive"
        
        # Verificar si ya tiene la recompensa
        if await self.has_reward(user_id, reward_id):
            return False, "Already obtained"
        
        # Sin condiciones = desbloqueada
        if not reward.unlock_conditions:
            return True, "Available"
        
        # Validar condiciones
        conditions = json.loads(reward.unlock_conditions)
        if await self._validate_single_condition(user_id, conditions):
            return True, "Available"
        
        return False, self._get_unlock_requirement_text(conditions)
    
    async def _validate_single_condition(
        self,
        user_id: int,
        condition: dict
    ) -> bool:
        """Valida condición individual."""
        # Implementar lógica descrita arriba
        pass
    
    def _get_unlock_requirement_text(self, conditions: dict) -> str:
        """Genera texto descriptivo de requisitos."""
        condition_type = conditions.get('type')
        
        if condition_type == 'mission':
            return f"Requiere completar misión ID {conditions['mission_id']}"
        elif condition_type == 'level':
            return f"Requiere nivel ID {conditions['level_id']}"
        elif condition_type == 'besitos':
            return f"Requiere {conditions['min_besitos']} besitos totales"
        elif condition_type == 'multiple':
            return "Requiere múltiples condiciones"
        
        return "Condiciones no especificadas"
    
    # ========================================
    # OTORGAR RECOMPENSAS
    # ========================================
    
    async def grant_reward(
        self,
        user_id: int,
        reward_id: int,
        obtained_via: ObtainedVia,
        reference_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[UserReward]]:
        """Otorga recompensa a usuario."""
        # Validar unlock conditions
        can_unlock, reason = await self.check_unlock_conditions(user_id, reward_id)
        if not can_unlock:
            return False, reason, None
        
        reward = await self.session.get(Reward, reward_id)
        
        # Crear UserReward
        user_reward = UserReward(
            user_id=user_id,
            reward_id=reward_id,
            obtained_at=datetime.now(UTC),
            obtained_via=obtained_via,
            reference_id=reference_id
        )
        self.session.add(user_reward)
        await self.session.commit()
        await self.session.refresh(user_reward)
        
        # Si es badge, crear UserBadge
        if reward.reward_type == RewardType.BADGE:
            user_badge = UserBadge(
                id=user_reward.id,
                displayed=False
            )
            self.session.add(user_badge)
            await self.session.commit()
        
        # Si es BESITOS, otorgar besitos extra
        if reward.reward_type == RewardType.BESITOS:
            metadata = json.loads(reward.metadata) if reward.metadata else {}
            amount = metadata.get('amount', 0)
            if amount > 0:
                from bot.gamification.services.container import gamification_container
                await gamification_container.besito.grant_besitos(
                    user_id=user_id,
                    amount=amount,
                    transaction_type=TransactionType.ADMIN_GRANT,
                    description=f"Recompensa: {reward.name}",
                    reference_id=user_reward.id
                )
        
        logger.info(f"User {user_id} obtained reward {reward.name} via {obtained_via}")
        return True, f"Recompensa obtenida: {reward.name}", user_reward
    
    async def purchase_reward(
        self,
        user_id: int,
        reward_id: int
    ) -> Tuple[bool, str, Optional[UserReward]]:
        """Compra recompensa con besitos."""
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            return False, "Reward not found", None
        
        if reward.cost_besitos is None:
            return False, "Reward cannot be purchased", None
        
        # Validar besitos suficientes
        user_gamif = await self.session.get(UserGamification, user_id)
        if not user_gamif or user_gamif.total_besitos < reward.cost_besitos:
            return False, f"Insufficient besitos (need {reward.cost_besitos})", None
        
        # Gastar besitos
        from bot.gamification.services.container import gamification_container
        try:
            await gamification_container.besito.spend_besitos(
                user_id=user_id,
                amount=reward.cost_besitos,
                transaction_type=TransactionType.PURCHASE,
                description=f"Compra: {reward.name}"
            )
        except Exception as e:
            return False, str(e), None
        
        # Otorgar recompensa
        success, message, user_reward = await self.grant_reward(
            user_id=user_id,
            reward_id=reward_id,
            obtained_via=ObtainedVia.PURCHASE
        )
        
        return success, message, user_reward
    
    # ========================================
    # CONSULTAS
    # ========================================
    
    async def get_user_rewards(
        self,
        user_id: int,
        reward_type: Optional[RewardType] = None
    ) -> List[UserReward]:
        """Obtiene recompensas de usuario."""
        stmt = select(UserReward).where(UserReward.user_id == user_id)
        if reward_type:
            stmt = stmt.join(Reward).where(Reward.reward_type == reward_type)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def has_reward(self, user_id: int, reward_id: int) -> bool:
        """Verifica si usuario tiene recompensa."""
        stmt = select(func.count()).select_from(UserReward).where(
            UserReward.user_id == user_id,
            UserReward.reward_id == reward_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0
    
    async def get_available_rewards(self, user_id: int) -> List[Reward]:
        """Recompensas disponibles para usuario."""
        all_rewards = await self.get_all_rewards()
        available = []
        
        for reward in all_rewards:
            can_unlock, _ = await self.check_unlock_conditions(user_id, reward.id)
            if can_unlock:
                available.append(reward)
        
        return available
    
    # ========================================
    # BADGES
    # ========================================
    
    async def get_user_badges(self, user_id: int) -> List[Tuple[Badge, UserBadge]]:
        """Obtiene badges de usuario."""
        stmt = (
            select(Badge, UserBadge)
            .join(UserReward, UserReward.id == UserBadge.id)
            .join(Reward, Reward.id == Badge.id)
            .where(UserReward.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.all())
    
    async def set_displayed_badges(
        self,
        user_id: int,
        badge_ids: List[int]
    ) -> bool:
        """Configura badges mostrados (máx 3)."""
        if len(badge_ids) > self.MAX_DISPLAYED_BADGES:
            return False
        
        # Desmarcar todos
        stmt = (
            select(UserBadge)
            .join(UserReward)
            .where(UserReward.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        user_badges = result.scalars().all()
        
        for ub in user_badges:
            ub.displayed = ub.id in badge_ids
        
        await self.session.commit()
        return True
```

---

## INTEGRACIÓN

```python
# bot/gamification/services/container.py

@property
def reward(self) -> RewardService:
    if self._reward_service is None:
        self._reward_service = RewardService(self._session)
    return self._reward_service
```

---

## VALIDACIÓN

- ✅ CRUD recompensas y badges
- ✅ Validación de unlock conditions
- ✅ Compra con besitos
- ✅ Otorgamiento automático de besitos extra
- ✅ Sistema de badges displayed
- ✅ Type hints y docstrings

---

**ENTREGABLE:** Archivo `reward.py` completo con gestión de recompensas y unlock conditions.
