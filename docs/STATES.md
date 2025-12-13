# Documentación de States (FSM)

Referencia completa de máquinas de estado (Finite State Machine) para conversaciones de usuario.

## Introducción a FSM

FSM en Aiogram permite manejar conversaciones multi-paso. El estado define qué espera el bot del usuario.

**Ventajas:**
- Conversaciones lógicas y lineales
- Fácil validación del contexto
- Gestión de datos temporales (await_data)

**Storage en MVP:**
- MemoryStorage (en RAM, se pierde al reiniciar)
- En ONDA 2+: Redis o Base de datos

## Estados Planeados (ONDA 1)

### AdminStates (Fase 1.2)

Máquina de estado para administradores.

```python
from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    """Estados de la máquina de estado de administrador"""

    # Menú principal
    admin_menu = State()                    # En menú principal

    # Generación de tokens
    generating_token = State()              # Seleccionando duración token
    token_duration_custom = State()         # Ingresando duración personalizada

    # Configuración
    config_menu = State()                   # En menú configuración
    setting_vip_channel = State()           # Configurando canal VIP
    setting_free_channel = State()          # Configurando canal Free
    setting_wait_time = State()             # Configurando tiempo espera
    setting_reactions = State()             # Configurando reacciones

    # Renovación
    renewing_subscription = State()         # Seleccionando suscriptor a renovar
    renew_selecting_user = State()          # Ingresando user_id del usuario

    # Eliminación
    confirming_deletion = State()           # Confirmando eliminación
```

#### Diagrama de Transiciones AdminStates

```
                    ┌─────────────────────────────────┐
                    │    [/admin]                     │
                    │  Presenta menú principal        │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐      ┌──────────┐    ┌────────┐
        │ Generar  │      │ Ver      │    │ Config │
        │ Token    │      │ Tokens   │    │        │
        └────┬─────┘      └──────────┘    └───┬────┘
             │                                 │
             ▼                                 ▼
    ┌─────────────────┐            ┌──────────────────┐
    │ Seleccionar     │            │ Menú Config      │
    │ Duración        │            │                  │
    │ • 24h           │            │ • Canal VIP      │
    │ • 7d            │            │ • Canal Free     │
    │ • 30d           │            │ • Tiempo espera  │
    │ • Custom        │            │ • Reacciones     │
    └────┬────────────┘            └────┬─────────────┘
         │                              │
         ▼                              ▼
    ┌─────────────────┐    ┌──────────────────────┐
    │ [Opción = 24h]  │    │ Ingresar valor nuevo │
    │ Generar token   │    │ (ID canal, minutos)  │
    │ Guardar BD      │    │ Guardar BD           │
    │ ✅ Token creado │    │ ✅ Configurado       │
    └────┬────────────┘    └──────┬───────────────┘
         │                        │
         └────────────┬───────────┘
                      │
                      ▼
                 [Volver a /admin]
```

#### Ejemplos de Uso AdminStates

**Generación de Token:**
```python
# Handler 1: Mostrar opciones de duración
@router.callback_query(lambda c: c.data == "vip_generate")
async def show_duration_options(callback, state):
    await state.set_state(AdminStates.generating_token)
    # Mostrar botones 24h, 7d, 30d, Custom

# Handler 2: Procesar selección
@router.callback_query(AdminStates.generating_token)
async def process_duration(callback, state, session):
    # Generar token
    # Guardar en BD
    # Responder con token creado
    await state.clear()
```

**Configuración Personalizada:**
```python
@router.callback_query(lambda c: c.data == "token_duration_custom")
async def request_custom_duration(callback, state):
    await state.set_state(AdminStates.token_duration_custom)
    await callback.message.answer("Ingresa duración en horas:")

@router.message(AdminStates.token_duration_custom)
async def process_custom_duration(message, state, session):
    hours = int(message.text)
    # Generar token con duración personalizada
    await state.clear()
```

### UserStates (Fase 1.3)

Máquina de estado para usuarios normales.

```python
class UserStates(StatesGroup):
    """Estados de la máquina de estado de usuario"""

    # Menú principal
    user_menu = State()                     # En menú principal

    # VIP
    waiting_for_vip_token = State()         # Esperando ingreso de token VIP
    vip_confirming = State()                # Confirmando token (si es necesario)

    # Free
    waiting_for_free_confirmation = State() # Confirmando solicitud Free
    free_in_queue = State()                 # En cola de espera

    # Información
    viewing_status = State()                # Viendo estado de suscripción
    viewing_help = State()                  # Viendo ayuda
```

### BroadcastStates (T21)

Máquina de estado para envío de publicaciones a canales (broadcasting).

```python
class BroadcastStates(StatesGroup):
    """
    Estados para envío de publicaciones a canales (BROADCASTING AVANZADO).

    Flujo completo:
    1. Admin selecciona canal destino (VIP, Free, o Ambos)
    2. Bot entra en waiting_for_content
    3. Admin envía contenido (texto, foto, o video)
    4. Bot muestra preview y entra en waiting_for_confirmation
    5. Admin confirma o cancela
    6. Si confirma: Bot envía al canal(es) y sale del estado
    7. Si cancela: Bot vuelve a waiting_for_content o sale

    Estados adicionales para reacciones (ONDA 2):
    - selecting_reactions: Admin selecciona reacciones a aplicar

    Tipos de Contenido:
    - Soportar: texto, foto, video
    - Estado waiting_for_content acepta cualquiera
    - Estado waiting_for_confirmation maneja confirmación
    - Estado selecting_reactions permite cambiar reacciones (opcional)
    """

    # Estado 1: Esperando contenido del mensaje a enviar
    waiting_for_content = State()

    # Estado 2: Esperando confirmación de envío (después de preview)
    waiting_for_confirmation = State()

    # Estado 3: Seleccionando reacciones a aplicar (NUEVO - T23)
    selecting_reactions = State()
```

#### Diagrama de Transiciones BroadcastStates

```
                    ┌─────────────────────────────────┐
                    │    [Admin selecciona canal]     │
                    │  Inicia broadcasting            │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐      ┌──────────┐    ┌────────┐
        │ Enviar   │      │ Ver      │    │ Confir │
        │ Contenido│      │ Preview  │    │ mar/env│
        └────┬─────┘      └──────────┘    └───┬────┘
             │                                 │
             ▼                                 ▼
    ┌─────────────────┐            ┌──────────────────┐
    │ Admin envía     │            │ Mostrar preview  │
    │ contenido       │            │ y pedir confirma │
    │ (texto, foto,   │            │ ción             │
    │ video)          │            │                  │
    └────┬────────────┘            └────┬─────────────┘
         │                              │
         ▼                              ▼
    ┌─────────────────┐    ┌──────────────────────┐
    │ [Contenido      │    │ [Confirmar envío]    │
    │ recibido]       │    │ Enviar contenido     │
    │ Procesar        │    │ al canal             │
    │ contenido       │    │ ✅ Enviado           │
    └────┬────────────┘    └──────┬───────────────┘
         │                        │
         └────────────┬───────────┘
                      │
                      ▼
                 [Volver a menú]
```

#### Ejemplos de Uso BroadcastStates

**Envío de Contenido:**
```python
# Handler 1: Iniciar espera de contenido
@admin_router.callback_query(F.data == "vip:broadcast")
async def callback_broadcast_to_vip(callback, state):
    await state.set_data({"target_channel": "vip"})
    await state.set_state(BroadcastStates.waiting_for_content)
    await callback.message.edit_text("Envía el contenido que quieres publicar...")

# Handler 2: Procesar contenido recibido
@admin_router.message(
    BroadcastStates.waiting_for_content,
    F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO])
)
async def process_broadcast_content(message, state, session):
    # Guardar contenido en FSM data
    await state.update_data({
        "content_type": message.content_type,
        "file_id": getattr(message, 'photo', [None])[-1].file_id if message.photo else
                  getattr(message, 'video', None).file_id if message.video else None,
        "caption": getattr(message, 'caption', getattr(message, 'text', ''))
    })

    # Mostrar preview y cambiar a estado de confirmación
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    # Mostrar preview al admin con opciones de confirmación
```

### ReactionSetupStates (T23)

Máquina de estado para configuración de reacciones automáticas.

```python
class ReactionSetupStates(StatesGroup):
    """
    Estados para configuración de reacciones automáticas.

    Flujo:
    1. Admin selecciona "Configurar Reacciones VIP/Free"
    2. Bot entra en waiting_for_vip_reactions o waiting_for_free_reactions
    3. Admin envía lista de emojis separados por espacios
    4. Bot valida (1-10 emojis) y guarda
    5. Bot sale del estado

    Validación de Input:
    - Formato: Emojis separados por espacios
    - Rango válido: 1-10 emojis
    - Si no es válido → Error y mantener estado
    - Si es válido → Guardar en DB y clear state

    NUEVO EN ONDA 2 - T21
    """

    # Esperando lista de emojis para canal VIP
    waiting_for_vip_reactions = State()

    # Esperando lista de emojis para canal Free
    waiting_for_free_reactions = State()
```

#### Diagrama de Transiciones ReactionSetupStates

```
                    ┌─────────────────────────────────┐
                    │    [Admin selecciona config    │
                    │  reacciones VIP o Free]         │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐      ┌──────────┐    ┌────────┐
        │ Config   │      │ Config   │    │ Validar│
        │ Reacc.   │      │ Reacc.   │    │ y guardar│
        │ VIP      │      │ Free     │    │        │
        └────┬─────┘      └────┬─────┘    └────────┘
             │                 │
             ▼                 ▼
    ┌──────────────────┐ ┌─────────────────────┐
    │ Bot entra en     │ │ Bot entra en        │
    │ waiting_for_     │ │ waiting_for_        │
    │ vip_reactions    │ │ free_reactions      │
    │                  │ │                     │
    │ [Admin envía     │ │ [Admin envía        │
    │ emojis]          │ │ emojis]             │
    └────┬─────────────┘ └────┬────────────────┘
         │                    │
         ▼                    ▼
    ┌──────────────────┐ ┌──────────────────┐
    │ Validar emojis   │ │ Validar emojis   │
    │ (1-10, formato)  │ │ (1-10, formato)  │
    │ Guardar en BD    │ │ Guardar en BD    │
    │ Limpiar estado   │ │ Limpiar estado   │
    └────┬─────────────┘ └────┬─────────────┘
         │                    │
         └────────────┬───────┘
                      │
                      ▼
                  [Volver a config]
```

#### Ejemplos de Uso ReactionSetupStates

**Configuración de Reacciones VIP:**
```python
# Handler 1: Iniciar configuración de reacciones VIP
@admin_router.callback_query(F.data == "config:reactions:vip")
async def callback_setup_vip_reactions(callback, session, state):
    await state.set_state(ReactionSetupStates.waiting_for_vip_reactions)
    await callback.message.edit_text(
        "Envía los emojis que quieres usar como reacciones para el canal VIP, "
        "separados por espacios.\n\nEjemplo: 👍 ❤️ 🔥 🎉 💯"
    )

# Handler 2: Procesar emojis recibidos
@admin_router.message(ReactionSetupStates.waiting_for_vip_reactions)
async def process_vip_reactions_input(message, session, state):
    text = message.text.strip()

    # Validar emojis
    is_valid, error_msg, emojis = validate_emoji_list(text)

    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nIntenta nuevamente.")
        return  # Mantener estado para reintentar

    # Guardar reacciones en BD
    container = ServiceContainer(session, message.bot)
    await container.config.set_vip_reactions(emojis)

    await message.answer(
        f"✅ Reacciones VIP configuradas: {' '.join(emojis)}"
    )

    # Limpiar estado
    await state.clear()
```

**Configuración de Reacciones Free:**
```python
# Similar para Free
@admin_router.callback_query(F.data == "config:reactions:free")
async def callback_setup_free_reactions(callback, session, state):
    await state.set_state(ReactionSetupStates.waiting_for_free_reactions)
    await callback.message.edit_text(
        "Envía los emojis que quieres usar como reacciones para el canal Free, "
        "separados por espacios.\n\nEjemplo: ✅ ✔️ ☑️"
    )

@admin_router.message(ReactionSetupStates.waiting_for_free_reactions)
async def process_free_reactions_input(message, session, state):
    # Similar a VIP pero guarda reacciones Free
    # ...
```

#### Diagrama de Transiciones UserStates

```
                    ┌─────────────────────────────────┐
                    │    [/start]                     │
                    │  Presenta menú principal        │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐      ┌──────────┐    ┌────────┐
        │ Acceso   │      │ Acceso   │    │ Ayuda  │
        │ VIP      │      │ Free     │    │        │
        └────┬─────┘      └────┬─────┘    └────────┘
             │                 │
             ▼                 ▼
    ┌──────────────────┐ ┌─────────────────────┐
    │ Esperar token    │ │ Confirmar solicitud │
    │ VIP              │ │ ¿Quieres acceso     │
    │                  │ │ Free (5 min espera)?│
    │ [Usuario ingresa]│ │ [Si] [No]           │
    └────┬─────────────┘ └────┬────────────────┘
         │                    │
         ▼                    ▼
    ┌──────────────────┐ ┌──────────────────┐
    │ Validar token    │ │ Crear solicitud  │
    │ • Existe         │ │ En cola de espera│
    │ • No usado       │ │ [Espera 5 min]   │
    │ • No expirado    │ │                  │
    └────┬─────────────┘ └────┬─────────────┘
         │                    │
         ▼                    ▼
    ┌──────────────────┐ ┌──────────────────┐
    │ ✅ VIP activado  │ │ ✅ Solicitud en  │
    │ Invitado a canal │ │ cola             │
    │ Datos guardados  │ │ Esperar bg task  │
    └────┬─────────────┘ └────┬─────────────┘
         │                    │
         └────────────┬───────┘
                      │
                      ▼
                  [Volver a inicio]
```

#### Ejemplos de Uso UserStates

**Canje de Token VIP:**
```python
# Handler 1: Solicitar token
@router.callback_query(lambda c: c.data == "user_vip")
async def request_vip_token(callback, state):
    await state.set_state(UserStates.waiting_for_vip_token)
    await callback.message.answer("Ingresa tu token VIP:")

# Handler 2: Procesar token
@router.message(UserStates.waiting_for_vip_token)
async def process_vip_token(message, state, session):
    token = message.text.strip()

    # Validar
    token_obj = await validate_token(session, token)

    if token_obj:
        # Crear VIPSubscriber
        # Invitar a canal
        await message.answer("✅ Acceso VIP activado!")
        await state.clear()
    else:
        await message.answer("❌ Token inválido")
        # Volver a pedir token (estado se mantiene)
```

**Solicitud Free:**
```python
# Handler 1: Mostrar confirmación
@router.callback_query(lambda c: c.data == "user_free")
async def request_free(callback, state):
    await state.set_state(UserStates.waiting_for_free_confirmation)
    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Si", callback_data="free_yes"),
            InlineKeyboardButton(text="No", callback_data="free_no"),
        ]
    ])
    await callback.message.answer(
        "Solicitar acceso Free? (espera 5 min)",
        reply_markup=teclado
    )

# Handler 2: Procesar confirmación
@router.callback_query(UserStates.waiting_for_free_confirmation)
async def process_free_confirmation(callback, state, session):
    if callback.data == "free_yes":
        # Crear FreeChannelRequest
        request = FreeChannelRequest(user_id=callback.from_user.id)
        session.add(request)
        await session.commit()
        await callback.answer("✅ Solicitud registrada!")
    else:
        await callback.answer("Cancelado")

    await state.clear()
```

## Datos Persistentes (await_data)

FSMContext permite guardar datos temporales durante una conversación:

```python
# Guardar datos
await state.update_data(
    token="ABC123XYZ456",
    duration=24,
    confirmed=False
)

# Obtener datos
data = await state.get_data()
token = data.get("token")

# Limpiar estado
await state.clear()
```

**Ejemplo de uso:**

```python
@router.callback_query(lambda c: c.data == "vip_generate")
async def start_token_generation(callback, state):
    await state.set_state(AdminStates.generating_token)
    await callback.message.answer("Selecciona duración:")
    # Opciones...

@router.callback_query(AdminStates.generating_token)
async def select_duration(callback, state, session):
    duration_map = {
        "token_24h": 24,
        "token_7d": 168,
        "token_30d": 720,
    }

    duration = duration_map[callback.data]

    # Guardar en contexto
    await state.update_data(duration_hours=duration)

    # Siguiente paso (confirmación)
    await state.set_state(AdminStates.confirming_token)

    data = await state.get_data()
    await callback.message.answer(
        f"Generar token válido por {data['duration_hours']}h? "
        "[Confirmar] [Cancelar]"
    )
```

## Patrón Completo: Multi-paso

Ejemplo de conversación con 3 pasos:

```python
class FormStates(StatesGroup):
    step_1 = State()  # Input A
    step_2 = State()  # Input B
    step_3 = State()  # Confirmación

# Paso 1: Solicitar primer input
@router.callback_query(lambda c: c.data == "start_form")
async def form_step1(callback, state):
    await state.set_state(FormStates.step_1)
    await callback.message.answer("Ingresa valor A:")

# Paso 1: Procesar y ir a paso 2
@router.message(FormStates.step_1)
async def form_step1_handler(message, state):
    value_a = message.text
    await state.update_data(value_a=value_a)

    await state.set_state(FormStates.step_2)
    await message.answer("Ingresa valor B:")

# Paso 2: Procesar y ir a paso 3
@router.message(FormStates.step_2)
async def form_step2_handler(message, state):
    value_b = message.text
    await state.update_data(value_b=value_b)

    # Mostrar confirmación
    data = await state.get_data()

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Confirmar", callback_data="confirm"),
            InlineKeyboardButton(text="Cancelar", callback_data="cancel"),
        ]
    ])

    await state.set_state(FormStates.step_3)
    await message.answer(
        f"Confirma:\nA={data['value_a']}\nB={data['value_b']}",
        reply_markup=teclado
    )

# Paso 3: Procesar confirmación
@router.callback_query(FormStates.step_3)
async def form_confirm(callback, state, session):
    if callback.data == "confirm":
        data = await state.get_data()
        # Procesar datos
        # Guardar en BD
        await callback.answer("✅ Confirmado!")
    else:
        await callback.answer("Cancelado")

    await state.clear()
```

## Limpieza de Estados

Es importante limpiar estados al terminar:

```python
# Opción 1: Limpiar todo
await state.clear()

# Opción 2: Ir a estado neutral
await state.set_state(UserStates.user_menu)

# Opción 3: Obtener datos antes de limpiar
final_data = await state.get_data()
await state.clear()
# Usar final_data...
```

## Casos de Uso Avanzados

### Cancelación en Cualquier Momento

```python
@router.message.command("cancel")
async def cancel(message, state):
    """Permite cancelar en cualquier estado"""
    current = await state.get_state()

    if current is None:
        await message.answer("No hay nada que cancelar")
        return

    await state.clear()
    await message.answer("❌ Operación cancelada")
```

### Reintentos con Límite

```python
RETRY_LIMIT = 3

@router.message(UserStates.waiting_for_vip_token)
async def process_token_with_retries(message, state, session):
    token = message.text

    # Obtener intentos previos
    data = await state.get_data()
    retries = data.get("retries", 0)

    # Validar
    if not is_valid_token(token):
        retries += 1

        if retries >= RETRY_LIMIT:
            await message.answer("❌ Intentos agotados")
            await state.clear()
        else:
            remaining = RETRY_LIMIT - retries
            await state.update_data(retries=retries)
            await message.answer(
                f"❌ Token inválido\n"
                f"Intentos restantes: {remaining}"
            )
        return

    # Token válido
    await process_valid_token(message, session)
    await state.clear()
```

### Timeouts (Futuro - ONDA 2+)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Cancelar estado después de 5 minutos de inactividad
@router.message(UserStates.waiting_for_vip_token)
async def token_handler_with_timeout(message, state):
    # Resetear timer
    scheduler.reschedule_job(
        f"timeout_{message.from_user.id}",
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=5)
    )
    # ...
```

## Debugging de Estados

Ver estado actual del usuario:

```python
@router.message.command("debug_state")
async def debug_state(message, state):
    """Ver estado actual (solo para testing)"""
    current_state = await state.get_state()
    data = await state.get_data()

    await message.answer(
        f"Estado actual: {current_state}\n"
        f"Datos: {data}"
    )
```

## Migración de States

En ONDA 2+, cambiar de MemoryStorage a RedisStorage:

```python
# ONDA 1 (MVP): MemoryStorage
from aiogram.fsm.storage.memory import MemoryStorage
storage = MemoryStorage()

# ONDA 2+: RedisStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
storage = RedisStorage(Redis(host="localhost", port=6379))
```

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
**Estado:** Documentación de states planeados (implementación en fases posteriores)
