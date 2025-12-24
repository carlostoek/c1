# PROMPT G4.5: Handlers de Usuarios

---

## ROL

Actúa como Ingeniero de Software Senior especializado en interfaces de usuario conversacionales con Aiogram 3.

---

## TAREA

Implementa handlers para usuarios finales en `bot/gamification/handlers/user/` que permiten ver perfil, misiones, recompensas y leaderboard.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/handlers/user/
├── profile.py         # Ver perfil completo
├── missions.py        # Ver/reclamar misiones
├── rewards.py         # Ver recompensas
└── leaderboard.py     # Rankings
```

---

## HANDLERS REQUERIDOS

### 1. Profile Handler

```python
# bot/gamification/handlers/user/profile.py

@router.message(Command("profile"))
@router.message(Command("perfil"))
async def show_profile(message: Message, gamification: GamificationContainer):
    """
    Muestra perfil completo del usuario.
    
    Usa: gamification.user_gamification.get_profile_summary()
    
    Botones:
    [📋 Misiones] [🎁 Recompensas]
    [🏆 Leaderboard]
    """
```

### 2. Missions Handler

```python
# bot/gamification/handlers/user/missions.py

@router.callback_query(F.data == "user:missions")
async def show_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Lista misiones disponibles/en progreso.
    
    Botones por misión:
    - IN_PROGRESS: [📊 Ver Progreso]
    - COMPLETED: [🎁 Reclamar]
    - NOT_STARTED: [▶️ Iniciar]
    """

@router.callback_query(F.data.startswith("user:mission:claim:"))
async def claim_mission_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Reclama recompensa de misión completada.
    
    Usa: gamification.mission.claim_reward()
    """
```

### 3. Rewards Handler

```python
# bot/gamification/handlers/user/rewards.py

@router.callback_query(F.data == "user:rewards")
async def show_rewards(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra recompensas obtenidas y disponibles.
    
    Tabs:
    [🏆 Obtenidas] [🔒 Bloqueadas]
    """

@router.callback_query(F.data.startswith("user:reward:buy:"))
async def buy_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Compra recompensa con besitos.
    
    Usa: gamification.reward.purchase_reward()
    """
```

### 4. Leaderboard Handler

```python
# bot/gamification/handlers/user/leaderboard.py

@router.callback_query(F.data == "user:leaderboard")
async def show_leaderboard(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra top 10 por besitos.
    
    Tabs:
    [💰 Besitos] [⭐ Nivel] [🔥 Racha]
    
    Incluye posición del usuario actual.
    """
```

---

## FORMATO DE SALIDA

Entregar 4 archivos:

### 1. profile.py

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()

@router.message(Command("profile"))
@router.message(Command("perfil"))
async def show_profile(message: Message, gamification: GamificationContainer):
    summary = await gamification.user_gamification.get_profile_summary(
        message.from_user.id
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Mis Misiones", callback_data="user:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="user:rewards")
        ],
        [
            InlineKeyboardButton(text="🏆 Leaderboard", callback_data="user:leaderboard")
        ]
    ])
    
    await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
```

### 2. missions.py

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionStatus

router = Router()

@router.callback_query(F.data == "user:missions")
async def show_missions(callback: CallbackQuery, gamification: GamificationContainer):
    user_id = callback.from_user.id
    
    # Obtener misiones
    in_progress = await gamification.mission.get_user_missions(
        user_id, status=MissionStatus.IN_PROGRESS
    )
    completed = await gamification.mission.get_user_missions(
        user_id, status=MissionStatus.COMPLETED
    )
    available = await gamification.mission.get_available_missions(user_id)
    
    text = "📋 <b>Mis Misiones</b>\n\n"
    keyboard_buttons = []
    
    # En progreso
    if in_progress:
        text += "<b>En Progreso:</b>\n"
        for um in in_progress:
            mission = um.mission
            text += f"• {mission.name}\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"📊 {mission.name}",
                    callback_data=f"user:mission:view:{mission.id}"
                )
            ])
    
    # Completadas
    if completed:
        text += "\n<b>Completadas:</b>\n"
        for um in completed:
            mission = um.mission
            text += f"• {mission.name} - {mission.besitos_reward} besitos\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🎁 Reclamar: {mission.name}",
                    callback_data=f"user:mission:claim:{mission.id}"
                )
            ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("user:mission:claim:"))
async def claim_mission_reward(callback: CallbackQuery, gamification: GamificationContainer):
    mission_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success, message, rewards_info = await gamification.mission.claim_reward(
        user_id, mission_id
    )
    
    if success:
        await callback.answer(f"🎉 {message}", show_alert=True)
    else:
        await callback.answer(f"❌ {message}", show_alert=True)
```

### 3. rewards.py

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()

@router.callback_query(F.data == "user:rewards")
async def show_rewards(callback: CallbackQuery, gamification: GamificationContainer):
    user_id = callback.from_user.id
    
    obtained = await gamification.reward.get_user_rewards(user_id)
    available = await gamification.reward.get_available_rewards(user_id)
    
    text = "🎁 <b>Recompensas</b>\n\n"
    text += f"Obtenidas: {len(obtained)}\n"
    text += f"Disponibles: {len(available)}\n\n"
    
    keyboard_buttons = []
    
    # Disponibles para comprar/desbloquear
    for reward in available[:5]:
        if reward.cost_besitos:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"💰 {reward.name} ({reward.cost_besitos} besitos)",
                    callback_data=f"user:reward:buy:{reward.id}"
                )
            ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
```

### 4. leaderboard.py

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()

@router.callback_query(F.data == "user:leaderboard")
async def show_leaderboard(callback: CallbackQuery, gamification: GamificationContainer):
    # Obtener top 10
    top_users = await gamification.level.get_leaderboard(limit=10)
    
    # Posición del usuario
    position = await gamification.user_gamification.get_leaderboard_position(
        callback.from_user.id
    )
    
    text = "🏆 <b>Leaderboard</b>\n\n"
    
    for idx, user in enumerate(top_users, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx}.")
        text += f"{medal} {user.total_besitos:,} besitos\n"
    
    text += f"\n<b>Tu posición:</b> #{position['besitos_rank']}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
```

---

## INTEGRACIÓN

```python
# bot/main.py
from bot.gamification.handlers.user import profile, missions, rewards, leaderboard

dp.include_router(profile.router)
dp.include_router(missions.router)
dp.include_router(rewards.router)
dp.include_router(leaderboard.router)
```

---

## VALIDACIÓN

- ✅ Comando /profile funcional
- ✅ Navegación entre secciones
- ✅ Reclamar recompensas de misiones
- ✅ Leaderboard con posición del usuario
- ✅ Mensajes de error claros

---

**ENTREGABLES:** 4 archivos (profile.py, missions.py, rewards.py, leaderboard.py)
