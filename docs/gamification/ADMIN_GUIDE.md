# Guía de Administración - Módulo de Gamificación

## 🎯 Visión General

Esta guía está dirigida a administradores del bot que desean configurar, gestionar y monitorear el sistema de gamificación. Incluye instrucciones paso a paso para tareas administrativas comunes.

## 🏁 Inicio Rápido para Administradores

### 1. Acceder al Menú de Administración

Para acceder al sistema de gamificación, los administradores deben usar el comando:

```
/gamification
```

Esto abrirá el menú principal con las siguientes opciones:
- Misiones: Crear, editar, listar misiones
- Recompensas: Gestionar recompensas y badges
- Niveles: Configurar sistema de niveles
- Reacciones: Definir emojis que otorgan puntos
- Plantillas: Aplicar configuraciones predefinidas
- Estadísticas: Ver métricas del sistema
- Usuarios: Ver y gestionar perfil de usuarios

### 2. Configuración Inicial Recomendada

Para empezar rápidamente, se recomienda:

1. **Aplicar la plantilla "Starter Pack"** - Crea un sistema básico con 3 niveles, misión de bienvenida y badge inicial
2. **Configurar reacciones básicas** - Definir emojis que otorgan besitos
3. **Crear misiones iniciales** - Establecer objetivos para nuevos usuarios

## 📝 Gestión de Misiones

### Crear Misión con Wizard (Recomendado)

1. Ir a "Misiones"
2. Seleccionar "Wizard de Nueva Misión"
3. Seguir los pasos:

#### Paso 1: Tipo de Misión
- **One Time**: Misión que se completa una vez (ej: "Reacciona por primera vez")
- **Daily**: Misión diaria (ej: "Reacciona a 5 mensajes hoy")
- **Weekly**: Misión semanal (ej: "Reacciona a 25 mensajes esta semana")
- **Streak**: Misión de racha (ej: "Reacciona 7 días consecutivos")

#### Paso 2: Criterios de Completitud
- Define cómo se completa la misión según su tipo
- Ejemplo para misión diaria: Reaccionar a 5 mensajes en un día
- Ejemplo para misión de streak: Mantener racha por 7 días consecutivos

#### Paso 3: Recompensa
- Define cuántos besitos se otorgan al completar la misión
- Opcionalmente, crear o seleccionar una recompensa especial

#### Paso 4: Nivel Auto-Creación (Opcional)
- ¿Crear nuevo nivel al completar esta misión?
- Útil para misiones de progresión

#### Paso 5: Recompensas Unlock (Opcional)
- ¿Esta misión desbloquea recompensas adicionales?
- Puedes crear una recompensa nueva desde cero o **seleccionar una recompensa ya existente** de una lista paginada.
- Es posible añadir múltiples recompensas (tanto nuevas como existentes) a la misión.

#### Paso 6: Confirmación
- Revisa la configuración completa
- Confirma para crear la misión

### Crear Misión Manualmente

Alternativamente, puedes crear misiones directamente:

1. Ir a "Misiones" → "Crear Misión Manual"
2. Ingresar nombre, descripción y tipo
3. Configurar criterios JSON
4. Definir recompensa en besitos
5. Guardar

### Editar/Desactivar Misiones

- Ir a "Misiones" → "Listar Misiones"
- Seleccionar la misión a editar
- Opciones disponibles: Editar, Desactivar, Eliminar (soft-delete)

## 🎁 Gestión de Recompensas

### Crear Recompensa con Wizard

1. Ir a "Recompensas"
2. Seleccionar "Wizard de Nueva Recompensa"
3. Seguir los pasos:

#### Paso 1: Tipo de Recompensa
- **Badge**: Distintivo coleccionable (icono + rareza)
- **Item**: Recurso virtual (usado en el sistema)
- **Permission**: Acceso especial (ej: canales premium)
- **Besitos**: Recompensa monetaria directa

#### Paso 2: Metadata
- Propiedades específicas según el tipo
- Para badges: icono, rareza (common, rare, epic, legendary)
- Para items: tipo de item, atributos especiales

#### Paso 3: Condiciones de Desbloqueo (Opcional)
- ¿Qué se requiere para obtener esta recompensa?
- **Por nivel**: Alcanzar cierto nivel
- **Por misión**: Completar cierta misión
- **Por besitos**: Tener cierta cantidad de besitos
- **Múltiple**: Combinación de condiciones (AND)

#### Paso 4: Confirmación
- Revisa la configuración completa
- Confirma para crear la recompensa

### Compra de Recompensas

Los usuarios pueden comprar recompensas con sus besitos si:
- La recompensa está configurada como comprable
- El usuario tiene suficientes besitos
- No hay condiciones de desbloqueo pendientes

## ⬆️ Gestión de Niveles

### Crear Nivel con Wizard

1. Ir a "Niveles" → "Crear Nivel".
2. Seguir los pasos del wizard:

#### Paso 1: Nombre del Nivel
- Define el nombre que identificará al nivel.
- Ejemplo: "Novato", "Entusiasta", "Leyenda".

#### Paso 2: Besitos Mínimos
- Cantidad de besitos que un usuario debe acumular para alcanzar este nivel.
- Ejemplo: 1000.

#### Paso 3: Orden de Progresión
- Número que define la secuencia de los niveles (1, 2, 3...).
- El orden debe ser único y positivo.

#### Paso 4: Beneficios (Opcional)
- Opcionalmente, puedes añadir un objeto JSON con beneficios.
- Ejemplo: `{"reaction_multiplier": 1.2}`
- Puedes saltar este paso si no hay beneficios.

#### Paso 5: Confirmación
- Revisa el resumen del nivel a crear.
- Confirma para guardar el nuevo nivel en el sistema.

### Niveles Automáticos

El sistema puede crear niveles automáticamente como parte de:
- Wizard de misión (opción "Auto-Creación")
- Aplicación de plantillas
- Configuración de sistema completo

### Progresión Automática

Los usuarios suben de nivel automáticamente cuando:
- Sus besitos totales alcanzan el mínimo requerido
- Se completan misiones que otorgan besitos suficientes
- El background job de auto-progresión detecta cambios (cada 6 horas)

## 🔄 Gestión de Reacciones

### Configurar Emojis que Otorgan Puntos

1. Ir a "Reacciones" → "Configurar Reacciones"
2. Para cada emoji, definir:
   - Emoji (ej: ❤️, 🔥, 👍)
   - Nombre descriptivo
   - Valor en besitos
   - Estado (activo/inactivo)

### Valores Recomendados

- Reacciones comunes (❤️, 👍): 1 besito
- Reacciones especiales (🔥, 💎): 2-3 besitos
- Reacciones raras: 5+ besitos (usar con moderación)

### Límites de Reacciones

El sistema incluye límites para prevenir abuso:
- Reacciones diarias máximas por usuario
- Besitos máximos por día por usuario
- Control anti-spam (mismo mensaje)

## 🧰 Plantillas Predefinidas

### Tipos de Plantillas

#### **Starter Pack**
- 3 niveles iniciales (0, 50, 100 besitos)
- Misión de bienvenida (una vez)
- Badge de bienvenida
- Configuración básica de sistema

#### **Engagement System**
- Misión diaria (5 reacciones/día)
- Misión de racha (7 días)
- Badges de engagement
- Sistema de progresión motivacional

#### **Progression System**
- 6 niveles progresivos
- Badges por cada nivel
- Misiones de progresión
- Sistema completo de recompensas

### Aplicar Plantilla

1. Ir a "Misiones" → "Plantillas"
2. Seleccionar plantilla deseada
3. Confirmar aplicación
4. El sistema creará todo atómicamente

## 📊 Estadísticas del Sistema

### Acceder a Estadísticas

Ir a "Estadísticas" para ver:

- **Resumen General**: Usuarios totales, besitos otorgados, misiones completadas
- **Distribución por Nivel**: Cuántos usuarios en cada nivel
- **Estadísticas de Misiones**: Completitud, éxito promedio
- **Estadísticas de Engagement**: Reacciones, rachas promedio, besitos por usuario

### Interpreting Metrics

- **Usuarios por nivel**: Indica progresión del sistema
- **Misiones activas vs completadas**: Salud del sistema de misiones
- **Reacciones promedio**: Nivel de engagement
- **Rachas promedio**: Consistencia de participación

## 👤 Gestión de Usuarios

### Ver Perfil de Usuario

1. Ir a "Usuarios" → "Buscar Usuario"
2. Ingresar ID o usar búsqueda
3. Ver perfil completo con:
   - Nivel actual y progreso
   - Besitos totales y semanales
   - Misiones activas y completadas
   - Recompensas obtenidas
   - Rachas actuales y récords

### Administración Especial

- Otorgar besitos manualmente
- Forzar level-up
- Desbloquear recompensas
- Reiniciar rachas si necesario

## ⚙️ Configuración del Sistema

### Parámetros Configurables

Los siguientes parámetros pueden ajustarse según necesidades:

- **Intervalo de auto-progresión**: Cada cuántas horas verificar level-ups
- **Horas para reset de rachas**: Cuándo expiran las rachas de inactividad
- **Límites diarios**: Máximo de reacciones o besitos por día
- **Estado de notificaciones**: Qué tipos de notificaciones enviar

### Variables de Entorno

Algunos ajustes requieren modificación en `.env`:

```
AUTO_PROGRESSION_INTERVAL_HOURS=6
STREAK_RESET_HOURS=24
MAX_DAILY_REACTIONS=50
MAX_DAILY_BESITOS_PER_USER=1000
NOTIFICATIONS_ENABLED=true
```

## 🛠️ Solución de Problemas Comunes

### Usuarios no reciben besitos

- Verificar que las reacciones estén activas
- Confirmar que el emoji es exactamente igual
- Verificar límites diarios no alcanzados

### Misiones no se completan automáticamente

- Validar que los criterios sean correctos
- Revisar si hay errores en el background job
- Confirmar que el usuario esté en estado válido

### Niveles no se actualizan

- El sistema actualiza automáticamente con actividad
- Para forzar actualización: usar comando administrativo
- Verificar que los besitos estén correctamente contados

## 🔒 Roles y Permisos

### Acceso al Sistema

- **Gamification Admins**: Acceso completo al sistema
- **Super Admins**: Acceso a todas las funciones
- **Moderadores**: Solo lectura de estadísticas

### Funciones Requeridas

Para usar las funciones administrativas:
- El usuario debe estar en la lista de ADMINS
- El bot debe tener permisos para enviar mensajes
- Debe haber conexión a la base de datos

## 📞 Soporte Administrativo

### Recursos Adicionales

- Documentación API completa
- Changelog con versiones
- Foro de administradores
- Soporte técnico prioritario

### Reportar Problemas

Si encuentras problemas técnicos:

1. Verificar logs del sistema
2. Documentar paso a paso la reproducción
3. Reportar al equipo de desarrollo con:
   - Comportamiento esperado
   - Comportamiento real
   - Pasos para reproducir
   - Capturas de pantalla si aplica

---

**Nota:** El sistema de gamificación está diseñado para ser usado principalmente a través de los wizards conversacionales. Las opciones manuales están disponibles para configuraciones avanzadas o personalizadas.