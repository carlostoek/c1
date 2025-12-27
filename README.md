# 🤖 Bot de Administración de Canales VIP/Free - Telegram

Bot para gestionar canales VIP (por invitación con tokens) y canales Free (con tiempo de espera) en Telegram, optimizado para ejecutarse en Termux.

## 📋 Requisitos

- Python 3.11+
- Termux (Android) o Linux
- Token de bot de Telegram (via @BotFather)

## 🚀 Instalación en Termux

```bash
# 1. Actualizar Termux
pkg update && pkg upgrade

# 2. Instalar Python
pkg install python

# 3. Clonar o crear el proyecto
mkdir telegram_vip_bot
cd telegram_vip_bot

# 4. Instalar dependencias
pip install -r requirements.txt --break-system-packages

# 5. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus valores
```

## ⚙️ Configuración

1. **Obtener Token del Bot:**
   - Hablar con @BotFather en Telegram
   - Ejecutar `/newbot` y seguir instrucciones
   - Copiar el token generado

2. **Obtener tu User ID:**
   - Hablar con @userinfobot
   - Copiar tu ID numérico

3. **Editar `.env`:**
   ```bash
   BOT_TOKEN=tu_token_aqui
   ADMIN_USER_IDS=tu_user_id_aqui
   ```

## 🏃 Ejecución

```bash
# Desarrollo
python main.py

# En background (Termux)
nohup python main.py > bot.log 2>&1 &
```

## 📁 Estructura del Proyecto

```
/
├── main.py              # Entry point
├── config.py            # Configuración
├── bot/
│   ├── database/        # Modelos y engine SQLAlchemy
│   ├── services/        # Lógica de negocio
│   │   ├── container.py # Contenedor de servicios (DI + Lazy Loading)
│   │   ├── subscription.py # Gestión de suscripciones VIP/Free
│   │   ├── channel.py   # Gestión de canales
│   │   ├── config.py    # Configuración del bot
│   │   └── stats.py     # Estadísticas
│   ├── handlers/        # Handlers de comandos/callbacks
│   ├── middlewares/     # Middlewares (auth, DB)
│   ├── states/          # Estados FSM
│   ├── utils/           # Utilidades
│   └── background/      # Tareas programadas
├── docs/
│   ├── ARCHITECTURE.md  # Documentación de arquitectura
│   ├── CHANNEL_SERVICE.md # Documentación específica del servicio de canales
│   ├── CONFIG_SERVICE.md # Documentación específica del servicio de configuración
│   ├── DASHBOARD.md # Documentación del dashboard completo del sistema (T27)
│   └── ...
```

## 🔧 Arquitectura de Servicios

### Service Container (T6)
Implementación de patrón Dependency Injection + Lazy Loading para reducir consumo de memoria en Termux:

- **4 servicios disponibles:** subscription, channel, config, stats
- **Carga diferida:** servicios se instancian solo cuando se acceden por primera vez
- **Monitoreo:** método `get_loaded_services()` para tracking de uso de memoria
- **Optimización:** reduce memoria inicial en Termux al cargar servicios bajo demanda

### Subscription Service (T7)
Gestión completa de suscripciones VIP y Free con 14 métodos asíncronos:

- **Tokens VIP:** generación, validación, canje y extensión de suscripciones
- **Flujo completo:** generar token → validar → canjear → extender
- **Cola Free:** sistema de espera configurable con `wait_time`
- **Invite links únicos:** enlaces de un solo uso (`member_limit=1`)
- **Gestión de usuarios:** creación, extensión y expiración automática de suscripciones

### Channel Service (T8)
Gestión completa de canales VIP y Free con verificación de permisos y envío de publicaciones:

- **Configuración de canales:** setup_vip_channel() y setup_free_channel() con verificación de permisos
- **Verificación de permisos:** can_invite_users, can_post_messages y verificación de admin status
- **Envío de contenido:** soporte para texto, fotos y videos a canales
- **Reenvío y copia:** métodos para reenviar y copiar mensajes a canales
- **Validación de configuración:** métodos para verificar si canales están configurados

### Config Service (T9)
Gestión de configuración global del bot con funcionalidades clave:

- **Gestión de configuración global:** Obtener/actualizar configuración de BotConfig (singleton)
- **Tiempo de espera Free:** Gestionar tiempo de espera para acceso al canal Free
- **Reacciones de canales:** Gestionar reacciones personalizadas para canales VIP y Free
- **Validación de configuración:** Verificar que la configuración esté completa
- **Tarifas de suscripción:** Configurar y gestionar precios de suscripciones

### Middlewares (T10)
Implementación de middlewares para autenticación de administradores e inyección automática de sesiones de base de datos:

- **AdminAuthMiddleware:** Valida que el usuario tenga permisos de administrador antes de ejecutar handlers protegidos
- **DatabaseMiddleware:** Inyecta automáticamente una sesión de SQLAlchemy a cada handler que lo requiera
- **Aplicación a handlers:** Se aplican a routers y handlers que requieren permisos administrativos o acceso a BD
- **Manejo de errores:** Si el usuario no es admin, responde con mensaje de error y no ejecuta el handler
- **Inyección automática:** Proporciona una sesión de SQLAlchemy a cada handler automáticamente

**Ejemplo de uso de los middlewares:**
```python
from aiogram import Router
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.middlewares.database import DatabaseMiddleware

# Aplicar middlewares a un router de administración
admin_router = Router()
admin_router.message.middleware(AdminAuthMiddleware())  # Protege todos los handlers de mensajes
admin_router.callback_query.middleware(AdminAuthMiddleware())  # Protege callbacks

# Aplicar middleware de base de datos al dispatcher para inyectar sesiones
dispatcher.update.middleware(DatabaseMiddleware())

# Handler que recibe la sesión automáticamente gracias al middleware
@admin_router.message(Command("admin_command"))
async def admin_handler(message: Message, session: AsyncSession):
    # La sesión está disponible automáticamente gracias al DatabaseMiddleware
    # Si el usuario no es admin, este handler no se ejecuta gracias al AdminAuthMiddleware
    await message.answer("Comando de administrador ejecutado correctamente")
```

**Ejemplo de validación de permisos de administrador:**
```python
# El middleware AdminAuthMiddleware se encarga de validar automáticamente
# Si el usuario no es admin, envía un mensaje de error y no ejecuta el handler
# Configuración en config.py:
# ADMIN_USER_IDS = [123456789, 987654321]  # Lista de IDs de administradores
```

**Ejemplo de inyección automática de sesiones de base de datos:**
```python
# El middleware DatabaseMiddleware inyecta la sesión automáticamente
# No es necesario abrir/cerrar conexiones manualmente
async def handler_con_bd(message: Message, session: AsyncSession):
    # Usar la sesión inyectada para operaciones de base de datos
    result = await session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()

    if user:
        await message.answer(f"Usuario encontrado: {user.name}")
    else:
        await message.answer("Usuario no encontrado")
```

### FSM States (T11)
Implementación de Finite State Machine (FSM) para manejar flujos interactivos con múltiples pasos:

- **Admin States:** Estados para flujos de administración como configuración de canales y envío de publicaciones
- **User States:** Estados para flujos de usuarios como canje de tokens VIP y solicitud de acceso Free
- **Storage:** MemoryStorage para mantener estados en memoria (ligero para Termux)
- **Flujos implementados:**
  - Configuración de canales VIP y Free (extracción de IDs de canales)
  - Configuración de tiempo de espera del canal Free
  - Envío de publicaciones a canales (broadcast)
  - Canje de tokens VIP
  - Solicitud de acceso Free

### Pricing System (T28)
Sistema de gestión de planes de suscripción con precios, duración y monedas configurables:

- **Subscription Plans:** Creación de planes con nombre, duración en días y precio
- **Plan Management:** CRUD completo de planes de suscripción (crear, listar, actualizar, activar/desactivar)
- **Currency Support:** Configuración de símbolo de moneda por plan (USD, EUR, etc.)
- **Integration with Tokens:** Tokens VIP generados asociados a planes específicos con información de precio y duración
- **Professional Deep Links:** Generación de deep links profesionales para distribución de tokens
- **Role Management:** Sistema de roles de usuario (FREE, VIP, ADMIN) con transiciones automáticas

**Documentación:** Ver `docs/PRICING_SYSTEM.md` para detalles completos del sistema de precios.

### User Roles System (T29)
Sistema de roles jerárquico para clasificar usuarios con diferentes permisos y funcionalidades:

- **Role Hierarchy:** FREE (default), VIP (suscriptores pagos), ADMIN (gestión del bot)
- **Automatic Transitions:** Cambios automáticos de rol basados en estado de suscripción
- **Permission Control:** Acceso diferenciado a funcionalidades según rol
- **Role Management:** Promoción y degradación de roles con registro de motivos
- **Integration with Pricing:** Usuarios VIP tienen acceso a planes de suscripción

**Documentación:** Ver `docs/USER_ROLES.md` para detalles completos del sistema de roles.

### Deep Links System (T30)
Sistema de deep links para activación automática de tokens VIP con formato profesional:

- **Professional Format:** Deep links con formato `https://t.me/botname?start=TOKEN`
- **Automatic Activation:** Activación automática de suscripciones al hacer click en el enlace
- **Token Integration:** Deep links generados asociados a planes de suscripción específicos
- **User Experience:** Proceso simplificado de activación sin pasos manuales
- **Link Distribution:** Fácil distribución de enlaces para activación de suscripciones

**Documentación:** Ver `docs/DEEP_LINKS.md` para detalles completos del sistema de deep links.

**Ejemplo de uso de estados FSM:**
```python
from aiogram.fsm.context import FSMContext
from bot.states.admin import ChannelSetupStates

# Handler que inicia un flujo FSM
@admin_router.message(Command("setup_vip_channel"))
async def setup_vip_channel_start(message: Message, state: FSMContext):
    await message.answer("Por favor, reenvía un mensaje del canal VIP para extraer su ID:")
    await state.set_state(ChannelSetupStates.waiting_for_vip_channel)

# Handler que procesa el siguiente paso del flujo FSM
@admin_router.message(ChannelSetupStates.waiting_for_vip_channel, F.forward_from_chat)
async def process_vip_channel(message: Message, state: FSMContext):
    channel_id = str(message.forward_from_chat.id)

    # Aquí se procesaría la configuración del canal
    await message.answer(f"Canal VIP configurado con ID: {channel_id}")
    await state.clear()  # Limpiar estado al finalizar flujo

# Handler para manejar entradas inválidas durante el flujo FSM
@admin_router.message(ChannelSetupStates.waiting_for_vip_channel)
async def invalid_vip_channel(message: Message):
    await message.answer("Por favor, reenvía un mensaje del canal VIP (no un mensaje normal).")
```

**Estados Admin disponibles:**
- `ChannelSetupStates`: Configuración de canales VIP y Free
- `WaitTimeSetupStates`: Configuración de tiempo de espera del canal Free
- `BroadcastStates`: Envío de publicaciones a canales

**Estados User disponibles:**
- `TokenRedemptionStates`: Canje de tokens VIP
- `FreeAccessStates`: Solicitud de acceso Free
```

### Admin Handler (T12)
Handler del comando /admin que muestra el menú principal de administración con navegación, verificación de estado de configuración y teclado inline:

- **Navegación del menú principal:** Permite navegar entre diferentes secciones de administración con estado de configuración
- **Aplicación de middlewares:** Utiliza AdminAuthMiddleware y DatabaseMiddleware para protección y acceso a base de datos
- **Verificación de estado de configuración:** Muestra estado actual de configuración del bot (completo o incompleto)
- **Callback handlers:** Implementa manejadores de callback para navegación entre menús
- **Teclado inline:** Proporciona opciones de administración a través de teclado inline

**Ejemplo de uso del handler admin:**
```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import AdminAuthMiddleware, DatabaseMiddleware
from bot.utils.keyboards import admin_main_menu_keyboard, back_to_main_menu_keyboard
from bot.services.container import ServiceContainer

# Router para handlers de admin
admin_router = Router(name="admin")

# Aplicar middlewares (orden correcto: Database primero, AdminAuth después)
admin_router.message.middleware(DatabaseMiddleware())
admin_router.message.middleware(AdminAuthMiddleware())
admin_router.callback_query.middleware(DatabaseMiddleware())
admin_router.callback_query.middleware(AdminAuthMiddleware())

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession):
    """
    Handler del comando /admin.

    Muestra el menú principal de administración con estado de configuración.
    """
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

@admin_router.callback_query(F.data == "admin:main")
async def callback_admin_main(callback: CallbackQuery, session: AsyncSession):
    """
    Handler del callback para volver al menú principal.
    """
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

### VIP and Free Handlers (T13)
Handlers para la gestión de canales VIP y Free con funcionalidades completas de configuración y administración:

- **Submenú VIP:** Gestión del canal VIP con generación de tokens de invitación
- **Configuración del canal VIP:** Configuración del canal VIP por reenvío de mensajes
- **Generación de tokens de invitación:** Creación de tokens VIP con duración configurable
- **Submenú Free:** Gestión del canal Free con configuración de tiempo de espera
- **Configuración del canal Free:** Configuración del canal Free por reenvío de mensajes
- **Configuración de tiempo de espera:** Configuración de tiempo de espera para acceso Free

### User Handler (T14)
Handler del comando /start que detecta el rol del usuario y proporciona flujos para canje de tokens VIP y solicitud de acceso Free:

- **Handler /start:** Punto de entrada para usuarios con detección de rol (admin/VIP/usuario)
- **Flujo VIP:** Canje de tokens VIP con validación y generación de invite links
- **Flujo Free:** Solicitud de acceso Free con tiempo de espera y notificaciones automáticas
- **Middleware de base de datos:** Inyección de sesiones sin autenticación de admin
- **FSM para validación de tokens:** Estados para manejo de entrada de tokens
- **Validación de configuración:** Verificación de canales configurados antes de procesar

### Stats Handler (T19)
Handlers del panel de estadísticas que proporcionan métricas generales y detalladas sobre el sistema, incluyendo suscriptores VIP, solicitudes Free y tokens de invitación, con funcionalidades de caching y actualización manual:

- **Dashboard general:** Visualización de métricas generales del sistema (VIP, Free, Tokens)
- **Estadísticas VIP detalladas:** Métricas sobre suscriptores VIP (activos, expirados, próximos a expirar)
- **Estadísticas Free detalladas:** Métricas sobre solicitudes Free (pendientes, procesadas, tiempos de espera)
- **Estadísticas de tokens:** Métricas sobre tokens de invitación (generados, usados, expirados, tasa de conversión)
- **Sistema de cache:** Implementación de cache con TTL de 5 minutos para optimizar performance
- **Actualización manual:** Posibilidad de forzar recálculo de estadísticas ignorando el cache
- **Formato visual:** Mensajes HTML formateados con iconos y estructura clara
- **Proyecciones de ingresos:** Cálculo de ingresos proyectados mensuales y anuales basados en suscriptores activos

**Ejemplo de uso del handler de estadísticas:**
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.container import ServiceContainer
from bot.utils.keyboards import stats_menu_keyboard, back_to_main_menu_keyboard

# Router para handlers de admin (ya incluye stats handlers)
admin_router = Router(name="admin")

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

# Otros handlers para estadísticas detalladas:
# - callback_stats_vip: Estadísticas VIP detalladas
# - callback_stats_free: Estadísticas Free detalladas
# - callback_stats_tokens: Estadísticas de tokens
# - callback_stats_refresh: Actualización manual de estadísticas
```

### Background Tasks (T15)
Tareas programadas automáticas que realizan operaciones periódicas para mantener el sistema funcionando correctamente:

- **Expulsión de VIPs expirados:** Tarea que marca como expirados y expulsa del canal a los suscriptores VIP cuya fecha pasó
- **Procesamiento de cola Free:** Tarea que busca solicitudes que cumplieron el tiempo de espera y envía invite links a los usuarios
- **Limpieza de datos antiguos:** Tarea que elimina solicitudes Free procesadas hace más de 30 días
- **Scheduler con tareas programadas:** Configuración del scheduler APScheduler con intervalos configurables
- **Configuración de intervalos:** Configuración de frecuencias de ejecución mediante variables de entorno
- **Manejo de errores:** Control de errores en todas las tareas con logging apropiado

### Daily Gift System (T25)
Sistema de regalo diario que permite a los usuarios reclamar besitos diariamente manteniendo rachas de días consecutivos:

- **Reclamación diaria:** Usuarios pueden reclamar un regalo diario con un monto configurable de besitos
- **Sistema de rachas:** Mantiene registro de días consecutivos de reclamación con récords personales
- **Configuración flexible:** Administradores pueden configurar cantidad de besitos y habilitar/deshabilitar el sistema
- **Integración con gamificación:** Los besitos recibidos se integran con el sistema de economía de gamificación
- **Validación de horarios:** Sistema considera zona horaria de Ciudad de México para cálculo de días
- **Seguimiento de progreso:** Registro de total de reclamos y rachas máximas por usuario

### Dynamic Menu Configuration (T28)
Sistema que permite a los administradores configurar dinámicamente los menús visibles para usuarios:

- **Configuración por rol:** Diferencia entre menús VIP y FREE
- **Botones personalizables:** Texto, emojis, acciones configurables por admin
- **Tipos de acción:** Soporta información, URLs, callbacks y contactos
- **Ordenamiento flexible:** Control sobre posición y agrupación de botones
- **Activación/desactivación:** Control granular sobre visibilidad de botones
- **Integración con usuarios:** Menús se generan dinámicamente según rol del usuario

### Narrative Module (T35)
Sistema de historias interactivas con decisiones del usuario, requisitos de acceso y tracking de progreso:

- **Capítulos y fragmentos narrativos:** Estructura modular para contenido narrativo
- **Decisiones del usuario:** Ramificaciones narrativas basadas en elecciones del usuario
- **Requisitos de acceso:** Control de acceso basado en VIP, besitos o arquetipo
- **Tracking de progreso:** Registro del avance del usuario en la narrativa
- **Detección de arquetipos:** Análisis de patrones de decisión para identificar tipo de usuario
- **Integración con gamificación:** Recompensas y misiones vinculadas a la narrativa
- **Sistema de recompensas:** Besitos, misiones y niveles por completar fragmentos

**Ejemplo de uso de las background tasks:**
```python
from aiogram import Bot
from bot.background.tasks import start_background_tasks, stop_background_tasks

# Iniciar tareas programadas al inicio del bot
async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    # ... otras inicializaciones ...

    # Iniciar background tasks
    start_background_tasks(bot)

# Detener tareas programadas al apagar el bot
async def on_shutdown(bot: Bot, dispatcher: Dispatcher) -> None:
    # Detener background tasks
    stop_background_tasks()

    # ... otras tareas de cierre ...

# Configuración de intervalos en config.py:
# CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "60"))  # Expulsión VIPs
# PROCESS_FREE_QUEUE_MINUTES = int(os.getenv("PROCESS_FREE_QUEUE_MINUTES", "5"))  # Procesamiento Free
```

**Tareas programadas configuradas:**
- `expire_and_kick_vip_subscribers`: Cada 60 minutos (configurable) - Expulsa VIPs expirados del canal
- `process_free_queue`: Cada 5 minutos (configurable) - Procesa solicitudes Free que cumplieron tiempo de espera
- `cleanup_old_data`: Diariamente a las 3 AM UTC - Limpia datos antiguos de solicitudes Free
```

**Ejemplo de uso del handler User:**
```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.utils.keyboards import create_inline_keyboard
from bot.services.container import ServiceContainer
from bot.states.user import TokenRedemptionStates
from config import Config

# Router para handlers de usuario
user_router = Router(name="user")

# Aplicar middleware de database (NO AdminAuth, estos son usuarios normales)
user_router.message.middleware(DatabaseMiddleware())
user_router.callback_query.middleware(DatabaseMiddleware())

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

# Flujo de canje de token VIP
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

# Flujo de solicitud Free
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

# Cancelar flujo
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

**Ejemplo de uso de los handlers VIP y Free:**
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import ChannelSetupStates, WaitTimeSetupStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

# Submenú VIP
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

@admin_router.callback_query(F.data == "admin:vip")
async def callback_vip_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el submenú de gestión VIP.

    Args:
        callback: Callback query
        session: Sesión de BD (inyectada por middleware)
    """
    logger.debug(f"📺 Usuario {callback.from_user.id} abrió menú VIP")

    container = ServiceContainer(session, callback.bot)

    # Verificar si canal VIP está configurado
    is_configured = await container.channel.is_vip_channel_configured()

    if is_configured:
        vip_channel_id = await container.channel.get_vip_channel_id()

        # Obtener info del canal
        channel_info = await container.channel.get_channel_info(vip_channel_id)
        channel_name = channel_info.title if channel_info else "Canal VIP"

        text = (
            f"📺 <b>Gestión Canal VIP</b>\n\n"
            f"✅ Canal configurado: <b>{channel_name}</b>\n"
            f"ID: <code>{vip_channel_id}</code>\n\n"
            f"Selecciona una opción:"
        )
    else:
        text = (
            "📺 <b>Gestión Canal VIP</b>\n\n"
            "⚠️ Canal VIP no configurado\n\n"
            "Configura el canal para comenzar a generar tokens de invitación."
        )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=vip_menu_keyboard(is_configured),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje VIP: {e}")

    await callback.answer()

# Configuración del canal VIP
@admin_router.callback_query(F.data == "vip:setup")
async def callback_vip_setup(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el proceso de configuración del canal VIP.

    Entra en estado FSM esperando que el admin reenvíe un mensaje del canal.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} iniciando setup VIP")

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

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard([
                [{"text": "❌ Cancelar", "callback_data": "admin:vip"}]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje setup VIP: {e}")

    await callback.answer()

# Procesamiento del reenvío para configuración del canal VIP
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

# Generación de tokens VIP
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

# Submenú Free
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

@admin_router.callback_query(F.data == "admin:free")
async def callback_free_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el submenú de gestión Free.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.debug(f"📺 Usuario {callback.from_user.id} abrió menú Free")

    container = ServiceContainer(session, callback.bot)

    # Verificar si canal Free está configurado
    is_configured = await container.channel.is_free_channel_configured()

    if is_configured:
        free_channel_id = await container.channel.get_free_channel_id()
        wait_time = await container.config.get_wait_time()

        # Obtener info del canal
        channel_info = await container.channel.get_channel_info(free_channel_id)
        channel_name = channel_info.title if channel_info else "Canal Free"

        text = (
            f"📺 <b>Gestión Canal Free</b>\n\n"
            f"✅ Canal configurado: <b>{channel_name}</b>\n"
            f"ID: <code>{free_channel_id}</code>\n\n"
            f"⏱️ Tiempo de espera: <b>{wait_time} minutos</b>\n\n"
            f"Selecciona una opción:"
        )
    else:
        text = (
            "📺 <b>Gestión Canal Free</b>\n\n"
            "⚠️ Canal Free no configurado\n\n"
            "Configura el canal para que usuarios puedan solicitar acceso."
        )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=free_menu_keyboard(is_configured),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error editando mensaje Free: {e}")

    await callback.answer()

# Configuración del canal Free
@admin_router.callback_query(F.data == "free:setup")
async def callback_free_setup(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    """
    Inicia el proceso de configuración del canal Free.

    Args:
        callback: Callback query
        session: Sesión de BD
        state: FSM context
    """
    logger.info(f"⚙️ Usuario {callback.from_user.id} iniciando setup Free")

    # Entrar en estado FSM
    await state.set_state(ChannelSetupStates.waiting_for_free_channel)

    text = (
        "⚙️ <b>Configurar Canal Free</b>\n\n"
        "Para configurar el canal Free:\n\n"
        "1️⃣ Vayas al canal Free\n"
        "2️⃣ Reenvíes cualquier mensaje del canal a este chat\n"
        "3️⃣ Yo extraeré el ID automáticamente\n\n"
        "⚠️ <b>Importante:</b>\n"
        "- El bot debe ser administrador del canal\n"
        "- El bot debe tener permiso para invitar usuarios\n\n"
        "👉 Reenvía un mensaje del canal ahora..."
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
            logger.error(f"Error editando mensaje setup Free: {e}")

    await callback.answer()

# Procesamiento del reenvío para configuración del canal Free
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

# Configuración de tiempo de espera
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

# Procesamiento del tiempo de espera
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

## 🧪 Testing

El proyecto incluye suite completa de tests E2E e integración para validar funcionalidad.

### Instalar Dependencias de Testing

```bash
# Instalar pytest y pytest-asyncio
pip install pytest==7.4.3 pytest-asyncio==0.21.1 --break-system-packages
```

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Solo tests E2E
pytest tests/test_e2e_flows.py -v

# Solo tests de integracion
pytest tests/test_integration.py -v

# Test especifico
pytest tests/test_e2e_flows.py::test_vip_flow_complete -v

# Script helper (limpia BD y ejecuta tests)
bash scripts/run_tests.sh
```

### Tests Disponibles

**End-to-End (E2E):**
- `test_vip_flow_complete` - Flujo VIP completo (generar token → canjear → acceso)
- `test_free_flow_complete` - Flujo Free completo (solicitar → esperar → acceso)
- `test_vip_expiration` - Expiracion automatica de VIP
- `test_token_validation_edge_cases` - Validacion de tokens (casos edge)
- `test_duplicate_free_request_prevention` - Prevencion de solicitudes duplicadas

**Integracion:**
- `test_service_container_lazy_loading` - Lazy loading de servicios
- `test_config_service_singleton` - BotConfig como singleton
- `test_database_session_management` - Manejo de sesiones de BD
- `test_error_handling_across_services` - Error handling entre servicios

Ver `tests/README.md` para documentacion completa.

## 🔧 Desarrollo

Este proyecto está en desarrollo iterativo. Consulta las tareas completadas:
- [x] T6: Service Container - Contenedor de servicios con patrón DI + Lazy Loading para reducir consumo de memoria en Termux
- [x] T7: Subscription Service - Gestión completa de suscripciones VIP (tokens, validación, canjes) y cola de acceso Free
- [x] T8: Channel Service - Gestión completa de canales VIP y Free con verificación de permisos y envío de publicaciones
- [x] T9: Config Service - Gestión de configuración global del bot, tiempos de espera, reacciones y tarifas
- [x] T10: Middlewares - Implementación de AdminAuthMiddleware y DatabaseMiddleware para autenticación de administradores e inyección automática de sesiones de base de datos
- [x] T11: FSM States - Implementación de estados FSM para administradores y usuarios para flujos de configuración y canje de tokens
- [x] T12: Handler /admin (Menú Principal) - Handler del comando /admin que muestra el menú principal de administración con navegación, verificación de estado de configuración y teclado inline
- [x] T13: Handlers VIP y Free - Submenú VIP (gestión del canal VIP con generación de tokens de invitación), Configuración del canal VIP (configuración del canal VIP por reenvío de mensajes), Generación de tokens de invitación (creación de tokens VIP con duración configurable), Submenú Free (gestión del canal Free con configuración de tiempo de espera), Configuración del canal Free (configuración del canal Free por reenvío de mensajes), Configuración de tiempo de espera (configuración de tiempo de espera para acceso Free)
- [x] T14: Handlers User (/start, flujos) - Handler /start con detección de rol (admin/VIP/usuario), Flujo VIP (canje de tokens VIP con validación y generación de invite links), Flujo Free (solicitud de acceso Free con tiempo de espera y notificaciones automáticas), Middleware de base de datos (inyección de sesiones sin autenticación de admin), FSM para validación de tokens (estados para manejo de entrada de tokens), Validación de configuración (verificación de canales configurados antes de procesar)
- [x] T15: Background Tasks - Tareas programadas que expulsan VIPs expirados del canal, procesan la cola Free para enviar invite links a usuarios que completaron tiempo de espera, limpian datos antiguos y usan APScheduler con configuración de intervalos mediante variables de entorno
- [x] T19: Stats Handler - Panel de estadísticas que proporciona métricas generales y detalladas sobre el sistema (VIP, Free, Tokens), con sistema de cache y actualización manual
- [x] T24: Pagination System - Sistema de paginación reutilizable con clase Paginator genérica, teclado de navegación paginado y formateadores de contenido para listas largas de elementos
- [x] T25: Paginated VIP Subscriber Management - Gestión paginada de suscriptores VIP con listado, filtrado por estado (activos, expirados, próximos a expirar, todos), vistas detalladas y expulsión manual de suscriptores
- [x] T26: Free Queue Visualization - Visualización paginada de cola de solicitudes Free con filtrado por estado (pendientes, listas para procesar, procesadas, todas) y monitoreo del tiempo de espera configurado
- [x] T27: Complete Status Dashboard - Panel de control completo del sistema con health checks, configuración, estadísticas clave, tareas en segundo plano y acciones rápidas
- [ ] ONDA 1: MVP Funcional (T1-T17)
- [ ] ONDA 2: Features Avanzadas (T18-T33)
- [ ] ONDA 3: Optimización (T34-T44)

## 📝 Licencia

MIT License
