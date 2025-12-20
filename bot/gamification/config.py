# bot/gamification/config.py

"""
Configuración del módulo de gamificación.

Gestiona:
- Variables de entorno (.env)
- Configuración dinámica desde BD
- Cache de configuración
- Validación de parámetros
"""

from dotenv import load_dotenv
import os
import logging
from time import time
from typing import Optional, TYPE_CHECKING

# Importación condicional para evitar circular imports
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class GamificationConfig:
    """Configuración híbrida del módulo de gamificación."""
    
    # ========================================
    # ENVIRONMENT VARIABLES (estáticas)
    # ========================================
    
    # Activación del módulo
    ENABLED: bool = os.getenv("GAMIFICATION_ENABLED", "false").lower() == "true"
    
    # Límites globales
    MAX_BESITOS_PER_DAY: int = int(os.getenv("GAMIFICATION_MAX_BESITOS_PER_DAY", "1000"))
    MAX_STREAK_DAYS: int = int(os.getenv("GAMIFICATION_MAX_STREAK_DAYS", "365"))
    MIN_LEVEL_BESITOS: int = int(os.getenv("GAMIFICATION_MIN_LEVEL_BESITOS", "0"))
    
    # Features opcionales
    NOTIFICATIONS_ENABLED: bool = os.getenv("GAMIFICATION_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    LEADERBOARD_ENABLED: bool = os.getenv("GAMIFICATION_LEADERBOARD_ENABLED", "true").lower() == "true"
    TRANSFERS_ENABLED: bool = os.getenv("GAMIFICATION_TRANSFERS_ENABLED", "false").lower() == "true"
    
    # Performance
    CACHE_TTL_SECONDS: int = int(os.getenv("GAMIFICATION_CACHE_TTL_SECONDS", "300"))  # 5 minutos
    BATCH_SIZE: int = int(os.getenv("GAMIFICATION_BATCH_SIZE", "100"))
    
    # ========================================
    # DATABASE CONFIG (dinámica)
    # ========================================
    
    # Cache de valores de BD (clave: valor)
    _db_config_cache: dict = {}
    _cache_timestamp: float = 0
    
    @classmethod
    async def get_besitos_per_reaction(cls, session) -> int:
        """
        Obtiene besitos por reacción desde BD (con cache).
        
        Args:
            session: Sesión de SQLAlchemy para consulta a BD
            
        Returns:
            Cantidad de besitos por reacción (default: 1)
        """
        from bot.gamification.database.models import GamificationConfig as DBConfig
        
        # Si cache expiró, refrescar
        if time() - cls._cache_timestamp > cls.CACHE_TTL_SECONDS:
            await cls.refresh_db_config(session)
        
        # Retornar valor cacheado o default
        return cls._db_config_cache.get('besitos_per_reaction', 1)
    
    @classmethod
    async def get_streak_reset_hours(cls, session) -> int:
        """
        Obtiene horas para resetear racha desde BD (con cache).
        
        Args:
            session: Sesión de SQLAlchemy para consulta a BD
            
        Returns:
            Cantidad de horas para resetear racha (default: 24)
        """
        from bot.gamification.database.models import GamificationConfig as DBConfig
        
        # Si cache expiró, refrescar
        if time() - cls._cache_timestamp > cls.CACHE_TTL_SECONDS:
            await cls.refresh_db_config(session)
        
        # Retornar valor cacheado o default
        return cls._db_config_cache.get('streak_reset_hours', 24)
    
    @classmethod
    async def get_notifications_enabled(cls, session) -> bool:
        """
        Obtiene si las notificaciones están habilitadas desde BD (con cache).
        
        Args:
            session: Sesión de SQLAlchemy para consulta a BD
            
        Returns:
            True si las notificaciones están habilitadas
        """
        from bot.gamification.database.models import GamificationConfig as DBConfig
        
        # Si cache expiró, refrescar
        if time() - cls._cache_timestamp > cls.CACHE_TTL_SECONDS:
            await cls.refresh_db_config(session)
        
        # Retornar valor cacheado o default
        return cls._db_config_cache.get('notifications_enabled', True)
    
    @classmethod
    async def refresh_db_config(cls, session):
        """
        Refresca cache de configuración desde BD.
        
        Carga los valores de GamificationConfig (registro id=1) desde la base de datos
        y los cachea para evitar consultas repetidas.
        
        Args:
            session: Sesión de SQLAlchemy para consulta a BD
        """
        try:
            from bot.gamification.database.models import GamificationConfig as DBConfig
            
            # Consultar configuración de BD
            config = await session.get(DBConfig, 1)
            
            if config:
                cls._db_config_cache = {
                    'besitos_per_reaction': config.besitos_per_reaction,
                    'streak_reset_hours': config.streak_reset_hours,
                    'notifications_enabled': config.notifications_enabled,
                }
                cls._cache_timestamp = time()
                
                logger.debug("Gamification DB config refreshed from database")
            else:
                # Config no existe en BD, usar valores por defecto
                cls._db_config_cache = {
                    'besitos_per_reaction': 1,
                    'streak_reset_hours': 24,
                    'notifications_enabled': True,
                }
                cls._cache_timestamp = time()
                
                logger.warning("Gamification config not found in DB, using defaults")
                
        except Exception as e:
            logger.warning(f"Failed to load DB config: {e}, using defaults")
            # En caso de error, mantener valores anteriores o usar defaults
            if not cls._db_config_cache:
                cls._db_config_cache = {
                    'besitos_per_reaction': 1,
                    'streak_reset_hours': 24,
                    'notifications_enabled': True,
                }
                cls._cache_timestamp = time()
    
    @classmethod
    async def update_db_config(cls, session, **kwargs):
        """
        Actualiza configuración en BD y refresca cache.
        
        Args:
            session: Sesión de SQLAlchemy para actualización
            **kwargs: Valores a actualizar (ej: besitos_per_reaction=2)
        """
        try:
            from bot.gamification.database.models import GamificationConfig as DBConfig
            
            # Obtener o crear configuración (id=1)
            config = await session.get(DBConfig, 1)
            if not config:
                # Crear nueva configuración con valores por defecto
                config = DBConfig(
                    id=1,
                    besitos_per_reaction=1,
                    streak_reset_hours=24,
                    notifications_enabled=True
                )
                session.add(config)
            
            # Actualizar los campos proporcionados
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # Commit y refresh cache
            await session.commit()
            await cls.refresh_db_config(session)
            
            logger.info(f"Gamification DB config updated: {list(kwargs.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to update DB config: {e}")
            raise
    
    # ========================================
    # VALIDACIÓN
    # ========================================
    
    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """
        Valida configuración del módulo.
        
        Returns:
            (is_valid, error_message)
        """
        # Validar rangos
        if cls.MAX_BESITOS_PER_DAY < 1:
            return False, "MAX_BESITOS_PER_DAY must be > 0"
        
        if cls.MAX_STREAK_DAYS < 1:
            return False, "MAX_STREAK_DAYS must be > 0"
        
        if cls.MIN_LEVEL_BESITOS < 0:
            return False, "MIN_LEVEL_BESITOS must be >= 0"
        
        if cls.CACHE_TTL_SECONDS < 60:
            return False, "CACHE_TTL_SECONDS must be >= 60"
        
        if cls.BATCH_SIZE < 10 or cls.BATCH_SIZE > 10000:
            return False, "BATCH_SIZE must be between 10-10000"
        
        # Validar que límites razonables
        if cls.MAX_BESITOS_PER_DAY > 100000:
            return False, "MAX_BESITOS_PER_DAY seems too high (>100k)"
        
        if cls.MAX_STREAK_DAYS > 3650:  # 10 años
            return False, "MAX_STREAK_DAYS seems too high (>10 years)"
        
        return True, "OK"
    
    @classmethod
    def get_summary(cls) -> str:
        """
        Resumen de configuración para logging.
        
        Returns:
            String con valores de configuración importantes
        """
        return (
            f"Gamification Config: "
            f"ENABLED={cls.ENABLED}, "
            f"MAX_BESITOS_PER_DAY={cls.MAX_BESITOS_PER_DAY}, "
            f"MAX_STREAK_DAYS={cls.MAX_STREAK_DAYS}, "
            f"NOTIFICATIONS_ENABLED={cls.NOTIFICATIONS_ENABLED}, "
            f"LEADERBOARD_ENABLED={cls.LEADERBOARD_ENABLED}, "
            f"TRANSFERS_ENABLED={cls.TRANSFERS_ENABLED}, "
            f"CACHE_TTL={cls.CACHE_TTL_SECONDS}s"
        )
    
    @classmethod
    def get_db_config_summary(cls) -> str:
        """
        Resumen de configuración desde BD (cacheado).
        
        Returns:
            String con valores de configuración de BD
        """
        besitos = cls._db_config_cache.get('besitos_per_reaction', 'N/A')
        streak_hours = cls._db_config_cache.get('streak_reset_hours', 'N/A')
        notifications = cls._db_config_cache.get('notifications_enabled', 'N/A')
        
        return (
            f"DB Config (cached): "
            f"besitos_per_reaction={besitos}, "
            f"streak_reset_hours={streak_hours}, "
            f"notifications_enabled={notifications}"
        )
    
    @classmethod
    async def get_full_config(cls, session) -> dict:
        """
        Obtiene configuración completa (environment + BD).
        
        Args:
            session: Sesión de SQLAlchemy para consulta a BD
            
        Returns:
            Dict con toda la configuración
        """
        # Asegurar que cache esté actualizada
        if time() - cls._cache_timestamp > cls.CACHE_TTL_SECONDS:
            await cls.refresh_db_config(session)
        
        return {
            # Config estática (environment)
            'enabled': cls.ENABLED,
            'max_besitos_per_day': cls.MAX_BESITOS_PER_DAY,
            'max_streak_days': cls.MAX_STREAK_DAYS,
            'min_level_besitos': cls.MIN_LEVEL_BESITOS,
            'notifications_enabled_env': cls.NOTIFICATIONS_ENABLED,
            'leaderboard_enabled': cls.LEADERBOARD_ENABLED,
            'transfers_enabled': cls.TRANSFERS_ENABLED,
            'cache_ttl_seconds': cls.CACHE_TTL_SECONDS,
            'batch_size': cls.BATCH_SIZE,
            
            # Config dinámica (BD)
            'besitos_per_reaction': cls._db_config_cache.get('besitos_per_reaction', 1),
            'streak_reset_hours': cls._db_config_cache.get('streak_reset_hours', 24),
            'notifications_enabled_db': cls._db_config_cache.get('notifications_enabled', True),
            
            # Info de cache
            'cache_age_seconds': time() - cls._cache_timestamp,
            'cache_expires_in_seconds': max(0, cls.CACHE_TTL_SECONDS - (time() - cls._cache_timestamp))
        }