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

## 🔧 Desarrollo

Este proyecto está en desarrollo iterativo. Consulta las tareas completadas:
- [x] T6: Service Container - Contenedor de servicios con patrón DI + Lazy Loading para reducir consumo de memoria en Termux
- [x] T7: Subscription Service - Gestión completa de suscripciones VIP (tokens, validación, canjes) y cola de acceso Free
- [x] T8: Channel Service - Gestión completa de canales VIP y Free con verificación de permisos y envío de publicaciones
- [x] T9: Config Service - Gestión de configuración global del bot, tiempos de espera, reacciones y tarifas
- [x] T10: Middlewares - Implementación de AdminAuthMiddleware y DatabaseMiddleware para autenticación de administradores e inyección automática de sesiones de base de datos
- [ ] ONDA 1: MVP Funcional (T1-T17)
- [ ] ONDA 2: Features Avanzadas (T18-T33)
- [ ] ONDA 3: Optimización (T34-T44)

## 📝 Licencia

MIT License
