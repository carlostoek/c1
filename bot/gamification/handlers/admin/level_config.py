"""
Handlers CRUD para configuración de niveles de gamificación.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()


class LevelConfigStates(StatesGroup):
    """Estados para configuración de niveles."""
    waiting_name = State()
    waiting_min_besitos = State()
    waiting_order = State()
    editing_field = State()
    waiting_benefits = State()  # For editing benefits as JSON string


# ========================================
# MENÚ PRINCIPAL DE NIVELES
# ========================================

@router.callback_query(F.data == "gamif:admin:levels")
async def levels_menu(callback: CallbackQuery, session):
    """Muestra lista de niveles configurados."""
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    levels = await gamification.level.get_all_levels(active_only=True)
    
    text = "📊 <b>NIVELES CONFIGURADOS</b>\n━━━━━━━━━━━━━━━━\n\n"
    
    if not levels:
        text += "No hay niveles configurados.\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Crear Primer Nivel", callback_data="gamif:level:add")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])
    else:
        # Get level distribution stats
        distribution = await gamification.level.get_level_distribution()
        
        keyboard_buttons = []
        
        for level in levels:
            status = "✅" if level.active else "❌"
            user_count = distribution.get(level.name, 0)
            
            text += f"{level.order}. {status} <b>{level.name}</b>\n"
            text += f"   • Min. besitos: {level.min_besitos:,}\n"
            text += f"   • Usuarios: {user_count:,}\n"
            
            # Botones por nivel
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{level.order}. {level.name}",
                    callback_data=f"gamif:level:view:{level.id}"
                ),
                InlineKeyboardButton(
                    text="✏️",
                    callback_data=f"gamif:level:edit:{level.id}"
                )
            ])
        
        text += f"\n<i>Total: {len(levels)} nivel(es)</i>"
        
        # Botones de acción
        keyboard_buttons.append([
            InlineKeyboardButton(text="➕ Crear Nivel", callback_data="gamif:level:add")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# CREAR NIVEL
# ========================================

@router.callback_query(F.data == "gamif:level:add")
async def start_add_level(callback: CallbackQuery, state: FSMContext):
    """Inicia proceso de crear nivel."""
    await callback.message.edit_text(
        "➕ <b>Crear Nuevo Nivel</b>\n\n"
        "Envía el nombre del nuevo nivel.\n\n"
        "Ejemplo: Novato, Regular, Experto",
        parse_mode="HTML"
    )
    await state.set_state(LevelConfigStates.waiting_name)
    await callback.answer()


@router.message(LevelConfigStates.waiting_name)
async def receive_level_name(message: Message, state: FSMContext, session):
    """Recibe nombre del nivel."""
    name = message.text.strip()

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    if len(name) < 2:
        await message.answer("❌ El nombre debe tener al menos 2 caracteres. Intenta de nuevo:")
        return
    
    # Validar si nombre ya existe
    all_levels = await gamification.level.get_all_levels(active_only=False)
    for level in all_levels:
        if level.name.lower() == name.lower():
            await message.answer(
                f"❌ Ya existe un nivel con nombre '{name}' (ID: {level.id}).\n"
                f"Por favor elige otro nombre:"
            )
            return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ Nombre: <b>{name}</b>\n\n"
        f"Ahora envía la cantidad mínima de besitos para alcanzar este nivel.\n\n"
        f"Ejemplo: 0, 500, 2000",
        parse_mode="HTML"
    )
    await state.set_state(LevelConfigStates.waiting_min_besitos)


@router.message(LevelConfigStates.waiting_min_besitos)
async def receive_min_besitos(message: Message, state: FSMContext, session):
    """Recibe cantidad mínima de besitos."""
    try:
        min_besitos = int(message.text)
        if min_besitos < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número entero no negativo. Intenta de nuevo:")
        return

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)

    # Validar si min_besitos ya existe
    all_levels = await gamification.level.get_all_levels(active_only=False)
    for level in all_levels:
        if level.min_besitos == min_besitos:
            await message.answer(
                f"❌ Ya existe un nivel con {min_besitos} besitos mínimos (nivel '{level.name}', ID: {level.id}).\n"
                f"Por favor elige otro valor:"
            )
            return
    
    await state.update_data(min_besitos=min_besitos)
    
    # Determine suggested order
    all_levels = await gamification.level.get_all_levels(active_only=True)
    orders = [level.order for level in all_levels]
    suggested_order = max(orders) + 1 if orders else 1
    
    await message.answer(
        f"✅ Nombre: {message.text}\n"
        f"✅ Mín. besitos: {min_besitos:,}\n\n"
        f"Ahora envía el orden de progresión (número entero).\n\n"
        f"Sugerencia: {suggested_order}\n"
        f"Recuerda: La progresión debe ser secuencial (1, 2, 3, etc.)",
        parse_mode="HTML"
    )
    await state.set_state(LevelConfigStates.waiting_order)


@router.message(LevelConfigStates.waiting_order)
async def receive_level_order(message: Message, state: FSMContext, session):
    """Recibe orden de progresión."""
    try:
        order = int(message.text)
        if order <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número entero positivo. Intenta de nuevo:")
        return

    # Validate order progression
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    all_levels = await gamification.level.get_all_levels(active_only=True)
    orders = [level.order for level in all_levels]
    
    if orders and order > max(orders) + 1:
        await message.answer(
            f"❌ No puedes crear nivel con order {order} cuando el máximo actual es {max(orders)}.\n"
            f"Usa {max(orders) + 1} para mantener la progresión secuencial."
        )
        return
    
    # Validate if order is already taken
    for level in all_levels:
        if level.order == order:
            await message.answer(
                f"❌ Ya existe un nivel con order {order} ('{level.name}', ID: {level.id}).\n"
                f"Elige un order diferente:"
            )
            return
    
    # Get data and create level
    data = await state.get_data()
    
    try:
        level = await gamification.level.create_level(
            name=data['name'],
            min_besitos=data['min_besitos'],
            order=order
        )
        
        await message.answer(
            f"✅ <b>Nivel Creado Exitosamente</b>\n\n"
            f"ID: {level.id}\n"
            f"Nombre: {level.name}\n"
            f"Mín. besitos: {level.min_besitos:,}\n"
            f"Orden: {level.order}\n\n"
            f"Los usuarios podrán alcanzar este nivel según sus besitos acumulados.",
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Error al crear nivel: {str(e)}")


# ========================================
# VER DETALLES DE NIVEL
# ========================================

@router.callback_query(F.data.startswith("gamif:level:view:"))
async def view_level_details(callback: CallbackQuery, session):
    """Muestra detalles de un nivel específico."""
    level_id = int(callback.data.split(":")[-1])
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    level = await gamification.level.get_level_by_id(level_id)
    
    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return
    
    status = "✅ Activo" if level.active else "❌ Inactivo"
    
    # Get distribution data
    distribution = await gamification.level.get_level_distribution()
    user_count = distribution.get(level.name, 0)
    
    # Get users in this level (sample)
    users_in_level = await gamification.level.get_users_in_level(level_id, limit=10)
    users_sample = [str(user.user_id) for user in users_in_level[:5]]  # Show first 5
    
    text = f"""📋 <b>Detalles del Nivel</b>

<b>ID:</b> {level.id}
<b>Nombre:</b> {level.name}
<b>Estado:</b> {status}
<b>Mín. Besitos:</b> {level.min_besitos:,}
<b>Orden:</b> {level.order}

<b>Estadísticas:</b>
• Usuarios en este nivel: {user_count:,}
• Beneficios: {level.benefits or 'Ninguno'}

<b>Usuarios (muestra):</b>
{', '.join(users_sample) if users_sample else 'Ninguno'}
"""
    
    # Prepare keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar", callback_data=f"gamif:level:edit:{level_id}"),
            InlineKeyboardButton(
                text="🔄 Activar/Desactivar" if level.active else "🔄 Activar/Desactivar",
                callback_data=f"gamif:level:toggle:{level_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:level:delete:{level_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:levels")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# EDITAR NIVEL
# ========================================

@router.callback_query(F.data.startswith("gamif:level:edit:"))
async def edit_level_menu(callback: CallbackQuery, session):
    """Muestra menú de edición de nivel."""
    level_id = int(callback.data.split(":")[-1])
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    level = await gamification.level.get_level_by_id(level_id)

    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return
    
    text = f"""✏️ <b>Editar Nivel: {level.name}</b>

Selecciona qué campo deseas editar:

• <b>Nombre:</b> {level.name}
• <b>Mín. Besitos:</b> {level.min_besitos:,}
• <b>Orden:</b> {level.order}
• <b>Beneficios:</b> {level.benefits or 'Ninguno'}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nombre", callback_data=f"gamif:level:edit_field:{level_id}:name"),
            InlineKeyboardButton(text="💰 Min. Besitos", callback_data=f"gamif:level:edit_field:{level_id}:min_besitos")
        ],
        [
            InlineKeyboardButton(text="🔢 Orden", callback_data=f"gamif:level:edit_field:{level_id}:order"),
            InlineKeyboardButton(text="🎁 Beneficios", callback_data=f"gamif:level:edit_field:{level_id}:benefits")
        ],
        [
            InlineKeyboardButton(text="🔄 Activar/Desactivar", callback_data=f"gamif:level:toggle:{level_id}"),
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:level:delete:{level_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:level:view:{level_id}")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:level:edit_field:"))
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de campo específico."""
    parts = callback.data.split(":")
    level_id = int(parts[3])
    field = parts[4]
    
    await state.update_data(editing_level_id=level_id, editing_field=field)
    
    field_names = {
        'name': 'nombre',
        'min_besitos': 'mínimos besitos',
        'order': 'orden de progresión',
        'benefits': 'beneficios (JSON)'
    }
    
    await callback.message.edit_text(
        f"✏️ <b>Editar {field_names.get(field, field)}</b>\n\n"
        f"Envía el nuevo valor:",
        parse_mode="HTML"
    )
    await state.set_state(LevelConfigStates.editing_field)
    await callback.answer()


@router.message(LevelConfigStates.editing_field)
async def receive_edited_field(message: Message, state: FSMContext, session):
    """Recibe valor editado para campo específico."""
    data = await state.get_data()
    level_id = data['editing_level_id']
    field = data['editing_field']

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    level = await gamification.level.get_level_by_id(level_id)
    if not level:
        await message.answer("❌ Nivel no encontrado")
        await state.clear()
        return
    
    # Prepare update data
    update_data = {}
    
    try:
        if field == 'name':
            new_value = message.text.strip()
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres. Intenta de nuevo:")
                return
            
            # Validar duplicado
            all_levels = await gamification.level.get_all_levels(active_only=False)
            for l in all_levels:
                if l.name.lower() == new_value.lower() and l.id != level_id:
                    await message.answer(
                        f"❌ Ya existe un nivel con nombre '{new_value}' (ID: {l.id}).\n"
                        f"Por favor elige otro nombre:"
                    )
                    return
            
            update_data['name'] = new_value
        elif field == 'min_besitos':
            new_value = int(message.text)
            if new_value < 0:
                raise ValueError
            
            # Validar duplicado
            all_levels = await gamification.level.get_all_levels(active_only=False)
            for l in all_levels:
                if l.min_besitos == new_value and l.id != level_id:
                    await message.answer(
                        f"❌ Ya existe un nivel con {new_value} besitos mínimos (nivel '{l.name}', ID: {l.id}).\n"
                        f"Por favor elige otro valor:"
                    )
                    return
            
            update_data['min_besitos'] = new_value
        elif field == 'order':
            new_value = int(message.text)
            if new_value <= 0:
                raise ValueError
            
            # Validate progression
            all_levels = await gamification.level.get_all_levels(active_only=True)
            orders = [l.order for l in all_levels if l.id != level_id]
            
            if new_value > 1 and (new_value - 1) not in orders:
                await message.answer(
                    f"❌ No puedes usar order {new_value} porque rompería la secuencia.\n"
                    f"Los orders deben ser secuenciales (1, 2, 3, etc.)."
                )
                return
            
            update_data['order'] = new_value
        elif field == 'benefits':
            new_value = message.text.strip()
            # Validate JSON if provided
            import json
            try:
                if new_value.lower() != 'none' and new_value.lower() != 'null':
                    json.loads(new_value)  # Validate JSON format
                update_data['benefits'] = new_value if new_value.lower() not in ['none', 'null'] else None
            except json.JSONDecodeError:
                await message.answer("❌ Formato JSON inválido. Ingresa 'none' para eliminar beneficios o un JSON válido:")
                return
        else:
            await message.answer("❌ Campo no válido para editar")
            await state.clear()
            return
        
        # Update the level
        updated_level = await gamification.level.update_level(level_id, **update_data)
        
        await message.answer(
            f"✅ <b>Nivel Actualizado</b>\n\n"
            f"ID: {updated_level.id}\n"
            f"Campo: {field}\n"
            f"Nuevo valor: {updated_level.__dict__.get(field, 'unknown')}"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Debe ser un número válido. Intenta de nuevo:")
    except Exception as e:
        await message.answer(f"❌ Error al actualizar: {str(e)}")


# ========================================
# TOGGLE ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:level:toggle:"))
async def toggle_level(callback: CallbackQuery, session):
    """Activa o desactiva un nivel."""
    level_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    level = await gamification.level.get_level_by_id(level_id)
    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    await gamification.level.update_level(level_id, active=not level.active)

    status_text = "activado" if not level.active else "desactivado"
    await callback.answer(f"✅ Nivel {status_text}", show_alert=True)

    # Refresh the view
    await view_level_details(callback, session)


# ========================================
# ELIMINAR NIVEL
# ========================================

@router.callback_query(F.data.startswith("gamif:level:delete:"))
async def delete_level_prompt(callback: CallbackQuery, session):
    """Pide confirmación para eliminar nivel."""
    level_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    level = await gamification.level.get_level_by_id(level_id)
    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    # Check if level has users
    users_in_level = await gamification.level.get_users_in_level(level_id)
    user_count = len(users_in_level)

    if user_count > 0:
        # Show reassignment options since there are users
        all_levels = await gamification.level.get_all_levels(active_only=True)
        other_levels = [l for l in all_levels if l.id != level_id]

        text = f"""⚠️ <b>Advertencia: Eliminación con Usuarios</b>

Nivel: <b>{level.name}</b> (ID: {level.id})
Usuarios afectados: <b>{user_count}</b>

⚠️ Este nivel tiene {user_count} usuarios asignados.
Para continuar, debes reasignarlos a otro nivel primero.

<b>Elige un nivel de destino para los usuarios:</b>
"""

        keyboard_buttons = []

        for other_level in other_levels:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"→ {other_level.name}",
                    callback_data=f"gamif:level:reassign_users:{level_id}:{other_level.id}"
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:level:view:{level_id}")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    else:
        # No users, can delete directly
        text = f"""⚠️ <b>Confirmar Eliminación</b>

¿Estás seguro de eliminar el nivel?

Nombre: <b>{level.name}</b>
ID: {level.id}
Min. besitos: {level.min_besitos:,}
Orden: {level.order}

Esta acción no se puede deshacer."""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠️ Sí, Eliminar", callback_data=f"gamif:level:delete_confirm:{level_id}"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:level:view:{level_id}")
            ]
        ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:level:reassign_users:"))
async def reassign_users_before_delete(callback: CallbackQuery, session):
    """Reasigna usuarios de nivel antes de eliminar."""
    parts = callback.data.split(":")
    source_level_id = int(parts[3])
    target_level_id = int(parts[4])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    # Get target level for confirmation
    source_level = await gamification.level.get_level_by_id(source_level_id)
    target_level = await gamification.level.get_level_by_id(target_level_id)

    if not source_level or not target_level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    # Update all users from source level to target level using ORM
    from sqlalchemy import update
    from bot.gamification.database.models import UserGamification

    stmt = (
        update(UserGamification)
        .where(UserGamification.current_level_id == source_level_id)
        .values(current_level_id=target_level_id)
    )
    await gamification.session.execute(stmt)
    await gamification.session.commit()

    text = f"""🔄 <b>Usuarios Reasignados</b>

{source_level.name} (ID: {source_level_id}) → {target_level.name} (ID: {target_level_id})

Todos los usuarios han sido reasignados.
¿Deseas eliminar ahora el nivel {source_level.name}?
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ Sí, Eliminar", callback_data=f"gamif:level:delete_confirm:{source_level_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="gamif:admin:levels")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:level:delete_confirm:"))
async def confirm_delete_level(callback: CallbackQuery, session):
    """Confirma eliminación de nivel."""
    level_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    level = await gamification.level.get_level_by_id(level_id)
    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    # Since the service already does a soft-delete, we'll use that
    success = await gamification.level.delete_level(level_id)

    if success:
        await callback.answer("✅ Nivel eliminado", show_alert=True)
        await levels_menu(callback, session)
    else:
        await callback.answer("❌ Error al eliminar nivel", show_alert=True)