# Documentación de Handlers

Referencia técnica de handlers de comandos y callbacks. Cubre el flujo de eventos, validaciones y patrones de implementación.

## Estructura de Handlers

Los handlers se organizan en dos categorías principales:

```
bot/handlers/
├── admin/
│   ├── __init__.py         # Exports y registro
│   ├── main.py             # Menú principal /admin (Fase 1.2)
│   ├── vip.py              # Gestión VIP (Fase 1.2)
│   └── free.py             # Gestión Free (Fase 1.2)
└── user/
    ├── __init__.py         # Exports y registro
    ├── start.py            # Comando /start (Fase 1.3)
    ├── vip_flow.py         # Canje de tokens (Fase 1.3)
    └── free_flow.py        # Solicitud Free (Fase 1.3)
```

## Patrones de Handler

### Patrón General

Todos los handlers siguen este patrón:

```python
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from config import Config

router = Router()

@router.message.command("comando")
async def comando_handler(
    message: Message,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """
    Descripción del handler.

    Handler para el comando /comando que realiza X acción.

    Args:
        message: Objeto Message con información del mensaje
        state: FSMContext para gestión de estados
        session: AsyncSession inyectada por DatabaseMiddleware

    Raises:
        Exception: Si hay error en operación de BD
    """
    try:
        # 1. Validar permisos si es necesario
        if not Config.is_admin(message.from_user.id):
            await message.answer("❌ No tienes permisos")
            return

        # 2. Validar estado de entrada
        # (si aplica FSM)

        # 3. Procesar lógica
        # - Consultas a BD
        # - Llamadas a servicios
        # - Cálculos

        # 4. Actualizar BD si es necesario
        await session.commit()

        # 5. Responder usuario
        await message.answer(
            "✅ Operación exitosa",
            reply_markup=teclado_opcional
        )

        # 6. Actualizar FSM si es necesario
        await state.set_state(NuevoEstado)

    except ValueError as e:
        logger.warning(f"Validación fallida: {e}")
        await message.answer("❌ Datos inválidos")
    except Exception as e:
        logger.error(f"Error en comando_handler: {e}", exc_info=True)
        await message.answer("❌ Error procesando comando")
```

### Patrón de Callback

Para botones inline (callbackquery):

```python
@router.callback_query(lambda c: c.data == "accion")
async def callback_accion(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """Handler de callback para acción X"""
    try:
        # 1. Reconocer callback
        await callback.answer()  # Elimina "reloj" en el cliente

        # 2. Procesar lógica
        # ...

        # 3. Editar o responder
        await callback.message.edit_text("Texto actualizado")
        # o
        await callback.message.answer("Nuevo mensaje")

    except Exception as e:
        logger.error(f"Error en callback: {e}")
        await callback.answer("Error procesando solicitud", show_alert=True)
```

## Handlers Planeados (ONDA 1)

### Fase 1.2: Handlers Admin

#### admin/main.py - Menú Principal Admin

```python
@router.message.command("admin")
async def admin_menu(message: Message, state: FSMContext) -> None:
    """
    Menú principal de administración.

    Acceso restringido a admins configurados en ADMIN_USER_IDS.
    Presenta opciones para gestionar VIP, Free, configuración y estadísticas.

    Args:
        message: Message del usuario admin
        state: FSMContext para cambios de estado

    Validaciones:
        - Usuario debe estar en ADMIN_USER_IDS
        - Sin parámetros adicionales

    Respuesta:
        InlineKeyboard con opciones de administración
    """
    # Validar que es admin
    if not Config.is_admin(message.from_user.id):
        await message.answer("❌ No tienes permisos para usar /admin")
        return

    # Crear teclado de opciones
    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Gestionar VIP", callback_data="admin_vip")],
        [InlineKeyboardButton(text="📺 Gestionar Free", callback_data="admin_free")],
        [InlineKeyboardButton(text="⚙️ Configuración", callback_data="admin_config")],
        [InlineKeyboardButton(text="📊 Estadísticas", callback_data="admin_stats")],
    ])

    await message.answer(
        "🤖 <b>Panel de Administración</b>\n\n"
        "Selecciona una opción:",
        reply_markup=teclado,
        parse_mode="HTML"
    )
```

#### admin/vip.py - Gestión VIP

```python
@router.callback_query(lambda c: c.data == "admin_vip")
async def vip_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Menú de gestión VIP.

    Opciones:
    - Generar token
    - Ver tokens
    - Ver suscriptores
    - Renovar suscripción

    Args:
        callback: CallbackQuery de admin
        state: FSMContext
    """
    await callback.answer()

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Generar Token", callback_data="vip_generate")],
        [InlineKeyboardButton(text="📋 Ver Tokens", callback_data="vip_list")],
        [InlineKeyboardButton(text="👥 Ver Suscriptores", callback_data="vip_subscribers")],
        [InlineKeyboardButton(text="🔄 Renovar Suscripción", callback_data="vip_renew")],
        [InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_back")],
    ])

    await callback.message.edit_text(
        "🔑 <b>Gestión VIP</b>\n\n"
        "Selecciona una opción:",
        reply_markup=teclado,
        parse_mode="HTML"
    )

@router.callback_query(lambda c: c.data == "vip_generate")
async def generate_token(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Genera nuevo token VIP.

    Flujo:
    1. Mostrar opciones de duración
    2. Admin selecciona duración
    3. Bot genera token
    4. Guardar en BD
    5. Mostrar token

    Args:
        callback: CallbackQuery del admin
        state: FSMContext para guardar duración temporal
    """
    await callback.answer()

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="24 horas", callback_data="token_duration_24")],
        [InlineKeyboardButton(text="7 días", callback_data="token_duration_168")],
        [InlineKeyboardButton(text="30 días", callback_data="token_duration_720")],
        [InlineKeyboardButton(text="Custom", callback_data="token_duration_custom")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="vip_back")],
    ])

    await state.set_state(AdminStates.generating_token)
    await callback.message.edit_text(
        "⏱️ <b>Duración del Token</b>\n\n"
        "Selecciona cuánto tiempo debe ser válido:",
        reply_markup=teclado,
        parse_mode="HTML"
    )

@router.callback_query(AdminStates.generating_token)
async def process_token_duration(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """
    Procesa la duración seleccionada y crea el token.

    Args:
        callback: CallbackQuery con duración seleccionada
        state: FSMContext
        session: AsyncSession para guardar token
    """
    await callback.answer()

    # Determinar duración en horas
    duration_map = {
        "token_duration_24": 24,
        "token_duration_168": 168,
        "token_duration_720": 720,
    }

    duration_hours = duration_map.get(callback.data, 24)

    # Generar token único
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(16))

    # Guardar en BD
    from bot.database import InvitationToken
    new_token = InvitationToken(
        token=token,
        generated_by=callback.from_user.id,
        duration_hours=duration_hours
    )
    session.add(new_token)
    await session.commit()

    # Responder
    expiry_hours = duration_hours
    expiry_days = expiry_hours // 24

    await callback.message.edit_text(
        f"✅ <b>Token Generado</b>\n\n"
        f"<code>{token}</code>\n\n"
        f"📊 Detalles:\n"
        f"• Válido por: {expiry_hours}h ({expiry_days}d)\n"
        f"• Generado en: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"• Generado por: @{callback.from_user.username or callback.from_user.first_name}\n\n"
        f"Comparte este token para invitar usuarios VIP",
        parse_mode="HTML"
    )

    await state.clear()
```

### Fase 1.3: Handlers User

#### user/start.py - Bienvenida

```python
@router.message.command("start")
async def start(message: Message, state: FSMContext) -> None:
    """
    Comando /start - Bienvenida del bot.

    Envía mensaje de bienvenida y presenta opciones para:
    - Acceso VIP (canjear token)
    - Acceso Free (cola de espera)
    - Ayuda

    Args:
        message: Message del usuario
        state: FSMContext
    """
    user = message.from_user
    await state.clear()

    teclado = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Acceso VIP", callback_data="user_vip")],
        [InlineKeyboardButton(text="📺 Acceso Free", callback_data="user_free")],
        [InlineKeyboardButton(text="❓ Ayuda", callback_data="user_help")],
    ])

    await message.answer(
        f"👋 <b>¡Hola, {user.first_name}!</b>\n\n"
        f"Bienvenido al bot de acceso a canales exclusivos.\n\n"
        f"🔑 <b>Acceso VIP:</b> Requiere token de invitación (válido 24h)\n"
        f"📺 <b>Acceso Free:</b> Solicita acceso e espera {DEFAULT_WAIT_TIME} min\n\n"
        f"¿Qué deseas hacer?",
        reply_markup=teclado,
        parse_mode="HTML"
    )
```

#### user/vip_flow.py - Canje de Tokens

```python
@router.callback_query(lambda c: c.data == "user_vip")
async def request_vip_token(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Solicita token VIP al usuario.

    Inicia FSM para capturar token ingresado.

    Args:
        callback: CallbackQuery del usuario
        state: FSMContext
    """
    await callback.answer()

    await state.set_state(UserStates.waiting_for_vip_token)
    await callback.message.edit_text(
        "🔐 <b>Acceso VIP</b>\n\n"
        "Ingresa tu token VIP (16 caracteres):\n\n"
        "<i>Ej: ABC123XYZ456789</i>",
        parse_mode="HTML"
    )

@router.message(UserStates.waiting_for_vip_token)
async def process_vip_token(
    message: Message,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """
    Procesa token VIP ingresado por usuario.

    Validaciones:
    - Longitud exacta 16 caracteres
    - Token existe en BD
    - Token no fue usado
    - Token no expiró

    Si válido:
    - Crear VIPSubscriber
    - Marcar token como usado
    - Invitar a canal VIP
    - Responder con detalles

    Args:
        message: Message con token
        state: FSMContext
        session: AsyncSession para BD
    """
    token_str = message.text.strip().upper()

    # Validar formato
    if len(token_str) != 16:
        await message.answer(
            "❌ <b>Token inválido</b>\n\n"
            "El token debe tener exactamente 16 caracteres.",
            parse_mode="HTML"
        )
        return

    # Buscar token en BD
    from sqlalchemy import select
    from bot.database import InvitationToken, VIPSubscriber

    query = select(InvitationToken).where(
        InvitationToken.token == token_str
    )
    result = await session.execute(query)
    token = result.scalar_one_or_none()

    if not token:
        await message.answer(
            "❌ <b>Token no encontrado</b>\n\n"
            "El token ingresado no existe.",
            parse_mode="HTML"
        )
        return

    # Validar que no fue usado
    if token.used:
        await message.answer(
            "❌ <b>Token ya fue usado</b>\n\n"
            "Este token ya fue canjeado por otro usuario.",
            parse_mode="HTML"
        )
        return

    # Validar que no expiró
    if token.is_expired():
        await message.answer(
            "⏰ <b>Token expirado</b>\n\n"
            "Este token ya no es válido.",
            parse_mode="HTML"
        )
        return

    # Token válido - crear suscriptor VIP
    try:
        from datetime import timedelta

        subscriber = VIPSubscriber(
            user_id=message.from_user.id,
            token_id=token.id,
            expiry_date=datetime.utcnow() + timedelta(hours=token.duration_hours),
            status="active"
        )
        session.add(subscriber)

        # Marcar token como usado
        token.used = True
        token.used_by = message.from_user.id
        token.used_at = datetime.utcnow()

        await session.commit()

        # Invitar a canal VIP
        from config import Config
        from aiogram import Bot
        bot = Bot(token=Config.BOT_TOKEN)
        try:
            await bot.add_chat_member(
                chat_id=Config.VIP_CHANNEL_ID,
                user_id=message.from_user.id
            )
        except Exception as e:
            logger.warning(f"No se pudo invitar a canal VIP: {e}")

        # Responder usuario
        days = subscriber.days_remaining()
        expiry = subscriber.expiry_date.strftime("%Y-%m-%d %H:%M")

        await message.answer(
            f"✅ <b>¡Bienvenido al VIP!</b>\n\n"
            f"🎉 Tu acceso VIP ha sido activado\n\n"
            f"📊 Detalles:\n"
            f"• Válido hasta: {expiry}\n"
            f"• Días restantes: {days}\n"
            f"• Canal: @vip_channel\n\n"
            f"Disfruta de contenido exclusivo!",
            parse_mode="HTML"
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error al procesar token VIP: {e}", exc_info=True)
        await message.answer(
            "❌ <b>Error procesando token</b>\n\n"
            "Intenta más tarde",
            parse_mode="HTML"
        )
```

#### user/free_flow.py - Cola Free

```python
@router.callback_query(lambda c: c.data == "user_free")
async def request_free_access(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """
    Procesa solicitud de acceso Free.

    Crea FreeChannelRequest si no existe uno pendiente.

    Args:
        callback: CallbackQuery del usuario
        state: FSMContext
        session: AsyncSession para BD
    """
    await callback.answer()

    # Verificar si ya tiene solicitud pendiente
    from sqlalchemy import select
    from bot.database import FreeChannelRequest

    query = select(FreeChannelRequest).where(
        (FreeChannelRequest.user_id == callback.from_user.id) &
        (FreeChannelRequest.processed == False)
    )
    result = await session.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        wait_total = Config.DEFAULT_WAIT_TIME_MINUTES
        wait_elapsed = existing.minutes_since_request()
        wait_remaining = max(0, wait_total - wait_elapsed)

        await callback.message.edit_text(
            f"⏳ <b>Solicitud pendiente</b>\n\n"
            f"Ya tienes una solicitud en cola de espera.\n\n"
            f"Tiempo restante: {wait_remaining} minutos",
            parse_mode="HTML"
        )
        return

    # Crear solicitud nueva
    try:
        request = FreeChannelRequest(user_id=callback.from_user.id)
        session.add(request)
        await session.commit()

        await callback.message.edit_text(
            f"✅ <b>Solicitud registrada</b>\n\n"
            f"Tu solicitud fue agregada a la cola de espera.\n\n"
            f"⏱️ Serás invitado al canal en {Config.DEFAULT_WAIT_TIME_MINUTES} minutos\n\n"
            f"Recibirás una notificación cuando sea tu turno.",
            parse_mode="HTML"
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error al procesar solicitud Free: {e}")
        await callback.answer("Error procesando solicitud", show_alert=True)
```

## Stats Handler (T19)

#### admin/stats.py - Panel de Estadísticas

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

**Uso del ServiceContainer:**
```python
# Crear container de servicios con sesión de BD y bot
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

**Flujo de estadísticas VIP detalladas:**
```python
@admin_router.callback_query(F.data == "admin:stats:vip")
async def callback_stats_vip(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra estadísticas detalladas de VIP.

    Incluye:
    - Total activos, expirados, histórico
    - Expiración próxima (hoy, semana, mes)
    - Actividad reciente (hoy, semana, mes)
    - Top suscriptores por días restantes

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió stats VIP detalladas")

    await callback.answer("📊 Calculando estadísticas VIP...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    try:
        vip_stats = await container.stats.get_vip_stats()

        text = _format_vip_stats_message(vip_stats)

        await callback.message.edit_text(
            text=text,
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.debug(f"✅ VIP stats mostradas a user {callback.from_user.id}")

    except Exception as e:
        logger.error(f"❌ Error obteniendo VIP stats: {e}", exc_info=True)

        await callback.message.edit_text(
            "❌ <b>Error al Calcular Estadísticas VIP</b>\n\n"
            "Hubo un problema al obtener las métricas.\n"
            "Intenta nuevamente en unos momentos.",
            reply_markup=stats_menu_keyboard(),
            parse_mode="HTML"
        )
```

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

## Dashboard Handler (T27)

#### admin/dashboard.py - Panel de Control Completo

**Responsabilidad:** Handlers del panel de control completo del sistema que proporciona una visión general del estado del bot con health checks, configuración, estadísticas clave, tareas en segundo plano y acciones rápidas.

**Componentes:**
- `bot/handlers/admin/dashboard.py` - Handlers principales y callbacks de navegación para el panel de control completo

**Características:**
- **Estado de configuración:** Visualización del estado de los canales VIP y Free, reacciones configuradas y tiempo de espera
- **Estadísticas clave:** Métricas importantes como VIPs activos, solicitudes Free pendientes, tokens disponibles y nuevos VIPs
- **Health checks:** Verificación del estado del sistema con identificación de problemas y advertencias
- **Background tasks:** Estado del scheduler y próxima ejecución de tareas programadas
- **Acciones rápidas:** Acceso directo a funciones administrativas desde el dashboard
- **Actualización automática:** Muestra la hora exacta de la última actualización
- **Diseño estructurado:** Información organizada en secciones claras con bordes y emojis

**Flujo principal:**
1. Usuario admin selecciona "📊 Dashboard Completo" en el menú principal
2. Bot recopila todos los datos necesarios para el dashboard
3. Bot realiza health checks del sistema
4. Bot formatea mensaje con `_format_dashboard_message()`
5. Bot crea teclado inline con `_create_dashboard_keyboard()`
6. Bot envía dashboard completo con estado general, problemas detectados, configuración actual, estadísticas clave y estado de tareas en segundo plano
7. Usuario puede navegar a otras secciones desde el teclado inline

**Estructura de callbacks:**
- `admin:dashboard` - Callback para mostrar el dashboard completo del sistema

**Flujo de recopilación de datos:**
1. Admin selecciona "📊 Dashboard Completo"
2. Bot llama a `_gather_dashboard_data()` que recopila:
   - Estado de configuración (VIP/Free channels, reacciones, tiempo de espera)
   - Estadísticas generales del sistema
   - Estado del scheduler y tareas en segundo plano
   - Realiza health checks del sistema
3. Bot formatea mensaje con `_format_dashboard_message()`
4. Bot crea teclado inline con `_create_dashboard_keyboard()`
5. Bot envía dashboard al admin

**Ejemplo de handler de dashboard:**
```python
@admin_router.callback_query(F.data == "admin:dashboard")
async def callback_admin_dashboard(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra dashboard completo del sistema.

    Incluye:
    - Estado de configuración (canales, reacciones)
    - Estadísticas clave (VIP, Free, Tokens)
    - Background tasks (estado, próxima ejecución)
    - Health checks
    - Acciones rápidas

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"📊 Usuario {callback.from_user.id} abrió dashboard completo")

    await callback.answer("📊 Cargando dashboard...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    try:
        # Obtener datos del dashboard
        dashboard_data = await _gather_dashboard_data(container)

        # Formatear mensaje
        text = _format_dashboard_message(dashboard_data)

        # Keyboard con acciones rápidas
        keyboard = _create_dashboard_keyboard(dashboard_data)

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        logger.debug("✅ Dashboard mostrado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error generando dashboard: {e}", exc_info=True)

        await callback.message.edit_text(
            "❌ <b>Error al Cargar Dashboard</b>\n\n"
            "No se pudo generar el dashboard completo.\n"
            "Intenta nuevamente.",
            reply_markup=create_inline_keyboard([
                [{"text": "🔄 Reintentar", "callback_data": "admin:dashboard"}],
                [{"text": "🔙 Volver", "callback_data": "admin:main"}]
            ]),
            parse_mode="HTML"
        )
```

**Flujo de health checks:**
1. Bot recibe datos de configuración, estadísticas y scheduler
2. Bot llama a `_perform_health_checks()` con los datos
3. Función verifica:
   - Canales configurados (VIP y Free)
   - Background tasks corriendo
   - Tokens disponibles
   - VIPs próximos a expirar
   - Cola Free grande
4. Función determina estado general (healthy, degraded, down)
5. Bot incluye resultados en el dashboard

**Formato de mensaje del dashboard:**
- `_format_dashboard_message()` - Dashboard general con secciones de configuración, estadísticas clave, background tasks y health checks
- Diseño estructurado con emojis y bordes para mejor visualización
- Muestra estado general del sistema con indicadores visuales

**Interacción con teclados inline:**
```python
def _create_dashboard_keyboard(data: dict) -> "InlineKeyboardMarkup":
    """
    Crea keyboard del dashboard con acciones rápidas.

    Args:
        data: Dict con datos del dashboard

    Returns:
        InlineKeyboardMarkup con acciones
    """
    buttons = []

    # Fila 1: Stats y Config
    buttons.append([
        {"text": "📊 Estadísticas Detalladas", "callback_data": "admin:stats"},
        {"text": "⚙️ Configuración", "callback_data": "admin:config"}
    ])

    # Fila 2: Gestión (adaptativa según configuración)
    row_2 = []

    if data["config"]["vip_configured"]:
        row_2.append(
            {"text": "👥 Suscriptores VIP", "callback_data": "vip:list_subscribers"}
        )

    if data["config"]["free_configured"]:
        row_2.append(
            {"text": "📋 Cola Free", "callback_data": "free:view_queue"}
        )

    if row_2:
        buttons.append(row_2)

    # Fila 3: Actualizar y Volver
    buttons.append([
        {"text": "🔄 Actualizar", "callback_data": "admin:dashboard"},
        {"text": "🔙 Menú", "callback_data": "admin:main"}
    ])

    return create_inline_keyboard(buttons)
```

**Características del dashboard:**
- **Actualización automática:** Muestra la hora exacta de la última actualización
- **Diseño estructurado:** Información organizada en secciones claras con bordes y emojis
- **Adaptabilidad:** El teclado inline se adapta según la configuración actual (muestra "Suscriptores VIP" solo si canal VIP está configurado)
- **Acceso directo:** Botones para acceder rápidamente a funciones administrativas importantes
- **Health checks:** Identificación automática de problemas y advertencias en el sistema
- **Visualización clara:** Uso de emojis y formato HTML para mejor comprensión del estado del sistema
```

## Inyección de Dependencias

Los handlers reciben dependencias inyectadas automáticamente:

```python
async def handler(
    message: Message,              # Inyectado por Aiogram
    state: FSMContext,             # Inyectado por Dispatcher
    session: AsyncSession           # Inyectado por DatabaseMiddleware
) -> None:
    pass
```

La inyección se configura en middlewares (Fase 1.4):

```python
# En main.py
dp.message.middleware(DatabaseMiddleware())
```

## Registro de Handlers

Todos los handlers se registran en __init__.py de cada módulo:

```python
# bot/handlers/__init__.py
from aiogram import Router
from bot.handlers.admin import admin_router
from bot.handlers.user import user_router

main_router = Router()
main_router.include_router(admin_router)
main_router.include_router(user_router)

# En main.py
from bot.handlers import main_router
dp.include_router(main_router)
```

## Manejo de Errores en Handlers

Patrón recomendado:

```python
@router.message.command("ejemplo")
async def ejemplo_handler(message: Message) -> None:
    """Handler con manejo de errores"""
    try:
        # Lógica del handler
        pass

    except ValueError as e:
        # Errores de validación (usuario)
        logger.warning(f"Validación fallida: {e}")
        await message.answer(f"❌ Error de validación: {e}")

    except DatabaseError as e:
        # Errores de base de datos
        logger.error(f"Error de BD: {e}", exc_info=True)
        await message.answer("❌ Error accediendo base de datos")

    except Exception as e:
        # Errores inesperados
        logger.critical(f"Error inesperado: {e}", exc_info=True)
        await message.answer("❌ Error inesperado procesando comando")
```

## Logging en Handlers

Usar logger para auditoría:

```python
import logging

logger = logging.getLogger(__name__)

@router.message.command("comando")
async def comando_handler(message: Message) -> None:
    logger.info(
        f"Comando ejecutado por usuario {message.from_user.id}: "
        f"/{message.text}"
    )
    # ...
```

## Testing de Handlers

En ONDA 2+, se usará pytest-asyncio:

```python
import pytest
from aiogram.types import Message, User, Chat

@pytest.mark.asyncio
async def test_start_handler():
    message = Message(
        message_id=1,
        date=1234567890,
        chat=Chat(id=1, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Test"),
        text="/start"
    )
    # Simular handler
    # Verificar respuesta
    assert response == expected
```

---

## Custom Reactions Handler (T11)

#### gamification/handlers/user/reactions.py - Handler de Reacciones Personalizadas

**Responsabilidad:** Handlers para el sistema de reacciones personalizadas que permiten a los usuarios interactuar con mensajes de broadcasting mediante botones de reacción con gamificación (ganancia de besitos).

**Componentes:**
- `bot/gamification/handlers/user/reactions.py` - Handler principal para procesar reacciones de usuarios a mensajes de broadcasting

**Características:**
- **Reacciones personalizadas:** Botones de reacción con emojis configurables
- **Gamificación:** Usuarios ganan besitos por reaccionar a mensajes
- **Prevención de duplicados:** No permite múltiples reacciones idénticas por usuario
- **Visualización en tiempo real:** Actualización del botón con checkmark personal
- **Integración con estadísticas:** Actualización de contadores de reacciones en tiempo real
- **Feedback inmediato:** Notificaciones con cantidad de besitos ganados

**Flujo principal:**
1. Usuario hace click en botón de reacción en mensaje de broadcasting
2. Bot recibe callback con reaction_type_id
3. Bot identifica el mensaje de broadcasting y al usuario
4. Bot verifica que no exista reacción duplicada
5. Bot registra reacción y otorga besitos al usuario
6. Bot actualiza teclado con marca personal
7. Bot notifica al usuario besitos ganados

**Estructura de callbacks:**
- `react:{reaction_type_id}` - Callback para registrar una reacción personalizada (ej: "react:1", "react:2")

**Aplicación de handler:**
```python
from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.engine import get_session
from bot.gamification.services.custom_reaction import CustomReactionService
from bot.services.container import ServiceContainer

router = Router()

@router.callback_query(lambda c: c.data.startswith("react:"))
async def handle_reaction_button(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Handler para botones de reacción personalizados.

    Callback data: "react:{reaction_type_id}"

    Args:
        callback: CallbackQuery con reaction_type_id
        session: Sesión de BD (inyectada por middleware)
    """
    # Extraer reaction_type_id del callback
    reaction_type_id = int(callback.data.split(":")[1])

    user_id = callback.from_user.id
    message_id = callback.message.message_id
    chat_id = callback.message.chat.id

    # Validar que el mensaje es un broadcast registrado
    broadcast_result = await session.execute(
        select(BroadcastMessage)
        .where(BroadcastMessage.message_id == message_id)
        .where(BroadcastMessage.chat_id == chat_id)
    )
    broadcast_msg = broadcast_result.scalar_one_or_none()

    if not broadcast_msg:
        await callback.answer(
            text="❌ Esta publicación no tiene gamificación activa",
            show_alert=True
        )
        return

    # Obtener el servicio de reacciones personalizadas
    container = ServiceContainer(session, callback.bot)
    custom_reaction_service = container.custom_reaction

    # Registrar la reacción
    result = await custom_reaction_service.register_custom_reaction(
        broadcast_message_id=broadcast_msg.id,
        user_id=user_id,
        reaction_type_id=reaction_type_id
    )

    if result["success"]:
        # Actualizar teclado con marca personal
        updated_keyboard = await _build_reaction_keyboard_with_marks(
            session, broadcast_msg.id, user_id, broadcast_msg.reaction_buttons
        )

        try:
            await callback.message.edit_reply_markup(
                reply_markup=updated_keyboard
            )
        except Exception:
            # No se puede editar el teclado, continuar sin error
            pass

        # Enviar alerta con besitos ganados
        await callback.answer(
            text=f"🎉 ¡Reacción registrada! Ganaste {result['besitos_earned']} besitos",
            show_alert=False  # Mostrar como toast, no alerta
        )
    else:
        if result["already_reacted"]:
            await callback.answer(
                text="Ya reaccionaste con este emoji a esta publicación",
                show_alert=False
            )
        else:
            await callback.answer(
                text="Error al registrar reacción",
                show_alert=True
            )

async def _build_reaction_keyboard_with_marks(
    session: AsyncSession,
    broadcast_message_id: int,
    current_user_id: int,
    reaction_config: List[Dict]
) -> InlineKeyboardMarkup:
    """
    Construye un teclado con marcas de reacciones ya realizadas por el usuario.
    """
    # Obtener estadísticas de reacciones
    reaction_stats = await get_reaction_counts(session, broadcast_message_id)

    # Obtener reacciones del usuario actual
    user_reactions = await get_user_reactions_for_message(
        session, broadcast_message_id, current_user_id
    )

    # Ordenar reacciones por sort_order
    sorted_reactions = sorted(
        reaction_config,
        key=lambda x: x.get("sort_order", 0)
    )

    buttons = []
    current_row = []

    for i, reaction in enumerate(sorted_reactions):
        emoji = reaction["emoji"]
        label = reaction.get("label", emoji)
        reaction_type_id = reaction["reaction_type_id"]

        # Obtener conteo para este emoji
        count = reaction_stats.get(emoji, 0)

        # Determinar si el usuario actual ya reaccionó con este tipo
        is_reacted = reaction_type_id in user_reactions

        if is_reacted:
            # Añadir checkmark personal
            button_text = f"{emoji} {count} ✓"
        else:
            button_text = f"{emoji} {count}"

        callback_data = f"react:{reaction_type_id}"

        current_row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        ))

        # Cada 3 botones o al final, crear nueva fila
        if len(current_row) == 3 or i == len(sorted_reactions) - 1:
            buttons.append(current_row)
            current_row = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_reaction_counts(
    session: AsyncSession,
    broadcast_message_id: int
) -> Dict[str, int]:
    """
    Obtiene el conteo de reacciones por emoji para un mensaje.
    """
    result = await session.execute(
        select(CustomReaction.emoji, func.count(CustomReaction.id))
        .where(CustomReaction.broadcast_message_id == broadcast_message_id)
        .group_by(CustomReaction.emoji)
    )
    return dict(result.fetchall())

async def get_user_reactions_for_message(
    session: AsyncSession,
    broadcast_message_id: int,
    user_id: int
) -> List[int]:
    """
    Obtiene los IDs de reacciones ya realizadas por un usuario en un mensaje.
    """
    result = await session.execute(
        select(CustomReaction.reaction_type_id)
        .where(CustomReaction.broadcast_message_id == broadcast_message_id)
        .where(CustomReaction.user_id == user_id)
    )
    return [row[0] for row in result.fetchall()]
```

**Flujo de reacción de usuario:**
1. Usuario hace click en botón con emoji (ej: "👍 45")
2. Bot recibe callback "react:1" con reaction_type_id
3. Bot verifica que mensaje es broadcast con gamificación
4. Bot verifica que usuario no haya reaccionado previamente con mismo emoji
5. Bot registra CustomReaction en base de datos
6. Bot otorga besitos al usuario
7. Bot actualiza teclado con marca personal (✓)
8. Bot notifica cantidad de besitos ganados

**Integración con teclados inline:**
- `_build_reaction_keyboard_with_marks()` - Crea teclado con contadores públicos de reacciones y checkmark personal
- `get_reaction_counts()` - Obtiene conteo de reacciones por emoji
- `get_user_reactions_for_message()` - Obtiene reacciones específicas de un usuario

**Características del sistema:**
- **Contadores públicos:** Muestra cantidad real de reacciones por emoji (ej: "👍 45", "❤️ 32")
- **Checkmarks personales:** Indicador visual que muestra al usuario reacciones propias (ej: "👍 45 ✓")
- **No cambio de reacción:** Una vez reaccionado, no se puede cambiar a otro emoji
- **Reacciones ilimitadas:** Usuario puede reaccionar con múltiples botones diferentes
- **Feedback inmediato:** Notificación toast con cantidad de besitos ganados
- **Prevención de spam:** Índice único en BD previene reacciones duplicadas

**Manejo de errores:**
- Validación de existencia de mensaje de broadcasting
- Prevención de reacciones duplicadas
- Manejo de errores de edición de teclado
- Logging detallado de reacciones registradas

## Broadcasting Handler con Gamificación (T22 - Extensión)

#### handlers/admin/broadcast.py - Extensión con Gamificación

**Responsabilidad:** Extensión del sistema de broadcasting para incluir opciones de gamificación con reacciones personalizadas y protección de contenido.

**Características extendidas:**
- **Estados FSM extendidos:** Nuevo estado `configuring_options` entre `waiting_for_content` y `waiting_for_confirmation`
- **Configuración de gamificación:** Activación/desactivación de sistema de reacciones
- **Selección de reacciones:** Elección de emojis para botones de reacción
- **Protección de contenido:** Opción para activar `protect_content` en mensajes
- **Caché de estadísticas:** Actualización en tiempo real de contadores

**Estados FSM extendidos:**
```python
class BroadcastStates(StatesGroup):
    waiting_for_content = State()        # Ya existente
    configuring_options = State()        # Nuevo estado
    selecting_reactions = State()        # Ya existente
    waiting_for_confirmation = State()   # Ya existente
```

**Flujo extendido de broadcasting:**
1. Admin selecciona "📤 Enviar a Canal VIP" o "📤 Enviar a Canal Free"
2. Bot entra en estado FSM `waiting_for_content`
3. Admin envía contenido (texto, foto o video)
4. Bot entra en estado FSM `configuring_options` (nuevo)
5. Bot muestra opciones de configuración:
   - Activar/desactivar gamificación
   - Seleccionar reacciones
   - Activar/desactivar protección de contenido
6. Admin configura opciones
7. Bot entra en estado `waiting_for_confirmation`
8. Bot muestra vista previa y solicita confirmación
9. Admin confirma o cancela envío
10. Si confirma: Bot envía contenido al canal y registra en BD con opciones

**Ejemplo de handler de configuración:**
```python
@router.message(BroadcastStates.waiting_for_content)
async def process_broadcast_content(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el contenido enviado para broadcasting y pasa a opciones de configuración.

    Args:
        message: Mensaje con contenido
        state: FSM context
        session: Sesión de BD
    """
    # ... código existente para procesar contenido ...
    content_data = {
        'text': getattr(message, 'text', getattr(message, 'caption', '')),
        'photo': getattr(message, 'photo', None),
        'video': getattr(message, 'video', None),
        'document': getattr(message, 'document', None)
    }

    # Guardar contenido en el estado para uso posterior
    await state.update_data({
        **content_data,
        "gamification_enabled": False,  # Por defecto deshabilitado
        "content_protected": False,     # Por defecto sin protección
        "selected_reactions": []        # Reacciones seleccionadas
    })

    # Cambiar al nuevo estado de configuración
    await state.set_state(BroadcastStates.configuring_options)

    # Mostrar opciones de configuración
    await show_broadcast_options(message, state)

async def show_broadcast_options(message: Message, state: FSMContext):
    """
    Muestra las opciones de configuración para el broadcast.

    Args:
        message: Mensaje para responder
        state: FSM context
    """
    data = await state.get_data()
    gamification_enabled = data.get("gamification_enabled", False)
    content_protected = data.get("content_protected", False)
    selected_reactions = data.get("selected_reactions", [])

    text = (
        "<b>⚙️ Opciones de Broadcasting</b>\n\n"
        f"🎮 Gamificación: {'✅ Activada' if gamification_enabled else '❌ Desactivada'}\n"
        f"🔒 Contenido protegido: {'✅ Sí' if content_protected else '❌ No'}\n"
        f".Reactivos seleccionados: {len(selected_reactions)}\n\n"
        "Selecciona las opciones que deseas aplicar:"
    )

    # Crear teclado con opciones
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎮 Configurar Reacciones" if not gamification_enabled else "🎮 Editar Reacciones",
                callback_data="broadcast:config:reactions"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Desactivar Gamificación" if gamification_enabled else "✅ Activar Gamificación",
                callback_data="broadcast:config:gamification_toggle"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔒 Activar Protección" if not content_protected else "🔓 Desactivar Protección",
                callback_data="broadcast:config:protection_toggle"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Continuar",
                callback_data="broadcast:continue"
            ),
            InlineKeyboardButton(
                text="❌ Cancelar",
                callback_data="broadcast:cancel"
            )
        ]
    ])

    await message.answer(text=text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("broadcast:config:"))
async def handle_broadcast_config_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Maneja callbacks de configuración de broadcasting.
    """
    data = callback.data.split(":")

    if data[2] == "reactions":
        # Mostrar selección de reacciones
        await show_reaction_selection(callback, state, session)
    elif data[2] == "gamification_toggle":
        # Alternar gamificación
        current_data = await state.get_data()
        new_state = not current_data.get("gamification_enabled", False)
        await state.update_data({"gamification_enabled": new_state})

        # Actualizar mensaje
        await show_broadcast_options(callback.message, state)
        await callback.answer()
    elif data[2] == "protection_toggle":
        # Alternar protección
        current_data = await state.get_data()
        new_state = not current_data.get("content_protected", False)
        await state.update_data({"content_protected": new_state})

        # Actualizar mensaje
        await show_broadcast_options(callback.message, state)
        await callback.answer()
    elif data[2] == "continue":
        # Confirmar broadcasting
        await callback_broadcast_confirm(callback, state, session)
    elif data[2] == "cancel":
        # Cancelar
        await callback.message.edit_text("❌ Envío cancelado.")
        await state.clear()

async def show_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Muestra la selección de reacciones para el broadcast.
    """
    # Obtener todas las reacciones disponibles
    all_reactions_result = await session.execute(
        select(Reaction)
        .where(Reaction.active == True)
        .order_by(Reaction.sort_order)
    )
    all_reactions = all_reactions_result.scalars().all()

    current_data = await state.get_data()
    selected_reactions = current_data.get("selected_reactions", [])

    # Crear teclado con todas las reacciones y checkboxes
    keyboard_rows = []
    current_row = []

    for i, reaction in enumerate(all_reactions):
        # Determinar si está seleccionado
        is_selected = reaction.id in selected_reactions

        # Texto del botón con checkbox
        checkbox = "✅ " if is_selected else "☐ "
        button_text = f"{checkbox}{reaction.emoji} {reaction.button_label or reaction.emoji}"

        # Callback para alternar selección
        callback_data = f"broadcast:react:toggle:{reaction.id}"

        current_row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        ))

        # Cada 2 botones o al final, crear nueva fila
        if len(current_row) == 2 or i == len(all_reactions) - 1:
            keyboard_rows.append(current_row)
            current_row = []

    # Añadir botones de confirmación
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Confirmar Reacciones",
            callback_data="broadcast:react:confirm"
        )
    ])
    keyboard_rows.append([
        InlineKeyboardButton(
            text="❌ Volver",
            callback_data="broadcast:back_to_options"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        text="<b>🎮 Selecciona Reacciones para el Broadcast</b>\n\n"
             "Elige los emojis que se mostrarán como botones en la publicación:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("broadcast:react:toggle:"))
async def toggle_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Alterna la selección de una reacción específica.
    """
    reaction_id = int(callback.data.split(":")[3])

    current_data = await state.get_data()
    selected_reactions = current_data.get("selected_reactions", [])

    # Alternar selección
    if reaction_id in selected_reactions:
        selected_reactions.remove(reaction_id)
    else:
        selected_reactions.append(reaction_id)

    # Actualizar FSM data
    await state.update_data({"selected_reactions": selected_reactions})

    # Actualizar mensaje con selección actualizada
    await show_reaction_selection(callback, state, callback.bot.session)
    await callback.answer()

@router.callback_query(F.data == "broadcast:react:confirm")
async def confirm_reaction_selection(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Confirma la selección de reacciones.
    """
    current_data = await state.get_data()
    selected_reactions = current_data.get("selected_reactions", [])

    if not selected_reactions:
        await callback.answer("❌ Debes seleccionar al menos una reacción", show_alert=True)
        return

    # Activar gamificación
    await state.update_data({
        "gamification_enabled": True,
        "selected_reactions": selected_reactions
    })

    # Volver a opciones
    await show_broadcast_options(callback.message, state)
    await callback.answer("✅ Reacciones seleccionadas")

@router.callback_query(F.data == "broadcast:continue")
async def callback_broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Confirma y envía el mensaje al canal(es) con opciones de gamificación.

    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    user_id = callback.from_user.id

    # Obtener data del FSM
    data = await state.get_data()

    # Determinar tipo de contenido
    content_type = "text"  # o "photo", "video" según el contenido
    caption = data.get('text', '')
    file_id = data.get('photo', data.get('video', None))

    # Obtener opciones de gamificación
    gamification_enabled = data.get("gamification_enabled", False)
    content_protected = data.get("content_protected", False)
    selected_reactions = data.get("selected_reactions", [])

    logger.info(f"📤 Usuario {user_id} confirmó broadcast "
                f"con gamificación: {gamification_enabled}, "
                f"contenido protegido: {content_protected}")

    # Notificar que se está enviando
    await callback.answer("📤 Enviando publicación...", show_alert=False)

    container = ServiceContainer(session, callback.bot)

    # Determinar canales destino
    # ... código para obtener canales ...

    # Configurar gamificación si está habilitada
    gamification_config = None
    if gamification_enabled and selected_reactions:
        gamification_config = {
            "enabled": True,
            "reactions": selected_reactions,
            "protected": content_protected
        }

    # Enviar usando BroadcastService con gamificación
    result = await container.broadcast.send_broadcast_with_gamification(
        target="vip",  # o "free", "both" según el caso
        content_type=content_type,
        content_text=caption,
        media_file_id=file_id,
        sent_by=user_id,
        gamification_config=gamification_config or {},
        content_protected=content_protected
    )

    # ... manejo de resultados ...

    # Limpiar estado FSM
    await state.clear()

    logger.info(f"✅ Broadcasting con gamificación completado para user {user_id}")
```

**Integración con teclados inline de broadcasting con gamificación:**
```python
# Teclado para opciones de configuración
options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="🎮 Configurar Reacciones",
            callback_data="broadcast:config:reactions"
        )
    ],
    [
        InlineKeyboardButton(
            text="🔒 Activar Protección",
            callback_data="broadcast:config:protection_toggle"
        )
    ],
    [
        InlineKeyboardButton(
            text="✅ Continuar",
            callback_data="broadcast:continue"
        ),
        InlineKeyboardButton(
            text="❌ Cancelar",
            callback_data="broadcast:cancel"
        )
    ]
])

# Teclado para selección de reacciones
reactions_selection_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    # Botones con checkboxes para cada reacción
    # [InlineKeyboardButton(text="✅ 👍 Me Gusta", callback_data="broadcast:react:toggle:1")],
    # [InlineKeyboardButton(text="☐ ❤️ Me Encanta", callback_data="broadcast:react:toggle:2")],
    # ...
    [
        InlineKeyboardButton(
            text="✅ Confirmar Reacciones",
            callback_data="broadcast:react:confirm"
        )
    ]
])
```

**Características de la extensión:**
- **Backward compatibility:** Broadcasting sin gamificación sigue funcionando exactamente igual
- **Configuración intuitiva:** Interfaz de usuario clara para activar/desactivar opciones
- **Selección flexible:** Elección de múltiples reacciones para cada broadcast
- **Protección opcional:** Activación opcional de `protect_content` para evitar forward/copiar
- **Integración completa:** Registro en BD con todas las opciones configuradas
- **Visualización en canal:** Botones de reacción aparecen directamente en el mensaje enviado

**Manejo de errores:**
- Validación de selección mínima de reacciones
- Manejo de errores en servicios de broadcasting
- Logging detallado de proceso de broadcasting

---

## Dynamic Menu Handler (T28)

#### user/dynamic_menu.py - Handler de Menús Dinámicos

**Responsabilidad:** Handler para procesar callbacks de menús dinámicos que permiten a los administradores personalizar los botones y opciones disponibles para los usuarios VIP y FREE.

**Componentes:**
- `bot/handlers/user/dynamic_menu.py` - Handler principal para procesar menús dinámicos
- `bot/services/menu_service.py` - Servicio para gestión de menús configurables
- `bot/database/models.py` - Modelos MenuItem y MenuConfig para almacenar configuración

**Características:**
- **Configuración por rol:** Diferencia entre menús VIP y FREE
- **Botones personalizables:** Texto, emojis, acciones configurables por admin
- **Tipos de acción:** Información, URLs, callbacks, contactos
- **Orden personalizable:** Control sobre posición y agrupación de botones
- **Activación/desactivación:** Control granular sobre visibilidad de botones
- **Integración con start:** Menús se generan dinámicamente al iniciar bot

**Flujo principal:**
1. Usuario envía /start o accede a menú
2. Bot determina rol del usuario (VIP, FREE o otro)
3. Bot obtiene configuración de menú para ese rol
4. Bot genera teclado con botones configurados
5. Usuario interactúa con botones personalizados
6. Bot procesa acciones según tipo (info, URL, callback)

**Estructura de callbacks:**
- `menu:{item_key}` - Callback general para procesar menús dinámicos (ej: "menu:vip_info_1", "menu:free_contact")

**Aplicación de handler:**
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.container import ServiceContainer

dynamic_menu_router = Router()

@dynamic_menu_router.callback_query(F.data.startswith("menu:"))
async def callback_dynamic_menu_item(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Procesa clicks en botones de menú dinámico.

    Callback format: menu:{item_key}
    """
    item_key = callback.data.replace("menu:", "")

    container = ServiceContainer(session, callback.bot)
    item = await container.menu.get_menu_item(item_key)

    if not item:
        await callback.answer("❌ Opción no disponible", show_alert=True)
        return

    if item.action_type == "info":
        # Mostrar información
        emoji = item.button_emoji or "ℹ️"
        await callback.message.answer(
            f"{emoji} <b>{item.button_text}</b>\n\n"
            f"{item.action_content}",
            parse_mode="HTML"
        )
        await callback.answer()

    elif item.action_type == "contact":
        # Mostrar información de contacto
        await callback.message.answer(
            f"📞 <b>Contacto</b>\n\n"
            f"{item.action_content}",
            parse_mode="HTML"
        )
        await callback.answer()

    elif item.action_type == "callback":
        # Procesar callback interno (ej: "menu:subscribe_vip")
        # Lógica específica según item.action_content
        pass

    # action_type == "url" se maneja automáticamente por Telegram
    # (el botón tiene url en lugar de callback_data)
```

**Flujo de generación de menú dinámico:**
1. Usuario envía /start o accede a menú
2. Bot determina rol del usuario (VIP o FREE)
3. Bot llama a `container.menu.build_keyboard_for_role(role)`
4. Servicio obtiene todos los `MenuItem` activos para ese rol
5. Servicio agrupa botones por `row_number` y ordena por `display_order`
6. Servicio crea estructura de teclado compatible con `create_inline_keyboard()`
7. Bot envía mensaje con menú personalizado

**Integración con teclados:**
```python
# Función para generar menú dinámico
async def dynamic_user_menu_keyboard(
    session: AsyncSession,
    role: str
) -> InlineKeyboardMarkup:
    """
    Genera keyboard dinámico para usuarios basado en configuración.

    Args:
        session: Sesión de BD
        role: 'vip' o 'free'

    Returns:
        InlineKeyboardMarkup con botones configurados
    """
    from bot.services.menu_service import MenuService

    menu_service = MenuService(session)
    keyboard_structure = await menu_service.build_keyboard_for_role(role)

    if not keyboard_structure:
        # Fallback a menú por defecto si no hay configuración
        if role == 'vip':
            return vip_user_menu_keyboard()  # Existente
        else:
            return free_user_menu_keyboard()  # Existente

    return create_inline_keyboard(keyboard_structure)
```

**Características del sistema:**
- **Flexibilidad:** Admins pueden crear botones con diferentes tipos de acciones
- **Filtro por rol:** Botones se muestran solo a usuarios de roles específicos
- **Ordenamiento:** Control sobre posición y agrupación de botones
- **Fallback:** Si no hay configuración, se usan menús por defecto
- **Cache opcional:** Para optimizar performance en menús estáticos
- **Acciones personalizadas:** Soporte para info, URLs, callbacks y contactos

**Manejo de errores:**
- Validación de existencia de item al procesar callback
- Manejo de tipos de acción desconocidos
- Logging detallado de interacciones con menú

---

**Última actualización:** 2025-12-26
**Versión:** 1.0.0
**Estado:** Documentación de todos los handlers implementados
