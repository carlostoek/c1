"""
Servicio de gestión de niveles.

Responsabilidades:
- CRUD de niveles
- Cálculo automático de level-ups
- Progresión de usuarios
- Estadísticas por nivel
"""

from typing import Optional, List, Tuple
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

from bot.gamification.database.models import Level, UserGamification

logger = logging.getLogger(__name__)


class LevelService:
    """Servicio de gestión de niveles y progresión."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================
    # CRUD NIVELES
    # ========================================

    async def create_level(
        self,
        name: str,
        min_besitos: int,
        order: int,
        benefits: Optional[dict] = None
    ) -> Level:
        """Crea nuevo nivel.

        Args:
            name: Nombre del nivel
            min_besitos: Mínimo de besitos requeridos
            order: Orden de progresión (1, 2, 3...)
            benefits: Dict con beneficios del nivel

        Returns:
            Level creado

        Raises:
            ValueError: Si validación falla
        """
        # Validar
        is_valid, error = await self._validate_level_data(
            name, min_besitos, order
        )
        if not is_valid:
            raise ValueError(error)

        level = Level(
            name=name,
            min_besitos=min_besitos,
            order=order,
            benefits=json.dumps(benefits) if benefits else None,
            active=True
        )
        self.session.add(level)
        await self.session.commit()
        await self.session.refresh(level)

        logger.info(f"Created level: {name} ({min_besitos} besitos, order {order})")
        return level

    async def update_level(
        self,
        level_id: int,
        name: Optional[str] = None,
        min_besitos: Optional[int] = None,
        order: Optional[int] = None,
        benefits: Optional[dict] = None,
        active: Optional[bool] = None
    ) -> Level:
        """Actualiza nivel existente.

        Args:
            level_id: ID del nivel a actualizar
            name: Nuevo nombre (opcional)
            min_besitos: Nuevos besitos mínimos (opcional)
            order: Nuevo orden (opcional)
            benefits: Nuevos beneficios (opcional)
            active: Nuevo estado activo (opcional)

        Returns:
            Level actualizado

        Raises:
            ValueError: Si nivel no existe o validación falla
        """
        level = await self.session.get(Level, level_id)
        if not level:
            raise ValueError(f"Level {level_id} not found")

        # Validar cambios si se proporcionan
        final_name = name if name is not None else level.name
        final_min_besitos = min_besitos if min_besitos is not None else level.min_besitos
        final_order = order if order is not None else level.order

        is_valid, error = await self._validate_level_data(
            final_name, final_min_besitos, final_order, level_id
        )
        if not is_valid:
            raise ValueError(error)

        # Aplicar cambios
        if name is not None:
            level.name = name
        if min_besitos is not None:
            level.min_besitos = min_besitos
        if order is not None:
            level.order = order
        if benefits is not None:
            level.benefits = json.dumps(benefits)
        if active is not None:
            level.active = active

        await self.session.commit()
        await self.session.refresh(level)

        logger.info(f"Updated level {level_id}: {level.name}")
        return level

    async def delete_level(self, level_id: int) -> bool:
        """Soft-delete de nivel (active=False).

        Args:
            level_id: ID del nivel a eliminar

        Returns:
            True si se eliminó correctamente
        """
        level = await self.session.get(Level, level_id)
        if not level:
            return False

        level.active = False
        await self.session.commit()

        logger.info(f"Deleted level {level_id}: {level.name}")
        return True

    async def get_all_levels(self, active_only: bool = True) -> List[Level]:
        """Obtiene niveles ordenados por order ASC.

        Args:
            active_only: Si True, solo retorna niveles activos

        Returns:
            Lista de niveles ordenados
        """
        stmt = select(Level)
        if active_only:
            stmt = stmt.where(Level.active == True)
        stmt = stmt.order_by(Level.order.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_level_by_id(self, level_id: int) -> Optional[Level]:
        """Obtiene nivel por ID.

        Args:
            level_id: ID del nivel

        Returns:
            Level o None si no existe
        """
        return await self.session.get(Level, level_id)

    # ========================================
    # CÁLCULO DE NIVELES
    # ========================================

    async def calculate_level_for_besitos(self, besitos: int) -> Optional[Level]:
        """
        Calcula nivel correspondiente a cantidad de besitos.

        Lógica: Mayor nivel cuyo min_besitos <= besitos del usuario

        Args:
            besitos: Cantidad de besitos del usuario

        Returns:
            Level correspondiente o None
        """
        stmt = (
            select(Level)
            .where(Level.active == True)
            .where(Level.min_besitos <= besitos)
            .order_by(Level.min_besitos.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_next_level(self, current_level_id: int) -> Optional[Level]:
        """Retorna siguiente nivel en progresión.

        Args:
            current_level_id: ID del nivel actual

        Returns:
            Siguiente nivel o None si es el máximo
        """
        # Obtener current level
        current = await self.session.get(Level, current_level_id)
        if not current:
            return None

        # Buscar nivel con order = current.order + 1
        stmt = (
            select(Level)
            .where(Level.active == True)
            .where(Level.order == current.order + 1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_besitos_to_next_level(self, user_id: int) -> Optional[int]:
        """Calcula besitos faltantes para siguiente nivel.

        Args:
            user_id: ID del usuario

        Returns:
            Besitos faltantes o None si ya está en nivel máximo
        """
        # Obtener usuario
        user = await self.session.get(UserGamification, user_id)
        if not user or not user.current_level_id:
            return None

        # Obtener siguiente nivel
        next_level = await self.get_next_level(user.current_level_id)
        if not next_level:
            return None  # Ya está en nivel máximo

        return max(0, next_level.min_besitos - user.total_besitos)

    # ========================================
    # LEVEL-UPS
    # ========================================

    async def check_and_apply_level_up(
        self,
        user_id: int
    ) -> Tuple[bool, Optional[Level], Optional[Level]]:
        """
        Verifica y aplica level-up automático.

        Flujo:
        1. Obtener UserGamification
        2. Calcular nivel que debería tener según besitos
        3. Si nivel calculado != nivel actual → aplicar cambio
        4. Retornar información del cambio

        Args:
            user_id: ID del usuario

        Returns:
            (changed, old_level, new_level)
        """
        # Obtener usuario
        user = await self.session.get(UserGamification, user_id)
        if not user:
            return False, None, None

        # Calcular nivel que debería tener
        target_level = await self.calculate_level_for_besitos(user.total_besitos)
        if not target_level:
            return False, None, None

        # Si ya está en el nivel correcto, no hacer nada
        if user.current_level_id == target_level.id:
            return False, None, None

        # Obtener nivel anterior para logging
        old_level = None
        if user.current_level_id:
            old_level = await self.session.get(Level, user.current_level_id)

        # Aplicar level-up
        user.current_level_id = target_level.id
        await self.session.commit()

        logger.info(
            f"User {user_id} leveled up: "
            f"{old_level.name if old_level else 'None'} → {target_level.name}"
        )

        return True, old_level, target_level

    async def set_user_level(self, user_id: int, level_id: int) -> bool:
        """Fuerza nivel específico (admin override).

        Args:
            user_id: ID del usuario
            level_id: ID del nivel a asignar

        Returns:
            True si se aplicó correctamente
        """
        user = await self.session.get(UserGamification, user_id)
        if not user:
            return False

        level = await self.session.get(Level, level_id)
        if not level:
            return False

        user.current_level_id = level_id
        await self.session.commit()

        logger.warning(f"Admin override: User {user_id} set to level {level.name}")
        return True

    # ========================================
    # PROGRESIÓN
    # ========================================

    async def get_user_level_progress(self, user_id: int) -> dict:
        """Retorna información completa de progresión.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con información de progresión:
            {
                'current_level': Level,
                'next_level': Optional[Level],
                'current_besitos': int,
                'besitos_to_next': Optional[int],
                'progress_percentage': float
            }
        """
        user = await self.session.get(UserGamification, user_id)
        if not user:
            return {}

        current_level = None
        if user.current_level_id:
            current_level = await self.session.get(Level, user.current_level_id)

        next_level = None
        besitos_to_next = None
        progress_pct = 0.0

        if current_level:
            next_level = await self.get_next_level(current_level.id)
            if next_level:
                besitos_to_next = next_level.min_besitos - user.total_besitos

                # Calcular porcentaje
                range_size = next_level.min_besitos - current_level.min_besitos
                progress_in_range = user.total_besitos - current_level.min_besitos
                progress_pct = (progress_in_range / range_size * 100) if range_size > 0 else 100.0

        return {
            'current_level': current_level,
            'next_level': next_level,
            'current_besitos': user.total_besitos,
            'besitos_to_next': besitos_to_next,
            'progress_percentage': round(progress_pct, 1)
        }

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_level_distribution(self) -> dict:
        """
        Distribución de usuarios por nivel.

        Returns:
            Dict mapeando nombre de nivel a cantidad de usuarios:
            {
                'Novato': 150,
                'Regular': 75,
                'Fanático': 20
            }
        """
        stmt = (
            select(
                Level.name,
                func.count(UserGamification.user_id).label('count')
            )
            .join(UserGamification, Level.id == UserGamification.current_level_id, isouter=True)
            .where(Level.active == True)
            .group_by(Level.name)
            .order_by(Level.order.asc())
        )

        result = await self.session.execute(stmt)
        distribution = {}
        for row in result:
            distribution[row.name] = row.count

        return distribution

    async def get_users_in_level(self, level_id: int, limit: int = 50) -> List[UserGamification]:
        """Lista usuarios en un nivel específico.

        Args:
            level_id: ID del nivel
            limit: Máximo de usuarios a retornar

        Returns:
            Lista de UserGamification en ese nivel
        """
        stmt = (
            select(UserGamification)
            .where(UserGamification.current_level_id == level_id)
            .order_by(UserGamification.total_besitos.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ========================================
    # VALIDACIONES
    # ========================================

    async def _validate_level_data(
        self,
        name: str,
        min_besitos: int,
        order: int,
        level_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Valida datos de nivel.

        Args:
            name: Nombre del nivel
            min_besitos: Besitos mínimos
            order: Orden de progresión
            level_id: ID del nivel (si es update)

        Returns:
            (is_valid, error_message)
        """
        # Validar rangos
        if min_besitos < 0:
            return False, "min_besitos must be >= 0"

        if order <= 0:
            return False, "order must be > 0"

        # Validar nombre único
        stmt = select(func.count()).select_from(Level).where(Level.name == name)
        if level_id:
            stmt = stmt.where(Level.id != level_id)
        result = await self.session.execute(stmt)
        if result.scalar() > 0:
            return False, f"Level name '{name}' already exists"

        # Validar min_besitos único
        stmt = select(func.count()).select_from(Level).where(Level.min_besitos == min_besitos)
        if level_id:
            stmt = stmt.where(Level.id != level_id)
        result = await self.session.execute(stmt)
        if result.scalar() > 0:
            return False, f"Level with min_besitos={min_besitos} already exists"

        # Validar order único
        stmt = select(func.count()).select_from(Level).where(Level.order == order)
        if level_id:
            stmt = stmt.where(Level.id != level_id)
        result = await self.session.execute(stmt)
        if result.scalar() > 0:
            return False, f"Level with order={order} already exists"

        return True, "OK"
