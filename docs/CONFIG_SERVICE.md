# Config Service (T9) - Documentación Completa

## Descripción General

El **Config Service** es un componente esencial del bot que gestiona la configuración global del sistema. Implementa un patrón singleton donde toda la configuración del bot se almacena en un único registro de la tabla `BotConfig`. Este servicio permite a los administradores gestionar dinámicamente los parámetros del bot sin necesidad de reiniciar el sistema.

## Responsabilidades

- **Obtención/actualización de configuración:** Acceso y modificación de la configuración global (BotConfig singleton)
- **Gestión de tiempo de espera Free:** Control del tiempo de espera para acceso al canal Free
- **Gestión de reacciones de canales:** Configuración de emojis personalizados para canales VIP y Free
- **Validación de configuración:** Verificación de que la configuración esté completa y funcional
- **Configuración de tarifas de suscripción:** Gestión de precios para diferentes tipos de membresías
- **Resumen de configuración:** Proporcionar información detallada del estado actual del bot

## Arquitectura

### Singleton Pattern
El modelo `BotConfig` implementa un patrón singleton donde solo existe un registro con `id=1` que contiene toda la configuración global del bot. Todos los métodos del servicio operan sobre este único registro.

### Estructura de la Configuración
```python
class BotConfig:
    id: int = 1  # Siempre 1 (singleton)
    vip_channel_id: str  # ID del canal VIP
    free_channel_id: str  # ID del canal Free
    wait_time_minutes: int  # Tiempo de espera para Free
    vip_reactions: List[str]  # JSON array de emojis para VIP
    free_reactions: List[str]  # JSON array de emojis para Free
    subscription_fees: Dict[str, float]  # JSON object con tarifas
    created_at: datetime
    updated_at: datetime
```

## API Pública

### Getters

#### `get_config()` → BotConfig
Obtiene la configuración global del bot.

**Returns:** `BotConfig` - Objeto de configuración completa

**Raises:** `RuntimeError` - Si BotConfig no existe (caso no esperado)

**Ejemplo:**
```python
config = await container.config.get_config()
print(f"Canal VIP: {config.vip_channel_id}")
print(f"Tiempo de espera: {config.wait_time_minutes} minutos")
```

#### `get_wait_time()` → int
Obtiene el tiempo de espera para el canal Free en minutos.

**Returns:** `int` - Tiempo de espera en minutos

**Ejemplo:**
```python
wait_time = await container.config.get_wait_time()
print(f"Tiempo de espera actual: {wait_time} minutos")
```

#### `get_vip_channel_id()` → Optional[str]
Obtiene el ID del canal VIP configurado.

**Returns:** `str` - ID del canal VIP, o `None` si no está configurado

**Ejemplo:**
```python
vip_channel_id = await container.config.get_vip_channel_id()
if vip_channel_id:
    print(f"Canal VIP configurado: {vip_channel_id}")
else:
    print("Canal VIP no configurado")
```

#### `get_free_channel_id()` → Optional[str]
Obtiene el ID del canal Free configurado.

**Returns:** `str` - ID del canal Free, o `None` si no está configurado

**Ejemplo:**
```python
free_channel_id = await container.config.get_free_channel_id()
if free_channel_id:
    print(f"Canal Free configurado: {free_channel_id}")
else:
    print("Canal Free no configurado")
```

#### `get_vip_reactions()` → List[str]
Obtiene las reacciones configuradas para el canal VIP.

**Returns:** `List[str]` - Lista de emojis (ej: ["👍", "❤️", "🔥"])

**Ejemplo:**
```python
reactions = await container.config.get_vip_reactions()
print(f"Reacciones VIP: {reactions}")
```

#### `get_free_reactions()` → List[str]
Obtiene las reacciones configuradas para el canal Free.

**Returns:** `List[str]` - Lista de emojis

**Ejemplo:**
```python
reactions = await container.config.get_free_reactions()
print(f"Reacciones Free: {reactions}")
```

#### `get_subscription_fees()` → Dict[str, float]
Obtiene las tarifas de suscripción configuradas.

**Returns:** `Dict[str, float]` - Dict con tarifas (ej: {"monthly": 10, "yearly": 100})

**Ejemplo:**
```python
fees = await container.config.get_subscription_fees()
print(f"Tarifas de suscripción: {fees}")
```

### Setters

#### `set_wait_time(minutes: int)` → None
Actualiza el tiempo de espera para el canal Free.

**Args:**
- `minutes` - Tiempo en minutos (debe ser >= 1)

**Raises:** `ValueError` - Si minutes < 1

**Ejemplo:**
```python
try:
    await container.config.set_wait_time(15)  # 15 minutos
    print("Tiempo de espera actualizado a 15 minutos")
except ValueError as e:
    print(f"Error: {e}")
```

#### `set_vip_reactions(reactions: List[str])` → None
Actualiza las reacciones del canal VIP.

**Args:**
- `reactions` - Lista de emojis (ej: ["👍", "❤️"])

**Raises:** 
- `ValueError` - Si la lista está vacía o tiene más de 10 elementos

**Ejemplo:**
```python
try:
    await container.config.set_vip_reactions(["👍", "❤️", "🔥", "🎉"])
    print("Reacciones VIP actualizadas")
except ValueError as e:
    print(f"Error: {e}")
```

#### `set_free_reactions(reactions: List[str])` → None
Actualiza las reacciones del canal Free.

**Args:**
- `reactions` - Lista de emojis

**Raises:** 
- `ValueError` - Si la lista está vacía o tiene más de 10 elementos

**Ejemplo:**
```python
try:
    await container.config.set_free_reactions(["✅", "✔️", "☑️"])
    print("Reacciones Free actualizadas")
except ValueError as e:
    print(f"Error: {e}")
```

#### `set_subscription_fees(fees: Dict[str, float])` → None
Actualiza las tarifas de suscripción.

**Args:**
- `fees` - Dict con tarifas (ej: {"monthly": 10, "yearly": 100})

**Raises:** 
- `ValueError` - Si fees está vacío o contiene valores negativos

**Ejemplo:**
```python
try:
    await container.config.set_subscription_fees({
        "monthly": 10.0,
        "yearly": 100.0,
        "lifetime": 500.0
    })
    print("Tarifas de suscripción actualizadas")
except ValueError as e:
    print(f"Error: {e}")
```

### Validación y Estado

#### `is_fully_configured()` → bool
Verifica si el bot está completamente configurado.

**Configuración completa requiere:**
- Canal VIP configurado
- Canal Free configurado  
- Tiempo de espera > 0

**Returns:** `bool` - True si la configuración está completa, False si no

**Ejemplo:**
```python
is_configured = await container.config.is_fully_configured()
if is_configured:
    print("Bot completamente configurado ✅")
else:
    print("Bot necesita configuración adicional ❌")
```

#### `get_config_status()` → Dict[str, any]
Obtiene el estado de la configuración para dashboard.

**Returns:** `Dict` con información de configuración:
```python
{
    "is_configured": bool,           # True si todo está configurado
    "vip_channel_id": str | None,    # ID del canal VIP o None
    "free_channel_id": str | None,   # ID del canal Free o None
    "wait_time_minutes": int,        # Tiempo de espera en minutos
    "vip_reactions_count": int,      # Número de reacciones VIP
    "free_reactions_count": int,     # Número de reacciones Free
    "missing": List[str]             # Lista de elementos faltantes
}
```

**Ejemplo:**
```python
status = await container.config.get_config_status()
print(f"Configurado: {status['is_configured']}")
print(f"Faltante: {status['missing']}")
print(f"Reacciones VIP: {status['vip_reactions_count']}")
```

#### `get_config_summary()` → str
Retorna un resumen de la configuración en formato texto, útil para mostrar en mensajes de Telegram.

**Returns:** `str` - String formateado con información de configuración

**Ejemplo:**
```python
summary = await container.config.get_config_summary()
print(summary)
# Salida:
# 📊 <b>Estado de Configuración</b>
#
# <b>Canal VIP:</b> ✅ Configurado
# ID: <code>-1001234567890</code>
#
# <b>Canal Free:</b> ✅ Configurado
# ID: <code>-1009876543210</code>
#
# <b>Tiempo de Espera:</b> 5 minutos
#
# <b>Reacciones VIP:</b> 3 configuradas
# <b>Reacciones Free:</b> 2 configuradas
```

### Utilidades

#### `reset_to_defaults()` → None
Resetea la configuración a valores por defecto.

**Advertencia:** Esto elimina la configuración de canales. Solo usar en caso de necesitar resetear completamente.

**Valores por defecto:**
- `vip_channel_id`: None
- `free_channel_id`: None
- `wait_time_minutes`: 5
- `vip_reactions`: []
- `free_reactions`: []
- `subscription_fees`: {"monthly": 10, "yearly": 100}

**Ejemplo:**
```python
await container.config.reset_to_defaults()
print("Configuración reseteada a valores por defecto")
```

## Ejemplos de Uso Completo

### 1. Obtención de configuración global
```python
# Obtener la configuración completa del bot
config = await container.config.get_config()
print(f"Canal VIP: {config.vip_channel_id}")
print(f"Canal Free: {config.free_channel_id}")
print(f"Tiempo de espera: {config.wait_time_minutes} minutos")
print(f"Reacciones VIP: {config.vip_reactions}")
print(f"Reacciones Free: {config.free_reactions}")
print(f"Tarifas: {config.subscription_fees}")
```

### 2. Configuración de tiempos de espera
```python
# Verificar tiempo actual de espera
current_wait_time = await container.config.get_wait_time()
print(f"Tiempo actual de espera: {current_wait_time} minutos")

# Configurar nuevo tiempo de espera (15 minutos)
await container.config.set_wait_time(15)
print("Tiempo de espera actualizado a 15 minutos")

# Validar el cambio
new_wait_time = await container.config.get_wait_time()
print(f"Nuevo tiempo de espera: {new_wait_time} minutos")
```

### 3. Gestión de reacciones de canales
```python
# Obtener reacciones actuales
current_vip_reactions = await container.config.get_vip_reactions()
current_free_reactions = await container.config.get_free_reactions()

print(f"Reacciones VIP actuales: {current_vip_reactions}")
print(f"Reacciones Free actuales: {current_free_reactions}")

# Configurar nuevas reacciones VIP
await container.config.set_vip_reactions(["👍", "❤️", "🔥", "🎉", "💯"])
print("Reacciones VIP actualizadas")

# Configurar nuevas reacciones Free
await container.config.set_free_reactions(["✅", "✔️", "☑️", "🟢", "🔵"])
print("Reacciones Free actualizadas")

# Verificar cambios
updated_vip_reactions = await container.config.get_vip_reactions()
updated_free_reactions = await container.config.get_free_reactions()
print(f"Nuevas reacciones VIP: {updated_vip_reactions}")
print(f"Nuevas reacciones Free: {updated_free_reactions}")
```

### 4. Configuración de tarifas de suscripción
```python
# Obtener tarifas actuales
current_fees = await container.config.get_subscription_fees()
print(f"Tarifas actuales: {current_fees}")

# Configurar nuevas tarifas
new_fees = {
    "monthly": 10.0,
    "quarterly": 25.0,
    "yearly": 100.0,
    "lifetime": 500.0
}

await container.config.set_subscription_fees(new_fees)
print("Tarifas de suscripción actualizadas")

# Verificar cambios
updated_fees = await container.config.get_subscription_fees()
print(f"Nuevas tarifas: {updated_fees}")
```

### 5. Validación de configuración completa
```python
# Verificar si el bot está completamente configurado
is_configured = await container.config.is_fully_configured()

if is_configured:
    print("✅ Bot completamente configurado")
else:
    # Obtener detalles de lo que falta
    status = await container.config.get_config_status()
    print("❌ Bot necesita configuración adicional")
    print(f"Faltan elementos: {', '.join(status['missing'])}")
    
    # Mostrar estado detallado
    print(f"Canal VIP configurado: {'✅' if status['vip_channel_id'] else '❌'}")
    print(f"Canal Free configurado: {'✅' if status['free_channel_id'] else '❌'}")
    print(f"Tiempo de espera: {status['wait_time_minutes']} minutos")
```

### 6. Obtención de resumen de configuración
```python
# Obtener resumen completo de la configuración
summary = await container.config.get_config_summary()
print(summary)

# Este resumen está formateado especialmente para ser mostrado en Telegram
# con etiquetas HTML, emojis y formato claro
```

## Patrones de Diseño

### Lazy Loading
El ConfigService se carga bajo demanda a través del ServiceContainer, optimizando el uso de memoria en entornos limitados como Termux.

### Validación de Entrada
Todos los setters incluyen validación de entrada para prevenir configuraciones inválidas:
- Tiempos de espera >= 1 minuto
- Listas de reacciones con 1-10 elementos
- Tarifas de suscripción no negativas
- Campos obligatorios no nulos

### Logging
El servicio incluye logging detallado para seguimiento de cambios:
- Modificaciones de tiempos de espera
- Actualizaciones de reacciones
- Cambios en tarifas de suscripción
- Acciones de reseteo

## Integración con Otros Servicios

El ConfigService se integra con otros servicios del sistema:

- **ChannelService:** Lee los IDs de canal configurados para operaciones
- **SubscriptionService:** Usa el tiempo de espera Free para gestionar colas
- **ServiceContainer:** Implementa el patrón DI + Lazy Loading

## Consideraciones de Seguridad

- Solo usuarios administradores deben tener acceso a los métodos de configuración
- Validación exhaustiva de entradas para prevenir inyección de datos maliciosos
- Logging de todas las modificaciones de configuración para auditoría
- Protección contra valores extremos que puedan afectar el rendimiento

## Excepciones Comunes

- `RuntimeError`: Cuando BotConfig no existe (caso crítico)
- `ValueError`: Parámetros inválidos en setters (tiempo < 1, listas vacías, etc.)
- `SQLAlchemyError`: Errores de base de datos (generalmente manejados por el contenedor de servicios)