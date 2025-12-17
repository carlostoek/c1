"""
Rewards Handlers - Tienda y canje de recompensas.

Comandos:
- /tienda: Muestra catálogo de recompensas disponibles
- Callback redeem:ID: Procesa canje de recompensa
- /mis_canjes: Muestra histórico de canjes del usuario

Flujo:
1. Usuario executa /tienda
2. Se muestran recompensas disponibles (con validación de saldo)
3. Usuario toca botón de recompensa
4. Se valida canje y se ejecuta
5. Se muestra confirmación con detalles
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import get_session
from bot.services.container import ServiceContainer

logger = logging.getLogger(__name__)
router = Router()


# ===== COMANDO /TIENDA =====

@router.message(Command("tienda"))
async def show_rewards_catalog(message: Message):
    """
    Muestra el catálogo de recompensas disponibles.

    Filtra por:
    - Nivel del usuario
    - VIP status
    - Saldo disponible

    Estructura del mensaje:
    - Saldo actual
    - Lista de recompensas
    - Botones deshabilitados si no hay saldo suficiente
    """
    try:
        async with get_session() as session:
            container = ServiceContainer(session, message.bot)

            # Obtener recompensas disponibles
            rewards = await container.rewards.get_available_rewards(
                message.from_user.id
            )

            if not rewards:
                await message.answer(
                    "🏪 <b>Tienda de Recompensas</b>\n\n"
                    "No hay recompensas disponibles en este momento.",
                    parse_mode="HTML"
                )
                return

            # Obtener saldo del usuario
            try:
                balance = await container.points.get_user_balance(
                    message.from_user.id
                )
            except Exception:
                balance = 0

            # Construcción del mensaje
            text = "🏪 <b>Tienda de Recompensas</b>\n\n"
            text += f"💰 Tu saldo: <b>{balance} 💋</b>\n"
            text += f"📦 Recompensas disponibles: {len(rewards)}\n\n"
            text += "─────────────────────────────\n\n"

            # Botones
            keyboard = []

            for reward in rewards:
                # Construir texto del botón
                reward_text = f"{reward.display_name}\n"
                reward_text += f"💸 {reward.cost} 💋"

                # Mostrar stock si aplica
                if reward.stock is not None:
                    reward_text += f" • Stock: {reward.stock}"

                # Mostrar límite
                if reward.limit_type.value != "unlimited":
                    reward_text += f"\n({reward.limit_type.value})"

                # Verificar si puede pagarlo
                can_afford = balance >= reward.cost

                # Callback data
                callback_data = (
                    f"reward:redeem:{reward.id}"
                    if can_afford
                    else "reward:insufficient"
                )

                # Botón (deshabilitado visualmente si no puede pagarlo)
                button_text = (
                    reward_text
                    if can_afford
                    else f"🔒 {reward_text}\n❌ Saldo insuficiente"
                )

                keyboard.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=callback_data
                    )
                ])

            # Agregar botón de histórico
            keyboard.append([
                InlineKeyboardButton(
                    text="📦 Ver mis canjes",
                    callback_data="reward:history"
                )
            ])

            await message.answer(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error showing rewards catalog: {e}", exc_info=True)
        await message.answer(
            "❌ Error al cargar la tienda. Intenta más tarde.",
            parse_mode="HTML"
        )


# ===== CALLBACK CANJE DE RECOMPENSA =====

@router.callback_query(F.data.startswith("reward:redeem:"))
async def process_reward_redemption(callback: CallbackQuery):
    """
    Procesa el canje de una recompensa.

    Validación final:
    - Recompensa existe
    - Usuario tiene saldo
    - No ha alcanzado límite de canje
    - Stock disponible

    Resultado:
    - Éxito: Muestra detalles de la recompensa canjeada
    - Error: Muestra mensaje de error con motivo
    """
    try:
        # Extraer ID de recompensa
        reward_id = int(callback.data.split(":")[2])

        async with get_session() as session:
            container = ServiceContainer(session, callback.bot)

            # Ejecutar canje
            success, message_text, user_reward = await container.rewards.redeem_reward(
                user_id=callback.from_user.id,
                reward_id=reward_id
            )

            if success:
                # Construcción del mensaje de éxito
                reward = user_reward.reward
                response = "✅ <b>¡Canje Exitoso!</b>\n\n"
                response += f"{reward.display_name}\n"
                response += f"💸 Gastaste: {reward.cost} 💋\n\n"
                response += "─────────────────────────────\n\n"

                # Info según tipo de recompensa
                if reward.badge:
                    response += f"🏆 <b>Badge:</b> {reward.badge.display_name}\n"
                    response += f"📝 {reward.badge.description}\n\n"

                if reward.points_amount > 0:
                    response += f"💰 <b>Puntos Extra:</b> +{reward.points_amount} 💋\n\n"

                # Saldo actual
                try:
                    balance = await container.points.get_user_balance(
                        callback.from_user.id
                    )
                    response += f"💰 Saldo actual: {balance} 💋"
                except Exception:
                    response += "💰 Saldo actualizado"

                # Editar mensaje
                await callback.message.edit_text(
                    response,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[[
                            InlineKeyboardButton(
                                text="🔙 Volver a tienda",
                                callback_data="reward:back_to_store"
                            )
                        ]]
                    )
                )

                # Notificación
                await callback.answer(
                    f"✅ ¡Canjeado: {reward.display_name}!",
                    show_alert=False
                )

            else:
                # Error en el canje
                await callback.answer(
                    f"❌ {message_text}",
                    show_alert=True
                )

    except Exception as e:
        logger.error(f"Error processing reward redemption: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al procesar el canje",
            show_alert=True
        )


# ===== CALLBACK SALDO INSUFICIENTE =====

@router.callback_query(F.data == "reward:insufficient")
async def insufficient_balance_alert(callback: CallbackQuery):
    """Alerta cuando el usuario intenta canjear sin saldo suficiente."""
    await callback.answer(
        "❌ No tienes saldo suficiente para esta recompensa",
        show_alert=True
    )


# ===== CALLBACK VOLVER A TIENDA =====

@router.callback_query(F.data == "reward:back_to_store")
async def go_back_to_store(callback: CallbackQuery):
    """Vuelve a mostrar la tienda de recompensas."""
    try:
        async with get_session() as session:
            container = ServiceContainer(session, callback.bot)

            # Obtener recompensas
            rewards = await container.rewards.get_available_rewards(
                callback.from_user.id
            )

            if not rewards:
                await callback.message.edit_text(
                    "🏪 <b>Tienda de Recompensas</b>\n\n"
                    "No hay recompensas disponibles.",
                    parse_mode="HTML"
                )
                return

            # Obtener saldo
            try:
                balance = await container.points.get_user_balance(
                    callback.from_user.id
                )
            except Exception:
                balance = 0

            # Texto
            text = "🏪 <b>Tienda de Recompensas</b>\n\n"
            text += f"💰 Tu saldo: <b>{balance} 💋</b>\n"
            text += f"📦 Recompensas disponibles: {len(rewards)}\n\n"
            text += "─────────────────────────────\n\n"

            # Botones
            keyboard = []

            for reward in rewards:
                reward_text = f"{reward.display_name}\n"
                reward_text += f"💸 {reward.cost} 💋"

                if reward.stock is not None:
                    reward_text += f" • Stock: {reward.stock}"

                if reward.limit_type.value != "unlimited":
                    reward_text += f"\n({reward.limit_type.value})"

                can_afford = balance >= reward.cost
                callback_data = (
                    f"reward:redeem:{reward.id}"
                    if can_afford
                    else "reward:insufficient"
                )

                button_text = (
                    reward_text
                    if can_afford
                    else f"🔒 {reward_text}\n❌ Saldo insuficiente"
                )

                keyboard.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=callback_data
                    )
                ])

            keyboard.append([
                InlineKeyboardButton(
                    text="📦 Ver mis canjes",
                    callback_data="reward:history"
                )
            ])

            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error going back to store: {e}", exc_info=True)


# ===== COMANDO /MIS_CANJES =====

@router.message(Command("mis_canjes"))
async def show_user_rewards_history(message: Message):
    """
    Muestra el histórico de canjes del usuario.

    Información mostrada:
    - Recompensa canjeada
    - Costo en besitos
    - Fecha del canje
    - Estado (entregada o pendiente)
    """
    try:
        async with get_session() as session:
            container = ServiceContainer(session, message.bot)

            # Obtener histórico
            user_rewards = await container.rewards.get_user_rewards(
                message.from_user.id,
                limit=15
            )

            if not user_rewards:
                await message.answer(
                    "📦 <b>Mis Canjes</b>\n\n"
                    "No has canjeado ninguna recompensa aún.\n\n"
                    "Usa /tienda para ver recompensas disponibles.",
                    parse_mode="HTML"
                )
                return

            # Construcción del texto
            text = "📦 <b>Mis Canjes Recientes</b>\n\n"

            total_spent = 0

            for ur in user_rewards:
                # Formatear fecha
                date_str = ur.redeemed_at.strftime("%d/%m/%Y %H:%M")
                total_spent += ur.cost_paid

                # Status
                status = "✅ Entregado" if ur.is_delivered else "⏳ Pendiente"

                text += f"{ur.reward.display_name}\n"
                text += f"  💸 {ur.cost_paid} 💋 • {date_str}\n"
                text += f"  {status}\n\n"

            # Resumen
            text += "─────────────────────────────\n\n"
            text += f"📊 Total gastado: {total_spent} 💋\n"
            text += f"📦 Canjes realizados: {len(user_rewards)}"

            await message.answer(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error showing user rewards history: {e}", exc_info=True)
        await message.answer(
            "❌ Error al cargar tu histórico. Intenta más tarde.",
            parse_mode="HTML"
        )


# ===== CALLBACK HISTÓRICO DESDE TIENDA =====

@router.callback_query(F.data == "reward:history")
async def show_history_from_store(callback: CallbackQuery):
    """Muestra el histórico de canjes desde la tienda."""
    try:
        async with get_session() as session:
            container = ServiceContainer(session, callback.bot)

            # Obtener histórico
            user_rewards = await container.rewards.get_user_rewards(
                callback.from_user.id,
                limit=10
            )

            if not user_rewards:
                text = (
                    "📦 <b>Mis Canjes</b>\n\n"
                    "No has canjeado ninguna recompensa aún."
                )
            else:
                text = "📦 <b>Mis Canjes Recientes</b>\n\n"
                total_spent = 0

                for ur in user_rewards:
                    date_str = ur.redeemed_at.strftime("%d/%m/%Y %H:%M")
                    total_spent += ur.cost_paid
                    status = "✅" if ur.is_delivered else "⏳"

                    text += f"{ur.reward.display_name}\n"
                    text += f"  {status} {ur.cost_paid} 💋 • {date_str}\n\n"

                text += f"─────────────────────────────\n\n"
                text += f"💸 Total: {total_spent} 💋"

            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text="🔙 Volver a tienda",
                            callback_data="reward:back_to_store"
                        )
                    ]]
                )
            )

    except Exception as e:
        logger.error(f"Error showing history from store: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar el histórico",
            show_alert=True
        )
