# Comandos del Bot VIP/Free

Documentación completa de los comandos disponibles en el bot de administración de canales VIP y Free.

## Comandos de Administración

### `/admin` - Panel de Administración Principal

**Descripción:** Abre el panel de administración principal con acceso a todas las funciones de gestión.

**Permisos:** Solo administradores (definidos en `ADMIN_USER_IDS`)

**Flujo de uso:**
1. El administrador envía `/admin`
2. El bot verifica permisos y muestra el menú principal
3. Opciones disponibles:
   - Gestión Canal VIP
   - Gestión Canal Free
   - Configuración

**Ejemplo:**
```
/admin
🤖 Panel de Administración
✅ Bot configurado correctamente

Selecciona una opción:
- 📺 Gestión Canal VIP
- 📺 Gestión Canal Free
- ⚙️ Configuración
```

## Submenú VIP

### `Gestión Canal VIP` - Opción del menú admin

**Descripción:** Accede al submenú de gestión del canal VIP.

**Permisos:** Solo administradores

**Funcionalidades:**
- Verificar estado de configuración del canal VIP
- Generar tokens de invitación VIP
- Configurar o reconfigurar el canal VIP

**Flujo de uso:**
1. Seleccionar "Gestión Canal VIP" en el menú principal
2. El bot muestra estado actual del canal VIP
3. Opciones disponibles dependiendo del estado:
   - Si está configurado: "🎟️ Generar Token de Invitación", "🔧 Reconfigurar Canal"
   - Si no está configurado: "⚙️ Configurar Canal VIP"

### `Configurar Canal VIP` - Configuración del canal VIP

**Descripción:** Configura el canal VIP por reenvío de mensajes.

**Permisos:** Solo administradores

**Flujo de uso:**
1. Seleccionar "⚙️ Configurar Canal VIP"
2. El bot solicita reenviar un mensaje del canal VIP
3. El administrador va al canal VIP y reenvía cualquier mensaje al bot
4. El bot extrae automáticamente el ID del canal
5. El bot verifica permisos y configura el canal
6. El bot actualiza el menú con el canal configurado

**Requisitos:**
- El bot debe ser administrador del canal VIP
- El bot debe tener permiso para invitar usuarios

**Ejemplo de interacción:**
```
👉 Reenvía un mensaje del canal ahora...

(Administrador reenvía un mensaje del canal VIP)
✅ Canal VIP Configurado
Canal: Mi Canal VIP
ID: -1001234567890
Ya puedes generar tokens de invitación.
```

### `Generar Token de Invitación` - Creación de tokens VIP

**Descripción:** Genera un token de invitación para acceso VIP.

**Permisos:** Solo administradores

**Flujo de uso:**
1. Asegurarse de que el canal VIP esté configurado
2. Seleccionar "🎟️ Generar Token de Invitación"
3. El bot genera un token único con duración configurable
4. El bot envía el token al administrador
5. El administrador comparte el token con el usuario

**Características del token:**
- 16 caracteres alfanuméricos
- Válido por 24 horas (por defecto)
- Un solo uso
- Se marca como usado después del primer canje

**Ejemplo de token generado:**
```
🎟️ Token VIP Generado

Token: ABCD1234EFGH5678
⏱️ Válido por: 24 horas
📅 Expira: 2025-12-12 10:30 UTC

👉 Comparte este token con el usuario.
El usuario debe enviarlo al bot para canjear acceso VIP.
```

## Submenú Free

### `Gestión Canal Free` - Opción del menú admin

**Descripción:** Accede al submenú de gestión del canal Free.

**Permisos:** Solo administradores

**Funcionalidades:**
- Verificar estado de configuración del canal Free
- Configurar o reconfigurar el canal Free
- Configurar tiempo de espera para acceso Free

**Flujo de uso:**
1. Seleccionar "Gestión Canal Free" en el menú principal
2. El bot muestra estado actual del canal Free y tiempo de espera
3. Opciones disponibles dependiendo del estado:
   - Si está configurado: "⏱️ Configurar Tiempo de Espera", "🔧 Reconfigurar Canal"
   - Si no está configurado: "⚙️ Configurar Canal Free"

### `Configurar Canal Free` - Configuración del canal Free

**Descripción:** Configura el canal Free por reenvío de mensajes.

**Permisos:** Solo administradores

**Flujo de uso:**
1. Seleccionar "⚙️ Configurar Canal Free"
2. El bot solicita reenviar un mensaje del canal Free
3. El administrador va al canal Free y reenvía cualquier mensaje al bot
4. El bot extrae automáticamente el ID del canal
5. El bot verifica permisos y configura el canal
6. El bot actualiza el menú con el canal configurado

**Requisitos:**
- El bot debe ser administrador del canal Free
- El bot debe tener permiso para invitar usuarios

**Ejemplo de interacción:**
```
👉 Reenvía un mensaje del canal ahora...

(Administrador reenvía un mensaje del canal Free)
✅ Canal Free Configurado
Canal: Mi Canal Free
ID: -1000987654321
Los usuarios ya pueden solicitar acceso.
```

### `Configurar Tiempo de Espera` - Configuración del tiempo de espera

**Descripción:** Configura el tiempo de espera para acceso al canal Free.

**Permisos:** Solo administradores

**Flujo de uso:**
1. Asegurarse de que el canal Free esté configurado
2. Seleccionar "⏱️ Configurar Tiempo de Espera"
3. El bot solicita ingresar el nuevo tiempo en minutos
4. El administrador envía el número de minutos
5. El bot valida y actualiza la configuración
6. El bot actualiza el menú con el nuevo tiempo

**Requisitos:**
- El tiempo debe ser al menos 1 minuto
- Solo se aceptan valores numéricos

**Ejemplo de interacción:**
```
⏱️ Configurar Tiempo de Espera

Tiempo actual: 10 minutos

Envía el nuevo tiempo de espera en minutos.
Ejemplo: 5

El tiempo debe ser mayor o igual a 1 minuto.

(Administrador envía: 15)
✅ Tiempo de Espera Actualizado
Nuevo tiempo: 15 minutos
Las nuevas solicitudes esperarán 15 minutos antes de procesarse.
```

## Estadísticas

### `Estadísticas` - Panel de Estadísticas del Sistema

**Descripción:** Accede al panel de estadísticas que proporciona métricas generales y detalladas sobre el sistema, incluyendo información sobre suscriptores VIP, solicitudes Free y tokens de invitación.

**Permisos:** Solo administradores

**Funcionalidades:**
- Visualización de estadísticas generales del sistema
- Estadísticas detalladas de suscriptores VIP
- Estadísticas detalladas de solicitudes Free
- Estadísticas detalladas de tokens de invitación
- Proyecciones de ingresos
- Actualización manual de estadísticas (force refresh)

**Flujo de uso:**
1. El administrador selecciona "📊 Estadísticas" en el menú principal
2. El bot muestra el dashboard de estadísticas generales
3. El administrador puede navegar entre diferentes vistas de estadísticas
4. El bot actualiza automáticamente las estadísticas cada 5 minutos (cache)

### `Ver Stats VIP Detalladas` - Estadísticas de suscriptores VIP

**Descripción:** Muestra estadísticas detalladas sobre los suscriptores VIP, incluyendo activos, expirados, próximos a expirar y actividad reciente.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "📊 Ver Stats VIP Detalladas" en el menú de estadísticas
2. El bot calcula y muestra las métricas VIP detalladas
3. El bot incluye información como:
   - Total de suscriptores activos y expirados
   - Suscriptores que expirarán próximamente (hoy, semana, mes)
   - Nuevos suscriptores (hoy, semana, mes)
   - Top suscriptores por días restantes

### `Ver Stats Free Detalladas` - Estadísticas de solicitudes Free

**Descripción:** Muestra estadísticas detalladas sobre las solicitudes de acceso Free, incluyendo pendientes, procesadas y tiempos de espera.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "📊 Ver Stats Free Detalladas" en el menú de estadísticas
2. El bot calcula y muestra las métricas Free detalladas
3. El bot incluye información como:
   - Total de solicitudes pendientes y procesadas
   - Solicitudes listas para procesar y aún esperando
   - Tiempo promedio de espera
   - Solicitudes próximas a procesar
   - Actividad reciente (hoy, semana, mes)

### `Ver Stats de Tokens` - Estadísticas de tokens de invitación

**Descripción:** Muestra estadísticas detalladas sobre los tokens de invitación VIP, incluyendo generados, usados, expirados y tasa de conversión.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "🎟️ Ver Stats de Tokens" en el menú de estadísticas
2. El bot calcula y muestra las métricas de tokens detalladas
3. El bot incluye información como:
   - Total de tokens generados, usados, expirados y disponibles
   - Tokens generados y usados por período (hoy, semana, mes)
   - Tasa de conversión (tokens usados vs generados)

### `Actualizar Estadísticas` - Forzar recálculo de estadísticas

**Descripción:** Fuerza el recálculo de todas las estadísticas, ignorando el cache actual.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "🔄 Actualizar Estadísticas" en el menú de estadísticas
2. El bot recalcula todas las métricas desde la base de datos
3. El bot muestra las estadísticas actualizadas inmediatamente
4. El cache se actualiza con los nuevos valores

## Configuración Avanzada

### `Configuración` - Panel de Configuración Avanzada

**Descripción:** Accede al panel de configuración avanzada que permite gestionar las opciones de reacciones y otras configuraciones del sistema.

**Permisos:** Solo administradores

**Funcionalidades:**
- Visualización del estado actual de configuración
- Configuración de reacciones para canales VIP y Free
- Verificación de parámetros de configuración

**Flujo de uso:**
1. El administrador selecciona "⚙️ Configuración" en el menú principal
2. El bot muestra el menú de configuración con las opciones disponibles
3. El administrador puede navegar entre diferentes opciones de configuración

### `Configurar Reacciones VIP` - Configuración de reacciones para canal VIP

**Descripción:** Configura las reacciones automáticas que se aplicarán a las publicaciones en el canal VIP.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "⚙️ Configurar Reacciones VIP" en el menú de configuración
2. El bot muestra las reacciones actuales y solicita ingresar nuevos emojis
3. El administrador envía los emojis separados por espacios
4. El bot valida y guarda las nuevas reacciones
5. El bot actualiza la configuración y notifica el cambio

**Requisitos:**
- Mínimo 1 emoji
- Máximo 10 emojis
- Solo emojis válidos

**Ejemplo de interacción:**
```
⚙️ Configurar Reacciones VIP

Reacciones actuales: 👍 ❤️ 🔥 🎉 💯

Envía los emojis que quieres usar como reacciones, separados por espacios.
Ejemplo: 👍 ❤️ 🔥

Reglas:
• Mínimo: 1 emoji
• Máximo: 10 emojis
• Solo emojis válidos

Las reacciones se aplicarán automáticamente a nuevas publicaciones en el canal VIP.

(Administrador envía: 👍 ❤️ 🌟 💯 ✨)
✅ Reacciones VIP Configuradas
Reacciones: 👍 ❤️ 🌟 💯 ✨
Total: 5 emojis
Estas reacciones se aplicarán automáticamente a nuevas publicaciones en el canal VIP.
```

### `Configurar Reacciones Free` - Configuración de reacciones para canal Free

**Descripción:** Configura las reacciones automáticas que se aplicarán a las publicaciones en el canal Free.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "⚙️ Configurar Reacciones Free" en el menú de configuración
2. El bot muestra las reacciones actuales y solicita ingresar nuevos emojis
3. El administrador envía los emojis separados por espacios
4. El bot valida y guarda las nuevas reacciones
5. El bot actualiza la configuración y notifica el cambio

**Requisitos:**
- Mínimo 1 emoji
- Máximo 10 emojis
- Solo emojis válidos

**Ejemplo de interacción:**
```
⚙️ Configurar Reacciones Free

Reacciones actuales: ✅ ✔️ ☑️

Envía los emojis que quieres usar como reacciones, separados por espacios.
Ejemplo: ✅ ✔️ ☑️

Reglas:
• Mínimo: 1 emoji
• Máximo: 10 emojis
• Solo emojis válidos

Las reacciones se aplicarán automáticamente a nuevas publicaciones en el canal Free.

(Administrador envía: ✅ ✔️ 📝)
✅ Reacciones Free Configuradas
Reacciones: ✅ ✔️ 📝
Total: 3 emojis
Estas reacciones se aplicarán automáticamente a nuevas publicaciones en el canal Free.
```

## Broadcasting

### `Enviar a Canal VIP` - Envío de publicaciones al canal VIP

**Descripción:** Inicia el flujo de envío de contenido al canal VIP con funcionalidad de vista previa y confirmación.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "📤 Enviar a Canal VIP" en el menú de gestión VIP
2. El bot solicita enviar el contenido (texto, foto o video)
3. El administrador envía el contenido deseado
4. El bot muestra una vista previa del contenido
5. El administrador confirma o cancela el envío
6. Si confirma, el bot envía el contenido al canal VIP

**Tipos de contenido soportados:**
- Texto
- Foto (con caption opcional)
- Video (con caption opcional)

**Características:**
- Vista previa antes de enviar
- Confirmación de envío
- Cancelación en cualquier momento

**Ejemplo de interacción:**
```
📤 Enviar Publicación a Canal VIP

Envía el contenido que quieres publicar:

• Texto: Envía un mensaje de texto
• Foto: Envía una foto (con caption opcional)
• Video: Envía un video (con caption opcional)

El mensaje será enviado exactamente como lo envíes.

👁️ Verás un preview antes de confirmar el envío.

(Administrador envía una foto con caption)
👁️ Preview de Publicación

Destino: Canal VIP
Tipo: Foto

Caption:
Contenido exclusivo para VIPs

⚠️ Verifica que el contenido sea correcto antes de confirmar.

✅ Confirmar y Enviar | ❌ Cancelar | 🔄 Enviar Otro Contenido

(Administrador selecciona "✅ Confirmar y Enviar")
📤 Resultado del Envío

✅ Canal VIP

La publicación ha sido procesada.
```

### `Enviar a Canal Free` - Envío de publicaciones al canal Free

**Descripción:** Inicia el flujo de envío de contenido al canal Free con funcionalidad de vista previa y confirmación.

**Permisos:** Solo administradores

**Flujo de uso:**
1. El administrador selecciona "📤 Enviar a Canal Free" en el menú de gestión Free
2. El bot solicita enviar el contenido (texto, foto o video)
3. El administrador envía el contenido deseado
4. El bot muestra una vista previa del contenido
5. El administrador confirma o cancela el envío
6. Si confirma, el bot envía el contenido al canal Free

**Tipos de contenido soportados:**
- Texto
- Foto (con caption opcional)
- Video (con caption opcional)

**Características:**
- Vista previa antes de enviar
- Confirmación de envío
- Cancelación en cualquier momento

**Ejemplo de interacción:**
```
📤 Enviar Publicación a Canal Free

Envía el contenido que quieres publicar:

• Texto: Envía un mensaje de texto
• Foto: Envía una foto (con caption opcional)
• Video: Envía un video (con caption opcional)

El mensaje será enviado exactamente como lo envíes.

👁️ Verás un preview antes de confirmar el envío.

(Administrador envía un texto)
👁️ Preview de Publicación

Destino: Canal Free
Tipo: Texto

Texto:
¡Novedades en el canal Free!

⚠️ Verifica que el contenido sea correcto antes de confirmar.

✅ Confirmar y Enviar | ❌ Cancelar | 🔄 Enviar Otro Contenido

(Administrador selecciona "✅ Confirmar y Enviar")
📤 Resultado del Envío

✅ Canal Free

La publicación ha sido procesada.
```

## Comandos de Usuario

### `/start` - Bienvenida y menú principal de usuario

**Descripción:** Punto de entrada para usuarios que detecta el rol (admin/VIP/usuario) y proporciona las opciones correspondientes.

**Permisos:** Todos los usuarios

**Flujo de uso:**
1. El usuario envía `/start`
2. El bot detecta el rol del usuario (admin, VIP o normal)
3. Si es admin: redirige al panel de administración
4. Si es VIP: muestra mensaje de bienvenida con días restantes de suscripción
5. Si es usuario normal: muestra menú con opciones VIP/Free

**Opciones disponibles para usuarios normales:**
- Canjear Token VIP: Iniciar flujo de canje de tokens VIP
- Solicitar Acceso Free: Iniciar flujo de solicitud de acceso Free

**Ejemplo:**
```
/start
👋 Hola Usuario!

Bienvenido al bot de acceso a canales.

Opciones disponibles:

🎟️ Canjear Token VIP
Si tienes un token de invitación, canjéalo para acceso VIP.

📺 Solicitar Acceso Free
Solicita acceso al canal gratuito (con tiempo de espera).

👉 Selecciona una opción:
```

### `/vip` - Canje de token VIP (Futuro)

**Descripción:** Solicitar acceso VIP ingresando un token. (Funcionalidad movida al flujo de `/start`)

**Permisos:** Usuarios normales

**Flujo de uso:**
1. El usuario envía `/vip`
2. El bot solicita ingresar el token VIP
3. El bot valida y procesa el token
4. El bot envía link de invitación al canal VIP

### `/free` - Solicitud de acceso Free (Futuro)

**Descripción:** Solicitar acceso al canal Free. (Funcionalidad movida al flujo de `/start`)

**Permisos:** Usuarios normales

**Flujo de uso:**
1. El usuario envía `/free`
2. El bot registra la solicitud en la cola
3. El bot notifica el tiempo de espera
4. El bot envía link de invitación cuando se cumple el tiempo
```

## Flujos de Usuario

### Flujo VIP - Canje de Tokens

**Descripción:** Proceso para que usuarios canjeen tokens VIP y reciban acceso al canal VIP.

**Flujo de uso:**
1. Usuario selecciona "Canjear Token VIP" en el menú de `/start`
2. Bot verifica que canal VIP esté configurado
3. Bot entra en estado FSM `waiting_for_token`
4. Usuario envía token de invitación
5. Bot valida token (formato, vigencia, no usado)
6. Bot genera invite link único para el usuario
7. Bot envía link de acceso al canal VIP

**Características del invite link:**
- Válido por 1 hora
- Solo puede usarse 1 vez
- No se comparte con otros usuarios

**Ejemplo de interacción:**
```
👉 Copia y pega tu token aquí...
(Usuario envía: ABCD1234EFGH5678)
✅ Token Canjeado Exitosamente!

🎉 Tu acceso VIP está activo
⏱️ Duración: 30 días

👇 Usa este link para unirte al canal VIP:
https://t.me/+abc123def456

⚠️ Importante:
• El link expira en 1 hora
• Solo puedes usarlo 1 vez
• No lo compartas con otros

Disfruta del contenido exclusivo! 🚀
```

### Flujo Free - Solicitud de Acceso

**Descripción:** Proceso para que usuarios soliciten acceso al canal Free con tiempo de espera.

**Flujo de uso:**
1. Usuario selecciona "Solicitar Acceso Free" en el menú de `/start`
2. Bot verifica que canal Free esté configurado
3. Bot verifica si usuario ya tiene solicitud pendiente
4. Si no tiene solicitud: crea nueva solicitud y notifica tiempo de espera
5. Si ya tiene solicitud: muestra tiempo restante
6. Proceso automático procesa solicitudes cuando cumplen tiempo de espera
7. Bot envía notificación con invite link al usuario

**Características del tiempo de espera:**
- Configurable por administrador (mínimo 1 minuto)
- Procesamiento automático en background
- Notificación al usuario cuando esté listo

**Ejemplo de interacción:**
```
✅ Solicitud Recibida

Tu solicitud de acceso al canal Free ha sido registrada.

⏱️ Tiempo de espera: 10 minutos

📨 Recibirás un mensaje con el link de invitación cuando el tiempo se cumpla.

💡 No necesitas hacer nada más, el proceso es automático.

Puedes cerrar este chat, te notificaré cuando esté listo! 🔔
```

## Ejemplos de Flujos Completos

### Flujo de Configuración VIP Completo

1. Administrador envía `/admin`
2. Selecciona "Gestión Canal VIP"
3. Selecciona "⚙️ Configurar Canal VIP"
4. Reenvía mensaje del canal VIP
5. Bot configura el canal
6. Selecciona "🎟️ Generar Token de Invitación"
7. Bot genera y envía token VIP

### Flujo de Configuración Free Completo

1. Administrador envía `/admin`
2. Selecciona "Gestión Canal Free"
3. Selecciona "⚙️ Configurar Canal Free"
4. Reenvía mensaje del canal Free
5. Bot configura el canal
6. Selecciona "⏱️ Configurar Tiempo de Espera"
7. Ingresa nuevo tiempo (por ejemplo: 20)
8. Bot actualiza tiempo de espera

## Errores Comunes y Soluciones

### Error de permisos en configuración de canal
- **Problema:** El bot no puede configurar un canal
- **Causa:** El bot no es administrador o no tiene permisos suficientes
- **Solución:** Asegurarse de que el bot sea administrador con permiso para invitar usuarios

### Error de formato en tiempo de espera
- **Problema:** El bot no acepta el tiempo de espera ingresado
- **Causa:** No es un número o es menor a 1
- **Solución:** Ingresar un número entero mayor o igual a 1

### Error de token inválido
- **Problema:** El token no se puede canjear
- **Causas posibles:**
  - El token ya fue usado
  - El token ha expirado
  - El token no existe
  - El canal VIP no está configurado

## Tareas Programadas (Background Tasks)

El bot ejecuta automáticamente tareas programadas que realizan operaciones periódicas para mantener el sistema funcionando correctamente:

### Tarea: Expulsión de VIPs expirados
- **Frecuencia:** Cada 60 minutos (configurable con `CLEANUP_INTERVAL_MINUTES`)
- **Funcionalidad:** Marca como expirados y expulsa del canal a los suscriptores VIP cuya fecha pasó
- **Proceso:**
  1. Busca suscriptores VIP con fecha de expiración anterior a la actual
  2. Marca como expirados en la base de datos
  3. Expulsa del canal VIP usando la API de Telegram
  4. Registra en logs el número de usuarios expulsados

### Tarea: Procesamiento de cola Free
- **Frecuencia:** Cada 5 minutos (configurable con `PROCESS_FREE_QUEUE_MINUTES`)
- **Funcionalidad:** Busca solicitudes que cumplieron el tiempo de espera y envía invite links a los usuarios
- **Proceso:**
  1. Busca solicitudes Free que cumplen el tiempo de espera configurado
  2. Para cada solicitud:
     - Marca como procesada
     - Crea un invite link único (válido 24 horas, un solo uso)
     - Envía el link al usuario por mensaje privado
  3. Registra en logs el número de solicitudes procesadas

### Tarea: Limpieza de datos antiguos
- **Frecuencia:** Diariamente a las 3 AM UTC
- **Funcionalidad:** Elimina solicitudes Free procesadas hace más de 30 días
- **Proceso:**
  1. Busca solicitudes Free procesadas hace más de 30 días
  2. Elimina los registros antiguos de la base de datos
  3. Registra en logs el número de registros eliminados

**Configuración de intervalos:**
- `CLEANUP_INTERVAL_MINUTES`: Intervalo para expulsión de VIPs expirados (default: 60)
- `PROCESS_FREE_QUEUE_MINUTES`: Intervalo para procesamiento de cola Free (default: 5)

Estas tareas se ejecutan automáticamente sin intervención del usuario y ayudan a mantener el sistema limpio y funcional.