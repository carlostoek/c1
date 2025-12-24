# PROMPT G4.2: Handler Menú Admin Gamification

---

## ROL

Actúa como Ingeniero de Software Senior especializado en interfaces conversacionales con Aiogram 3 y menús inline.

---

## TAREA

Implementa el handler del menú principal de administración de gamificación en `bot/gamification/handlers/admin/main.py` con navegación por callbacks.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/handlers/admin/
├── main.py              # ← ESTE ARCHIVO (menú principal)
├── mission_wizard.py    # G4.3
├── reward_wizard.py     # G4.4
└── stats.py
```

### Sistema de Callbacks
```python
# Patrón: "gamif:section:action[:params]"
"gamif:menu"                 # Menú principal
"gamif:admin:missions"       # Submenu misiones
"gamif:admin:rewards"        # Submenu recompensas
"gamif:admin:levels"         # Submenu niveles
"gamif:admin:stats"          # Estadísticas
"gamif:wizard:mission"       # Iniciar wizard misión
"gamif:wizard:reward"        # Iniciar wizard recompensa
```

---

## RESPONSABILIDADES

### 1. Comando de Entrada

```python
@router.message(Command("gamification"))
@router.message(Command("gamif"))
async def gamification_menu(message: Message):
    """Muestra menú principal de gamificación."""
```

### 2. Menú Principal

```python
async def show_main_menu(callback: CallbackQuery):
    """
    Menú principal con opciones:
    
    [📋 Misiones] [🎁 Recompensas]
    [⭐ Niveles]  [📊 Estadísticas]
    [🔧 Configuración]
    [🔙 Volver]
    """
```

### 3. Submenús

```python
async def missions_menu(callback: CallbackQuery):
    """
    Submenu de misiones:
    
    [➕ Crear Misión] [📝 Listar]
    [🎯 Wizard]      [📄 Plantillas]
    [🔙 Volver]
    """

async def rewards_menu(callback: CallbackQuery):
    """
    Submenu de recompensas:
    
    [➕ Crear Recompensa] [📝 Listar]
    [🎯 Wizard]          [🏆 Badges]
    [🔙 Volver]
    """

async def levels_menu(callback: CallbackQuery):
    """
    Submenu de niveles:
    
    [➕ Crear Nivel] [📝 Listar]
    [🔄 Reordenar]   [📊 Distribución]
    [🔙 Volver]
    """
```

### 4. Listados Paginados

```python
async def list_missions(callback: CallbackQuery, page: int = 0):
    """Lista misiones con paginación."""

async def list_rewards(callback: CallbackQuery, page: int = 0):
    """Lista recompensas con paginación."""

async def list_levels(callback: CallbackQuery):
    """Lista niveles ordenados."""
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/handlers/admin/main.py

"""
Handlers del menú principal de administración de gamificación.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.gamification.services.container import GamificationContainer

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ========================================
# COMANDOS DE ENTRADA
# ========================================

@router.message(Command("gamification"))
@router.message(Command("gamif"))
async def gamification_menu(message: Message):
    """Muestra menú principal de gamificación."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data="gamif:admin:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="gamif:admin:rewards")
        ],
        [
            InlineKeyboardButton(text="⭐ Niveles", callback_data="gamif:admin:levels"),
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="gamif:admin:stats")
        ],
        [
            InlineKeyboardButton(text="🔧 Configuración", callback_data="gamif:admin:config")
        ]
    ])
    
    await message.answer(
        "🎮 <b>Panel de Gamificación</b>\n\n"
        "Gestiona misiones, recompensas y niveles del sistema.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ========================================
# MENÚ PRINCIPAL
# ========================================

@router.callback_query(F.data == "gamif:menu")
async def show_main_menu(callback: CallbackQuery):
    """Volver al menú principal."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Misiones", callback_data="gamif:admin:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="gamif:admin:rewards")
        ],
        [
            InlineKeyboardButton(text="⭐ Niveles", callback_data="gamif:admin:levels"),
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="gamif:admin:stats")
        ],
        [
            InlineKeyboardButton(text="🔧 Configuración", callback_data="gamif:admin:config")
        ]
    ])
    
    await callback.message.edit_text(
        "🎮 <b>Panel de Gamificación</b>\n\n"
        "Gestiona misiones, recompensas y niveles del sistema.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ MISIONES
# ========================================

@router.callback_query(F.data == "gamif:admin:missions")
async def missions_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Submenú de gestión de misiones."""
    # Contar misiones activas
    missions = await gamification.mission.get_all_missions()
    count = len(missions)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Wizard Crear", callback_data="gamif:wizard:mission"),
            InlineKeyboardButton(text="📝 Listar", callback_data="gamif:missions:list")
        ],
        [
            InlineKeyboardButton(text="📄 Plantillas", callback_data="gamif:missions:templates"),
            InlineKeyboardButton(text="⚙️ Config Avanzada", callback_data="gamif:missions:advanced")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ]
    ])
    
    await callback.message.edit_text(
        f"📋 <b>Gestión de Misiones</b>\n\n"
        f"Misiones activas: {count}\n\n"
        f"• <b>Wizard:</b> Creación guiada paso a paso\n"
        f"• <b>Listar:</b> Ver y editar misiones existentes\n"
        f"• <b>Plantillas:</b> Aplicar configuraciones predefinidas",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ RECOMPENSAS
# ========================================

@router.callback_query(F.data == "gamif:admin:rewards")
async def rewards_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Submenú de gestión de recompensas."""
    rewards = await gamification.reward.get_all_rewards()
    badges = await gamification.reward.get_all_rewards(reward_type=RewardType.BADGE)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Wizard Crear", callback_data="gamif:wizard:reward"),
            InlineKeyboardButton(text="📝 Listar", callback_data="gamif:rewards:list")
        ],
        [
            InlineKeyboardButton(text="🏆 Badges", callback_data="gamif:rewards:badges"),
            InlineKeyboardButton(text="🎁 Set de Badges", callback_data="gamif:rewards:badge_set")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ]
    ])
    
    await callback.message.edit_text(
        f"🎁 <b>Gestión de Recompensas</b>\n\n"
        f"Recompensas totales: {len(rewards)}\n"
        f"Badges: {len(badges)}\n\n"
        f"Crea recompensas con unlock conditions automáticas.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# SUBMENÚ NIVELES
# ========================================

@router.callback_query(F.data == "gamif:admin:levels")
async def levels_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Submenú de gestión de niveles."""
    levels = await gamification.level.get_all_levels()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Crear Nivel", callback_data="gamif:levels:create"),
            InlineKeyboardButton(text="📝 Listar", callback_data="gamif:levels:list")
        ],
        [
            InlineKeyboardButton(text="📊 Distribución", callback_data="gamif:levels:distribution")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ]
    ])
    
    await callback.message.edit_text(
        f"⭐ <b>Gestión de Niveles</b>\n\n"
        f"Niveles configurados: {len(levels)}\n\n"
        f"Los niveles determinan la progresión de usuarios según besitos.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# LISTADOS
# ========================================

@router.callback_query(F.data == "gamif:missions:list")
async def list_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista todas las misiones."""
    missions = await gamification.mission.get_all_missions()
    
    if not missions:
        await callback.answer("No hay misiones creadas", show_alert=True)
        return
    
    text = "📋 <b>Misiones Activas</b>\n\n"
    keyboard_buttons = []
    
    for mission in missions[:10]:  # Mostrar primeras 10
        type_icon = {
            MissionType.ONE_TIME: "🎯",
            MissionType.DAILY: "📅",
            MissionType.WEEKLY: "📆",
            MissionType.STREAK: "🔥"
        }.get(mission.mission_type, "📋")
        
        text += f"{type_icon} <b>{mission.name}</b>\n"
        text += f"   Recompensa: {mission.besitos_reward} besitos\n\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{type_icon} {mission.name}",
                callback_data=f"gamif:mission:view:{mission.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:missions")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
```

---

## INTEGRACIÓN

Registrar router en main:

```python
# bot/main.py
from bot.gamification.handlers.admin import main as gamif_admin_main

dp.include_router(gamif_admin_main.router)
```

---

## VALIDACIÓN

- ✅ Comando /gamification para entrada
- ✅ Menú principal con 4 secciones
- ✅ Submenús con botones de acción
- ✅ Listados con información resumida
- ✅ Callbacks consistentes ("gamif:section:action")
- ✅ Filtro IsAdmin aplicado

---

**ENTREGABLE:** Archivo `main.py` con menús de navegación completos.
