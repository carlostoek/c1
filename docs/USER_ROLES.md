# Sistema de Roles de Usuario

Documentación del sistema de roles de usuario del bot VIP/Free.

## Descripción General

El sistema de roles de usuario permite clasificar a los usuarios en diferentes categorías con permisos y funcionalidades específicas. El sistema implementa un modelo de roles jerárquico con tres niveles principales: FREE, VIP y ADMIN.

## Componentes del Sistema

### 1. UserRole Enum

**Ubicación:** `bot/database/enums.py`

**Definición:**
```python
class UserRole(str, Enum):
    FREE = "free"      # Usuario con acceso al canal Free (default)
    VIP = "vip"        # Usuario con suscripción VIP activa
    ADMIN = "admin"    # Administrador del bot
```

**Atributos:**
- `display_name`: Nombre legible del rol (ej: "Usuario Free", "Usuario VIP", "Administrador")
- `emoji`: Emoji representativo del rol (ej: "🆓", "⭐", "👑")

### 2. UserService

**Ubicación:** `bot/services/user.py`

**Responsabilidades:**
- Crear/actualizar usuarios
- Obtener usuarios por ID
- Cambiar roles
- Verificar permisos
- Listar usuarios por rol

**Métodos Principales:**

#### `get_or_create_user(telegram_user, default_role=UserRole.FREE)`
Obtiene un usuario existente o lo crea si no existe.

**Parámetros:**
- `telegram_user`: Objeto User de Telegram
- `default_role`: Rol por defecto si se crea (default: FREE)

**Ejemplo:**
```python
user = await service.get_or_create_user(message.from_user)
```

#### `get_user(user_id)`
Obtiene un usuario por ID.

**Parámetros:**
- `user_id`: ID de Telegram del usuario

#### `change_role(user_id, new_role, reason="Manual")`
Cambia el rol de un usuario.

**Parámetros:**
- `user_id`: ID del usuario
- `new_role`: Nuevo rol a asignar
- `reason`: Razón del cambio (para logging)

**Ejemplo:**
```python
await service.change_role(123456, UserRole.VIP, "Token activado")
```

#### `promote_to_vip(user_id)`
Promociona un usuario a VIP.

**Parámetros:**
- `user_id`: ID del usuario

#### `demote_to_free(user_id)`
Degrada un usuario a Free.

**Parámetros:**
- `user_id`: ID del usuario

#### `promote_to_admin(user_id)`
Promociona un usuario a Admin (uso manual).

**Parámetros:**
- `user_id`: ID del usuario

#### `is_admin(user_id)`
Verifica si un usuario es admin.

**Parámetros:**
- `user_id`: ID del usuario

**Retorna:** True si es admin, False si no

#### `get_users_by_role(role)`
Obtiene todos los usuarios con un rol específico.

**Parámetros:**
- `role`: Rol a filtrar

### 3. User Model

**Ubicación:** `bot/database/models.py`

**Atributos:**
- `user_id`: ID único de Telegram (Primary Key)
- `username`: Username de Telegram (puede ser None)
- `first_name`: Nombre del usuario
- `last_name`: Apellido (puede ser None)
- `role`: Rol actual del usuario (FREE/VIP/ADMIN)
- `created_at`: Fecha de primer contacto con el bot
- `updated_at`: Última actualización de datos

**Propiedades:**
- `full_name`: Retorna nombre completo del usuario
- `mention`: Retorna mention HTML del usuario
- `is_admin`: Verifica si el usuario es admin
- `is_vip`: Verifica si el usuario es VIP
- `is_free`: Verifica si el usuario es Free

## Transiciones de Roles

### Transiciones Automáticas

1. **Nuevo usuario → FREE**
   - Ocurre cuando un usuario interactúa por primera vez con el bot
   - Rol por defecto asignado en `get_or_create_user`

2. **Activar token VIP → VIP**
   - Ocurre cuando un usuario canjea un token VIP válido
   - Actualización automática del rol en la base de datos

3. **Expirar suscripción → FREE**
   - Ocurre cuando la suscripción VIP de un usuario expira
   - Procesado por la tarea en segundo plano de expulsión de VIPs expirados

### Transiciones Manuales

1. **Asignación manual → ADMIN**
   - Realizada por otros administradores
   - Uso del método `promote_to_admin`

2. **Cambio de rol por administrador**
   - Uso del método `change_role` con motivo específico

## Flujos de Uso

### Registro de Nuevo Usuario

1. Usuario envía `/start` al bot
2. Bot llama a `get_or_create_user` con rol FREE por defecto
3. Usuario se registra en la base de datos con rol FREE
4. Bot muestra menú de usuario (VIP/Free)

### Activación de Suscripción VIP

1. Usuario ingresa token VIP o hace click en deep link
2. Bot valida el token y lo activa
3. Bot actualiza el rol del usuario a VIP en la base de datos
4. Bot envía mensaje de bienvenida con información VIP

### Verificación de Permisos de Administrador

1. Handler verifica si el usuario es admin con `is_admin`
2. Si es admin, se le muestra el panel de administración
3. Si no es admin, se le muestra el menú de usuario normal

### Degradación de Suscripción Expirada

1. Tarea en segundo plano identifica suscriptores VIP expirados
2. Sistema actualiza el rol de los usuarios afectados a FREE
3. Usuarios son expulsados del canal VIP
4. Se registra la transición en los logs

## Integración con Otros Sistemas

### Sistema de Precios

- Los usuarios VIP tienen acceso a planes de suscripción
- Los usuarios FREE no tienen acceso a planes VIP

### Sistema de Canales

- Los usuarios VIP reciben invite links al canal VIP
- Los usuarios FREE reciben acceso al canal Free con tiempo de espera
- Los administradores tienen acceso a todas las funciones

### Sistema de Estadísticas

- Las estadísticas distinguen entre usuarios FREE y VIP
- Se rastrean métricas por rol de usuario
- Se calculan proyecciones de ingresos basadas en usuarios VIP

## Comandos y Handlers Relacionados

### Handler de Inicio

**Ubicación:** `bot/handlers/user/start.py`

- `cmd_start`: Detecta el rol del usuario y proporciona la interfaz correspondiente
- Si es admin → redirige a `/admin`
- Si es VIP → muestra mensaje de bienvenida VIP
- Si es FREE → muestra opciones de usuario FREE

### Verificación de Permisos

**Ubicación:** `bot/middlewares/admin_auth.py`

- `AdminAuthMiddleware`: Verifica que el usuario sea admin antes de ejecutar handlers protegidos
- Uso del método `is_admin` del UserService

## Ejemplos de Interacción

### Usuario FREE

```
👋 Hola Usuario!

Bienvenido al bot de acceso a canales.

Opciones disponibles:

🎟️ Canjear Token VIP
Si tienes un token de invitación, canjéalo para acceso VIP.

📺 Solicitar Acceso Free
Solicita acceso al canal gratuito (con tiempo de espera).

👉 Selecciona una opción:
```

### Usuario VIP

```
👋 Hola Usuario!

✅ Tienes acceso VIP activo
⏱️ Días restantes: 15

Disfruta del contenido exclusivo! 🎉
```

### Usuario ADMIN

```
👋 Hola Usuario!

Eres administrador. Usa /admin para gestionar los canales.
```

## Beneficios del Sistema de Roles

1. **Control de Acceso:** Diferentes niveles de permisos según el rol
2. **Personalización:** Interfaz adaptada al rol del usuario
3. **Automatización:** Transiciones automáticas según el estado
4. **Auditoría:** Registro de cambios de rol con motivos
5. **Escalabilidad:** Fácil extensión para nuevos roles si es necesario

## Consideraciones de Seguridad

- Solo administradores pueden cambiar roles manualmente
- Las transiciones automáticas están validadas y controladas
- Se registra en logs cada cambio de rol
- Verificación de permisos en todos los handlers protegidos

---

**Última actualización:** 2025-12-13
**Versión:** 1.0.0
**Estado:** Documentación completa del sistema de roles de usuario