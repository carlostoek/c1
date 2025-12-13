# Documentación del Dashboard Completo (T27)

## Descripción General

El dashboard completo es un panel de control del sistema que proporciona una visión general del estado del bot con health checks, configuración, estadísticas clave, tareas en segundo plano y acciones rápidas.

## Componentes

- `bot/handlers/admin/dashboard.py` - Handlers principales y callbacks de navegación para el panel de control completo

## Características

- **Estado de configuración:** Visualización del estado de los canales VIP y Free, reacciones configuradas y tiempo de espera
- **Estadísticas clave:** Métricas importantes como VIPs activos, solicitudes Free pendientes, tokens disponibles y nuevos VIPs
- **Health checks:** Verificación del estado del sistema con identificación de problemas y advertencias
- **Background tasks:** Estado del scheduler y próxima ejecución de tareas programadas
- **Acciones rápidas:** Acceso directo a funciones administrativas desde el dashboard
- **Actualización automática:** Muestra la hora exacta de la última actualización
- **Diseño estructurado:** Información organizada en secciones claras con bordes y emojis

## Funcionalidades

### Dashboard Principal

El dashboard principal se accede desde el menú de administración y proporciona:

1. **Estado general del sistema** - Indicador visual del estado operativo del bot
2. **Problemas y advertencias** - Lista de problemas detectados y advertencias
3. **Configuración actual** - Estado de los canales VIP y Free, reacciones y tiempo de espera
4. **Estadísticas clave** - Métricas importantes como VIPs activos, solicitudes Free pendientes, tokens disponibles
5. **Tareas en segundo plano** - Estado del scheduler y próxima ejecución de tareas

### Health Checks

El sistema realiza automáticamente verificaciones de salud que incluyen:

- **Canales configurados:** Verifica que al menos uno de los canales (VIP o Free) esté configurado
- **Background tasks:** Verifica que el scheduler esté corriendo
- **Tokens disponibles:** Alerta si hay menos de 3 tokens disponibles
- **VIPs próximos a expirar:** Alerta si hay más de 10 VIPs expirando en los próximos 7 días
- **Cola Free:** Alerta si hay más de 50 solicitudes Free pendientes

### Acciones Rápidas

El dashboard incluye botones de acceso directo a funciones administrativas comunes:

- "📊 Estadísticas Detalladas" - Acceso al panel de estadísticas completo
- "⚙️ Configuración" - Acceso al panel de configuración
- "👥 Suscriptores VIP" - Visualización de suscriptores VIP (si canal VIP está configurado)
- "📋 Cola Free" - Visualización de cola Free (si canal Free está configurado)
- "🔄 Actualizar" - Recarga manual del dashboard
- "🔙 Menú" - Vuelve al menú principal de administración

## Flujo de Uso

1. El administrador selecciona "📊 Dashboard Completo" en el menú principal de administración
2. El bot recopila todos los datos necesarios para el dashboard
3. El bot realiza health checks del sistema
4. El bot muestra el dashboard completo con estado general, problemas detectados, configuración actual, estadísticas clave y estado de tareas en segundo plano
5. El administrador puede navegar a otras secciones desde el teclado inline

## Estructura del Mensaje

El dashboard se presenta en formato HTML con secciones estructuradas:

```
📊 <b>Dashboard del Sistema</b>

🟢 <b>Estado:</b> Operativo

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>⚙️ CONFIGURACIÓN</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Canal VIP: ✅ (5 reacciones)
┃ Canal Free: ✅ (10 min espera)
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>📈 ESTADÍSTICAS CLAVE</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ VIP Activos: <b>25</b>
┃ Free Pendientes: <b>8</b>
┃ Tokens Disponibles: <b>12</b>
┃
┃ Nuevos VIP (hoy): 2
┃ Nuevos VIP (semana): 15
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ <b>🔄 BACKGROUND TASKS</b>
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ Estado: 🟢 Corriendo
┃ Jobs: 3
┃ Próximo job: 4 min
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━

<i>Actualizado: 2025-12-13 10:30:00 UTC</i>
```

## Estados de Health Check

- **Operativo (🟢):** No se detectaron problemas ni advertencias
- **Funcionando con Advertencias (🟡):** Se detectaron advertencias pero no problemas críticos
- **Problemas Detectados (🔴):** Se detectaron problemas críticos que requieren atención

## Implementación Técnica

### Callback Principal

```python
@admin_router.callback_query(F.data == "admin:dashboard")
async def callback_admin_dashboard(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra dashboard completo del sistema.

    Incluye:
    - Estado de configuración (canales, reacciones)
    - Estadísticas clave (VIP, Free, Tokens)
    - Background tasks (estado, próxima ejecución)
    - Health checks
    - Acciones rápidas

    Args:
        callback: Callback query
        session: Sesión de BD
    """
```

### Recolección de Datos

La función `_gather_dashboard_data()` recopila toda la información necesaria:

- Estado de configuración (VIP/Free channels, reacciones, tiempo de espera)
- Estadísticas generales del sistema
- Estado del scheduler y tareas en segundo plano
- Realiza health checks del sistema

### Formateo del Mensaje

La función `_format_dashboard_message()` estructura la información en secciones claras con formato HTML y emojis para mejor visualización.

### Teclado Inline

La función `_create_dashboard_keyboard()` crea un teclado adaptativo que se ajusta según la configuración actual del sistema.

## Manejo de Errores

- Cada handler está envuelto en try-catch para manejar errores de generación del dashboard
- Mensajes de error claros para el usuario administrador
- Logging detallado de errores para debugging
- Opción de reintentar o volver al menú principal en caso de error

## Características Adicionales

- **Actualización automática:** Muestra la hora exacta de la última actualización
- **Diseño estructurado:** Información organizada en secciones claras con bordes y emojis
- **Adaptabilidad:** El teclado inline se adapta según la configuración actual
- **Acceso directo:** Botones para acceder rápidamente a funciones administrativas importantes
- **Health checks:** Identificación automática de problemas y advertencias en el sistema
- **Visualización clara:** Uso de emojis y formato HTML para mejor comprensión del estado del sistema

---

**Última actualización:** 2025-12-13
**Versión:** 1.0.0
**Estado:** Documentación completa del dashboard del bot VIP/Free