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

**Ejemplo de uso del Service Container:**
```python
container = ServiceContainer(session, bot)

# Primera vez: carga el servicio (lazy loading)
token = await container.subscription.generate_token(...)

# Segunda vez: reutiliza instancia ya cargada
result = await container.subscription.validate_token(...)

# Uso del servicio de canales
success, message = await container.channel.setup_vip_channel("-1001234567890")
is_valid, perm_message = await container.channel.verify_bot_permissions("-1001234567890")
sent_success, sent_message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="Publicación VIP",
    photo="photo_file_id"
)

# Uso del servicio de configuración
config = await container.config.get_config()
wait_time = await container.config.get_wait_time()
await container.config.set_wait_time(10)  # 10 minutos de espera
await container.config.set_vip_reactions(["👍", "❤️", "🔥"])
await container.config.set_subscription_fees({"monthly": 10, "yearly": 100})
is_configured = await container.config.is_fully_configured()
summary = await container.config.get_config_summary()
```

## 🔧 Desarrollo

Este proyecto está en desarrollo iterativo. Consulta las tareas completadas:
- [x] T6: Service Container - Contenedor de servicios con patrón DI + Lazy Loading para reducir consumo de memoria en Termux
- [x] T7: Subscription Service - Gestión completa de suscripciones VIP (tokens, validación, canjes) y cola de acceso Free
- [x] T8: Channel Service - Gestión completa de canales VIP y Free con verificación de permisos y envío de publicaciones
- [x] T9: Config Service - Gestión de configuración global del bot, tiempos de espera, reacciones y tarifas
- [ ] ONDA 1: MVP Funcional (T1-T17)
- [ ] ONDA 2: Features Avanzadas (T18-T33)
- [ ] ONDA 3: Optimización (T34-T44)

## 📝 Licencia

MIT License
