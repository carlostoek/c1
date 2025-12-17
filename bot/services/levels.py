"""
Levels Service - Servicio de gestión de niveles del sistema de gamificación.

Gestiona:
- Verificación de level-up automático
- Consultas de nivel actual del usuario
- Cálculo de progreso hacia siguiente nivel
- Obtención de multiplicadores de nivel
- Información de niveles disponibles
- Cache de definiciones de niveles
"""
import logging
from typing import Optional, List, Tuple, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Level, UserProgress

logger = logging.getLogger(__name__)


class LevelsService:
    """
    Servicio de gestión de niveles.

    Responsabilidades:
    - Verificar si usuario alcanzó nuevo nivel
    - Obtener información de nivel actual
    - Calcular progreso hacia siguiente nivel
    - Proporcionar multiplicador de nivel
    - Consultar niveles disponibles
    - Gestionar cache de definiciones de niveles

    Atributos:
        session: Sesión de base de datos async
        bot: Instancia del bot (opcional)
        _levels_cache: Cache de niveles para optimizar queries
    """

    def __init__(self, session: AsyncSession, bot=None):
        """
        Inicializa el servicio de niveles.

        Args:
            session: Sesión de base de datos async
            bot: Instancia del bot (opcional)
        """
        self._session = session
        self._bot = bot
        self._logger = logging.getLogger(__name__)

        # Cache de niveles (se carga una vez y se reutiliza)
        self._levels_cache: Optional[List[Level]] = None

    # ===== MÉTODOS DE CONSULTA DE NIVELES =====

    async def get_all_levels(self, use_cache: bool = True) -> List[Level]:
        """
        Obtiene todos los niveles del sistema.

        Args:
            use_cache: Usar cache si está disponible (default: True)

        Returns:
            Lista de niveles ordenados por level ASC

        Raises:
            Ninguna, retorna lista vacía si hay error
        """
        try:
            # Usar cache si está disponible y se permite
            if use_cache and self._levels_cache is not None:
                return self._levels_cache

            # Cargar desde BD
            result = await self._session.execute(
                select(Level).order_by(Level.level)
            )
            levels = result.scalars().all()

            # Guardar en cache
            self._levels_cache = list(levels)

            self._logger.debug(f"Cargados {len(levels)} niveles del sistema")
            return list(levels)

        except Exception as e:
            self._logger.error(f"❌ Error obteniendo niveles: {e}", exc_info=True)
            return []

    async def get_level_by_number(self, level_number: int) -> Optional[Level]:
        """
        Obtiene un nivel específico por su número.

        Args:
            level_number: Número de nivel (1-7)

        Returns:
            Level si existe, None si no encontrado o hay error

        Example:
            >>> level = await service.get_level_by_number(5)
            >>> print(level.display_name)
            "🌟 Experto"
        """
        try:
            all_levels = await self.get_all_levels()

            for level in all_levels:
                if level.level == level_number:
                    return level

            self._logger.warning(f"⚠️ Nivel {level_number} no encontrado")
            return None

        except Exception as e:
            self._logger.error(
                f"❌ Error obteniendo nivel {level_number}: {e}",
                exc_info=True
            )
            return None

    async def get_level_for_points(self, points: int) -> Optional[Level]:
        """
        Obtiene el nivel correspondiente a una cantidad de puntos.

        Args:
            points: Cantidad total de puntos

        Returns:
            Level correspondiente o None si hay error

        Example:
            >>> level = await service.get_level_for_points(150)
            >>> print(level.name)
            "Aprendiz"
        """
        try:
            all_levels = await self.get_all_levels()

            for level in all_levels:
                if level.is_in_range(points):
                    return level

            # Si no encontró ninguno, retornar nivel máximo
            self._logger.warning(
                f"⚠️ No se encontró nivel para {points} puntos, "
                f"retornando nivel máximo"
            )
            return all_levels[-1] if all_levels else None

        except Exception as e:
            self._logger.error(
                f"❌ Error obteniendo nivel para {points} puntos: {e}",
                exc_info=True
            )
            return None

    async def get_level_multiplier(self, level_number: int) -> float:
        """
        Obtiene el multiplicador de un nivel específico.

        Args:
            level_number: Número de nivel (1-7)

        Returns:
            Multiplicador (1.0 si no encuentra)

        Example:
            >>> mult = await service.get_level_multiplier(7)
            >>> print(mult)
            2.0
        """
        level = await self.get_level_by_number(level_number)

        if level:
            return level.multiplier

        self._logger.warning(
            f"⚠️ No se encontró nivel {level_number}, "
            f"retornando multiplicador neutro (1.0)"
        )
        return 1.0

    # ===== MÉTODOS DE VERIFICACIÓN DE LEVEL-UP =====

    async def check_level_up(
        self,
        user_id: int,
        current_points: int
    ) -> Tuple[bool, Optional[Level], Optional[Level]]:
        """
        Verifica si un usuario debe subir de nivel.

        Compara el nivel actual del usuario con el que debería tener
        según sus puntos totales actuales.

        Args:
            user_id: ID del usuario
            current_points: Puntos totales actuales

        Returns:
            Tupla (should_level_up, old_level, new_level)
            - should_level_up: True si debe subir de nivel
            - old_level: Level actual del usuario
            - new_level: Level que debería tener

        Example:
            >>> should_up, old, new = await service.check_level_up(123, 150)
            >>> if should_up:
            ...     print(f"Level up! {old.name} → {new.name}")
        """
        try:
            # Obtener progreso del usuario
            result = await self._session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()

            if not progress:
                self._logger.warning(
                    f"⚠️ UserProgress no encontrado para user {user_id}"
                )
                return (False, None, None)

            # Obtener definiciones de niveles
            current_level_def = await self.get_level_by_number(progress.current_level)
            target_level_def = await self.get_level_for_points(current_points)

            if not current_level_def or not target_level_def:
                self._logger.error("❌ No se pudieron obtener definiciones de niveles")
                return (False, None, None)

            # Verificar si debe subir
            if target_level_def.level > current_level_def.level:
                self._logger.info(
                    f"🆙 Level-up detectado: user {user_id} "
                    f"{current_level_def.display_name} → {target_level_def.display_name}"
                )
                return (True, current_level_def, target_level_def)

            # No hay level-up
            return (False, current_level_def, current_level_def)

        except Exception as e:
            self._logger.error(
                f"❌ Error verificando level-up para user {user_id}: {e}",
                exc_info=True
            )
            return (False, None, None)

    async def apply_level_up(
        self,
        user_id: int,
        new_level_number: int
    ) -> bool:
        """
        Aplica el level-up actualizando el UserProgress.

        Args:
            user_id: ID del usuario
            new_level_number: Nuevo número de nivel

        Returns:
            True si se aplicó exitosamente, False si hubo error

        Raises:
            Ninguna, retorna False si hay error
        """
        try:
            # Obtener progreso del usuario
            result = await self._session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()

            if not progress:
                self._logger.warning(
                    f"⚠️ UserProgress no encontrado para user {user_id}"
                )
                return False

            # Actualizar nivel
            progress.current_level = new_level_number
            await self._session.commit()

            self._logger.info(
                f"✅ Level-up aplicado: user {user_id} → nivel {new_level_number}"
            )
            return True

        except Exception as e:
            self._logger.error(
                f"❌ Error aplicando level-up para user {user_id}: {e}",
                exc_info=True
            )
            await self._session.rollback()
            return False

    # ===== MÉTODOS DE PROGRESO =====

    async def get_user_level_info(
        self,
        user_id: int
    ) -> Optional[Dict]:
        """
        Obtiene información completa del nivel actual de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con información de nivel o None si no existe

        Example:
            >>> info = await service.get_user_level_info(123)
            >>> print(info)
            {
                'current_level': 3,
                'level_name': 'Competente',
                'level_icon': '💪',
                'display_name': '💪 Competente',
                'multiplier': 1.2,
                'min_points': 250,
                'max_points': 499,
                'perks': ['...'],
                'is_max_level': False
            }
        """
        try:
            result = await self._session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()

            if not progress:
                return None

            level_def = await self.get_level_by_number(progress.current_level)

            if not level_def:
                return None

            return {
                "current_level": level_def.level,
                "level_name": level_def.name,
                "level_icon": level_def.icon,
                "display_name": level_def.display_name,
                "multiplier": level_def.multiplier,
                "min_points": level_def.min_points,
                "max_points": level_def.max_points,
                "perks": level_def.perks or [],
                "is_max_level": level_def.max_points is None
            }

        except Exception as e:
            self._logger.error(f"❌ Error obteniendo info de nivel: {e}", exc_info=True)
            return None

    async def calculate_progress_to_next_level(
        self,
        user_id: int,
        total_points: int
    ) -> Optional[Dict]:
        """
        Calcula el progreso hacia el siguiente nivel.

        Args:
            user_id: ID del usuario
            total_points: Total de puntos acumulados

        Returns:
            Dict con progreso o None si hay error

        Example:
            >>> progress = await service.calculate_progress_to_next_level(123, 350)
            >>> print(progress)
            {
                'current_level': 3,
                'next_level': 4,
                'current_points': 350,
                'points_in_current_level': 100,
                'points_needed_for_next': 150,
                'total_points_in_level': 250,
                'progress_percentage': 40.0,
                'is_max_level': False
            }
        """
        try:
            current_level_def = await self.get_level_for_points(total_points)

            if not current_level_def:
                return None

            # Si es nivel máximo
            if current_level_def.max_points is None:
                return {
                    "current_level": current_level_def.level,
                    "next_level": None,
                    "current_points": total_points,
                    "points_in_current_level": total_points - current_level_def.min_points,
                    "points_needed_for_next": 0,
                    "total_points_in_level": 0,
                    "progress_percentage": 100.0,
                    "is_max_level": True
                }

            # Obtener siguiente nivel
            next_level_def = await self.get_level_by_number(
                current_level_def.level + 1
            )

            if not next_level_def:
                return None

            # Calcular progreso
            points_in_current = total_points - current_level_def.min_points
            points_needed = next_level_def.min_points - total_points
            total_points_in_level = (
                current_level_def.max_points - current_level_def.min_points + 1
            )

            progress_percentage = (points_in_current / total_points_in_level) * 100

            return {
                "current_level": current_level_def.level,
                "next_level": next_level_def.level,
                "current_points": total_points,
                "points_in_current_level": points_in_current,
                "points_needed_for_next": points_needed,
                "total_points_in_level": total_points_in_level,
                "progress_percentage": round(progress_percentage, 1),
                "is_max_level": False
            }

        except Exception as e:
            self._logger.error(f"❌ Error calculando progreso: {e}", exc_info=True)
            return None

    async def get_next_level_info(
        self,
        current_level_number: int
    ) -> Optional[Dict]:
        """
        Obtiene información del siguiente nivel.

        Args:
            current_level_number: Número del nivel actual

        Returns:
            Dict con info del siguiente nivel o None si es nivel máximo

        Example:
            >>> next_info = await service.get_next_level_info(3)
            >>> print(next_info)
            {
                'level': 4,
                'name': 'Avanzado',
                'icon': '🎯',
                'display_name': '🎯 Avanzado',
                'min_points': 500,
                'multiplier': 1.3,
                'perks': ['...']
            }
        """
        try:
            if current_level_number >= 7:
                return None  # Ya es nivel máximo

            next_level = await self.get_level_by_number(current_level_number + 1)

            if not next_level:
                return None

            return {
                "level": next_level.level,
                "name": next_level.name,
                "icon": next_level.icon,
                "display_name": next_level.display_name,
                "min_points": next_level.min_points,
                "multiplier": next_level.multiplier,
                "perks": next_level.perks or []
            }

        except Exception as e:
            self._logger.error(f"❌ Error obteniendo siguiente nivel: {e}", exc_info=True)
            return None

    async def clear_cache(self) -> None:
        """
        Limpia el cache de niveles.

        Útil cuando se agregan/modifican niveles y se necesita recargar.
        """
        self._levels_cache = None
        self._logger.debug("🧹 Cache de niveles limpiado")
