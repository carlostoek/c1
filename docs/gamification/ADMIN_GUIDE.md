# Guía de Administración - Módulo de Gamificación

## Índice
- [Introducción](#introducción)
- [Panel de Administración](#panel-de-administración)
- [Creación de Misiones con Wizard](#creación-de-misiones-con-wizard)
- [Administración de Recompensas](#administración-de-recompensas)
- [Aplicación de Plantillas](#aplicación-de-plantillas)
- [Configuración del Sistema](#configuración-del-sistema)
- [Monitoreo y Estadísticas](#monitoreo-y-estadísticas)
- [Gestión de Usuarios](#gestión-de-usuarios)
- [Notificaciones y Anuncios](#notificaciones-y-anuncios)
- [Backup y Restauración](#backup-y-restauración)

## Introducción

Esta guía está destinada a administradores del bot que desean gestionar y configurar el módulo de gamificación. Cubre las tareas administrativas comunes y proporciona instrucciones paso a paso para gestionar eficientemente el sistema de gamificación.

## Panel de Administración

Accede al panel de administración de gamificación mediante el comando:

```
/gamification
```

Desde aquí puedes acceder a todas las funciones de administración:

- **Misiones**: Crear, editar y gestionar misiones
- **Recompensas**: Configurar recompensas y condiciones de desbloqueo
- **Plantillas**: Aplicar y gestionar plantillas predefinidas
- **Estadísticas**: Ver métricas del sistema y rankings
- **Usuarios**: Gestionar perfiles de usuarios
- **Configuración**: Ajustar parámetros del sistema

## Creación de Misiones con Wizard

El wizard de creación de misiones guía a los administradores a través del proceso de creación de nuevas misiones paso a paso.

### Paso 1: Acceder al Wizard
```
/gamification → Misiones → Wizard
```

### Paso 2: Seleccionar Tipo de Misión

El wizard te presentará opciones para diferentes tipos de misiones:

- **Misión Simple**: Una tarea específica con un objetivo claro
- **Misión Diaria**: Se reinicia diariamente, se completa una vez al día
- **Misión Semanal**: Se reinicia semanalmente, se completa una vez por semana
- **Misión de Racha**: Implica actividades continuas durante varios días
- **Misión de Nivel**: Requiere alcanzar cierto nivel o experiencia
- **Misión Social**: Implica interacciones sociales (reacciones, mensajes, etc.)

### Paso 3: Definir Criterios

Dependiendo del tipo de misión, ingresarás:

- **Título y Descripción**: Nombre atractivo y descripción clara
- **Objetivo**: Cantidad o condición a cumplir (ej: "Enviar 5 mensajes", "Recibir 10 ❤️")
- **Frecuencia**: Cada cuánto se puede repetir (única vez, diaria, semanal)
- **Expiración**: Duración máxima de la misión
- **Requisitos Previos**: Niveles o misiones necesarias para desbloquear

### Paso 4: Configurar Recompensa

Selecciona las recompensas que obtendrá el usuario al completar la misión:

- **Besitos**: Cantidad específica de besitos como recompensa
- **XP**: Puntos de experiencia adicionales
- **Niveles**: Avance instantáneo de nivel (si aplica)
- **Ítems Virtuales**: Badges, insignias o elementos especiales
- **Recompensas Personalizadas**: Elementos definidos por el sistema

### Paso 5: Opciones Avanzadas

Opcionalmente, puedes configurar:

- **Auto Level Up**: Al completar esta misión, ¿desbloquea nuevas misiones automáticamente?
- **Recompensas de Unlock**: ¿Desbloquea funcionalidades especiales al completarse?
- **Condiciones Especiales**: Requisitos extra o condiciones particulares
- **Notificaciones**: ¿Enviar notificación al completar?

### Paso 6: Revisar y Confirmar

Revisa todos los detalles de la misión antes de crearla y confirma la creación.

**Consejo profesional:** Mantén las misiones variadas y atractivas para mantener el engagement de los usuarios.

## Administración de Recompensas

### Crear Nueva Recompensa

```
/gamification → Recompensas → Nueva Recompensa
```

Tipos de recompensas disponibles:

#### Recompensas de Moneda
- **Besitos**: Cantidad fija de besitos
- **Bonuses Temporales**: Multiplicador de besitos por tiempo limitado
- **Cuentas Premium**: Beneficios temporales o permanentes

#### Recompensas de Progresión
- **Puntos de XP**: XP adicional para subir de nivel
- **Saltos de Nivel**: Avance de nivel instantáneo
- **Atajos de Misiones**: Acceso anticipado a misiones superiores

#### Recompensas Exclusivas
- **Badges Especiales**: Insignias únicas o limitadas
- **Accesos Premium**: Funcionalidades exclusivas
- **Contenido Bloqueado**: Desbloqueo de contenido especial

### Condiciones de Desbloqueo

Configura qué condiciones deben cumplirse para desbloquear recompensas:

```
/gamification → Recompensas → Condiciones de Desbloqueo
```

Tipos de condiciones:
- **Por Nivel**: "Disponible desde el nivel 5"
- **Por Besitos**: "Requiere 1000 besitos acumulados"
- **Por Colecciones**: "Requiere 10 badges diferentes"
- **Por Tiempo**: "Disponible después de 30 días de activad"
- **Por Logros**: "Después de completar 100 misiones"

## Aplicación de Plantillas

Las plantillas son paquetes preconfigurados que facilitan la implementación inicial del sistema.

### Plantillas Disponibles

#### Starter Pack
- **Objetivo**: Configuración inicial del sistema
- **Contiene**: 5 niveles básicos, 10 misiones iniciales, recompensas básicas
- **Uso recomendado**: Para primera implementación del sistema

```
/gamification → Misiones → Plantillas → Starter Pack → Aplicar
```

#### Engagement Pack
- **Objetivo**: Aumentar participación diaria
- **Contiene**: Misiones diarias/semanales, objetivos de interacción, recompensas frecuentes
- **Uso recomendado**: Para mantener engagement constante

#### Progression Pack
- **Objetivo**: Sistema completo de progresión
- **Contiene**: 6 niveles detallados, misiones progresivas, recompensas estructuradas
- **Uso recomendado**: Para sistemas maduros con buen engagement

#### Challenge Pack
- **Objetivo**: Misiones desafiantes y recompensas exclusivas
- **Contiene**: Misiones complejas, recompensas exclusivas, badges raros
- **Uso recomendado**: Para mantener interés de usuarios avanzados

### Aplicar Plantilla

1. Ve al panel de administración:
```
/gamification
```

2. Selecciona Misiones:
```
Misiones → Plantillas
```

3. Elige la plantilla deseada
4. Haz clic en "Previsualizar" para revisar contenido
5. Confirma con "Aplicar" para implementar en el sistema

**Importante:** La aplicación de plantillas no elimina contenido existente, solo agrega nuevas configuraciones.

## Configuración del Sistema

### Parámetros Generales

Accede a la configuración global desde:
```
/gamification → Configuración
```

#### Configuración de Reacciones
- **Emojis Válidos**: Emojis que otorgan besitos (por defecto: ❤️, 👍, 🎉, 🔥)
- **Valor de Besitos**: Cuántos besitos da cada emoji
- **Límites Diarios**: Máximo de veces que un emoji afecta a un usuario
- **Anti-Spam**: Reglas para evitar abusos

#### Configuración de Progresión
- **XP por Besito**: Cuánto XP equivale un besito
- **Curva de Niveles**: Cómo se distribuyen los requisitos por nivel
- **Intervalos de Auto-Progression**: Cada cuánto se aplica progresión automática
- **Notificaciones de Nivel**: Mensajes al subir de nivel

#### Configuración de Misiones
- **Misiones Diarias**: Cantidad de misiones que se generan diariamente
- **Frecuencia de Reset**: Cuándo se reinician las misiones
- **Tipos Prioritarios**: Qué tipos de misiones se sugieren primero
- **Dificultad Inicial**: Configuración de dificultad para nuevos usuarios

### Backup de Configuración

Guarda la configuración actual:
```
/gamification → Configuración → Exportar Configuración
```

Esto genera un archivo JSON con toda la configuración actual del sistema.

## Monitoreo y Estadísticas

### Dashboard de Administración

```
/gamification → Estadísticas → Dashboard
```

Visualiza métricas importantes:
- Usuarios activos (diario/semanal/mensual)
- Misiones completadas
- Besitos distribuidos
- Niveles promedio
- Engagement por canal
- Tasa de conversión de misiones

### Rankings

```
/gamification → Estadísticas → Rankings
```

Tipos de rankings disponibles:
- **Top Besitos**: Usuarios con más besitos
- **Top XP**: Usuarios con más experiencia
- **Top Niveles**: Usuarios en niveles más altos
- **Top Misiones**: Usuarios que completan más misiones
- **Top Reaccionados**: Usuarios que más besitos reciben

### Estadísticas por Canal

```
/gamification → Estadísticas → Por Canal
```

Analiza engagement por canal:
- Participación promedio
- Reacciones por mensaje
- Misiones completadas por canal
- Usuarios activos por canal

## Gestión de Usuarios

### Perfil de Usuario

```
/gamification → Usuarios → Buscar Usuario
```

Consulta o modifica perfiles individuales:

#### Información Disponible
- Nivel actual y XP
- Total de besitos
- Misiones completadas
- Badges obtenidos
- Estadísticas de actividad
- Historial de reacciones

#### Acciones Administrativas
- **Resetear Progreso**: Reiniciar estadísticas (con confirmación)
- **Ajustar Besitos**: Incrementar/decrementar besitos manualmente
- **Forzar Subida de Nivel**: Avanzar manualmente de nivel
- **Otorgar Recompensas**: Dar recompensas específicas
- **Bloquear/Desbloquear**: Impedir participación en gamificación

### Operaciones Masivas

```
/gamification → Usuarios → Operaciones Masivas
```

Herramientas para modificar múltiples usuarios:
- Ajustar besitos en lotes
- Otorgar recompensas masivas
- Resetear progreso seleccionado
- Exportar datos de usuarios

## Notificaciones y Anuncios

### Configuración de Notificaciones

```
/gamification → Configuración → Notificaciones
```

Tipos de notificaciones configurables:
- **Level Up**: Al subir de nivel
- **Misión Completada**: Al completar misiones
- **Recompensas Obtenidas**: Al recibir recompensas
- **Nuevas Misiones**: Al generar misiones diarias
- **Record de Usuario**: Logros notables

### Anuncios Personalizados

```
/gamification → Anuncios
```

Crea anuncios para difundir eventos o logros:

- **Anuncio de Top Usuarios**: Destacar ganadores semanales
- **Evento Especial**: Anunciar misiones temporales
- **Novedades del Sistema**: Informar mejoras
- **Concursos**: Promocionar competencias temporales

## Backup y Restauración

### Backup Completo

```
/gamification → Herramientas → Backup Completo
```

Crea copia de seguridad de:
- Configuración del sistema
- Definiciones de misiones
- Recompensas y condiciones
- Datos de usuarios y progresos

### Restauración

```
/gamification → Herramientas → Restaurar Backup
```

Importa backup previamente generado. La restauración incluye:
- Confirmación de sobrescritura
- Validación de formato
- Aplicación segura de datos

## FAQ para Administradores

### ¿Cómo cambio el valor de los besitos por reacción?
Ve a `/gamification → Configuración` y ajusta los valores en la sección "Configuración de Reacciones".

### ¿Qué hago si un usuario cree que le falta un besito?
Consulta el perfil del usuario en `/gamification → Usuarios → Buscar Usuario` y revisa su historial de transacciones.

### ¿Cómo creo una misión que requiera cierto nivel para aparecer?
En el wizard de misiones, en "Condiciones Avanzadas", establece el requisito de nivel mínimo.

### ¿Se pueden crear misiones temporales?
Sí, en las opciones avanzadas de misión puedes establecer fechas de inicio y fin específicas.

### ¿Cómo puedo ver quién está dominando las clasificaciones?
Usa `/gamification → Estadísticas → Rankings` para ver los tops en diferentes categorías.

### ¿Qué pasa si aplico una plantilla dos veces?
Las plantillas no duplican contenido existente, pero podrían crear inconsistencias si modificaste configuraciones después de la primera aplicación. Siempre haz backup antes de aplicar plantillas.

### ¿Puedo personalizar los niveles?
Sí, mediante la edición directa de definiciones de niveles o la aplicación de plantillas personalizadas.