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
        reward_metadata: Optional[dict] = None,
        created_by: int = 0
    ) -> Reward:
        """Crea nueva recompensa.

        Args:
            name: Nombre de la recompensa
            description: Descripción
            reward_type: Tipo de recompensa
            cost_besitos: Costo en besitos (opcional)
            unlock_conditions: Condiciones de desbloqueo (opcional)
            reward_metadata: Metadata específica del tipo (opcional)
            created_by: ID del admin que creó la recompensa

        Returns:
            Reward creada
        """
        reward = Reward(
            name=name,
            description=description,
            reward_type=reward_type.value,
            cost_besitos=cost_besitos,
            unlock_conditions=json.dumps(unlock_conditions) if unlock_conditions else None,
            reward_metadata=json.dumps(reward_metadata) if reward_metadata else None,
            active=True,
            created_by=created_by
        )
        self.session.add(reward)
        await self.session.commit()
        await self.session.refresh(reward)

        logger.info(f"Created reward: {name} (type: {reward_type.value})")
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
        """Crea reward + badge en una transacción.

        Args:
            name: Nombre del badge
            description: Descripción
            icon: Icono del badge (emoji)
            rarity: Rareza del badge
            cost_besitos: Costo en besitos (opcional)
            unlock_conditions: Condiciones de desbloqueo (opcional)
            created_by: ID del admin que creó el badge

        Returns:
            (Reward, Badge) creados
        """
        # Crear reward base
        metadata = {"icon": icon, "rarity": rarity.value}
        reward = await self.create_reward(
            name=name,
            description=description,
            reward_type=RewardType.BADGE,
            cost_besitos=cost_besitos,
            unlock_conditions=unlock_conditions,
            reward_metadata=metadata,
            created_by=created_by
        )

        # Crear badge
        badge = Badge(
            id=reward.id,
            icon=icon,
            rarity=rarity.value
        )
        self.session.add(badge)
        await self.session.commit()
        await self.session.refresh(badge)

        logger.info(f"Created badge: {name} ({rarity.value})")
        return reward, badge

    async def update_reward(
        self,
        reward_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cost_besitos: Optional[int] = None,
        active: Optional[bool] = None
    ) -> Reward:
        """Actualiza recompensa existente.

        Args:
            reward_id: ID de la recompensa
            name: Nuevo nombre (opcional)
            description: Nueva descripción (opcional)
            cost_besitos: Nuevo costo (opcional)
            active: Nuevo estado activo (opcional)

        Returns:
            Reward actualizada

        Raises:
            ValueError: Si recompensa no existe
        """
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            raise ValueError(f"Reward {reward_id} not found")

        if name is not None:
            reward.name = name
        if description is not None:
            reward.description = description
        if cost_besitos is not None:
            reward.cost_besitos = cost_besitos
        if active is not None:
            reward.active = active

        await self.session.commit()
        await self.session.refresh(reward)

        logger.info(f"Updated reward {reward_id}: {reward.name}")
        return reward

    async def delete_reward(self, reward_id: int) -> bool:
        """Soft-delete de recompensa (active=False).

        Args:
            reward_id: ID de la recompensa

        Returns:
            True si se eliminó correctamente
        """
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            return False

        reward.active = False
        await self.session.commit()

        logger.info(f"Deleted reward {reward_id}: {reward.name}")
        return True

    async def get_all_rewards(
        self,
        active_only: bool = True,
        reward_type: Optional[RewardType] = None
    ) -> List[Reward]:
        """Obtiene recompensas con filtros opcionales.

        Args:
            active_only: Si True, solo retorna recompensas activas
            reward_type: Filtrar por tipo de recompensa (opcional)

        Returns:
            Lista de Reward
        """
        stmt = select(Reward)
        if active_only:
            stmt = stmt.where(Reward.active == True)
        if reward_type:
            stmt = stmt.where(Reward.reward_type == reward_type.value)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_reward_by_id(self, reward_id: int) -> Optional[Reward]:
        """Obtiene recompensa por ID.

        Args:
            reward_id: ID de la recompensa

        Returns:
            Reward o None si no existe
        """
        return await self.session.get(Reward, reward_id)

    # ========================================
    # UNLOCK CONDITIONS
    # ========================================

    async def check_unlock_conditions(
        self,
        user_id: int,
        reward_id: int
    ) -> Tuple[bool, str]:
        """Verifica si usuario puede desbloquear recompensa.

        Args:
            user_id: ID del usuario
            reward_id: ID de la recompensa

        Returns:
            (can_unlock, reason)
        """
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
        """Valida condición individual.

        Args:
            user_id: ID del usuario
            condition: Dict con condición a validar

        Returns:
            True si la condición se cumple
        """
        condition_type = condition.get('type')

        if condition_type == 'mission':
            # Verificar que misión está claimed
            mission_id = condition['mission_id']
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission_id,
                UserMission.status == MissionStatus.CLAIMED.value
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

        # Condiciones narrativas
        elif condition_type == 'narrative_chapter':
            # Verificar que usuario completó el capítulo
            from bot.narrative.services.container import NarrativeContainer
            narrative = NarrativeContainer(self.session)
            chapter_slug = condition['chapter_slug']
            completed = await narrative.progress.has_completed_chapter(user_id, chapter_slug)
            return completed

        elif condition_type == 'narrative_fragment':
            # Verificar que usuario visitó el fragmento
            from bot.narrative.services.container import NarrativeContainer
            narrative = NarrativeContainer(self.session)
            fragment_key = condition['fragment_key']
            visited = await narrative.progress.has_visited_fragment(user_id, fragment_key)
            return visited

        elif condition_type == 'narrative_decision':
            # Verificar que usuario tomó la decisión específica
            from bot.narrative.services.container import NarrativeContainer
            narrative = NarrativeContainer(self.session)
            decision_key = condition['decision_key']
            taken = await narrative.progress.has_taken_decision(user_id, decision_key)
            return taken

        elif condition_type == 'archetype':
            # Verificar que usuario tiene el arquetipo requerido
            from bot.narrative.services.container import NarrativeContainer
            narrative = NarrativeContainer(self.session)
            progress = await narrative.progress.get_or_create_progress(user_id)
            required_archetype = condition['archetype']
            return progress.detected_archetype.value == required_archetype

        return False

    def _get_unlock_requirement_text(self, conditions: dict) -> str:
        """Genera texto descriptivo de requisitos.

        Args:
            conditions: Dict con condiciones

        Returns:
            Texto descriptivo
        """
        condition_type = conditions.get('type')

        if condition_type == 'mission':
            return f"Requiere completar misión ID {conditions['mission_id']}"
        elif condition_type == 'level':
            return f"Requiere nivel ID {conditions['level_id']}"
        elif condition_type == 'besitos':
            return f"Requiere {conditions['min_besitos']} besitos totales"
        elif condition_type == 'multiple':
            return "Requiere múltiples condiciones"
        elif condition_type == 'narrative_chapter':
            return f"Requiere completar el capítulo '{conditions['chapter_slug']}'"
        elif condition_type == 'narrative_fragment':
            return f"Requiere avanzar en la historia hasta '{conditions['fragment_key']}'"
        elif condition_type == 'narrative_decision':
            return f"Requiere tomar la decisión '{conditions['decision_key']}'"
        elif condition_type == 'archetype':
            return f"Requiere tener arquetipo '{conditions['archetype']}'"

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
        """Otorga recompensa a usuario.

        Args:
            user_id: ID del usuario
            reward_id: ID de la recompensa
            obtained_via: Método de obtención
            reference_id: ID de referencia (opcional)

        Returns:
            (success, message, user_reward)
        """
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
            obtained_via=obtained_via.value,
            reference_id=reference_id
        )
        self.session.add(user_reward)
        await self.session.commit()
        await self.session.refresh(user_reward)

        # Eager load la relación reward para evitar lazy loading issues
        from sqlalchemy.orm import selectinload
        stmt = select(UserReward).where(UserReward.id == user_reward.id).options(
            selectinload(UserReward.reward)
        )
        result = await self.session.execute(stmt)
        user_reward = result.scalar_one()

        # Si es badge, crear UserBadge (solo si no existe)
        if reward.reward_type == RewardType.BADGE.value:
            existing_badge = await self.session.get(UserBadge, user_reward.id)
            if not existing_badge:
                user_badge = UserBadge(
                    id=user_reward.id,
                    displayed=False
                )
                self.session.add(user_badge)
                await self.session.commit()
            else:
                logger.debug(f"UserBadge {user_reward.id} already exists, skipping creation")

        # Si es BESITOS, otorgar besitos extra
        if reward.reward_type == RewardType.BESITOS.value:
            metadata = json.loads(reward.reward_metadata) if reward.reward_metadata else {}
            amount = metadata.get('amount', 0)
            if amount > 0:
                from bot.gamification.services.besito import BesitoService
                besito_service = BesitoService(self.session)

                await besito_service.grant_besitos(
                    user_id=user_id,
                    amount=amount,
                    transaction_type=TransactionType.ADMIN_GRANT,
                    description=f"Recompensa: {reward.name}",
                    reference_id=user_reward.id
                )

        logger.info(f"User {user_id} obtained reward {reward.name} via {obtained_via.value}")
        return True, f"Recompensa obtenida: {reward.name}", user_reward

    async def purchase_reward(
        self,
        user_id: int,
        reward_id: int
    ) -> Tuple[bool, str, Optional[UserReward]]:
        """Compra recompensa con besitos.

        Args:
            user_id: ID del usuario
            reward_id: ID de la recompensa

        Returns:
            (success, message, user_reward)
        """
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            return False, "Reward not found", None

        if reward.cost_besitos is None:
            return False, "Reward cannot be purchased", None

        # Validar unlock conditions ANTES de gastar besitos
        can_unlock, reason = await self.check_unlock_conditions(user_id, reward_id)
        if not can_unlock:
            return False, reason, None

        # Validar besitos suficientes
        user_gamif = await self.session.get(UserGamification, user_id)
        if not user_gamif or user_gamif.total_besitos < reward.cost_besitos:
            return False, f"Insufficient besitos (need {reward.cost_besitos})", None

        # Gastar besitos
        from bot.gamification.services.besito import BesitoService
        besito_service = BesitoService(self.session)

        success, message, _ = await besito_service.deduct_besitos(
            user_id=user_id,
            amount=reward.cost_besitos,
            transaction_type=TransactionType.PURCHASE,
            description=f"Compra: {reward.name}"
        )

        if not success:
            return False, message, None

        # Crear UserReward directamente (ya validamos condiciones)
        user_reward = UserReward(
            user_id=user_id,
            reward_id=reward_id,
            obtained_at=datetime.now(UTC),
            obtained_via=ObtainedVia.PURCHASE.value,
            reference_id=None
        )
        self.session.add(user_reward)
        await self.session.commit()
        await self.session.refresh(user_reward)

        # Eager load la relación reward para evitar lazy loading issues
        from sqlalchemy.orm import selectinload
        stmt = select(UserReward).where(UserReward.id == user_reward.id).options(
            selectinload(UserReward.reward)
        )
        result = await self.session.execute(stmt)
        user_reward = result.scalar_one()

        # Si es badge, crear UserBadge (solo si no existe)
        if reward.reward_type == RewardType.BADGE.value:
            existing_badge = await self.session.get(UserBadge, user_reward.id)
            if not existing_badge:
                user_badge = UserBadge(
                    id=user_reward.id,
                    displayed=False
                )
                self.session.add(user_badge)
                await self.session.commit()
            else:
                logger.debug(f"UserBadge {user_reward.id} already exists, skipping creation")

        # Si es BESITOS, otorgar besitos extra
        if reward.reward_type == RewardType.BESITOS.value:
            metadata = json.loads(reward.reward_metadata) if reward.reward_metadata else {}
            amount = metadata.get('amount', 0)
            if amount > 0:
                await besito_service.grant_besitos(
                    user_id=user_id,
                    amount=amount,
                    transaction_type=TransactionType.ADMIN_GRANT,
                    description=f"Recompensa: {reward.name}",
                    reference_id=user_reward.id
                )

        logger.info(f"User {user_id} purchased reward {reward.name}")
        return True, f"Recompensa comprada: {reward.name}", user_reward

    # ========================================
    # CONSULTAS
    # ========================================

    async def get_user_rewards(
        self,
        user_id: int,
        reward_type: Optional[RewardType] = None
    ) -> List[UserReward]:
        """Obtiene recompensas de usuario.

        Args:
            user_id: ID del usuario
            reward_type: Filtrar por tipo (opcional)

        Returns:
            Lista de UserReward
        """
        from sqlalchemy.orm import selectinload

        stmt = select(UserReward).where(UserReward.user_id == user_id).options(
            selectinload(UserReward.reward)  # Eager load la relación reward
        )
        if reward_type:
            stmt = stmt.join(Reward).where(Reward.reward_type == reward_type.value)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_reward(self, user_id: int, reward_id: int) -> bool:
        """Verifica si usuario tiene recompensa.

        Args:
            user_id: ID del usuario
            reward_id: ID de la recompensa

        Returns:
            True si el usuario tiene la recompensa
        """
        stmt = select(func.count()).select_from(UserReward).where(
            UserReward.user_id == user_id,
            UserReward.reward_id == reward_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def get_available_rewards(self, user_id: int) -> List[Reward]:
        """Obtiene recompensas disponibles para usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de Reward disponibles
        """
        all_rewards = await self.get_all_rewards()
        available = []

        for reward in all_rewards:
            can_unlock, _ = await self.check_unlock_conditions(user_id, reward.id)
            if can_unlock:
                available.append(reward)

        return available

    async def get_locked_rewards(self, user_id: int) -> List[Tuple[Reward, str]]:
        """Obtiene recompensas bloqueadas con razón.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de (Reward, reason)
        """
        all_rewards = await self.get_all_rewards()
        locked = []

        for reward in all_rewards:
            can_unlock, reason = await self.check_unlock_conditions(user_id, reward.id)
            if not can_unlock and reason != "Already obtained":
                locked.append((reward, reason))

        return locked

    # ========================================
    # BADGES
    # ========================================

    async def get_user_badges(self, user_id: int) -> List[Tuple[Badge, UserBadge]]:
        """Obtiene badges de usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de (Badge, UserBadge)
        """
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
        """Configura badges mostrados en perfil.

        Args:
            user_id: ID del usuario
            badge_ids: Lista de IDs de badges a mostrar (máx 3)

        Returns:
            True si se configuró correctamente
        """
        if len(badge_ids) > self.MAX_DISPLAYED_BADGES:
            return False

        # Desmarcar todos los badges del usuario
        stmt = (
            select(UserBadge)
            .join(UserReward)
            .where(UserReward.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        user_badges = list(result.scalars().all())

        # Marcar los seleccionados
        for ub in user_badges:
            ub.displayed = ub.id in badge_ids

        await self.session.commit()

        logger.info(f"User {user_id} set displayed badges: {badge_ids}")
        return True

    # ========================================
    # AUTOMATIC REWARDS
    # ========================================

    async def check_and_grant_unlocked_rewards(
        self,
        user_id: int
    ) -> List[Tuple["Reward", str]]:
        """Verifica y otorga automáticamente recompensas desbloqueadas.

        Busca TODAS las recompensas con condición tipo 'besitos' que el usuario
        cumple, y las otorga automáticamente si aún no las tiene.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de (Reward, message) de recompensas otorgadas
            Ej: [(Reward(...), "Recompensa otorgada"), ...]
        """
        granted_rewards = []

        # Obtener todas las recompensas con condición de besitos
        all_rewards = await self.get_all_rewards(active_only=True)

        for reward in all_rewards:
            # Si no tiene condiciones, saltar
            if not reward.unlock_conditions:
                continue

            try:
                conditions = json.loads(reward.unlock_conditions)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    f"Invalid unlock_conditions JSON for reward {reward.id}: "
                    f"{reward.unlock_conditions}"
                )
                continue

            # Solo procesar recompensas con condición tipo 'besitos'
            if conditions.get('type') != 'besitos':
                continue

            # Verificar si usuario cumple la condición
            can_unlock, _ = await self.check_unlock_conditions(user_id, reward.id)

            if can_unlock:
                # Otorgar recompensa automáticamente
                success, message, user_reward = await self.grant_reward(
                    user_id=user_id,
                    reward_id=reward.id,
                    obtained_via=ObtainedVia.AUTO_UNLOCK,
                    reference_id=None
                )

                if success:
                    granted_rewards.append((reward, message))
                    logger.info(
                        f"Automatically granted reward '{reward.name}' "
                        f"to user {user_id}"
                    )
                else:
                    logger.debug(
                        f"Could not grant reward '{reward.name}' "
                        f"to user {user_id}: {message}"
                    )

        return granted_rewards

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_users_with_reward(self, reward_id: int) -> int:
        """Obtiene la cantidad de usuarios que tienen una recompensa.

        Args:
            reward_id: ID de la recompensa

        Returns:
            Número de usuarios que tienen la recompensa
        """
        stmt = select(func.count(UserReward.id)).where(
            UserReward.reward_id == reward_id
        )
        result = await self.session.execute(stmt)
        count = result.scalar_one()

        return count
