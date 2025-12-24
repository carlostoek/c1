"""
Wizard de creación de niveles paso a paso.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.states.admin import LevelWizardStates
from bot.gamification.services.container import GamificationContainer
import json

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# INICIAR WIZARD
# ========================================

@router.callback_query(F.data == "gamif:wizard:level_prog")
async def start_level_wizard(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creación de nivel."""
    await state.clear()
    await state.set_state(LevelWizardStates.enter_level_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel_level")
        ]
    ])

    await callback.message.edit_text(
        "⭐ <b>Wizard: Crear Nivel</b>\n\n"
        "Paso 1/4: Escribe el nombre del nivel\n\n"
        "Ejemplo: Novato, Entusiasta, Leyenda",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(LevelWizardStates.enter_level_name)
async def enter_level_name(message: Message, state: FSMContext):
    """Recibe nombre de nivel."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    await state.update_data(level_name=message.text.strip())

    await message.answer(
        f"✅ Nombre: <b>{message.text}</b>\n\n"
        f"Paso 2/4: ¿Cuántos besitos mínimos se requieren para este nivel?\n\n"
        f"Ejemplo: 1000",
        parse_mode="HTML"
    )
    await state.set_state(LevelWizardStates.enter_min_besitos)


@router.message(LevelWizardStates.enter_min_besitos)
async def enter_min_besitos(message: Message, state: FSMContext):
    """Recibe besitos mínimos para nivel."""
    try:
        besitos = int(message.text)
        if besitos < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número no negativo")
        return

    await state.update_data(min_besitos=besitos)

    await message.answer(
        f"✅ Besitos mínimos: <b>{besitos}</b>\n\n"
        f"Paso 3/4: ¿Qué orden tendrá este nivel?\n\n"
        f"Ejemplo: 4 (cuarto nivel)",
        parse_mode="HTML"
    )
    await state.set_state(LevelWizardStates.enter_level_order)


@router.message(LevelWizardStates.enter_level_order)
async def enter_level_order(message: Message, state: FSMContext):
    """Recibe orden del nivel."""
    try:
        order = int(message.text)
        if order <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número entero positivo (orden > 0)")
        return

    await state.update_data(order=order)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Saltar", callback_data="wizard:skip_benefits")]
    ])

    await message.answer(
        f"✅ Orden: <b>{order}</b>\n\n"
        f"Paso 4/4: Introduce los beneficios de este nivel (formato JSON, opcional).\n\n"
        f"Ejemplo: `{{\"reaction_multiplier\": 1.2, \"special_perks\": [\"emoji_extra\"]}}`",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(LevelWizardStates.enter_level_benefits)


@router.message(LevelWizardStates.enter_level_benefits)
async def enter_level_benefits(message: Message, state: FSMContext):
    """Recibe beneficios del nivel (JSON opcional)."""
    benefits = None
    if message.text and message.text.strip():
        try:
            benefits = json.loads(message.text.strip())
            await state.update_data(benefits=benefits)
        except json.JSONDecodeError:
            await message.answer("❌ Formato JSON inválido. Por favor, inténtalo de nuevo o salta este paso.")
            return
    else:
        await state.update_data(benefits=None)

    await confirm_level_creation(message, state) # Go to confirmation step


@router.callback_query(F.data == "wizard:skip_benefits")
async def skip_benefits(callback: CallbackQuery, state: FSMContext):
    """Salto el paso de beneficios."""
    await state.update_data(benefits=None)
    await confirm_level_creation(callback.message, state)
    await callback.answer()


# ========================================
# PASO 4: CONFIRMACIÓN
# ========================================

@router.message(LevelWizardStates.enter_level_benefits) # This handler is called after benefits are entered or skipped
@router.callback_query(F.data == "wizard:confirm_level_summary") # For re-displaying summary
async def confirm_level_creation(event: Message | CallbackQuery, state: FSMContext):
    """Muestra resumen y pide confirmación."""
    data = await state.get_data()

    # Construir resumen
    summary = f"""⭐ <b>RESUMEN DE NIVEL</b>
    
<b>Nombre:</b> {data.get('level_name', 'N/A')}
<b>Besitos Mínimos:</b> {data.get('min_besitos', 'N/A')}
<b>Orden:</b> {data.get('order', 'N/A')}
<b>Beneficios:</b> `{json.dumps(data.get('benefits'))}` if data.get('benefits') else 'Ninguno'
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="wizard:create_level"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel_level")
        ]
    ])

    if isinstance(event, Message):
        await event.answer(summary, reply_markup=keyboard, parse_mode="HTML")
    else:
        await event.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(LevelWizardStates.confirm)
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(LevelWizardStates.confirm, F.data == "wizard:create_level")
async def create_level(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Crea el nivel usando LevelService."""
    data = await state.get_data()

    await callback.message.edit_text("⚙️ Creando nivel...", parse_mode="HTML")

    try:
        new_level = await gamification.level.create_level(
            name=data['level_name'],
            min_besitos=data['min_besitos'],
            order=data['order'],
            benefits=data.get('benefits')
        )
        await callback.message.edit_text(
            f"✅ <b>Nivel '{new_level.name}' creado exitosamente!</b>\n\n"
            f"ID: {new_level.id}\n"
            f"Besitos mínimos: {new_level.min_besitos}\n"
            f"Orden: {new_level.order}",
            parse_mode="HTML"
        )
        await state.clear()
    except ValueError as e:
        await callback.message.edit_text(
            f"❌ <b>Error al crear nivel:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Error inesperado al crear nivel:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )
    finally:
        await callback.answer()


@router.message(LevelWizardStates.enter_level_benefits)
async def enter_level_benefits(message: Message, state: FSMContext):
    """Recibe beneficios del nivel (JSON opcional)."""
    benefits = None
    if message.text and message.text.strip():
        try:
            benefits = json.loads(message.text.strip())
            await state.update_data(benefits=benefits)
            message_text = f"✅ Beneficios guardados: `{message.text.strip()}`"
        except json.JSONDecodeError:
            await message.answer("❌ Formato JSON inválido. Por favor, inténtalo de nuevo o salta este paso.")
            return
    else:
        await state.update_data(benefits=None)
        message_text = "✅ Beneficios: Saltado"

    await confirm_level_creation(message, state) # Go to confirmation step


@router.callback_query(F.data == "wizard:skip_benefits")
async def skip_benefits(callback: CallbackQuery, state: FSMContext):
    """Salto el paso de beneficios."""
    await state.update_data(benefits=None)
    await confirm_level_creation(callback.message, state)
    await callback.answer()


# ========================================
# CANCELAR
# ========================================

@router.callback_query(F.data == "wizard:cancel_level")
async def cancel_level_wizard(callback: CallbackQuery, state: FSMContext):
    """Cancela wizard de nivel."""
    await state.clear()
    await callback.message.edit_text("❌ Creación de nivel cancelada.", parse_mode="HTML")
    await callback.answer()
