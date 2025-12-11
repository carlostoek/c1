# Guía de Mantenimiento y Troubleshooting

Procedimientos de mantenimiento, recuperación de errores y resolución de problemas.

## Logs y Monitoreo

### Ver Logs en Tiempo Real

**En background (Termux):**
```bash
tail -f bot.log
```

**En systemd (Linux):**
```bash
sudo journalctl -u telegram-vip-bot -f
```

### Niveles de Log

```
DEBUG   - Información de debug (queries, variables)
INFO    - Eventos importantes (startup, token creado)
WARNING - Problemas no críticos (token no encontrado)
ERROR   - Fallos (error de BD)
CRITICAL - Bot no operativo
```

### Cambiar Log Level

En .env:
```env
LOG_LEVEL=DEBUG   # Para desarrollo
LOG_LEVEL=INFO    # Para producción
```

Reinicia el bot para aplicar cambios.

## Problemas Comunes

### El bot no responde a comandos

**Síntomas:**
- Bot recibe mensajes pero no responde
- Sin errores en logs

**Causas posibles:**
1. Handlers no registrados
2. Middleware bloqueando
3. Bot detenido
4. Problema de conexión

**Solución:**
```bash
# 1. Verificar que bot está corriendo
ps aux | grep "python main.py"

# 2. Reiniciar bot
pkill -f "python main.py"
python main.py

# 3. Verificar BOT_TOKEN es válido
# Prueba un comando simple: /start
```

### "Database engine no inicializado"

**Error:** RuntimeError: Database engine no inicializado

**Causa:** init_db() no fue llamado o falló

**Solución:**
```python
# En main.py on_startup, asegúrate que init_db() se llama:
await init_db()
```

Verifica que no hay errores previos en el output del bot.

### "ADMIN_USER_IDS no configurado"

**Error:** ❌ ADMIN_USER_IDS no configurado o inválido en .env

**Causa:** Variable no está en .env o tiene formato incorrecto

**Solución:**
```env
# Correcto: números separados por comas, sin espacios
ADMIN_USER_IDS=123456789,987654321

# Incorrecto:
ADMIN_USER_IDS=123456789 987654321  # Espacio en lugar de coma
ADMIN_USER_IDS=                      # Vacío
```

Reinicia bot y verifica logs.

### "Token inválido" en login Telegram

**Síntoma:** Bot no se conecta a Telegram

**Causa:**
- Token es incorrecto
- Token fue revocado
- Bot fue eliminado

**Solución:**

1. Obtén nuevo token de @BotFather:
   - Abre Telegram
   - Busca @BotFather
   - Envía `/newbot` o `/mybots`
   - Selecciona tu bot
   - Envía `/revoke` para generar nuevo token

2. Actualiza .env:
   ```env
   BOT_TOKEN=nuevo_token_aqui
   ```

3. Reinicia bot

### Base de datos corrupta

**Síntomas:**
- Errores de SQL
- Inconsistencia de datos
- Queries retornan resultados raros

**Solución:**

```bash
# 1. Detener bot
pkill -f "python main.py"

# 2. Hacer backup
cp bot.db bot.db.corrupted.backup

# 3. Borrar DB (se recreará limpia)
rm bot.db

# 4. Reiniciar bot
python main.py
```

**Nota:** Se perderán todos los datos. Si necesitas recuperar:
- Restaurar desde backup anterior
- O usar script de recuperación (futuro)

### Error de permisos al escribir BD

**Error:** PermissionError: No se puede escribir bot.db

**Causa:** Permisos de directorio insuficientes

**Solución:**

```bash
# Verificar permisos
ls -la bot.db

# Cambiar a usuario actual
chown $USER:$USER bot.db

# O cambiar permisos
chmod 644 bot.db

# Para directorio
chmod 755 .
```

### Timeout de conexión a BD

**Error:** asyncio.TimeoutError al conectarse a BD

**Cause:** BD está muy ocupada (queries largas)

**Solución:**

1. Verifica si hay queries pesadas:
   ```python
   # En engine.py, aumentar timeout
   "timeout": 30  # Ya está en 30s
   ```

2. Optimizar queries (índices):
   - Verificar que índices están creados
   - No hacer queries sin WHERE innecesarias

3. Cerrar otras conexiones:
   ```bash
   # Ver procesos de DB
   lsof bot.db
   ```

## Mantenimiento Preventivo

### Backup Automático

**En Termux (manual):**
```bash
# Crear directorio backups
mkdir -p ~/backups

# Backup diario con timestamp
cp bot.db ~/backups/bot.db.$(date +%Y%m%d_%H%M%S).backup

# Guardar último 7 días
find ~/backups -name "*.backup" -mtime +7 -delete
```

**En Linux (con systemd timer):**

Archivo: `/etc/systemd/system/bot-backup.service`
```ini
[Unit]
Description=Telegram Bot Backup
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/home/your_username/telegram_vip_bot
ExecStart=/bin/bash -c 'cp bot.db backups/bot.db.$(date +\%Y\%m\%d_\%H\%M\%S).backup && find backups -name "*.backup" -mtime +7 -delete'
```

Archivo: `/etc/systemd/system/bot-backup.timer`
```ini
[Unit]
Description=Daily Bot Backup Timer

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bot-backup.timer
```

### Limpieza Periódica

**Background tasks** (ONDA 1.4+):
```python
@scheduler.scheduled_job('cron', hour=2, minute=0)
async def daily_cleanup():
    """Ejecuta limpieza diaria"""
    async with get_session() as session:
        service = SubscriptionService(session)

        # Marcar suscriptores como expirados
        count = await service.cleanup_expired_subscriptions()
        logger.info(f"Marcadas {count} suscriptores como expirados")

        # Eliminar tokens muy viejos (> 30 días)
        from sqlalchemy import delete
        old_date = datetime.utcnow() - timedelta(days=30)
        stmt = delete(InvitationToken).where(
            InvitationToken.created_at < old_date
        )
        result = await session.execute(stmt)
        logger.info(f"Eliminados {result.rowcount} tokens antiguos")
```

### Monitoreo de Recursos

**En Termux:**
```bash
# Ver uso de memoria del bot
ps aux | grep "python main.py"

# Ver tamaño de BD
ls -lh bot.db
du -sh .
```

**Alertar si:**
- bot.db > 500 MB (posible fuga de datos)
- Proceso Python > 100 MB (posible memory leak)
- Logs > 1 GB (rotación de logs)

### Rotación de Logs

**Crear script** `rotate_logs.sh`:
```bash
#!/bin/bash

LOG_FILE="/home/user/telegram_vip_bot/bot.log"
ARCHIVE_DIR="/home/user/telegram_vip_bot/logs_archive"

# Crear directorio si no existe
mkdir -p "$ARCHIVE_DIR"

# Comprimir log actual
gzip -c "$LOG_FILE" > "$ARCHIVE_DIR/bot.log.$(date +%Y%m%d_%H%M%S).gz"

# Limpiar log original
> "$LOG_FILE"

# Eliminar logs > 30 días
find "$ARCHIVE_DIR" -name "*.gz" -mtime +30 -delete

echo "Logs rotados"
```

**Agendar** con cron:
```bash
# Ejecutar cada día a las 3 AM
crontab -e
# Agregar:
0 3 * * * /home/user/telegram_vip_bot/rotate_logs.sh
```

## Diagnosticar Problemas

### Script de Diagnóstico

Crea `diagnose.py`:

```python
#!/usr/bin/env python3
import asyncio
import sys
from config import Config
from bot.database import init_db, close_db, get_session, BotConfig, InvitationToken
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose():
    """Diagnóstico completo del sistema"""
    print("=" * 50)
    print("DIAGNÓSTICO DEL BOT")
    print("=" * 50)

    # 1. Configuración
    print("\n1. CONFIGURACIÓN")
    print(f"   BOT_TOKEN: {'✓' if Config.BOT_TOKEN else '✗'}")
    print(f"   ADMIN_IDs: {'✓' if Config.ADMIN_USER_IDS else '✗'} ({len(Config.ADMIN_USER_IDS)})")
    print(f"   DATABASE_URL: {Config.DATABASE_URL}")
    print(f"   LOG_LEVEL: {Config.LOG_LEVEL}")

    # 2. Base de datos
    print("\n2. BASE DE DATOS")
    try:
        await init_db()
        print("   ✓ Conexión exitosa")

        async with get_session() as session:
            config = await session.get(BotConfig, 1)
            print(f"   ✓ BotConfig existe (id=1)")
            print(f"     Canal VIP: {config.vip_channel_id or 'NO CONFIGURADO'}")
            print(f"     Canal Free: {config.free_channel_id or 'NO CONFIGURADO'}")

            # Contar registros
            from sqlalchemy import select, func
            from bot.database import InvitationToken, VIPSubscriber, FreeChannelRequest

            for Model, name in [
                (InvitationToken, "Tokens"),
                (VIPSubscriber, "VIP Subscribers"),
                (FreeChannelRequest, "Free Requests")
            ]:
                query = select(func.count(Model.id))
                result = await session.execute(query)
                count = result.scalar()
                print(f"     {name}: {count}")

        await close_db()
    except Exception as e:
        print(f"   ✗ Error en BD: {e}")
        return False

    print("\n3. RESUMEN")
    print("   Sistema operativo")

    return True

if __name__ == "__main__":
    success = asyncio.run(diagnose())
    sys.exit(0 if success else 1)
```

Ejecutar:
```bash
python diagnose.py
```

## Recovery Procedures

### Restaurar desde Backup

```bash
# 1. Detener bot
pkill -f "python main.py"

# 2. Restaurar backup
cp backups/bot.db.20251210_020000.backup bot.db

# 3. Verificar
sqlite3 bot.db "SELECT COUNT(*) FROM bot_config;"

# 4. Reiniciar
python main.py
```

### Migrar a Nuevas Máquinas

```bash
# En máquina vieja:
cp bot.db ~/telegram_vip_bot.backup
cp .env ~/telegram_vip_bot.env

# Transferir a nueva máquina
scp ~/telegram_vip_bot.backup user@newhost:~/
scp ~/telegram_vip_bot.env user@newhost:~/

# En nueva máquina:
mv ~/telegram_vip_bot.backup bot.db
mv ~/telegram_vip_bot.env .env
python main.py
```

## Updating del Bot

### Actualizar Dependencias

```bash
# Ver versiones instaladas
pip list

# Ver versiones disponibles
pip list --outdated

# Actualizar una librería
pip install --upgrade aiogram

# Actualizar todas (cuidado!)
pip install --upgrade -r requirements.txt
```

### Actualizar Código

```bash
# Si usas Git
git pull origin main

# Ver cambios
git diff HEAD

# Reiniciar bot
pkill -f "python main.py"
python main.py
```

### Rollback si Falla

```bash
# Ir a versión anterior
git checkout HEAD~1

# O restaurar backup
cp bot.db.backup bot.db

# Reiniciar
python main.py
```

## Performance Tuning

### Analizar Queries Lentas

En `engine.py`, habilitar echo:

```python
_engine = create_async_engine(
    Config.DATABASE_URL,
    echo=True,  # IMPORTANTE: ver todas las queries
    ...
)
```

Ver qué queries son lentas en logs y optimizar.

### Índices

Agregar índices si notas queries lentas:

```python
# En models.py
class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(...)

    # Índice compuesto
    __table_args__ = (
        Index('idx_custom', 'col1', 'col2'),
    )
```

Recrear BD:
```bash
rm bot.db
python main.py  # Recreará con nuevos índices
```

## Checklist de Mantenimiento

### Semanal
- [ ] Revisar logs (errores, warnings)
- [ ] Verificar que bot responde (/start)
- [ ] Contar usuarios VIP activos
- [ ] Revisar solicitudes Free pendientes

### Mensual
- [ ] Backup manual
- [ ] Renovar tokens próximos a expirar
- [ ] Revisar tamaño de BD
- [ ] Actualizar documentación si hay cambios

### Trimestral
- [ ] Revisar performance (logs, memoria)
- [ ] Actualizar dependencias
- [ ] Test de recovery de backup
- [ ] Revision de seguridad (permisos, secretos)

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
