# Sistema de Precios y Planes de Suscripción

Documentación del sistema de precios y planes de suscripción del bot VIP/Free.

## Descripción General

El sistema de precios permite a los administradores gestionar planes de suscripción configurables con nombre, duración y precio. Estos planes se asocian a tokens VIP generados, permitiendo una estructura de precios profesional y escalable.

## Componentes del Sistema

### 1. PricingService

**Ubicación:** `bot/services/pricing.py`

**Responsabilidades:**
- Crear nuevos planes de suscripción
- Listar planes disponibles
- Obtener planes por ID
- Actualizar planes existentes
- Activar/desactivar planes
- Eliminar planes (si no tienen tokens asociados)

**Métodos Principales:**

#### `create_plan(name, duration_days, price, created_by, currency="$")`
Crea un nuevo plan de suscripción.

**Parámetros:**
- `name`: Nombre del plan (ej: "Plan Mensual")
- `duration_days`: Duración en días
- `price`: Precio del plan
- `created_by`: User ID del admin que crea el plan
- `currency`: Símbolo de moneda (default: "$")

**Ejemplo:**
```python
plan = await service.create_plan(
    name="Plan Mensual",
    duration_days=30,
    price=9.99,
    created_by=123456
)
```

#### `get_all_plans(active_only=True)`
Obtiene todos los planes.

**Parámetros:**
- `active_only`: Si True, solo retorna planes activos (default: True)

#### `get_plan_by_id(plan_id)`
Obtiene un plan por su ID.

**Parámetros:**
- `plan_id`: ID del plan

#### `update_plan(plan_id, name=None, duration_days=None, price=None, currency=None)`
Actualiza un plan existente.

**Parámetros:**
- `plan_id`: ID del plan a actualizar
- `name`: Nuevo nombre (opcional)
- `duration_days`: Nueva duración (opcional)
- `price`: Nuevo precio (opcional)
- `currency`: Nuevo símbolo de moneda (opcional)

#### `toggle_plan_status(plan_id)`
Activa o desactiva un plan.

**Parámetros:**
- `plan_id`: ID del plan

#### `delete_plan(plan_id)`
Elimina un plan (solo si no tiene tokens asociados).

**Parámetros:**
- `plan_id`: ID del plan a eliminar

**Retorna:** True si se eliminó, False si no existe o tiene tokens

### 2. SubscriptionPlan Model

**Ubicación:** `bot/database/models.py`

**Atributos:**
- `id`: ID único del plan
- `name`: Nombre del plan (ej: "Plan Mensual", "Plan Anual")
- `duration_days`: Duración en días del plan
- `price`: Precio del plan (en USD u otra moneda)
- `currency`: Símbolo de moneda (default: "$")
- `active`: Si el plan está activo (visible para generar tokens)
- `created_at`: Fecha de creación
- `created_by`: User ID del admin que creó el plan

**Relaciones:**
- `tokens`: Tokens generados con este plan

### 3. Integración con Generación de Tokens

Cuando se genera un token VIP, se puede asociar a un plan específico:
- El token hereda la duración y precio del plan
- Se crea un deep link profesional con el formato `https://t.me/bot?start=TOKEN`
- El usuario recibe información detallada del plan al activar el token

## Flujos de Uso

### Crear Plan de Suscripción

1. El administrador accede al panel de administración
2. Selecciona la opción de gestionar planes
3. Ingresa los detalles del plan (nombre, duración, precio)
4. El sistema crea el plan y lo almacena en la base de datos
5. El plan aparece en la lista de planes disponibles

### Generar Token con Plan

1. El administrador selecciona un plan existente
2. El sistema genera un token VIP asociado al plan
3. Se crea un deep link profesional: `https://t.me/bot?start=TOKEN`
4. El administrador comparte el deep link con el cliente

### Activar Suscripción desde Deep Link

1. El usuario hace click en el deep link: `https://t.me/bot?start=TOKEN`
2. El bot detecta el parámetro y activa automáticamente la suscripción
3. El usuario recibe información del plan: nombre, precio, duración
4. El sistema genera un invite link al canal VIP

## Configuración y Validaciones

### Validaciones de Planes

- El nombre del plan no puede estar vacío
- La duración debe ser mayor a 0 días
- El precio no puede ser negativo
- Los planes con tokens asociados no pueden eliminarse

### Currencies Soportadas

- Por defecto: "$" (dólar estadounidense)
- Configurable por plan: "€", "£", "¥", etc.
- El símbolo de moneda se muestra en la interfaz de usuario

## Comandos y Handlers Relacionados

### Generación de Tokens con Planes

**Ubicación:** `bot/handlers/admin/vip.py`

- `callback_generate_token_with_plan`: Genera token VIP vinculado a una tarifa específica con deep link
- Crea un deep link profesional con el formato: `https://t.me/bot?start=TOKEN`
- Muestra el deep link para que el administrador lo comparta

### Activación Automática desde Deep Link

**Ubicación:** `bot/handlers/user/start.py`

- `cmd_start`: Maneja el parámetro del deep link
- `_activate_token_from_deeplink`: Activa la suscripción VIP automáticamente cuando el usuario hace click en el deep link
- Actualiza el rol del usuario a VIP en la base de datos

## Ejemplos de Uso

### Ejemplo de Plan de Suscripción

```
Plan: "Plan Mensual Premium"
Duración: 30 días
Precio: $9.99
Moneda: $
Estado: Activo
```

### Ejemplo de Deep Link

```
https://t.me/nombre_bot?start=ABCD1234EFGH5678
```

### Mensaje de Activación

```
🎉 ¡Suscripción VIP Activada!

Plan: Plan Mensual Premium
Precio: $9.99
Duración: 30 días
Días Restantes: 30

⭐ Tu rol ha sido actualizado a: Usuario VIP

Siguiente Paso:
Haz click en el botón de abajo para unirte al canal VIP exclusivo.
```

## Beneficios del Sistema de Precios

1. **Profesionalidad:** Presentación clara de precios y planes
2. **Flexibilidad:** Configuración de múltiples planes con diferentes precios
3. **Automatización:** Activación automática desde deep links
4. **Transparencia:** Información clara sobre duración y costo
5. **Escalabilidad:** Posibilidad de crear nuevos planes según necesidades

## Consideraciones de Seguridad

- Solo administradores pueden crear y gestionar planes
- Los planes inactivos no se muestran para generar tokens
- Validación de datos al crear y actualizar planes
- Control de acceso a la gestión de planes

---

**Última actualización:** 2025-12-13
**Versión:** 1.0.0
**Estado:** Documentación completa del sistema de precios y planes de suscripción