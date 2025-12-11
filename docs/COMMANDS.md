# Documentación de Comandos

Referencia completa de comandos disponibles en el bot, funcionalidades y ejemplos de uso.

## Estado Actual de Comandos

En ONDA 1 Fase 1.1 (MVP Básico), la mayoría de comandos están **pendientes de implementar** en fases posteriores.

| Fase | Estado | Comandos |
|------|--------|----------|
| 1.1 (Actual) | Completada | - |
| 1.2 (Próxima) | Pendiente | Admin: /admin, /generar_token, /config |
| 1.3 (Próxima) | Pendiente | User: /start, /vip, /free |
| 1.4+ | Pendiente | Avanzados |

## Comandos Planeados (ONDA 1+)

### Comandos de Usuario

#### /start
Comando de bienvenida y menú principal del bot.

```
Descripción:
  Envía mensaje de bienvenida y muestra opciones disponibles para usuarios

Sintaxis:
  /start

Permisos:
  Ninguno (cualquier usuario)

Respuesta:
  [Menú inline con botones:]
  - Acceso VIP (Canjear Token)
  - Acceso Free (Cola de Espera)
  - Ayuda

Ejemplo:
  Usuario: /start
  Bot: ¡Hola! Bienvenido al bot...
```

Implementación planeada en Fase 1.3:
```python
@router.message.command("start")
async def start_handler(message: Message) -> None:
    """Manejador del comando /start"""
    # Enviar mensaje de bienvenida
    # Mostrar teclado inline con opciones
    # No requiere DB para MVP
```

#### /vip
Acceso al canal VIP mediante token de invitación.

```
Descripción:
  Inicia flujo de canje de token VIP
  Usuario ingresa token y obtiene acceso

Sintaxis:
  /vip

Permisos:
  Ninguno (cualquier usuario)

Estados FSM:
  waiting_for_vip_token → Esperando que usuario ingrese token

Flujo:
  1. Usuario envía /vip
  2. Bot responde: "Ingresa tu token VIP:"
  3. Usuario envía token (ej: ABC123XYZ456789)
  4. Bot valida:
     - Token existe
     - No fue usado antes
     - No expiró
  5. Si válido:
     - Crear VIPSubscriber en BD
     - Marcar token como usado
     - Invitar a canal VIP
     - "Bienvenido! Acceso VIP válido por 24h"
  6. Si inválido:
     - "Token inválido o expirado"

Ejemplo:
  Usuario: /vip
  Bot: Ingresa tu token VIP:
  Usuario: ABC123XYZ456789
  Bot: ✅ Bienvenido al canal VIP!
       Tu acceso es válido hasta 2025-12-12 11:30
       Días restantes: 1
```

Implementación planeada en Fase 1.3:
```python
@router.message.command("vip")
async def vip_handler(message: Message, state: FSMContext) -> None:
    """Inicia flujo de canje de token VIP"""
    await message.answer("Ingresa tu token VIP:")
    await state.set_state(UserStates.waiting_for_vip_token)

@router.message(UserStates.waiting_for_vip_token)
async def vip_token_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Procesa token VIP ingresado"""
    token_str = message.text.strip()
    # Validar token
    # Crear suscriptor
    # Invitar a canal
    await state.clear()
```

#### /free
Solicitar acceso al canal Free con tiempo de espera.

```
Descripción:
  Solicita acceso al canal Free
  El bot invita después de esperar DEFAULT_WAIT_TIME_MINUTES

Sintaxis:
  /free

Permisos:
  Ninguno (cualquier usuario)

Flujo:
  1. Usuario envía /free
  2. Bot:
     - Verifica si ya tiene solicitud pendiente
     - Si NO: Crea FreeChannelRequest
     - Si SÍ: "Ya tienes una solicitud pendiente"
  3. Bot responde: "Tu solicitud fue registrada"
                   "Espera 5 minutos..."
  4. [Background Task ejecuta cada 5 min]
     - Busca FreeChannelRequest listas (cumplieron espera)
     - Invita usuarios a canal Free
     - Marca como processed
  5. Usuario recibe invitación al canal

Ejemplo:
  Usuario: /free
  Bot: ✅ Solicitud registrada
       Serás invitado en 5 minutos
       [Después de 5 min...]
       ¡Bienvenido al canal Free!
       Tu acceso es permanente mientras el bot esté activo
```

Implementación planeada en Fase 1.3:
```python
@router.message.command("free")
async def free_handler(message: Message, session: AsyncSession) -> None:
    """Solicita acceso al canal Free"""
    # Verificar solicitud pendiente
    # Crear FreeChannelRequest
    # Background task procesa cada 5 min
```

### Comandos de Administrador

#### /admin
Menú principal de administración (requiere permisos admin).

```
Descripción:
  Acceso al panel de administración
  Solo disponible para admins configurados en ADMIN_USER_IDS

Sintaxis:
  /admin

Permisos:
  Admin (verificado por AdminAuthMiddleware)

Respuesta:
  [Menú inline con botones:]
  - Gestionar VIP
    - Generar Token
    - Ver Tokens
    - Ver Suscriptores
    - Renovar Suscripción
  - Gestionar Free
    - Ver Cola de Espera
    - Procesar Manual
  - Configuración
    - Canales
    - Tiempo Espera
    - Reacciones

Ejemplo:
  Admin: /admin
  Bot: Panel de Administración
       [Botones para gestión]
```

Implementación planeada en Fase 1.2:
```python
@router.message.command("admin")
async def admin_handler(message: Message) -> None:
    """Panel principal de admin"""
    # Verificar permisos (AdminAuthMiddleware)
    # Enviar teclado con opciones de admin
```

#### /generar_token
Generar nuevo token VIP (admin).

```
Descripción:
  Genera token único para invitar usuarios a VIP
  Incluye selección de duración

Sintaxis:
  /generar_token

Permisos:
  Admin

Estados FSM:
  admin_generating_token → Seleccionando duración

Flujo:
  1. Admin: /generar_token
  2. Bot: "Selecciona duración del token:"
          [Botones:]
          - 24 horas
          - 7 días
          - 30 días
          - Duración personalizada
  3. Admin selecciona opción
  4. Si "Personalizada": Bot pide horas
  5. Bot:
     - Genera token único de 16 caracteres
     - Guarda en BD: InvitationToken
     - Responde: "Token generado:
                  ABC123XYZ456789
                  Válido por: 24 horas
                  Generado por: @admin_username
                  Crea un enlace de invitación"

Ejemplo:
  Admin: /generar_token
  Bot: Selecciona duración:
       [24h] [7d] [30d] [Custom]
  Admin: Presiona [24h]
  Bot: ✅ Token generado: ABC123XYZ456789
       Válido por 24 horas
       Comparte este token para invitar usuarios VIP
```

Implementación planeada en Fase 1.2:
```python
@router.message.command("generar_token")
async def generar_token_handler(message: Message, state: FSMContext) -> None:
    """Inicia flujo de generación de token"""
    # Mostrar opciones de duración
    # Usar callbackquery para selección
    # Generar token con secrets
    # Guardar en BD
```

#### /ver_tokens
Ver lista de tokens generados (admin).

```
Descripción:
  Lista todos los tokens con su estado
  Puedes filtrar por: válidos, usados, expirados

Sintaxis:
  /ver_tokens [filtro]

Filtros:
  todos    - Todos los tokens (default)
  validos  - Tokens sin usar y no expirados
  usados   - Tokens ya canjeados
  expirados - Tokens expirados

Respuesta:
  Tabla con:
  - Token (primeros 8 caracteres)
  - Estado (válido/usado/expirado)
  - Generado por
  - Creado hace X tiempo
  - Canjeado por (si aplica)

Ejemplo:
  Admin: /ver_tokens validos
  Bot: 📋 Tokens válidos (3):

       1. ABC123XY... [VÁLIDO]
          Creado hace 2 horas
          Expira en 22 horas

       2. DEF456UV... [VÁLIDO]
          Creado hace 5 horas
          Expira en 19 horas

       3. GHI789ST... [VÁLIDO]
          Creado hace 1 día
          Expira en 10 horas
```

Implementación planeada en Fase 1.2:
```python
@router.message.command("ver_tokens")
async def ver_tokens_handler(message: Message, command: CommandObject, session: AsyncSession) -> None:
    """Muestra lista de tokens"""
    filtro = command.args or "todos"
    # Consultar tokens según filtro
    # Formatear tabla
    # Enviar respuesta
```

#### /suscriptores
Ver suscriptores VIP (admin).

```
Descripción:
  Lista usuarios con suscripción VIP activa
  Incluye información de expiración

Sintaxis:
  /suscriptores [filtro]

Filtros:
  activos   - Suscripción aún válida (default)
  proximos  - Expiran en próximos 7 días
  expirados - Suscripción ya expirada
  todos     - Todos los suscriptores

Respuesta:
  Tabla con:
  - User ID
  - Días restantes
  - Fecha expiración
  - Token usado
  - Acciones (renovar, eliminar)

Ejemplo:
  Admin: /suscriptores proximos
  Bot: 📊 Suscriptores próximos a expirar (2):

       1. User 987654321
          Expira en 2 días (2025-12-13 11:30)
          Token: ABC123XY...
          [Renovar] [Eliminar]

       2. User 555555555
          Expira en 5 días (2025-12-16 11:30)
          Token: DEF456UV...
          [Renovar] [Eliminar]
```

Implementación planeada en Fase 1.2:
```python
@router.message.command("suscriptores")
async def suscriptores_handler(message: Message, command: CommandObject, session: AsyncSession) -> None:
    """Muestra suscriptores VIP"""
    filtro = command.args or "activos"
    # Consultar suscriptores
    # Formatear tabla
    # Enviar con botones de acción
```

#### /config
Configuración del bot (admin).

```
Descripción:
  Accede a panel de configuración
  Permite cambiar canales, tiempos, reacciones

Sintaxis:
  /config

Permisos:
  Admin

Menú:
  - Canales
    - Ver Canal VIP
    - Configurar Canal VIP
    - Ver Canal Free
    - Configurar Canal Free
  - Tiempos
    - Ver Tiempo de Espera Free
    - Cambiar Tiempo de Espera
  - Reacciones
    - Ver Reacciones VIP
    - Configurar Reacciones VIP
    - Ver Reacciones Free
    - Configurar Reacciones Free
  - Tarifas
    - Ver Tarifas
    - Cambiar Tarifas

Ejemplo:
  Admin: /config
  Bot: ⚙️ Configuración del Bot

       [Canales]
       [Tiempos]
       [Reacciones]
       [Tarifas]
```

Implementación planeada en Fase 1.4:
```python
@router.message.command("config")
async def config_handler(message: Message, state: FSMContext) -> None:
    """Panel de configuración"""
    # Mostrar menú de opciones
    # Usar callbackquery para navegar
    # Actualizar BotConfig en BD
```

#### /stats
Estadísticas del bot (admin).

```
Descripción:
  Muestra estadísticas generales
  Usuarios VIP, Free, tokens, etc.

Sintaxis:
  /stats

Permisos:
  Admin

Respuesta:
  📊 Estadísticas del Bot:

  👥 Usuarios VIP: 42 (3 próximos a expirar)
  📋 Tokens generados: 50
     - Válidos: 8
     - Usados: 40
     - Expirados: 2

  📺 Canal Free:
     - Solicitudes en cola: 15
     - Procesadas hoy: 23

  💾 Base de datos: 125 KB
  ⏱️ Tiempo de espera Free: 5 minutos
  🔧 Versión: ONDA 1 (MVP)
```

Implementación planeada en Fase 1.5:
```python
@router.message.command("stats")
async def stats_handler(message: Message, session: AsyncSession) -> None:
    """Muestra estadísticas"""
    # Contar usuarios VIP
    # Contar tokens
    # Contar requests Free
    # Formatear respuesta
```

### Comandos Especiales

#### /help
Ayuda general del bot.

```
Descripción:
  Muestra información de ayuda
  Diferentes para usuarios y admins

Sintaxis:
  /help

Respuesta (Usuario normal):
  ℹ️ Ayuda del Bot VIP/Free

  /start - Menú principal
  /vip - Acceso al canal VIP (necesitas token)
  /free - Solicitar acceso Free
  /help - Esta ayuda

  Problemas? Contacta con @admin_username

Respuesta (Admin):
  ℹ️ Ayuda de Administración

  /admin - Panel de administración
  /generar_token - Crear nuevo token VIP
  /ver_tokens - Ver tokens
  /suscriptores - Ver suscriptores
  /config - Configuración del bot
  /stats - Estadísticas
  /help - Esta ayuda

  Para usuarios:
  /start - Menú principal
```

Implementación planeada en Fase 1.3:
```python
@router.message.command("help")
async def help_handler(message: Message) -> None:
    """Muestra ayuda según el tipo de usuario"""
    if Config.is_admin(message.from_user.id):
        # Mostrar ayuda admin
    else:
        # Mostrar ayuda usuario
```

## Manejo de Errores en Comandos

### Errores Comunes

**Usuario no autorizado:**
```
Admin: /admin
Bot: ❌ No tienes permisos para usar este comando
     Por favor contacta con el administrador
```

**Configuración incompleta:**
```
Admin: /config
Bot: ⚠️ Error: Canal VIP no configurado
     Configura los canales primero: /config
```

**Token inválido:**
```
Usuario: /vip
Bot: Ingresa tu token VIP:
Usuario: INVALID123
Bot: ❌ Token inválido
     Verifica que esté bien escrito
     Token debe tener 16 caracteres
```

**Solicitud duplicada:**
```
Usuario: /free
Bot: ⚠️ Ya tienes una solicitud pendiente
     Serás invitado en X minutos
     Espera a que se complete
```

## Validaciones de Comandos

### Token VIP
- Longitud: exactamente 16 caracteres
- Caracteres válidos: a-z, A-Z, 0-9
- Formato: case-sensitive
- No debe estar usado previamente
- No debe haber expirado

### User ID
- Debe ser número válido
- Rango: enteros positivos de 32-64 bits
- Identificador único por usuario

### Canal ID
- Formato: -100XXXXXXXXXXX (negativo de 13-15 dígitos)
- Alternativa: @nombre_canal

### Tiempo de Espera
- Mínimo: 1 minuto
- Máximo: 10080 minutos (7 días)
- Valor por defecto: 5 minutos

## Flujos de Comandos (FSM)

### Flujo de Usuario Normal

```
[Inicio]
   │
   ▼
/start ─────┬──→ /vip ──→ [waiting_for_vip_token] ──→ [VIP]
   │        │
   │        └──→ /free ──→ [waiting_confirmation] ──→ [Free Queue]
   │
   └──→ /help ──→ [Información]
```

### Flujo de Administrador

```
[Inicio]
   │
   ▼
/admin ─────┬──→ /generar_token ──→ [selecting_duration] ──→ [Token Creado]
   │        │
   │        ├──→ /ver_tokens ──→ [List Tokens]
   │        │
   │        ├──→ /suscriptores ──→ [List Subscribers]
   │        │
   │        └──→ /config ──────┬─→ [configure_vip_channel]
   │                           │
   │                           ├─→ [configure_free_channel]
   │                           │
   │                           └─→ [configure_wait_time]
   │
   └──→ /stats ──→ [Estadísticas]

   └──→ /help ──→ [Admin Help]
```

## Mensajes de Estado

El bot utiliza emojis para indicar estado:

- ✅ Operación exitosa
- ❌ Error o validación fallida
- ⚠️ Advertencia
- ℹ️ Información
- 📋 Lista o tabla
- 📊 Estadísticas
- ⏱️ Tiempo
- 📺 Canal
- 👥 Usuarios
- 💾 Base de datos
- 🔧 Configuración

## Futuras Mejoras

En ONDA 2+:

- [ ] Comandos de paginación (/prev, /next)
- [ ] Autocomplete en argumentos
- [ ] Comandos de búsqueda (/buscar_usuario)
- [ ] Comandos de reporte (/reporte)
- [ ] Comandos de backup (/backup)
- [ ] Comandos de moderación (/ban, /unban)

---

**Última actualización:** 2025-12-11
**Versión:** 1.0.0
**Estado:** Documentación de comandos planeados (implementación en fases posteriores)
