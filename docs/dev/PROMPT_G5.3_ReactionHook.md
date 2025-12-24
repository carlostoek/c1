# PROMPT G5.3: Reaction Event Hook - Integration Point

---

## ROL

Actúa como Ingeniero de Software Senior especializado en event-driven architecture y webhooks internos.

---

## TAREA

Implementa el hook de eventos de reacción en `bot/gamification/background/reaction_hook.py` que se integra con el sistema de reacciones de Telegram para actualizar gamificación.

---

## CONTEXTO

### Problema

El bot debe detectar cuando usuarios reaccionan a mensajes en canales y actualizar:
- Besitos del usuario
- Rachas
- Progreso de misiones

### Flujo de Integración

```
Usuario reacciona → MessageReactionUpdated → on_reaction_event() → gamification
```

---

## RESPONSABILIDADES

### 1. Handler de Reacción

```python
@router.message_reaction()
async def on_reaction_event(
    update: MessageReactionUpdated,
    session: AsyncSession,
    gamification: GamificationContainer
):
    """
    Procesa reacción de usuario.
    
    Flujo:
    1. Validar que sea en canal configurado
    2. Obtener emoji(s) añadidos
    3. Llamar reaction_service.record_reaction()
    4. Verificar auto level-up
    5. Actualizar progreso de misiones
    """
```

### 2. Validaciones

```python
async def is_valid_reaction(
    update: MessageReactionUpdated,
    session: AsyncSession
) -> bool:
    """
    Verifica:
    - Canal está configurado como VIP/Free
    - Usuario tiene acceso
    - Reacción es válida (no remove)
    """
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/background/reaction_hook.py

"""
Hook de eventos de reacción para gamificación.

Integra reacciones de Telegram con sistema de gamificación.
"""

from datetime import datetime, UTC
from aiogram import Router
from aiogram.types import MessageReactionUpdated
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.services.container import GamificationContainer
from bot.services.container import ServiceContainer

logger = logging.getLogger(__name__)
router = Router()


@router.message_reaction()
async def on_reaction_event(
    update: MessageReactionUpdated,
    session: AsyncSession,
    gamification: GamificationContainer,
    container: ServiceContainer
):
    """Procesa evento de reacción."""
    
    # Obtener datos
    user_id = update.user.id if update.user else None
    chat_id = update.chat.id
    message_id = update.message_id
    
    if not user_id:
        return
    
    # Validar que sea canal configurado
    is_valid = await is_valid_reaction(update, session, container)
    if not is_valid:
        return
    
    # Obtener emojis añadidos
    new_reactions = update.new_reaction
    if not new_reactions:
        return
    
    # Procesar cada emoji
    for reaction in new_reactions:
        if hasattr(reaction, 'emoji'):
            emoji = reaction.emoji
            
            try:
                # Registrar reacción
                success, message, besitos = await gamification.reaction.record_reaction(
                    user_id=user_id,
                    emoji=emoji,
                    message_id=message_id,
                    channel_id=chat_id,
                    reacted_at=datetime.now(UTC)
                )
                
                if success:
                    logger.info(f"Reaction recorded: User {user_id} {emoji} (+{besitos} besitos)")
                    
                    # Auto level-up
                    changed, old_level, new_level = await gamification.level.check_and_apply_level_up(user_id)
                    if changed:
                        logger.info(f"Level-up: User {user_id} → {new_level.name}")
                    
                    # Actualizar progreso de misiones
                    await gamification.mission.on_user_reaction(
                        user_id=user_id,
                        emoji=emoji,
                        reacted_at=datetime.now(UTC)
                    )
                else:
                    logger.warning(f"Reaction failed: User {user_id} - {message}")
            
            except Exception as e:
                logger.error(f"Error processing reaction: {e}")


async def is_valid_reaction(
    update: MessageReactionUpdated,
    session: AsyncSession,
    container: ServiceContainer
) -> bool:
    """Valida que reacción sea procesable."""
    
    # Verificar que chat sea canal configurado
    channel = await container.channel.get_channel_by_chat_id(update.chat.id)
    if not channel:
        return False
    
    # Verificar que usuario tenga acceso (si es VIP)
    if channel.is_vip:
        has_access = await container.subscription.check_access(
            update.user.id,
            channel.id
        )
        if not has_access:
            return False
    
    return True
```

---

## INTEGRACIÓN

```python
# bot/main.py
from bot.gamification.background.reaction_hook import router as reaction_router

dp.include_router(reaction_router)
```

---

## CONFIGURACIÓN

```python
# .env
GAMIFICATION_ENABLED=true
PROCESS_REACTIONS=true
```

---

## VALIDACIÓN

- ✅ Handler de MessageReactionUpdated
- ✅ Validación de canal configurado
- ✅ Registro de reacción
- ✅ Auto level-up
- ✅ Update de progreso de misiones
- ✅ Logging completo

---

**ENTREGABLE:** Archivo `reaction_hook.py` con integración completa.
