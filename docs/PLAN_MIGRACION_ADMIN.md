# PLAN DE MIGRACIÓN: dev4-ondaD → admin
## Administración de Canales VIP/Free

**Fecha:** 2025-01-21
**Rama origen:** dev4-ondaD
**Rama destino:** admin
**Alcance:** SOLO funcionalidades de administración de canales

---

## 📋 RESUMEN EJECUTIVO

Este plan migra las funcionalidades de administración de canales desde dev4-ondaD a admin, organizadas en 3 sprints con dependencias claras.

**Exclusiones explícitas:**
- ❌ Sistema de narrativa (handlers, services, modelos)
- ❌ Sistema de gamificación (badges, niveles, misiones)
- ❌ LucienVoiceService completo (solo mensajes básicos si necesario)
- ❌ Arquetipos y personalización avanzada
- ❌ Sistema de conversión/reengagement

---

## 🎯 SPRINT 1: CORE - Sistema de Solicitudes Free

**Objetivo:** Implementar el nuevo flujo de solicitudes Free con ChatJoinRequest

**Duración estimada:** 1 sesión

### Tareas

#### S1.T1: Crear handler ChatJoinRequest
**Archivo nuevo:** `bot/handlers/user/free_join_request.py`

```python
# Copiar desde dev4-ondaD y adaptar:
# - Eliminar dependencias de LucienVoice
# - Simplificar mensajes a texto plano con HTML básico
# - Mantener lógica de negocio intacta
```

**Funcionalidades:**
- [x] Router `free_join_router` con middleware de DB
- [x] Handler `handle_free_join_request()` para ChatJoinRequest
- [x] Verificar canal Free configurado
- [x] Verificar canal correcto (seguridad)
- [x] Detectar solicitudes duplicadas
- [x] Crear nueva solicitud si no existe
- [x] Notificar usuario con tiempo de espera
- [x] Mostrar progreso si solicitud duplicada

**Dependencias:** Ninguna

---

#### S1.T2: Agregar métodos en SubscriptionService
**Archivo:** `bot/services/subscription.py`

**Métodos nuevos a agregar:**

```python
async def create_free_request_from_join_request(
    self,
    user_id: int,
    from_chat_id: str
) -> Tuple[bool, str, Optional[FreeChannelRequest]]:
    """
    Crea solicitud Free desde ChatJoinRequest.

    - Verifica duplicados
    - Crea nueva solicitud si no existe
    - Retorna (success, message, request)
    """

async def approve_ready_free_requests(
    self,
    wait_time_minutes: int,
    free_channel_id: str
) -> Tuple[int, int]:
    """
    Aprueba solicitudes que cumplieron tiempo de espera.

    - Usa approve_chat_join_request() de Telegram
    - Retorna (success_count, error_count)
    """
```

**Dependencias:** S1.T1

---

#### S1.T3: Actualizar Background Tasks
**Archivo:** `bot/background/tasks.py`

**Cambios:**
- Modificar `process_free_queue()` para usar `approve_ready_free_requests()`
- Usar `approve_chat_join_request()` en lugar de enviar invite links
- Mejorar logging

**Antes (admin):**
```python
# Envía invite links por DM
await container.subscription.process_free_queue(wait_time)
```

**Después (migrado):**
```python
# Aprueba directamente con Telegram API
success, errors = await container.subscription.approve_ready_free_requests(
    wait_time_minutes=wait_time,
    free_channel_id=free_channel_id
)
```

**Dependencias:** S1.T2

---

#### S1.T4: Registrar Router en main.py
**Archivo:** `main.py`

```python
from bot.handlers.user.free_join_request import free_join_router

# En setup de routers:
dp.include_router(free_join_router)
```

**Dependencias:** S1.T1

---

#### S1.T5: Actualizar __init__.py de handlers
**Archivo:** `bot/handlers/user/__init__.py`

```python
from bot.handlers.user.free_join_request import free_join_router

__all__ = [
    "user_router",
    "free_join_router",  # NUEVO
]
```

**Dependencias:** S1.T1

---

### Validación Sprint 1

```bash
# Tests a ejecutar:
pytest tests/test_free_join_request.py -v

# Validaciones manuales:
1. Usuario solicita unirse a canal Free
2. Bot recibe ChatJoinRequest
3. Bot registra solicitud en BD
4. Bot notifica usuario con tiempo de espera
5. Background task aprueba automáticamente
6. Usuario queda en canal Free
```

---

## 🎯 SPRINT 2: MEJORAS - Broadcasting con Preview

**Objetivo:** Agregar vista previa antes de enviar publicaciones

**Duración estimada:** 1 sesión

### Tareas

#### S2.T1: Actualizar Estados FSM de Broadcast
**Archivo:** `bot/states/admin.py`

```python
class BroadcastStates(StatesGroup):
    """Estados para flujo de broadcasting."""
    waiting_for_content = State()      # Esperando contenido
    waiting_for_confirmation = State()  # NUEVO: Confirmación tras preview
```

**Dependencias:** Ninguna

---

#### S2.T2: Refactorizar Handler de Broadcast
**Archivo:** `bot/handlers/admin/broadcast.py`

**Cambios principales:**

1. **Handler para iniciar broadcast:**
```python
@admin_router.callback_query(F.data == "vip:broadcast")
async def callback_broadcast_to_vip(callback, state):
    # Guardar destino en FSM
    await state.set_data({"target_channel": "vip"})
    await state.set_state(BroadcastStates.waiting_for_content)
    # Mostrar instrucciones
```

2. **Handler para recibir contenido (texto):**
```python
@admin_router.message(BroadcastStates.waiting_for_content, F.text)
async def process_broadcast_text(message, session, state):
    # Guardar contenido en FSM
    # Mostrar preview
    # Pedir confirmación
```

3. **Handler para recibir contenido (foto):**
```python
@admin_router.message(BroadcastStates.waiting_for_content, F.photo)
async def process_broadcast_photo(message, session, state):
    # Guardar photo_id y caption
    # Mostrar preview (reenviar foto)
    # Pedir confirmación
```

4. **Handler para recibir contenido (video):**
```python
@admin_router.message(BroadcastStates.waiting_for_content, F.video)
async def process_broadcast_video(message, session, state):
    # Guardar video_id y caption
    # Mostrar preview
    # Pedir confirmación
```

5. **Handler para confirmar envío:**
```python
@admin_router.callback_query(F.data == "broadcast:confirm")
async def callback_broadcast_confirm(callback, session, state):
    # Obtener datos de FSM
    # Enviar a canal destino
    # Notificar éxito
    # Limpiar estado
```

6. **Handler para cancelar:**
```python
@admin_router.callback_query(F.data == "broadcast:cancel")
async def callback_broadcast_cancel(callback, state):
    # Limpiar estado
    # Volver al menú
```

**Dependencias:** S2.T1

---

#### S2.T3: Crear función de Preview
**Archivo:** `bot/handlers/admin/broadcast.py`

```python
async def _show_broadcast_preview(
    message: Message,
    content_type: str,  # "text", "photo", "video"
    content_data: dict,  # {"text": ..., "photo_id": ..., "caption": ...}
    target_channel: str  # "vip" o "free"
) -> None:
    """
    Muestra preview del mensaje antes de enviar.

    - Texto: Muestra en mensaje
    - Foto: Reenvía la foto con caption
    - Video: Reenvía el video con caption
    """
```

**Dependencias:** S2.T2

---

#### S2.T4: Keyboards para Broadcast
**Archivo:** `bot/utils/keyboards.py`

```python
def broadcast_preview_keyboard() -> InlineKeyboardMarkup:
    """Keyboard para preview de broadcast."""
    return create_inline_keyboard([
        [
            {"text": "✅ Confirmar Envío", "callback_data": "broadcast:confirm"},
            {"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}
        ],
        [{"text": "✏️ Editar", "callback_data": "broadcast:edit"}]
    ])

def broadcast_cancel_keyboard() -> InlineKeyboardMarkup:
    """Keyboard solo para cancelar."""
    return create_inline_keyboard([
        [{"text": "❌ Cancelar", "callback_data": "broadcast:cancel"}]
    ])
```

**Dependencias:** Ninguna

---

### Validación Sprint 2

```bash
# Validaciones manuales:
1. Admin inicia broadcast a VIP
2. Admin envía texto → Ve preview → Confirma → Envía
3. Admin envía foto → Ve preview → Confirma → Envía
4. Admin envía video → Ve preview → Confirma → Envía
5. Admin cancela en cualquier momento → Vuelve a menú
6. Admin edita → Puede modificar contenido
```

---

## 🎯 SPRINT 3: MEJORAS UI - Menús y Mensajes

**Objetivo:** Mejorar la experiencia de usuario en menús de admin

**Duración estimada:** 1 sesión

### Tareas

#### S3.T1: Actualizar Menú VIP
**Archivo:** `bot/handlers/admin/vip.py`

**Cambios en keyboard:**

```python
def vip_menu_keyboard(is_configured: bool) -> InlineKeyboardMarkup:
    buttons = []

    if is_configured:
        buttons.extend([
            [{"text": "🎟️ Generar Token", "callback_data": "vip:generate_token"}],
            [
                {"text": "👥 Suscriptores", "callback_data": "vip:list_subscribers"},
                {"text": "📊 Estadísticas", "callback_data": "admin:stats:vip"}
            ],
            [{"text": "📤 Enviar Publicación", "callback_data": "vip:broadcast"}],
            [{"text": "⚙️ Configuración", "callback_data": "vip:config"}],
        ])
    else:
        buttons.append([{"text": "⚙️ Configurar Canal VIP", "callback_data": "vip:setup"}])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:main"}])
    return create_inline_keyboard(buttons)
```

**Nuevo handler vip:config:**

```python
@admin_router.callback_query(F.data == "vip:config")
async def callback_vip_config(callback, session):
    """Submenú de configuración VIP."""
    text = (
        "⚙️ <b>Configuración Canal VIP</b>\n\n"
        "Selecciona una opción:"
    )

    keyboard = create_inline_keyboard([
        [{"text": "💰 Gestión de Tarifas", "callback_data": "admin:pricing"}],
        [{"text": "🔧 Reconfigurar Canal", "callback_data": "vip:setup"}],
        [{"text": "🔙 Volver", "callback_data": "admin:vip"}]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
```

**Dependencias:** Ninguna

---

#### S3.T2: Actualizar Menú Free
**Archivo:** `bot/handlers/admin/free.py`

**Cambios en keyboard:**

```python
def free_menu_keyboard(is_configured: bool) -> InlineKeyboardMarkup:
    buttons = []

    if is_configured:
        buttons.extend([
            [{"text": "📤 Enviar Publicación", "callback_data": "free:broadcast"}],
            [{"text": "📋 Cola de Solicitudes", "callback_data": "free:view_queue"}],
            [{"text": "⚙️ Configuración", "callback_data": "free:config"}],
        ])
    else:
        buttons.append([{"text": "⚙️ Configurar Canal Free", "callback_data": "free:setup"}])

    buttons.append([{"text": "🔙 Volver", "callback_data": "admin:main"}])
    return create_inline_keyboard(buttons)
```

**Nuevo handler free:config:**

```python
@admin_router.callback_query(F.data == "free:config")
async def callback_free_config(callback, session):
    """Submenú de configuración Free."""
    container = ServiceContainer(session, callback.bot)
    wait_time = await container.config.get_wait_time()

    text = (
        "⚙️ <b>Configuración Canal Free</b>\n\n"
        f"⏱️ Tiempo de espera actual: <b>{wait_time} minutos</b>\n\n"
        "Selecciona una opción:"
    )

    keyboard = create_inline_keyboard([
        [{"text": "⏱️ Cambiar Tiempo de Espera", "callback_data": "free:set_wait_time"}],
        [{"text": "🔧 Reconfigurar Canal", "callback_data": "free:setup"}],
        [{"text": "🔙 Volver", "callback_data": "admin:free"}]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
```

**Dependencias:** Ninguna

---

#### S3.T3: Mejorar Mensajes de Error/Confirmación
**Archivo:** `bot/utils/messages.py` (NUEVO - opcional)

```python
"""
Mensajes estándar para el bot.
Centraliza textos para consistencia.
"""

# Errores
ERROR_CHANNEL_NOT_CONFIGURED = (
    "⚠️ <b>Canal no configurado</b>\n\n"
    "El canal {channel_type} no está configurado.\n"
    "Configúralo primero desde el menú de administración."
)

ERROR_INVALID_FORWARD = (
    "❌ <b>Mensaje inválido</b>\n\n"
    "Debes <b>reenviar</b> un mensaje del canal.\n"
    "No envíes el ID manualmente."
)

ERROR_NOT_CHANNEL = (
    "❌ <b>No es un canal</b>\n\n"
    "El mensaje debe ser de un <b>canal</b> o <b>supergrupo</b>."
)

# Confirmaciones
SUCCESS_CHANNEL_CONFIGURED = (
    "✅ <b>Canal {channel_type} Configurado</b>\n\n"
    "Canal: <b>{channel_name}</b>\n"
    "ID: <code>{channel_id}</code>"
)

SUCCESS_TOKEN_GENERATED = (
    "🎟️ <b>Token VIP Generado</b>\n\n"
    "Token: <code>{token}</code>\n"
    "Válido por: <b>{duration} horas</b>\n\n"
    "🔗 Deep Link:\n"
    "<code>{deep_link}</code>\n\n"
    "Comparte este link con el usuario."
)

# Notificaciones Free
NOTIFY_FREE_REQUEST_CREATED = (
    "👋 <b>Solicitud Registrada</b>\n\n"
    "📺 Canal: <b>{channel_name}</b>\n\n"
    "✅ Tu solicitud está en cola.\n"
    "⏱️ Tiempo de espera: <b>{wait_time} minutos</b>\n\n"
    "Serás aprobado automáticamente. ¡Gracias por tu paciencia!"
)

NOTIFY_FREE_REQUEST_DUPLICATE = (
    "ℹ️ <b>Solicitud Existente</b>\n\n"
    "Ya tienes una solicitud pendiente.\n\n"
    "⏱️ Tiempo transcurrido: <b>{elapsed} min</b>\n"
    "⏳ Tiempo restante: <b>{remaining} min</b>\n\n"
    "No necesitas solicitar de nuevo."
)
```

**Dependencias:** Ninguna

---

#### S3.T4: Agregar Barra de Progreso
**Archivo:** `bot/utils/formatters.py`

```python
def format_progress_bar(
    current: int,
    total: int,
    length: int = 10,
    fill: str = "▓",
    empty: str = "░"
) -> str:
    """
    Genera barra de progreso visual.

    Args:
        current: Valor actual
        total: Valor total
        length: Longitud de la barra
        fill: Caracter para parte llena
        empty: Caracter para parte vacía

    Returns:
        String con barra de progreso

    Example:
        >>> format_progress_bar(3, 10, 10)
        "▓▓▓░░░░░░░ 30%"
    """
    if total <= 0:
        return empty * length + " 0%"

    progress = min(current / total, 1.0)
    filled_length = int(length * progress)
    bar = fill * filled_length + empty * (length - filled_length)
    percentage = int(progress * 100)

    return f"{bar} {percentage}%"


def format_progress_with_time(
    remaining_minutes: int,
    total_minutes: int,
    length: int = 15
) -> str:
    """
    Genera barra de progreso con tiempo restante.

    Example:
        >>> format_progress_with_time(3, 10)
        "▓▓▓▓▓▓▓▓▓▓░░░░░ 70% (3 min restantes)"
    """
    elapsed = total_minutes - remaining_minutes
    bar = format_progress_bar(elapsed, total_minutes, length)
    return f"{bar} ({remaining_minutes} min restantes)"
```

**Dependencias:** Ninguna

---

### Validación Sprint 3

```bash
# Validaciones manuales:
1. Menú VIP muestra botones en 2 columnas
2. Menú VIP tiene opción "Configuración"
3. Submenú VIP config funciona correctamente
4. Menú Free tiene opción "Configuración"
5. Submenú Free config muestra tiempo actual
6. Mensajes de error son claros y consistentes
7. Barra de progreso se muestra correctamente
```

---

## 📊 RESUMEN DE SPRINTS

| Sprint | Objetivo | Archivos | Prioridad |
|--------|----------|----------|-----------|
| S1 | Sistema ChatJoinRequest | 5 archivos | 🔴 CRÍTICA |
| S2 | Broadcasting con Preview | 3 archivos | 🟠 ALTA |
| S3 | Mejoras UI/UX | 4 archivos | 🟡 MEDIA |

---

## 📁 ARCHIVOS A CREAR/MODIFICAR

### Archivos Nuevos
```
bot/handlers/user/free_join_request.py  (S1)
bot/utils/messages.py                    (S3 - opcional)
```

### Archivos a Modificar
```
bot/services/subscription.py            (S1)
bot/background/tasks.py                 (S1)
bot/handlers/user/__init__.py           (S1)
main.py                                 (S1)
bot/states/admin.py                     (S2)
bot/handlers/admin/broadcast.py         (S2)
bot/utils/keyboards.py                  (S2)
bot/handlers/admin/vip.py               (S3)
bot/handlers/admin/free.py              (S3)
bot/utils/formatters.py                 (S3)
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Sprint 1 - Core
- [ ] S1.T1: Crear free_join_request.py
- [ ] S1.T2: Agregar métodos en subscription.py
- [ ] S1.T3: Actualizar background/tasks.py
- [ ] S1.T4: Registrar router en main.py
- [ ] S1.T5: Actualizar __init__.py
- [ ] Validar flujo completo

### Sprint 2 - Broadcasting
- [ ] S2.T1: Actualizar estados FSM
- [ ] S2.T2: Refactorizar handlers broadcast
- [ ] S2.T3: Crear función preview
- [ ] S2.T4: Agregar keyboards
- [ ] Validar flujo completo

### Sprint 3 - UI/UX
- [ ] S3.T1: Actualizar menú VIP
- [ ] S3.T2: Actualizar menú Free
- [ ] S3.T3: Centralizar mensajes (opcional)
- [ ] S3.T4: Agregar barra de progreso
- [ ] Validar cambios visuales

---

## 🚀 ORDEN DE EJECUCIÓN

```
1. Cambiar a rama admin
   git checkout admin

2. Crear rama de feature
   git checkout -b feature/channel-admin-improvements

3. Ejecutar Sprint 1 (Core)
   - Implementar tareas S1.T1 a S1.T5
   - Validar
   - Commit: "feat: implementar sistema ChatJoinRequest para Free"

4. Ejecutar Sprint 2 (Broadcasting)
   - Implementar tareas S2.T1 a S2.T4
   - Validar
   - Commit: "feat: agregar preview en broadcasting"

5. Ejecutar Sprint 3 (UI/UX)
   - Implementar tareas S3.T1 a S3.T4
   - Validar
   - Commit: "feat: mejorar UI de menús admin"

6. Merge a admin
   git checkout admin
   git merge feature/channel-admin-improvements

7. Push
   git push origin admin
```

---

## 📝 NOTAS IMPORTANTES

1. **Sin LucienVoice:** Los mensajes se mantienen en HTML plano
2. **Sin Narrativa:** No se incluye ningún handler de narrativa
3. **Sin Gamificación:** No se incluye ningún handler de gamificación
4. **Compatibilidad:** Mantener compatibilidad con código existente
5. **Tests:** Agregar tests básicos para nuevas funcionalidades

---

**Documento creado:** 2025-01-21
**Autor:** Migración automatizada
**Versión:** 1.0
