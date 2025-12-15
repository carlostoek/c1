# Sistema de Reacciones

## Descripción General

El sistema de reacciones es una funcionalidad avanzada que permite a los usuarios interactuar con las publicaciones del bot mediante emojis personalizados, ganando Besitos (puntos de gamificación) por cada reacción. Este sistema consta de configuración administrativa, gestión de reacciones, integración con broadcasting y manejo de contadores en tiempo real.

## Componentes del Sistema

### 1. Modelos de Base de Datos

#### ReactionConfig
Modelo que almacena la configuración de reacciones disponibles.

**Campos:**
- `id`: Identificador único
- `emoji`: Emoji Unicode único para la reacción (ej: "❤️", "👍")
- `label`: Etiqueta/descripción corta (ej: "Like", "Love")
- `besitos_reward`: Cantidad de besitos otorgados al reaccionar
- `active`: Estado activo/inactivo de la reacción
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

**Restricciones:**
- Emoji debe ser único en el sistema
- `besitos_reward` debe ser >= 1
- Máximo 6 reacciones activas simultáneamente (límite de Telegram)

#### MessageReaction
Modelo que rastrea las reacciones de usuarios a mensajes específicos.

**Campos:**
- `id`: Identificador único de la reacción
- `channel_id`: ID del canal de Telegram donde está el mensaje
- `message_id`: ID del mensaje de Telegram
- `user_id`: ID del usuario que reaccionó (FK a users)
- `emoji`: Emoji de la reacción
- `besitos_awarded`: Cantidad de besitos otorgados en este momento
- `created_at`: Fecha de la reacción

**Restricciones:**
- Un usuario solo puede tener una reacción por mensaje (UniqueConstraint: channel_id, message_id, user_id)

### 2. Servicio de Reacciones (ReactionService)

#### CRUD de Configuración de Reacciones

**Métodos principales:**
- `get_active_reactions()`: Obtiene todas las reacciones activas
- `get_all_reactions(include_inactive)`: Obtiene todas las reacciones (activas e inactivas)
- `get_reaction_by_id(reaction_id)`: Obtiene una reacción por su ID
- `get_reaction_by_emoji(emoji)`: Obtiene una reacción por su emoji
- `create_reaction(emoji, label, besitos_reward)`: Crea una nueva reacción
- `update_reaction(reaction_id, label, besitos_reward, active)`: Actualiza una reacción existente
- `delete_reaction(reaction_id)`: Elimina una reacción (desactiva si tiene histórico)
- `count_active_reactions()`: Cuenta reacciones activas

**Ejemplo de uso:**
```python
# Crear una nueva reacción
reaction = await service.create_reaction(
    emoji="❤️",
    label="Me encanta",
    besitos_reward=5
)

# Actualizar una reacción existente
updated = await service.update_reaction(
    reaction_id=1,
    label="Amor",
    besitos_reward=10
)

# Eliminar una reacción
success = await service.delete_reaction(reaction_id=1)
```

#### Gestión de Reacciones de Usuarios

**Métodos principales:**
- `record_user_reaction(channel_id, message_id, user_id, emoji)`: Registra o actualiza la reacción de un usuario
- `get_user_reaction(channel_id, message_id, user_id)`: Obtiene la reacción de un usuario a un mensaje específico
- `has_user_reacted(channel_id, message_id, user_id)`: Verifica si un usuario ha reaccionado a un mensaje
- `remove_user_reaction(channel_id, message_id, user_id)`: Elimina la reacción de un usuario a un mensaje

**Ejemplo de uso:**
```python
# Registrar la reacción de un usuario
reaction = await service.record_user_reaction(
    channel_id=-1001234567890,
    message_id=12345,
    user_id=987654321,
    emoji="❤️"
)

# Verificar si un usuario ha reaccionado
has_reacted = await service.has_user_reacted(
    channel_id=-1001234567890,
    message_id=12345,
    user_id=987654321
)
```

#### Contadores y Analytics

**Métodos principales:**
- `get_message_reaction_counts(channel_id, message_id)`: Obtiene contadores de reacciones para un mensaje
- `get_message_total_reactions(channel_id, message_id)`: Obtiene el total de reacciones de un mensaje
- `get_user_total_reactions(user_id, channel_id)`: Obtiene el total de reacciones hechas por un usuario
- `get_top_reacted_messages(channel_id, limit)`: Obtiene los mensajes con más reacciones en un canal
- `get_most_used_emoji(channel_id)`: Obtiene el emoji más usado

**Ejemplo de uso:**
```python
# Obtener contadores de un mensaje
counts = await service.get_message_reaction_counts(
    channel_id=-1001234567890,
    message_id=12345
)
# Resultado: {"❤️": 45, "👍": 23, "🔥": 12}

# Obtener los mensajes más reaccionados
top = await service.get_top_reacted_messages(
    channel_id=-1001234567890,
    limit=5
)
# Resultado: [(12345, 68), (12346, 52), ...]
```

### 3. Handlers de Configuración de Reacciones (Admin)

#### Menú Principal de Configuración
- `callback_reactions_config_menu()`: Muestra el menú principal de configuración de reacciones
- Muestra lista de reacciones existentes con estado
- Contador de reacciones activas (X/6)
- Botones para crear nueva reacción y volver al menú admin

#### Vista Detallada de Reacción
- `callback_view_reaction()`: Muestra detalles de una reacción específica
- Emoji, label, puntaje de besitos y estado
- Opciones para editar, activar/desactivar, eliminar y volver

#### Creación de Reacciones
- `callback_create_reaction_start()`: Inicia el flujo de creación de nueva reacción (Paso 1: Emoji)
- `process_create_emoji()`: Procesa el emoji enviado por el admin (Paso 2: Label)
- `process_create_label()`: Procesa el label enviado por el admin (Paso 3: Besitos)
- `process_create_besitos()`: Procesa los besitos y crea la reacción
- `callback_create_cancel()`: Cancela el flujo de creación

#### Edición de Reacciones
- `callback_edit_label_start()`: Inicia edición de label
- `process_edit_label()`: Procesa el nuevo label
- `callback_edit_besitos_start()`: Inicia edición de besitos
- `process_edit_besitos()`: Procesa los nuevos besitos

#### Activación/Desactivación
- `callback_activate_reaction()`: Activa una reacción desactivada
- `callback_deactivate_reaction()`: Desactiva una reacción activa

#### Eliminación
- `callback_delete_reaction_confirm()`: Muestra confirmación antes de eliminar
- `callback_delete_reaction_execute()`: Ejecuta la eliminación (o desactivación si tiene histórico)

### 4. Integración con Broadcasting

#### Estados FSM
- `choosing_options`: Estado para seleccionar opciones de broadcasting (reacciones y protección de contenido)

#### Opciones de Broadcasting
- Adjuntar botones de reacción: Permite adjuntar reacciones a las publicaciones
- Proteger contenido: Restringe reenvío/guardado de la publicación

#### Modificación de send_to_channel
- Parámetro `protect_content`: Si True, restringe reenvío/guardado del contenido
- Actualización del mensaje con keyboard de reacciones si está activada la opción

### 5. Handlers de Reacciones de Usuarios

#### Handler Principal
- `callback_user_reaction()`: Procesa clicks en botones de reacción
- Formato de callback: `react:{emoji}:{channel_id}:{message_id}`
- Valida rate limiting
- Registra reacción en BD
- Otorga besitos
- Actualiza contador en tiempo real
- Responde con feedback

#### Validación de Rate Limiting
- Máximo 50 reacciones por día (últimas 24 horas)
- Mínimo 5 segundos desde la última reacción
- Función: `_validate_rate_limiting(user_id, session)`

#### Otorgamiento de Besitos
- Función: `_award_besitos_for_reaction(user_id, reaction, session, bot)`
- Usa GamificationService para otorgar puntos
- Emite evento MessageReactedEvent al event bus

#### Actualización de Contadores
- Función: `_update_reaction_counter(callback, channel_id, message_id, session)`
- Actualiza el botón de reacción con contadores en tiempo real
- Regenera el keyboard con contadores actualizados

### 6. FSM States

#### ReactionConfigStates
Estados para la configuración de reacciones:
- `waiting_for_emoji`: Esperando emoji para nueva reacción
- `waiting_for_label`: Esperando label descriptivo
- `waiting_for_besitos`: Esperando cantidad de besitos
- `editing_label`: Esperando nuevo label para reacción existente
- `editing_besitos`: Esperando nuevos besitos para reacción existente

#### BroadcastStates
Estados para broadcasting con reacciones:
- `choosing_options`: Estado para seleccionar opciones (reacciones y protección)

### 7. Teclados y UI

#### Keyboard de Reacciones
- Función: `create_reaction_keyboard(reactions, channel_id, message_id, counts)`
- Crea keyboard inline con botones de reacción
- Agrupa botones en filas de máximo 3
- Muestra contadores si están disponibles
- Formato de callback: `react:{emoji}:{channel_id}:{message_id}`

### 8. Integración con Gamificación

El sistema de reacciones está completamente integrado con el sistema de gamificación:
- Cada reacción otorga Besitos al usuario
- Actualiza el progreso de gamificación
- Emite eventos para rastreo y análisis
- Contribuye al ranking y estadísticas del usuario

### 9. Pruebas

#### Pruebas Unitarias (25+ tests)
- CRUD de configuración de reacciones
- Gestión de reacciones de usuarios
- Validaciones de negocio
- Contadores y analytics

#### Pruebas de Integración (11 tests)
- Broadcasting con reacciones
- Disponibilidad de ReactionService en container
- Flujo completo de broadcasting con reacciones

#### Pruebas End-to-End (11 tests)
- Flujo completo de reacción de usuario
- Cambio de reacción
- Rate limiting
- Otorgamiento de besitos
- Validación de reacciones desactivadas
- Contadores de reacciones

## Flujo de Uso

### Para Administradores

1. **Configurar Reacciones**
   - Acceder al menú de configuración de reacciones
   - Crear nuevas reacciones con emoji, label y besitos
   - Activar/desactivar reacciones según sea necesario
   - Editar propiedades existentes

2. **Enviar Publicaciones con Reacciones**
   - Iniciar flujo de broadcasting
   - Enviar contenido multimedia
   - Seleccionar opción de adjuntar reacciones
   - Confirmar envío

### Para Usuarios

1. **Reaccionar a Publicaciones**
   - Ver publicaciones con botones de reacción
   - Hacer click en reacción deseada
   - Recibir feedback de reacción exitosa
   - Ganar besitos por reaccionar

2. **Seguimiento de Progreso**
   - Ver estadísticas de reacciones
   - Contador de besitos ganados
   - Ranking y progreso en gamificación

## Consideraciones Técnicas

### Límites del Sistema
- Máximo 6 reacciones activas simultáneamente (límite de Telegram)
- Rate limiting: 50 reacciones por día por usuario
- Mínimo 5 segundos entre reacciones consecutivas

### Seguridad y Validación
- Validación de emojis únicos
- Validación de besitos >= 1
- Rate limiting para prevenir abuso
- Validación de estado activo de reacciones

### Rendimiento
- Índices optimizados para consultas frecuentes
- Contadores en tiempo real sin impacto en rendimiento
- Manejo eficiente de bases de datos SQLite

## Migración de Base de Datos

La implementación incluye una migración Alembic para crear las tablas necesarias:

- `reaction_configs`: Tabla para configuración de reacciones
- `message_reactions`: Tabla para rastrear reacciones de usuarios

La migración incluye índices para optimizar consultas frecuentes y restricciones para mantener integridad de datos.