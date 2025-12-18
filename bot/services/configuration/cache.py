"""
Cache System para ConfigurationService.

Implementa cache en memoria con TTL y invalidación manual.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Entrada de cache con metadata."""
    value: T
    created_at: datetime
    ttl_seconds: int
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)


class ConfigCache:
    """
    Cache en memoria para configuración de gamificación.
    
    Features:
    - TTL configurable por tipo de dato
    - Invalidación manual por key o grupo
    - Thread-safe para uso básico
    - Métricas de hits/misses
    
    Usage:
        cache = ConfigCache()
        
        # Set
        cache.set("actions", actions_list, ttl=300)
        
        # Get
        data = cache.get("actions")  # None si expiró o no existe
        
        # Invalidate
        cache.invalidate("actions")
        cache.invalidate_group("levels")  # invalida levels:*
    """
    
    # TTL defaults en segundos
    DEFAULT_TTL = 300  # 5 minutos
    TTL_BY_TYPE = {
        "actions": 300,
        "levels": 300,
        "badges": 300,
        "rewards": 300,
        "missions": 300,
        "action_points": 60,  # Cache más corto para puntos específicos
    }
    
    def __init__(self):
        """Inicializa el cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        logger.debug("✅ ConfigCache inicializado")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene valor del cache.
        
        Args:
            key: Clave del cache
            
        Returns:
            Valor cacheado o None si no existe/expiró
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            logger.debug(f"🕐 Cache expirado: {key}")
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Guarda valor en cache.
        
        Args:
            key: Clave del cache
            value: Valor a guardar
            ttl: TTL en segundos (opcional, usa default por tipo)
        """
        # Determinar TTL
        if ttl is None:
            # Intentar obtener TTL por tipo (prefijo del key)
            key_type = key.split(":")[0] if ":" in key else key
            ttl = self.TTL_BY_TYPE.get(key_type, self.DEFAULT_TTL)
        
        self._cache[key] = CacheEntry(
            value=value,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl
        )
        logger.debug(f"💾 Cache set: {key} (TTL={ttl}s)")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalida una entrada específica.
        
        Args:
            key: Clave a invalidar
            
        Returns:
            True si existía y se eliminó
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"🗑️ Cache invalidado: {key}")
            return True
        return False
    
    def invalidate_group(self, prefix: str) -> int:
        """
        Invalida todas las entradas que comienzan con el prefijo.
        
        Args:
            prefix: Prefijo de las claves a invalidar
            
        Returns:
            Número de entradas eliminadas
        """
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]
        
        if keys_to_delete:
            logger.debug(f"🗑️ Cache grupo invalidado: {prefix}* ({len(keys_to_delete)} entradas)")
        
        return len(keys_to_delete)
    
    def invalidate_all(self) -> int:
        """
        Invalida todo el cache.
        
        Returns:
            Número de entradas eliminadas
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"🗑️ Cache completamente invalidado ({count} entradas)")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Dict con hits, misses, ratio, entries
        """
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": self._hits / total if total > 0 else 0,
            "entries": len(self._cache),
            "keys": list(self._cache.keys()),
        }
    
    def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas.
        
        Returns:
            Número de entradas eliminadas
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"🧹 Limpieza de cache: {len(expired_keys)} expiradas")
        
        return len(expired_keys)


# Instancia global del cache
_config_cache: Optional[ConfigCache] = None


def get_config_cache() -> ConfigCache:
    """
    Obtiene la instancia global del cache.
    
    Returns:
        ConfigCache singleton
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = ConfigCache()
    return _config_cache


def reset_config_cache() -> None:
    """Resetea el cache global (útil para tests)."""
    global _config_cache
    if _config_cache:
        _config_cache.invalidate_all()
    _config_cache = None