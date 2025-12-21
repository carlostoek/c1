"""
Handlers para historial de transacciones de besitos.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional
from math import ceil
import json

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import TransactionType

router = Router()


class TransactionHistoryStates(StatesGroup):
    """Estados para el historial de transacciones."""
    waiting_user_id = State()


# ========================================
# CONSTANTES Y AYUDANTES
# ========================================
PER_PAGE = 20

TRANSACTION_TYPE_EMOJIS = {
    TransactionType.REACTION: "💬",
    TransactionType.MISSION_REWARD: "🎯",
    TransactionType.PURCHASE: "🛒",
    TransactionType.ADMIN_GRANT: "⚙️",
    TransactionType.ADMIN_DEDUCT: "❌",
    TransactionType.REFUND: "🔄",
    TransactionType.STREAK_BONUS: "🔥",
    TransactionType.LEVEL_UP_BONUS: "🆙",
}

TYPE_FILTER_NAMES = {
    TransactionType.MISSION_REWARD: "Misiones",
    TransactionType.PURCHASE: "Compras", 
    TransactionType.ADMIN_GRANT: "Admin",
    TransactionType.ADMIN_DEDUCT: "Deducciones",
    TransactionType.REACTION: "Reacciones",
    TransactionType.REFUND: "Reembolsos",
    TransactionType.STREAK_BONUS: "Rachas",
    TransactionType.LEVEL_UP_BONUS: "Niveles"
}


def format_amount(amount: int) -> str:
    """Formatea cantidad de besitos con signo."""
    if amount > 0:
        return f"🟢 +{amount:,}"
    elif amount < 0:
        return f"🔴 {amount:,}"  # Already negative
    else:
        return f"🔵 {amount:,}"


def format_balance_change(prev_balance: Optional[int], new_balance: int) -> str:
    """Formatea el cambio de balance."""
    if prev_balance is not None:
        change = new_balance - prev_balance
        return f"Balance: {prev_balance:,} → {new_balance:,} ({'+' if change >= 0 else ''}{change:,})"
    else:
        return f"Balance: {new_balance:,}"


def format_transaction_display(transaction: dict) -> str:
    """Formatea una transacción para mostrar."""
    emoji = TRANSACTION_TYPE_EMOJIS.get(transaction['transaction_type'], "💰")
    amount_text = format_amount(transaction['amount'])
    
    text = f"{amount_text} | {emoji} {transaction['description']}"
    
    if transaction['reference_id']:
        text += f"\n   Ref: {transaction['transaction_type']} #{transaction['reference_id']}"
    
    text += f"\n   {format_balance_change(None, transaction['balance_after'])}"
    text += f"\n   {transaction['created_at'].strftime('%Y-%m-%d %H:%M')}"
    
    return text


def get_transactions_summary(transactions: list) -> dict:
    """Calcula resumen estadístico de transacciones."""
    summary = {
        'total_granted': 0,
        'total_spent': 0,
        'by_type': {}
    }
    
    for tx in transactions:
        amount = tx['amount']
        tx_type = tx['transaction_type']
        
        # Initialize counter for this type if not exists
        if tx_type not in summary['by_type']:
            summary['by_type'][tx_type] = 0
            
        if amount > 0:
            summary['total_granted'] += amount
        else:
            summary['total_spent'] += abs(amount)
            
        summary['by_type'][tx_type] += amount
    
    return summary


def paginate_transactions(transactions: list, page: int, per_page: int = 20):
    """Helper para paginar transacciones."""
    total_pages = max(1, ceil(len(transactions) / per_page))
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': transactions[start:end],
        'page': page,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'total_items': len(transactions)
    }


# ========================================
# MENÚ PRINCIPAL - PEDIR USER ID
# ========================================

@router.callback_query(F.data == "gamif:admin:transactions")
async def request_user_id(callback: CallbackQuery, state: FSMContext):
    """Pide ID de usuario para ver historial."""
    await callback.message.edit_text(
        "💰 <b>HISTORIAL DE BESITOS</b>\n\n"
        "Envía el ID del usuario para ver su historial de transacciones:\n\n"
        "<code>Ejemplo: 123456789</code>",
        parse_mode="HTML"
    )
    await state.set_state(TransactionHistoryStates.waiting_user_id)
    await callback.answer()


@router.message(TransactionHistoryStates.waiting_user_id)
async def show_user_transactions(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Muestra historial de transacciones para un usuario específico."""
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ ID de usuario inválido. Debe ser un número.")
        return
    
    # Validate user exists
    balance = await gamification.besito.get_balance(user_id)
    
    # Store in state
    await state.update_data(user_id=user_id, current_filter=None, current_page=1)
    
    await show_transactions_page(message, user_id, state, 1, None, balance)


async def show_transactions_page(
    message_or_callback,
    user_id: int,
    state: FSMContext,
    page: int,
    transaction_type: Optional[TransactionType],
    current_balance: Optional[int] = None
):
    """Muestra una página específica del historial de transacciones."""
    gamification = message_or_callback.bot['services']['gamification']
    
    if current_balance is None:
        current_balance = await gamification.besito.get_balance(user_id)
    
    # Get transactions
    transactions = await gamification.besito.get_transaction_history_with_offset(
        user_id=user_id,
        limit=PER_PAGE * 10,  # Get more than we need to allow filtering
        offset=(page - 1) * PER_PAGE,
        transaction_type=transaction_type
    )
    
    # Get all transactions for proper pagination (this is more accurate)
    all_tx = await gamification.besito.get_transaction_history(
        user_id=user_id,
        limit=10000,  # Get all that exist
        transaction_type=transaction_type
    )

    total_count = len(all_tx)
    total_pages = max(1, ceil(total_count / PER_PAGE))

    # Calculate correct slice for current page
    start_idx = (page - 1) * PER_PAGE
    end_idx = start_idx + PER_PAGE
    page_transactions = all_tx[start_idx:end_idx]

    text = f"💰 <b>HISTORIAL DE BESITOS</b>\n"
    text += f"Usuario ID: {user_id}\n"
    text += f"Balance actual: {current_balance:,}\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    
    # Filter buttons
    current_filter_name = "Todos" if not transaction_type else TYPE_FILTER_NAMES.get(transaction_type, str(transaction_type).title())
    text += f"Filtro: <b>{current_filter_name}</b> | "
    
    filter_buttons = [
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data=f"gamif:transactions:filter:{user_id}:{TransactionType.MISSION_REWARD}"),
            InlineKeyboardButton(text="🛒 Compras", callback_data=f"gamif:transactions:filter:{user_id}:{TransactionType.PURCHASE}")
        ],
        [
            InlineKeyboardButton(text="⚙️ Admin", callback_data=f"gamif:transactions:filter:{user_id}:{TransactionType.ADMIN_GRANT}"),
            InlineKeyboardButton(text="💬 Reacciones", callback_data=f"gamif:transactions:filter:{user_id}:{TransactionType.REACTION}")
        ]
    ]
    
    text += "\n\n"
    
    if not page_transactions:
        text += "No hay transacciones registradas.\n\n"
        keyboard_buttons = [
            [InlineKeyboardButton(text="🔄 Recargar", callback_data=f"gamif:transactions:user:{user_id}")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ]
    else:
        # Show transactions
        for tx in page_transactions:
            text += format_transaction_display(tx) + "\n\n"
        
        text += f"<i>Página {page}/{total_pages}</i>\n\n"
        
        # Calculate summary for this page
        summary = get_transactions_summary(page_transactions)
        text += f"📊 <b>RESUMEN (PÁGINA)</b>\n"
        text += f"• Otorgado: +{summary['total_granted']:,}\n"
        text += f"• Gastado: -{summary['total_spent']:,}\n"
        text += f"• Neto: {summary['total_granted'] - summary['total_spent']:+,}\n\n"
        
        # Pagination and filter buttons
        keyboard_buttons = []
        keyboard_buttons.extend(filter_buttons)
        
        # Pagination row
        pagination_row = []
        if page > 1:
            pagination_row.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"gamif:transactions:page:{user_id}:{page-1}:{transaction_type or 'all'}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            text=f"Página {page}/{total_pages}",
            callback_data=f"gamif:none"
        ))
        
        if page < total_pages:
            pagination_row.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"gamif:transactions:page:{user_id}:{page+1}:{transaction_type or 'all'}"
            ))
        
        keyboard_buttons.append(pagination_row)
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔄 Recargar", callback_data=f"gamif:transactions:user:{user_id}"),
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if hasattr(message_or_callback, 'message'):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# FILTROS Y PAGINACIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:transactions:filter:"))
async def filter_transactions(callback: CallbackQuery, state: FSMContext):
    """Filtra transacciones por tipo."""
    parts = callback.data.split(":")
    if len(parts) < 5:
        await callback.answer("❌ Datos inválidos", show_alert=True)
        return
        
    user_id = int(parts[3])
    tx_type = parts[4]
    
    try:
        transaction_type = TransactionType(tx_type)
    except ValueError:
        transaction_type = None
    
    await state.update_data(current_filter=transaction_type, current_page=1)
    
    balance = await callback.bot['services']['gamification'].besito.get_balance(user_id)
    await show_transactions_page(callback, user_id, state, 1, transaction_type, balance)


@router.callback_query(F.data.startswith("gamif:transactions:page:"))
async def change_transaction_page(callback: CallbackQuery, state: FSMContext):
    """Cambia entre páginas de transacciones."""
    parts = callback.data.split(":")
    if len(parts) < 6:
        await callback.answer("❌ Datos inválidos", show_alert=True)
        return
        
    user_id = int(parts[3])
    page = int(parts[4])
    tx_type = parts[5]
    
    transaction_type = None if tx_type == 'all' else TransactionType(tx_type)
    
    await state.update_data(current_page=page)
    
    balance = await callback.bot['services']['gamification'].besito.get_balance(user_id)
    await show_transactions_page(callback, user_id, state, page, transaction_type, balance)


@router.callback_query(F.data.startswith("gamif:transactions:user:"))
async def show_user_transactions_callback(callback: CallbackQuery, state: FSMContext):
    """Muestra historial de transacciones de usuario (desde menú principal)."""
    user_id = int(callback.data.split(":")[-1])
    
    await state.update_data(user_id=user_id, current_filter=None, current_page=1)
    
    balance = await callback.bot['services']['gamification'].besito.get_balance(user_id)
    await show_transactions_page(callback, user_id, state, 1, None, balance)