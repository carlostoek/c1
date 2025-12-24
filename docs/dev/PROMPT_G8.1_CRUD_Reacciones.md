# PROMPT G8.1: CRUD de Reacciones (Configuración de Emojis)

---

## ROL

Ingeniero de Software Senior especializado en interfaces CRUD y gestión de catálogos.

---

## TAREA

Implementa handlers de administración CRUD para el modelo `Reaction` en `bot/gamification/handlers/admin/reaction_config.py`, permitiendo configurar qué emojis otorgan besitos.

---

## CONTEXTO

### Modelo Reaction (ya existe)
```python
class Reaction(Base):
    id: Mapped[int]
    emoji: Mapped[str]              # "❤️", "🔥", "👍"
    name: Mapped[str]               # "Corazón", "Fuego"
    besitos_value: Mapped[int]      # Puntos base que otorga
    active: Mapped[bool]
    created_at: Mapped[datetime]
```

### Objetivo

Permitir a admins:
1. Ver lista de emojis configurados
2. Agregar nuevo emoji con valor de besitos
3. Editar valor de besitos de emoji existente
4. Activar/desactivar emojis
5. Eliminar emojis (soft-delete)

---

## HANDLERS REQUERIDOS

### 1. Menú Principal de Reacciones

```python
@router.callback_query(F.data == "gamif:admin:reactions")
async def reactions_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra lista de reacciones configuradas.
    
    Formato:
    ━━━━━━━━━━━━━━━━━━━━━
    📝 REACCIONES CONFIGURADAS
    
    ✅ ❤️ Corazón: 1 besito
    ✅ 🔥 Fuego: 2 besitos
    ✅ 👍 Me gusta: 1 besito
    ❌ 💰 Dinero: 5 besitos (inactivo)
    
    Botones:
    [➕ Agregar Emoji]
    [🔙 Volver]
    
    + Botón inline por cada emoji:
    [✏️ Editar] [🗑️ Eliminar]
    """
```

### 2. Agregar Nuevo Emoji

```python
# Estado FSM
class ReactionConfigStates(StatesGroup):
    waiting_emoji = State()
    waiting_name = State()
    waiting_besitos = State()

@router.callback_query(F.data == "gamif:reactions:add")
async def start_add_reaction(callback: CallbackQuery, state: FSMContext):
    """Inicia proceso de agregar emoji."""

@router.message(ReactionConfigStates.waiting_emoji)
async def receive_emoji(message: Message, state: FSMContext):
    """
    Recibe emoji y valida.
    
    Validaciones:
    - Es un emoji válido
    - No está ya configurado
    """

@router.message(ReactionConfigStates.waiting_besitos)
async def receive_besitos_value(message: Message, state: FSMContext, gamification: GamificationContainer):
    """
    Recibe valor de besitos y crea Reaction.
    
    Validación: besitos > 0
    """
```

### 3. Editar Reacción

```python
@router.callback_query(F.data.startswith("gamif:reaction:edit:"))
async def edit_reaction(callback: CallbackQuery, state: FSMContext):
    """
    Muestra opciones de edición.
    
    Botones:
    [✏️ Cambiar Valor] [🔄 Cambiar Estado] [🔙 Volver]
    """

@router.callback_query(F.data.startswith("gamif:reaction:change_value:"))
async def start_change_value(callback: CallbackQuery, state: FSMContext):
    """Pide nuevo valor de besitos."""

@router.message(ReactionConfigStates.editing_value)
async def receive_new_value(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Actualiza valor de besitos."""
```

### 4. Activar/Desactivar

```python
@router.callback_query(F.data.startswith("gamif:reaction:toggle:"))
async def toggle_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Activa o desactiva reacción."""
```

### 5. Eliminar

```python
@router.callback_query(F.data.startswith("gamif:reaction:delete:"))
async def delete_reaction(callback: CallbackQuery):
    """
    Pide confirmación antes de eliminar.
    
    [⚠️ Confirmar] [❌ Cancelar]
    """

@router.callback_query(F.data.startswith("gamif:reaction:delete_confirm:"))
async def confirm_delete_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Elimina reacción de BD."""
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/handlers/admin/reaction_config.py

"""
Handlers CRUD para configuración de reacciones (emojis).
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.gamification.services.container import GamificationContainer
from bot.gamification.utils.validators import is_valid_emoji

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class ReactionConfigStates(StatesGroup):
    """Estados para configuración de reacciones."""
    waiting_emoji = State()
    waiting_name = State()
    waiting_besitos = State()
    editing_value = State()


# ========================================
# MENÚ PRINCIPAL
# ========================================

@router.callback_query(F.data == "gamif:admin:reactions")
async def reactions_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra lista de reacciones configuradas."""
    reactions = await gamification.reaction.get_all_reactions()
    
    text = "📝 <b>REACCIONES CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not reactions:
        text += "No hay emojis configurados.\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Agregar Primer Emoji", callback_data="gamif:reactions:add")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])
    else:
        keyboard_buttons = []
        
        for reaction in reactions:
            status = "✅" if reaction.active else "❌"
            state_text = "" if reaction.active else " (inactivo)"
            
            text += f"{status} {reaction.emoji} <b>{reaction.name}</b>: {reaction.besitos_value} besito(s){state_text}\n"
            
            # Botones por reacción
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{reaction.emoji} {reaction.name}",
                    callback_data=f"gamif:reaction:view:{reaction.id}"
                ),
                InlineKeyboardButton(
                    text="✏️",
                    callback_data=f"gamif:reaction:edit:{reaction.id}"
                )
            ])
        
        text += f"\n<i>Total: {len(reactions)} emoji(s)</i>"
        
        # Botones de acción
        keyboard_buttons.append([
            InlineKeyboardButton(text="➕ Agregar Emoji", callback_data="gamif:reactions:add")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# AGREGAR NUEVO EMOJI
# ========================================

@router.callback_query(F.data == "gamif:reactions:add")
async def start_add_reaction(callback: CallbackQuery, state: FSMContext):
    """Inicia proceso de agregar emoji."""
    await callback.message.edit_text(
        "➕ <b>Agregar Nuevo Emoji</b>\n\n"
        "Envía el emoji que deseas configurar.\n\n"
        "Ejemplo: ❤️",
        parse_mode="HTML"
    )
    await state.set_state(ReactionConfigStates.waiting_emoji)
    await callback.answer()


@router.message(ReactionConfigStates.waiting_emoji)
async def receive_emoji(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Recibe y valida emoji."""
    emoji = message.text.strip()
    
    # Validar emoji
    if not is_valid_emoji(emoji):
        await message.answer("❌ Debe ser un emoji válido. Intenta de nuevo:")
        return
    
    # Verificar que no exista
    existing = await gamification.reaction.get_by_emoji(emoji)
    if existing:
        await message.answer(
            f"❌ El emoji {emoji} ya está configurado.\n\n"
            f"Valor actual: {existing.besitos_value} besito(s)"
        )
        await state.clear()
        return
    
    await state.update_data(emoji=emoji)
    
    await message.answer(
        f"✅ Emoji: {emoji}\n\n"
        f"Ahora envía un nombre descriptivo.\n\n"
        f"Ejemplo: Corazón, Fuego, Me gusta"
    )
    await state.set_state(ReactionConfigStates.waiting_name)


@router.message(ReactionConfigStates.waiting_name)
async def receive_name(message: Message, state: FSMContext):
    """Recibe nombre de la reacción."""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ El nombre debe tener al menos 2 caracteres.")
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ Nombre: {name}\n\n"
        f"¿Cuántos besitos otorgará este emoji?\n\n"
        f"Envía un número (ej: 1, 2, 5)"
    )
    await state.set_state(ReactionConfigStates.waiting_besitos)


@router.message(ReactionConfigStates.waiting_besitos)
async def receive_besitos_value(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Recibe valor de besitos y crea reacción."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo. Intenta de nuevo:")
        return
    
    # Obtener datos acumulados
    data = await state.get_data()
    
    # Crear reacción
    reaction = await gamification.reaction.create_reaction(
        emoji=data['emoji'],
        name=data['name'],
        besitos_value=besitos
    )
    
    await message.answer(
        f"✅ <b>Emoji Configurado</b>\n\n"
        f"{reaction.emoji} <b>{reaction.name}</b>\n"
        f"Valor: {reaction.besitos_value} besito(s)\n\n"
        f"Los usuarios ahora ganarán besitos al usar este emoji.",
        parse_mode="HTML"
    )
    
    await state.clear()


# ========================================
# EDITAR REACCIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:view:"))
async def view_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra detalles de reacción."""
    reaction_id = int(callback.data.split(":")[-1])
    reaction = await gamification.reaction.get_reaction_by_id(reaction_id)
    
    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return
    
    status = "✅ Activo" if reaction.active else "❌ Inactivo"
    
    # Obtener estadísticas de uso
    stats = await gamification.reaction.get_reaction_stats(reaction_id)
    
    text = f"""📊 <b>Detalles de Reacción</b>

{reaction.emoji} <b>{reaction.name}</b>

<b>Valor:</b> {reaction.besitos_value} besito(s)
<b>Estado:</b> {status}

<b>Estadísticas:</b>
• Usos totales: {stats.get('total_uses', 0):,}
• Besitos distribuidos: {stats.get('total_besitos', 0):,}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar Valor", callback_data=f"gamif:reaction:change_value:{reaction_id}"),
            InlineKeyboardButton(
                text="🔄 Desactivar" if reaction.active else "✅ Activar",
                callback_data=f"gamif:reaction:toggle:{reaction_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:reaction:delete:{reaction_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:reactions")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:change_value:"))
async def start_change_value(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de valor."""
    reaction_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_reaction_id=reaction_id)
    
    await callback.message.edit_text(
        "✏️ <b>Editar Valor</b>\n\n"
        "Envía el nuevo valor de besitos:",
        parse_mode="HTML"
    )
    await state.set_state(ReactionConfigStates.editing_value)
    await callback.answer()


@router.message(ReactionConfigStates.editing_value)
async def receive_new_value(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Actualiza valor de besitos."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return
    
    data = await state.get_data()
    reaction_id = data['editing_reaction_id']
    
    reaction = await gamification.reaction.update_reaction(
        reaction_id,
        besitos_value=besitos
    )
    
    await message.answer(
        f"✅ Valor actualizado\n\n"
        f"{reaction.emoji} {reaction.name}: {reaction.besitos_value} besito(s)"
    )
    
    await state.clear()


# ========================================
# ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:toggle:"))
async def toggle_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Activa o desactiva reacción."""
    reaction_id = int(callback.data.split(":")[-1])
    
    reaction = await gamification.reaction.get_reaction_by_id(reaction_id)
    new_state = not reaction.active
    
    await gamification.reaction.update_reaction(
        reaction_id,
        active=new_state
    )
    
    status_text = "activado" if new_state else "desactivado"
    await callback.answer(f"✅ Emoji {status_text}", show_alert=True)
    
    # Refrescar vista
    await view_reaction(callback, gamification)


# ========================================
# ELIMINAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:delete:"))
async def delete_reaction(callback: CallbackQuery):
    """Pide confirmación para eliminar."""
    reaction_id = callback.data.split(":")[-1]
    
    text = (
        "⚠️ <b>Confirmar Eliminación</b>\n\n"
        "¿Estás seguro de eliminar este emoji?\n\n"
        "Esta acción no se puede deshacer."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚠️ Sí, Eliminar", callback_data=f"gamif:reaction:delete_confirm:{reaction_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:reaction:view:{reaction_id}")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:delete_confirm:"))
async def confirm_delete_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Elimina reacción."""
    reaction_id = int(callback.data.split(":")[-1])
    
    await gamification.reaction.delete_reaction(reaction_id)
    
    await callback.answer("✅ Emoji eliminado", show_alert=True)
    await reactions_menu(callback, gamification)
```

---

## MÉTODOS NUEVOS EN ReactionService

```python
# bot/gamification/services/reaction.py

async def get_all_reactions(self, active_only: bool = False) -> List[Reaction]:
    """Obtiene todas las reacciones."""
    stmt = select(Reaction)
    if active_only:
        stmt = stmt.where(Reaction.active == True)
    stmt = stmt.order_by(Reaction.besitos_value.desc())
    
    result = await self.session.execute(stmt)
    return list(result.scalars().all())

async def get_reaction_by_id(self, reaction_id: int) -> Optional[Reaction]:
    """Obtiene reacción por ID."""
    return await self.session.get(Reaction, reaction_id)

async def create_reaction(self, emoji: str, name: str, besitos_value: int) -> Reaction:
    """Crea nueva reacción."""
    reaction = Reaction(
        emoji=emoji,
        name=name,
        besitos_value=besitos_value,
        active=True
    )
    self.session.add(reaction)
    await self.session.commit()
    await self.session.refresh(reaction)
    return reaction

async def update_reaction(self, reaction_id: int, **kwargs) -> Reaction:
    """Actualiza reacción."""
    reaction = await self.session.get(Reaction, reaction_id)
    for key, value in kwargs.items():
        setattr(reaction, key, value)
    await self.session.commit()
    await self.session.refresh(reaction)
    return reaction

async def delete_reaction(self, reaction_id: int) -> bool:
    """Elimina reacción (hard delete)."""
    reaction = await self.session.get(Reaction, reaction_id)
    if reaction:
        await self.session.delete(reaction)
        await self.session.commit()
        return True
    return False

async def get_reaction_stats(self, reaction_id: int) -> dict:
    """Obtiene estadísticas de uso de una reacción."""
    stmt = select(
        func.count(UserReaction.id),
        func.sum(UserReaction.besitos_earned)
    ).where(UserReaction.reaction_id == reaction_id)
    
    result = await self.session.execute(stmt)
    total_uses, total_besitos = result.one()
    
    return {
        'total_uses': total_uses or 0,
        'total_besitos': total_besitos or 0
    }
```

---

## INTEGRACIÓN

```python
# bot/main.py
from bot.gamification.handlers.admin import reaction_config

dp.include_router(reaction_config.router)
```

---

## VALIDACIÓN

- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Validación de emojis
- ✅ No permitir duplicados
- ✅ Activar/desactivar sin eliminar
- ✅ Estadísticas de uso
- ✅ Confirmación antes de eliminar

---

**ENTREGABLE:** Archivo `reaction_config.py` con CRUD completo de reacciones.
