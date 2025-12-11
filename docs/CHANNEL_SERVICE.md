# Channel Service Documentation

Documentation completa para el servicio de gestión de canales VIP y Free del bot de Telegram.

## Índice

1. [Introducción](#introducción)
2. [Características Principales](#características-principales)
3. [Instalación y Configuración](#instalación-y-configuración)
4. [API del Servicio](#api-del-servicio)
5. [Flujos de Trabajo](#flujos-de-trabajo)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Manejo de Errores](#manejo-de-errores)
8. [Consideraciones de Seguridad](#consideraciones-de-seguridad)

## Introducción

El Channel Service es un componente clave del bot que permite la gestión completa de canales VIP y Free. Proporciona funcionalidades para configurar canales, verificar permisos del bot, enviar contenido multimedia y operaciones avanzadas como reenvío y copia de mensajes.

## Características Principales

- **Configuración de canales VIP y Free** con verificación de existencia y permisos
- **Verificación de permisos del bot** (can_invite_users, can_post_messages)
- **Envío de contenido multimedia** (texto, fotos, videos) a canales
- **Reenvío y copia de mensajes** entre chats y canales
- **Validación robusta** de configuración y formato de IDs de canal
- **Integración con Service Container** para inyección de dependencias

## Instalación y Configuración

El Channel Service forma parte del contenedor de servicios y se inicializa automáticamente:

```python
from bot.services.container import ServiceContainer

container = ServiceContainer(session, bot)

# El servicio se carga de forma lazy cuando se accede por primera vez
channel_service = container.channel  # Carga el servicio si no está cargado
```

## API del Servicio

### Configuración de Canales

#### `setup_vip_channel(channel_id: str) -> Tuple[bool, str]`
Configura el canal VIP con verificaciones de existencia y permisos.

```python
success, message = await container.channel.setup_vip_channel("-1001234567890")
if success:
    print(f"✅ Canal VIP configurado: {message}")
else:
    print(f"❌ Error: {message}")
```

#### `setup_free_channel(channel_id: str) -> Tuple[bool, str]`
Configura el canal Free con las mismas verificaciones que VIP.

```python
success, message = await container.channel.setup_free_channel("-1009876543210")
if success:
    print(f"✅ Canal Free configurado: {message}")
else:
    print(f"❌ Error: {message}")
```

#### `verify_bot_permissions(channel_id: str) -> Tuple[bool, str]`
Verifica que el bot tenga los permisos necesarios en el canal.

```python
is_valid, perm_message = await container.channel.verify_bot_permissions("-1001234567890")
if is_valid:
    print("✅ Bot tiene todos los permisos necesarios")
else:
    print(f"❌ Permisos faltantes: {perm_message}")
```

### Validación de Configuración

#### `is_vip_channel_configured() -> bool`
Verifica si el canal VIP está configurado.

#### `is_free_channel_configured() -> bool`
Verifica si el canal Free está configurado.

#### `get_vip_channel_id() -> Optional[str]`
Obtiene el ID del canal VIP configurado.

#### `get_free_channel_id() -> Optional[str]`
Obtiene el ID del canal Free configurado.

### Envío de Contenido

#### `send_to_channel(channel_id: str, text: Optional[str] = None, photo: Optional[str] = None, video: Optional[str] = None, **kwargs) -> Tuple[bool, str, Optional[Message]]`
Envía contenido al canal especificado.

```python
# Envío de texto
success, message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="¡Nueva publicación en el canal VIP!",
    parse_mode="HTML"
)

# Envío de foto con texto
success, message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="Foto destacada del día",
    photo="AgACAgQAAxkBAA...",
    parse_mode="HTML"
)

# Envío de video con descripción
success, message, sent_msg = await container.channel.send_to_channel(
    channel_id="-1001234567890",
    text="Video promocional",
    video="BAACAgQAAxkBAA...",
    parse_mode="HTML"
)
```

### Operaciones Avanzadas

#### `forward_to_channel(channel_id: str, from_chat_id: int, message_id: int) -> Tuple[bool, str]`
Reenvía un mensaje a un canal.

```python
success, message = await container.channel.forward_to_channel(
    channel_id="-1001234567890",
    from_chat_id=-1009876543210,
    message_id=123
)
```

#### `copy_to_channel(channel_id: str, from_chat_id: int, message_id: int) -> Tuple[bool, str]`
Copia un mensaje a un canal sin la firma de origen.

```python
success, message = await container.channel.copy_to_channel(
    channel_id="-1001234567890",
    from_chat_id=-1009876543210,
    message_id=123
)
```

### Información de Canales

#### `get_channel_info(channel_id: str) -> Optional[Chat]`
Obtiene información del canal.

#### `get_channel_member_count(channel_id: str) -> Optional[int]`
Obtiene la cantidad de miembros del canal.

## Flujos de Trabajo

### Flujo de Configuración de Canal

1. Admin llama a `setup_vip_channel()` o `setup_free_channel()`
2. El servicio verifica el formato del ID (debe comenzar con "-100")
3. Verifica que el canal exista usando `bot.get_chat()`
4. Verifica que el bot tenga acceso al canal
5. Verifica los permisos del bot usando `verify_bot_permissions()`
6. Guarda el ID del canal en la configuración global
7. Retorna mensaje de confirmación o error

### Flujo de Envío de Contenido

1. Llamada a `send_to_channel()` con los parámetros apropiados
2. El servicio determina el tipo de contenido (texto, foto, video)
3. Realiza la llamada correspondiente a la API de Telegram
4. Maneja posibles excepciones
5. Retorna resultado de la operación

### Flujo de Verificación de Permisos

1. Llamada a `verify_bot_permissions()` con ID del canal
2. El servicio obtiene información del bot en el canal usando `get_chat_member()`
3. Verifica que el bot sea admin o creador
4. Verifica los permisos específicos (can_invite_users, can_post_messages)
5. Retorna estado de verificación y mensaje detallado

## Ejemplos de Uso

### Configuración Completa de Canales

```python
async def setup_channels_example(container):
    # Configurar canal VIP
    vip_success, vip_message = await container.channel.setup_vip_channel("-1001234567890")
    if vip_success:
        print(f"✅ Canal VIP configurado: {vip_message}")
    else:
        print(f"❌ Error en canal VIP: {vip_message}")
    
    # Configurar canal Free
    free_success, free_message = await container.channel.setup_free_channel("-1009876543210")
    if free_success:
        print(f"✅ Canal Free configurado: {free_message}")
    else:
        print(f"❌ Error en canal Free: {free_message}")
    
    # Verificar configuración
    is_vip_set = await container.channel.is_vip_channel_configured()
    is_free_set = await container.channel.is_free_channel_configured()
    
    print(f"VIP configurado: {is_vip_set}, Free configurado: {is_free_set}")
```

### Envío de Contenido Multimedia

```python
async def send_content_example(container):
    # Obtener IDs de canales
    vip_channel = await container.channel.get_vip_channel_id()
    free_channel = await container.channel.get_free_channel_id()
    
    if vip_channel:
        # Envío de publicación VIP con imagen
        success, message, sent_msg = await container.channel.send_to_channel(
            channel_id=vip_channel,
            text="<b>🎉 ¡Nuevo contenido exclusivo!</b>\n\n"
                 "Accede ahora a nuestro contenido VIP premium.",
            photo="AgACAgQAAxkBAAExamplePhotoId",
            parse_mode="HTML"
        )
        
        if success:
            print(f"✅ Publicación VIP enviada: {message}")
        else:
            print(f"❌ Error en publicación VIP: {message}")
    
    if free_channel:
        # Envío de publicación Free con video
        success, message, sent_msg = await container.channel.send_to_channel(
            channel_id=free_channel,
            text="<b>🎬 Contenido gratuito disponible</b>\n\n"
                 "Disfruta de este contenido exclusivo para todos nuestros seguidores.",
            video="BAACAgQAAxkBAAExampleVideoId",
            parse_mode="HTML"
        )
        
        if success:
            print(f"✅ Publicación Free enviada: {message}")
        else:
            print(f"❌ Error en publicación Free: {message}")
```

### Reenvío y Copia de Mensajes

```python
async def forward_copy_example(container):
    # Supongamos que tenemos un mensaje original en un grupo
    source_group_id = -1009876543210
    message_id = 456
    
    # Obtener IDs de canales
    vip_channel = await container.channel.get_vip_channel_id()
    free_channel = await container.channel.get_free_channel_id()
    
    if vip_channel:
        # Reenviar mensaje al canal VIP (muestra "Forwarded from...")
        forward_success, forward_message = await container.channel.forward_to_channel(
            channel_id=vip_channel,
            from_chat_id=source_group_id,
            message_id=message_id
        )
        
        if forward_success:
            print(f"✅ Mensaje reenviado a VIP: {forward_message}")
        else:
            print(f"❌ Error al reenviar a VIP: {forward_message}")
    
    if free_channel:
        # Copiar mensaje al canal Free (sin "Forwarded from...")
        copy_success, copy_message = await container.channel.copy_to_channel(
            channel_id=free_channel,
            from_chat_id=source_group_id,
            message_id=message_id
        )
        
        if copy_success:
            print(f"✅ Mensaje copiado a Free: {copy_message}")
        else:
            print(f"❌ Error al copiar a Free: {copy_message}")
```

### Verificación de Estado y Obtención de Información

```python
async def channel_info_example(container):
    # Verificar configuración de canales
    is_vip_configured = await container.channel.is_vip_channel_configured()
    is_free_configured = await container.channel.is_free_channel_configured()
    
    print(f"Canal VIP configurado: {is_vip_configured}")
    print(f"Canal Free configurado: {is_free_configured}")
    
    # Obtener IDs de canales
    vip_id = await container.channel.get_vip_channel_id()
    free_id = await container.channel.get_free_channel_id()
    
    if vip_id:
        # Obtener información del canal VIP
        vip_info = await container.channel.get_channel_info(vip_id)
        if vip_info:
            print(f"Información del canal VIP: {vip_info.title} (@{vip_info.username or 'N/A'})")
            
            # Obtener conteo de miembros
            member_count = await container.channel.get_channel_member_count(vip_id)
            if member_count:
                print(f"Miembros del canal VIP: {member_count}")
    
    if free_id:
        # Verificar permisos del bot en canal Free
        is_valid, perm_msg = await container.channel.verify_bot_permissions(free_id)
        print(f"Permisos en canal Free: {perm_msg}")
```

## Manejo de Errores

El Channel Service implementa manejo robusto de errores:

### Excepciones Comunes

- `TelegramBadRequest`: Error en la solicitud a la API de Telegram (ID inválido, etc.)
- `TelegramForbiddenError`: El bot no tiene permisos suficientes
- `RuntimeError`: Configuración de base de datos no encontrada

### Patrón de Manejo de Errores

```python
try:
    success, message, sent_msg = await container.channel.send_to_channel(
        channel_id="-1001234567890",
        text="Contenido de prueba"
    )
    
    if success:
        print(f"✅ Éxito: {message}")
    else:
        print(f"❌ Error: {message}")
        
except TelegramForbiddenError:
    print("❌ El bot no tiene permiso para publicar en el canal")
except TelegramBadRequest as e:
    print(f"❌ Error en la solicitud: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
```

## Consideraciones de Seguridad

1. **Verificación de permisos**: El servicio siempre verifica que el bot tenga los permisos necesarios antes de realizar operaciones
2. **Validación de IDs**: Todos los IDs de canal son validados para asegurar el formato correcto
3. **Control de acceso**: Las operaciones requieren que el bot sea administrador del canal
4. **Registro de operaciones**: Todas las operaciones exitosas son registradas para auditoría
5. **Protección contra inyecciones**: Los IDs de canal son validados y no se permiten caracteres especiales

## Buenas Prácticas

1. **Verificar configuración antes de operar**:
   ```python
   if await container.channel.is_vip_channel_configured():
       # Realizar operaciones en canal VIP
   ```

2. **Validar permisos regularmente**:
   ```python
   is_valid, msg = await container.channel.verify_bot_permissions(channel_id)
   if not is_valid:
       # Manejar error de permisos
   ```

3. **Usar el Service Container** para la inyección de dependencias:
   ```python
   # Correcto
   channel_service = container.channel
   
   # Evitar instanciar directamente
   # channel_service = ChannelService(session, bot)
   ```

4. **Manejar todos los resultados posibles**:
   ```python
   success, message, sent_msg = await container.channel.send_to_channel(...)
   
   if success:
       # Operación exitosa
   else:
       # Manejar error
   ```

---

**Última actualización:** 2025-12-11  
**Versión del servicio:** 1.0.0