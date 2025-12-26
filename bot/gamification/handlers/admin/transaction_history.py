"""Handler de historial de transacciones de besitos para administradores.

Responsabilidades:
- Ver historial de transacciones de usuario específico
- Filtrar por tipo de transacción
- Paginación de resultados
- Resumen estadístico
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import TransactionType
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

# Router para historial de transacciones
router = Router(name="transaction_history")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


class TransactionHistoryStates(StatesGroup):
    """Estados FSM para consulta de historial."""
    waiting_for_user_id = State()


# ========================================
# MENÚ PRINCIPAL
# ========================================

@router.callback_query(F.data == "gamif:admin:transactions")
async def show_transaction_menu(callback: CallbackQuery, state: FSMContext):
    """Muestra menú de historial de transacciones.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"👤 Usuario {callback.from_user.id} abriendo menú de transacciones")

    await state.set_state(TransactionHistoryStates.waiting_for_user_id)

    text = """💰 <b>Historial de Transacciones</b>

Para consultar el historial de un usuario, envía su <b>User ID</b>.

<i>Puedes obtener el User ID reenviándome un mensaje del usuario o usando /id en respuesta a su mensaje.</i>"""

    keyboard = [
        [{"text": "🔙 Volver al Menú", "callback_data": "gamif:menu"}]
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(TransactionHistoryStates.waiting_for_user_id)
async def process_user_id_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa User ID ingresado y muestra historial.

    Args:
        message: Mensaje del admin
        state: FSM context
        session: Sesión de BD
    """
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ User ID inválido. Debe ser un número.\n\n"
            "Ejemplo: 123456789"
        )
        return

    container = GamificationContainer(session, message.bot)

    # Verificar que usuario existe en gamificación
    balance = await container.besito.get_balance(user_id)

    # Obtener estadísticas
    stats = await container.besito.get_transaction_stats(user_id)

    # Guardar user_id en state para paginación
    await state.update_data(viewing_user_id=user_id, page=0, filter_type=None)
    await state.clear()

    # Mostrar resumen + historial
    await show_user_transaction_history(
        message, session, user_id, page=0, filter_type=None
    )


# ========================================
# HISTORIAL PAGINADO
# ========================================

async def show_user_transaction_history(
    message: Message,
    session: AsyncSession,
    user_id: int,
    page: int = 0,
    filter_type: str = None
):
    """Muestra historial de transacciones paginado.

    Args:
        message: Mensaje para responder
        session: Sesión de BD
        user_id: ID del usuario a consultar
        page: Página actual (0-indexed)
        filter_type: Tipo de transacción a filtrar (opcional)
    """
    container = GamificationContainer(session, message.bot)

    # Paginación
    per_page = 10
    offset = page * per_page

    # Obtener transacciones
    filter_enum = TransactionType(filter_type) if filter_type else None
    transactions = await container.besito.get_transaction_history(
        user_id=user_id,
        transaction_type=filter_enum,
        limit=per_page,
        offset=offset
    )

    # Obtener total para calcular páginas
    total_count = await container.besito.get_total_transactions_count(
        user_id=user_id,
        transaction_type=filter_enum
    )
    total_pages = (total_count + per_page - 1) // per_page

    # Obtener stats
    stats = await container.besito.get_transaction_stats(user_id)
    balance = await container.besito.get_balance(user_id)

    # Construir texto
    filter_text = f" ({filter_type})" if filter_type else ""
    text = f"""💰 <b>Historial de Besitos{filter_text}</b>
Usuario ID: <code>{user_id}</code>

📊 <b>RESUMEN</b>
━━━━━━━━━━━━━━━━
• Balance actual: <b>{balance:,}</b> besitos
• Total ganado: +{stats['total_earned']:,}
• Total gastado: -{stats['total_spent']:,}
• Transacciones: {stats['total_transactions']}

📋 <b>ÚLTIMAS TRANSACCIONES</b>
━━━━━━━━━━━━━━━━

"""

    if not transactions:
        text += "<i>No hay transacciones registradas.</i>\n"
    else:
        for tx in transactions:
            # Emoji según tipo
            emoji = "🟢" if tx.amount > 0 else "🔴"
            sign = "+" if tx.amount > 0 else ""

            # Formatear fecha
            date_str = tx.created_at.strftime("%d/%m/%Y %H:%M")

            # Tipo legible
            type_map = {
                "reaction": "Reacción",
                "mission_reward": "Misión",
                "purchase": "Compra",
                "admin_grant": "Admin +",
                "admin_deduct": "Admin -",
                "refund": "Reembolso",
                "streak_bonus": "Racha",
                "level_up_bonus": "Level Up"
            }
            type_name = type_map.get(tx.transaction_type, tx.transaction_type)

            text += f"""{emoji} <b>{sign}{tx.amount}</b> besitos | {type_name}
   {tx.description}
   Balance: {tx.balance_after:,} | {date_str}

"""

    # Paginación info
    text += f"\n<i>Página {page + 1}/{total_pages if total_pages > 0 else 1} ({total_count} total)</i>"

    # Botones de paginación y filtros
    keyboard = []

    # Filtros por tipo
    filter_buttons = []
    if filter_type:
        filter_buttons.append(
            {"text": "🔄 Mostrar Todos", "callback_data": f"gamif:tx:filter:{user_id}:all:{page}"}
        )
    else:
        filter_buttons.append(
            {"text": "📋 Misiones", "callback_data": f"gamif:tx:filter:{user_id}:mission_reward:{page}"}
        )
        filter_buttons.append(
            {"text": "🛒 Compras", "callback_data": f"gamif:tx:filter:{user_id}:purchase:{page}"}
        )

    if filter_buttons:
        keyboard.append(filter_buttons)

    # Paginación
    pagination_row = []
    if page > 0:
        pagination_row.append(
            {"text": "⬅️ Anterior", "callback_data": f"gamif:tx:page:{user_id}:{page - 1}:{filter_type or 'all'}"}
        )
    if page < total_pages - 1:
        pagination_row.append(
            {"text": "Siguiente ➡️", "callback_data": f"gamif:tx:page:{user_id}:{page + 1}:{filter_type or 'all'}"}
        )

    if pagination_row:
        keyboard.append(pagination_row)

    # Volver
    keyboard.append([{"text": "🔙 Volver", "callback_data": "gamif:admin:transactions"}])

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard(keyboard),
        parse_mode="HTML"
    )


# ========================================
# CALLBACKS DE PAGINACIÓN Y FILTROS
# ========================================

@router.callback_query(F.data.startswith("gamif:tx:page:"))
async def handle_transaction_page(callback: CallbackQuery, session: AsyncSession):
    """Maneja cambio de página en historial.

    Callback data format: gamif:tx:page:{user_id}:{page}:{filter_type}
    """
    parts = callback.data.split(":")
    user_id = int(parts[3])
    page = int(parts[4])
    filter_type = parts[5] if parts[5] != "all" else None

    await show_user_transaction_history(
        callback.message,
        session,
        user_id,
        page,
        filter_type
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:tx:filter:"))
async def handle_transaction_filter(callback: CallbackQuery, session: AsyncSession):
    """Maneja cambio de filtro en historial.

    Callback data format: gamif:tx:filter:{user_id}:{filter_type}:{page}
    """
    parts = callback.data.split(":")
    user_id = int(parts[3])
    filter_type = parts[4] if parts[4] != "all" else None
    page = int(parts[5])

    await show_user_transaction_history(
        callback.message,
        session,
        user_id,
        page,
        filter_type
    )
    await callback.answer(f"Filtro aplicado: {filter_type or 'Todos'}")
