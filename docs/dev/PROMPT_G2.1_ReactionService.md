# PROMPT G2.1: ReactionService - Gestión de Reacciones

---

## ROL

Actúa como Ingeniero de Software Senior especializado en sistemas de eventos, procesamiento de reacciones y integración con Telegram API.

---

## TAREA

Implementa el servicio `ReactionService` en `bot/gamification/services/reaction.py` que gestiona el catálogo de reacciones configuradas, registro de reacciones de usuarios, y integración con el sistema de besitos y rachas.

---

## CONTEXTO

### Stack Tecnológico
- Python 3.11+ async/await
- SQLAlchemy 2.0 async
- Aiogram 3.4+ (callbacks de reacciones)

### Arquitectura
```
bot/gamification/services/
├── reaction.py          # ← ESTE ARCHIVO
├── besito.py           # BesitoService (ya existe)
├── container.py        # GamificationContainer
```

### Modelos Relevantes
```python
# bot/gamification/database/models.py

class Reaction(Base):
    """Catálogo de reacciones configuradas"""
    id: Mapped[int]
    emoji: Mapped[str]           # "❤️", "🔥", etc.
    besitos_value: Mapped[int]   # Cuántos besitos otorga
    active: Mapped[bool]

class UserReaction(Base):
    """Registro de cada reacción de usuario"""
    id: Mapped[int]
    user_id: Mapped[int]
    reaction_id: Mapped[int]
    channel_id: Mapped[int]      # Dónde reaccionó
    message_id: Mapped[int]      # A qué mensaje
    reacted_at: Mapped[datetime]

class UserStreak(Base):
    """Racha de reacciones del usuario"""
    user_id: Mapped[int]
    current_streak: Mapped[int]
    longest_streak: Mapped[int]
    last_reaction_date: Mapped[datetime]
```

---

## RESTRICCIONES TÉCNICAS

### Flujo de Reacción
```
1. Usuario reacciona en canal → Telegram callback
2. ReactionService.record_reaction(user_id, emoji, channel_id, message_id)
3. Validar que reacción existe y está activa
4. Crear UserReaction
5. Otorgar besitos (integración con BesitoService)
6. Actualizar racha (integración con streak logic)
7. Retornar besitos otorgados
```

### Anti-Spam
```python
# Validaciones obligatorias:
- Usuario no puede reaccionar al mismo mensaje múltiples veces
- Respetar límite diario (GamificationConfig.max_besitos_per_day)
- Solo reacciones activas otorgan besitos
```

### Integración con BesitoService
```python
# Después de crear UserReaction
from bot.gamification.services.besito import BesitoService
from bot.gamification.database.enums import TransactionType

besitos_granted = await besito_service.grant_besitos(
    user_id=user_id,
    amount=reaction.besitos_value,
    transaction_type=TransactionType.REACTION,
    description=f"Reacción {emoji} en canal {channel_id}",
    reference_id=user_reaction.id
)
```

---

## RESPONSABILIDADES DEL SERVICIO

### 1. Gestión de Catálogo de Reacciones

```python
async def create_reaction(emoji: str, besitos_value: int = 1) -> Reaction
async def update_reaction(reaction_id: int, besitos_value: int, active: bool) -> Reaction
async def delete_reaction(reaction_id: int) -> bool
async def get_all_reactions(active_only: bool = True) -> List[Reaction]
async def get_reaction_by_emoji(emoji: str) -> Optional[Reaction]
```

### 2. Registro de Reacciones de Usuario

```python
async def record_reaction(
    user_id: int, 
    emoji: str, 
    channel_id: int, 
    message_id: int
) -> tuple[bool, str, int]
"""
Registra reacción y otorga besitos.

Returns:
    (success, message, besitos_granted)
    
Validaciones:
- Reacción existe y está activa
- Usuario no reaccionó antes a este mensaje
- No excede límite diario de besitos
"""
```

### 3. Consultas de Historial

```python
async def get_user_reactions(
    user_id: int, 
    limit: int = 50,
    channel_id: Optional[int] = None
) -> List[UserReaction]

async def get_reaction_stats(user_id: int) -> dict
"""
Returns:
    {
        'total_reactions': int,
        'reactions_by_emoji': {'❤️': 10, '🔥': 5},
        'total_besitos_from_reactions': int,
        'favorite_channel': int
    }
"""
```

### 4. Validaciones Anti-Spam

```python
async def _has_reacted_to_message(
    user_id: int, 
    message_id: int
) -> bool

async def _check_daily_limit(user_id: int) -> tuple[bool, int]
"""
Verifica si usuario puede seguir ganando besitos hoy.

Returns:
    (can_react, besitos_earned_today)
"""
```

---

## LÓGICA DE RACHAS

Implementar método auxiliar para actualizar rachas:

```python
async def _update_user_streak(user_id: int) -> UserStreak:
    """
    Actualiza racha del usuario.
    
    Lógica:
    1. Obtener UserStreak (crear si no existe)
    2. Comparar last_reaction_date con hoy
    3. Si es consecutivo → current_streak += 1
    4. Si saltó días → current_streak = 1
    5. Si current_streak > longest_streak → actualizar récord
    6. Actualizar last_reaction_date
    
    Returns:
        UserStreak actualizado
    """
    from datetime import datetime, UTC, timedelta
    
    # Obtener o crear streak
    streak = await self._get_or_create_streak(user_id)
    
    today = datetime.now(UTC).date()
    last_date = streak.last_reaction_date.date() if streak.last_reaction_date else None
    
    if last_date is None:
        # Primera reacción
        streak.current_streak = 1
    elif last_date == today:
        # Ya reaccionó hoy, no modificar streak
        pass
    elif last_date == today - timedelta(days=1):
        # Día consecutivo
        streak.current_streak += 1
    else:
        # Rompió racha
        streak.current_streak = 1
    
    # Actualizar récord
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak
    
    streak.last_reaction_date = datetime.now(UTC)
    await self.session.commit()
    
    return streak
```

---

## FORMATO DE SALIDA

Entrega el archivo completo `bot/gamification/services/reaction.py`:

```python
# bot/gamification/services/reaction.py

"""
Servicio de gestión de reacciones.

Responsabilidades:
- CRUD de catálogo de reacciones
- Registro de reacciones de usuarios
- Otorgamiento de besitos por reacciones
- Actualización de rachas
- Anti-spam y validaciones
"""

from typing import Optional, List, Tuple
from datetime import datetime, UTC, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import (
    Reaction, 
    UserReaction, 
    UserStreak,
    UserGamification
)
from bot.gamification.database.enums import TransactionType

logger = logging.getLogger(__name__)


class ReactionService:
    """Servicio de gestión de reacciones y rachas."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ========================================
    # CATÁLOGO DE REACCIONES
    # ========================================
    
    async def create_reaction(
        self, 
        emoji: str, 
        besitos_value: int = 1
    ) -> Reaction:
        """Crea nueva reacción en catálogo."""
        reaction = Reaction(
            emoji=emoji,
            besitos_value=besitos_value,
            active=True
        )
        self.session.add(reaction)
        await self.session.commit()
        await self.session.refresh(reaction)
        
        logger.info(f"Created reaction: {emoji} ({besitos_value} besitos)")
        return reaction
    
    async def get_all_reactions(
        self, 
        active_only: bool = True
    ) -> List[Reaction]:
        """Obtiene todas las reacciones."""
        stmt = select(Reaction)
        if active_only:
            stmt = stmt.where(Reaction.active == True)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_reaction_by_emoji(
        self, 
        emoji: str
    ) -> Optional[Reaction]:
        """Busca reacción por emoji."""
        stmt = select(Reaction).where(Reaction.emoji == emoji)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    # ========================================
    # REGISTRO DE REACCIONES
    # ========================================
    
    async def record_reaction(
        self,
        user_id: int,
        emoji: str,
        channel_id: int,
        message_id: int
    ) -> Tuple[bool, str, int]:
        """
        Registra reacción de usuario y otorga besitos.
        
        Returns:
            (success, message, besitos_granted)
        """
        # 1. Validar que reacción existe y está activa
        reaction = await self.get_reaction_by_emoji(emoji)
        if not reaction or not reaction.active:
            return False, f"Reacción {emoji} no configurada o inactiva", 0
        
        # 2. Validar anti-spam: no reaccionar dos veces al mismo mensaje
        if await self._has_reacted_to_message(user_id, message_id):
            return False, "Ya reaccionaste a este mensaje", 0
        
        # 3. Validar límite diario
        can_react, besitos_today = await self._check_daily_limit(user_id)
        if not can_react:
            return False, f"Límite diario alcanzado ({besitos_today} besitos)", 0
        
        # 4. Crear registro de reacción
        user_reaction = UserReaction(
            user_id=user_id,
            reaction_id=reaction.id,
            channel_id=channel_id,
            message_id=message_id,
            reacted_at=datetime.now(UTC)
        )
        self.session.add(user_reaction)
        await self.session.commit()
        await self.session.refresh(user_reaction)
        
        # 5. Otorgar besitos (integración con BesitoService)
        # NOTA: BesitoService debe estar disponible en container
        from bot.gamification.services.container import gamification_container
        besito_service = gamification_container.besito
        
        besitos_granted = await besito_service.grant_besitos(
            user_id=user_id,
            amount=reaction.besitos_value,
            transaction_type=TransactionType.REACTION,
            description=f"Reacción {emoji} en canal",
            reference_id=user_reaction.id
        )
        
        # 6. Actualizar racha
        streak = await self._update_user_streak(user_id)
        
        logger.info(
            f"User {user_id} reacted with {emoji}: "
            f"+{besitos_granted} besitos, streak: {streak.current_streak}"
        )
        
        return True, f"+{besitos_granted} besitos (racha: {streak.current_streak})", besitos_granted
    
    # ========================================
    # VALIDACIONES
    # ========================================
    
    async def _has_reacted_to_message(
        self, 
        user_id: int, 
        message_id: int
    ) -> bool:
        """Verifica si usuario ya reaccionó a este mensaje."""
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.user_id == user_id,
            UserReaction.message_id == message_id
        )
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def _check_daily_limit(self, user_id: int) -> Tuple[bool, int]:
        """Verifica límite diario de besitos."""
        from bot.gamification.config import GamificationConfig
        
        max_daily = GamificationConfig.MAX_BESITOS_PER_DAY
        if max_daily is None:
            return True, 0  # Sin límite
        
        # Contar besitos de hoy
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.coalesce(func.sum(UserReaction.besitos_value), 0)).join(
            Reaction
        ).where(
            UserReaction.user_id == user_id,
            UserReaction.reacted_at >= today_start
        )
        result = await self.session.execute(stmt)
        besitos_today = result.scalar()
        
        can_react = besitos_today < max_daily
        return can_react, besitos_today
    
    # ========================================
    # RACHAS
    # ========================================
    
    async def _update_user_streak(self, user_id: int) -> UserStreak:
        """Actualiza racha del usuario."""
        # Implementar lógica de rachas aquí
        pass
    
    async def get_user_streak(self, user_id: int) -> Optional[UserStreak]:
        """Obtiene racha actual del usuario."""
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    # ========================================
    # ESTADÍSTICAS
    # ========================================
    
    async def get_reaction_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de reacciones del usuario."""
        # Implementar estadísticas
        pass
```

---

## INTEGRACIÓN CON CONTAINER

```python
# bot/gamification/services/container.py

class GamificationContainer:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._reaction_service = None
        self._besito_service = None
    
    @property
    def reaction(self) -> ReactionService:
        if self._reaction_service is None:
            self._reaction_service = ReactionService(self._session)
        return self._reaction_service
    
    @property
    def besito(self) -> BesitoService:
        if self._besito_service is None:
            self._besito_service = BesitoService(self._session)
        return self._besito_service
```

---

## VALIDACIÓN

El servicio debe cumplir:
- ✅ CRUD completo de reacciones
- ✅ Registro de reacciones con validaciones anti-spam
- ✅ Integración con BesitoService
- ✅ Actualización de rachas
- ✅ Límite diario respetado
- ✅ Logging en operaciones importantes
- ✅ Type hints completos
- ✅ Docstrings en métodos públicos

---

**ENTREGABLE:** Archivo `reaction.py` completo con gestión de reacciones, besitos y rachas.
