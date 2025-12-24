# PROMPT G2.7: GamificationContainer - Dependency Injection

---

## ROL

Actúa como Ingeniero de Software Senior especializado en patrones de diseño, Dependency Injection y gestión de ciclo de vida de servicios.

---

## TAREA

Implementa el contenedor de servicios `GamificationContainer` en `bot/gamification/services/container.py` que gestiona las dependencias entre servicios del módulo usando lazy loading y singleton pattern.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/services/
├── container.py           # ← ESTE ARCHIVO
├── reaction.py           # ReactionService
├── besito.py             # BesitoService
├── level.py              # LevelService
├── mission.py            # MissionService
├── reward.py             # RewardService
└── user_gamification.py  # UserGamificationService
```

### Patrón del Sistema Core (Referencia)
```python
# bot/services/container.py (sistema core)

class ServiceContainer:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._subscription_service = None
        self._channel_service = None
    
    @property
    def subscription(self) -> SubscriptionService:
        if self._subscription_service is None:
            self._subscription_service = SubscriptionService(self._session)
        return self._subscription_service
```

---

## RESTRICCIONES TÉCNICAS

### Lazy Loading
- Servicios NO se instancian al crear container
- Solo se crean cuando se acceden por primera vez
- Reduce uso de memoria inicial

### Singleton per Session
- Un container por sesión de BD
- Servicios se reutilizan dentro de la misma sesión
- Previene múltiples instancias del mismo servicio

### Dependencias Circulares
Los servicios tienen dependencias entre sí:
```
ReactionService → BesitoService (otorgar besitos)
MissionService → BesitoService, LevelService (recompensas)
RewardService → BesitoService (compras)
```

Solución: Acceso al container global cuando sea necesario

---

## SERVICIOS A GESTIONAR

```python
class GamificationContainer:
    """
    Contenedor de servicios de gamificación.
    
    Implementa lazy loading para reducir memoria.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        
        # Servicios (lazy loaded)
        self._reaction_service: Optional[ReactionService] = None
        self._besito_service: Optional[BesitoService] = None
        self._level_service: Optional[LevelService] = None
        self._mission_service: Optional[MissionService] = None
        self._reward_service: Optional[RewardService] = None
        self._user_gamification_service: Optional[UserGamificationService] = None
    
    @property
    def reaction(self) -> ReactionService:
        """Servicio de reacciones."""
        if self._reaction_service is None:
            from bot.gamification.services.reaction import ReactionService
            self._reaction_service = ReactionService(self._session)
        return self._reaction_service
    
    @property
    def besito(self) -> BesitoService:
        """Servicio de besitos."""
        if self._besito_service is None:
            from bot.gamification.services.besito import BesitoService
            self._besito_service = BesitoService(self._session)
        return self._besito_service
    
    @property
    def level(self) -> LevelService:
        """Servicio de niveles."""
        if self._level_service is None:
            from bot.gamification.services.level import LevelService
            self._level_service = LevelService(self._session)
        return self._level_service
    
    @property
    def mission(self) -> MissionService:
        """Servicio de misiones."""
        if self._mission_service is None:
            from bot.gamification.services.mission import MissionService
            self._mission_service = MissionService(self._session)
        return self._mission_service
    
    @property
    def reward(self) -> RewardService:
        """Servicio de recompensas."""
        if self._reward_service is None:
            from bot.gamification.services.reward import RewardService
            self._reward_service = RewardService(self._session)
        return self._reward_service
    
    @property
    def user_gamification(self) -> UserGamificationService:
        """Servicio de perfil de usuario."""
        if self._user_gamification_service is None:
            from bot.gamification.services.user_gamification import UserGamificationService
            self._user_gamification_service = UserGamificationService(self._session)
        return self._user_gamification_service
```

---

## INSTANCIA GLOBAL

Para resolver dependencias circulares, crear instancia global:

```python
# Variable global para acceso desde servicios
_container_instance: Optional[GamificationContainer] = None

def set_container(container: GamificationContainer):
    """Establece container global."""
    global _container_instance
    _container_instance = container

def get_container() -> GamificationContainer:
    """Obtiene container global."""
    if _container_instance is None:
        raise RuntimeError("Container not initialized")
    return _container_instance

# Alias para conveniencia
gamification_container = property(lambda self: get_container())
```

---

## MÉTODOS DE UTILIDAD

```python
def get_loaded_services(self) -> List[str]:
    """
    Retorna lista de servicios cargados.
    Útil para debugging y monitoreo de memoria.
    """
    loaded = []
    if self._reaction_service is not None:
        loaded.append('reaction')
    if self._besito_service is not None:
        loaded.append('besito')
    # ... resto de servicios
    return loaded

def clear_cache(self):
    """
    Limpia servicios cargados.
    Útil para testing.
    """
    self._reaction_service = None
    self._besito_service = None
    self._level_service = None
    self._mission_service = None
    self._reward_service = None
    self._user_gamification_service = None
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/container.py

"""
Contenedor de servicios de gamificación.

Implementa Dependency Injection con lazy loading para gestionar
el ciclo de vida de los servicios del módulo.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession


class GamificationContainer:
    """Contenedor de servicios con lazy loading."""
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa container.
        
        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session
        
        # Servicios (lazy loaded)
        self._reaction_service = None
        self._besito_service = None
        self._level_service = None
        self._mission_service = None
        self._reward_service = None
        self._user_gamification_service = None
    
    # ========================================
    # PROPERTIES (LAZY LOADING)
    # ========================================
    
    @property
    def reaction(self):
        """Servicio de reacciones."""
        if self._reaction_service is None:
            from bot.gamification.services.reaction import ReactionService
            self._reaction_service = ReactionService(self._session)
        return self._reaction_service
    
    @property
    def besito(self):
        """Servicio de besitos."""
        if self._besito_service is None:
            from bot.gamification.services.besito import BesitoService
            self._besito_service = BesitoService(self._session)
        return self._besito_service
    
    @property
    def level(self):
        """Servicio de niveles."""
        if self._level_service is None:
            from bot.gamification.services.level import LevelService
            self._level_service = LevelService(self._session)
        return self._level_service
    
    @property
    def mission(self):
        """Servicio de misiones."""
        if self._mission_service is None:
            from bot.gamification.services.mission import MissionService
            self._mission_service = MissionService(self._session)
        return self._mission_service
    
    @property
    def reward(self):
        """Servicio de recompensas."""
        if self._reward_service is None:
            from bot.gamification.services.reward import RewardService
            self._reward_service = RewardService(self._session)
        return self._reward_service
    
    @property
    def user_gamification(self):
        """Servicio de perfil de usuario."""
        if self._user_gamification_service is None:
            from bot.gamification.services.user_gamification import UserGamificationService
            self._user_gamification_service = UserGamificationService(self._session)
        return self._user_gamification_service
    
    # ========================================
    # UTILIDADES
    # ========================================
    
    def get_loaded_services(self) -> List[str]:
        """Retorna servicios actualmente cargados."""
        loaded = []
        if self._reaction_service is not None:
            loaded.append('reaction')
        if self._besito_service is not None:
            loaded.append('besito')
        if self._level_service is not None:
            loaded.append('level')
        if self._mission_service is not None:
            loaded.append('mission')
        if self._reward_service is not None:
            loaded.append('reward')
        if self._user_gamification_service is not None:
            loaded.append('user_gamification')
        return loaded
    
    def clear_cache(self):
        """Limpia todos los servicios cargados."""
        self._reaction_service = None
        self._besito_service = None
        self._level_service = None
        self._mission_service = None
        self._reward_service = None
        self._user_gamification_service = None


# ========================================
# INSTANCIA GLOBAL
# ========================================

_container_instance: Optional[GamificationContainer] = None


def set_container(container: GamificationContainer):
    """Establece container global para acceso desde servicios."""
    global _container_instance
    _container_instance = container


def get_container() -> GamificationContainer:
    """Obtiene container global."""
    if _container_instance is None:
        raise RuntimeError("GamificationContainer not initialized. Call set_container() first.")
    return _container_instance


# Alias para conveniencia
class _ContainerProxy:
    """Proxy para acceso conveniente al container."""
    
    def __getattr__(self, name):
        return getattr(get_container(), name)


gamification_container = _ContainerProxy()
```

---

## INTEGRACIÓN EN MIDDLEWARE

```python
# bot/middlewares/database.py (modificar)

from bot.gamification.services.container import GamificationContainer, set_container

class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data['session'] = session
            
            # Crear containers
            data['container'] = ServiceContainer(session)
            
            # NUEVO: Container de gamificación
            gamif_container = GamificationContainer(session)
            set_container(gamif_container)  # Establecer global
            data['gamification'] = gamif_container
            
            return await handler(event, data)
```

---

## USO EN HANDLERS

```python
# Opción 1: Via middleware
@router.message(Command("profile"))
async def show_profile(message: Message, gamification: GamificationContainer):
    profile = await gamification.user_gamification.get_profile_summary(
        message.from_user.id
    )
    await message.answer(profile)

# Opción 2: Via global (dentro de servicios)
# bot/gamification/services/reaction.py
from bot.gamification.services.container import gamification_container

async def record_reaction(...):
    # Acceder a otros servicios
    await gamification_container.besito.grant_besitos(...)
```

---

## VALIDACIÓN

- ✅ Lazy loading implementado
- ✅ 6 servicios gestionados
- ✅ Instancia global para dependencias circulares
- ✅ Métodos de utilidad (get_loaded_services, clear_cache)
- ✅ Imports dentro de properties (evitar circulares)
- ✅ Docstrings en clase y métodos

---

**ENTREGABLE:** Archivo `container.py` completo con DI y lazy loading.
