# Guía de Instalación y Configuración

Instrucciones paso a paso para instalar, configurar y ejecutar el bot en Termux o Linux.

## Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes Python)
- Conexión a Internet
- Token de Telegram Bot (obtenido de @BotFather)
- User ID de Telegram (obtenido de @userinfobot)

## Instalación en Termux (Android)

### Paso 1: Actualizar Termux

```bash
pkg update && pkg upgrade
```

### Paso 2: Instalar Python

```bash
pkg install python
```

Verifica la versión:
```bash
python --version
```

Debe mostrar Python 3.11 o superior.

### Paso 3: Crear Directorio del Proyecto

```bash
mkdir ~/telegram_vip_bot
cd ~/telegram_vip_bot
```

O si ya clonaste el repositorio:
```bash
cd ~/repos/c1
```

### Paso 4: Crear Entorno Virtual (Recomendado)

```bash
python -m venv venv
source venv/bin/activate
```

Para desactivar el entorno:
```bash
deactivate
```

### Paso 5: Instalar Dependencias

```bash
pip install -r requirements.txt --break-system-packages
```

**Nota:** En Termux, a veces requiere `--break-system-packages` debido a restricciones de packaging.

Verifica la instalación:
```bash
pip list
```

Debe mostrar:
- aiogram (3.4.1)
- sqlalchemy (2.0.25)
- aiosqlite (0.19.0)
- APScheduler (3.10.4)
- python-dotenv (1.0.0)

## Instalación en Linux/Ubuntu

### Paso 1: Instalar Python

```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip
```

### Paso 2: Crear Directorio y Entorno Virtual

```bash
mkdir ~/telegram_vip_bot
cd ~/telegram_vip_bot
python3.11 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

## Configuración del Bot

### Paso 1: Obtener Token de Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Sigue las instrucciones (nombre del bot, username)
4. Copia el token generado (formato: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

Guarda el token de forma segura.

### Paso 2: Obtener tu User ID

1. Abre Telegram y busca **@userinfobot**
2. Enviále cualquier mensaje
3. Te responderá con tu User ID (número grande, ej: 123456789)

### Paso 3: Crear Archivo .env

Copia el template:
```bash
cp .env.example .env
```

Edita el archivo .env:

**En Termux:**
```bash
nano .env
```

**En Linux:**
```bash
nano .env
# o
vim .env
# o tu editor favorito
```

Llena los valores:
```env
# Telegram Bot Configuration
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_USER_IDS=123456789,987654321

# Database
DATABASE_URL=sqlite+aiosqlite:///bot.db

# Channels (se configuran desde el bot después)
VIP_CHANNEL_ID=
FREE_CHANNEL_ID=

# Bot Settings
DEFAULT_WAIT_TIME_MINUTES=5
LOG_LEVEL=INFO
```

**Detalles de configuración:**

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `BOT_TOKEN` | Token obtenido de @BotFather | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `ADMIN_USER_IDS` | Comma-separated list de user IDs con permisos admin | `123456789,987654321,555555555` |
| `DATABASE_URL` | URL de conexión a la base de datos (SQLite local) | `sqlite+aiosqlite:///bot.db` |
| `VIP_CHANNEL_ID` | ID del canal VIP (se configura desde el bot) | (dejar vacío inicialmente) |
| `FREE_CHANNEL_ID` | ID del canal Free (se configura desde el bot) | (dejar vacío inicialmente) |
| `DEFAULT_WAIT_TIME_MINUTES` | Minutos de espera para acceso Free | `5` |
| `LOG_LEVEL` | Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |

### Paso 4: Verificar Configuración

Ejecuta el bot para verificar que la configuración es correcta:

```bash
python main.py
```

Debe mostrar:
```
2025-12-11 10:30:45,123 - config - INFO - Logging configurado: nivel INFO
2025-12-11 10:30:45,456 - main - INFO - 🚀 Iniciando bot...
2025-12-11 10:30:46,789 - config - INFO - ✅ 1 admin(s) configurado(s)
2025-12-11 10:30:46,901 - config - INFO - ✅ Configuración validada correctamente
2025-12-11 10:30:47,012 - engine - INFO - 🔧 Inicializando base de datos...
2025-12-11 10:30:47,234 - engine - INFO - ✅ SQLite configurado (WAL mode, cache 64MB)
2025-12-11 10:30:47,345 - engine - INFO - ✅ Tablas creadas/verificadas
2025-12-11 10:30:47,456 - engine - INFO - ✅ BotConfig inicial creado
2025-12-11 10:30:47,567 - engine - INFO - ✅ Base de datos inicializada correctamente
2025-12-11 10:30:48,678 - main - INFO - 🔄 Iniciando polling...
```

Si todo está bien, deberías recibir un mensaje en Telegram del bot. Si hay errores:
- Verifica el BOT_TOKEN en .env
- Verifica que tienes usuario ID en ADMIN_USER_IDS
- Revisa los logs para mensajes de error específicos

Presiona **Ctrl+C** para detener el bot.

## Ejecución del Bot

### Ejecución Manual

```bash
python main.py
```

El bot estará activo mientras la terminal esté abierta.

### Ejecución en Background (Termux)

Para que el bot siga ejecutándose cuando cierres Termux:

```bash
nohup python main.py > bot.log 2>&1 &
```

Esto:
- `nohup` - Ignora señal de desconexión
- `> bot.log` - Redirige stdout a archivo
- `2>&1` - Redirige stderr a stdout
- `&` - Ejecuta en background

Para ver los logs:
```bash
tail -f bot.log
```

Para detener el bot:
```bash
pkill -f "python main.py"
```

### Ejecución en Background (Linux con systemd)

Crea archivo `/etc/systemd/system/telegram-vip-bot.service`:

```ini
[Unit]
Description=Telegram VIP/Free Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/telegram_vip_bot
ExecStart=/home/your_username/telegram_vip_bot/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/your_username/telegram_vip_bot/bot.log
StandardError=append:/home/your_username/telegram_vip_bot/bot.log

[Install]
WantedBy=multi-user.target
```

Reemplaza `your_username` con tu usuario.

Luego:
```bash
# Recargar systemd
sudo systemctl daemon-reload

# Iniciar el servicio
sudo systemctl start telegram-vip-bot

# Habilitar auto-start al reiniciar
sudo systemctl enable telegram-vip-bot

# Ver status
sudo systemctl status telegram-vip-bot

# Ver logs
sudo journalctl -u telegram-vip-bot -f
```

### Ejecución con Docker (Futuro)

En ONDA 2+, se proporcionará Dockerfile para containerizar el bot.

## Estructura de Directorios Después de Setup

```
telegram_vip_bot/
├── bot/                              # Código del bot
│   ├── __init__.py
│   ├── database/
│   │   ├── base.py
│   │   ├── engine.py
│   │   └── models.py
│   ├── services/                     # (vacío en MVP)
│   ├── handlers/                     # (vacío en MVP)
│   ├── middlewares/                  # (vacío en MVP)
│   ├── states/                       # (vacío en MVP)
│   ├── utils/                        # (vacío en MVP)
│   └── background/                   # (vacío en MVP)
├── docs/                             # Documentación
├── .env                              # Variables de entorno (NO commitear)
├── .env.example                      # Template
├── .gitignore
├── main.py                           # Entry point
├── config.py                         # Configuración
├── requirements.txt                  # Dependencias
├── bot.db                            # Base de datos (generado)
├── bot.log                           # Logs (si ejecutas en background)
└── venv/                             # Entorno virtual (opcional)
```

## Troubleshooting

### Error: "BOT_TOKEN no configurado"

**Problema:** El token de Telegram no está en .env

**Solución:**
1. Obtén el token de @BotFather en Telegram
2. Abre .env y asegúrate de que `BOT_TOKEN` está configurado
3. Reinicia el bot

### Error: "ADMIN_USER_IDS no configurado o inválido"

**Problema:** No hay IDs de admin configurados

**Solución:**
1. Obtén tu User ID desde @userinfobot
2. Abre .env y configura `ADMIN_USER_IDS=tu_id_aqui`
3. Si hay múltiples admins, sepáralos por comas: `ADMIN_USER_IDS=123,456,789`
4. Reinicia el bot

### Error: "Database engine no inicializado"

**Problema:** El engine de base de datos no se inicializó correctamente

**Solución:**
1. Verifica que el directorio existe y tienes permisos de escritura
2. Borra `bot.db` si existe (se regenerará)
3. Verifica `DATABASE_URL` en .env es correcto
4. Reinicia el bot

### Error: "Connection refused" en Termux

**Problema:** Posible timeout de red o problema de conexión

**Soluciones:**
1. Verifica que tienes conexión a Internet
2. Aumenta el timeout en engine.py (ya está en 30s)
3. Intenta reiniciar Termux
4. Verifica que el BOT_TOKEN es válido

### El bot no recibe mensajes

**Problema:** El bot está ejecutándose pero no responde

**Soluciones:**
1. Verifica que el token es correcto (intenta obtener uno nuevo de @BotFather)
2. Asegúrate de que no hay otro bot con el mismo token ejecutándose
3. Reinicia el bot
4. Verifica los logs para mensajes de error

### Error de permisos en Termux

**Problema:** `Permission denied` al ejecutar `pip install`

**Solución:**
```bash
pip install -r requirements.txt --break-system-packages
```

### Base de datos corrupta

**Problema:** Errores de integridad en base de datos

**Solución:**
1. Detén el bot
2. Borra `bot.db`
3. Reinicia el bot (se crea nueva BD)

## Seguridad

### Protege tu .env

El archivo `.env` contiene información sensible:
- **BOT_TOKEN** - Controla acceso al bot
- **ADMIN_USER_IDS** - Define permisos

**Nunca:**
- Commitees .env a Git
- Compartas .env públicamente
- Expongas el token en logs

**Siempre:**
- Usa `.gitignore` para excluir .env (ya incluido)
- Regenera token si sospechas que fue expuesto
- Usa variables de entorno en producción

### Regenerar Token Si Es Comprometido

1. Abre Telegram y busca @BotFather
2. Envía `/mybots` → Selecciona tu bot → `/revoke`
3. Genera un token nuevo
4. Actualiza .env con el nuevo token
5. Reinicia el bot

## Próximos Pasos

Después de configurar el bot:

1. Lee [ARCHITECTURE.md](./ARCHITECTURE.md) para entender la estructura
2. Lee [DATABASE.md](./DATABASE.md) para conocer los modelos de datos
3. Espera Fase 1.2 para funcionalidades de admin
4. Consulta [COMMANDS.md](./COMMANDS.md) para ver comandos disponibles

## Soporte

Si encuentras problemas:
1. Revisa los logs: `tail -f bot.log` (si ejecutas en background)
2. Verifica [MAINTENANCE.md](./MAINTENANCE.md) para troubleshooting
3. Revisa [README.md](../README.md) para más información

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
