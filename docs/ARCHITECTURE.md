# Arquitectura del Bot VIP/Free

Documento técnico que describe la arquitectura, componentes y flujo de datos del bot de administración de canales para Telegram.

## Resumen Arquitectónico

El bot implementa una arquitectura modular y asincrónica optimizada para Termux (Android), con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT API                          │
└────────────────────────┬────────────────────────────────────┘
                         │ (polling)
┌────────────────────────▼────────────────────────────────────┐
│              AIOGRAM DISPATCHER (async)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Middlewares                                             ││
│  │ • AdminAuthMiddleware: Validación de permisos           ││
│  │ • DatabaseMiddleware: Inyección de sesión BD            ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Handlers                                                ││
│  │ ├── Admin: Gestión de canales, tokens, suscriptores    ││
│  │ └── User: Canje de tokens, solicitud Free              ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ FSM States (Memory Storage)                             ││
│  │ • AdminStates: Máquina de estado para admin             ││
│  │ • UserStates: Máquina de estado para usuarios           ││
│  └─────────────────────────────────────────────────────────┘│
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌────────────────┐  ┌─────────────────┐
│  DATABASE    │  │  SERVICES      │  │  BACKGROUND     │
│              │  │                │  │  TASKS          │
│ • BotConfig  │  │ • Subscription │  │                 │
│ • VIPTokens  │  │ • Channel      │  │ • Cleanup       │
│ • VIPSubs    │  │ • Config       │  │ • Processing    │
│ • FreeReqs   │  │                │  │                 │
└──────────────┘  └────────────────┘  └─────────────────┘
     (SQLite)        (Business Logic)   (APScheduler)
```

## Componentes Principales

### 1. Entry Point (main.py)

**Responsabilidad:** Gestionar el ciclo de vida completo del bot

```python
asyncio.run(main())
    ├── on_startup()
    │   ├── Validar configuración
    │   ├── Inicializar base de datos
    │   ├── Registrar handlers y middlewares
    │   └── Notificar a admins que está online
    ├── dp.start_polling()
    │   └── Procesar mensajes en bucle continuo
    └── on_shutdown()
        ├── Detener background tasks
        ├── Cerrar base de datos
        └── Notificar a admins que está offline
```

**Características:**
- Manejo de errores críticos con try-except
- Keyboard interrupt (Ctrl+C) para shutdown graceful
- Logging en todos los pasos
- Drop de updates pendientes del pasado

### 2. Configuración (config.py)

**Responsabilidad:** Gestión centralizada de variables de entorno

**Componentes:**
- `Config.BOT_TOKEN` - Token de Telegram Bot API
- `Config.ADMIN_USER_IDS` - Lista de IDs de administradores
- `Config.DATABASE_URL` - URL de conexión SQLite
- `Config.DEFAULT_WAIT_TIME_MINUTES` - Tiempo espera canal Free
- `Config.LOG_LEVEL` - Nivel de logging (DEBUG, INFO, WARNING, ERROR)
- `Config.TOKEN_LENGTH` - Longitud de tokens (16 caracteres)
- `Config.DEFAULT_TOKEN_DURATION_HOURS` - Duración de tokens (24h)

**Métodos:**
- `validate()` - Valida configuración mínima requerida
- `setup_logging()` - Configura logging según nivel
- `is_admin(user_id)` - Verifica si usuario es admin
- `load_admin_ids()` - Parsea ADMIN_USER_IDS desde .env
- `get_summary()` - Retorna resumen para logging

### 3. Database Layer

**Responsabilidad:** Gestión de persistencia de datos

#### Modelos (models.py)

**BotConfig (Singleton)**
- `id` - Siempre 1 (singleton)
- `vip_channel_id` - ID del canal VIP
- `free_channel_id` - ID del canal Free
- `wait_time_minutes` - Tiempo espera para Free
- `vip_reactions` - JSON array de emojis para VIP
- `free_reactions` - JSON array de emojis para Free
- `subscription_fees` - JSON object con tarifas
- `created_at`, `updated_at` - Timestamps

**InvitationToken**
- `token` - Único, 16 caracteres, indexed
- `generated_by` - User ID del admin que creó
- `created_at` - Timestamp de creación
- `duration_hours` - Duración en horas (default 24)
- `used` - Boolean, indexed
- `used_by` - User ID que canjeó (null si no usado)
- `used_at` - Timestamp de uso (null si no usado)
- **Relación:** 1 Token → Many VIPSubscribers
- **Métodos:**
  - `is_expired()` - Verifica si token expiró
  - `is_valid()` - Verifica si puede usarse (no usado y no expirado)

**VIPSubscriber**
- `user_id` - ID Telegram, unique, indexed
- `join_date` - Timestamp de suscripción
- `expiry_date` - Fecha de expiración
- `status` - "active" o "expired", indexed
- `token_id` - FK a InvitationToken
- **Métodos:**
  - `is_expired()` - Verifica si suscripción expiró
  - `days_remaining()` - Retorna días restantes (negativo si expirado)

**FreeChannelRequest**
- `user_id` - ID Telegram, indexed
- `request_date` - Timestamp de solicitud
- `processed` - Boolean, indexed
- `processed_at` - Timestamp de procesamiento (null si no procesado)
- **Métodos:**
  - `minutes_since_request()` - Minutos desde solicitud
  - `is_ready(wait_time_minutes)` - Verifica si cumplió tiempo espera

#### Engine y Sesiones (engine.py)

**Inicialización:**
```python
init_db()
├── Crear engine con aiosqlite
├── Configurar SQLite (WAL mode, cache 64MB, PRAGMA)
├── Crear tablas
├── Crear session factory
└── Crear BotConfig inicial
```

**Context Manager:**
```python
async with get_session() as session:
    # Usar session
    # commit automático si éxito
    # rollback automático si error
```

**Configuración SQLite para Termux:**
- `PRAGMA journal_mode=WAL` - Write-Ahead Logging para concurrencia
- `PRAGMA synchronous=NORMAL` - Balance performance/seguridad
- `PRAGMA cache_size=-64000` - Cache de 64MB
- `PRAGMA foreign_keys=ON` - Integridad referencial

### 4. Handlers

**Responsabilidad:** Procesar comandos y callbacks de usuarios

**Estructura:**
```
handlers/
├── admin/
│   ├── __init__.py
│   ├── main.py         # /admin - Menú principal (pendiente)
│   ├── vip.py          # Gestión VIP (pendiente)
│   └── free.py         # Gestión Free (pendiente)
└── user/
    ├── __init__.py
    ├── start.py        # /start - Bienvenida (pendiente)
    ├── vip_flow.py     # Flujo canje token (pendiente)
    └── free_flow.py    # Flujo solicitud Free (pendiente)
```

**Patrón de Handler (será usado en fases siguientes):**
```python
@router.message.command("command")
async def command_handler(message: Message, session: AsyncSession) -> None:
    """
    Descripción del handler.

    Args:
        message: Objeto Message de Aiogram
        session: AsyncSession inyectada por middleware
    """
    try:
        # Validar permisos si es necesario
        if not Config.is_admin(message.from_user.id):
            await message.answer("No tienes permisos")
            return

        # Procesar lógica
        # Usar servicios para consultar/actualizar BD

        # Responder usuario
        await message.answer("Respuesta")
    except Exception as e:
        logger.error(f"Error en command_handler: {e}")
        await message.answer("Error procesando comando")
```

### 4.1 Admin Handler (T12)

**Responsabilidad:** Handler del comando /admin que muestra el menú principal de administración con navegación, verificación de estado de configuración y teclado inline

**Componentes:**
- `bot/handlers/admin/main.py` - Handler principal y callbacks de navegación

**Características:**
- **Navegación del menú principal:** Permite navegar entre diferentes secciones de administración con estado de configuración
- **Aplicación de middlewares:** Utiliza AdminAuthMiddleware y DatabaseMiddleware para protección y acceso a base de datos
- **Verificación de estado de configuración:** Muestra estado actual de configuración del bot (completo o incompleto)
- **Callback handlers:** Implementa manejadores de callback para navegación entre menús
- **Teclado inline:** Proporciona opciones de administración a través de teclado inline

**Flujo principal:**
1. Usuario ejecuta `/admin` → Handler verifica permisos y acceso a BD
2. Bot verifica estado de configuración (canal VIP, canal Free, tiempo de espera)
3. Bot muestra menú principal con estado actual
4. Usuario selecciona opción → Bot navega a submenú correspondiente
5. Usuario selecciona "Volver al Menú Principal" → Bot regresa al menú principal

**Estructura de callbacks:**
- `admin:main` - Callback para volver al menú principal
- `admin:config` - Callback para ver configuración detallada
- `admin:vip` - Callback para gestión de canal VIP (futuro)
- `admin:free` - Callback para gestión de canal Free (futuro)

**Aplicación de middlewares:**
```python
# Aplicar middlewares al router de admin (orden correcto)
admin_router.message.middleware(DatabaseMiddleware())
admin_router.message.middleware(AdminAuthMiddleware())
admin_router.callback_query.middleware(DatabaseMiddleware())
admin_router.callback_query.middleware(AdminAuthMiddleware())
```

**Flujo de verificación de estado de configuración:**
1. Handler llama a `container.config.get_config_status()`
2. Servicio retorna diccionario con estado de configuración
3. Handler construye mensaje con estado actual
4. Bot envía mensaje con información de configuración completa o incompleta

**Navegación entre menús usando callbacks:**
```python
# Callback para volver al menú principal
@admin_router.callback_query(F.data == "admin:main")
async def callback_admin_main(callback: CallbackQuery, session: AsyncSession):
    # Crear container de services
    container = ServiceContainer(session, callback.bot)

    # Verificar estado de configuración
    config_status = await container.config.get_config_status()

    # Construir texto del menú (mismo que cmd_admin)
    if config_status["is_configured"]:
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            "✅ Bot configurado correctamente\n\n"
            "Selecciona una opción:"
        )
    else:
        missing_items = ", ".join(config_status["missing"])
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            f"⚠️ <b>Configuración incompleta</b>\n"
            f"Faltante: {missing_items}\n\n"
            "Selecciona una opción para configurar:"
        )

    # Editar mensaje existente (no enviar nuevo)
    await callback.message.edit_text(
        text=text,
        reply_markup=admin_main_menu_keyboard(),
        parse_mode="HTML"
    )

    # Responder al callback (quitar "loading" del botón)
    await callback.answer()
```

**Uso del ServiceContainer en los handlers:**
```python
# Crear container de servicios con sesión de BD y bot
container = ServiceContainer(session, message.bot)

# Acceder a servicios específicos
config_status = await container.config.get_config_status()
```

**Interacción con teclados inline:**
- `admin_main_menu_keyboard()` - Teclado con opciones principales de administración
- `back_to_main_menu_keyboard()` - Teclado con botón para volver al menú principal
- `yes_no_keyboard()` - Teclado para confirmaciones (usado en operaciones futuras)

**Ejemplo completo de handler:**
```python
@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession):
    """
    Handler del comando /admin.

    Muestra el menú principal de administración con estado de configuración.
    """
    logger.info(f"📋 Admin panel abierto por user {message.from_user.id}")

    # Crear container de services
    container = ServiceContainer(session, message.bot)

    # Verificar estado de configuración
    config_status = await container.config.get_config_status()

    # Construir texto del menú
    if config_status["is_configured"]:
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            "✅ Bot configurado correctamente\n\n"
            "Selecciona una opción:"
        )
    else:
        missing_items = ", ".join(config_status["missing"])
        text = (
            "🤖 <b>Panel de Administración</b>\n\n"
            f"⚠️ <b>Configuración incompleta</b>\n"
            f"Faltante: {missing_items}\n\n"
            "Selecciona una opción para configurar:"
        )

    await message.answer(
        text=text,
        reply_markup=admin_main_menu_keyboard(),
        parse_mode="HTML"
    )
```

### 5. Middlewares

**Responsabilidad:** Interceptar y procesar updates antes de handlers

**Middlewares Implementados:**

#### AdminAuthMiddleware (T10)

**Responsabilidad:** Validar que el usuario tenga permisos de administrador antes de ejecutar handlers protegidos

**Características:**
- **Validación automática:** Verifica si el user_id está en la lista de `Config.ADMIN_USER_IDS`
- **Manejo de eventos:** Soporta tanto `Message` como `CallbackQuery` de Telegram
- **Mensajes de error:** Envía mensajes apropiados cuando el acceso es denegado
- **Logging:** Registra intentos de acceso no autorizados con nivel de advertencia
- **Interrupción de flujo:** Si el usuario no es admin, no ejecuta el handler original

**Flujo de operación:**
1. Middleware intercepta el evento (Message o CallbackQuery)
2. Extrae el user_id del evento
3. Verifica si el user_id está en la lista de administradores
4. Si es admin: ejecuta el handler original
5. Si no es admin: envía mensaje de error y retorna None (no ejecuta handler)

**Ejemplo de aplicación:**
```python
# En un router de administración
admin_router = Router()
admin_router.message.middleware(AdminAuthMiddleware())
admin_router.callback_query.middleware(AdminAuthMiddleware())

# Handler protegido por middleware
@admin_router.message(Command("admin_panel"))
async def admin_panel_handler(message: Message, session: AsyncSession):
    # Este handler solo se ejecuta si el usuario es admin
    await message.answer("Panel de administración")
```

**Tipos de respuesta según evento:**
- Para `Message`: Envía respuesta con `event.answer()` en formato HTML
- Para `CallbackQuery`: Envía respuesta con `event.answer(show_alert=True)` como alerta

#### DatabaseMiddleware (T10)

**Responsabilidad:** Inyectar automáticamente una sesión de base de datos en cada handler que lo requiera

**Características:**
- **Inyección automática:** Coloca una instancia de `AsyncSession` en el diccionario `data`
- **Context manager:** Utiliza `async with get_session()` para manejo automático de recursos
- **Commit automático:** Realiza commit si no hay excepciones
- **Rollback automático:** Realiza rollback si ocurre una excepción
- **Cierre automático:** Cierra la sesión al salir del contexto
- **Logging de errores:** Registra errores ocurridos durante la ejecución del handler

**Flujo de operación:**
1. Middleware crea una nueva sesión de base de datos
2. Inyecta la sesión en `data["session"]`
3. Ejecuta el handler original con la sesión disponible
4. Si no hay excepciones: realiza commit automático
5. Si hay excepción: realiza rollback y propaga la excepción
6. Cierra la sesión al finalizar

**Ejemplo de aplicación:**
```python
# Aplicar al dispatcher para que todos los handlers tengan acceso a la sesión
dispatcher.update.middleware(DatabaseMiddleware())

# Handler que recibe la sesión automáticamente
async def user_data_handler(message: Message, session: AsyncSession):
    # La sesión está disponible automáticamente gracias al middleware
    result = await session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()

    if user:
        await message.answer(f"Datos del usuario: {user.name}")
    else:
        await message.answer("Usuario no encontrado")
```

**Patrón de implementación:**
```python
class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with get_session() as session:
            data["session"] = session

            try:
                return await handler(event, data)
            except Exception as e:
                logger.error(f"❌ Error en handler con sesión DB: {e}", exc_info=True)
                raise
```

#### Aplicación combinada de ambos middlewares

Cuando ambos middlewares se aplican juntos, se forma una cadena de procesamiento:

```
1. Evento entrante (Message/CallbackQuery)
   ↓
2. AdminAuthMiddleware: Valida permisos de admin
   ↓ (si es admin, continúa; si no, interrumpe)
3. DatabaseMiddleware: Inyecta sesión de base de datos
   ↓
4. Handler: Recibe evento + sesión, ejecuta lógica
```

**Ejemplo completo de uso combinado:**
```python
from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.middlewares.database import DatabaseMiddleware

# Router para comandos de administrador
admin_router = Router()

# Aplicar ambos middlewares
admin_router.message.middleware(AdminAuthMiddleware())      # Valida permisos
admin_router.callback_query.middleware(AdminAuthMiddleware())  # Valida permisos
# La sesión se inyectará automáticamente gracias al DatabaseMiddleware
# aplicado al dispatcher.update.middleware(DatabaseMiddleware())

@admin_router.message(Command("admin_stats"))
async def admin_stats_handler(message: Message, session: AsyncSession):
    # Este handler solo se ejecuta si:
    # 1. El usuario es admin (validado por AdminAuthMiddleware)
    # 2. Tiene acceso a la sesión de BD (inyectada por DatabaseMiddleware)

    # Usar la sesión para obtener estadísticas
    stats = await get_statistics_from_db(session)

    await message.answer(
        f"📊 Estadísticas del bot:\n{stats}",
        parse_mode="HTML"
    )
```

**Beneficios de la arquitectura de middlewares:**
- **Separación de preocupaciones:** Lógica de autenticación y base de datos separada de la lógica de negocio
- **Reutilización:** Los mismos middlewares se pueden aplicar a múltples routers/handlers
- **Facilidad de mantenimiento:** Cambios en la autenticación o manejo de BD se hacen en un solo lugar
- **Consistencia:** Todos los handlers protegidos y con acceso a BD siguen el mismo patrón
- **Seguridad:** Prevención automática de accesos no autorizados
- **Gestión de recursos:** Manejo automático de sesiones de base de datos

### 6. States (FSM)

**Responsabilidad:** Gestionar estado de conversación de usuarios

**Storage:** MemoryStorage (ligero para Termux)

**Estados Implementados:**

#### ChannelSetupStates
Estados para configurar canales VIP y Free.

**Flujo típico:**
1. Admin selecciona "Configurar Canal VIP"
2. Bot entra en estado waiting_for_vip_channel
3. Admin reenvía mensaje del canal
4. Bot extrae ID del canal y configura
5. Bot sale del estado (clear state)

**Extracción de ID:**
- Usuario reenvía mensaje del canal → Bot extrae forward_from_chat.id
- ID extraído es negativo y empieza con -100
- Si no es forward o no es de canal → Error claro

**Estados disponibles:**
- `waiting_for_vip_channel` - Esperando que admin reenvíe mensaje del canal VIP
- `waiting_for_free_channel` - Esperando que admin reenvíe mensaje del canal Free

**Ejemplo de uso:**
```python
from aiogram.fsm.context import FSMContext
from bot.states.admin import ChannelSetupStates

@admin_router.message(Command("setup_vip_channel"))
async def setup_vip_channel_start(message: Message, state: FSMContext):
    await message.answer("Por favor, reenvía un mensaje del canal VIP para extraer su ID:")
    await state.set_state(ChannelSetupStates.waiting_for_vip_channel)

@admin_router.message(ChannelSetupStates.waiting_for_vip_channel, F.forward_from_chat)
async def process_vip_channel(message: Message, state: FSMContext):
    channel_id = str(message.forward_from_chat.id)

    # Validar que sea un canal y no un grupo
    if int(channel_id) < 0 and channel_id.startswith('-100'):
        # Procesar configuración del canal VIP
        success, msg = await container.channel.setup_vip_channel(channel_id)
        if success:
            await message.answer(f"✅ Canal VIP configurado exitosamente: {channel_id}")
        else:
            await message.answer(f"❌ Error: {msg}")
    else:
        await message.answer("❌ El ID no corresponde a un canal válido. Inténtalo de nuevo:")
        return  # Mantener estado para reintentar

    await state.clear()  # Salir del estado FSM

@admin_router.message(ChannelSetupStates.waiting_for_vip_channel)
async def invalid_vip_channel(message: Message):
    await message.answer("⚠️ Por favor, reenvía un mensaje del canal VIP (no un mensaje normal).")
```

#### WaitTimeSetupStates
Estados para configurar tiempo de espera del canal Free.

**Flujo:**
1. Admin selecciona "Configurar Tiempo de Espera"
2. Bot entra en estado waiting_for_minutes
3. Admin envía número de minutos
4. Bot valida y guarda
5. Bot sale del estado

**Validación de Minutos:**
- Usuario envía texto → Bot intenta convertir a int
- Valor debe ser >= 1
- Si no es número o es inválido → Error y mantener estado

**Estados disponibles:**
- `waiting_for_minutes` - Esperando que admin envíe número de minutos

**Ejemplo de uso:**
```python
from bot.states.admin import WaitTimeSetupStates

@admin_router.message(Command("set_wait_time"))
async def set_wait_time_start(message: Message, state: FSMContext):
    current_time = await container.config.get_wait_time()
    await message.answer(
        f"⏰ Tiempo actual de espera: {current_time} minutos\n\n"
        "Ingresa el nuevo tiempo de espera en minutos (mínimo 1):"
    )
    await state.set_state(WaitTimeSetupStates.waiting_for_minutes)

@admin_router.message(WaitTimeSetupStates.waiting_for_minutes)
async def process_wait_time(message: Message, state: FSMContext):
    try:
        minutes = int(message.text.strip())
        if minutes < 1:
            await message.answer("❌ El tiempo debe ser al menos 1 minuto. Inténtalo de nuevo:")
            return  # Mantener estado para reintentar

        await container.config.set_wait_time(minutes)
        await message.answer(f"✅ Tiempo de espera actualizado a {minutes} minutos.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Por favor, ingresa un número válido de minutos:")
```

#### BroadcastStates
Estados para envío de publicaciones a canales.

**Flujo:**
1. Admin selecciona "Enviar a Canal VIP"
2. Bot entra en estado waiting_for_content
3. Admin envía mensaje (texto, foto o video)
4. Bot pide confirmación (opcional)
5. Bot envía al canal y sale del estado

**Tipos de Contenido:**
- Soportar: texto, foto, video
- Estado waiting_for_content acepta cualquiera
- Estado waiting_for_confirmation es opcional (puede omitirse)

**Estados disponibles:**
- `waiting_for_content` - Esperando contenido del mensaje a enviar
- `waiting_for_confirmation` - Esperando confirmación de envío (opcional)

**Ejemplo de uso:**
```python
from bot.states.admin import BroadcastStates

@admin_router.message(Command("broadcast_vip"))
async def broadcast_vip_start(message: Message, state: FSMContext):
    await message.answer("📤 Por favor, envía el contenido que deseas publicar en el canal VIP:")
    await state.set_state(BroadcastStates.waiting_for_content)

@admin_router.message(BroadcastStates.waiting_for_content)
async def process_broadcast_content(message: Message, state: FSMContext):
    # Almacenar el contenido del mensaje en el estado
    content_data = {
        'text': getattr(message, 'text', getattr(message, 'caption', '')),
        'photo': getattr(message, 'photo', None),
        'video': getattr(message, 'video', None),
        'document': getattr(message, 'document', None)
    }

    # Guardar contenido en el estado para uso posterior
    await state.update_data(content=content_data)

    # Confirmar antes de enviar
    await message.answer("📋 ¿Deseas enviar este contenido al canal VIP ahora?\n\n"
                        "Responde 'Sí' para confirmar o 'No' para cancelar:")
    await state.set_state(BroadcastStates.waiting_for_confirmation)

@admin_router.message(BroadcastStates.waiting_for_confirmation, F.text.lower() == "sí")
async def confirm_broadcast(message: Message, state: FSMContext):
    data = await state.get_data()
    content = data.get('content', {})

    channel_id = await container.channel.get_vip_channel_id()
    if not channel_id:
        await message.answer("❌ Canal VIP no configurado. Configúralo primero.")
        await state.clear()
        return

    # Enviar contenido al canal
    success, result, sent_msg = await container.channel.send_to_channel(
        channel_id=channel_id,
        text=content['text'],
        photo=content.get('photo'),
        video=content.get('video')
    )

    if success:
        await message.answer("✅ Contenido enviado exitosamente al canal VIP.")
    else:
        await message.answer(f"❌ Error al enviar contenido: {result}")

    await state.clear()

@admin_router.message(BroadcastStates.waiting_for_confirmation, F.text.lower() == "no")
async def cancel_broadcast(message: Message, state: FSMContext):
    await message.answer("❌ Envío cancelado.")
    await state.clear()
```

#### TokenRedemptionStates
Estados para canje de tokens VIP.

**Flujo:**
1. Usuario envía /start
2. Bot pregunta por token
3. Bot entra en estado waiting_for_token
4. Usuario envía token
5. Bot valida y canjea
6. Bot sale del estado

**Validación de Token:**
- Usuario envía texto → Bot valida formato y existe en BD
- Token debe estar vigente (no expirado)
- Token debe no estar ya canjeado
- Si token es inválido → Error claro y mantener estado

**Estados disponibles:**
- `waiting_for_token` - Esperando que usuario envíe token

**Ejemplo de uso:**
```python
from bot.states.user import TokenRedemptionStates

@user_router.message(Command("vip"))
async def request_vip_token(message: Message, state: FSMContext):
    await message.answer("🔐 Ingresa tu token VIP para canjear acceso:")
    await state.set_state(TokenRedemptionStates.waiting_for_token)

@user_router.message(TokenRedemptionStates.waiting_for_token)
async def process_vip_token(message: Message, state: FSMContext, session: AsyncSession):
    token_str = message.text.strip()

    # Validar token
    is_valid, validation_msg, token_obj = await container.subscription.validate_token(token_str)

    if not is_valid:
        await message.answer(f"❌ {validation_msg}\n\nIntenta de nuevo:")
        return  # Mantener estado para reintentar

    # Canjear token
    success, redeem_msg, subscriber = await container.subscription.redeem_vip_token(
        token_str=token_str,
        user_id=message.from_user.id
    )

    if success:
        # Crear enlace de invitación
        invite_link = await container.subscription.create_invite_link(
            channel_id=await container.channel.get_vip_channel_id(),
            user_id=message.from_user.id,
            expire_hours=token_obj.duration_hours
        )

        await message.answer(
            f"✅ ¡Acceso VIP concedido!\n\n"
            f"{redeem_msg}\n"
            f"Enlace de acceso: {invite_link}"
        )
    else:
        await message.answer(f"❌ Error al canjear token: {redeem_msg}")

    await state.clear()
```

#### FreeAccessStates
Estados para solicitud de acceso Free.

**Flujo:**
1. Usuario solicita acceso Free
2. Bot crea solicitud
3. Bot puede usar estado para tracking (opcional)

**Nota:** Este flujo es mayormente automático (background task),
pero el estado se puede usar para prevenir spam de solicitudes.

**Estados disponibles:**
- `waiting_for_approval` - Usuario tiene solicitud pendiente

**Ejemplo de uso:**
```python
from bot.states.user import FreeAccessStates

@user_router.message(Command("free"))
async def request_free_access(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id

    # Verificar si ya tiene solicitud pendiente
    existing_request = await container.subscription.get_pending_free_request(user_id)
    if existing_request:
        remaining_minutes = await container.subscription.get_remaining_wait_time(
            existing_request,
            await container.config.get_wait_time()
        )
        await message.answer(
            f"⏳ Ya tienes una solicitud pendiente de acceso Free.\n"
            f"Tiempo restante: {remaining_minutes} minutos."
        )
        return

    # Crear nueva solicitud
    request = await container.subscription.create_free_request(user_id)

    # Poner usuario en estado de espera
    await state.set_state(FreeAccessStates.waiting_for_approval)

    # Informar tiempo de espera
    wait_time = await container.config.get_wait_time()
    await message.answer(
        f"✅ Solicitud de acceso Free registrada.\n"
        f"⏰ Tiempo de espera estimado: {wait_time} minutos.\n\n"
        f"Serás notificado cuando esté listo."
    )

    # El proceso de aprobación ocurre en background
    # No se limpia el estado hasta que se procese la solicitud
```

### 4.2 VIP Handler (T13)

**Responsabilidad:** Handlers del submenú VIP que gestionan el canal VIP con generación de tokens de invitación, configuración del canal VIP por reenvío de mensajes y generación de tokens VIP con duración configurable

**Componentes:**
- `bot/handlers/admin/vip.py` - Handlers principales y callbacks de navegación para el canal VIP

**Características:**
- **Submenú VIP:** Gestión del canal VIP con generación de tokens de invitación
- **Configuración del canal VIP:** Configuración del canal VIP por reenvío de mensajes
- **Generación de tokens de invitación:** Creación de tokens VIP con duración configurable
- **Uso de FSM:** Utiliza ChannelSetupStates para el flujo de configuración del canal
- **Interacción con teclados inline:** Proporciona opciones de administración a través de teclado inline
- **Verificación de configuración:** Verifica que el canal VIP esté configurado antes de permitir ciertas operaciones

**Flujo principal:**
1. Usuario admin ejecuta callback `admin:vip` → Handler verifica permisos y acceso a BD
2. Bot verifica estado de configuración del canal VIP
3. Bot muestra menú VIP con estado actual del canal
4. Usuario selecciona opción (generar token o configurar canal)
5. Usuario selecciona "Volver al Menú Principal" → Bot regresa al menú principal

**Estructura de callbacks:**
- `admin:vip` - Callback para mostrar el menú VIP
- `vip:setup` - Callback para iniciar configuración del canal VIP
- `vip:generate_token` - Callback para generar token VIP

**Aplicación de FSM:**
```python
# Aplicar estados FSM para configuración del canal VIP
@admin_router.message(ChannelSetupStates.waiting_for_vip_channel)
async def process_vip_channel_forward(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el mensaje reenviado para configurar el canal VIP.

    Extrae el ID del canal del forward y lo configura.

    Args:
        message: Mensaje reenviado del canal
        session: Sesión de BD
        state: FSM context
    """
    # Verificar que es un forward de un canal
    if not message.forward_from_chat:
        await message.answer(
            "❌ Debes <b>reenviar</b> un mensaje del canal VIP.\n\n"
            "No me envíes el ID manualmente, reenvía un mensaje.",
            parse_mode="HTML"
        )
        return

    forward_chat = message.forward_from_chat

    # Verificar que es un canal (no grupo ni usuario)
    if forward_chat.type not in ["channel", "supergroup"]:
        await message.answer(
            "❌ El mensaje debe ser de un <b>canal</b> o <b>supergrupo</b>.\n\n"
            "Reenvía un mensaje del canal VIP.",
            parse_mode="HTML"
        )
        return

    channel_id = str(forward_chat.id)
    channel_title = forward_chat.title

    logger.info(f"📺 Configurando canal VIP: {channel_id} ({channel_title})")

    container = ServiceContainer(session, message.bot)

    # Intentar configurar el canal
    success, msg = await container.channel.setup_vip_channel(channel_id)

    if success:
        # Configuración exitosa
        await message.answer(
            f"✅ <b>Canal VIP Configurado</b>\n\n"
            f"Canal: <b>{channel_title}</b>\n"
            f"ID: <code>{channel_id}</code>\n\n"
            f"Ya puedes generar tokens de invitación.",
            parse_mode="HTML",
            reply_markup=vip_menu_keyboard(True)
        )

        # Limpiar estado FSM
        await state.clear()
    else:
        # Error en configuración
        await message.answer(
            f"{msg}\n\n"
            f"Verifica que:\n"
            f"• El bot es administrador del canal\n"
            f"• El bot tiene permiso para invitar usuarios\n\n"
            f"Intenta nuevamente reenviando un mensaje del canal.",
            parse_mode="HTML"
        )
        # Mantener estado FSM para reintentar
```

**Flujo de generación de tokens VIP:**
1. Usuario admin selecciona "Generar Token de Invitación"
2. Bot verifica que canal VIP está configurado
3. Bot genera token único con duración configurable
4. Bot responde con el token y su información

**Ejemplo de generación de token:**
```python
@admin_router.callback_query(F.data == "vip:generate_token")
async def callback_generate_vip_token(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Genera un token de invitación VIP.

    Token válido por 24 horas, un solo uso.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"🎟️ Usuario {callback.from_user.id} generando token VIP")

    container = ServiceContainer(session, callback.bot)

    # Verificar que canal VIP está configurado
    if not await container.channel.is_vip_channel_configured():
        await callback.answer(
            "❌ Debes configurar el canal VIP primero",
            show_alert=True
        )
        return

    try:
        # Generar token (24 horas por defecto)
        token = await container.subscription.generate_vip_token(
            generated_by=callback.from_user.id,
            duration_hours=Config.DEFAULT_TOKEN_DURATION_HOURS
        )

        # Crear mensaje con el token
        token_message = (
            f"🎟️ <b>Token VIP Generado</b>\n\n"
            f"Token: <code>{token.token}</code>\n\n"
            f"⏱️ Válido por: {token.duration_hours} horas\n"
            f"📅 Expira: {token.created_at.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
            f"👉 Comparte este token con el usuario.\n"
            f"El usuario debe enviarlo al bot para canjear acceso VIP."
        )

        await callback.message.answer(
            text=token_message,
            parse_mode="HTML"
        )

        await callback.answer("✅ Token generado")

    except Exception as e:
        logger.error(f"Error generando token VIP: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al generar token. Intenta nuevamente.",
            show_alert=True
        )
```

**Uso del ServiceContainer en los handlers VIP:**
```python
# Crear container de servicios con sesión de BD y bot
container = ServiceContainer(session, callback.bot)

# Acceder a servicios específicos
is_configured = await container.channel.is_vip_channel_configured()
token = await container.subscription.generate_vip_token(...)
```

**Interacción con teclados inline VIP:**
```python
def vip_menu_keyboard(is_configured: bool) -> "InlineKeyboardMarkup":
    """
    Keyboard del submenú VIP.

    Args:
        is_configured: Si el canal VIP está configurado

    Returns:
        InlineKeyboardMarkup con opciones VIP
    """
    buttons = []

    if is_configured:
        buttons.extend([
            [{"text": "🎟️ Generar Token de Invitación", "callback_data": "vip:generate_token"}],
            [{"text": "🔧 Reconfigurar Canal", "callback_data": "vip:setup"}],
        ])
    else:
        buttons.append([{"text": "⚙️ Configurar Canal VIP", "callback_data": "vip:setup"}])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:main"}])

    return create_inline_keyboard(buttons)
```

### 4.3 Free Handler (T13)

**Responsabilidad:** Handlers del submenú Free que gestionan el canal Free con configuración de tiempo de espera, configuración del canal Free por reenvío de mensajes y configuración de tiempo de espera para acceso Free

### 4.4 User Handler (T14)

**Responsabilidad:** Handler del comando /start que detecta el rol del usuario y proporciona flujos para canje de tokens VIP y solicitud de acceso Free

**Componentes:**
- `bot/handlers/user/start.py` - Handler principal del comando /start
- `bot/handlers/user/vip_flow.py` - Flujo de canje de tokens VIP
- `bot/handlers/user/free_flow.py` - Flujo de solicitud de acceso Free

**Características:**
- **Handler /start:** Punto de entrada para usuarios con detección de rol (admin/VIP/usuario)
- **Flujo VIP:** Canje de tokens VIP con validación y generación de invite links
- **Flujo Free:** Solicitud de acceso Free con tiempo de espera y notificaciones automáticas
- **Middleware de base de datos:** Inyección de sesiones sin autenticación de admin
- **FSM para validación de tokens:** Estados para manejo de entrada de tokens
- **Validación de configuración:** Verificación de canales configurados antes de procesar

**Flujo principal:**
1. Usuario ejecuta `/start` → Handler verifica acceso a BD
2. Bot detecta rol del usuario (admin, VIP, usuario normal)
3. Si es admin: redirige a `/admin`
4. Si es VIP: muestra mensaje de bienvenida con días restantes
5. Si es usuario normal: muestra menú con opciones VIP/Free
6. Usuario selecciona opción → Bot inicia flujo correspondiente

**Estructura de callbacks:**
- `user:redeem_token` - Callback para iniciar flujo de canje de token VIP
- `user:request_free` - Callback para iniciar flujo de solicitud Free
- `user:cancel` - Callback para cancelar flujo actual

**Aplicación de FSM:**
```python
# Aplicar estados FSM para canje de tokens VIP
@user_router.message(TokenRedemptionStates.waiting_for_token)
async def process_token_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el token enviado por el usuario.

    Valida el token, lo canjea y envía invite link.

    Args:
        message: Mensaje con el token
        session: Sesión de BD
        state: FSM context
    """
    user_id = message.from_user.id
    token_str = message.text.strip()

    container = ServiceContainer(session, message.bot)

    # Intentar canjear token
    success, msg, subscriber = await container.subscription.redeem_vip_token(
        token_str=token_str,
        user_id=user_id
    )

    if not success:
        # Token inválido
        await message.answer(
            f"{msg}\n\n"
            f"Verifica el token e intenta nuevamente.\n\n"
            f"Si el problema persiste, contacta al administrador.",
            parse_mode="HTML"
        )
        # Mantener estado para reintentar
        return

    # Token válido: crear invite link
    vip_channel_id = await container.channel.get_vip_channel_id()

    try:
        invite_link = await container.subscription.create_invite_link(
            channel_id=vip_channel_id,
            user_id=user_id,
            expire_hours=1  # Link expira en 1 hora
        )

        # Calcular días restantes
        if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
            from datetime import datetime, timezone
            days_remaining = max(0, (subscriber.expiry_date - datetime.now(timezone.utc)).days)
        else:
            days_remaining = 0

        await message.answer(
            f"✅ <b>Token Canjeado Exitosamente!</b>\n\n"
            f"🎉 Tu acceso VIP está activo\n"
            f"⏱️ Duración: <b>{days_remaining} días</b>\n\n"
            f"👇 Usa este link para unirte al canal VIP:\n"
            f"{invite_link.invite_link}\n\n"
            f"⚠️ <b>Importante:</b>\n"
            f"• El link expira en 1 hora\n"
            f"• Solo puedes usarlo 1 vez\n"
            f"• No lo compartas con otros\n\n"
            f"Disfruta del contenido exclusivo! 🚀",
            parse_mode="HTML"
        )

        # Limpiar estado
        await state.clear()

    except Exception as e:
        logger.error(f"Error creando invite link para user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Error al crear el link de invitación.\n\n"
            "Tu token fue canjeado correctamente, pero hubo un problema técnico.\n"
            "Contacta al administrador.",
            parse_mode="HTML"
        )
        await state.clear()
```

**Flujo de detección de rol:**
1. Usuario envía `/start`
2. Bot verifica si es admin usando `Config.is_admin()`
3. Si es admin: redirige a panel de administración
4. Si no es admin: verifica si es VIP activo
5. Si es VIP: muestra días restantes de suscripción
6. Si no es VIP: muestra opciones de acceso (VIP/Free)

**Ejemplo de detección de rol:**
```python
@user_router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """
    Handler del comando /start para usuarios.

    Comportamiento:
    - Si es admin → Redirige a /admin
    - Si es VIP activo → Muestra mensaje de bienvenida con días restantes
    - Si no es admin → Muestra menú de usuario (VIP/Free)
    """
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Usuario"

    # Verificar si es admin
    if Config.is_admin(user_id):
        await message.answer(
            f"👋 Hola <b>{user_name}</b>!\n\n"
            f"Eres administrador. Usa /admin para gestionar los canales.",
            parse_mode="HTML"
        )
        return

    # Usuario normal: verificar si es VIP activo
    container = ServiceContainer(session, message.bot)

    is_vip = await container.subscription.is_vip_active(user_id)

    if is_vip:
        # Usuario ya tiene acceso VIP
        subscriber = await container.subscription.get_vip_subscriber(user_id)

        # Calcular días restantes
        if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
            from datetime import datetime, timezone
            days_remaining = max(0, (subscriber.expiry_date - datetime.now(timezone.utc)).days)
        else:
            days_remaining = 0

        await message.answer(
            f"👋 Hola <b>{user_name}</b>!\n\n"
            f"✅ Tienes acceso VIP activo\n"
            f"⏱️ Días restantes: <b>{days_remaining}</b>\n\n"
            f"Disfruta del contenido exclusivo! 🎉",
            parse_mode="HTML"
        )
        return

    # Usuario no es VIP: mostrar opciones
    keyboard = create_inline_keyboard([
        [{"text": "🎟️ Canjear Token VIP", "callback_data": "user:redeem_token"}],
        [{"text": "📺 Solicitar Acceso Free", "callback_data": "user:request_free"}],
    ])

    await message.answer(
        f"👋 Hola <b>{user_name}</b>!\n\n"
        f"Bienvenido al bot de acceso a canales.\n\n"
        f"<b>Opciones disponibles:</b>\n\n"
        f"🎟️ <b>Canjear Token VIP</b>\n"
        f"Si tienes un token de invitación, canjéalo para acceso VIP.\n\n"
        f"📺 <b>Solicitar Acceso Free</b>\n"
        f"Solicita acceso al canal gratuito (con tiempo de espera).\n\n"
        f"👉 Selecciona una opción:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
```

**Uso del ServiceContainer en los handlers User:**
```python
# Crear container de servicios con sesión de BD y bot
container = ServiceContainer(session, message.bot)

# Acceder a servicios específicos
is_vip = await container.subscription.is_vip_active(user_id)
subscriber = await container.subscription.get_vip_subscriber(user_id)
success, msg, subscriber = await container.subscription.redeem_vip_token(token_str, user_id)
is_configured = await container.channel.is_vip_channel_configured()
wait_time = await container.config.get_wait_time()
```

**Interacción con teclados inline User:**
```python
# Teclado para opciones de usuario
keyboard = create_inline_keyboard([
    [{"text": "🎟️ Canjear Token VIP", "callback_data": "user:redeem_token"}],
    [{"text": "📺 Solicitar Acceso Free", "callback_data": "user:request_free"}],
])

# Teclado para cancelar flujo
cancel_keyboard = create_inline_keyboard([
    [{"text": "❌ Cancelar", "callback_data": "user:cancel"}]
])
```

**Flujo de canje de tokens VIP:**
1. Usuario selecciona "Canjear Token VIP"
2. Bot verifica que canal VIP esté configurado
3. Bot entra en estado FSM `waiting_for_token`
4. Usuario envía token
5. Bot valida y canjea token
6. Bot genera invite link único y lo envía al usuario
7. Bot limpia estado FSM

**Flujo de solicitud Free:**
1. Usuario selecciona "Solicitar Acceso Free"
2. Bot verifica que canal Free esté configurado
3. Bot verifica si usuario ya tiene solicitud pendiente
4. Si no tiene solicitud: crea nueva solicitud y notifica tiempo de espera
5. Si ya tiene solicitud: muestra tiempo restante
6. Proceso automático en background procesa solicitudes cuando cumplen tiempo

**Validación de configuración:**
- `is_vip_channel_configured()` - Verifica que canal VIP esté configurado antes de permitir canje de tokens
- `is_free_channel_configured()` - Verifica que canal Free esté configurado antes de permitir solicitudes
- `get_wait_time()` - Obtiene tiempo de espera configurado para solicitudes Free
```

### 4.6 Stats Handler (T19)

**Responsabilidad:** Handlers del panel de estadísticas que proporcionan métricas generales y detalladas sobre el sistema, incluyendo suscriptores VIP, solicitudes Free y tokens de invitación, con funcionalidades de caching y actualización manual.

**Componentes:**
- `bot/handlers/admin/stats.py` - Handlers principales y callbacks de navegación para el panel de estadísticas

**Características:**
- **Dashboard general:** Visualización de métricas generales del sistema (VIP, Free, Tokens)
- **Estadísticas VIP detalladas:** Métricas sobre suscriptores VIP (activos, expirados, próximos a expirar)
- **Estadísticas Free detalladas:** Métricas sobre solicitudes Free (pendientes, procesadas, tiempos de espera)
- **Estadísticas de tokens:** Métricas sobre tokens de invitación (generados, usados, expirados, tasa de conversión)
- **Sistema de cache:** Implementación de cache con TTL de 5 minutos para optimizar performance
- **Actualización manual:** Posibilidad de forzar recálculo de estadísticas ignorando el cache
- **Formato visual:** Mensajes HTML formateados con iconos y estructura clara
- **Proyecciones de ingresos:** Cálculo de ingresos proyectados mensuales y anuales basados en suscriptores activos

**Flujo principal:**
1. Usuario admin selecciona "📊 Estadísticas" en el menú principal
2. Bot muestra dashboard de estadísticas generales con cache
3. Usuario puede navegar entre diferentes vistas de estadísticas
4. Bot actualiza estadísticas cada 5 minutos (cache TTL)
5. Usuario puede forzar actualización manual con "🔄 Actualizar Estadísticas"

**Estructura de callbacks:**
- `admin:stats` - Callback para mostrar el dashboard general de estadísticas
- `admin:stats:vip` - Callback para mostrar estadísticas VIP detalladas
- `admin:stats:free` - Callback para mostrar estadísticas Free detalladas
- `admin:stats:tokens` - Callback para mostrar estadísticas de tokens
- `admin:stats:refresh` - Callback para forzar recálculo de estadísticas (ignorar cache)

**Aplicación de ServiceContainer:**
```python
# Aplicar container de servicios para acceder al servicio de estadísticas
container = ServiceContainer(session, callback.bot)

# Acceder al servicio de estadísticas
stats = await container.stats.get_overall_stats()
vip_stats = await container.stats.get_vip_stats()
free_stats = await container.stats.get_free_stats()
token_stats = await container.stats.get_token_stats()
```

**Flujo de estadísticas generales:**
1. Admin selecciona "📊 Estadísticas" en menú principal
2. Bot llama a `container.stats.get_overall_stats()` con cache
3. Bot formatea mensaje con `_format_overall_stats_message()`
4. Bot envía mensaje con teclado de estadísticas
5. Admin puede navegar entre vistas o actualizar

**Ejemplo de handler de estadísticas generales:**
```python
@admin_router.callback_query(F.data == "admin:stats")
async def callback_stats_general(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra dashboard de estadísticas generales.

    Incluye:
    - Resumen VIP (activos, expirados, próximos a expirar)
    - Resumen Free (pendientes, procesadas)
    - Resumen Tokens (generados, usados, disponibles)
    - Actividad reciente (hoy, semana, mes)
    - Proyección de ingresos

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió estadísticas generales")

    # Mostrar "cargando..." temporalmente
    await callback.answer("📊 Calculando estadísticas...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener estadísticas generales (con cache)
        stats = await container.stats.get_overall_stats()

        # Construir mensaje
        text = _format_overall_stats_message(stats)

        await callback.message.edit_text(
            text=text,
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.debug(f"✅ Stats generales mostradas a user {callback.from_user.id}")

    except Exception as e:
        logger.error(f"❌ Error obteniendo stats: {e}", exc_info=True)

        await callback.message.edit_text(
            "❌ <b>Error al Calcular Estadísticas</b>\n\n"
            "Hubo un problema al obtener las métricas.\n"
            "Intenta nuevamente en unos momentos.",
            reply_markup=back_to_main_menu_keyboard(),
            parse_mode="HTML"
        )
```

**Flujo de estadísticas VIP detalladas:**
1. Admin selecciona "📊 Ver Stats VIP Detalladas"
2. Bot llama a `container.stats.get_vip_stats()` con cache
3. Bot formatea mensaje con `_format_vip_stats_message()`
4. Bot incluye información sobre suscriptores activos, expirados y próximos a expirar
5. Bot envía mensaje con teclado de estadísticas

**Flujo de estadísticas Free detalladas:**
1. Admin selecciona "📊 Ver Stats Free Detalladas"
2. Bot llama a `container.stats.get_free_stats()` con cache
3. Bot formatea mensaje con `_format_free_stats_message()`
4. Bot incluye información sobre solicitudes listas para procesar y tiempo promedio de espera
5. Bot envía mensaje con teclado de estadísticas

**Flujo de estadísticas de tokens:**
1. Admin selecciona "🎟️ Ver Stats de Tokens"
2. Bot llama a `container.stats.get_token_stats()` con cache
3. Bot formatea mensaje con `_format_token_stats_message()`
4. Bot incluye tasa de conversión y métricas por período
5. Bot envía mensaje con teclado de estadísticas

**Flujo de actualización manual:**
1. Admin selecciona "🔄 Actualizar Estadísticas"
2. Bot llama a servicios con `force_refresh=True`
3. Servicios ignoran cache y recalculan desde BD
4. Bot actualiza mensaje con estadísticas recién calculadas
5. Cache se actualiza con nuevos valores

**Interacción con teclados inline:**
```python
def stats_menu_keyboard() -> "InlineKeyboardMarkup":
    """
    Keyboard del menú de estadísticas.

    Opciones:
    - Ver Stats VIP Detalladas
    - Ver Stats Free Detalladas
    - Ver Stats de Tokens
    - Actualizar Estadísticas (force refresh)
    - Volver al Menú Principal

    Returns:
        InlineKeyboardMarkup con menú de stats
    """
    return create_inline_keyboard([
        [{"text": "📊 Ver Stats VIP Detalladas", "callback_data": "admin:stats:vip"}],
        [{"text": "📊 Ver Stats Free Detalladas", "callback_data": "admin:stats:free"}],
        [{"text": "🎟️ Ver Stats de Tokens", "callback_data": "admin:stats:tokens"}],
        [{"text": "🔄 Actualizar Estadísticas", "callback_data": "admin:stats:refresh"}],
        [{"text": "🔙 Volver al Menú Principal", "callback_data": "admin:main"}],
    ])
```

**Formato de mensajes de estadísticas:**
- `_format_overall_stats_message()` - Dashboard general con secciones VIP, Free, Tokens, Actividad y Proyección de Ingresos
- `_format_vip_stats_message()` - Estadísticas VIP con secciones Estado General, Próximas a Expirar, Actividad Reciente y Top Suscriptores
- `_format_free_stats_message()` - Estadísticas Free con secciones Estado General, Procesamiento, Actividad Reciente y Próximas a Procesar
- `_format_token_stats_message()` - Estadísticas de Tokens con secciones Estado General, Generados/Usados por Período y Tasa de Conversión

**Funciones de utilidad:**
- `format_currency(amount)` - Formatea cantidades como moneda (ej: "$1,234.56")
- `format_percentage(value)` - Formatea valores como porcentaje (ej: "85.5%")

**Manejo de errores:**
- Cada handler está envuelto en try-catch para manejar errores de cálculo de estadísticas
- Mensajes de error claros para el usuario administrador
- Logging detallado de errores para debugging
- Retorno a menú de estadísticas en caso de error
```

### 4.5 Free Handler (T13)

**Responsabilidad:** Handlers del submenú Free que gestionan el canal Free con configuración de tiempo de espera, configuración del canal Free por reenvío de mensajes y configuración de tiempo de espera para acceso Free

**Componentes:**
- `bot/handlers/admin/free.py` - Handlers principales y callbacks de navegación para el canal Free

**Características:**
- **Submenú Free:** Gestión del canal Free con configuración de tiempo de espera
- **Configuración del canal Free:** Configuración del canal Free por reenvío de mensajes
- **Configuración de tiempo de espera:** Configuración de tiempo de espera para acceso Free
- **Uso de FSM:** Utiliza ChannelSetupStates y WaitTimeSetupStates para flujos de configuración
- **Interacción con teclados inline:** Proporciona opciones de administración a través de teclado inline
- **Verificación de configuración:** Verifica que el canal Free esté configurado antes de permitir ciertas operaciones

**Flujo principal:**
1. Usuario admin ejecuta callback `admin:free` → Handler verifica permisos y acceso a BD
2. Bot verifica estado de configuración del canal Free y tiempo de espera
3. Bot muestra menú Free con estado actual del canal y tiempo de espera
4. Usuario selecciona opción (configurar tiempo de espera o configurar canal)
5. Usuario selecciona "Volver al Menú Principal" → Bot regresa al menú principal

**Estructura de callbacks:**
- `admin:free` - Callback para mostrar el menú Free
- `free:setup` - Callback para iniciar configuración del canal Free
- `free:set_wait_time` - Callback para configurar tiempo de espera

**Aplicación de FSM:**
```python
# Aplicar estados FSM para configuración del canal Free
@admin_router.message(ChannelSetupStates.waiting_for_free_channel)
async def process_free_channel_forward(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el mensaje reenviado para configurar el canal Free.

    Args:
        message: Mensaje reenviado del canal
        session: Sesión de BD
        state: FSM context
    """
    # Validaciones idénticas a VIP
    if not message.forward_from_chat:
        await message.answer(
            "❌ Debes <b>reenviar</b> un mensaje del canal Free.\n\n"
            "No me envíes el ID manualmente, reenvía un mensaje.",
            parse_mode="HTML"
        )
        return

    forward_chat = message.forward_from_chat

    if forward_chat.type not in ["channel", "supergroup"]:
        await message.answer(
            "❌ El mensaje debe ser de un <b>canal</b> o <b>supergrupo</b>.\n\n"
            "Reenvía un mensaje del canal Free.",
            parse_mode="HTML"
        )
        return

    channel_id = str(forward_chat.id)
    channel_title = forward_chat.title

    logger.info(f"📺 Configurando canal Free: {channel_id} ({channel_title})")

    container = ServiceContainer(session, message.bot)

    # Intentar configurar el canal
    success, msg = await container.channel.setup_free_channel(channel_id)

    if success:
        await message.answer(
            f"✅ <b>Canal Free Configurado</b>\n\n"
            f"Canal: <b>{channel_title}</b>\n"
            f"ID: <code>{channel_id}</code>\n\n"
            f"Los usuarios ya pueden solicitar acceso.",
            parse_mode="HTML",
            reply_markup=free_menu_keyboard(True)
        )

        await state.clear()
    else:
        await message.answer(
            f"{msg}\n\n"
            f"Verifica permisos del bot e intenta nuevamente.",
            parse_mode="HTML"
        )
```

**Flujo de configuración de tiempo de espera:**
1. Usuario admin selecciona "Configurar Tiempo de Espera"
2. Bot entra en estado FSM `waiting_for_minutes`
3. Usuario envía número de minutos
4. Bot valida y guarda el tiempo de espera
5. Bot actualiza configuración y sale del estado

**Ejemplo de configuración de tiempo de espera:**
```python
@admin_router.callback_query(F.data == "free:set_wait_time")
async def callback_set_wait_time(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia configuración de tiempo de espera.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⏱️ Usuario {callback.from_user.id} configurando wait time")

    container = ServiceContainer(session, callback.bot)
    current_wait_time = await container.config.get_wait_time()

    # Entrar en estado FSM
    await state.set_state(WaitTimeSetupStates.waiting_for_minutes)

    text = (
        f"⏱️ <b>Configurar Tiempo de Espera</b>\n\n"
        f"Tiempo actual: <b>{current_wait_time} minutos</b>\n\n"
        f"Envía el nuevo tiempo de espera en minutos.\n"
        f"Ejemplo: <code>5</code>\n\n"
        f"El tiempo debe ser mayor o igual a 1 minuto."
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "❌ Cancelar", "callback_data": "admin:free"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje wait time: {e}")

    await callback.answer()

@admin_router.message(WaitTimeSetupStates.waiting_for_minutes)
async def process_wait_time_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el input de tiempo de espera.

    Args:
        message: Mensaje con los minutos
        session: Sesión de BD
        state: FSM context
    """
    # Intentar convertir a número
    try:
        minutes = int(message.text)
    except ValueError:
        await message.answer(
            "❌ Debes enviar un número válido.\n\n"
            "Ejemplo: <code>5</code>",
            parse_mode="HTML"
        )
        return

    # Validar rango
    if minutes < 1:
        await message.answer(
            "❌ El tiempo debe ser al menos 1 minuto.\n\n"
            "Envía un número mayor o igual a 1.",
            parse_mode="HTML"
        )
        return

    container = ServiceContainer(session, message.bot)

    try:
        # Actualizar configuración
        await container.config.set_wait_time(minutes)

        await message.answer(
            f"✅ <b>Tiempo de Espera Actualizado</b>\n\n"
            f"Nuevo tiempo: <b>{minutes} minutos</b>\n\n"
            f"Las nuevas solicitudes esperarán {minutes} minutos antes de procesarse.",
            parse_mode="HTML",
            reply_markup=free_menu_keyboard(True)
        )

        # Limpiar estado
        await state.clear()

    except Exception as e:
        logger.error(f"Error actualizando wait time: {e}", exc_info=True)
        await message.answer(
            "❌ Error al actualizar el tiempo de espera.\n\n"
            "Intenta nuevamente.",
            parse_mode="HTML"
        )
```

**Uso del ServiceContainer en los handlers Free:**
```python
# Crear container de servicios con sesión de BD y bot
container = ServiceContainer(session, callback.bot)

# Acceder a servicios específicos
is_configured = await container.channel.is_free_channel_configured()
wait_time = await container.config.get_wait_time()
await container.config.set_wait_time(minutes)
```

**Interacción con teclados inline Free:**
```python
def free_menu_keyboard(is_configured: bool) -> "InlineKeyboardMarkup":
    """
    Keyboard del submenú Free.

    Args:
        is_configured: Si el canal Free está configurado

    Returns:
        InlineKeyboardMarkup con opciones Free
    """
    buttons = []

    if is_configured:
        buttons.extend([
            [{"text": "⏱️ Configurar Tiempo de Espera", "callback_data": "free:set_wait_time"}],
            [{"text": "🔧 Reconfigurar Canal", "callback_data": "free:setup"}],
        ])
    else:
        buttons.append([{"text": "⚙️ Configurar Canal Free", "callback_data": "free:setup"}])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:main"}])

    return create_inline_keyboard(buttons)
```

**Flujo de configuración por reenvío de mensajes:**
1. Admin selecciona "Configurar Canal VIP" o "Configurar Canal Free"
2. Bot entra en estado FSM correspondiente
3. Admin reenvía mensaje del canal objetivo
4. Bot extrae ID del canal del mensaje reenviado
5. Bot verifica permisos del bot en el canal
6. Bot guarda configuración si todo es válido
7. Bot limpia estado FSM y actualiza menú

### 4.7 Broadcasting Handler (T22)

**Responsabilidad:** Handlers del sistema de broadcasting que permiten a los administradores enviar contenido a los canales VIP y Free con funcionalidad de vista previa y confirmación antes del envío.

**Componentes:**
- `bot/handlers/admin/broadcast.py` - Handlers principales y callbacks de navegación para el sistema de broadcasting

**Características:**
- **Envío de contenido:** Envío de texto, fotos y videos a canales VIP y Free
- **Vista previa:** Visualización del contenido antes de enviarlo al canal
- **Confirmación de envío:** Confirmación opcional antes de publicar en el canal
- **Uso de FSM:** Utiliza BroadcastStates para el flujo de envío de contenido
- **Interacción con teclados inline:** Proporciona opciones de confirmación y control a través de teclado inline
- **Tipos de contenido soportados:** Texto, foto con caption opcional, video con caption opcional

**Flujo principal:**
1. Usuario admin selecciona "📤 Enviar a Canal VIP" o "📤 Enviar a Canal Free" en menú de gestión
2. Bot entra en estado FSM `waiting_for_content`
3. Usuario envía contenido (texto, foto o video)
4. Bot procesa contenido y entra en estado `waiting_for_confirmation`
5. Bot muestra vista previa y solicita confirmación
6. Usuario confirma o cancela envío
7. Si confirma: Bot envía contenido al canal y limpia estado FSM
8. Si cancela: Bot limpia estado FSM y regresa al menú principal

**Estructura de callbacks:**
- `vip:broadcast` - Callback para iniciar broadcasting al canal VIP
- `free:broadcast` - Callback para iniciar broadcasting al canal Free
- `broadcast:confirm` - Callback para confirmar envío de contenido
- `broadcast:cancel` - Callback para cancelar broadcasting
- `broadcast:change` - Callback para cambiar contenido antes de enviar

**Aplicación de FSM:**
```python
# Aplicar estados FSM para broadcasting
@admin_router.callback_query(F.data == "vip:broadcast")
async def callback_broadcast_to_vip(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Inicia broadcasting al canal VIP.

    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"📤 Usuario {callback.from_user.id} iniciando broadcast a VIP")

    # Guardar canal destino en FSM data
    await state.set_data({"target_channel": "vip"})

    # Entrar en estado FSM
    await state.set_state(BroadcastStates.waiting_for_content)

    text = (
        "📤 <b>Enviar Publicación a Canal VIP</b>\n\n"
        "Envía el contenido que quieres publicar:\n\n"
        "• <b>Texto:</b> Envía un mensaje de texto\n"
        "• <b>Foto:</b> Envía una foto (con caption opcional)\n"
        "• <b>Video:</b> Envía un video (con caption opcional)\n\n"
        "El mensaje será enviado exactamente como lo envíes.\n\n"
        "👁️ Verás un preview antes de confirmar el envío."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()

@admin_router.message(
    BroadcastStates.waiting_for_content,
    F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO])
)
async def process_broadcast_content(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el contenido enviado para broadcasting.

    Guarda el contenido en FSM data y muestra preview.

    Args:
        message: Mensaje con el contenido
        state: FSM context
        session: Sesión de BD
    """
    user_id = message.from_user.id

    # Obtener data del FSM
    data = await state.get_data()
    target_channel = data.get("target_channel", "vip")

    logger.info(
        f"📥 Usuario {user_id} envió contenido para broadcast a {target_channel}"
    )

    # Determinar tipo de contenido
    content_type = message.content_type
    caption = None

    if content_type == ContentType.PHOTO:
        # Guardar file_id de la foto más grande
        photo = message.photo[-1]  # Última foto es la más grande
        file_id = photo.file_id
        caption = message.caption

    elif content_type == ContentType.VIDEO:
        file_id = message.video.file_id
        caption = message.caption

    else:  # TEXT
        file_id = None
        caption = message.text

    # Actualizar FSM data con contenido
    await state.update_data({
        "content_type": content_type,
        "file_id": file_id,
        "caption": caption,
        "original_message_id": message.message_id,
    })

    # Mostrar preview
    preview_text = await _generate_preview_text(target_channel, content_type, caption)

    # Enviar preview al admin
    await message.answer(
        text=preview_text,
        reply_markup=create_inline_keyboard([
            [
                {"text": "✅ Confirmar y Enviar", "callback_data": "broadcast:confirm"},
                {"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}
            ],
            [{"text": "🔄 Enviar Otro Contenido", "callback_data": "broadcast:change"}]
        ]),
        parse_mode="HTML"
    )

    # Reenviar el contenido como preview visual
    if content_type == ContentType.PHOTO:
        await message.answer_photo(
            photo=file_id,
            caption="👁️ <i>Preview del mensaje</i>",
            parse_mode="HTML"
        )
    elif content_type == ContentType.VIDEO:
        await message.answer_video(
            video=file_id,
            caption="👁️ <i>Preview del mensaje</i>",
            parse_mode="HTML"
        )

    # Cambiar a estado de confirmación
    await state.set_state(BroadcastStates.waiting_for_confirmation)

    logger.debug(f"✅ Preview generado para user {user_id}")
```

**Flujo de envío con confirmación:**
1. Admin selecciona "📤 Enviar a Canal VIP" o "📤 Enviar a Canal Free"
2. Bot entra en estado `waiting_for_content`
3. Admin envía contenido (texto, foto o video)
4. Bot procesa contenido y entra en estado `waiting_for_confirmation`
5. Bot muestra vista previa del contenido
6. Bot solicita confirmación con teclado inline
7. Admin confirma o cancela envío
8. Si confirma: Bot envía contenido al canal y limpia estado
9. Si cancela: Bot limpia estado y regresa al menú

**Ejemplo de confirmación de envío:**
```python
@admin_router.callback_query(
    BroadcastStates.waiting_for_confirmation,
    F.data == "broadcast:confirm"
)
async def callback_broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Confirma y envía el mensaje al canal(es).

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    user_id = callback.from_user.id

    # Obtener data del FSM
    data = await state.get_data()
    target_channel = data["target_channel"]
    content_type = data["content_type"]
    file_id = data.get("file_id")
    caption = data.get("caption")

    logger.info(f"📤 Usuario {user_id} confirmó broadcast a {target_channel}")

    # Notificar que se está enviando
    await callback.answer("📤 Enviando publicación...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    # Determinar canales destino
    channels_to_send = []

    if target_channel == "vip":
        vip_channel = await container.channel.get_vip_channel_id()
        if vip_channel:
            channels_to_send.append(("VIP", vip_channel))

    elif target_channel == "free":
        free_channel = await container.channel.get_free_channel_id()
        if free_channel:
            channels_to_send.append(("Free", free_channel))

    # Validar que hay canales configurados
    if not channels_to_send:
        await callback.message.edit_text(
            "❌ <b>Error: Canales No Configurados</b>\n\n"
            "Debes configurar los canales antes de enviar publicaciones.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver", "callback_data": "admin:main"}]
            ]),
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Enviar a cada canal
    results = []

    for channel_name, channel_id in channels_to_send:
        try:
            if content_type == ContentType.PHOTO:
                success, msg, _ = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or "",
                    photo=file_id
                )

            elif content_type == ContentType.VIDEO:
                success, msg, _ = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or "",
                    video=file_id
                )

            else:  # TEXT
                success, msg, _ = await container.channel.send_to_channel(
                    channel_id=channel_id,
                    text=caption or ""
                )

            if success:
                results.append(f"✅ Canal {channel_name}")
                logger.info(f"✅ Publicación enviada a canal {channel_name}")
            else:
                results.append(f"❌ Canal {channel_name}: {msg}")
                logger.error(f"❌ Error enviando a {channel_name}: {msg}")

        except Exception as e:
            results.append(f"❌ Canal {channel_name}: Error inesperado")
            logger.error(f"❌ Excepción enviando a {channel_name}: {e}", exc_info=True)

    # Mostrar resultados
    results_text = "\n".join(results)

    await callback.message.edit_text(
        f"📤 <b>Resultado del Envío</b>\n\n{results_text}\n\n"
        f"La publicación ha sido procesada.",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "admin:main"}]
        ]),
        parse_mode="HTML"
    )

    # Limpiar estado FSM
    await state.clear()

    logger.info(f"✅ Broadcasting completado para user {user_id}")
```

**Uso del ServiceContainer en los handlers de broadcasting:**
```python
# Crear container de servicios con sesión de BD y bot
container = ServiceContainer(session, callback.bot)

# Acceder a servicios específicos
vip_channel = await container.channel.get_vip_channel_id()
free_channel = await container.channel.get_free_channel_id()
success, msg, _ = await container.channel.send_to_channel(
    channel_id=channel_id,
    text=caption or "",
    photo=file_id
)
```

**Interacción con teclados inline de broadcasting:**
```python
# Teclado para confirmación de envío
confirmation_keyboard = create_inline_keyboard([
    [
        {"text": "✅ Confirmar y Enviar", "callback_data": "broadcast:confirm"},
        {"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}
    ],
    [{"text": "🔄 Enviar Otro Contenido", "callback_data": "broadcast:change"}]
])

# Teclado para cancelación de broadcasting
cancel_keyboard = create_inline_keyboard([
    [{"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}]
])
```

### 4.8 Reactions Handler (T23)

**Responsabilidad:** Handlers del sistema de configuración de reacciones automáticas que permiten a los administradores definir emojis que se aplicarán automáticamente a las publicaciones en los canales VIP y Free.

**Componentes:**
- `bot/handlers/admin/reactions.py` - Handlers principales y callbacks de navegación para el sistema de reacciones

**Características:**
- **Configuración de reacciones VIP:** Configuración de emojis para el canal VIP
- **Configuración de reacciones Free:** Configuración de emojis para el canal Free
- **Validación de emojis:** Validación de formato y cantidad de emojis (1-10)
- **Uso de FSM:** Utiliza ReactionSetupStates para el flujo de configuración de reacciones
- **Interacción con teclados inline:** Proporciona opciones de navegación a través de teclado inline
- **Persistencia de configuración:** Almacenamiento en la tabla BotConfig

**Flujo principal:**
1. Usuario admin selecciona "⚙️ Configurar Reacciones VIP" o "⚙️ Configurar Reacciones Free" en menú de configuración
2. Bot entra en estado FSM correspondiente (`waiting_for_vip_reactions` o `waiting_for_free_reactions`)
3. Usuario envía emojis separados por espacios
4. Bot valida formato y cantidad de emojis
5. Si válido: Bot guarda configuración y limpia estado FSM
6. Si inválido: Bot mantiene estado FSM y solicita reingreso

**Estructura de callbacks:**
- `config:reactions:vip` - Callback para iniciar configuración de reacciones VIP
- `config:reactions:free` - Callback para iniciar configuración de reacciones Free

**Aplicación de FSM:**
```python
# Aplicar estados FSM para configuración de reacciones VIP
@admin_router.callback_query(F.data == "config:reactions:vip")
async def callback_setup_vip_reactions(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia configuración de reacciones para canal VIP.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} configurando reacciones VIP")

    container = ServiceContainer(session, callback.bot)

    # Obtener reacciones actuales
    current_reactions = await container.config.get_vip_reactions()

    if current_reactions:
        current_text = " ".join(current_reactions)
        status_text = f"<b>Reacciones actuales:</b> {current_text}\n\n"
    else:
        status_text = "<b>Reacciones actuales:</b> <i>Ninguna configurada</i>\n\n"

    # Entrar en estado FSM
    await state.set_state(ReactionSetupStates.waiting_for_vip_reactions)

    text = (
        "⚙️ <b>Configurar Reacciones VIP</b>\n\n"
        f"{status_text}"
        "Envía los emojis que quieres usar como reacciones, "
        "separados por espacios.\n\n"
        "<b>Ejemplo:</b> <code>👍 ❤️ 🔥 🎉 💯</code>\n\n"
        "<b>Reglas:</b>\n"
        "• Mínimo: 1 emoji\n"
        "• Máximo: 10 emojis\n"
        "• Solo emojis válidos\n\n"
        "Las reacciones se aplicarán automáticamente a "
        "nuevas publicaciones en el canal VIP."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:config"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()

@admin_router.message(ReactionSetupStates.waiting_for_vip_reactions)
async def process_vip_reactions_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    """
    Procesa el input de reacciones VIP.

    Args:
        message: Mensaje con emojis
        session: Sesión de BD
        state: FSM context
    """
    user_id = message.from_user.id
    text = message.text.strip()

    logger.info(f"⚙️ Usuario {user_id} enviando reacciones VIP: {text}")

    # Validar emojis
    is_valid, error_msg, emojis = validate_emoji_list(text)

    if not is_valid:
        # Input inválido
        await message.answer(
            f"❌ <b>Input Inválido</b>\n\n"
            f"{error_msg}\n\n"
            f"Por favor, envía los emojis separados por espacios.\n"
            f"Ejemplo: <code>👍 ❤️ 🔥</code>",
            parse_mode="HTML"
        )
        # Mantener estado FSM para reintentar
        return

    container = ServiceContainer(session, message.bot)

    try:
        # Guardar reacciones
        await container.config.set_vip_reactions(emojis)

        reactions_text = " ".join(emojis)

        await message.answer(
            f"✅ <b>Reacciones VIP Configuradas</b>\n\n"
            f"<b>Reacciones:</b> {reactions_text}\n"
            f"<b>Total:</b> {len(emojis)} emojis\n\n"
            f"Estas reacciones se aplicarán automáticamente a "
            f"nuevas publicaciones en el canal VIP.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔙 Volver a Configuración", "callback_data": "admin:config"}]
            ]),
            parse_mode="HTML"
        )

        # Limpiar estado FSM
        await state.clear()

        logger.info(f"✅ Reacciones VIP configuradas: {len(emojis)} emojis")

    except ValueError as e:
        # Error de validación del service
        logger.error(f"❌ Error validando reacciones VIP: {e}")

        await message.answer(
            f"❌ <b>Error al Guardar Reacciones</b>\n\n"
            f"{str(e)}\n\n"
            f"Intenta nuevamente.",
            parse_mode="HTML"
        )
        # Mantener estado para reintentar

    except Exception as e:
        # Error inesperado
        logger.error(f"❌ Error guardando reacciones VIP: {e}", exc_info=True)

        await message.answer(
            "❌ <b>Error Inesperado</b>\n\n"
            "No se pudieron guardar las reacciones.\n"
            "Intenta nuevamente.",
            parse_mode="HTML"
        )
        await state.clear()
```

**Flujo de configuración de reacciones:**
1. Admin selecciona "⚙️ Configurar Reacciones VIP" o "⚙️ Configurar Reacciones Free"
2. Bot entra en estado FSM correspondiente
3. Bot muestra reacciones actuales y solicita nuevas reacciones
4. Admin envía emojis separados por espacios
5. Bot valida formato y cantidad (1-10 emojis)
6. Bot guarda configuración en BD
7. Bot limpia estado FSM y actualiza menú

**Validación de reacciones:**
- Mínimo 1 emoji
- Máximo 10 emojis
- Solo caracteres de emoji válidos
- Formato: emojis separados por espacios

**Uso del ServiceContainer en los handlers de reacciones:**
```python
# Crear container de servicios con sesión de BD y bot
container = ServiceContainer(session, message.bot)

# Acceder a servicios específicos
current_reactions = await container.config.get_vip_reactions()
await container.config.set_vip_reactions(emojis)
current_reactions = await container.config.get_free_reactions()
await container.config.set_free_reactions(emojis)
```

**Interacción con teclados inline de reacciones:**
```python
# Teclado para cancelación de configuración de reacciones
cancel_keyboard = create_inline_keyboard([
    [{"text": "❌ Cancelar", "callback_data": "admin:config"}]
])

# Teclado para volver a menú de configuración
back_to_config_keyboard = create_inline_keyboard([
    [{"text": "🔙 Volver a Configuración", "callback_data": "admin:config"}]
])
```

### 7. Services

**Responsabilidad:** Lógica de negocio reutilizable

**Servicios Disponibles:**

```
services/
├── container.py        # Contenedor de servicios (DI + Lazy Loading)
├── subscription.py     # Gestión de suscripciones VIP/Free
├── channel.py          # Gestión de canales Telegram
├── config.py           # Config service
└── stats.py            # Estadísticas
```

#### Service Container (T6)

Implementación del patrón Dependency Injection + Lazy Loading para reducir consumo de memoria en Termux:

**Arquitectura:**
```python
class ServiceContainer:
    def __init__(self, session: AsyncSession, bot: Bot):
        self._session = session
        self._bot = bot

        # Servicios (cargados lazy)
        self._subscription_service = None
        self._channel_service = None
        self._config_service = None
        self._stats_service = None

    @property
    def subscription(self):
        """Carga lazy el servicio de suscripciones"""
        if self._subscription_service is None:
            from bot.services.subscription import SubscriptionService
            self._subscription_service = SubscriptionService(self._session, self._bot)
        return self._subscription_service

    # Similar para otros servicios...

    def get_loaded_services(self) -> list[str]:
        """Retorna lista de servicios ya cargados en memoria"""
        # Útil para debugging y monitoreo de uso de memoria
```

**Características:**
- **Lazy Loading:** servicios se instancian solo cuando se acceden por primera vez
- **Optimización de Memoria:** reduce el consumo inicial de memoria en Termux
- **4 servicios disponibles:** subscription, channel, config, stats
- **Monitoreo:** método `get_loaded_services()` para tracking de uso de memoria
- **Precarga opcional:** `preload_critical_services()` para servicios críticos

**Uso:**
```python
container = ServiceContainer(session, bot)

# Primera vez: carga el servicio (lazy loading)
token = await container.subscription.generate_token(...)

# Segunda vez: reutiliza instancia ya cargada
result = await container.subscription.validate_token(...)
```

#### Subscription Service (T7)

Gestión completa de suscripciones VIP y Free con 14 métodos asíncronos:

**Responsabilidades:**
- Generación de tokens de invitación VIP
- Validación y canje de tokens
- Gestión de suscriptores VIP (crear, extender, expirar)
- Gestión de solicitudes Free (crear, procesar)
- Limpieza automática de datos antiguos

**Flujos Implementados:**

**VIP Flow:**
```
1. Admin genera token → generate_vip_token()
2. Usuario canjea token → redeem_vip_token()
3. Usuario recibe invite link → create_invite_link()
4. Suscripción expira automáticamente → expire_vip_subscribers() (background)
```

**Free Flow:**
```
1. Usuario solicita acceso → create_free_request()
2. Espera N minutos
3. Sistema procesa cola → process_free_queue() (background)
4. Usuario recibe invite link
```

**Características principales:**
- **Tokens VIP:** 16 caracteres alfanuméricos, únicos, expiran después de N horas
- **Cola Free:** sistema de espera configurable con `wait_time`
- **Invite links únicos:** enlaces de un solo uso (`member_limit=1`)
- **Gestión de usuarios:** creación, extensión y expiración automática de suscripciones
- **Limpieza automática:** elimina datos antiguos para mantener rendimiento

**Ejemplo de uso:**
```python
# Generar token VIP
token = await container.subscription.generate_vip_token(
    generated_by=admin_user_id,
    duration_hours=24
)

# Validar token
is_valid, message, token_obj = await container.subscription.validate_token("token_string")

# Canjear token VIP
success, message, subscriber = await container.subscription.redeem_vip_token(
    token_str="token_string",
    user_id=user_id
)

# Crear solicitud Free
request = await container.subscription.create_free_request(user_id)

# Procesar cola Free
processed_requests = await container.subscription.process_free_queue(
    wait_time_minutes=Config.WAIT_TIME_MINUTES
)

# Crear invite link único
invite_link = await container.subscription.create_invite_link(
    channel_id="-1001234567890",
    user_id=user_id,
    expire_hours=1
)
```

#### Channel Service (T8)

Gestión completa de canales VIP y Free con verificación de permisos y envío de publicaciones:

**Responsabilidades:**
- Configuración de canales VIP y Free con validación de existencia
- Verificación de permisos del bot (can_invite_users, can_post_messages)
- Envío de contenido a canales (texto, fotos, videos)
- Reenvío y copia de mensajes entre chats y canales
- Validación de configuración de canales

**Flujos Implementados:**

**Setup Channel Flow:**
```
1. Admin configura canal → setup_vip_channel() o setup_free_channel()
2. Bot verifica que el canal existe
3. Bot verifica que es admin del canal
4. Bot verifica permisos necesarios (can_invite_users, can_post_messages)
5. Canal guardado en BotConfig
```

**Send to Channel Flow:**
```
1. Admin/envío automático → send_to_channel()
2. Bot determina tipo de contenido (texto, foto, video)
3. Bot envía mensaje al canal
4. Retorno de resultado exitoso/error
```

**Permissions Verification Flow:**
```
1. Bot obtiene información del miembro → get_chat_member()
2. Verifica que sea admin o creador
3. Verifica permisos específicos (can_invite_users, can_post_messages)
4. Retorna mensaje detallado de permisos faltantes
```

**Características principales:**
- **Configuración segura:** verificación de existencia y permisos antes de guardar
- **Permisos completos:** verifica can_invite_users y can_post_messages
- **Soporte multimedia:** envío de texto, fotos y videos
- **Operaciones avanzadas:** reenvío y copia de mensajes
- **Validación robusta:** verificaciones de formato e ID de canal

**Ejemplos de uso:**
```python
# Configuración de canal VIP
success, message = await container.channel.setup_vip_channel("-1001234567890")
if success:
    print(f"Canal VIP configurado: {message}")
else:
    print(f"Error en configuración: {message}")

# Configuración de canal Free
success, message = await container.channel.setup_free_channel("-1009876543210")
if success:
    print(f"Canal Free configurado: {message}")
else:
    print(f"Error en configuración: {message}")

# Verificación de permisos del bot
is_valid, perm_message = await container.channel.verify_bot_permissions("-1001234567890")
if is_valid:
    print("Bot tiene todos los permisos necesarios")
else:
    print(f"Permisos insuficientes: {perm_message}")

# Envío de mensaje de texto al canal
sent_success, sent_message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="¡Nueva publicación en el canal VIP!",
    parse_mode="HTML"
)
if sent_success:
    print(f"Mensaje enviado: {sent_message}")
else:
    print(f"Error al enviar: {sent_message}")

# Envío de foto con texto al canal
sent_success, sent_message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="Foto destacada del día",
    photo="AgACAgQAAxkBAA...",
    parse_mode="HTML"
)

# Envío de video con descripción
sent_success, sent_message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="Video promocional",
    video="BAACAgQAAxkBAA...",
    parse_mode="HTML"
)

# Reenvío de mensaje a canal
forward_success, forward_message = await container.channel.forward_to_channel(
    channel_id="-1001234567890",
    from_chat_id=-1009876543210,
    message_id=123
)

# Copia de mensaje a canal (sin firma de origen)
copy_success, copy_message = await container.channel.copy_to_channel(
    channel_id="-1001234567890",
    from_chat_id=-1009876543210,
    message_id=123
)

# Verificación de configuración de canales
is_vip_configured = await container.channel.is_vip_channel_configured()
is_free_configured = await container.channel.is_free_channel_configured()
print(f"Canales configurados - VIP: {is_vip_configured}, Free: {is_free_configured}")

# Obtención de IDs de canales
vip_channel_id = await container.channel.get_vip_channel_id()
free_channel_id = await container.channel.get_free_channel_id()

if vip_channel_id:
    print(f"Canal VIP ID: {vip_channel_id}")
if free_channel_id:
    print(f"Canal Free ID: {free_channel_id}")

# Obtención de información del canal
channel_info = await container.channel.get_channel_info("-1001234567890")
if channel_info:
    print(f"Nombre del canal: {channel_info.title}")
    print(f"Tipo de canal: {channel_info.type}")

member_count = await container.channel.get_channel_member_count("-1001234567890")
if member_count:
    print(f"Número de miembros: {member_count}")
```

#### Config Service (T9)

Gestión de configuración global del bot con funcionalidades clave para administrar la configuración centralizada:

**Responsabilidades:**
- Obtener/actualizar configuración de BotConfig (singleton)
- Gestionar tiempo de espera Free
- Gestionar reacciones de canales
- Validar que la configuración está completa
- Configurar tarifas de suscripción
- Proporcionar resumen de configuración

**Características principales:**
- **Singleton Pattern:** BotConfig es un registro único (id=1) que almacena toda la configuración global
- **Tiempo de espera configurable:** Gestión flexible del tiempo de espera para acceso al canal Free
- **Reacciones personalizables:** Configuración de emojis para reacciones en canales VIP y Free
- **Validación integral:** Verificación completa de la configuración para asegurar funcionamiento óptimo
- **Tarifas de suscripción:** Soporte para múltiples tipos de tarifas (mensual, anual, etc.)
- **Resumen de configuración:** Información detallada del estado de la configuración para administradores

**Flujos Implementados:**

**Get Configuration Flow:**
```
1. Servicio solicita configuración → get_config()
2. Consulta a BD por registro con id=1
3. Retorna objeto BotConfig
4. Validación de existencia (debe existir siempre)
```

**Set Wait Time Flow:**
```
1. Admin define tiempo de espera → set_wait_time(minutes)
2. Validación: minutos >= 1
3. Actualiza campo wait_time_minutes en BotConfig
4. Guarda cambios en BD
5. Log de cambio realizado
```

**Set Channel Reactions Flow:**
```
1. Admin define reacciones → set_vip_reactions() o set_free_reactions()
2. Validación: lista no vacía, máximo 10 elementos
3. Actualiza campo correspondiente (vip_reactions o free_reactions)
4. Guarda cambios en BD
5. Log de reacciones actualizadas
```

**Validation Flow:**
```
1. Verificación de configuración completa → is_fully_configured()
2. Valida:
   - Canal VIP configurado (vip_channel_id != null)
   - Canal Free configurado (free_channel_id != null)
   - Tiempo de espera >= 1 minuto
3. Retorna booleano indicando estado
```

**Ejemplos de uso:**
```python
# Obtención de configuración global
config = await container.config.get_config()
print(f"Canal VIP: {config.vip_channel_id}")
print(f"Canal Free: {config.free_channel_id}")
print(f"Tiempo de espera: {config.wait_time_minutes} minutos")

# Configuración de tiempos de espera
current_wait_time = await container.config.get_wait_time()
print(f"Tiempo actual de espera: {current_wait_time} minutos")
await container.config.set_wait_time(15)  # 15 minutos de espera

# Gestión de reacciones de canales
current_vip_reactions = await container.config.get_vip_reactions()
print(f"Reacciones VIP actuales: {current_vip_reactions}")

# Actualizar reacciones VIP
await container.config.set_vip_reactions(["👍", "❤️", "🔥", "🎉"])
await container.config.set_free_reactions(["✅", "✔️", "☑️"])

# Configuración de tarifas de suscripción
current_fees = await container.config.get_subscription_fees()
print(f"Tarifas actuales: {current_fees}")

# Actualizar tarifas de suscripción
await container.config.set_subscription_fees({
    "monthly": 10.0,
    "yearly": 100.0,
    "lifetime": 500.0
})

# Validación de configuración completa
is_configured = await container.config.is_fully_configured()
if is_configured:
    print("Bot completamente configurado")
else:
    status = await container.config.get_config_status()
    print(f"Faltan elementos: {', '.join(status['missing'])}")

# Obtención de resumen de configuración
summary = await container.config.get_config_summary()
print(summary)

# Resetear a valores por defecto (advertencia: borra configuración de canales)
await container.config.reset_to_defaults()
```

### 8. Background Tasks (T15)

**Responsabilidad:** Tareas programadas asincrónicas que realizan operaciones periódicas para mantener el sistema funcionando correctamente

**Tareas Implementadas:**
- `expire_and_kick_vip_subscribers()` - Marcar VIPs expirados y expulsarlos del canal
- `process_free_queue()` - Procesar cola de solicitudes Free que cumplieron tiempo de espera
- `cleanup_old_data()` - Eliminar solicitudes Free procesadas hace más de 30 días

**Componentes:**
```
background/
├── __init__.py
├── tasks.py          # Tareas programadas y scheduler
```

**Arquitectura:**
```python
import logging
from typing import Optional
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# Scheduler global
_scheduler: Optional[AsyncIOScheduler] = None

async def expire_and_kick_vip_subscribers(bot: Bot):
    """
    Tarea: Expulsar suscriptores VIP expirados del canal.
    """
    logger.info("🔄 Ejecutando tarea: Expulsión VIP expirados")

    try:
        async with get_session() as session:
            container = ServiceContainer(session, bot)

            # Verificar que canal VIP está configurado
            vip_channel_id = await container.channel.get_vip_channel_id()

            if not vip_channel_id:
                logger.warning("⚠️ Canal VIP no configurado, saltando expulsión")
                return

            # Marcar como expirados
            expired_count = await container.subscription.expire_vip_subscribers()

            if expired_count > 0:
                logger.info(f"⏱️ {expired_count} suscriptor(es) VIP expirados")

                # Expulsar del canal
                kicked_count = await container.subscription.kick_expired_vip_from_channel(
                    vip_channel_id
                )

                logger.info(f"✅ {kicked_count} usuario(s) expulsados del canal VIP")
            else:
                logger.debug("✓ No hay VIPs expirados")

    except Exception as e:
        logger.error(f"❌ Error en tarea de expulsión VIP: {e}", exc_info=True)

def start_background_tasks(bot: Bot):
    """
    Inicia el scheduler con todas las tareas programadas.
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("⚠️ Scheduler ya está corriendo")
        return

    logger.info("🚀 Iniciando background tasks...")

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Tarea 1: Expulsión VIP expirados
    # Frecuencia: Cada 60 minutos (Config.CLEANUP_INTERVAL_MINUTES)
    _scheduler.add_job(
        expire_and_kick_vip_subscribers,
        trigger=IntervalTrigger(minutes=Config.CLEANUP_INTERVAL_MINUTES),
        args=[bot],
        id="expire_vip",
        name="Expulsar VIPs expirados",
        replace_existing=True,
        max_instances=1
    )

    # Tarea 2: Procesamiento cola Free
    # Frecuencia: Cada 5 minutos (Config.PROCESS_FREE_QUEUE_MINUTES)
    _scheduler.add_job(
        process_free_queue,
        trigger=IntervalTrigger(minutes=Config.PROCESS_FREE_QUEUE_MINUTES),
        args=[bot],
        id="process_free_queue",
        name="Procesar cola Free",
        replace_existing=True,
        max_instances=1
    )

    # Tarea 3: Limpieza de datos antiguos
    # Frecuencia: Diaria a las 3 AM UTC
    _scheduler.add_job(
        cleanup_old_data,
        trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),
        args=[bot],
        id="cleanup_old_data",
        name="Limpieza de datos antiguos",
        replace_existing=True,
        max_instances=1
    )

    # Iniciar scheduler
    _scheduler.start()
    logger.info("✅ Background tasks iniciados correctamente")

def stop_background_tasks():
    """
    Detiene el scheduler y todas las tareas programadas.
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("⚠️ Scheduler no está corriendo")
        return

    logger.info("🛑 Deteniendo background tasks...")

    _scheduler.shutdown(wait=True)
    _scheduler = None

    logger.info("✅ Background tasks detenidos correctamente")
```

**Flujos Implementados:**

**VIP Expiration Flow:**
```
1. [Cada 60 minutos] Tarea expire_and_kick_vip_subscribers() se ejecuta
   ├→ Verifica si canal VIP está configurado
   ├→ Busca suscriptores VIP con expiry_date < datetime.now()
   ├→ Marca como expirados (status = "expired")
   ├→ Expulsa del canal VIP usando Telegram API
   └→ Log de resultados
```

**Free Queue Processing Flow:**
```
1. [Cada 5 minutos] Tarea process_free_queue() se ejecuta
   ├→ Verifica si canal Free está configurado
   ├→ Busca solicitudes Free con (request_date + wait_time) < datetime.now()
   ├→ Para cada solicitud:
   │  ├→ Marca como procesada
   │  ├→ Crea invite link único (member_limit=1, expire_hours=24)
   │  ├→ Envía link al usuario por mensaje privado
   │  └→ Log de éxito/error
   └→ Log de resultados
```

**Data Cleanup Flow:**
```
1. [Diariamente a las 3 AM UTC] Tarea cleanup_old_data() se ejecuta
   ├→ Busca solicitudes Free con request_date > 30 días
   ├→ Elimina registros antiguos
   └→ Log de cantidad eliminada
```

**Configuración de Variables de Entorno:**
- `CLEANUP_INTERVAL_MINUTES` - Intervalo para expulsión de VIPs expirados (default: 60)
- `PROCESS_FREE_QUEUE_MINUTES` - Intervalo para procesamiento de cola Free (default: 5)

**Ejemplo de uso en main.py:**
```python
from bot.background import start_background_tasks, stop_background_tasks

async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    # ... otras inicializaciones ...

    # Iniciar background tasks
    start_background_tasks(bot)

async def on_shutdown(bot: Bot, dispatcher: Dispatcher) -> None:
    # Detener background tasks
    stop_background_tasks()

    # ... otras tareas de cierre ...
```

**Manejo de Errores:**
- Cada tarea está envuelta en try-catch para evitar interrupciones
- Logging detallado de errores con traceback
- Continuidad de otras tareas si una falla
- Validación de configuración antes de ejecutar tareas

**Monitoreo:**
- Función `get_scheduler_status()` para obtener estado del scheduler
- Logging detallado de ejecución de tareas
- Conteo de elementos procesados por cada tarea
- Información de próxima ejecución de tareas
```

### 9. Utilities

**Responsabilidad:** Funciones y utilidades comunes

**Módulos Planeados:**
- `keyboards.py` - Factory de inline/reply keyboards
- `validators.py` - Funciones de validación (token format, user_id, etc.)

## Flujo de Datos

### Flujo de Comando Admin

```
1. Admin envía /admin
   └→ Handler recibe Update

2. Dispatcher procesa update
   ├→ AdminAuthMiddleware valida permisos
   ├→ DatabaseMiddleware inyecta session
   └→ Dispatcher routea a handler

3. Handler procesa comando
   ├→ Consulta datos con session
   ├→ Llama servicios si es necesario
   ├→ Responde con keyboard inline
   └→ Transición de estado FSM

4. Usuario hace click en botón
   └→ CallbackQuery enviado

5. CallbackHandler procesa callback
   ├→ Valida acción
   ├→ Actualiza BD
   └→ Responde usuario
```

### Flujo de Creación de Token

```
Sequence: Admin → Bot → Database → Telegram API

1. Admin: /admin → "Generar Token"
   │
2. Bot: ¿Token para 24h? [Si] [No] [Cancelar]
   │
3. Admin: Presiona [Si]
   │
4. Bot:
   ├→ Generar token único (16 caracteres)
   ├→ Insertar en BD: InvitationToken
   └→ Responder: "Token: ABC123XYZ456 - Válido por 24h"
```

### Flujo de Canje de Token

```
Sequence: Usuario → Bot → Database → VIP Channel

1. Usuario: /vip
   │
2. Bot: "Ingresa tu token VIP:"
   │ [FSM: waiting_for_token]
   │
3. Usuario: "ABC123XYZ456"
   │
4. Bot:
   ├→ Buscar token en BD
   ├→ Validar: no usado, no expirado
   ├→ Si válido:
   │  ├→ Crear VIPSubscriber
   │  ├→ Marcar token como usado
   │  ├→ Invitar usuario a canal VIP
   │  └→ "Bienvenido! Acceso VIP válido por 24h"
   └→ Si inválido:
      └→ "Token inválido o expirado"
```

### Flujo de Solicitud Free

```
Sequence: Usuario → Bot → Database → Queue → Timer → Invite

1. Usuario: /free
   │
2. Bot:
   ├→ Crear FreeChannelRequest
   ├→ Iniciar timer (DEFAULT_WAIT_TIME_MINUTES)
   └→ "Esperando... [5 minutos]"

3. [Background Task: Cada 5 minutos]
   ├→ Buscar requests "ready"
   ├→ Invitar usuarios a Free channel
   ├→ Marcar como processed
   └→ Log: "Usuario X invitado a Free"
```

## Modelos de Datos

### Diagrama Entidad-Relación

```
┌──────────────────────────┐
│     BotConfig (1)        │
│──────────────────────────│
│ id: int (1)              │
│ vip_channel_id: str      │
│ free_channel_id: str     │
│ wait_time_minutes: int   │
│ vip_reactions: JSON      │
│ free_reactions: JSON     │
│ subscription_fees: JSON  │
│ created_at: datetime     │
│ updated_at: datetime     │
└──────────────────────────┘

┌──────────────────────────┐       1:N       ┌────────────────────┐
│  InvitationToken         │◄──────────────┼─│  VIPSubscriber     │
│──────────────────────────│                 │────────────────────│
│ id: int (PK)             │                 │ id: int (PK)       │
│ token: str (UNIQUE)      │                 │ user_id: int (UQ)  │
│ generated_by: int        │                 │ join_date: dt      │
│ created_at: datetime     │                 │ expiry_date: dt    │
│ duration_hours: int      │                 │ status: str        │
│ used: bool               │                 │ token_id: int (FK) │
│ used_by: int (null)      │                 └────────────────────┘
│ used_at: datetime (null) │
└──────────────────────────┘

┌────────────────────────────────────┐
│    FreeChannelRequest              │
│────────────────────────────────────│
│ id: int (PK)                       │
│ user_id: int                       │
│ request_date: datetime             │
│ processed: bool                    │
│ processed_at: datetime (null)      │
└────────────────────────────────────┘
```

### Índices Implementados

Para optimizar queries comunes:

```sql
-- InvitationToken
CREATE INDEX idx_token_used_created
ON invitation_tokens(used, created_at);

-- VIPSubscriber
CREATE INDEX idx_status_expiry
ON vip_subscribers(status, expiry_date);

-- FreeChannelRequest
CREATE INDEX idx_user_date
ON free_channel_requests(user_id, request_date);

CREATE INDEX idx_processed_date
ON free_channel_requests(processed, request_date);
```

## Patrones de Arquitectura

### 1. Dependency Injection

Los handlers reciben dependencias inyectadas vía middlewares:

```python
async def handler(message: Message, session: AsyncSession):
    # session inyectada por DatabaseMiddleware
    pass
```

### 2. Service Layer

La lógica de negocio reside en servicios, no en handlers:

```python
# Handler: Orquesta y responde
async def handler(message: Message, session: AsyncSession):
    service = TokenService(session)
    token = await service.generate_token(24)
    await message.answer(f"Token: {token}")

# Service: Implementa lógica
class TokenService:
    async def generate_token(self, duration_hours: int) -> str:
        # Lógica de generación
        pass
```

### 3. Repository Pattern (planeado)

Para aislar lógica de acceso a datos:

```python
class TokenRepository:
    async def find_by_token(self, token: str) -> InvitationToken:
        pass

    async def find_valid_tokens(self) -> List[InvitationToken]:
        pass
```

### 4. Context Managers

Para garantizar limpieza de recursos:

```python
async with get_session() as session:
    # Auto-commit si éxito
    # Auto-rollback si error
    # Auto-close al salir
```

## Flujo de Inicialización

```
main.py
├─ Config.setup_logging()
│  └─ Configura logging según LOG_LEVEL
│
├─ asyncio.run(main())
│  ├─ Bot(token, parse_mode="HTML")
│  ├─ MemoryStorage()
│  ├─ Dispatcher(storage)
│  │
│  ├─ on_startup()
│  │  ├─ Config.validate()
│  │  ├─ init_db()
│  │  │  ├─ create_async_engine()
│  │  │  ├─ PRAGMA journal_mode=WAL
│  │  │  ├─ create_all(Base.metadata)
│  │  │  ├─ async_sessionmaker()
│  │  │  └─ _ensure_bot_config_exists()
│  │  ├─ register_handlers()
│  │  ├─ register_middlewares()
│  │  └─ notify_admins("Bot online")
│  │
│  ├─ dp.start_polling()
│  │  └─ [Loop: Procesar updates]
│  │
│  └─ on_shutdown()
│     ├─ stop_background_tasks()
│     ├─ close_db()
│     └─ notify_admins("Bot offline")
```

## Consideraciones de Rendimiento

### Para Termux (Android)

1. **MemoryStorage vs RedisStorage** - MemoryStorage es ligero pero se pierde al reiniciar
2. **Polling vs Webhook** - Polling es más simple pero consume más energía
3. **Database Connection Pool** - NullPool para SQLite (sin pooling)
4. **Logging Level** - INFO en producción, DEBUG solo en desarrollo
5. **Task Scheduling** - APScheduler con intervalos razonables (no < 5 min)

## Seguridad

### 1. Autenticación

- Validación de ADMIN_USER_IDS en config.py
- AdminAuthMiddleware valida permisos antes de handlers
- Control de acceso basado en roles (admin/no admin)
- Mensajes de error personalizados para accesos denegados
- Logging de intentos de acceso no autorizados

### 2. Base de Datos

- Foreign keys habilitadas
- SQLite con WAL mode para integridad
- Índices en columnas sensibles (user_id, status)
- Context managers para manejo automático de transacciones
- Commit automático en operaciones exitosas
- Rollback automático en caso de errores

### 3. Tokens

- 16 caracteres alfanuméricos (192 bits de entropía)
- Duración limitada (expiran después de X horas)
- Marca de "usado" previene reutilización
- Validación doble: no expirado + no usado

### 4. Secretos

- BOT_TOKEN en .env (NO commitear)
- Logging con preview de token (primeros 10 caracteres)
- Protección contra filtrado accidental de credenciales

## Escalabilidad Futura

### ONDA 2+

1. **Servicios Microservicios** - Separar en múltiples bots
2. **Redis Cache** - Cache de sesiones y config
3. **Webhook Updates** - Reemplazar polling
4. **PostgreSQL** - Reemplazar SQLite para múltiples conexiones
5. **Container + Kubernetes** - Deploy en producción

## Ejemplos de Implementación

### Ejemplos de uso de Middlewares

#### Aplicación de AdminAuthMiddleware

```python
# En handlers/admin/main.py
from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.admin_auth import AdminAuthMiddleware

admin_router = Router()
admin_router.message.middleware(AdminAuthMiddleware())

@admin_router.message(Command("admin_panel"))
async def admin_panel_handler(message: Message, session: AsyncSession):
    """Handler protegido por middleware de autenticación."""
    await message.answer("_PANEL DE ADMINISTRADOR_\n\n"
                        "Selecciona una opción:",
                        parse_mode="HTML")
```

#### Aplicación de DatabaseMiddleware

```python
# En main.py
from bot.middlewares.database import DatabaseMiddleware

# Aplicar a nivel global para que todos los handlers tengan acceso a la BD
dp.update.middleware(DatabaseMiddleware())

# En cualquier handler
async def user_info_handler(message: Message, session: AsyncSession):
    """Handler que recibe la sesión automáticamente."""
    # La sesión está disponible gracias al middleware
    user_id = message.from_user.id

    # Ejemplo de consulta a la base de datos
    result = await session.execute(
        select(VIPSubscriber)
        .where(VIPSubscriber.user_id == user_id)
        .where(VIPSubscriber.status == "active")
    )
    subscriber = result.scalar_one_or_none()

    if subscriber:
        days_left = subscriber.days_remaining()
        await message.answer(f"Suscripción VIP activa. Días restantes: {days_left}")
    else:
        await message.answer("No tienes suscripción VIP activa.")
```

#### Uso combinado de ambos middlewares

```python
# Router específico para comandos de administrador
admin_router = Router()

# Aplicar middleware de autenticación a nivel de router
admin_router.message.middleware(AdminAuthMiddleware())
admin_router.callback_query.middleware(AdminAuthMiddleware())

# La inyección de sesión se hace a nivel global con DatabaseMiddleware
# aplicado en el dispatcher

@admin_router.message(Command("generate_token"))
async def generate_token_handler(message: Message, session: AsyncSession):
    """
    Handler que requiere:
    1. Permisos de administrador (verificado por AdminAuthMiddleware)
    2. Acceso a la base de datos (inyectado por DatabaseMiddleware)
    """
    # Solo se llega aquí si el usuario es admin
    # La sesión está disponible automáticamente

    container = ServiceContainer(session, bot_instance)

    try:
        # Generar token usando el servicio de suscripciones
        token = await container.subscription.generate_vip_token(
            generated_by=message.from_user.id,
            duration_hours=24
        )

        await message.answer(
            f"✅ Token VIP generado:\n\n"
            f"<code>{token.token}</code>\n\n"
            f"Válido por 24 horas.\n"
            f"Generado por: {message.from_user.full_name}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error generando token: {e}")
        await message.answer("❌ Error al generar token. Intenta nuevamente.")

# Aplicar middleware global de base de datos en el dispatcher
dp.update.middleware(DatabaseMiddleware())

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
