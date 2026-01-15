"""
Streak Service - Gestión de rachas basadas en publicaciones consecutivas.

Maneja:
- Cálculo de rachas (NO basado en días, sino en publicaciones)
- Actualización de rachas tras reacciones
- Multiplicador de puntos según racha
- Records de racha máxima
"""
import logging
from typing import Tuple, List

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from aiogram import Bot

from bot.database.gamification_models import Publication, UserReaction, UserPoints
from bot.database.enums import ChannelType

logger = logging.getLogger(__name__)


class StreakService:
    """
    Servicio para gestión de rachas de participación.

    Responsabilidades:
    - Calcular rachas basadas en publicaciones consecutivas
    - Actualizar rachas tras cada reacción
    - Aplicar multiplicadores de puntos según racha
    - Mantener registros de racha máxima

    Concepto de Racha:
    - NO se basa en días consecutivos
    - Se basa en publicaciones consecutivas reaccionadas
    - Ejemplo: Si hay 5 publicaciones [P1, P2, P3, P4, P5]
      y el usuario reaccionó a [P3, P4, P5], tiene racha de 3
    - Prioriza publicaciones más recientes (orden DESC)

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
        _bot: Instancia del bot de Telegram
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el StreakService.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        self._session = session
        self._bot = bot

    # ===== CÁLCULO DE RACHAS =====

    async def calculate_streak(
        self,
        user_id: int,
        channel_id: str
    ) -> int:
        """
        Calcula la racha actual de un usuario en un canal.

        La racha se basa en las últimas N publicaciones activas del canal.
        Cuenta cuántas publicaciones consecutivas (de las más recientes)
        tiene el usuario ha reaccionado.

        Args:
            user_id: ID del usuario
            channel_id: ID del canal

        Returns:
            int: Racha actual (0 si no tiene reacciones recientes)

        Ejemplo:
            Publicaciones en canal (orden DESC):
            [P5, P4, P3, P2, P1]

            Reacciones del usuario: [P5, P4, P3]
            → Racha = 3 (consecutivas desde la más reciente)

            Reacciones del usuario: [P5, P3]
            → Racha = 1 (P5 sí, P4 no → rompe la racha)
        """
        # Obtener últimas 50 publicaciones activas del canal
        result = await self._session.execute(
            select(Publication)
            .where(
                and_(
                    Publication.channel_id == channel_id,
                    Publication.active == True
                )
            )
            .order_by(desc(Publication.created_at))
            .limit(50)
        )
        publications = list(result.scalars().all())

        if not publications:
            return 0

        # Obtener IDs de publicaciones donde el usuario reaccionó
        pub_ids = [p.id for p in publications]
        result = await self._session.execute(
            select(UserReaction.publication_id)
            .where(
                and_(
                    UserReaction.user_id == user_id,
                    UserReaction.publication_id.in_(pub_ids)
                )
            )
        )
        reacted_ids = set(row[0] for row in result.all())

        # Calcular racha: cuántas publicaciones consecutivas
        # (desde la más reciente) tienen reacción
        streak = 0
        for publication in publications:
            if publication.id in reacted_ids:
                streak += 1
            else:
                # Rompe la racha
                break

        logger.debug(
            f"🔥 User {user_id} en canal {channel_id}: racha = {streak} "
            f"({len(publications)} publicaciones evaluadas)"
        )

        return streak

    async def calculate_global_streak(self, user_id: int) -> int:
        """
        Calcula la racha global de un usuario (todos los canales).

        Args:
            user_id: ID del usuario

        Returns:
            int: Racha global (máximo entre VIP y Free)
        """
        # Obtener canales desde config
        from bot.database.gamification_models import GamificationConfig

        result = await self._session.execute(
            select(GamificationConfig).where(GamificationConfig.id == 1)
        )
        config = result.scalar_one_or_none()

        if not config:
            return 0

        streaks = []

        # Calcular racha en cada canal configurado
        from bot.services.config import ConfigService
        config_service = ConfigService(self._session)

        vip_channel_id = await config_service.get_vip_channel_id()
        free_channel_id = await config_service.get_free_channel_id()

        if vip_channel_id:
            streak = await self.calculate_streak(user_id, vip_channel_id)
            streaks.append(streak)

        if free_channel_id:
            streak = await self.calculate_streak(user_id, free_channel_id)
            streaks.append(streak)

        # Retornar la máxima
        return max(streaks) if streaks else 0

    # ===== ACTUALIZACIÓN DE RACHAS =====

    async def update_streak_after_reaction(
        self,
        user_id: int,
        channel_id: str
    ) -> Tuple[int, bool]:
        """
        Actualiza la racha de un usuario después de reaccionar.

        Args:
            user_id: ID del usuario
            channel_id: ID del canal

        Returns:
            Tuple[int, bool]: (nueva_racha, es_nuevo_record)
        """
        # Calcular nueva racha
        new_streak = await self.calculate_streak(user_id, channel_id)

        # Obtener o crear UserPoints
        from bot.services.points import PointsService
        points_service = PointsService(self._session, self._bot)
        user_points = await points_service.get_or_create_points(user_id)

        old_max = user_points.max_streak
        is_new_record = new_streak > old_max

        # Actualizar rachas
        user_points.current_streak = new_streak
        if is_new_record:
            user_points.max_streak = new_streak

        await self._session.commit()

        if is_new_record:
            logger.info(
                f"🏆 User {user_id} NUEVO RÉCORD: racha {new_streak} "
                f"(anterior: {old_max})"
            )

        return new_streak, is_new_record

    async def update_global_streak_after_reaction(
        self,
        user_id: int,
        channel_id: str
    ) -> Tuple[int, bool]:
        """
        Actualiza la racha global de un usuario después de reaccionar.

        Args:
            user_id: ID del usuario
            channel_id: ID del canal donde reaccionó

        Returns:
            Tuple[int, bool]: (nueva_racha_global, es_nuevo_record)
        """
        # Actualizar racha del canal específico
        new_channel_streak, is_new_channel_record = await self.update_streak_after_reaction(
            user_id, channel_id
        )

        # Calcular racha global (máximo entre canales)
        global_streak = await self.calculate_global_streak(user_id)

        # Obtener UserPoints
        from bot.services.points import PointsService
        points_service = PointsService(self._session, self._bot)
        user_points = await points_service.get_or_create_points(user_id)

        old_max = user_points.max_streak
        is_new_global_record = global_streak > old_max

        if is_new_global_record:
            user_points.max_streak = global_streak
            await self._session.commit()

            logger.info(
                f"🏆 User {user_id} NUEVO RÉCORD GLOBAL: racha {global_streak} "
                f"(anterior: {old_max})"
            )

        return global_streak, is_new_global_record

    # ===== GETTERS =====

    async def get_current_streak(self, user_id: int) -> int:
        """
        Obtiene la racha actual de un usuario desde BD.

        Args:
            user_id: ID del usuario

        Returns:
            int: Racha actual almacenada (puede no estar actualizada)
        """
        from bot.services.points import PointsService
        points_service = PointsService(self._session, self._bot)
        user_points = await points_service.get_balance(user_id)

        if user_points is None:
            return 0

        return user_points.current_streak

    async def get_max_streak(self, user_id: int) -> int:
        """
        Obtiene la racha máxima histórica de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            int: Racha máxima
        """
        from bot.services.points import PointsService
        points_service = PointsService(self._session, self._bot)
        user_points = await points_service.get_balance(user_id)

        if user_points is None:
            return 0

        return user_points.max_streak

    # ===== MULTIPLICADOR =====

    async def get_streak_multiplier(self, streak: int) -> float:
        """
        Obtiene el multiplicador de puntos según la racha.

        Args:
            streak: Racha actual

        Returns:
            float: Multiplicador (ej: 1.5x para racha de 5)

        Tabla de multiplicadores:
        - Racha 0-4: 1.0x (sin bonificación)
        - Racha 5-9: 1.5x
        - Racha 10-19: 2.0x
        - Racha 20-29: 2.5x
        - Racha 30+: 3.0x

        Nota: Los valores base se configuran en GamificationConfig
        """
        if streak < 5:
            return 1.0
        elif streak < 10:
            return 1.5
        elif streak < 20:
            return 2.0
        elif streak < 30:
            return 2.5
        else:
            return 3.0

    async def get_configured_streak_multiplier(self) -> float:
        """
        Obtiene el multiplicador base configurado en GamificationConfig.

        Returns:
            float: Multiplicador base (ej: 1.5)
        """
        from bot.database.gamification_models import GamificationConfig

        result = await self._session.execute(
            select(GamificationConfig).where(GamificationConfig.id == 1)
        )
        config = result.scalar_one_or_none()

        if config:
            return config.streak_multiplier

        return 1.5  # Default

    # ===== ESTADÍSTICAS =====

    async def get_top_streak_users(self, limit: int = 10) -> List[Tuple[int, UserPoints]]:
        """
        Obtiene los usuarios con mayor racha actual.

        Args:
            limit: Máximo de resultados

        Returns:
            List[Tuple[int, UserPoints]]: Lista de (posición, UserPoints)
        """
        from bot.database.gamification_models import UserPoints

        result = await self._session.execute(
            select(UserPoints)
            .where(UserPoints.current_streak > 0)
            .order_by(desc(UserPoints.current_streak))
            .limit(limit)
        )
        points_list = list(result.scalars().all())

        return [(i + 1, points) for i, points in enumerate(points_list)]

    async def get_top_max_streak_users(self, limit: int = 10) -> List[UserPoints]:
        """
        Obtiene los usuarios con mayor racha máxima histórica.

        Args:
            limit: Máximo de resultados

        Returns:
            List[UserPoints]: Lista ordenada por max_streak
        """
        from bot.database.gamification_models import UserPoints

        result = await self._session.execute(
            select(UserPoints)
            .order_by(desc(UserPoints.max_streak))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def refresh_user_streak(self, user_id: int) -> int:
        """
        Refresca la racha de un usuario recalculándola desde cero.

        Útil para actualizar rachas que puedan estar desincronizadas.

        Args:
            user_id: ID del usuario

        Returns:
            int: Nueva racha actual
        """
        from bot.services.config import ConfigService
        config_service = ConfigService(self._session)

        # Obtener canales configurados
        vip_channel_id = await config_service.get_vip_channel_id()
        free_channel_id = await config_service.get_free_channel_id()

        max_streak = 0

        # Calcular racha en cada canal
        if vip_channel_id:
            streak = await self.calculate_streak(user_id, vip_channel_id)
            max_streak = max(max_streak, streak)

        if free_channel_id:
            streak = await self.calculate_streak(user_id, free_channel_id)
            max_streak = max(max_streak, streak)

        # Actualizar UserPoints
        from bot.services.points import PointsService
        points_service = PointsService(self._session, self._bot)
        user_points = await points_service.get_or_create_points(user_id)

        user_points.current_streak = max_streak
        if max_streak > user_points.max_streak:
            user_points.max_streak = max_streak

        await self._session.commit()

        logger.info(f"🔄 Racha de user {user_id} refrescada: {max_streak}")

        return max_streak
