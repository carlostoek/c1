# Documento de Decisiones de Diseño

Justificaciones y decisiones arquitectónicas tomadas en el desarrollo del bot.

## Tabla de Contenidos

1. [Stack Tecnológico](#stack-tecnológico)
2. [Arquitectura General](#arquitectura-general)
3. [Base de Datos](#base-de-datos)
4. [Patrones de Desarrollo](#patrones-de-desarrollo)
5. [Decisiones Operacionales](#decisiones-operacionales)

## Stack Tecnológico

### Python 3.11+

**Decisión:** Usar Python 3.11 mínimo

**Justificaciones:**
- Async/await soporte completo y optimizado
- Type hints mejorados (PEP 613)
- Pattern matching (case/when)
- Performance mejorado
- Termux soporta Python 3.11+

**Alternativas consideradas:**
- Python 3.10 - Funciona pero sin optimizaciones recientes
- Python 3.12 - No ampliamente disponible en Termux
- Otros lenguajes (Go, Rust) - Overhead innecesario para MVP

### Aiogram 3.4.1

**Decisión:** Framework async para Telegram Bot API

**Justificaciones:**
- Soporte nativo async/await
- Dispatcher con routing y middlewares
- FSM para conversaciones
- Actualizado y mantenido activamente
- Comunidad grande

**Alternativas consideradas:**
- `python-telegram-bot` - Más lento, menos async
- `pyrogram` - Orientado a userbot, no bot
- Aiogram 2.x - Versión anterior, menos features

### SQLAlchemy 2.0.25 + aiosqlite

**Decisión:** ORM async con SQLite local

**Justificaciones:**
- SQLAlchemy 2.0 con soporte async nativo
- aiosqlite para operaciones async en SQLite
- Sin necesidad de servidor externo (ideal para Termux)
- Índices y relaciones ForeignKey
- Migraciones fáciles con Alembic (futuro)

**Alternativas consideradas:**
- PostgreSQL - Overkill para MVP, necesita servidor
- MongoDB - No SQL, más complejo sin ORM
- Raw SQLite - Sin ORM, queries manuales
- Tortoise ORM - Menor comunidad y features que SQLAlchemy

### SQLite 3.x (WAL mode)

**Decisión:** Base de datos local con WAL mode

**Justificaciones:**
- Sin instalación/configuración de servidor
- WAL mode permite lecturas concurrentes
- Suficiente para 100-1000 usuarios
- Fácil backup (copiar archivo .db)
- Rendimiento adecuado para Termux

**Alternativas consideradas:**
- PostgreSQL - Necesita servidor, recursos
- MySQL - Necesita servidor, más complejo
- Redis - Solo cache, no persistencia

### MemoryStorage (Aiogram FSM)

**Decisión:** Estados en memoria para MVP

**Justificaciones:**
- Ligero y sin dependencias
- Suficiente para MVP
- Perdida de estados al reiniciar es aceptable
- Sin complejidad de Redis

**Futuro (ONDA 2+):**
- Migrar a RedisStorage para persistencia

### APScheduler 3.10.4

**Decisión:** Tareas programadas para background

**Justificaciones:**
- Scheduling flexible (intervalo, cron)
- Async support
- Integración simple con Aiogram
- Trigger tipos: interval, cron, date

**Alternativas consideradas:**
- Celery - Overkill, necesita broker
- Schedule - Más simple pero menos flexible
- Asyncio.create_task - Manual y difícil de mantener

### Python-dotenv

**Decisión:** Variables de entorno desde .env

**Justificaciones:**
- Separar secretos del código
- Fácil manejo de configuración
- NO commitear .env a Git
- Standard en desarrollo Python

## Arquitectura General

### Separación en Capas

```
Handlers (Orquestación)
    ↓
Services (Lógica)
    ↓
Database (Persistencia)
```

**Decisión:** 3 capas claramente separadas

**Justificación:**
- Handlers no tienen lógica de BD (solo orquestación)
- Services encapsulan lógica de negocio reutilizable
- Database acceso centralizado y controlado
- Fácil testing (mockear layers)
- Cambios en BD sin afectar handlers

### Routers y Middlewares

**Decisión:** Router separado por dominio (admin, user)

**Justificación:**
- Handlers organizados por responsabilidad
- Fácil encontrar código relacionado
- Escalable a más funcionalidades

**Middlewares:**
- `AdminAuthMiddleware` - Validación de permisos
- `DatabaseMiddleware` - Inyección de sesión

**Justificación:**
- Código limpio sin repetición de validación
- Inyección de dependencias automática

### FSM y Estados

**Decisión:** Usar StatesGroup de Aiogram

**Justificación:**
- Conversaciones multi-paso clara
- Dato temporal con await_data
- Type-safe con enums
- Fácil debug (ver estado actual)

**Alternativas consideradas:**
- Sin FSM - Código estateless, difícil conversaciones
- FSM manual - Propenso a errores

## Base de Datos

### Modelos y Relaciones

**Decisión:** 4 modelos independientes (no over-engineer)

```
BotConfig (1 singleton)
InvitationToken (1:N -> VIPSubscriber)
VIPSubscriber (N:1 <- InvitationToken)
FreeChannelRequest (independiente)
```

**Justificación:**
- Bajo acoplamiento
- Cada modelo responsabilidad clara
- Relación solo entre Token y Subscriber
- FreeChannelRequest independiente (simple)

### Índices Específicos

**Decisión:** Índices compuestos en columnas de búsqueda

```
InvitationToken: (used, created_at)
VIPSubscriber: (status, expiry_date)
FreeChannelRequest: (processed, request_date)
```

**Justificación:**
- Queries comunes son rápidas
- Bajo overhead de escritura
- Performance en background tasks

### Foreign Keys y Cascades

**Decisión:** Foreign key único entre Token y Subscriber

**Justificación:**
- Integridad referencial
- Cascade delete si se elimina token
- Previene datos huérfanos

### Timestamps (UTC)

**Decisión:** Todas las fechas en UTC (datetime.utcnow())

**Justificación:**
- Independiente de zona horaria
- Consistente en múltiples servidores (futuro)
- Fácil conversión a zona local si es necesario

## Patrones de Desarrollo

### Async/Await Obligatorio

**Decisión:** TODO es async (handlers, services, BD)

**Justificación:**
- Concurrencia sin threading
- Mejor performance en Termux
- Único paradigma (sin mezcla sync/async)
- Aiogram es async-first

### Type Hints

**Decisión:** Type hints en TODAS las funciones

**Justificación:**
- Documentación automática
- IDE autocompletion
- Detección de errores antes de runtime
- Mypy para validación estática (futuro)

**Ejemplo:**
```python
async def redeem_token(
    self,
    user_id: int,
    token: str
) -> VIPSubscriber:
    """Docstring aquí"""
    pass
```

### Error Handling

**Decisión:** Try-except en handlers, nunca dejar crashear

**Justificación:**
- Bot sigue corriendo incluso con errores
- Logging de errores para debug
- Usuario recibe respuesta (error message)

**Patrón:**
```python
try:
    # Lógica
except ValueError:
    # Error usuario (validación)
    logger.warning(...)
except Exception:
    # Error inesperado
    logger.error(..., exc_info=True)
    await message.answer("Error")
```

### Logging Niveles

**Decisión:** DEBUG, INFO, WARNING, ERROR, CRITICAL

**Justificación:**
- DEBUG: desarrollo (queries SQL, debug)
- INFO: eventos importantes (bot start, token generado)
- WARNING: problemas no críticos (token no encontrado)
- ERROR: fallos (error de BD, usuario no invitado)
- CRITICAL: bot no operativo

### Docstrings (Google Style)

**Decisión:** Google Style para todas las funciones públicas

**Justificación:**
- Formato estándar Python
- Parseable por documentación automática
- Claro para desarrolladores

**Ejemplo:**
```python
async def redeem_token(self, user_id: int, token: str) -> VIPSubscriber:
    """
    Canjea token VIP para usuario.

    Args:
        user_id: ID del usuario
        token: Valor del token

    Returns:
        VIPSubscriber creado

    Raises:
        ValueError: Si token es inválido
    """
```

## Decisiones Operacionales

### Configuración Centralizada (config.py)

**Decisión:** Una clase Config global con validación

**Justificación:**
- Un único punto de verdad
- Validación automática al startup
- Logging de resumen de config
- Fácil agregar nuevas variables

**No usar:** Variables globales directas, múltiples configs

### Context Manager para Sesiones BD

**Decisión:** Usar async with para garantizar cleanup

```python
async with get_session() as session:
    # auto-commit si éxito
    # auto-rollback si error
    # auto-close siempre
```

**Justificación:**
- No olvidar commit/rollback/close
- Manejo automático de excepciones
- Código limpio y seguro

### Validación en Servicios, No Handlers

**Decisión:** Servicios hacen validación, handlers solo orquestan

**Justificación:**
- Lógica reutilizable en tests
- Handlers más legibles
- Fácil encontrar lógica de negocio

**Ejemplo:**
```python
# Handler (orquestación)
@router.message(...)
async def handler(message, session):
    try:
        subscriber = await service.redeem_token(user_id, token)
        await message.answer("Éxito")
    except ValueError as e:
        await message.answer(f"Error: {e}")

# Service (validación)
async def redeem_token(self, user_id, token):
    if not token:
        raise ValueError("Token requerido")
    # ... más validación
```

### Polling vs Webhook

**Decisión:** Polling para MVP (Termux compatible)

**Justificación:**
- Sin necesidad de SSL/HTTPS
- Sin server web para webhook
- Funciona en Termux/Android
- Timeout de 30s apropiado para conexiones inestables

**Futuro (ONDA 2+):** Considerar webhook si host disponible

### Drop Pending Updates

**Decisión:** `drop_pending_updates=True` al iniciar

**Justificación:**
- Ignora mensajes viejos antes de iniciar bot
- Previene duplicación de mensajes
- Bot siempre responde a eventos "nuevos"

### HTML Parse Mode

**Decisión:** `parse_mode="HTML"` por defecto en Bot

**Justificación:**
- Más flexible que Markdown
- Soporta más formatting
- Consistente en todos los mensajes

### Token de 16 Caracteres

**Decisión:** Tokens con 16 caracteres alfanuméricos

**Justificación:**
- 16 caracteres = 96 bits de entropía (con [a-zA-Z0-9])
- Suficiente para seguridad
- Fácil de copiar/pegar
- Menos de 20 caracteres (máx de Telegram)

**Alternativas consideradas:**
- 8 caracteres - Muy fácil de adivinarse
- 32 caracteres - Demasiado largo, inconveniente
- UUID - Muy largo, no user-friendly

### Tiempo de Espera Free (5 min default)

**Decisión:** 5 minutos como valor default

**Justificación:**
- Corto para usuario (acceso rápido)
- Suficiente para moderar (spam protection)
- Configurable por admin
- Background task cada 5 min

**Alternativas consideradas:**
- 1 min - Muy corto, sin protección
- 24 horas - Demasiado largo, malo UX
- 1 hora - Mejor, pero 5 min más ágil para MVP

### Duración Token (24 horas default)

**Decisión:** 24 horas como duración default

**Justificación:**
- Suficiente para 1 día de acceso
- Corto para seguridad (revocation)
- Otras opciones: 7 días, 30 días, custom

## Compromesos (Trade-offs)

### Performance vs Flexibilidad

**Decisión:** Sacrificar algo de performance por flexibilidad

- Queries un poco menos optimizadas (legibilidad)
- No cached en memoria (persistencia confiable)
- JSON para config flexible (menos performante que columnas separadas)

**Justificación:** MVP debe ser mantenible, no ultra-rápido

### Seguridad vs Usabilidad

**Decisión:** Balance entre seguridad y facilidad de uso

- Tokens legibles (no random bytes)
- Sin 2FA (UX compleja para MVP)
- Validaciones básicas (no CAPTCHA)

**Justificación:** MVP debe ser usable por usuarios normales

### Simplicity vs Features

**Decisión:** MVP mínimo, features en ONDA 2+

- No hay renovación automática (manual por admin)
- No hay webhook updates (polling)
- No hay Redis cache (memory storage)
- No hay múltiples canales

**Justificación:** Iterar rápido, agregar después si es necesario

## Evolución Planeada

### ONDA 2: Features Avanzadas

- Redis para FSM persistente
- Webhook updates (si host disponible)
- Sistema de pagos/suscripción
- Múltiples canales por categoría
- Estadísticas y reportes

### ONDA 3: Optimización

- PostgreSQL reemplazar SQLite
- Microservicios separados
- Load balancing
- Container + Kubernetes
- 100% cobertura de tests

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
