"""
Handlers CRUD para configuración de recompensas de gamificación.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List
import json

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import RewardType, BadgeRarity
from bot.gamification.utils.validators import (
    validate_reward_metadata,
    validate_unlock_conditions,
    is_valid_emoji
)

router = Router()


class RewardConfigStates(StatesGroup):
    """Estados para configuración de recompensas."""
    waiting_name = State()
    waiting_description = State()
    waiting_type = State()
    waiting_cost = State()
    waiting_metadata = State()
    # Badge specific
    waiting_badge_icon = State()
    waiting_badge_rarity = State()
    # Conditions
    editing_conditions = State()
    waiting_condition_type = State()
    waiting_condition_value = State()
    building_multiple_conditions = State()


# ========================================
# CONSTANTES Y AYUDANTES
# ========================================
REWARD_TYPE_EMOJIS = {
    RewardType.BADGE: "🏆",
    RewardType.ITEM: "🎁",
    RewardType.PERMISSION: "🔓",
    RewardType.TITLE: "🏷️",
    RewardType.BESITOS: "💰"
}

BADGE_RARITY_EMOJIS = {
    BadgeRarity.COMMON: "🟢",
    BadgeRarity.RARE: "🔵",
    BadgeRarity.EPIC: "🟣",
    BadgeRarity.LEGENDARY: "⭐"
}

REWARD_TYPE_NAMES = {
    RewardType.BADGE: "Badge",
    RewardType.ITEM: "Item",
    RewardType.PERMISSION: "Permiso",
    RewardType.TITLE: "Título",
    RewardType.BESITOS: "Besitos"
}


def format_unlock_condition_display(conditions: dict) -> str:
    """Formatea condiciones de unlock para mostrar de forma legible."""
    try:
        condition_data = conditions if isinstance(conditions, dict) else json.loads(conditions)
        
        if condition_data.get('type') == 'mission':
            mission_id = condition_data.get('mission_id')
            return f"Completar misión ID: {mission_id}"
        
        elif condition_data.get('type') == 'level':
            level_id = condition_data.get('level_id')
            return f"Alcanzar nivel ID: {level_id}"
        
        elif condition_data.get('type') == 'besitos':
            min_besitos = condition_data.get('min_besitos')
            return f"{min_besitos:,} besitos totales"
        
        elif condition_data.get('type') == 'multiple':
            conditions_list = condition_data.get('conditions', [])
            if not conditions_list:
                return "Condiciones múltiples (sin especificar)"
            
            formatted_conds = []
            for i, cond in enumerate(conditions_list):
                formatted_conds.append(f"• {format_unlock_condition_display(cond)}")
            
            return "Requiere TODO lo siguiente:\n" + "\n".join(formatted_conds)
        
        else:
            return str(condition_data)
    except Exception:
        return str(conditions)


def format_metadata_display(reward_type: str, metadata: dict) -> str:
    """Formatea metadata para mostrar de forma legible."""
    try:
        if reward_type == 'badge':
            metadata_data = metadata if isinstance(metadata, dict) else json.loads(metadata) if metadata else {}
            icon = metadata_data.get('icon', '?')
            rarity = metadata_data.get('rarity', '?')
            return f"{icon} ({rarity})"
        elif reward_type == 'permission':
            metadata_data = metadata if isinstance(metadata, dict) else json.loads(metadata) if metadata else {}
            perm_key = metadata_data.get('permission_key', 'N/A')
            duration = metadata_data.get('duration_days', 'Permanente')
            return f"{perm_key} ({duration} días)" if duration != 'Permanente' else f"{perm_key}"
        elif reward_type == 'title':
            metadata_data = metadata if isinstance(metadata, dict) else json.loads(metadata) if metadata else {}
            title = metadata_data.get('title', 'Título no especificado')
            icon = metadata_data.get('icon', '')
            return f"{icon} {title}".strip()
        elif reward_type == 'item':
            metadata_data = metadata if isinstance(metadata, dict) else json.loads(metadata) if metadata else {}
            item_type = metadata_data.get('item_type', 'N/A')
            item_id = metadata_data.get('item_id', 'N/A')
            return f"{item_type}: {item_id}"
        elif reward_type == 'besitos':
            metadata_data = metadata if isinstance(metadata, dict) else json.loads(metadata) if metadata else {}
            amount = metadata_data.get('amount', 0)
            return f"{amount:,} besitos"
        else:
            return str(metadata)
    except Exception:
        return str(metadata)


def get_reward_icon(reward: 'Reward') -> str:
    """Obtiene icono apropiado para la recompensa."""
    if reward.reward_type == RewardType.BADGE:
        # Para badges, obtenemos el icono del badge si es posible
        try:
            metadata = json.loads(reward.reward_metadata) if reward.reward_metadata else {}
            return metadata.get('icon', REWARD_TYPE_EMOJIS.get(reward.reward_type, "❓"))
        except:
            return REWARD_TYPE_EMOJIS.get(reward.reward_type, "❓")
    else:
        return REWARD_TYPE_EMOJIS.get(reward.reward_type, "❓")


# ========================================
# MENÚ PRINCIPAL DE RECOMPENSAS (Con Filtros)
# ========================================

@router.callback_query(F.data == "gamif:admin:rewards")
async def rewards_menu(callback: CallbackQuery, state: FSMContext, session):
    """Muestra lista de recompensas configuradas con filtros."""
    await state.update_data(current_filter=None, current_page=1)
    await show_rewards_list(callback, state, session, reward_type=None)


async def show_rewards_list(callback: CallbackQuery, state: FSMContext, session, reward_type: Optional[str] = None):
    """Muestra lista de recompensas con opción de filtrado."""
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    
    # Obtener recompensas
    all_rewards = await gamification.reward.get_all_rewards(active_only=True, reward_type=reward_type)
    
    # Filtros para mostrar
    filter_buttons = [
        [
            InlineKeyboardButton(text="🏆 Badges", callback_data="gamif:rewards:filter:badge"),
            InlineKeyboardButton(text="🎁 Items", callback_data="gamif:rewards:filter:item")
        ],
        [
            InlineKeyboardButton(text="🔓 Permisos", callback_data="gamif:rewards:filter:permission"),
            InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:rewards:filter:besitos")
        ],
        [
            InlineKeyboardButton(text="🏷️ Títulos", callback_data="gamif:rewards:filter:title"),
            InlineKeyboardButton(text=" TODOS ", callback_data="gamif:rewards:filter:all")
        ]
    ]
    
    text = f"🎁 <b>RECOMPENSAS CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━\n\n"
    
    current_filter_name = "Todas" if not reward_type or reward_type == 'all' else REWARD_TYPE_NAMES.get(reward_type, reward_type.title())
    text += f"<b>Filtro:</b> {current_filter_name}\n"
    text += f"<b>Total:</b> {len(all_rewards)} recompensa(s)\n\n"
    
    if not all_rewards:
        text += "No hay recompensas configuradas.\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Crear Primera Recompensa", callback_data="gamif:reward:create:start")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])
    else:
        # Mostrar recompensas
        for reward in all_rewards:
            status = "✅" if reward.active else "❌"
            icon = get_reward_icon(reward)
            
            # Obtener estadísticas
            users_count = await gamification.reward.get_users_with_reward(reward.id)
            
            # Formatear costo
            cost_text = f" ({reward.cost_besitos:,} besitos)" if reward.cost_besitos else " (gratis)"
            
            text += f"{status} {icon} <b>{reward.name}</b>\n"
            text += f"   • {REWARD_TYPE_NAMES.get(reward.reward_type, reward.reward_type)}{cost_text}\n"
            text += f"   • {users_count:,} usuarios lo tienen\n\n"
        
        # Botones de cada recompensa
        keyboard_buttons = []
        for reward in all_rewards:
            icon = get_reward_icon(reward)
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{icon} {reward.name}",
                    callback_data=f"gamif:reward:view:{reward.id}"
                ),
                InlineKeyboardButton(
                    text="✏️",
                    callback_data=f"gamif:reward:edit:{reward.id}"
                )
            ])
        
        # Añadir botones de filtros y acción
        keyboard_buttons.extend(filter_buttons)
        keyboard_buttons.extend([
            [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="gamif:reward:create:start")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:rewards:filter:"))
async def filter_rewards(callback: CallbackQuery, state: FSMContext):
    """Filtra recompensas por tipo."""
    reward_type = callback.data.split(":")[-1]
    
    if reward_type == 'all':
        filter_type = None
    else:
        filter_type = reward_type
    
    await state.update_data(current_filter=filter_type, current_page=1)
    await show_rewards_list(callback, state, reward_type=filter_type)


# ========================================
# CREAR NUEVA RECOMPENSA
# ========================================

@router.callback_query(F.data == "gamif:reward:create:start")
async def start_create_reward(callback: CallbackQuery, state: FSMContext):
    """Inicia proceso de crear recompensa."""
    await callback.message.edit_text(
        "➕ <b>Crear Nueva Recompensa</b>\n\n"
        "Envía el nombre de la nueva recompensa.\n\n"
        "Ejemplo: 'Fanático del Chat' o 'Rey de las RACHAS'",
        parse_mode="HTML"
    )
    await state.set_state(RewardConfigStates.waiting_name)
    await callback.answer()


@router.message(RewardConfigStates.waiting_name)
async def receive_reward_name(message: Message, state: FSMContext):
    """Recibe nombre de la recompensa."""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ El nombre debe tener al menos 2 caracteres. Intenta de nuevo:")
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ Nombre: <b>{name}</b>\n\n"
        f"Ahora envía la descripción de la recompensa.\n\n"
        f"Ejemplo: 'Otorgado a usuarios que reaccionan constantemente'",
        parse_mode="HTML"
    )
    await state.set_state(RewardConfigStates.waiting_description)


@router.message(RewardConfigStates.waiting_description)
async def receive_reward_description(message: Message, state: FSMContext):
    """Recibe descripción de la recompensa."""
    description = message.text.strip()
    
    if len(description) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres. Intenta de nuevo:")
        return
    
    await state.update_data(description=description)
    
    # Mostrar opciones de tipo de recompensa
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 Badge", callback_data="gamif:reward:type:badge"),
            InlineKeyboardButton(text="🎁 Item", callback_data="gamif:reward:type:item")
        ],
        [
            InlineKeyboardButton(text="🔓 Permiso", callback_data="gamif:reward:type:permission"),
            InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:reward:type:besitos")
        ],
        [
            InlineKeyboardButton(text="🏷️ Título", callback_data="gamif:reward:type:title"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="gamif:admin:rewards")
        ]
    ])
    
    await message.answer(
        f"✅ Nombre: {state.data['name']}\n"
        f"✅ Descripción: {description}\n\n"
        f"Selecciona el tipo de recompensa:",
        reply_markup=keyboard
    )
    await state.set_state(RewardConfigStates.waiting_type)


@router.callback_query(F.data.startswith("gamif:reward:type:"))
async def receive_reward_type(callback: CallbackQuery, state: FSMContext):
    """Recibe tipo de recompensa."""
    reward_type = callback.data.split(":")[-1]
    
    try:
        # Validar tipo de recompensa
        RewardType(reward_type)
    except ValueError:
        await callback.answer("❌ Tipo de recompensa no válido", show_alert=True)
        return
    
    await state.update_data(reward_type=reward_type)
    
    # Preguntar si es comprable
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Comprable", callback_data="gamif:reward:cost:yes"),
            InlineKeyboardButton(text="🎁 Gratis", callback_data="gamif:reward:cost:no")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="gamif:admin:rewards")
        ]
    ])
    
    await callback.message.edit_text(
        f"🏷️ <b>Tipo:</b> {REWARD_TYPE_NAMES.get(reward_type, reward_type.title())}\n\n"
        f"¿La recompensa será comprable?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reward:cost:"))
async def receive_reward_cost_preference(callback: CallbackQuery, state: FSMContext):
    """Recibe preferencia de costo."""
    has_cost = callback.data.split(":")[-1] == 'yes'
    
    if has_cost:
        await callback.message.edit_text(
            "💰 <b>Costo de la Recompensa</b>\n\n"
            "Envía el costo en besitos (número positivo):",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_cost)
    else:
        # No tiene costo, ir directo a especificar metadata
        await state.update_data(cost_besitos=None)
        await ask_metadata_for_type(callback, state)


@router.message(RewardConfigStates.waiting_cost)
async def receive_reward_cost(message: Message, state: FSMContext):
    """Recibe costo de la recompensa."""
    try:
        cost = int(message.text)
        if cost <= 0:
            raise ValueError("Costo debe ser positivo")
    except ValueError:
        await message.answer("❌ Debe ser un número entero positivo. Intenta de nuevo:")
        return
    
    await state.update_data(cost_besitos=cost)
    
    # Ir a especificar metadata según tipo
    await ask_metadata_for_type(message, state)


async def ask_metadata_for_type(message: Message, state: FSMContext):
    """Pregunta por metadata según tipo de recompensa."""
    data = await state.get_data()
    reward_type = data['reward_type']
    
    # Manejar casos especiales
    if reward_type == 'badge':
        # Preguntar por icono del badge
        await message.answer(
            "🏆 <b>Badge</b>\n\n"
            "Envía el icono del badge (emoji) para el badge:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_badge_icon)
    elif reward_type == 'permission':
        await message.answer(
            "🔓 <b>Permiso</b>\n\n"
            "Envía los metadatos en formato JSON:\n\n"
            "<code>{\"permission_key\": \"custom_emoji\", \"duration_days\": 30}</code>\n\n"
            "O envía solo el permission_key (ej: custom_emoji):",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_metadata)
    elif reward_type == 'title':
        await message.answer(
            "🏷️ <b>Título</b>\n\n"
            "Envía los metadatos en formato JSON:\n\n"
            "<code>{\"title\": \"Rey del Chat\", \"icon\": \"👑\", \"color\": \"#FFD700\"}</code>\n\n"
            "O envía solo el título (ej: Rey del Chat):",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_metadata)
    elif reward_type == 'item':
        await message.answer(
            "🎁 <b>Item</b>\n\n"
            "Envía los metadatos en formato JSON:\n\n"
            "<code>{\"item_type\": \"sticker\", \"item_id\": \"12345\", \"quantity\": 1}</code>\n\n"
            "O envía solo el tipo de item (ej: sticker):",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_metadata)
    elif reward_type == 'besitos':
        await message.answer(
            "💰 <b>Besitos</b>\n\n"
            "Envía los metadatos en formato JSON:\n\n"
            "<code>{\"amount\": 500}</code>\n\n"
            "O envía solo la cantidad (ej: 500):",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_metadata)
    else:
        # Otros tipos - pedir metadata genérica
        await message.answer(
            f"📦 <b>{REWARD_TYPE_NAMES.get(reward_type, reward_type.title())}</b>\n\n"
            f"Envía los metadatos en formato JSON:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_metadata)


@router.message(RewardConfigStates.waiting_badge_icon)
async def receive_badge_icon(message: Message, state: FSMContext):
    """Recibe icono del badge."""
    icon = message.text.strip()
    
    # Validar que sea un emoji
    if not is_valid_emoji(icon):
        await message.answer("❌ Debe ser un emoji válido. Intenta de nuevo:")
        return
    
    await state.update_data(badge_icon=icon)
    
    # Preguntar por rareza
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Común", callback_data="gamif:badge:rarity:common"),
            InlineKeyboardButton(text="🔵 Raro", callback_data="gamif:badge:rarity:rare")
        ],
        [
            InlineKeyboardButton(text="🟣 Épico", callback_data="gamif:badge:rarity:epic"),
            InlineKeyboardButton(text="⭐ Legendario", callback_data="gamif:badge:rarity:legendary")
        ]
    ])
    
    await message.answer(
        f"✅ Icono: {icon}\n\n"
        f"Selecciona la rareza del badge:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("gamif:badge:rarity:"))
async def receive_badge_rarity(callback: CallbackQuery, state: FSMContext):
    """Recibe rareza del badge."""
    rarity = callback.data.split(":")[-1]
    
    try:
        BadgeRarity(rarity)
    except ValueError:
        await callback.answer("❌ Rareza no válida", show_alert=True)
        return
    
    await state.update_data(badge_rarity=rarity)
    
    # Construir metadata para badge
    data = await state.get_data()
    metadata = {
        "icon": data['badge_icon'],
        "rarity": rarity
    }
    await state.update_data(metadata=metadata)
    
    # Ir a configurar condiciones
    await ask_reward_conditions(callback, state)


@router.message(RewardConfigStates.waiting_metadata)
async def receive_metadata(message: Message, state: FSMContext):
    """Recibe metadata de la recompensa."""
    metadata_input = message.text.strip()
    data = await state.get_data()
    reward_type = data['reward_type']
    
    try:
        # Si es número, construir metadata básica según tipo
        if metadata_input.isdigit():
            if reward_type == 'besitos':
                metadata = {"amount": int(metadata_input)}
            elif reward_type == 'permission':
                metadata = {"permission_key": metadata_input, "duration_days": None}
            elif reward_type == 'title':
                metadata = {"title": metadata_input, "icon": None, "color": None}
            elif reward_type == 'item':
                metadata = {"item_type": metadata_input, "item_id": None, "quantity": None}
            else:
                await message.answer("❌ Para este tipo necesitas enviar JSON completo:")
                return
        else:
            # Intentar parsear como JSON
            metadata = json.loads(metadata_input)
        
        # Validar con el validador existente
        is_valid, error = validate_reward_metadata(RewardType(reward_type), metadata)
        if not is_valid:
            await message.answer(f"❌ Metadata inválida: {error}\n\nIntenta de nuevo:")
            return
        
        await state.update_data(metadata=metadata)
        
        # Ir a configurar condiciones
        await ask_reward_conditions(message, state)
        
    except json.JSONDecodeError:
        await message.answer("❌ Formato JSON inválido. Intenta de nuevo:")
    except Exception as e:
        await message.answer(f"❌ Error en metadata: {str(e)}\n\nIntenta de nuevo:")


async def ask_reward_conditions(message: Message, state: FSMContext):
    """Pregunta por condiciones de unlock."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏁 Misión", callback_data="gamif:condition:type:mission"),
            InlineKeyboardButton(text="🏆 Nivel", callback_data="gamif:condition:type:level")
        ],
        [
            InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:condition:type:besitos"),
            InlineKeyboardButton(text="📋 Múltiple", callback_data="gamif:condition:type:multiple")
        ],
        [
            InlineKeyboardButton(text="❌ Ninguna", callback_data="gamif:condition:type:none")
        ]
    ])
    
    await message.answer(
        "🔓 <b>Condiciones de Desbloqueo</b>\n\n"
        "¿Qué condiciones debe cumplir un usuario para obtener esta recompensa?\n\n"
        "Selecciona el tipo de condición:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("gamif:condition:type:"))
async def select_condition_type(callback: CallbackQuery, state: FSMContext, session):
    """Selecciona tipo de condición."""
    condition_type = callback.data.split(":")[-1]

    if condition_type == 'none':
        # No condiciones
        await state.update_data(unlock_conditions=None)
        await create_reward_from_state(callback, state, session)
        return
    
    await state.update_data(condition_type=condition_type)
    
    if condition_type == 'mission':
        # Pedir ID de misión
        await callback.message.edit_text(
            "🏁 <b>Condición: Misión</b>\n\n"
            "Envía el ID de la misión que debe completar el usuario:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'level':
        # Pedir ID de nivel
        await callback.message.edit_text(
            "🏆 <b>Condición: Nivel</b>\n\n"
            "Envía el ID del nivel que debe alcanzar el usuario:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'besitos':
        # Pedir cantidad mínima de besitos
        await callback.message.edit_text(
            "💰 <b>Condición: Besitos</b>\n\n"
            "Envía la cantidad mínima de besitos totales que debe tener el usuario:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'multiple':
        # Iniciar wizard para múltiples condiciones
        await callback.message.edit_text(
            "📋 <b>Condiciones Múltiples</b>\n\n"
            "Agrega la primera condición:\n\n"
            "¿Qué tipo de condición quieres agregar?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏁 Misión", callback_data="gamif:condition:add:mission"),
                    InlineKeyboardButton(text="🏆 Nivel", callback_data="gamif:condition:add:level")
                ],
                [
                    InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:condition:add:besitos"),
                    InlineKeyboardButton(text="✅ Finalizar", callback_data="gamif:condition:finish_multiple")
                ]
            ]),
            parse_mode="HTML"
        )
        await state.update_data(multiple_conditions=[])
        await state.set_state(RewardConfigStates.building_multiple_conditions)


@router.callback_query(F.data.startswith("gamif:condition:add:"))
async def add_condition_to_multiple(callback: CallbackQuery, state: FSMContext):
    """Agrega condición a condiciones múltiples."""
    condition_type = callback.data.split(":")[-1]
    
    await state.update_data(current_condition_type=condition_type)
    
    if condition_type == 'mission':
        await callback.message.edit_text(
            "🏁 <b>Agregar Misión</b>\n\n"
            "Envía el ID de la misión:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'level':
        await callback.message.edit_text(
            "🏆 <b>Agregar Nivel</b>\n\n"
            "Envía el ID del nivel:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'besitos':
        await callback.message.edit_text(
            "💰 <b>Agregar Besitos</b>\n\n"
            "Envía la cantidad mínima de besitos totales:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)


@router.message(RewardConfigStates.waiting_condition_value)
async def receive_condition_value(message: Message, state: FSMContext, session):
    """Recibe valor de condición."""
    data = await state.get_data()

    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError("Valor debe ser positivo")
    except ValueError:
        await message.answer("❌ Debe ser un número entero positivo. Intenta de nuevo:")
        return

    # Construir condición según tipo
    if data.get('condition_type') == 'multiple':
        # Agregar a condiciones múltiples
        condition_type = data['current_condition_type']
        condition = {"type": condition_type}

        if condition_type == 'mission':
            condition["mission_id"] = value
        elif condition_type == 'level':
            condition["level_id"] = value
        elif condition_type == 'besitos':
            condition["min_besitos"] = value

        # Validar condición individual
        is_valid, error = validate_unlock_conditions(condition)
        if not is_valid:
            await message.answer(f"❌ Condición inválida: {error}\n\nIntenta de nuevo:")
            return

        # Actualizar lista de condiciones
        current_conditions = data.get('multiple_conditions', [])
        current_conditions.append(condition)
        await state.update_data(multiple_conditions=current_conditions)

        # Volver al menú de agregar condiciones
        await message.answer(
            f"✅ Condición agregada: {format_unlock_condition_display(condition)}\n\n"
            "Agrega otra condición o finaliza:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏁 Misión", callback_data="gamif:condition:add:mission"),
                    InlineKeyboardButton(text="🏆 Nivel", callback_data="gamif:condition:add:level")
                ],
                [
                    InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:condition:add:besitos"),
                    InlineKeyboardButton(text="✅ Finalizar", callback_data="gamif:condition:finish_multiple")
                ]
            ]),
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.building_multiple_conditions)

    else:
        # Condición individual
        condition = {"type": data['condition_type']}

        if data['condition_type'] == 'mission':
            condition["mission_id"] = value
        elif data['condition_type'] == 'level':
            condition["level_id"] = value
        elif data['condition_type'] == 'besitos':
            condition["min_besitos"] = value

        # Validar
        is_valid, error = validate_unlock_conditions(condition)
        if not is_valid:
            await message.answer(f"❌ Condición inválida: {error}\n\nIntenta de nuevo:")
            return

        await state.update_data(unlock_conditions=condition)
        await create_reward_from_state(message, state, session)


@router.callback_query(F.data == "gamif:condition:finish_multiple")
async def finish_multiple_conditions(callback: CallbackQuery, state: FSMContext, session):
    """Finaliza condiciones múltiples."""
    data = await state.get_data()
    conditions = data.get('multiple_conditions', [])

    if not conditions:
        await callback.answer("❌ Debes agregar al menos una condición", show_alert=True)
        return

    unlock_conditions = {
        "type": "multiple",
        "conditions": conditions
    }

    # Validar condiciones múltiples
    is_valid, error = validate_unlock_conditions(unlock_conditions)
    if not is_valid:
        await callback.answer(f"❌ Condiciones inválidas: {error}", show_alert=True)
        return

    await state.update_data(unlock_conditions=unlock_conditions)
    await create_reward_from_state(callback, state, session)


async def create_reward_from_state(message_or_callback: Message | CallbackQuery, state: FSMContext, session):
    """Crea recompensa desde datos de estado."""
    data = await state.get_data()
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    
    try:
        # Crear recompensa según tipo
        if data['reward_type'] == 'badge':
            reward, badge = await gamification.reward.create_badge(
                name=data['name'],
                description=data['description'],
                icon=data['badge_icon'],
                rarity=BadgeRarity(data['badge_rarity']),
                cost_besitos=data['cost_besitos'],
                unlock_conditions=data['unlock_conditions'],
                created_by=message_or_callback.from_user.id
            )
        else:
            reward = await gamification.reward.create_reward(
                name=data['name'],
                description=data['description'],
                reward_type=RewardType(data['reward_type']),
                cost_besitos=data['cost_besitos'],
                unlock_conditions=data['unlock_conditions'],
                metadata=data['metadata'],
                created_by=message_or_callback.from_user.id
            )
        
        await message_or_callback.answer(
            f"✅ <b>Recompensa Creada Exitosamente</b>\n\n"
            f"ID: {reward.id}\n"
            f"Nombre: {reward.name}\n"
            f"Tipo: {REWARD_TYPE_NAMES.get(reward.reward_type, reward.reward_type)}\n"
            f"Costo: {reward.cost_besitos or 'Gratis'} besitos\n\n"
            f"La recompensa está lista para que los usuarios la obtengan.",
            parse_mode="HTML"
        )
        
        await state.clear()
        
        # Volver a la lista de recompensas
        await state.update_data(current_filter=None, current_page=1)
        await show_rewards_list(message_or_callback, state, reward_type=None)
        
    except Exception as e:
        await message_or_callback.answer(f"❌ Error al crear recompensa: {str(e)}", show_alert=True)


# ========================================
# VER DETALLES DE RECOMPENSA
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:view:"))
async def view_reward_details(callback: CallbackQuery, session):
    """Muestra detalles de una recompensa específica."""
    reward_id = int(callback.data.split(":")[-1])
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reward = await gamification.reward.get_reward_by_id(reward_id)

    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    status = "✅ Activa" if reward.active else "❌ Inactiva"
    icon = get_reward_icon(reward)
    type_name = REWARD_TYPE_NAMES.get(reward.reward_type, reward.reward_type)

    # Obtener estadísticas
    users_count = await gamification.reward.get_users_with_reward(reward_id)
    
    # Formatear condiciones
    try:
        conditions_text = "Ninguna - Disponible para todos" if not reward.unlock_conditions else format_unlock_condition_display(reward.unlock_conditions)
    except:
        conditions_text = str(reward.unlock_conditions)
    
    # Formatear metadata
    try:
        metadata_text = format_metadata_display(reward.reward_type, reward.reward_metadata)
    except:
        metadata_text = str(reward.reward_metadata)
    
    text = f"""🎁 <b>RECOMPENSA: {reward.name}</b>
{icon} Tipo: {type_name}
{status}

📝 <b>DESCRIPCIÓN</b>
{reward.description}

💰 <b>CONFIGURACIÓN</b>
• Costo: {reward.cost_besitos or 'Gratis'} besitos
• Metadata: {metadata_text}

🔓 <b>CONDICIONES DE DESBLOQUEO</b>
{conditions_text}

📊 <b>ESTADÍSTICAS</b>
• Usuarios que lo tienen: {users_count:,}
• Tasa de obtención: {'N/A' if users_count == 0 else f'{users_count/1000:.2%}'}"""

    # Prepare keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar", callback_data=f"gamif:reward:edit:{reward_id}"),
            InlineKeyboardButton(
                text="🔄 Activar/Desactivar",
                callback_data=f"gamif:reward:toggle:{reward_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🔓 Editar Conditions", callback_data=f"gamif:reward:edit_conditions:{reward_id}"),
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:reward:delete:{reward_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:rewards")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# EDITAR RECOMPENSA
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:edit:"))
async def edit_reward_menu(callback: CallbackQuery, session):
    """Muestra menú de edición de recompensa."""
    reward_id = int(callback.data.split(":")[-1])
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reward = await gamification.reward.get_reward_by_id(reward_id)

    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    metadata_text = format_metadata_display(reward.reward_type, reward.reward_metadata)
    
    text = f"""✏️ <b>Editar Recompensa: {reward.name}</b>

Selecciona qué campo deseas editar:

• <b>Nombre:</b> {reward.name}
• <b>Descripción:</b> {reward.description[:50]}...
• <b>Costo:</b> {reward.cost_besitos or 'Gratis'} besitos
• <b>Metadata:</b> {metadata_text}
• <b>Activa:</b> {'Sí' if reward.active else 'No'}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nombre", callback_data=f"gamif:reward:edit_field:{reward_id}:name"),
            InlineKeyboardButton(text="📄 Descripción", callback_data=f"gamif:reward:edit_field:{reward_id}:description")
        ],
        [
            InlineKeyboardButton(text="💰 Costo", callback_data=f"gamif:reward:edit_field:{reward_id}:cost_besitos"),
            InlineKeyboardButton(text="⚙️ Metadata", callback_data=f"gamif:reward:edit_field:{reward_id}:metadata")
        ],
        [
            InlineKeyboardButton(text="🔓 Conditions", callback_data=f"gamif:reward:edit_conditions:{reward_id}"),
            InlineKeyboardButton(text="🔄 Activar/Desactivar", callback_data=f"gamif:reward:toggle:{reward_id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:reward:delete:{reward_id}"),
            InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:reward:view:{reward_id}")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reward:edit_field:"))
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de campo específico."""
    parts = callback.data.split(":")
    reward_id = int(parts[3])
    field = parts[4]
    
    await state.update_data(editing_reward_id=reward_id, editing_field=field)
    
    field_names = {
        'name': 'nombre',
        'description': 'descripción', 
        'cost_besitos': 'costo en besitos',
        'metadata': 'metadata (JSON)',
        'active': 'activo (sí/no)'
    }
    
    if field == 'cost_besitos':
        await callback.message.edit_text(
            f"💰 <b>Editar Costo</b>\n\n"
            f"Envía el nuevo costo en besitos (número positivo) o 0 para gratis:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_cost)
        await callback.answer()
        return
    elif field == 'metadata':
        await callback.message.edit_text(
            f"⚙️ <b>Editar Metadata</b>\n\n"
            f"Envía la nueva metadata en formato JSON:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_metadata)
        await callback.answer()
        return

    # Create a proper state for editing general fields
    await callback.message.edit_text(
        f"✏️ <b>Editar {field_names.get(field, field)}</b>\n\n"
        f"Envía el nuevo valor:",
        parse_mode="HTML"
    )
    await state.set_state(RewardConfigStates.waiting_description)  # Using general state for text
    await callback.answer()


@router.message(RewardConfigStates.waiting_name)  # Using it for general text input
async def receive_edited_general_field(message: Message, state: FSMContext, session):
    """Recibe valor editado para campo general."""
    data = await state.get_data()
    reward_id = data['editing_reward_id']
    field = data['editing_field']

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    try:
        if field == 'name':
            new_value = message.text.strip()
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres. Intenta de nuevo:")
                return
        elif field == 'description':
            new_value = message.text.strip()
            if len(new_value) < 5:
                await message.answer("❌ La descripción debe tener al menos 5 caracteres. Intenta de nuevo:")
                return
        else:
            await message.answer("❌ Campo no válido para editar")
            await state.clear()
            return

        # Update the reward
        update_data = {field: new_value}
        await gamification.reward.update_reward(reward_id, **update_data)

        await message.answer(
            f"✅ <b>Campo Actualizado</b>\n\n"
            f"Campo: {field}\n"
            f"Nuevo valor: {new_value[:50]}..."
        )

        await state.clear()

        # Volver a detalles de la recompensa - need to redirect to callback-based navigation
        # Send a new message with navigation options instead of calling view_reward_details with message
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Ver Recompensa", callback_data=f"gamif:reward:view:{reward_id}")],
            [InlineKeyboardButton(text="🔙 Volver al Menú", callback_data="gamif:admin:rewards")]
        ])

        await message.answer(
            "✅ <b>Campo Actualizado</b>\n\n"
            "¿Qué deseas hacer ahora?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"❌ Error al actualizar: {str(e)}")


@router.message(RewardConfigStates.waiting_cost)
async def receive_edited_cost(message: Message, state: FSMContext, session):
    """Recibe valor editado para costo."""
    try:
        cost = int(message.text)
        if cost < 0:
            raise ValueError("Costo no puede ser negativo")
    except ValueError:
        await message.answer("❌ Debe ser un número entero no negativo. Intenta de nuevo:")
        return

    data = await state.get_data()
    reward_id = data['editing_reward_id']

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    try:
        await gamification.reward.update_reward(reward_id, cost_besitos=cost if cost > 0 else None)

        await message.answer(
            f"✅ <b>Costo Actualizado</b>\n\n"
            f"Nuevo costo: {cost if cost > 0 else 'Gratis'} besitos"
        )

        await state.clear()

        # Volver a detalles de la recompensa - need to redirect to callback-based navigation
        # Send a new message with navigation options instead of calling view_reward_details with message
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Ver Recompensa", callback_data=f"gamif:reward:view:{reward_id}")],
            [InlineKeyboardButton(text="🔙 Volver al Menú", callback_data="gamif:admin:rewards")]
        ])

        await message.answer(
            "✅ <b>Costo Actualizado</b>\n\n"
            "¿Qué deseas hacer ahora?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"❌ Error al actualizar: {str(e)}")


@router.message(RewardConfigStates.waiting_metadata)
async def receive_edited_metadata(message: Message, state: FSMContext, session):
    """Recibe metadata editada."""
    metadata_input = message.text.strip()
    data = await state.get_data()
    reward_id = data['editing_reward_id']

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await message.answer("❌ Recompensa no encontrada")
        await state.clear()
        return
    
    try:
        # Intentar parsear como JSON
        metadata = json.loads(metadata_input)
        
        # Validar con el validador existente
        is_valid, error = validate_reward_metadata(RewardType(reward.reward_type), metadata)
        if not is_valid:
            await message.answer(f"❌ Metadata inválida: {error}\n\nIntenta de nuevo:")
            return
        
        # Actualizar la recompensa
        await gamification.reward.update_reward(reward_id, reward_metadata=metadata)
        
        await message.answer(
            f"✅ <b>Metadata Actualizada</b>\n\n"
            f"Tipo: {reward.reward_type}"
        )

        await state.clear()

        # Volver a detalles de la recompensa - need to redirect to callback-based navigation
        # Send a new message with navigation options instead of calling view_reward_details with message
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Ver Recompensa", callback_data=f"gamif:reward:view:{reward_id}")],
            [InlineKeyboardButton(text="🔙 Volver al Menú", callback_data="gamif:admin:rewards")]
        ])

        await message.answer(
            "✅ <b>Metadata Actualizada</b>\n\n"
            "¿Qué deseas hacer ahora?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except json.JSONDecodeError:
        await message.answer("❌ Formato JSON inválido. Intenta de nuevo:")
    except Exception as e:
        await message.answer(f"❌ Error al actualizar metadata: {str(e)}")


# ========================================
# EDITAR CONDICIONES DE DESBLOQUEO
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:edit_conditions:"))
async def start_edit_conditions(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de condiciones de desbloqueo."""
    reward_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_reward_id=reward_id)
    
    # Mostrar menú para editar condiciones
    await callback.message.edit_text(
        "🔓 <b>Editar Condiciones de Desbloqueo</b>\n\n"
        "¿Qué tipo de condición quieres establecer?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏁 Misión", callback_data="gamif:edit_condition:type:mission"),
                InlineKeyboardButton(text="🏆 Nivel", callback_data="gamif:edit_condition:type:level")
            ],
            [
                InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:edit_condition:type:besitos"),
                InlineKeyboardButton(text="📋 Múltiple", callback_data="gamif:edit_condition:type:multiple")
            ],
            [
                InlineKeyboardButton(text="❌ Ninguna", callback_data="gamif:edit_condition:type:none"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:reward:view:{reward_id}")
            ]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(RewardConfigStates.waiting_condition_type)
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:edit_condition:type:"))
async def select_edit_condition_type(callback: CallbackQuery, state: FSMContext, session):
    """Selecciona tipo de condición para editar."""
    condition_type = callback.data.split(":")[-1]
    data = await state.get_data()
    reward_id = data['editing_reward_id']

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    if condition_type == 'none':
        # No condiciones
        await gamification.reward.update_reward(reward_id, unlock_conditions=None)
        
        await callback.answer("✅ Condiciones eliminadas", show_alert=True)
        await view_reward_details(callback, gamification)
        await state.clear()
        return
    
    await state.update_data(condition_type=condition_type)
    
    if condition_type == 'mission':
        # Pedir ID de misión
        await callback.message.edit_text(
            "🏁 <b>Condición: Misión</b>\n\n"
            "Envía el ID de la misión que debe completar el usuario:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'level':
        # Pedir ID de nivel
        await callback.message.edit_text(
            "🏆 <b>Condición: Nivel</b>\n\n"
            "Envía el ID del nivel que debe alcanzar el usuario:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'besitos':
        # Pedir cantidad mínima de besitos
        await callback.message.edit_text(
            "💰 <b>Condición: Besitos</b>\n\n"
            "Envía la cantidad mínima de besitos totales que debe tener el usuario:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'multiple':
        # Iniciar wizard para múltiples condiciones
        await callback.message.edit_text(
            "📋 <b>Editar Condiciones Múltiples</b>\n\n"
            "Agrega la primera condición:\n\n"
            "¿Qué tipo de condición quieres agregar?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏁 Misión", callback_data="gamif:edit_add_condition:mission"),
                    InlineKeyboardButton(text="🏆 Nivel", callback_data="gamif:edit_add_condition:level")
                ],
                [
                    InlineKeyboardButton(text="💰 Besitos", callback_data="gamif:edit_add_condition:besitos"),
                    InlineKeyboardButton(text="✅ Finalizar", callback_data="gamif:finish_edit_multiple")
                ]
            ]),
            parse_mode="HTML"
        )
        await state.update_data(multiple_conditions=[])
        await state.set_state(RewardConfigStates.building_multiple_conditions)


@router.callback_query(F.data.startswith("gamif:edit_add_condition:"))
async def add_condition_for_edit(callback: CallbackQuery, state: FSMContext):
    """Agrega condición a condiciones múltiples para edición."""
    condition_type = callback.data.split(":")[-1]
    
    await state.update_data(current_condition_type=condition_type)
    
    if condition_type == 'mission':
        await callback.message.edit_text(
            "🏁 <b>Agregar Misión</b>\n\n"
            "Envía el ID de la misión:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'level':
        await callback.message.edit_text(
            "🏆 <b>Agregar Nivel</b>\n\n"
            "Envía el ID del nivel:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)
        
    elif condition_type == 'besitos':
        await callback.message.edit_text(
            "💰 <b>Agregar Besitos</b>\n\n"
            "Envía la cantidad mínima de besitos totales:",
            parse_mode="HTML"
        )
        await state.set_state(RewardConfigStates.waiting_condition_value)


@router.callback_query(F.data == "gamif:finish_edit_multiple")
async def finish_editing_multiple_conditions(callback: CallbackQuery, state: FSMContext, session):
    """Finaliza edición de condiciones múltiples."""
    data = await state.get_data()
    conditions = data.get('multiple_conditions', [])
    reward_id = data['editing_reward_id']

    if not conditions:
        await callback.answer("❌ Debes agregar al menos una condición", show_alert=True)
        return

    unlock_conditions = {
        "type": "multiple",
        "conditions": conditions
    }

    # Validar condiciones múltiples
    is_valid, error = validate_unlock_conditions(unlock_conditions)
    if not is_valid:
        await callback.answer(f"❌ Condiciones inválidas: {error}", show_alert=True)
        return

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    try:
        await gamification.reward.update_reward(reward_id, unlock_conditions=unlock_conditions)

        await callback.answer("✅ Condiciones actualizadas", show_alert=True)
        await view_reward_details(callback, session)
        await state.clear()

    except Exception as e:
        await callback.answer(f"❌ Error al actualizar: {str(e)}", show_alert=True)


# ========================================
# TOGGLE ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:toggle:"))
async def toggle_reward(callback: CallbackQuery, session):
    """Activa o desactiva una recompensa."""
    reward_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    await gamification.reward.update_reward(reward_id, active=not reward.active)

    status_text = "activada" if not reward.active else "desactivada"
    await callback.answer(f"✅ Recompensa {status_text}", show_alert=True)

    # Refresh the view
    await view_reward_details(callback, session)


# ========================================
# ELIMINAR RECOMPENSA
# ========================================

@router.callback_query(F.data.startswith("gamif:reward:delete:"))
async def delete_reward_prompt(callback: CallbackQuery, session):
    """Pide confirmación para eliminar recompensa."""
    reward_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    # Check if reward has users
    users_count = await gamification.reward.get_users_with_reward(reward_id)

    if users_count > 0:
        text = f"""⚠️ <b>Advertencia: Eliminación con Usuarios</b>

Recompensa: <b>{reward.name}</b> (ID: {reward.id})
Usuarios afectados: <b>{users_count}</b>

⚠️ Esta recompensa ha sido obtenida por {users_count} usuario(s).
Al eliminarla, se ocultará de sus perfiles pero no se revocará.

¿Deseas continuar con la eliminación?

<b>Esta acción no se puede deshacer.</b>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Sí, Eliminar", callback_data=f"gamif:reward:delete_confirm:{reward_id}"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:reward:view:{reward_id}")
            ]
        ])
    else:
        text = f"""⚠️ <b>Confirmar Eliminación</b>

¿Estás seguro de eliminar la recompensa?

Nombre: <b>{reward.name}</b>
ID: {reward.id}
Tipo: {REWARD_TYPE_NAMES.get(reward.reward_type, reward.reward_type)}
Costo: {reward.cost_besitos or 'Gratis'} besitos

<b>Esta acción no se puede deshacer.</b>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Sí, Eliminar", callback_data=f"gamif:reward:delete_confirm:{reward_id}"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:reward:view:{reward_id}")
            ]
        ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reward:delete_confirm:"))
async def confirm_delete_reward(callback: CallbackQuery, state: FSMContext, session):
    """Confirma eliminación de recompensa (soft delete)."""
    reward_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    # Since the service already does a soft-delete, we'll use that
    success = await gamification.reward.delete_reward(reward_id)

    if success:
        await callback.answer("✅ Recompensa eliminada", show_alert=True)
        # Go back to main rewards menu
        await state.update_data(current_filter=None, current_page=1)
        await show_rewards_list(callback, state, session, reward_type=None)
    else:
        await callback.answer("❌ Error al eliminar recompensa", show_alert=True)