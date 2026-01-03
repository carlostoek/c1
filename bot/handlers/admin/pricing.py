"""
Pricing Handlers - Gestión de tarifas/planes de suscripción.

Handlers para:
- Listar planes configurados
- Crear nuevo plan (FSM)
- Editar plan existente
- Activar/desactivar planes
- Eliminar planes
"""
import logging

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import InvitationToken
from bot.handlers.admin.main import admin_router
from bot.services.container import ServiceContainer
from bot.states.admin import PricingSetupStates
from bot.utils.formatters import format_currency
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)


def _format_plan_summary(plan) -> str:
    """Formatea resumen de un plan."""
    status = "🟢" if plan.active else "⚪"
    price_str = format_currency(plan.price, symbol=plan.currency)

    return (
        f"{status} <b>{plan.name}</b>\n"
        f"   └─ {plan.duration_days} días • {price_str}"
    )


# ===== MENÚ PRINCIPAL DE TARIFAS =====

@admin_router.callback_query(F.data == "admin:pricing")
async def callback_pricing_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra menú principal de gestión de tarifas.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"💰 Usuario {callback.from_user.id} abrió menú de tarifas")

    container = ServiceContainer(session, callback.bot)

    # Obtener planes
    plans = await container.pricing.get_all_plans(active_only=False)

    # Formatear mensaje
    if plans:
        plans_text = "\n\n".join(_format_plan_summary(plan) for plan in plans)
        text = f"💰 <b>Gestión de Tarifas</b>\n\n{plans_text}"
    else:
        text = (
            "💰 <b>Gestión de Tarifas</b>\n\n"
            "<i>No hay tarifas configuradas aún.</i>\n\n"
            "Las tarifas definen los planes de suscripción VIP disponibles."
        )

    # Keyboard
    buttons = [
        [{"text": "➕ Crear Nueva Tarifa", "callback_data": "pricing:create"}]
    ]

    if plans:
        buttons.append([
            {"text": "📋 Ver Todas las Tarifas", "callback_data": "pricing:list"}
        ])

    buttons.append([
        {"text": "🔙 Volver a Configuración", "callback_data": "admin:config"}
    ])

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(buttons),
        parse_mode="HTML"
    )

    await callback.answer()


# ===== CREAR NUEVA TARIFA (FSM) =====

@admin_router.callback_query(F.data == "pricing:create")
async def callback_pricing_create_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Inicia flujo de creación de tarifa.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"➕ Usuario {callback.from_user.id} creando tarifa")

    await state.set_state(PricingSetupStates.waiting_for_name)

    text = (
        "➕ <b>Crear Nueva Tarifa</b>\n\n"
        "Paso 1/3: <b>Nombre de la Tarifa</b>\n\n"
        "Envía el nombre del plan de suscripción.\n\n"
        "<b>Ejemplos:</b>\n"
        "• Plan Mensual\n"
        "• Plan Trimestral\n"
        "• Plan Anual\n"
        "• VIP Premium 6 Meses"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "pricing:cancel"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


@admin_router.message(PricingSetupStates.waiting_for_name)
async def process_pricing_name(
    message: Message,
    state: FSMContext
):
    """
    Procesa el nombre de la tarifa.

    Args:
        message: Mensaje con el nombre
        state: FSM context
    """
    name = message.text.strip()

    # Validar
    if len(name) == 0:
        await message.answer(
            "❌ El nombre no puede estar vacío.\n\n"
            "Envía un nombre válido:",
            parse_mode="HTML"
        )
        return

    if len(name) > 100:
        await message.answer(
            "❌ El nombre es demasiado largo (máximo 100 caracteres).\n\n"
            "Envía un nombre más corto:",
            parse_mode="HTML"
        )
        return

    # Guardar en FSM
    await state.update_data(name=name)

    # Siguiente paso
    await state.set_state(PricingSetupStates.waiting_for_days)

    await message.answer(
        f"✅ Nombre: <b>{name}</b>\n\n"
        f"Paso 2/3: <b>Duración en Días</b>\n\n"
        f"Envía el número de días de duración del plan.\n\n"
        f"<b>Ejemplos:</b>\n"
        f"• 30 (1 mes)\n"
        f"• 90 (3 meses)\n"
        f"• 365 (1 año)",
        parse_mode="HTML"
    )


@admin_router.message(PricingSetupStates.waiting_for_days)
async def process_pricing_days(
    message: Message,
    state: FSMContext
):
    """
    Procesa la duración en días.

    Args:
        message: Mensaje con los días
        state: FSM context
    """
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Debes enviar un número entero.\n\n"
            "Ejemplo: 30",
            parse_mode="HTML"
        )
        return

    # Validar
    if days <= 0:
        await message.answer(
            "❌ La duración debe ser mayor a 0 días.\n\n"
            "Envía un número válido:",
            parse_mode="HTML"
        )
        return

    if days > 3650:  # Máximo 10 años
        await message.answer(
            "❌ La duración máxima es 3650 días (10 años).\n\n"
            "Envía un número menor:",
            parse_mode="HTML"
        )
        return

    # Guardar en FSM
    await state.update_data(duration_days=days)

    # Siguiente paso
    await state.set_state(PricingSetupStates.waiting_for_price)

    await message.answer(
        f"✅ Duración: <b>{days} días</b>\n\n"
        f"Paso 3/3: <b>Precio</b>\n\n"
        f"Envía el precio del plan.\n\n"
        f"<b>Ejemplos:</b>\n"
        f"• 9.99\n"
        f"• 24.50\n"
        f"• 79",
        parse_mode="HTML"
    )


@admin_router.message(PricingSetupStates.waiting_for_price)
async def process_pricing_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el precio y crea la tarifa.

    Args:
        message: Mensaje con el precio
        state: FSM context
        session: Sesión de BD
    """
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Debes enviar un número válido.\n\n"
            "Ejemplo: 9.99",
            parse_mode="HTML"
        )
        return

    # Validar
    if price < 0:
        await message.answer(
            "❌ El precio no puede ser negativo.\n\n"
            "Envía un número válido:",
            parse_mode="HTML"
        )
        return

    if price > 9999:
        await message.answer(
            "❌ El precio máximo es 9999.\n\n"
            "Envía un número menor:",
            parse_mode="HTML"
        )
        return

    # Obtener datos del FSM
    data = await state.get_data()
    name = data["name"]
    duration_days = data["duration_days"]

    # Crear plan
    container = ServiceContainer(session, message.bot)

    try:
        plan = await container.pricing.create_plan(
            name=name,
            duration_days=duration_days,
            price=price,
            created_by=message.from_user.id
        )

        # Confirmar
        price_str = format_currency(price)

        await message.answer(
            f"{LucienMessages.confirm('ACTION_COMPLETED')}\n\n"
            f"<b>Nombre:</b> {plan.name}\n"
            f"<b>Duración:</b> {plan.duration_days} días\n"
            f"<b>Precio:</b> {price_str}\n\n"
            f"Puede generar tokens usando esta tarifa.",
            reply_markup=create_inline_keyboard([
                [{"text": "💰 Ver Tarifas", "callback_data": "admin:pricing"}],
                [{"text": "🔙 Volver", "callback_data": "admin:config"}]
            ]),
            parse_mode="HTML"
        )

        # Limpiar FSM
        await state.clear()

        logger.info(
            f"✅ Tarifa creada: {plan.name} ({plan.duration_days} días, "
            f"{price_str}) por {message.from_user.id}"
        )

    except Exception as e:
        logger.error(f"❌ Error creando tarifa: {e}", exc_info=True)

        await message.answer(
            "❌ <b>Error al Crear Tarifa</b>\n\n"
            "Ocurrió un error inesperado. Intenta nuevamente.",
            parse_mode="HTML"
        )

        await state.clear()


@admin_router.callback_query(F.data == "pricing:cancel")
async def callback_pricing_cancel(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Cancela creación de tarifa.

    Args:
        callback: Callback query
        state: FSM context
    """
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Creación de Tarifa Cancelada</b>",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver", "callback_data": "admin:pricing"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()


# ===== LISTAR TARIFAS =====

@admin_router.callback_query(F.data == "pricing:list")
async def callback_pricing_list(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Lista todas las tarifas con detalles.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    container = ServiceContainer(session, callback.bot)

    plans = await container.pricing.get_all_plans(active_only=False)

    if not plans:
        await callback.answer("No hay tarifas configuradas", show_alert=True)
        return

    # Obtener conteo de tokens eficientemente (evitar N+1)
    token_counts = {}
    for plan in plans:
        result = await session.execute(
            select(func.count(InvitationToken.id))
            .where(InvitationToken.plan_id == plan.id)
        )
        token_counts[plan.id] = result.scalar() or 0

    # Formatear lista
    text = "📋 <b>Todas las Tarifas</b>\n\n"

    for plan in plans:
        status = "🟢 Activa" if plan.active else "⚪ Inactiva"
        price_str = format_currency(plan.price, symbol=plan.currency)

        text += (
            f"<b>{plan.name}</b> (ID: {plan.id})\n"
            f"├─ Estado: {status}\n"
            f"├─ Duración: {plan.duration_days} días\n"
            f"├─ Precio: {price_str}\n"
            f"└─ Tokens: {token_counts[plan.id]}\n\n"
        )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver", "callback_data": "admin:pricing"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()
