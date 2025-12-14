# Sistema de Deep Links

Documentación del sistema de deep links del bot VIP/Free para activación automática de tokens VIP.

## Descripción General

El sistema de deep links permite a los usuarios activar suscripciones VIP automáticamente haciendo click en un enlace especial. El formato del deep link es `https://t.me/botname?start=TOKEN`, lo que facilita la distribución y activación de tokens VIP de manera profesional y automática.

## Componentes del Sistema

### 1. Handler de Inicio con Deep Links

**Ubicación:** `bot/handlers/user/start.py`

**Responsabilidades:**
- Detectar parámetros en el comando `/start`
- Activar tokens VIP automáticamente desde deep links
- Actualizar roles de usuarios según activación
- Manejar flujos normales de usuarios sin deep links

**Método Principal:**

#### `cmd_start(message, session)`
Handler del comando `/start` que detecta si hay parámetro (deep link) y activa automáticamente el token.

**Flujo de ejecución:**
1. Verifica si hay parámetro en `/start` (deep link)
2. Si hay parámetro → Activa token automáticamente
3. Si no hay parámetro → Muestra mensaje de bienvenida normal
4. Maneja la lógica de roles y permisos

**Formato de Deep Link:**
- `/start` → Mensaje de bienvenida normal
- `/start TOKEN` → Activa token VIP automáticamente (deep link)

### 2. Activación Automática desde Deep Link

**Método:** `_activate_token_from_deeplink(message, session, container, user, token_string)`

**Responsabilidades:**
- Validar el token recibido desde el deep link
- Marcar el token como usado en la base de datos
- Activar la suscripción VIP para el usuario
- Actualizar el rol del usuario a VIP
- Generar y enviar invite link al canal VIP

### 3. Generación de Deep Links Profesionales

**Ubicación:** `bot/handlers/admin/vip.py`

**Método:** `callback_generate_token_with_plan`

**Responsabilidades:**
- Generar token VIP vinculado a una tarifa específica
- Crear deep link profesional con formato: `https://t.me/bot?start=TOKEN`
- Mostrar el deep link para que el administrador lo comparta

## Formato de Deep Links

### Formato Estándar

```
https://t.me/botname?start=TOKEN
```

**Componentes:**
- `https://t.me/botname`: URL base del bot
- `?start=TOKEN`: Parámetro que activa la lógica de deep link
- `TOKEN`: Token VIP de 16 caracteres alfanuméricos

### Ejemplo de Deep Link

```
https://t.me/mi_bot_vip?start=ABCD1234EFGH5678
```

## Flujos de Uso

### Flujo Completo de Deep Link

1. **Generación del Token:**
   - Administrador selecciona "Generar Token con Plan" en el panel de administración
   - Sistema genera token VIP único y lo asocia a un plan de suscripción
   - Sistema crea deep link profesional: `https://t.me/bot?start=TOKEN`

2. **Distribución del Deep Link:**
   - Administrador copia el deep link generado
   - Administrador comparte el deep link con el cliente potencial
   - Cliente recibe el enlace directo para activar su suscripción

3. **Activación Automática:**
   - Cliente hace click en el deep link
   - Telegram abre el bot con el parámetro `start=TOKEN`
   - Bot detecta el parámetro y activa automáticamente la suscripción
   - Usuario recibe confirmación y acceso al canal VIP

4. **Proceso Automático:**
   - Validación del token
   - Actualización del rol a VIP
   - Generación de invite link al canal VIP
   - Notificación al usuario

### Ejemplo de Interacción

**Cliente hace click en:** `https://t.me/mi_bot_vip?start=ABCD1234EFGH5678`

**Bot responde:**
```
🎉 ¡Suscripción VIP Activada!

Plan: Plan Mensual Premium
Precio: $9.99
Duración: 30 días
Días Restantes: 30

⭐ Tu rol ha sido actualizado a: Usuario VIP

━━━━━━━━━━━━━━━━━━━━
Siguiente Paso:

Haz click en el botón de abajo para unirte al canal VIP exclusivo.

⚠️ El link expira en 5 horas.
```

## Integración con Otros Sistemas

### Sistema de Precios

- Los deep links están asociados a planes de suscripción específicos
- Al activar el token, se muestra información del plan: nombre, precio, duración
- Se actualiza el rol del usuario según el plan asociado

### Sistema de Roles

- Al activar un token desde deep link, el rol del usuario cambia a VIP
- Se actualiza el rol en la base de datos automáticamente
- El usuario recibe confirmación de cambio de rol

### Sistema de Canales

- Al activar el token, se genera automáticamente un invite link al canal VIP
- El invite link tiene validez limitada (por defecto: 5 horas)
- El invite link es de un solo uso

## Validaciones y Seguridad

### Validaciones del Token

- Verifica que el token exista en la base de datos
- Verifica que el token no haya sido usado previamente
- Verifica que el token no haya expirado
- Verifica que el plan asociado sea válido

### Seguridad del Sistema

- Solo tokens válidos pueden activar suscripciones
- Los tokens se marcan como usados inmediatamente después de la activación
- Se registra en logs cada activación desde deep link
- Se verifica que el canal VIP esté configurado antes de generar invite links

## Beneficios del Sistema de Deep Links

1. **Profesionalismo:** Deep links con formato limpio y profesional
2. **Automatización:** Activación automática sin intervención manual
3. **Facilidad de Distribución:** Enlaces fáciles de compartir
4. **Experiencia de Usuario:** Proceso de activación simplificado
5. **Seguimiento:** Registro de activaciones y métricas de conversión
6. **Seguridad:** Validaciones múltiples para prevenir abusos

## Comandos y Handlers Relacionados

### Generación de Tokens con Deep Links

**Ubicación:** `bot/handlers/admin/vip.py`

- `callback_generate_token_with_plan`: Genera token VIP con deep link profesional
- Crea el formato: `https://t.me/bot_username?start=TOKEN`
- Muestra botón "🔗 Copiar Link" para facilitar la distribución

### Activación desde Deep Link

**Ubicación:** `bot/handlers/user/start.py`

- `cmd_start`: Detecta parámetros y activa tokens automáticamente
- `_activate_token_from_deeplink`: Procesa la activación del token
- Actualiza roles y genera invite links

## Ejemplos de Implementación

### Ejemplo de Deep Link con Plan Asociado

```
Formato: https://t.me/bot_username?start=TOKEN
Ejemplo: https://t.me/mi_bot_vip?start=ABCD1234EFGH5678
```

### Mensaje de Confirmación

```
✅ Usuario 123456789 activado como VIP vía deep link | Plan: Plan Mensual Premium
```

### Registro en Logs

```
[INFO] 🔗 Deep link detectado: Token=ABCD1234EFGH5678 | User=123456789
[INFO] ✅ Usuario 123456789 activado como VIP vía deep link | Plan: Plan Mensual Premium
```

## Pruebas y Validación

### Casos de Prueba

1. **Activación válida:** Token correcto → Activación exitosa
2. **Token inválido:** Token incorrecto → Mensaje de error
3. **Token ya usado:** Token usado previamente → Mensaje de error
4. **Token expirado:** Token fuera de validez → Mensaje de error
5. **Canal no configurado:** Canal VIP no configurado → Mensaje de error

### Pruebas Automatizadas

**Ubicación:** `tests/test_a3_deep_links.py`

- `test_activate_vip_from_deep_link`: Activar suscripción desde deep link
- `test_deep_link_format`: Validar formato correcto del deep link
- `test_extend_vip_via_deep_link`: Extender suscripción existente
- `test_generate_token_with_plan`: Generar token con deep link
- `test_token_expiry_validation`: Validación de expiración
- `test_token_single_use`: Validación de uso único

## Consideraciones Técnicas

### Manejo de Errores

- Errores de validación del token
- Errores de generación de invite links
- Errores de base de datos durante la activación
- Errores de API de Telegram

### Performance

- Validación eficiente de tokens
- Caching de información de planes
- Manejo asincrónico de operaciones

---

**Última actualización:** 2025-12-13
**Versión:** 1.0.0
**Estado:** Documentación completa del sistema de deep links