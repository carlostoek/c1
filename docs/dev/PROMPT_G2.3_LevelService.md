# PROMPT G2.3: LevelService - Gestión de Niveles

---

## ROL

Actúa como Ingeniero de Software Senior especializado en sistemas de progresión, gamificación y cálculo de niveles basados en métricas.

---

## TAREA

Implementa el servicio `LevelService` en `bot/gamification/services/level.py` que gestiona niveles del sistema, cálculo automático de level-ups, y progresión de usuarios.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/services/
├── level.py           # ← ESTE ARCHIVO
├── besito.py          # Ya existe
├── reaction.py        # Ya existe
└── container.py       # GamificationContainer
```

### Modelos Relevantes
```python
class Level(Base):
    id: Mapped[int]
    name: Mapped[str]              # "Novato", "Fanático"
    min_besitos: Mapped[int]       # Mínimo de besitos para alcanzar
    order: Mapped[int]             # 1, 2, 3... (orden de progresión)
    benefits: Mapped[str]          # JSON con beneficios
    active: Mapped[bool]

class UserGamification(Base):
    user_id: Mapped[int]
    total_besitos: Mapped[int]
    current_level_id: Mapped[int]  # FK a Level
```

---

## RESTRICCIONES TÉCNICAS

### Lógica de Level-Up

```python
# Regla: Usuario debe estar en el nivel más alto que pueda según sus besitos
# Ejemplo:
# Niveles: Novato (0), Regular (500), Fanático (2000)
# User con 1500 besitos → debe estar en "Regular"

# Algoritmo:
# 1. Ordenar niveles activos por min_besitos DESC
# 2. Iterar hasta encontrar primer nivel donde user.besitos >= level.min_besitos
# 3. Actualizar current_level_id si cambió
```

### Auto Level-Up

El servicio debe detectar automáticamente cuándo un usuario sube de nivel:

```python
async def check_and_apply_level_up(user_id: int) -> tuple[bool, Optional[Level], Optional[Level]]
"""
Verifica si usuario debe subir de nivel y lo aplica.

Returns:
    (changed, old_level, new_level)
"""
```

---

## RESPONSABILIDADES DEL SERVICIO

### 1. CRUD de Niveles

```python
async def create_level(
    name: str, 
    min_besitos: int, 
    order: int,
    benefits: Optional[dict] = None
) -> Level

async def update_level(
    level_id: int,
    name: Optional[str] = None,
    min_besitos: Optional[int] = None,
    order: Optional[int] = None,
    benefits: Optional[dict] = None,
    active: Optional[bool] = None
) -> Level

async def delete_level(level_id: int) -> bool
"""Soft-delete (active=False)"""

async def get_all_levels(active_only: bool = True) -> List[Level]
"""Ordenados por 'order' ASC"""

async def get_level_by_id(level_id: int) -> Optional[Level]
```

### 2. Cálculo de Niveles

```python
async def calculate_level_for_besitos(besitos: int) -> Optional[Level]
"""
Calcula qué nivel corresponde a cierta cantidad de besitos.

Lógica:
- Obtener niveles activos ordenados por min_besitos DESC
- Retornar primer nivel donde besitos >= min_besitos
"""

async def get_next_level(current_level_id: int) -> Optional[Level]
"""Retorna siguiente nivel en progresión (order + 1)"""

async def get_besitos_to_next_level(user_id: int) -> Optional[int]
"""
Calcula cuántos besitos faltan para siguiente nivel.

Returns:
    None si ya está en nivel máximo
    int con besitos faltantes
"""
```

### 3. Aplicación de Level-Ups

```python
async def check_and_apply_level_up(
    user_id: int
) -> tuple[bool, Optional[Level], Optional[Level]]
"""
Verifica y aplica level-up automático.

Flujo:
1. Obtener UserGamification
2. Calcular nivel que debería tener según besitos
3. Si nivel calculado != nivel actual → aplicar cambio
4. Retornar información del cambio

Returns:
    (changed, old_level, new_level)
"""

async def set_user_level(user_id: int, level_id: int) -> bool
"""Fuerza nivel específico (admin override)"""
```

### 4. Progresión de Usuario

```python
async def get_user_level_progress(user_id: int) -> dict
"""
Retorna información completa de progresión.

Returns:
    {
        'current_level': Level,
        'next_level': Optional[Level],
        'current_besitos': int,
        'besitos_to_next': Optional[int],
        'progress_percentage': float  # 0-100
    }
"""
```

### 5. Estadísticas

```python
async def get_level_distribution() -> dict
"""
Distribución de usuarios por nivel.

Returns:
    {
        'Novato': 150,
        'Regular': 75,
        'Fanático': 20
    }
"""

async def get_users_in_level(level_id: int, limit: int = 50) -> List[UserGamification]
"""Lista usuarios en un nivel específico"""
```

---

## VALIDACIONES

### Al Crear/Editar Niveles

```python
# Validaciones obligatorias:
1. min_besitos >= 0
2. order > 0
3. name único
4. No puede haber dos niveles con mismo min_besitos
5. Si se edita min_besitos, verificar que no rompe progresión
```

### Progresión Consistente

```python
# Al crear nivel, validar:
async def _validate_level_progression(new_level: Level) -> tuple[bool, str]:
    """
    Verifica que nuevo nivel no rompe progresión.
    
    Reglas:
    - order debe ser único
    - min_besitos debe ser único
    - Si order=N, debe existir order=N-1
    """
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/level.py

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
    
    async def get_all_levels(self, active_only: bool = True) -> List[Level]:
        """Obtiene niveles ordenados por order ASC."""
        stmt = select(Level)
        if active_only:
            stmt = stmt.where(Level.active == True)
        stmt = stmt.order_by(Level.order.asc())
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
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
        
        return True, "OK"
```

---

## INTEGRACIÓN

```python
# bot/gamification/services/container.py

class GamificationContainer:
    @property
    def level(self) -> LevelService:
        if self._level_service is None:
            self._level_service = LevelService(self._session)
        return self._level_service
```

### Uso después de otorgar besitos

```python
# En BesitoService.grant_besitos(), después de actualizar besitos:
from bot.gamification.services.container import gamification_container

# Check level-up
changed, old_level, new_level = await gamification_container.level.check_and_apply_level_up(user_id)
if changed:
    logger.info(f"User {user_id} leveled up to {new_level.name}!")
```

---

## VALIDACIÓN

- ✅ CRUD completo de niveles
- ✅ Cálculo automático de level-ups
- ✅ Validación de progresión consistente
- ✅ Estadísticas por nivel
- ✅ Type hints completos
- ✅ Logging en operaciones importantes

---

**ENTREGABLE:** Archivo `level.py` completo con gestión de niveles y progresión automática.
