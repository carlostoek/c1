"""
ConfigurationService - Servicio de configuración unificada de gamificación.

Maneja CRUD para:
- ActionConfig (puntos por acción)
- LevelConfig (niveles/rangos)
- BadgeConfig (insignias)
- RewardConfig (recompensas)
- MissionConfig (misiones)
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import (
    ActionConfig,
    LevelConfig,
    BadgeConfig,
    RewardConfig,
    MissionConfig,
)
from .exceptions import (
    ConfigNotFoundError,
    ConfigAlreadyExistsError,
    ConfigValidationError,
    ConfigInUseError,
)
from .cache import get_config_cache, ConfigCache

logger = logging.getLogger(__name__)


class ConfigurationService:
    """
    Servicio de configuración unificada de gamificación.
    
    Proporciona CRUD completo para todas las entidades de configuración,
    con validaciones de negocio y soporte para transacciones atómicas.
    
    Attributes:
        session: Sesión async de SQLAlchemy
    
    Example:
        >>> container = ServiceContainer(session, bot)
        >>> config_service = container.configuration
        >>> 
        >>> # Listar acciones
        >>> actions = await config_service.list_actions()
        >>> 
        >>> # Crear acción
        >>> action = await config_service.create_action(
        ...     action_key="custom_action",
        ...     display_name="Acción Custom",
        ...     points_amount=15
        ... )
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self.session = session
        self._cache = get_config_cache()
        logger.debug("✅ ConfigurationService inicializado")
    
    # ═══════════════════════════════════════════════════════════════
    # ACTION CONFIG CRUD
    # ═══════════════════════════════════════════════════════════════
    
    async def list_actions(self, include_inactive: bool = False) -> List[ActionConfig]:
        """
        Lista todas las acciones configuradas.

        Args:
            include_inactive: Si True, incluye acciones desactivadas

        Returns:
            Lista de ActionConfig ordenadas por action_key
        """
        cache_key = f"actions:{'all' if include_inactive else 'active'}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📋 Listadas {len(cached)} acciones (from cache)")
            return cached

        # Query a BD
        query = select(ActionConfig)
        if not include_inactive:
            query = query.where(ActionConfig.is_active == True)
        query = query.order_by(ActionConfig.action_key)

        result = await self.session.execute(query)
        actions = list(result.scalars().all())

        # Guardar en cache
        self._cache.set(cache_key, actions)

        logger.debug(f"📋 Listadas {len(actions)} acciones (from DB)")
        return actions
    
    async def get_action(self, action_key: str) -> ActionConfig:
        """
        Obtiene una acción por su key.

        Args:
            action_key: Identificador único de la acción

        Returns:
            ActionConfig encontrado

        Raises:
            ConfigNotFoundError: Si la acción no existe
        """
        cache_key = f"action:{action_key}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self.session.execute(
            select(ActionConfig).where(ActionConfig.action_key == action_key)
        )
        action = result.scalar_one_or_none()

        if not action:
            raise ConfigNotFoundError("ActionConfig", action_key)

        # Guardar en cache
        self._cache.set(cache_key, action)

        return action
    
    async def get_action_by_id(self, action_id: int) -> ActionConfig:
        """
        Obtiene una acción por su ID.
        
        Args:
            action_id: ID de la acción
            
        Returns:
            ActionConfig encontrado
            
        Raises:
            ConfigNotFoundError: Si la acción no existe
        """
        action = await self.session.get(ActionConfig, action_id)
        
        if not action:
            raise ConfigNotFoundError("ActionConfig", str(action_id))
        
        return action
    
    async def create_action(
        self,
        action_key: str,
        display_name: str,
        points_amount: int,
        description: Optional[str] = None
    ) -> ActionConfig:
        """
        Crea una nueva configuración de acción.

        Args:
            action_key: Identificador único (ej: "custom_reaction")
            display_name: Nombre para mostrar (ej: "Reacción Custom")
            points_amount: Puntos a otorgar
            description: Descripción opcional

        Returns:
            ActionConfig creado

        Raises:
            ConfigAlreadyExistsError: Si action_key ya existe
            ConfigValidationError: Si los datos son inválidos
        """
        # Validaciones
        if not action_key or len(action_key) < 3:
            raise ConfigValidationError("action_key", "Debe tener al menos 3 caracteres")
        if not display_name:
            raise ConfigValidationError("display_name", "Es requerido")
        if points_amount < 0:
            raise ConfigValidationError("points_amount", "No puede ser negativo")

        # Verificar duplicado
        existing = await self.session.execute(
            select(ActionConfig).where(ActionConfig.action_key == action_key)
        )
        if existing.scalar_one_or_none():
            raise ConfigAlreadyExistsError("ActionConfig", action_key)

        # Crear
        action = ActionConfig(
            action_key=action_key,
            display_name=display_name,
            description=description,
            points_amount=points_amount,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(action)
        await self.session.flush()  # Para obtener ID sin commit

        # Invalidar cache al final
        self._cache.invalidate_group("actions")

        logger.info(f"✅ ActionConfig creado: {action_key} ({points_amount} pts)")
        return action
    
    async def update_action(
        self,
        action_key: str,
        display_name: Optional[str] = None,
        points_amount: Optional[int] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> ActionConfig:
        """
        Actualiza una configuración de acción existente.

        Args:
            action_key: Key de la acción a actualizar
            display_name: Nuevo nombre (opcional)
            points_amount: Nuevos puntos (opcional)
            description: Nueva descripción (opcional)
            is_active: Nuevo estado (opcional)

        Returns:
            ActionConfig actualizado

        Raises:
            ConfigNotFoundError: Si la acción no existe
            ConfigValidationError: Si los datos son inválidos
        """
        action = await self.get_action(action_key)

        # Validaciones
        if points_amount is not None and points_amount < 0:
            raise ConfigValidationError("points_amount", "No puede ser negativo")

        # Actualizar campos proporcionados
        if display_name is not None:
            action.display_name = display_name
        if points_amount is not None:
            action.points_amount = points_amount
        if description is not None:
            action.description = description
        if is_active is not None:
            action.is_active = is_active

        action.updated_at = datetime.utcnow()
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("actions")
        # Invalidar cache específica de la acción
        self._cache.invalidate(f"action:{action_key}")
        # Invalidar cache del punto específico
        self._cache.invalidate(f"action_points:{action_key}")

        logger.info(f"📝 ActionConfig actualizado: {action_key}")
        return action
    
    async def delete_action(self, action_key: str, hard_delete: bool = False) -> bool:
        """
        Elimina (soft o hard) una configuración de acción.

        Args:
            action_key: Key de la acción a eliminar
            hard_delete: Si True, elimina permanentemente

        Returns:
            True si se eliminó correctamente

        Raises:
            ConfigNotFoundError: Si la acción no existe
            ConfigInUseError: Si la acción está siendo usada por misiones
        """
        action = await self.get_action(action_key)

        # Verificar si está en uso por misiones
        missions_using = await self.session.execute(
            select(func.count(MissionConfig.id))
            .where(MissionConfig.target_action == action_key)
            .where(MissionConfig.is_active == True)
        )
        count = missions_using.scalar()
        if count > 0:
            raise ConfigInUseError("ActionConfig", action_key, f"{count} misiones activas")

        if hard_delete:
            await self.session.delete(action)
            logger.warning(f"🗑️ ActionConfig eliminado permanentemente: {action_key}")
        else:
            action.is_active = False
            action.updated_at = datetime.utcnow()
            logger.info(f"🗑️ ActionConfig desactivado: {action_key}")

        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("actions")
        # Invalidar cache específica de la acción
        self._cache.invalidate(f"action:{action_key}")
        # Invalidar cache del punto específico
        self._cache.invalidate(f"action_points:{action_key}")

        return True
    
    async def get_points_for_action(self, action_key: str) -> int:
        """
        Obtiene los puntos configurados para una acción.

        Método de conveniencia para uso en GamificationService.

        Args:
            action_key: Key de la acción

        Returns:
            Puntos configurados, o 0 si no existe o está inactiva
        """
        cache_key = f"action_points:{action_key}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            action = await self.get_action(action_key)
            if not action.is_active:
                points = 0
            else:
                points = action.points_amount

            # Guardar en cache con TTL más corto
            self._cache.set(cache_key, points, ttl=60)  # 1 minuto para puntos específicos

            return points
        except ConfigNotFoundError:
            logger.warning(f"⚠️ Acción no configurada: {action_key}")
            # Guardar el valor 0 en cache para evitar consultas repetidas
            self._cache.set(cache_key, 0, ttl=60)
            return 0
    
    # ═══════════════════════════════════════════════════════════════
    # LEVEL CONFIG CRUD
    # ═══════════════════════════════════════════════════════════════
    
    async def list_levels(self, include_inactive: bool = False) -> List[LevelConfig]:
        """
        Lista todos los niveles configurados.

        Args:
            include_inactive: Si True, incluye niveles desactivados

        Returns:
            Lista de LevelConfig ordenados por 'order'
        """
        cache_key = f"levels:{'all' if include_inactive else 'active'}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📋 Listados {len(cached)} niveles (from cache)")
            return cached

        # Query a BD
        query = select(LevelConfig)
        if not include_inactive:
            query = query.where(LevelConfig.is_active == True)
        query = query.order_by(LevelConfig.order)

        result = await self.session.execute(query)
        levels = list(result.scalars().all())

        # Guardar en cache
        self._cache.set(cache_key, levels)

        logger.debug(f"📋 Listados {len(levels)} niveles (from DB)")
        return levels
    
    async def get_level(self, level_id: int) -> LevelConfig:
        """
        Obtiene un nivel por su ID.

        Args:
            level_id: ID del nivel

        Returns:
            LevelConfig encontrado

        Raises:
            ConfigNotFoundError: Si el nivel no existe
        """
        cache_key = f"level:{level_id}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        level = await self.session.get(LevelConfig, level_id)

        if not level:
            raise ConfigNotFoundError("LevelConfig", str(level_id))

        # Guardar en cache
        self._cache.set(cache_key, level)

        return level
    
    async def get_level_for_points(self, points: int) -> Optional[LevelConfig]:
        """
        Obtiene el nivel correspondiente a una cantidad de puntos.

        Args:
            points: Cantidad de puntos

        Returns:
            LevelConfig correspondiente, o None si no hay niveles configurados
        """
        cache_key = f"level_for_points:{points}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        query = (
            select(LevelConfig)
            .where(LevelConfig.is_active == True)
            .where(LevelConfig.min_points <= points)
            .order_by(LevelConfig.min_points.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        level = result.scalar_one_or_none()

        # Guardar en cache
        self._cache.set(cache_key, level)

        return level
    
    async def create_level(
        self,
        name: str,
        min_points: int,
        max_points: Optional[int],
        multiplier: float = 1.0,
        icon: str = "🌱",
        color: Optional[str] = None
    ) -> LevelConfig:
        """
        Crea un nuevo nivel.

        Args:
            name: Nombre del nivel
            min_points: Puntos mínimos para alcanzar
            max_points: Puntos máximos (None = infinito)
            multiplier: Multiplicador de puntos
            icon: Emoji del nivel
            color: Color para UI (opcional)

        Returns:
            LevelConfig creado

        Raises:
            ConfigValidationError: Si los datos son inválidos
        """
        # Validaciones
        if not name or len(name) < 2:
            raise ConfigValidationError("name", "Debe tener al menos 2 caracteres")
        if min_points < 0:
            raise ConfigValidationError("min_points", "No puede ser negativo")
        if max_points is not None and max_points <= min_points:
            raise ConfigValidationError("max_points", "Debe ser mayor que min_points")
        if multiplier < 0.1 or multiplier > 10:
            raise ConfigValidationError("multiplier", "Debe estar entre 0.1 y 10")

        # Calcular order (siguiente al máximo actual)
        max_order = await self.session.execute(
            select(func.max(LevelConfig.order))
        )
        current_max = max_order.scalar() or 0

        level = LevelConfig(
            name=name,
            min_points=min_points,
            max_points=max_points,
            multiplier=multiplier,
            icon=icon,
            color=color,
            order=current_max + 1,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(level)
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("levels")

        logger.info(f"✅ LevelConfig creado: {name} ({min_points}-{max_points} pts)")
        return level
    
    async def update_level(
        self,
        level_id: int,
        name: Optional[str] = None,
        min_points: Optional[int] = None,
        max_points: Optional[int] = None,
        multiplier: Optional[float] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> LevelConfig:
        """
        Actualiza un nivel existente.

        Args:
            level_id: ID del nivel a actualizar
            ... campos opcionales a actualizar

        Returns:
            LevelConfig actualizado

        Raises:
            ConfigNotFoundError: Si el nivel no existe
            ConfigValidationError: Si los datos son inválidos
        """
        level = await self.get_level(level_id)

        # Validaciones
        if min_points is not None and min_points < 0:
            raise ConfigValidationError("min_points", "No puede ser negativo")
        if multiplier is not None and (multiplier < 0.1 or multiplier > 10):
            raise ConfigValidationError("multiplier", "Debe estar entre 0.1 y 10")

        # Actualizar campos proporcionados
        if name is not None:
            level.name = name
        if min_points is not None:
            level.min_points = min_points
        if max_points is not None:
            level.max_points = max_points
        if multiplier is not None:
            level.multiplier = multiplier
        if icon is not None:
            level.icon = icon
        if color is not None:
            level.color = color
        if is_active is not None:
            level.is_active = is_active

        level.updated_at = datetime.utcnow()
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("levels")
        # Invalidar cache específica del nivel
        self._cache.invalidate(f"level:{level_id}")

        logger.info(f"📝 LevelConfig actualizado: {level.name}")
        return level
    
    async def delete_level(self, level_id: int, hard_delete: bool = False) -> bool:
        """
        Elimina (soft o hard) un nivel.

        Args:
            level_id: ID del nivel a eliminar
            hard_delete: Si True, elimina permanentemente

        Returns:
            True si se eliminó correctamente

        Raises:
            ConfigNotFoundError: Si el nivel no existe
        """
        level = await self.get_level(level_id)

        if hard_delete:
            await self.session.delete(level)
            logger.warning(f"🗑️ LevelConfig eliminado permanentemente: {level.name}")
        else:
            level.is_active = False
            level.updated_at = datetime.utcnow()
            logger.info(f"🗑️ LevelConfig desactivado: {level.name}")

        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("levels")
        # Invalidar cache específica del nivel
        self._cache.invalidate(f"level:{level_id}")
        # Invalidar cache de niveles por puntos
        self._cache.invalidate_group("level_for_points")

        return True
    
    async def reorder_levels(self, level_ids: List[int]) -> List[LevelConfig]:
        """
        Reordena los niveles según el orden proporcionado.

        Args:
            level_ids: Lista de IDs en el nuevo orden

        Returns:
            Lista de niveles reordenados
        """
        levels = []
        for idx, level_id in enumerate(level_ids, start=1):
            level = await self.get_level(level_id)
            level.order = idx
            level.updated_at = datetime.utcnow()
            levels.append(level)

        await self.session.flush()
        logger.info(f"📝 Niveles reordenados: {level_ids}")
        return levels

    # ═══════════════════════════════════════════════════════════════
    # BADGE CONFIG CRUD
    # ═══════════════════════════════════════════════════════════════

    async def list_badges(self, include_inactive: bool = False) -> List[BadgeConfig]:
        """
        Lista todos los badges configurados.

        Args:
            include_inactive: Si True, incluye badges desactivados

        Returns:
            Lista de BadgeConfig ordenados por badge_key
        """
        cache_key = f"badges:{'all' if include_inactive else 'active'}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📋 Listados {len(cached)} badges (from cache)")
            return cached

        # Query a BD
        query = select(BadgeConfig)
        if not include_inactive:
            query = query.where(BadgeConfig.is_active == True)
        query = query.order_by(BadgeConfig.badge_key)

        result = await self.session.execute(query)
        badges = list(result.scalars().all())

        # Guardar en cache
        self._cache.set(cache_key, badges)

        logger.debug(f"📋 Listados {len(badges)} badges (from DB)")
        return badges

    async def get_badge(self, badge_key: str) -> BadgeConfig:
        """
        Obtiene un badge por su key.

        Args:
            badge_key: Identificador único del badge

        Returns:
            BadgeConfig encontrado

        Raises:
            ConfigNotFoundError: Si el badge no existe
        """
        cache_key = f"badge:{badge_key}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self.session.execute(
            select(BadgeConfig).where(BadgeConfig.badge_key == badge_key)
        )
        badge = result.scalar_one_or_none()

        if not badge:
            raise ConfigNotFoundError("BadgeConfig", badge_key)

        # Guardar en cache
        self._cache.set(cache_key, badge)

        return badge

    async def get_badge_by_id(self, badge_id: int) -> BadgeConfig:
        """
        Obtiene un badge por su ID.

        Args:
            badge_id: ID del badge

        Returns:
            BadgeConfig encontrado

        Raises:
            ConfigNotFoundError: Si el badge no existe
        """
        badge = await self.session.get(BadgeConfig, badge_id)

        if not badge:
            raise ConfigNotFoundError("BadgeConfig", str(badge_id))

        return badge

    async def create_badge(
        self,
        badge_key: str,
        name: str,
        icon: str,
        requirement_type: str,
        requirement_value: int,
        description: Optional[str] = None
    ) -> BadgeConfig:
        """
        Crea un nuevo badge.

        Args:
            badge_key: Identificador único (ej: "super_reactor")
            name: Nombre para mostrar (ej: "Super Reactor")
            icon: Emoji del badge
            requirement_type: Tipo de requisito (total_reactions, streak_days, etc)
            requirement_value: Valor requerido
            description: Descripción de cómo obtenerlo

        Returns:
            BadgeConfig creado

        Raises:
            ConfigAlreadyExistsError: Si badge_key ya existe
            ConfigValidationError: Si los datos son inválidos
        """
        # Validaciones
        if not badge_key or len(badge_key) < 3:
            raise ConfigValidationError("badge_key", "Debe tener al menos 3 caracteres")
        if not name:
            raise ConfigValidationError("name", "Es requerido")
        if not icon:
            raise ConfigValidationError("icon", "Es requerido")
        if not requirement_type:
            raise ConfigValidationError("requirement_type", "Es requerido")
        if requirement_value < 0:
            raise ConfigValidationError("requirement_value", "No puede ser negativo")

        # Validar requirement_type
        valid_types = [
            "total_reactions",
            "total_points",
            "streak_days",
            "is_vip",
            "total_missions",
            "level_reached",
            "custom"
        ]
        if requirement_type not in valid_types:
            raise ConfigValidationError(
                "requirement_type",
                f"Debe ser uno de: {', '.join(valid_types)}"
            )

        # Verificar duplicado
        existing = await self.session.execute(
            select(BadgeConfig).where(BadgeConfig.badge_key == badge_key)
        )
        if existing.scalar_one_or_none():
            raise ConfigAlreadyExistsError("BadgeConfig", badge_key)

        badge = BadgeConfig(
            badge_key=badge_key,
            name=name,
            icon=icon,
            description=description,
            requirement_type=requirement_type,
            requirement_value=requirement_value,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(badge)
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("badges")

        logger.info(f"✅ BadgeConfig creado: {badge_key} ({requirement_type}={requirement_value})")
        return badge

    async def update_badge(
        self,
        badge_key: str,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        requirement_type: Optional[str] = None,
        requirement_value: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> BadgeConfig:
        """
        Actualiza un badge existente.

        Args:
            badge_key: Key del badge a actualizar
            ... campos opcionales a actualizar

        Returns:
            BadgeConfig actualizado

        Raises:
            ConfigNotFoundError: Si el badge no existe
            ConfigValidationError: Si los datos son inválidos
        """
        badge = await self.get_badge(badge_key)

        # Validaciones
        if requirement_value is not None and requirement_value < 0:
            raise ConfigValidationError("requirement_value", "No puede ser negativo")

        # Actualizar campos proporcionados
        if name is not None:
            badge.name = name
        if icon is not None:
            badge.icon = icon
        if description is not None:
            badge.description = description
        if requirement_type is not None:
            badge.requirement_type = requirement_type
        if requirement_value is not None:
            badge.requirement_value = requirement_value
        if is_active is not None:
            badge.is_active = is_active

        badge.updated_at = datetime.utcnow()
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("badges")
        # Invalidar cache específica del badge
        self._cache.invalidate(f"badge:{badge_key}")

        logger.info(f"📝 BadgeConfig actualizado: {badge_key}")
        return badge

    async def delete_badge(self, badge_key: str, hard_delete: bool = False) -> bool:
        """
        Elimina (soft o hard) un badge.

        Args:
            badge_key: Key del badge a eliminar
            hard_delete: Si True, elimina permanentemente

        Returns:
            True si se eliminó correctamente

        Raises:
            ConfigNotFoundError: Si el badge no existe
            ConfigInUseError: Si el badge está siendo usado por recompensas
        """
        badge = await self.get_badge(badge_key)

        # Verificar si está en uso por rewards
        rewards_using = await self.session.execute(
            select(func.count(RewardConfig.id))
            .where(RewardConfig.badge_id == badge.id)
            .where(RewardConfig.is_active == True)
        )
        count = rewards_using.scalar()
        if count > 0:
            raise ConfigInUseError("BadgeConfig", badge_key, f"{count} recompensas activas")

        if hard_delete:
            await self.session.delete(badge)
            logger.warning(f"🗑️ BadgeConfig eliminado permanentemente: {badge_key}")
        else:
            badge.is_active = False
            badge.updated_at = datetime.utcnow()
            logger.info(f"🗑️ BadgeConfig desactivado: {badge_key}")

        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("badges")
        # Invalidar cache específica del badge
        self._cache.invalidate(f"badge:{badge_key}")

        return True

    async def get_badges_for_user_progress(
        self,
        total_reactions: int,
        total_points: int,
        streak_days: int,
        is_vip: bool
    ) -> List[BadgeConfig]:
        """
        Obtiene los badges que un usuario califica para desbloquear.

        Método de conveniencia para GamificationService.

        Args:
            total_reactions: Total de reacciones del usuario
            total_points: Total de puntos del usuario
            streak_days: Días de racha actual
            is_vip: Si el usuario es VIP

        Returns:
            Lista de badges que el usuario cumple requisitos
        """
        all_badges = await self.list_badges()
        qualified = []

        for badge in all_badges:
            req_type = badge.requirement_type
            req_value = badge.requirement_value

            if req_type == "total_reactions" and total_reactions >= req_value:
                qualified.append(badge)
            elif req_type == "total_points" and total_points >= req_value:
                qualified.append(badge)
            elif req_type == "streak_days" and streak_days >= req_value:
                qualified.append(badge)
            elif req_type == "is_vip" and is_vip:
                qualified.append(badge)

        return qualified

    # ═══════════════════════════════════════════════════════════════
    # REWARD CONFIG CRUD
    # ═══════════════════════════════════════════════════════════════

    async def list_rewards(self, include_inactive: bool = False) -> List[RewardConfig]:
        """
        Lista todas las recompensas configuradas.

        Args:
            include_inactive: Si True, incluye recompensas desactivadas

        Returns:
            Lista de RewardConfig con badge relacionado cargado
        """
        cache_key = f"rewards:{'all' if include_inactive else 'active'}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📋 Listadas {len(cached)} recompensas (from cache)")
            return cached

        # Query a BD
        query = select(RewardConfig).options(selectinload(RewardConfig.badge))
        if not include_inactive:
            query = query.where(RewardConfig.is_active == True)
        query = query.order_by(RewardConfig.name)

        result = await self.session.execute(query)
        rewards = list(result.scalars().all())

        # Guardar en cache
        self._cache.set(cache_key, rewards)

        logger.debug(f"📋 Listadas {len(rewards)} recompensas (from DB)")
        return rewards

    async def get_reward(self, reward_id: int) -> RewardConfig:
        """
        Obtiene una recompensa por su ID.

        Args:
            reward_id: ID de la recompensa

        Returns:
            RewardConfig encontrado con badge cargado

        Raises:
            ConfigNotFoundError: Si la recompensa no existe
        """
        cache_key = f"reward:{reward_id}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self.session.execute(
            select(RewardConfig)
            .options(selectinload(RewardConfig.badge))
            .where(RewardConfig.id == reward_id)
        )
        reward = result.scalar_one_or_none()

        if not reward:
            raise ConfigNotFoundError("RewardConfig", str(reward_id))

        # Guardar en cache
        self._cache.set(cache_key, reward)

        return reward

    async def create_reward(
        self,
        name: str,
        reward_type: str,
        points_amount: Optional[int] = None,
        badge_id: Optional[int] = None,
        description: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> RewardConfig:
        """
        Crea una nueva recompensa.

        Args:
            name: Nombre de la recompensa
            reward_type: Tipo (points, badge, both, custom)
            points_amount: Puntos a otorgar (requerido si type incluye points)
            badge_id: ID del badge a otorgar (requerido si type incluye badge)
            description: Descripción opcional
            custom_data: Datos adicionales para recompensas custom

        Returns:
            RewardConfig creado

        Raises:
            ConfigValidationError: Si los datos son inválidos
            ConfigNotFoundError: Si badge_id no existe
        """
        # Validar reward_type
        valid_types = ["points", "badge", "both", "custom"]
        if reward_type not in valid_types:
            raise ConfigValidationError(
                "reward_type",
                f"Debe ser uno de: {', '.join(valid_types)}"
            )

        # Validaciones según tipo
        if reward_type in ["points", "both"]:
            if points_amount is None or points_amount <= 0:
                raise ConfigValidationError(
                    "points_amount",
                    "Es requerido y debe ser positivo para tipo 'points' o 'both'"
                )

        if reward_type in ["badge", "both"]:
            if badge_id is None:
                raise ConfigValidationError(
                    "badge_id",
                    "Es requerido para tipo 'badge' o 'both'"
                )
            # Verificar que badge existe
            await self.get_badge_by_id(badge_id)

        if not name:
            raise ConfigValidationError("name", "Es requerido")

        reward = RewardConfig(
            name=name,
            description=description,
            reward_type=reward_type,
            points_amount=points_amount,
            badge_id=badge_id,
            custom_data=custom_data,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(reward)
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("rewards")

        logger.info(f"✅ RewardConfig creado: {name} (tipo={reward_type})")
        return reward

    async def create_reward_with_new_badge(
        self,
        name: str,
        reward_type: str,
        points_amount: Optional[int] = None,
        description: Optional[str] = None,
        # Datos del badge a crear
        badge_key: str = None,
        badge_name: str = None,
        badge_icon: str = "🏆",
        badge_requirement_type: str = "custom",
        badge_requirement_value: int = 1,
        badge_description: Optional[str] = None
    ) -> Tuple[RewardConfig, BadgeConfig]:
        """
        Crea una recompensa junto con un nuevo badge (nested creation).

        Operación atómica: si falla la creación del badge o reward,
        ninguno se crea.

        Args:
            name: Nombre de la recompensa
            reward_type: Tipo (debe ser 'badge' o 'both')
            points_amount: Puntos (solo si type es 'both')
            description: Descripción de la recompensa
            badge_key: Key única del badge
            badge_name: Nombre del badge
            badge_icon: Emoji del badge
            badge_requirement_type: Tipo de requisito
            badge_requirement_value: Valor del requisito
            badge_description: Descripción del badge

        Returns:
            Tuple de (RewardConfig, BadgeConfig) creados

        Raises:
            ConfigValidationError: Si los datos son inválidos
            ConfigAlreadyExistsError: Si badge_key ya existe
        """
        if reward_type not in ["badge", "both"]:
            raise ConfigValidationError(
                "reward_type",
                "Debe ser 'badge' o 'both' para crear con badge"
            )

        if not badge_key or not badge_name:
            raise ConfigValidationError(
                "badge_key/badge_name",
                "Son requeridos para crear badge"
            )

        # Crear badge primero
        badge = await self.create_badge(
            badge_key=badge_key,
            name=badge_name,
            icon=badge_icon,
            requirement_type=badge_requirement_type,
            requirement_value=badge_requirement_value,
            description=badge_description
        )

        # Crear reward con el badge
        reward = await self.create_reward(
            name=name,
            reward_type=reward_type,
            points_amount=points_amount,
            badge_id=badge.id,
            description=description
        )

        logger.info(f"✅ Nested creation: Reward '{name}' + Badge '{badge_key}'")
        return reward, badge

    async def update_reward(
        self,
        reward_id: int,
        name: Optional[str] = None,
        reward_type: Optional[str] = None,
        points_amount: Optional[int] = None,
        badge_id: Optional[int] = None,
        description: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> RewardConfig:
        """
        Actualiza una recompensa existente.

        Args:
            reward_id: ID de la recompensa a actualizar
            ... campos opcionales a actualizar

        Returns:
            RewardConfig actualizado

        Raises:
            ConfigNotFoundError: Si la recompensa no existe
            ConfigValidationError: Si los datos son inválidos
        """
        reward = await self.get_reward(reward_id)

        # Validar badge_id si se proporciona
        if badge_id is not None:
            await self.get_badge_by_id(badge_id)

        # Actualizar campos proporcionados
        if name is not None:
            reward.name = name
        if reward_type is not None:
            reward.reward_type = reward_type
        if points_amount is not None:
            reward.points_amount = points_amount
        if badge_id is not None:
            reward.badge_id = badge_id
        if description is not None:
            reward.description = description
        if custom_data is not None:
            reward.custom_data = custom_data
        if is_active is not None:
            reward.is_active = is_active

        reward.updated_at = datetime.utcnow()
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("rewards")
        # Invalidar cache específica de la recompensa
        self._cache.invalidate(f"reward:{reward_id}")

        logger.info(f"📝 RewardConfig actualizado: {reward.name}")
        return reward

    async def delete_reward(self, reward_id: int, hard_delete: bool = False) -> bool:
        """
        Elimina (soft o hard) una recompensa.

        Args:
            reward_id: ID de la recompensa a eliminar
            hard_delete: Si True, elimina permanentemente

        Returns:
            True si se eliminó correctamente

        Raises:
            ConfigNotFoundError: Si la recompensa no existe
            ConfigInUseError: Si está siendo usada por misiones
        """
        reward = await self.get_reward(reward_id)

        # Verificar si está en uso por misiones
        missions_using = await self.session.execute(
            select(func.count(MissionConfig.id))
            .where(MissionConfig.reward_id == reward_id)
            .where(MissionConfig.is_active == True)
        )
        count = missions_using.scalar()
        if count > 0:
            raise ConfigInUseError("RewardConfig", reward.name, f"{count} misiones activas")

        if hard_delete:
            await self.session.delete(reward)
            logger.warning(f"🗑️ RewardConfig eliminado permanentemente: {reward.name}")
        else:
            reward.is_active = False
            reward.updated_at = datetime.utcnow()
            logger.info(f"🗑️ RewardConfig desactivado: {reward.name}")

        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("rewards")
        # Invalidar cache específica de la recompensa
        self._cache.invalidate(f"reward:{reward_id}")

        return True

    # ═══════════════════════════════════════════════════════════════
    # MISSION CONFIG CRUD
    # ═══════════════════════════════════════════════════════════════

    async def list_missions(self, include_inactive: bool = False) -> List[MissionConfig]:
        """
        Lista todas las misiones configuradas.

        Args:
            include_inactive: Si True, incluye misiones desactivadas

        Returns:
            Lista de MissionConfig con reward (y badge) cargados
        """
        cache_key = f"missions:{'all' if include_inactive else 'active'}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📋 Listadas {len(cached)} misiones (from cache)")
            return cached

        # Query a BD
        query = (
            select(MissionConfig)
            .options(
                selectinload(MissionConfig.reward)
                .selectinload(RewardConfig.badge)
            )
        )
        if not include_inactive:
            query = query.where(MissionConfig.is_active == True)
        query = query.order_by(MissionConfig.name)

        result = await self.session.execute(query)
        missions = list(result.scalars().all())

        # Guardar en cache
        self._cache.set(cache_key, missions)

        logger.debug(f"📋 Listadas {len(missions)} misiones (from DB)")
        return missions

    async def get_mission(self, mission_id: int) -> MissionConfig:
        """
        Obtiene una misión por su ID.

        Args:
            mission_id: ID de la misión

        Returns:
            MissionConfig con reward y badge cargados

        Raises:
            ConfigNotFoundError: Si la misión no existe
        """
        cache_key = f"mission:{mission_id}"

        # Intentar obtener de cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self.session.execute(
            select(MissionConfig)
            .options(
                selectinload(MissionConfig.reward)
                .selectinload(RewardConfig.badge)
            )
            .where(MissionConfig.id == mission_id)
        )
        mission = result.scalar_one_or_none()

        if not mission:
            raise ConfigNotFoundError("MissionConfig", str(mission_id))

        # Guardar en cache
        self._cache.set(cache_key, mission)

        return mission

    async def create_mission(
        self,
        name: str,
        mission_type: str,
        target_value: int,
        target_action: Optional[str] = None,
        reward_id: Optional[int] = None,
        description: Optional[str] = None,
        time_limit_hours: Optional[int] = None,
        is_repeatable: bool = False,
        cooldown_hours: Optional[int] = None
    ) -> MissionConfig:
        """
        Crea una nueva misión.

        Args:
            name: Nombre de la misión
            mission_type: Tipo (single, streak, cumulative, timed)
            target_value: Valor objetivo (ej: 10 reacciones)
            target_action: Acción objetivo (referencia a ActionConfig.action_key)
            reward_id: ID de la recompensa al completar
            description: Descripción de la misión
            time_limit_hours: Límite de tiempo (solo para tipo 'timed')
            is_repeatable: Si se puede completar múltiples veces
            cooldown_hours: Tiempo entre repeticiones

        Returns:
            MissionConfig creado

        Raises:
            ConfigValidationError: Si los datos son inválidos
            ConfigNotFoundError: Si reward_id o target_action no existen
        """
        # Validar mission_type
        valid_types = ["single", "streak", "cumulative", "timed"]
        if mission_type not in valid_types:
            raise ConfigValidationError(
                "mission_type",
                f"Debe ser uno de: {', '.join(valid_types)}"
            )

        # Validaciones
        if not name:
            raise ConfigValidationError("name", "Es requerido")
        if target_value <= 0:
            raise ConfigValidationError("target_value", "Debe ser positivo")

        # Validar target_action si se proporciona
        if target_action:
            try:
                await self.get_action(target_action)
            except ConfigNotFoundError:
                raise ConfigValidationError(
                    "target_action",
                    f"Acción '{target_action}' no existe"
                )

        # Validar reward_id si se proporciona
        if reward_id:
            await self.get_reward(reward_id)

        # Validaciones específicas por tipo
        if mission_type == "timed" and not time_limit_hours:
            raise ConfigValidationError(
                "time_limit_hours",
                "Es requerido para misiones tipo 'timed'"
            )

        if is_repeatable and not cooldown_hours:
            raise ConfigValidationError(
                "cooldown_hours",
                "Es requerido si is_repeatable=True"
            )

        mission = MissionConfig(
            name=name,
            description=description,
            mission_type=mission_type,
            target_action=target_action,
            target_value=target_value,
            reward_id=reward_id,
            time_limit_hours=time_limit_hours,
            is_repeatable=is_repeatable,
            cooldown_hours=cooldown_hours,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(mission)
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("missions")

        logger.info(f"✅ MissionConfig creado: {name} (tipo={mission_type})")
        return mission

    async def create_mission_with_reward(
        self,
        # Mission data
        name: str,
        mission_type: str,
        target_value: int,
        target_action: Optional[str] = None,
        description: Optional[str] = None,
        time_limit_hours: Optional[int] = None,
        is_repeatable: bool = False,
        cooldown_hours: Optional[int] = None,
        # Reward data
        reward_name: str = None,
        reward_type: str = "points",
        reward_points: Optional[int] = None,
        reward_badge_id: Optional[int] = None,
        reward_description: Optional[str] = None
    ) -> Tuple[MissionConfig, RewardConfig]:
        """
        Crea una misión junto con una nueva recompensa (nested creation nivel 1).

        Args:
            ... parámetros de misión ...
            reward_name: Nombre de la recompensa a crear
            reward_type: Tipo de recompensa
            reward_points: Puntos de la recompensa
            reward_badge_id: Badge existente para la recompensa
            reward_description: Descripción de la recompensa

        Returns:
            Tuple de (MissionConfig, RewardConfig)
        """
        if not reward_name:
            raise ConfigValidationError("reward_name", "Es requerido para crear recompensa")

        # Crear reward primero
        reward = await self.create_reward(
            name=reward_name,
            reward_type=reward_type,
            points_amount=reward_points,
            badge_id=reward_badge_id,
            description=reward_description
        )

        # Crear mission con el reward
        mission = await self.create_mission(
            name=name,
            mission_type=mission_type,
            target_value=target_value,
            target_action=target_action,
            reward_id=reward.id,
            description=description,
            time_limit_hours=time_limit_hours,
            is_repeatable=is_repeatable,
            cooldown_hours=cooldown_hours
        )

        logger.info(f"✅ Nested creation nivel 1: Mission '{name}' + Reward '{reward_name}'")
        return mission, reward

    async def create_mission_complete(
        self,
        # Mission data
        name: str,
        mission_type: str,
        target_value: int,
        target_action: Optional[str] = None,
        description: Optional[str] = None,
        time_limit_hours: Optional[int] = None,
        is_repeatable: bool = False,
        cooldown_hours: Optional[int] = None,
        # Reward data
        reward_name: str = None,
        reward_type: str = "both",
        reward_points: Optional[int] = None,
        reward_description: Optional[str] = None,
        # Badge data (para crear nuevo)
        badge_key: str = None,
        badge_name: str = None,
        badge_icon: str = "🏆",
        badge_requirement_type: str = "custom",
        badge_requirement_value: int = 1,
        badge_description: Optional[str] = None
    ) -> Tuple[MissionConfig, RewardConfig, BadgeConfig]:
        """
        Crea una misión completa con recompensa Y badge nuevos (nested creation nivel 2).

        Esta es la operación más completa: crea los 3 recursos en una transacción.

        Args:
            ... parámetros de misión ...
            ... parámetros de recompensa ...
            ... parámetros de badge ...

        Returns:
            Tuple de (MissionConfig, RewardConfig, BadgeConfig)

        Raises:
            ConfigValidationError: Si faltan datos requeridos
            ConfigAlreadyExistsError: Si badge_key ya existe
        """
        # Validar que tenemos datos para todo
        if not reward_name:
            raise ConfigValidationError("reward_name", "Es requerido")
        if not badge_key or not badge_name:
            raise ConfigValidationError("badge_key/badge_name", "Son requeridos")

        # Crear badge primero
        badge = await self.create_badge(
            badge_key=badge_key,
            name=badge_name,
            icon=badge_icon,
            requirement_type=badge_requirement_type,
            requirement_value=badge_requirement_value,
            description=badge_description
        )

        # Crear reward con el badge
        reward = await self.create_reward(
            name=reward_name,
            reward_type=reward_type,
            points_amount=reward_points,
            badge_id=badge.id,
            description=reward_description
        )

        # Crear mission con el reward
        mission = await self.create_mission(
            name=name,
            mission_type=mission_type,
            target_value=target_value,
            target_action=target_action,
            reward_id=reward.id,
            description=description,
            time_limit_hours=time_limit_hours,
            is_repeatable=is_repeatable,
            cooldown_hours=cooldown_hours
        )

        logger.info(
            f"✅ Nested creation completa: "
            f"Mission '{name}' + Reward '{reward_name}' + Badge '{badge_key}'"
        )
        return mission, reward, badge

    async def update_mission(
        self,
        mission_id: int,
        name: Optional[str] = None,
        mission_type: Optional[str] = None,
        target_action: Optional[str] = None,
        target_value: Optional[int] = None,
        reward_id: Optional[int] = None,
        description: Optional[str] = None,
        time_limit_hours: Optional[int] = None,
        is_repeatable: Optional[bool] = None,
        cooldown_hours: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> MissionConfig:
        """
        Actualiza una misión existente.
        """
        mission = await self.get_mission(mission_id)

        # Validaciones
        if target_value is not None and target_value <= 0:
            raise ConfigValidationError("target_value", "Debe ser positivo")
        if reward_id is not None:
            await self.get_reward(reward_id)
        if target_action is not None:
            try:
                await self.get_action(target_action)
            except ConfigNotFoundError:
                raise ConfigValidationError(
                    "target_action",
                    f"Acción '{target_action}' no existe"
                )

        # Actualizar campos
        if name is not None:
            mission.name = name
        if mission_type is not None:
            mission.mission_type = mission_type
        if target_action is not None:
            mission.target_action = target_action
        if target_value is not None:
            mission.target_value = target_value
        if reward_id is not None:
            mission.reward_id = reward_id
        if description is not None:
            mission.description = description
        if time_limit_hours is not None:
            mission.time_limit_hours = time_limit_hours
        if is_repeatable is not None:
            mission.is_active = is_repeatable
        if cooldown_hours is not None:
            mission.cooldown_hours = cooldown_hours
        if is_active is not None:
            mission.is_active = is_active

        mission.updated_at = datetime.utcnow()
        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("missions")
        # Invalidar cache específica de la misión
        self._cache.invalidate(f"mission:{mission_id}")

        logger.info(f"📝 MissionConfig actualizado: {mission.name}")
        return mission

    async def delete_mission(self, mission_id: int, hard_delete: bool = False) -> bool:
        """
        Elimina (soft o hard) una misión.
        """
        mission = await self.get_mission(mission_id)

        if hard_delete:
            await self.session.delete(mission)
            logger.warning(f"🗑️ MissionConfig eliminado permanentemente: {mission.name}")
        else:
            mission.is_active = False
            mission.updated_at = datetime.utcnow()
            logger.info(f"🗑️ MissionConfig desactivado: {mission.name}")

        await self.session.flush()

        # Invalidar cache al final
        self._cache.invalidate_group("missions")
        # Invalidar cache específica de la misión
        self._cache.invalidate(f"mission:{mission_id}")

        return True

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE PREVIEW
    # ═══════════════════════════════════════════════════════════════

    def preview_mission_complete(
        self,
        mission_data: Dict[str, Any],
        reward_data: Dict[str, Any],
        badge_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera un preview de texto de lo que se creará.

        Args:
            mission_data: Datos de la misión
            reward_data: Datos de la recompensa
            badge_data: Datos del badge (opcional)

        Returns:
            String formateado con el preview
        """
        lines = [
            "📋 <b>PREVIEW - Se crearán los siguientes recursos:</b>",
            "",
            "🎯 <b>MISIÓN</b>",
            f"   Nombre: {mission_data.get('name', 'Sin nombre')}",
            f"   Tipo: {mission_data.get('mission_type', 'single')}",
            f"   Objetivo: {mission_data.get('target_value', 1)}",
        ]

        if mission_data.get('target_action'):
            lines.append(f"   Acción: {mission_data['target_action']}")

        lines.extend([
            "",
            "🎁 <b>RECOMPENSA</b>",
            f"   Nombre: {reward_data.get('name', 'Sin nombre')}",
            f"   Tipo: {reward_data.get('reward_type', 'points')}",
        ])

        if reward_data.get('points_amount'):
            lines.append(f"   Puntos: +{reward_data['points_amount']}")

        if badge_data:
            lines.extend([
                "",
                "🏆 <b>BADGE</b>",
                f"   Key: {badge_data.get('badge_key', 'sin_key')}",
                f"   Nombre: {badge_data.get('name', 'Sin nombre')}",
                f"   Icono: {badge_data.get('icon', '🏆')}",
            ])

        lines.extend([
            "",
            "─" * 30,
            "✅ Confirmar para crear todo",
            "❌ Cancelar para descartar",
        ])

        return "\n".join(lines)