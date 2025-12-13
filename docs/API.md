# Integración con la API de Telegram

Documentación técnica sobre cómo el bot interactúa con la API de Telegram, incluyendo los handlers VIP y Free.

## API de Telegram

### Configuración Básica

El bot se comunica con la API de Telegram a través del framework Aiogram 3, usando el siguiente esquema:

```python
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)
```

## Handlers VIP y Free

### Handler de Menú VIP (`/admin` → `admin:vip`)

#### Callback Query: `admin:vip`

**Descripción:** Muestra el submenú de gestión VIP.

**Flujo de ejecución:**
1. Usuario admin selecciona "Gestión Canal VIP" en el menú principal
2. Bot recibe callback `admin:vip`
3. Bot verifica configuración del canal VIP
4. Bot envía mensaje con información del canal y opciones disponibles
5. Bot actualiza el mensaje existente con teclado VIP

**Implementación:**
```python
@admin_router.callback_query(F.data == "admin:vip")
async def callback_vip_menu(callback: CallbackQuery, session: AsyncSession):
    # Verificar si canal VIP está configurado
    is_configured = await container.channel.is_vip_channel_configured()
    
    # Construir mensaje según estado
    if is_configured:
        text = f"📺 <b>Gestión Canal VIP</b>\n\n✅ Canal configurado: <b>{channel_name}</b>..."
    else:
        text = "📺 <b>Gestión Canal VIP</b>\n\n⚠️ Canal VIP no configurado..."
    
    # Enviar mensaje con teclado VIP
    await callback.message.edit_text(
        text=text,
        reply_markup=vip_menu_keyboard(is_configured),
        parse_mode="HTML"
    )
```

**API Calls:**
- `callback.message.edit_text()` - Edita el mensaje existente con nuevo contenido
- `container.channel.is_vip_channel_configured()` - Consulta BD para verificar configuración
- `container.channel.get_vip_channel_id()` - Obtiene ID del canal VIP de la BD
- `container.channel.get_channel_info()` - Obtiene información del canal de la API de Telegram

### Configuración de Canal VIP

#### Callback Query: `vip:setup`

**Descripción:** Inicia el proceso de configuración del canal VIP.

**Flujo de ejecución:**
1. Usuario admin selecciona "⚙️ Configurar Canal VIP"
2. Bot recibe callback `vip:setup`
3. Bot entra en estado FSM `waiting_for_vip_channel`
4. Bot envía instrucciones para reenviar mensaje del canal
5. Bot espera mensaje reenviado

**Implementación:**
```python
@admin_router.callback_query(F.data == "vip:setup")
async def callback_vip_setup(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    # Entrar en estado FSM
    await state.set_state(ChannelSetupStates.waiting_for_vip_channel)
    
    text = (
        "⚙️ <b>Configurar Canal VIP</b>\n\n"
        "Para configurar el canal VIP, necesito que:\n\n"
        "1️⃣ Vayas al canal VIP\n"
        "2️⃣ Reenvíes cualquier mensaje del canal a este chat\n"
        "3️⃣ Yo extraeré el ID automáticamente\n\n"
        "⚠️ <b>Importante:</b>\n"
        "- El bot debe ser administrador del canal\n"
        "- El bot debe tener permiso para invitar usuarios\n\n"
        "👉 Reenvía un mensaje del canal ahora..."
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:vip"}]
        ]),
        parse_mode="HTML"
    )
```

**API Calls:**
- `state.set_state()` - Establece el estado FSM para esperar mensaje reenviado
- `callback.message.edit_text()` - Edita mensaje con instrucciones

#### Message Handler: `ChannelSetupStates.waiting_for_vip_channel`

**Descripción:** Procesa el mensaje reenviado para configurar el canal VIP.

**Flujo de ejecución:**
1. Usuario reenvía mensaje del canal VIP al bot
2. Bot recibe mensaje mientras está en estado `waiting_for_vip_channel`
3. Bot verifica que sea un reenvío de canal
4. Bot extrae ID del canal del mensaje reenviado
5. Bot configura el canal VIP
6. Bot sale del estado FSM

**Implementación:**
```python
@admin_router.message(ChannelSetupStates.waiting_for_vip_channel)
async def process_vip_channel_forward(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    # Verificar que es un forward de un canal
    if not message.forward_from_chat:
        await message.answer(
            "❌ Debes <b>reenviar</b> un mensaje del canal VIP...",
            parse_mode="HTML"
        )
        return
    
    forward_chat = message.forward_from_chat
    
    # Verificar que es un canal
    if forward_chat.type not in ["channel", "supergroup"]:
        await message.answer(
            "❌ El mensaje debe ser de un <b>canal</b>...",
            parse_mode="HTML"
        )
        return
    
    channel_id = str(forward_chat.id)
    
    # Configurar canal VIP
    container = ServiceContainer(session, message.bot)
    success, msg = await container.channel.setup_vip_channel(channel_id)
    
    if success:
        await message.answer(
            f"✅ <b>Canal VIP Configurado</b>...",
            parse_mode="HTML",
            reply_markup=vip_menu_keyboard(True)
        )
        await state.clear()
    else:
        await message.answer(f"{msg}...", parse_mode="HTML")
```

**API Calls:**
- `message.forward_from_chat` - Accede a la información del canal reenviado
- `message.answer()` - Envía mensaje de respuesta al usuario
- `state.clear()` - Limpia el estado FSM
- `container.channel.setup_vip_channel()` - Configura el canal en la BD y verifica permisos

### Generación de Tokens VIP

#### Callback Query: `vip:generate_token`

**Descripción:** Genera un token de invitación VIP.

**Flujo de ejecución:**
1. Usuario admin selecciona "🎟️ Generar Token de Invitación"
2. Bot recibe callback `vip:generate_token`
3. Bot verifica que canal VIP esté configurado
4. Bot genera token único con duración configurable
5. Bot envía token al administrador

**Implementación:**
```python
@admin_router.callback_query(F.data == "vip:generate_token")
async def callback_generate_vip_token(
    callback: CallbackQuery,
    session: AsyncSession
):
    container = ServiceContainer(session, callback.bot)
    
    # Verificar que canal VIP está configurado
    if not await container.channel.is_vip_channel_configured():
        await callback.answer(
            "❌ Debes configurar el canal VIP primero",
            show_alert=True
        )
        return
    
    # Generar token
    token = await container.subscription.generate_vip_token(
        generated_by=callback.from_user.id,
        duration_hours=Config.DEFAULT_TOKEN_DURATION_HOURS
    )
    
    # Enviar token al admin
    token_message = (
        f"🎟️ <b>Token VIP Generado</b>\n\n"
        f"Token: <code>{token.token}</code>\n\n"
        f"⏱️ Válido por: {token.duration_hours} horas\n"
        f"📅 Expira: {token.created_at.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        f"👉 Comparte este token con el usuario."
    )
    
    await callback.message.answer(
        text=token_message,
        parse_mode="HTML"
    )
```

**API Calls:**
- `callback.answer()` - Responde al callback (con alerta si error)
- `callback.message.answer()` - Envía mensaje con token generado
- `container.subscription.generate_vip_token()` - Genera token en la BD

## Handlers Free

### Handler de Menú Free (`/admin` → `admin:free`)

#### Callback Query: `admin:free`

**Descripción:** Muestra el submenú de gestión Free.

**Flujo de ejecución:**
1. Usuario admin selecciona "Gestión Canal Free" en el menú principal
2. Bot recibe callback `admin:free`
3. Bot verifica configuración del canal Free y tiempo de espera
4. Bot envía mensaje con información del canal y tiempo de espera
5. Bot actualiza el mensaje existente con teclado Free

**Implementación:**
```python
@admin_router.callback_query(F.data == "admin:free")
async def callback_free_menu(callback: CallbackQuery, session: AsyncSession):
    container = ServiceContainer(session, callback.bot)
    
    # Verificar si canal Free está configurado
    is_configured = await container.channel.is_free_channel_configured()
    wait_time = await container.config.get_wait_time()
    
    # Construir mensaje según estado
    if is_configured:
        text = f"📺 <b>Gestión Canal Free</b>\n\n✅ Canal configurado: <b>{channel_name}</b>..."
    else:
        text = "📺 <b>Gestión Canal Free</b>\n\n⚠️ Canal Free no configurado..."
    
    await callback.message.edit_text(
        text=text,
        reply_markup=free_menu_keyboard(is_configured),
        parse_mode="HTML"
    )
```

### Configuración de Canal Free

#### Callback Query: `free:setup`

**Descripción:** Inicia el proceso de configuración del canal Free.

**Flujo de ejecución:**
1. Usuario admin selecciona "⚙️ Configurar Canal Free"
2. Bot recibe callback `free:setup`
3. Bot entra en estado FSM `waiting_for_free_channel`
4. Bot envía instrucciones para reenviar mensaje del canal
5. Bot espera mensaje reenviado

**Implementación similar a VIP setup pero con estado `waiting_for_free_channel`.**

#### Message Handler: `ChannelSetupStates.waiting_for_free_channel`

**Descripción:** Procesa el mensaje reenviado para configurar el canal Free.

**API Calls y flujo similar a la configuración de canal VIP, pero configurando el canal Free.**

### Configuración de Tiempo de Espera

#### Callback Query: `free:set_wait_time`

**Descripción:** Inicia configuración de tiempo de espera para acceso Free.

**Flujo de ejecución:**
1. Usuario admin selecciona "⏱️ Configurar Tiempo de Espera"
2. Bot recibe callback `free:set_wait_time`
3. Bot entra en estado FSM `waiting_for_minutes`
4. Bot solicita ingresar nuevo tiempo en minutos
5. Bot espera mensaje con número de minutos

**Implementación:**
```python
@admin_router.callback_query(F.data == "free:set_wait_time")
async def callback_set_wait_time(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
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
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:free"}]
        ]),
        parse_mode="HTML"
    )
```

**API Calls:**
- `state.set_state()` - Establece estado FSM para esperar minutos
- `container.config.get_wait_time()` - Obtiene tiempo actual de la BD
- `callback.message.edit_text()` - Edita mensaje con instrucciones

#### Message Handler: `WaitTimeSetupStates.waiting_for_minutes`

**Descripción:** Procesa el input de tiempo de espera.

**Flujo de ejecución:**
1. Usuario envía número de minutos
2. Bot recibe mensaje mientras está en estado `waiting_for_minutes`
3. Bot convierte texto a número
4. Bot valida rango (mínimo 1 minuto)
5. Bot actualiza configuración de tiempo de espera
6. Bot sale del estado FSM

**Implementación:**
```python
@admin_router.message(WaitTimeSetupStates.waiting_for_minutes)
async def process_wait_time_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    # Intentar convertir a número
    try:
        minutes = int(message.text)
    except ValueError:
        await message.answer(
            "❌ Debes enviar un número válido...",
            parse_mode="HTML"
        )
        return
    
    # Validar rango
    if minutes < 1:
        await message.answer(
            "❌ El tiempo debe ser al menos 1 minuto...",
            parse_mode="HTML"
        )
        return
    
    container = ServiceContainer(session, message.bot)
    
    # Actualizar configuración
    await container.config.set_wait_time(minutes)
    
    await message.answer(
        f"✅ <b>Tiempo de Espera Actualizado</b>...",
        parse_mode="HTML",
        reply_markup=free_menu_keyboard(True)
    )
    
    # Limpiar estado
    await state.clear()
```

**API Calls:**
- `message.text` - Accede al texto del mensaje
- `message.answer()` - Envía confirmación de actualización
- `container.config.set_wait_time()` - Actualiza tiempo en la BD
- `state.clear()` - Limpia el estado FSM

## Manejo de Errores y Excepciones

### Manejo de Edición de Mensajes

Para evitar errores de "message is not modified" al editar mensajes:

```python
try:
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
except Exception as e:
    if "message is not modified" not in str(e):
        logger.error(f"Error editando mensaje: {e}")
    else:
        logger.debug("ℹ️ Mensaje sin cambios, ignorando")
```

### Manejo de Permisos

Los middlewares verifican permisos antes de ejecutar handlers:

```python
# AdminAuthMiddleware verifica si el usuario es admin
# DatabaseMiddleware inyecta la sesión de base de datos
```

## Interacción con Teclados Inline

### Creación de Teclados

Los teclados se crean usando el factory `create_inline_keyboard()`:

```python
def vip_menu_keyboard(is_configured: bool) -> "InlineKeyboardMarkup":
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

### Callback Data Format

Los callbacks siguen el formato `modulo:accion`:
- `admin:vip` - Ir al menú VIP
- `admin:free` - Ir al menú Free
- `vip:setup` - Configurar canal VIP
- `vip:generate_token` - Generar token VIP
- `free:setup` - Configurar canal Free
- `free:set_wait_time` - Configurar tiempo de espera
- `admin:main` - Volver al menú principal

## Handlers User

### Handler de Menú Principal (`/start`)

#### Message Handler: `/start`

**Descripción:** Handler del comando /start que detecta el rol del usuario y proporciona opciones según su estado.

**Flujo de ejecución:**
1. Usuario envía `/start`
2. Bot detecta rol del usuario (admin, VIP, normal)
3. Si es admin: redirige a panel de administración
4. Si es VIP: muestra mensaje de bienvenida con días restantes
5. Si es usuario normal: muestra menú con opciones VIP/Free

**Implementación:**
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

**API Calls:**
- `message.from_user.id` - Accede al ID del usuario
- `message.from_user.first_name` - Accede al nombre del usuario
- `message.answer()` - Envía mensaje de respuesta al usuario
- `Config.is_admin()` - Verifica si el usuario es administrador
- `container.subscription.is_vip_active()` - Verifica si el usuario tiene suscripción VIP activa
- `container.subscription.get_vip_subscriber()` - Obtiene información del suscriptor VIP

### Flujo VIP - Canje de Tokens

#### Callback Query: `user:redeem_token`

**Descripción:** Inicia el flujo de canje de token VIP.

**Flujo de ejecución:**
1. Usuario selecciona "Canjear Token VIP"
2. Bot recibe callback `user:redeem_token`
3. Bot verifica que canal VIP esté configurado
4. Bot entra en estado FSM `waiting_for_token`
5. Bot solicita ingresar token de invitación

**Implementación:**
```python
@user_router.callback_query(F.data == "user:redeem_token")
async def callback_redeem_token(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el flujo de canje de token VIP.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    user_id = callback.from_user.id

    # Verificar que canal VIP está configurado
    container = ServiceContainer(session, callback.bot)

    if not await container.channel.is_vip_channel_configured():
        await callback.answer(
            "⚠️ Canal VIP no está configurado. Contacta al administrador.",
            show_alert=True
        )
        return

    # Entrar en estado FSM
    await state.set_state(TokenRedemptionStates.waiting_for_token)

    try:
        await callback.message.edit_text(
            "🎟️ <b>Canjear Token VIP</b>\n\n"
            "Por favor, envía tu token de invitación.\n\n"
            "El token tiene este formato:\n"
            "<code>A1b2C3d4E5f6G7h8</code>\n\n"
            "👉 Copia y pega tu token aquí:",
            reply_markup=create_inline_keyboard([
                [{"text": "❌ Cancelar", "callback_data": "user:cancel"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje: {e}")

    await callback.answer()
```

**API Calls:**
- `callback.from_user.id` - Accede al ID del usuario
- `callback.answer()` - Responde al callback
- `callback.message.edit_text()` - Edita mensaje existente con instrucciones
- `state.set_state()` - Establece estado FSM para esperar token
- `container.channel.is_vip_channel_configured()` - Verifica configuración del canal VIP

#### Message Handler: `TokenRedemptionStates.waiting_for_token`

**Descripción:** Procesa el token enviado por el usuario.

**Flujo de ejecución:**
1. Usuario envía token
2. Bot recibe mensaje mientras está en estado `waiting_for_token`
3. Bot valida token (formato, vigencia, no usado)
4. Bot canjea token y genera invite link
5. Bot envía link de acceso al usuario
6. Bot sale del estado FSM

**Implementación:**
```python
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

**API Calls:**
- `message.text` - Accede al texto del mensaje (token)
- `message.answer()` - Envía respuesta con link de acceso
- `state.clear()` - Limpia el estado FSM
- `container.subscription.redeem_vip_token()` - Canjea token en la BD
- `container.channel.get_vip_channel_id()` - Obtiene ID del canal VIP
- `container.subscription.create_invite_link()` - Crea link de invitación único

### Flujo Free - Solicitud de Acceso

#### Callback Query: `user:request_free`

**Descripción:** Procesa solicitud de acceso al canal Free.

**Flujo de ejecución:**
1. Usuario selecciona "Solicitar Acceso Free"
2. Bot recibe callback `user:request_free`
3. Bot verifica que canal Free esté configurado
4. Bot verifica si usuario ya tiene solicitud pendiente
5. Si no tiene solicitud: crea nueva solicitud y notifica tiempo de espera
6. Si ya tiene solicitud: muestra tiempo restante

**Implementación:**
```python
@user_router.callback_query(F.data == "user:request_free")
async def callback_request_free(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Procesa solicitud de acceso al canal Free.

    Crea la solicitud y notifica al usuario del tiempo de espera.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id

    container = ServiceContainer(session, callback.bot)

    # Verificar que canal Free está configurado
    if not await container.channel.is_free_channel_configured():
        await callback.answer(
            "⚠️ Canal Free no está configurado. Contacta al administrador.",
            show_alert=True
        )
        return

    # Verificar si ya tiene solicitud pendiente
    existing_request = await container.subscription.get_free_request(user_id)

    if existing_request:
        # Calcular tiempo restante
        from datetime import datetime, timezone, timedelta

        wait_time_minutes = await container.config.get_wait_time()
        time_since_request = (datetime.now(timezone.utc) - existing_request.request_date).total_seconds() / 60
        minutes_remaining = max(0, int(wait_time_minutes - time_since_request))

        try:
            await callback.message.edit_text(
                f"⏱️ <b>Solicitud Pendiente</b>\n\n"
                f"Ya tienes una solicitud en proceso.\n\n"
                f"Tiempo transcurrido: <b>{int(time_since_request)} minutos</b>\n"
                f"Tiempo restante: <b>{minutes_remaining} minutos</b>\n\n"
                f"Recibirás el link de acceso automáticamente cuando el tiempo se cumpla.\n\n"
                f"💡 <i>Puedes cerrar este chat, te notificaré cuando esté listo.</i>",
                parse_mode="HTML"
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                logger.error(f"Error editando mensaje: {e}")

        await callback.answer()
        return

    # Crear nueva solicitud
    request = await container.subscription.create_free_request(user_id)
    wait_time = await container.config.get_wait_time()

    try:
        await callback.message.edit_text(
            f"✅ <b>Solicitud Recibida</b>\n\n"
            f"Tu solicitud de acceso al canal Free ha sido registrada.\n\n"
            f"⏱️ Tiempo de espera: <b>{wait_time} minutos</b>\n\n"
            f"📨 Recibirás un mensaje con el link de invitación cuando el tiempo se cumpla.\n\n"
            f"💡 <i>No necesitas hacer nada más, el proceso es automático.</i>\n\n"
            f"Puedes cerrar este chat, te notificaré cuando esté listo! 🔔",
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje: {e}")

    await callback.answer("✅ Solicitud creada")
```

**API Calls:**
- `callback.from_user.id` - Accede al ID del usuario
- `callback.answer()` - Responde al callback
- `callback.message.edit_text()` - Edita mensaje existente con información de solicitud
- `container.channel.is_free_channel_configured()` - Verifica configuración del canal Free
- `container.subscription.get_free_request()` - Obtiene solicitud pendiente del usuario
- `container.subscription.create_free_request()` - Crea nueva solicitud en la BD
- `container.config.get_wait_time()` - Obtiene tiempo de espera configurado

### Cancelación de Flujos

#### Callback Query: `user:cancel`

**Descripción:** Cancela el flujo actual y limpia estado FSM.

**Flujo de ejecución:**
1. Usuario selecciona opción de cancelar
2. Bot recibe callback `user:cancel`
3. Bot limpia estado FSM
4. Bot envía mensaje de confirmación

**Implementación:**
```python
@user_router.callback_query(F.data == "user:cancel")
async def callback_cancel(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Cancela el flujo actual y limpia estado FSM.

    Args:
        callback: Callback query
        state: FSM context
    """
    await state.clear()

    try:
        await callback.message.edit_text(
            "❌ Operación cancelada.\n\n"
            "Usa /start para volver al menú principal.",
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje: {e}")

    await callback.answer()
```

**API Calls:**
- `state.clear()` - Limpia el estado FSM
- `callback.message.edit_text()` - Edita mensaje con confirmación de cancelación
- `callback.answer()` - Responde al callback

## Validaciones y Seguridad

### Validación de Reenvíos

Para asegurar que los mensajes son reenvíos de canales válidos:

```python
if not message.forward_from_chat:
    # No es un reenvío, solicitar reenvío
    return

if forward_chat.type not in ["channel", "supergroup"]:
    # No es un canal válido, solicitar canal
    return
```

### Validación de Números

Para asegurar que los tiempos de espera son válidos:

```python
try:
    minutes = int(message.text)
except ValueError:
    # No es un número, solicitar número válido
    return

if minutes < 1:
    # Valor no válido, solicitar valor >= 1
    return
```

### Validación de Tokens

Para asegurar que los tokens son válidos antes de canjear:

```python
success, msg, subscriber = await container.subscription.redeem_vip_token(
    token_str=token_str,
    user_id=user_id
)

if not success:
    # Token inválido, notificar al usuario
    await message.answer(f"{msg}...")
    return
```

### Validación de Configuración

Para asegurar que los canales están configurados antes de procesar solicitudes:

```python
if not await container.channel.is_vip_channel_configured():
    await callback.answer(
        "⚠️ Canal VIP no está configurado. Contacta al administrador.",
        show_alert=True
    )
    return

if not await container.channel.is_free_channel_configured():
    await callback.answer(
        "⚠️ Canal Free no está configurado. Contacta al administrador.",
        show_alert=True
    )
    return
```

## Integración con APScheduler

El bot utiliza APScheduler para ejecutar tareas programadas que realizan operaciones periódicas para mantener el sistema funcionando correctamente.

### Configuración del Scheduler

**Inicialización:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

_scheduler: Optional[AsyncIOScheduler] = None
```

**Iniciar tareas programadas:**
```python
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
```

**Detener tareas programadas:**
```python
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

### Tareas Programadas

#### Tarea: Expulsión de VIPs expirados

**Descripción:** Marca como expirados y expulsa del canal a los suscriptores VIP cuya fecha pasó.

**Frecuencia:** Cada 60 minutos (configurable con `CLEANUP_INTERVAL_MINUTES`)

**Flujo de ejecución:**
1. Se ejecuta la función `expire_and_kick_vip_subscribers(bot)`
2. Verifica si canal VIP está configurado
3. Busca suscriptores VIP con fecha de expiración anterior a la actual
4. Marca como expirados en la base de datos
5. Expulsa del canal VIP usando la API de Telegram
6. Registra en logs el número de usuarios expulsados

**API Calls:**
- `container.subscription.expire_vip_subscribers()` - Marca suscriptores como expirados
- `container.subscription.kick_expired_vip_from_channel()` - Expulsa usuarios del canal
- `container.channel.get_vip_channel_id()` - Obtiene ID del canal VIP

#### Tarea: Procesamiento de cola Free

**Descripción:** Busca solicitudes que cumplieron el tiempo de espera y envía invite links a los usuarios.

**Frecuencia:** Cada 5 minutos (configurable con `PROCESS_FREE_QUEUE_MINUTES`)

**Flujo de ejecución:**
1. Se ejecuta la función `process_free_queue(bot)`
2. Verifica si canal Free está configurado
3. Busca solicitudes Free que cumplen el tiempo de espera configurado
4. Para cada solicitud:
   - Marca como procesada
   - Crea invite link único (válido 24 horas, un solo uso)
   - Envía link al usuario por mensaje privado
5. Registra en logs el número de solicitudes procesadas

**API Calls:**
- `container.subscription.process_free_queue()` - Procesa solicitudes pendientes
- `container.subscription.create_invite_link()` - Crea link de invitación único
- `container.channel.get_free_channel_id()` - Obtiene ID del canal Free
- `bot.send_message()` - Envía mensaje privado al usuario

#### Tarea: Limpieza de datos antiguos

**Descripción:** Elimina solicitudes Free procesadas hace más de 30 días.

**Frecuencia:** Diariamente a las 3 AM UTC

**Flujo de ejecución:**
1. Se ejecuta la función `cleanup_old_data(bot)`
2. Busca solicitudes Free procesadas hace más de 30 días
3. Elimina los registros antiguos de la base de datos
4. Registra en logs el número de registros eliminados

**API Calls:**
- `container.subscription.cleanup_old_free_requests()` - Elimina solicitudes antiguas

### Variables de Entorno para Configuración

- `CLEANUP_INTERVAL_MINUTES`: Intervalo para expulsión de VIPs expirados (default: 60)
- `PROCESS_FREE_QUEUE_MINUTES`: Intervalo para procesamiento de cola Free (default: 5)

### Manejo de Errores en Tareas

Cada tarea está envuelta en try-catch para evitar interrupciones:

```python
async def expire_and_kick_vip_subscribers(bot: Bot):
    logger.info("🔄 Ejecutando tarea: Expulsión VIP expirados")

    try:
        # Procesamiento de la tarea
        async with get_session() as session:
            container = ServiceContainer(session, bot)
            # ... lógica de la tarea
    except Exception as e:
        logger.error(f"❌ Error en tarea de expulsión VIP: {e}", exc_info=True)
```

### Monitoreo del Scheduler

**Obtener estado del scheduler:**
```python
def get_scheduler_status() -> dict:
    """
    Obtiene el estado actual del scheduler.

    Returns:
        Dict con información del scheduler:
        {
            "running": bool,
            "jobs_count": int,
            "jobs": List[dict]
        }
    """
    if _scheduler is None:
        return {
            "running": False,
            "jobs_count": 0,
            "jobs": []
        }

    jobs_info = []
    for job in _scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        "running": True,
        "jobs_count": len(jobs_info),
        "jobs": jobs_info
    }
```

## Flujo Completo de Configuración

### Configuración de Canal por Reenvío

1. Admin selecciona opción de configuración
2. Bot entra en estado FSM correspondiente
3. Bot solicita reenvío de mensaje del canal
4. Admin reenvía mensaje del canal objetivo
5. Bot extrae ID del canal del mensaje reenviado
6. Bot verifica permisos del bot en el canal
7. Bot guarda configuración si todo es válido
8. Bot limpia estado FSM y actualiza menú

### Generación de Tokens

1. Admin selecciona "Generar Token"
2. Bot verifica que canal VIP esté configurado
3. Bot genera token único con duración configurable
4. Bot guarda token en BD
5. Bot envía token al admin

## Sistema de Paginación (T24, T25, T26)

### Integración con la API de Telegram

El sistema de paginación se integra con la API de Telegram a través de los siguientes endpoints:

- `editMessageText` - Para actualizar el contenido de los mensajes paginados cuando el usuario navega entre páginas
- `answerCallbackQuery` - Para responder a las queries de callback que representan las acciones de paginación (anterior/siguiente)
- `createInlineKeyboardMarkup` - Para generar teclados inline con botones de navegación paginada

### Componentes del Sistema de Paginación

#### Clase Paginator

**Responsabilidad:** Sistema de paginación reutilizable para listas largas de elementos.

**Características:**
- Clase genérica que soporta cualquier tipo de datos (T)
- Cálculo automático de páginas, elementos por página y rangos
- Validación de números de página
- Métodos para obtener primera y última página

**API Integration:**
```python
# Uso en handlers para paginar resultados de consultas
page = paginate_query_results(
    results=list(subscribers),
    page_number=page_number,
    page_size=10
)
```

#### Función create_pagination_keyboard

**Responsabilidad:** Creación de teclado inline con botones de navegación paginada.

**Características:**
- Botones "Anterior" y "Siguiente" según disponibilidad
- Visualización del número de página actual
- Callback patterns configurables
- Botón de retorno personalizable

**API Integration:**
```python
keyboard = create_pagination_keyboard(
    page=page,
    callback_pattern=f"vip:subscribers:page:{{page}}:{filter_status}",
    additional_buttons=additional_buttons,
    back_callback="admin:vip"
)

await callback.message.edit_text(
    text=text,
    reply_markup=keyboard,
    parse_mode="HTML"
)
```

#### Función format_page_header

**Responsabilidad:** Formateo de headers para páginas paginadas.

**Características:**
- Visualización de total de elementos
- Mostrar rango de elementos visibles
- Formato HTML para mensajes de Telegram

**API Integration:**
```python
header = format_page_header(page, f"Suscriptores VIP - {filter_name}")
await callback.message.edit_text(text=f"{header}\n\n{items_text}", ...)
```

#### Función format_items_list

**Responsabilidad:** Formateo de listas de elementos con formatters personalizados.

**Características:**
- Formateadores personalizables para diferentes tipos de elementos
- Numeración automática
- Separadores personalizables

**API Integration:**
```python
items_text = format_items_list(page.items, _format_vip_subscriber)
await callback.message.edit_text(text=f"{header}\n\n{items_text}", ...)
```

### Paginación de Suscriptores VIP (T25)

#### Callback Query: `vip:list_subscribers`

**Descripción:** Muestra listado paginado de suscriptores VIP.

**Flujo de ejecución:**
1. Admin selecciona "👥 Listar Suscriptores VIP"
2. Bot recibe callback `vip:list_subscribers`
3. Bot muestra la primera página de suscriptores activos
4. Bot envía mensaje con información paginada y teclado de navegación

**API Calls:**
- `callback.message.edit_text()` - Edita mensaje con lista paginada
- `callback.answer()` - Responde al callback de carga
- `create_pagination_keyboard()` - Crea teclado con botones de paginación

**Implementación:**
```python
@admin_router.callback_query(F.data == "vip:list_subscribers")
async def callback_list_vip_subscribers(
    callback: CallbackQuery,
    session: AsyncSession
):
    await callback.answer("📋 Cargando suscriptores...", show_alert=False)

    await _show_vip_subscribers_page(
        callback=callback,
        session=session,
        page_number=1,
        filter_status="active"
    )
```

#### Callback Query: `vip:subscribers:page:{page}:{filter}`

**Descripción:** Navega a una página específica de suscriptores VIP con filtro aplicado.

**Flujo de ejecución:**
1. Admin selecciona botón de página (anterior/siguiente)
2. Bot recibe callback `vip:subscribers:page:N:FILTER`
3. Bot extrae número de página y filtro del callback data
4. Bot muestra la página solicitada con el filtro aplicado

**API Calls:**
- `callback.message.edit_text()` - Edita mensaje con nueva página
- `extract_page_from_callback()` - Extrae número de página del callback

**Implementación:**
```python
@admin_router.callback_query(F.data.startswith("vip:subscribers:page:"))
async def callback_vip_subscribers_page(
    callback: CallbackQuery,
    session: AsyncSession
):
    # Parsear callback data
    parts = callback.data.split(":")
    page_number = int(parts[3])
    filter_status = parts[4] if len(parts) > 4 else "active"

    await _show_vip_subscribers_page(
        callback=callback,
        session=session,
        page_number=page_number,
        filter_status=filter_status
    )
```

#### Callback Query: `vip:filter:{status}`

**Descripción:** Cambia filtro de visualización de suscriptores VIP.

**Flujo de ejecución:**
1. Admin selecciona botón de filtro (activos, expirados, etc.)
2. Bot recibe callback `vip:filter:STATUS`
3. Bot aplica nuevo filtro y muestra primera página
4. Bot actualiza mensaje con nueva visualización

**API Calls:**
- `callback.answer()` - Responde con confirmación de filtro
- `callback.message.edit_text()` - Edita mensaje con nueva visualización

### Visualización de Cola Free (T26)

#### Callback Query: `free:view_queue`

**Descripción:** Muestra cola de solicitudes Free paginada.

**Flujo de ejecución:**
1. Admin selecciona "📋 Ver Cola Free"
2. Bot recibe callback `free:view_queue`
3. Bot muestra la primera página de solicitudes pendientes
4. Bot envía mensaje con información paginada y teclado de navegación

**API Calls:**
- `callback.message.edit_text()` - Edita mensaje con cola paginada
- `callback.answer()` - Responde al callback de carga

#### Callback Query: `free:queue:page:{page}:{filter}`

**Descripción:** Navega a una página específica de la cola Free con filtro aplicado.

**Flujo de ejecución:**
1. Admin selecciona botón de página (anterior/siguiente)
2. Bot recibe callback `free:queue:page:N:FILTER`
3. Bot extrae número de página y filtro del callback data
4. Bot muestra la página solicitada con el filtro aplicado

**API Calls:**
- `callback.message.edit_text()` - Edita mensaje con nueva página
- `extract_page_from_callback()` - Extrae número de página del callback

#### Callback Query: `free:filter:{status}`

**Descripción:** Cambia filtro de visualización de cola Free.

**Flujo de ejecución:**
1. Admin selecciona botón de filtro (pendientes, listas, etc.)
2. Bot recibe callback `free:filter:STATUS`
3. Bot aplica nuevo filtro y muestra primera página
4. Bot actualiza mensaje con nueva visualización

**API Integration Examples:**
```python
# Actualización de mensaje paginado
await callback.message.edit_text(
    text=text,
    reply_markup=keyboard,
    parse_mode="HTML"
)

# Respuesta a query de callback de paginación
await callback.answer("Cargando página...")

# Creación de teclado con botones de paginación
keyboard = create_pagination_keyboard(
    page=page,
    callback_pattern=f"vip:subscribers:page:{{page}}:{filter_status}",
    additional_buttons=additional_buttons,
    back_callback="admin:vip"
)
```

### Filtros Disponibles

#### Filtros para Suscriptores VIP:
- `active` - Solo suscriptores activos
- `expired` - Solo suscriptores expirados
- `expiring_soon` - Suscriptores que expirarán en los próximos 7 días
- `all` - Todos los suscriptores

#### Filtros para Cola Free:
- `pending` - Solo solicitudes pendientes
- `ready` - Solicitudes listas para procesar (cumplen tiempo de espera)
- `processed` - Solicitudes ya procesadas
- `all` - Todas las solicitudes

### Formateadores de Elementos

#### `_format_vip_subscriber`

**Responsabilidad:** Formatea un suscriptor VIP para visualización en listas paginadas.

**Características:**
- Muestra ID de usuario
- Muestra fecha de expiración y días restantes
- Emojis indicadores según estado (activo, próximo a expirar, expirado)

#### `_format_free_request`

**Responsabilidad:** Formatea una solicitud Free para visualización en listas paginadas.

**Características:**
- Muestra ID de usuario
- Muestra fecha de solicitud
- Muestra tiempo restante o estado de procesamiento
- Emojis indicadores según estado (pendiente, listo, procesado)

### Navegación y Estado

El sistema de paginación mantiene el estado de filtro entre páginas, permitiendo al usuario navegar sin perder el contexto de visualización. Los teclados de paginación incluyen botones de filtro para cambiar dinámicamente la vista sin salir del modo paginado.