"""
Handlers CRUD para configuración de recompensas.

Responsabilidades:
- Lista con filtros por RewardType
- Vista detallada con estadísticas
- Edición de campos individuales
- Edición de unlock_conditions
- Manejo especial de Badges (herencia)
- Activar/desactivar recompensas
- Eliminar con validaciones
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import json
import logging

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.states.admin import RewardConfigStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import RewardType, BadgeRarity
from bot.gamification.utils.validators import is_valid_emoji

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Registrar middleware
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# LISTA CON FILTROS
# ========================================

@router.callback_query(F.data == "gamif:rewards:list")
@router.callback_query(F.data == "gamif:admin:rewards_list")
async def rewards_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra lista de recompensas."""
    await show_rewards_list(callback, gamification, reward_type=None)
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:rewards:filter:"))
async def filter_rewards_by_type(callback: CallbackQuery, gamification: GamificationContainer):
    """Filtra recompensas por tipo."""
    reward_type = callback.data.split(":")[-1]
    await show_rewards_list(callback, gamification, reward_type=reward_type)
    await callback.answer()


async def show_rewards_list(
    callback: CallbackQuery,
    gamification: GamificationContainer,
    reward_type: str = None
):
    """Muestra lista de recompensas con filtro opcional.

    Args:
        callback: CallbackQuery
        gamification: GamificationContainer
        reward_type: Filtro opcional por tipo (badge, item, permission, besitos)
    """
    # Obtener recompensas (con o sin filtro)
    if reward_type:
        from bot.gamification.database.enums import RewardType as RT
        type_map = {
            "badge": RT.BADGE,
            "item": RT.ITEM,
            "permission": RT.PERMISSION,
            "besitos": RT.BESITOS
        }
        filter_type = type_map.get(reward_type)
        rewards = await gamification.reward.get_all_rewards(
            active_only=False,
            reward_type=filter_type
        )
    else:
        rewards = await gamification.reward.get_all_rewards(active_only=False)

    if not rewards:
        text = "🎁 <b>RECOMPENSAS CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━\n\n"
        text += "No hay recompensas configuradas.\n\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="gamif:wizard:reward")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Emojis por tipo
    type_emojis = {
        RewardType.BADGE.value: "🏆",
        RewardType.ITEM.value: "🎁",
        RewardType.PERMISSION.value: "🔓",
        RewardType.BESITOS.value: "💰"
    }

    type_names = {
        RewardType.BADGE.value: "Badge",
        RewardType.ITEM.value: "Item",
        RewardType.PERMISSION.value: "Permiso",
        RewardType.BESITOS.value: "Besitos"
    }

    # Construir mensaje
    if reward_type:
        text = f"🎁 <b>RECOMPENSAS: {type_names.get(reward_type, reward_type.upper())}</b>\n━━━━━━━━━━━━━━━━\n\n"
    else:
        text = "🎁 <b>RECOMPENSAS CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━\n\n"

    keyboard_buttons = []

    for idx, reward in enumerate(rewards, start=1):
        status = "✅" if reward.active else "❌"
        type_emoji = type_emojis.get(reward.reward_type, "🎁")
        type_name = type_names.get(reward.reward_type, reward.reward_type)

        cost_text = ""
        if reward.cost_besitos:
            cost_text = f" • {reward.cost_besitos} besitos"

        text += f"{idx}. {status} {type_emoji} <b>{reward.name}</b> ({type_name}){cost_text}\n"

        # Botón de la recompensa
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{type_emoji} {reward.name}",
                callback_data=f"gamif:reward:view:{reward.id}"
            )
        ])

    text += f"\n<i>Total: {len(rewards)} recompensa(s)</i>"

    # Botones de filtro
    filter_row_1 = [
        InlineKeyboardButton(text="🏆 Badges", callback_data="gamif:rewards:filter:badge"),
        InlineKeyboardButton(text="🎁 Items", callback_data="gamif:rewards:filter:item")
    ]
    keyboard_buttons.append(filter_row_1)

    filter_row_2 = [
        InlineKeyboardButton(text="🔓 Permisos", callback_data="gamif:rewards:filter:permission"),
        InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:rewards:filter:besitos")
    ]
    keyboard_buttons.append(filter_row_2)

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔄 Todas", callback_data="gamif:rewards:list")
    ])

    # Botones de acción
    keyboard_buttons.append([
        InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="gamif:wizard:reward")
    ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# VISTA DETALLADA
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:view:"))
async def view_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra detalles de recompensa con estadísticas."""
    reward_id = int(callback.data.split(":")[-1])
    reward = await gamification.reward.get_reward_by_id(reward_id)

    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    # Obtener estadísticas
    users_count = await gamification.reward.get_users_with_reward(reward_id)

    # Status
    status = "✅ Activa" if reward.active else "❌ Inactiva"

    # Tipo
    type_names = {
        RewardType.BADGE.value: "🏆 Badge",
        RewardType.ITEM.value: "🎁 Item",
        RewardType.PERMISSION.value: "🔓 Permiso",
        RewardType.BESITOS.value: "💰 Besitos"
    }
    type_name = type_names.get(reward.reward_type, reward.reward_type)

    # Costo
    cost_text = "No se puede comprar" if not reward.cost_besitos else f"{reward.cost_besitos} besitos"

    # Unlock conditions
    conditions_text = "Sin condiciones"
    if reward.unlock_conditions:
        try:
            conditions = json.loads(reward.unlock_conditions)
            conditions_text = _format_unlock_conditions(conditions)
        except (json.JSONDecodeError, TypeError):
            conditions_text = "Condiciones inválidas"

    text = f"""🎁 <b>RECOMPENSA: {reward.name}</b>
━━━━━━━━━━━━━━━━

{type_name}
📝 {reward.description}

⚙️ <b>CONFIGURACIÓN</b>
• Costo: {cost_text}
• Estado: {status}

🔓 <b>UNLOCK CONDITIONS</b>
{conditions_text}

👥 <b>ESTADÍSTICAS</b>
• Usuarios que la tienen: {users_count}
"""

    # Si es Badge, mostrar info adicional
    if reward.reward_type == RewardType.BADGE.value:
        # Intentar obtener badge
        from sqlalchemy import select
        from bot.gamification.database.models import Badge
        stmt = select(Badge).where(Badge.id == reward_id)
        result = await gamification.reward.session.execute(stmt)
        badge = result.scalar_one_or_none()

        if badge:
            rarity_names = {
                BadgeRarity.COMMON.value: "Común",
                BadgeRarity.RARE.value: "Rara",
                BadgeRarity.EPIC.value: "Épica",
                BadgeRarity.LEGENDARY.value: "Legendaria"
            }
            rarity_name = rarity_names.get(badge.rarity, badge.rarity)

            text += f"\n🏆 <b>BADGE INFO</b>\n"
            text += f"• Icono: {badge.icon}\n"
            text += f"• Rareza: {rarity_name}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar", callback_data=f"gamif:reward:edit:{reward_id}"),
            InlineKeyboardButton(
                text="🔄 Desactivar" if reward.active else "✅ Activar",
                callback_data=f"gamif:reward:toggle:{reward_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:reward:delete:{reward_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver a Lista", callback_data="gamif:rewards:list")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


def _format_unlock_conditions(conditions: dict) -> str:
    """Formatea condiciones de unlock para mostrar."""
    if not conditions:
        return "Sin condiciones"

    cond_type = conditions.get('type', 'unknown')

    if cond_type == 'mission':
        mission_id = conditions.get('mission_id')
        return f"• Completar misión ID: {mission_id}"

    elif cond_type == 'level':
        level_id = conditions.get('level_id')
        return f"• Alcanzar nivel ID: {level_id}"

    elif cond_type == 'besitos':
        min_besitos = conditions.get('min_besitos', 0)
        return f"• Tener al menos {min_besitos:,} besitos"

    elif cond_type == 'multiple':
        sub_conditions = conditions.get('conditions', [])
        text = "Requiere TODO lo siguiente:\n"
        for sub_cond in sub_conditions:
            sub_text = _format_unlock_conditions(sub_cond)
            text += f"{sub_text}\n"
        return text.strip()

    return str(conditions)


# ========================================
# EDICIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:edit:"))
async def edit_reward_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra menú de edición."""
    reward_id = int(callback.data.split(":")[-1])
    reward = await gamification.reward.get_reward_by_id(reward_id)

    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    text = f"✏️ <b>EDITAR: {reward.name}</b>\n\n"
    text += "Selecciona el campo a editar:"

    keyboard_buttons = [
        [
            InlineKeyboardButton(text="📝 Nombre", callback_data=f"gamif:reward:edit_field:{reward_id}:name"),
            InlineKeyboardButton(text="📄 Descripción", callback_data=f"gamif:reward:edit_field:{reward_id}:description")
        ],
        [
            InlineKeyboardButton(text="💰 Costo", callback_data=f"gamif:reward:edit_field:{reward_id}:cost"),
            InlineKeyboardButton(text="🔓 Conditions", callback_data=f"gamif:reward:edit_conditions:{reward_id}")
        ]
    ]

    # Si es Badge, agregar opciones específicas
    if reward.reward_type == RewardType.BADGE.value:
        keyboard_buttons.append([
            InlineKeyboardButton(text="🎨 Icono Badge", callback_data=f"gamif:reward:edit_badge_icon:{reward_id}"),
            InlineKeyboardButton(text="⭐ Rareza Badge", callback_data=f"gamif:reward:edit_badge_rarity:{reward_id}")
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:reward:view:{reward_id}")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reward:edit_field:"))
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de campo."""
    parts = callback.data.split(":")
    reward_id = int(parts[3])
    field = parts[4]

    await state.update_data(reward_id=reward_id, field=field)

    field_names = {
        "name": ("📝 Nombre", RewardConfigStates.waiting_for_name),
        "description": ("📄 Descripción", RewardConfigStates.waiting_for_description),
        "cost": ("💰 Costo", RewardConfigStates.waiting_for_cost)
    }

    field_name, state_to_set = field_names[field]

    text = f"✏️ <b>EDITAR {field_name.upper()}</b>\n\n"
    text += f"Envía el nuevo valor:"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(state_to_set)
    await callback.answer()


@router.message(RewardConfigStates.waiting_for_name)
async def process_edit_name(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa edición de nombre."""
    data = await state.get_data()
    reward_id = data['reward_id']

    new_name = message.text.strip()

    if len(new_name) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres.")
        return

    try:
        reward = await gamification.reward.update_reward(reward_id, name=new_name)
        await message.answer(
            f"✅ Nombre actualizado\n\n"
            f"<b>{reward.name}</b>",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating reward name: {e}")
        await message.answer("❌ Error al actualizar nombre")
        await state.clear()


@router.message(RewardConfigStates.waiting_for_description)
async def process_edit_description(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa edición de descripción."""
    data = await state.get_data()
    reward_id = data['reward_id']

    new_description = message.text.strip()

    if len(new_description) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres.")
        return

    try:
        await gamification.reward.update_reward(reward_id, description=new_description)
        await message.answer("✅ Descripción actualizada")
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating reward description: {e}")
        await message.answer("❌ Error al actualizar descripción")
        await state.clear()


@router.message(RewardConfigStates.waiting_for_cost)
async def process_edit_cost(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa edición de costo."""
    data = await state.get_data()
    reward_id = data['reward_id']

    try:
        cost = int(message.text)
        if cost < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número mayor o igual a 0 (0 = no comprable).")
        return

    try:
        cost_value = cost if cost > 0 else None
        reward = await gamification.reward.update_reward(reward_id, cost_besitos=cost_value)
        cost_text = f"{reward.cost_besitos} besitos" if reward.cost_besitos else "No comprable"
        await message.answer(
            f"✅ Costo actualizado\n\n"
            f"<b>{reward.name}</b>: {cost_text}",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating reward cost: {e}")
        await message.answer("❌ Error al actualizar costo")
        await state.clear()


# ========================================
# EDICIÓN DE UNLOCK CONDITIONS
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:edit_conditions:"))
async def edit_conditions_menu(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Muestra menú de edición de unlock conditions."""
    reward_id = int(callback.data.split(":")[-1])
    reward = await gamification.reward.get_reward_by_id(reward_id)

    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    await state.update_data(reward_id=reward_id)

    # Parsear condiciones actuales
    current_conditions = "Sin condiciones"
    if reward.unlock_conditions:
        try:
            conditions = json.loads(reward.unlock_conditions)
            current_conditions = _format_unlock_conditions(conditions)
        except (json.JSONDecodeError, TypeError):
            current_conditions = "Condiciones inválidas"

    text = f"🔓 <b>EDITAR UNLOCK CONDITIONS</b>\n\n"
    text += f"Recompensa: <b>{reward.name}</b>\n"
    text += f"Condiciones actuales:\n{current_conditions}\n\n"
    text += "Selecciona tipo de condición:"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Misión", callback_data=f"gamif:condition:mission:{reward_id}"),
            InlineKeyboardButton(text="⭐ Nivel", callback_data=f"gamif:condition:level:{reward_id}")
        ],
        [
            InlineKeyboardButton(text="💰 Besitos", callback_data=f"gamif:condition:besitos:{reward_id}"),
            InlineKeyboardButton(text="❌ Sin Condición", callback_data=f"gamif:condition:none:{reward_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:reward:edit:{reward_id}")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:condition:mission:"))
async def set_mission_condition(callback: CallbackQuery, state: FSMContext):
    """Establece condición tipo misión."""
    reward_id = int(callback.data.split(":")[-1])
    await state.update_data(reward_id=reward_id, condition_type='mission')

    text = "📋 <b>CONDICIÓN: MISIÓN</b>\n\n"
    text += "Envía el ID de la misión requerida:"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(RewardConfigStates.waiting_for_mission_id)
    await callback.answer()


@router.message(RewardConfigStates.waiting_for_mission_id)
async def process_mission_id(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa ID de misión."""
    data = await state.get_data()
    reward_id = data['reward_id']

    try:
        mission_id = int(message.text)
        if mission_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    # Verificar que la misión existe
    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await message.answer(f"❌ No existe misión con ID {mission_id}")
        return

    # Actualizar conditions
    conditions = {"type": "mission", "mission_id": mission_id}

    try:
        await gamification.reward.update_reward(reward_id, unlock_conditions=conditions)
        await message.answer(
            f"✅ Condición actualizada\n\n"
            f"Requiere completar misión: {mission.name}",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating conditions: {e}")
        await message.answer("❌ Error al actualizar condición")
        await state.clear()


@router.callback_query(F.data.startswith("gamif:condition:level:"))
async def set_level_condition(callback: CallbackQuery, state: FSMContext):
    """Establece condición tipo nivel."""
    reward_id = int(callback.data.split(":")[-1])
    await state.update_data(reward_id=reward_id, condition_type='level')

    text = "⭐ <b>CONDICIÓN: NIVEL</b>\n\n"
    text += "Envía el ID del nivel requerido:"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(RewardConfigStates.waiting_for_level_id)
    await callback.answer()


@router.message(RewardConfigStates.waiting_for_level_id)
async def process_level_id(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa ID de nivel."""
    data = await state.get_data()
    reward_id = data['reward_id']

    try:
        level_id = int(message.text)
        if level_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    # Verificar que el nivel existe
    level = await gamification.level.get_level_by_id(level_id)
    if not level:
        await message.answer(f"❌ No existe nivel con ID {level_id}")
        return

    # Actualizar conditions
    conditions = {"type": "level", "level_id": level_id}

    try:
        await gamification.reward.update_reward(reward_id, unlock_conditions=conditions)
        await message.answer(
            f"✅ Condición actualizada\n\n"
            f"Requiere alcanzar nivel: {level.name}",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating conditions: {e}")
        await message.answer("❌ Error al actualizar condición")
        await state.clear()


@router.callback_query(F.data.startswith("gamif:condition:besitos:"))
async def set_besitos_condition(callback: CallbackQuery, state: FSMContext):
    """Establece condición tipo besitos."""
    reward_id = int(callback.data.split(":")[-1])
    await state.update_data(reward_id=reward_id, condition_type='besitos')

    text = "💰 <b>CONDICIÓN: BESITOS</b>\n\n"
    text += "Envía la cantidad mínima de besitos requerida:"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(RewardConfigStates.waiting_for_min_besitos)
    await callback.answer()


@router.message(RewardConfigStates.waiting_for_min_besitos)
async def process_min_besitos(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa cantidad mínima de besitos."""
    data = await state.get_data()
    reward_id = data['reward_id']

    try:
        min_besitos = int(message.text)
        if min_besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    # Actualizar conditions
    conditions = {"type": "besitos", "min_besitos": min_besitos}

    try:
        await gamification.reward.update_reward(reward_id, unlock_conditions=conditions)
        await message.answer(
            f"✅ Condición actualizada\n\n"
            f"Requiere al menos {min_besitos:,} besitos"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating conditions: {e}")
        await message.answer("❌ Error al actualizar condición")
        await state.clear()


@router.callback_query(F.data.startswith("gamif:condition:none:"))
async def remove_conditions(callback: CallbackQuery, gamification: GamificationContainer):
    """Elimina condiciones de unlock."""
    reward_id = int(callback.data.split(":")[-1])

    try:
        await gamification.reward.update_reward(reward_id, unlock_conditions=None)
        await callback.answer("✅ Condiciones eliminadas", show_alert=True)

        # Volver a vista de edición
        callback.data = f"gamif:reward:edit:{reward_id}"
        await edit_reward_menu(callback, gamification)
    except Exception as e:
        logger.error(f"Error removing conditions: {e}")
        await callback.answer("❌ Error al eliminar condiciones", show_alert=True)


# ========================================
# EDICIÓN DE BADGES (ESPECIAL)
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:edit_badge_icon:"))
async def edit_badge_icon(callback: CallbackQuery, state: FSMContext):
    """Edita icono de badge."""
    reward_id = int(callback.data.split(":")[-1])
    await state.update_data(reward_id=reward_id)

    text = "🎨 <b>EDITAR ICONO DE BADGE</b>\n\n"
    text += "Envía el nuevo emoji para el badge:"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(RewardConfigStates.waiting_for_badge_icon)
    await callback.answer()


@router.message(RewardConfigStates.waiting_for_badge_icon)
async def process_badge_icon(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa icono de badge."""
    data = await state.get_data()
    reward_id = data['reward_id']

    icon = message.text.strip()

    # Validar emoji
    if not is_valid_emoji(icon):
        await message.answer("❌ Debe ser un emoji válido.")
        return

    try:
        # Actualizar Badge
        from sqlalchemy import select, update
        from bot.gamification.database.models import Badge

        stmt = update(Badge).where(Badge.id == reward_id).values(icon=icon)
        await gamification.reward.session.execute(stmt)
        await gamification.reward.session.commit()

        await message.answer(f"✅ Icono actualizado: {icon}")
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating badge icon: {e}")
        await message.answer("❌ Error al actualizar icono")
        await state.clear()


@router.callback_query(F.data.startswith("gamif:reward:edit_badge_rarity:"))
async def edit_badge_rarity(callback: CallbackQuery, state: FSMContext):
    """Edita rareza de badge."""
    reward_id = int(callback.data.split(":")[-1])
    await state.update_data(reward_id=reward_id)

    text = "⭐ <b>EDITAR RAREZA DE BADGE</b>\n\n"
    text += "Selecciona la nueva rareza:"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Común", callback_data=f"gamif:set_rarity:{reward_id}:common"),
            InlineKeyboardButton(text="Rara", callback_data=f"gamif:set_rarity:{reward_id}:rare")
        ],
        [
            InlineKeyboardButton(text="Épica", callback_data=f"gamif:set_rarity:{reward_id}:epic"),
            InlineKeyboardButton(text="Legendaria", callback_data=f"gamif:set_rarity:{reward_id}:legendary")
        ],
        [
            InlineKeyboardButton(text="🔙 Cancelar", callback_data=f"gamif:reward:edit:{reward_id}")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:set_rarity:"))
async def process_badge_rarity(callback: CallbackQuery, gamification: GamificationContainer):
    """Procesa rareza de badge."""
    parts = callback.data.split(":")
    reward_id = int(parts[2])
    rarity_str = parts[3]

    rarity_map = {
        "common": BadgeRarity.COMMON,
        "rare": BadgeRarity.RARE,
        "epic": BadgeRarity.EPIC,
        "legendary": BadgeRarity.LEGENDARY
    }

    rarity = rarity_map.get(rarity_str)

    try:
        # Actualizar Badge
        from sqlalchemy import update
        from bot.gamification.database.models import Badge

        stmt = update(Badge).where(Badge.id == reward_id).values(rarity=rarity.value)
        await gamification.reward.session.execute(stmt)
        await gamification.reward.session.commit()

        await callback.answer(f"✅ Rareza actualizada: {rarity.value}", show_alert=True)

        # Volver a vista de edición
        callback.data = f"gamif:reward:edit:{reward_id}"
        await edit_reward_menu(callback, gamification)
    except Exception as e:
        logger.error(f"Error updating badge rarity: {e}")
        await callback.answer("❌ Error al actualizar rareza", show_alert=True)


# ========================================
# ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:toggle:"))
async def toggle_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """Activa o desactiva recompensa."""
    reward_id = int(callback.data.split(":")[-1])

    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    new_state = not reward.active

    await gamification.reward.update_reward(reward_id, active=new_state)

    status_text = "activada" if new_state else "desactivada"
    await callback.answer(f"✅ Recompensa {status_text}", show_alert=True)

    # Refrescar vista
    await view_reward(callback, gamification)


# ========================================
# ELIMINAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:delete:"))
async def delete_reward_confirm(callback: CallbackQuery, gamification: GamificationContainer):
    """Pide confirmación para eliminar."""
    reward_id = int(callback.data.split(":")[-1])

    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    # Obtener estadísticas de usuarios
    users_count = await gamification.reward.get_users_with_reward(reward_id)

    text = f"⚠️ <b>CONFIRMAR ELIMINACIÓN</b>\n\n"
    text += f"Recompensa: <b>{reward.name}</b>\n\n"

    if users_count > 0:
        text += f"⚠️ <b>ADVERTENCIA:</b> {users_count} usuario(s) tienen esta recompensa.\n\n"
        text += "Al eliminar, la perderán.\n\n"

    text += "¿Estás seguro de eliminar esta recompensa?"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚠️ Sí, Eliminar", callback_data=f"gamif:reward:delete_confirm:{reward_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:reward:view:{reward_id}")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reward:delete_confirm:"))
async def confirm_delete_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """Elimina recompensa (soft-delete)."""
    reward_id = int(callback.data.split(":")[-1])

    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    await gamification.reward.delete_reward(reward_id)

    await callback.answer("✅ Recompensa eliminada", show_alert=True)
    await rewards_menu(callback, gamification)
