"""Configuración del módulo de gamificación.

Gestiona:
- Variables de entorno (.env) para configuración estática
- Configuración dinámica desde base de datos (GamificationConfig)
- Cache de configuración con TTL
- Validación de parámetros
"""

from dotenv import load_dotenv
import os
import logging
from time import time
from typing import Optional, Tuple

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class GamificationConfig:
    """Configuración híbrida del módulo de gamificación.

    Combina variables de entorno (estáticas, instalación)
    con configuración de base de datos (dinámica, editable por admin).
    """

    # ========================================
    # ENVIRONMENT VARIABLES (estáticas)
    # ========================================

    # Activación del módulo
    ENABLED: bool = os.getenv("GAMIFICATION_ENABLED", "true").lower() == "true"

    # Límites globales anti-spam
    MAX_BESITOS_PER_DAY: int = int(os.getenv("GAMIFICATION_MAX_BESITOS_PER_DAY", "1000"))
    MAX_STREAK_DAYS: int = int(os.getenv("GAMIFICATION_MAX_STREAK_DAYS", "365"))
    MIN_LEVEL_BESITOS: int = int(os.getenv("GAMIFICATION_MIN_LEVEL_BESITOS", "0"))

    # Features opcionales
    NOTIFICATIONS_ENABLED: bool = (
        os.getenv("GAMIFICATION_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    )
    LEADERBOARD_ENABLED: bool = (
        os.getenv("GAMIFICATION_LEADERBOARD_ENABLED", "true").lower() == "true"
    )
    TRANSFERS_ENABLED: bool = (
        os.getenv("GAMIFICATION_TRANSFERS_ENABLED", "false").lower() == "true"
    )

    # Performance
    CACHE_TTL_SECONDS: int = int(os.getenv("GAMIFICATION_CACHE_TTL_SECONDS", "300"))
    BATCH_SIZE: int = int(os.getenv("GAMIFICATION_BATCH_SIZE", "100"))

    # ========================================
    # DATABASE CONFIG (dinámica, cacheada)
    # ========================================

    _db_config_cache: dict = {}
    _cache_timestamp: float = 0

    @classmethod
    async def get_besitos_per_reaction(cls, session) -> int:
        """Obtiene besitos por reacción desde BD (con cache).

        Args:
            session: AsyncSession de SQLAlchemy

        Returns:
            Número de besitos por reacción (default: 1)
        """
        return await cls._get_db_value(session, "besitos_per_reaction", 1)

    @classmethod
    async def get_streak_reset_hours(cls, session) -> int:
        """Obtiene horas para resetear racha desde BD (con cache).

        Args:
            session: AsyncSession de SQLAlchemy

        Returns:
            Horas para resetear racha (default: 24)
        """
        return await cls._get_db_value(session, "streak_reset_hours", 24)

    @classmethod
    async def get_max_besitos_per_day_db(cls, session) -> Optional[int]:
        """Obtiene límite máximo de besitos por día desde BD.

        Args:
            session: AsyncSession de SQLAlchemy

        Returns:
            Límite máximo o None si no configurado
        """
        return await cls._get_db_value(session, "max_besitos_per_day", None)

    @classmethod
    async def are_notifications_enabled(cls, session) -> bool:
        """Obtiene si notificaciones están habilitadas desde BD.

        Args:
            session: AsyncSession de SQLAlchemy

        Returns:
            True si notificaciones están habilitadas
        """
        return await cls._get_db_value(session, "notifications_enabled", True)

    @classmethod
    async def _get_db_value(cls, session, key: str, default):
        """Helper genérico para obtener valores de BD con cache.

        Implementa patrón de cache con TTL:
        - Si cache expiró (TTL), refrescar desde BD
        - Retornar valor cacheado o default si falla

        Args:
            session: AsyncSession de SQLAlchemy
            key: Nombre del parámetro en BD
            default: Valor default si no existe

        Returns:
            Valor cacheado o default
        """
        # Refrescar cache si TTL expiró
        if time() - cls._cache_timestamp > cls.CACHE_TTL_SECONDS:
            await cls.refresh_db_config(session)

        # Retornar valor cacheado o default
        return cls._db_config_cache.get(key, default)

    @classmethod
    async def refresh_db_config(cls, session) -> None:
        """Refresca cache de configuración desde BD.

        Lee GamificationConfig (id=1) de la base de datos y actualiza
        el cache interno con los valores actuales.

        Args:
            session: AsyncSession de SQLAlchemy
        """
        try:
            from bot.gamification.database.models import GamificationConfig as DBConfig

            # Obtener configuración singleton (id=1)
            config = await session.get(DBConfig, 1)

            if config:
                # Actualizar cache
                cls._db_config_cache = {
                    "besitos_per_reaction": config.besitos_per_reaction,
                    "streak_reset_hours": config.streak_reset_hours,
                    "max_besitos_per_day": config.max_besitos_per_day,
                    "notifications_enabled": config.notifications_enabled,
                }
                cls._cache_timestamp = time()
                logger.debug(
                    f"Gamification config refreshed from DB. "
                    f"besitos_per_reaction={config.besitos_per_reaction}"
                )
            else:
                logger.warning(
                    "GamificationConfig (id=1) not found in DB, using defaults"
                )
                cls._cache_timestamp = time()

        except Exception as e:
            logger.warning(
                f"Failed to load gamification config from DB: {e}, using cached values"
            )

    @classmethod
    def validate(cls) -> Tuple[bool, str]:
        """Valida configuración del módulo.

        Verifica rangos válidos de parámetros y coherencia.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Validar MAX_BESITOS_PER_DAY
        if cls.MAX_BESITOS_PER_DAY < 1:
            return False, "GAMIFICATION_MAX_BESITOS_PER_DAY must be > 0"

        # Validar MAX_STREAK_DAYS
        if cls.MAX_STREAK_DAYS < 1:
            return False, "GAMIFICATION_MAX_STREAK_DAYS must be > 0"

        # Validar MIN_LEVEL_BESITOS
        if cls.MIN_LEVEL_BESITOS < 0:
            return False, "GAMIFICATION_MIN_LEVEL_BESITOS must be >= 0"

        # Validar CACHE_TTL_SECONDS
        if cls.CACHE_TTL_SECONDS < 60:
            return False, "GAMIFICATION_CACHE_TTL_SECONDS must be >= 60"

        # Validar BATCH_SIZE
        if cls.BATCH_SIZE < 10 or cls.BATCH_SIZE > 1000:
            return False, "GAMIFICATION_BATCH_SIZE must be between 10-1000"

        return True, "OK"

    @classmethod
    def get_summary(cls) -> str:
        """Resumen de configuración para logging.

        Returns:
            String con resumen de parámetros principales
        """
        status = "ENABLED" if cls.ENABLED else "DISABLED"
        features = []

        if cls.NOTIFICATIONS_ENABLED:
            features.append("notifications")
        if cls.LEADERBOARD_ENABLED:
            features.append("leaderboard")
        if cls.TRANSFERS_ENABLED:
            features.append("transfers")

        features_str = ", ".join(features) if features else "none"

        return (
            f"[Gamification] {status}\n"
            f"  • Max besitos/day: {cls.MAX_BESITOS_PER_DAY}\n"
            f"  • Max streak: {cls.MAX_STREAK_DAYS} days\n"
            f"  • Cache TTL: {cls.CACHE_TTL_SECONDS}s\n"
            f"  • Features: {features_str}\n"
            f"  • Batch size: {cls.BATCH_SIZE}"
        )

    @classmethod
    def is_fully_configured(cls) -> bool:
        """Verifica si el módulo está completamente configurado.

        Returns:
            True si módulo está habilitado y validado
        """
        is_valid, _ = cls.validate()
        return cls.ENABLED and is_valid
