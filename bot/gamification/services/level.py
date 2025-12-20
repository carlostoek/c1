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
        """Crea nuevo nivel."""
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
    ) -> Optional[Level]:
        """Actualiza un nivel existente."""
        level = await self.session.get(Level, level_id)
        if not level:
            return None
        
        # Preparar datos actualizados
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if min_besitos is not None:
            update_data['min_besitos'] = min_besitos
        if order is not None:
            update_data['order'] = order
        if benefits is not None:
            update_data['benefits'] = json.dumps(benefits)
        if active is not None:
            update_data['active'] = active
        
        # Validar datos si hay cambios
        if update_data:
            is_valid, error = await self._validate_level_data(
                name or level.name,
                min_besitos or level.min_besitos,
                order or level.order,
                level_id
            )
            if not is_valid:
                raise ValueError(error)
        
        # Aplicar actualizaciones
        for key, value in update_data.items():
            setattr(level, key, value)
        
        await self.session.commit()
        await self.session.refresh(level)
        
        logger.info(f"Updated level {level_id}: {level.name}")
        return level
    
    async def delete_level(self, level_id: int) -> bool:
        """Soft-delete (active=False) de un nivel."""
        level = await self.session.get(Level, level_id)
        if not level:
            return False
        
        level.active = False
        await self.session.commit()
        
        logger.info(f"Soft-deleted level {level_id}: {level.name}")
        return True
    
    async def get_all_levels(self, active_only: bool = True) -> List[Level]:
        """Obtiene niveles ordenados por order ASC."""
        stmt = select(Level)
        if active_only:
            stmt = stmt.where(Level.active == True)
        stmt = stmt.order_by(Level.order.asc())
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_level_by_id(self, level_id: int) -> Optional[Level]:
        """Obtiene un nivel por ID."""
        return await self.session.get(Level, level_id)
    
    # ========================================
    # CÁLCULO DE NIVELES
    # ========================================
    
    async def calculate_level_for_besitos(self, besitos: int) -> Optional[Level]:
        """
        Calcula nivel correspondiente a cantidad de besitos.
        
        Lógica: Mayor nivel cuyo min_besitos <= besitos del usuario
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
        """Retorna siguiente nivel en progresión."""
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
        """Calcula besitos faltantes para siguiente nivel."""
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
        """Fuerza nivel específico (admin override)."""
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
        """Retorna información completa de progresión."""
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
                besitos_to_next = max(0, next_level.min_besitos - user.total_besitos)
                
                # Calcular porcentaje
                range_size = next_level.min_besitos - current_level.min_besitos
                progress_in_range = user.total_besitos - current_level.min_besitos
                progress_pct = (progress_in_range / range_size * 100) if range_size > 0 else 100.0
            else:
                # Usuario en el nivel más alto
                progress_pct = 100.0
        
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
        """Distribución de usuarios por nivel."""
        stmt = (
            select(Level.name, func.count(UserGamification.user_id).label('user_count'))
            .join(UserGamification, Level.id == UserGamification.current_level_id, isouter=True)
            .where(Level.active == True)
            .group_by(Level.id, Level.name)
            .order_by(Level.order.asc())
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        return {row.name: row.user_count for row in rows}
    
    async def get_users_in_level(self, level_id: int, limit: int = 50) -> List[UserGamification]:
        """Lista usuarios en un nivel específico."""
        stmt = (
            select(UserGamification)
            .where(UserGamification.current_level_id == level_id)
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
        """Valida datos de nivel."""
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
        
        # Verificar consistencia de progresión
        if not await self._validate_level_progression(min_besitos, order, level_id):
            return False, f"Level progression would be inconsistent with order={order}"
        
        return True, "OK"
    
    async def _validate_level_progression(
        self,
        min_besitos: int,
        order: int,
        level_id: Optional[int] = None
    ) -> bool:
        """Valida que la progresión de niveles sea consistente."""
        # Verificar si hay otro nivel con el mismo order (excepto el actual)
        stmt = select(func.count()).select_from(Level).where(
            Level.order == order
        )
        if level_id:
            stmt = stmt.where(Level.id != level_id)
        result = await self.session.execute(stmt)
        if result.scalar() > 0:
            return False  # Order debe ser único

        # Verificar si hay otro nivel con el mismo min_besitos (excepto el actual)
        stmt = select(func.count()).select_from(Level).where(
            Level.min_besitos == min_besitos
        )
        if level_id:
            stmt = stmt.where(Level.id != level_id)
        result = await self.session.execute(stmt)
        if result.scalar() > 0:
            return False  # min_besitos debe ser único

        return True