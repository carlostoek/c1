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
            reward_metadata=json.dumps(metadata) if metadata else None,
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
    
    async def update_reward(self, reward_id: int, **kwargs) -> Optional[Reward]:
        """Actualiza una recompensa existente."""
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            return None
        
        # Permitir actualizar todos los campos válidos
        update_fields = [
            'name', 'description', 'reward_type', 'cost_besitos',
            'unlock_conditions', 'reward_metadata', 'active'
        ]
        
        for key, value in kwargs.items():
            if key in update_fields:
                if key in ['unlock_conditions', 'reward_metadata'] and value is not None:
                    # Convertir a JSON si es necesario
                    setattr(reward, key, json.dumps(value) if isinstance(value, dict) else json.dumps(value))
                else:
                    setattr(reward, key, value)
        
        await self.session.commit()
        await self.session.refresh(reward)
        
        logger.info(f"Updated reward {reward_id}: {reward.name}")
        return reward
    
    async def delete_reward(self, reward_id: int) -> bool:
        """Soft-delete (active=False) de una recompensa."""
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            return False
        
        reward.active = False
        await self.session.commit()
        
        logger.info(f"Soft-deleted reward {reward_id}: {reward.name}")
        return True
    
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
    
    async def get_reward_by_id(self, reward_id: int) -> Optional[Reward]:
        """Obtiene una recompensa por ID."""
        stmt = select(Reward).where(Reward.id == reward_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
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
            if not user_gamif:
                return False
            return user_gamif.total_besitos >= min_besitos
        
        elif condition_type == 'multiple':
            # Todas las condiciones deben cumplirse (AND)
            conditions = condition['conditions']
            for cond in conditions:
                if not await self._validate_single_condition(user_id, cond):
                    return False
            return True
        
        return False
    
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
        if not reward:
            return False, "Reward not found", None
        
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
            metadata = json.loads(reward.reward_metadata) if reward.reward_metadata else {}
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
        
        # Validar unlock conditions
        can_unlock, reason = await self.check_unlock_conditions(user_id, reward_id)
        if not can_unlock:
            return False, reason, None
        
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
    
    async def get_locked_rewards(self, user_id: int) -> List[tuple]:
        """Recompensas bloqueadas con razón."""
        all_rewards = await self.get_all_rewards()
        locked = []
        
        for reward in all_rewards:
            can_unlock, reason = await self.check_unlock_conditions(user_id, reward.id)
            if not can_unlock:
                locked.append((reward, reason))
        
        return locked
    
    # ========================================
    # BADGES
    # ========================================
    
    async def get_user_badges(self, user_id: int) -> List[tuple]:
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
        
        # Desmarcar todos los badges del usuario
        stmt = (
            select(UserBadge)
            .join(UserReward)
            .where(UserReward.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        all_user_badges = result.scalars().all()
        
        for user_badge in all_user_badges:
            user_badge.displayed = user_badge.id in badge_ids
        
        await self.session.commit()
        return True