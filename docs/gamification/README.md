# Módulo de Gamificación

Sistema completo de gamificación para bots de Telegram.

## Índice
- [Features](#features)
- [Quick Start](#quick-start)
- [Arquitectura](#arquitectura)
- [Componentes Principales](#componentes-principales)
- [Guías](#guías)

## Features

- ✅ Sistema de besitos (moneda virtual)
- ✅ Niveles y progresión automática
- ✅ Misiones (diarias, semanales, rachas)
- ✅ Recompensas con unlock conditions
- ✅ Badges coleccionables
- ✅ Leaderboards
- ✅ Wizards de configuración
- ✅ Plantillas predefinidas
- ✅ Background jobs automáticos

## Quick Start

1. Aplicar migración
2. Aplicar plantilla inicial
3. Configurar reacciones
4. ¡Listo!

### Estructura de Directorios
```
docs/gamification/
├── README.md              # Este archivo - Overview general
├── ARCHITECTURE.md        # Diseño técnico detallado
├── SETUP.md              # Guía de instalación y configuración
├── API.md                # Referencia de servicios
└── ADMIN_GUIDE.md        # Guía para administradores
```

## Arquitectura

El módulo de gamificación está construido sobre una arquitectura de capas que sigue principios de diseño limpio y separación de responsabilidades:

```
Usuario reacciona → ReactionHook → ReactionService → BesitoService → LevelService → MissionService
```

### Capas del Sistema
1. **Database Layer**: 13 modelos SQLAlchemy
2. **Services Layer**: 7 servicios + Container DI
3. **Orchestrators Layer**: 3 orchestrators para workflows complejos
4. **Handlers Layer**: Admin + User handlers
5. **Background Jobs**: Auto-progression + Streak expiration

## Componentes Principales

### Servicios
- `ReactionService`: Gestiona las reacciones de usuarios
- `BesitoService`: Maneja la economía de besitos
- `LevelService`: Controla los niveles y progresión
- `MissionService`: Administra las misiones y objetivos
- `BadgeService`: Maneja las insignias y reconocimientos
- `RewardService`: Gestiona las recompensas
- `StatsService`: Estadísticas y métricas

### Modelos de Base de Datos
- Usuarios y perfiles
- Besitos y transacciones
- Niveles y experiencia
- Misiones y progreso
- Recompensas y desbloqueos
- Inscripciones de canales

## Guías

- [Configuración del Sistema](SETUP.md) - Pasos para instalar y configurar el módulo
- [Referencia de API](API.md) - Documentación de servicios y métodos disponibles
- [Guía de Administración](ADMIN_GUIDE.md) - Cómo gestionar y administrar el sistema
- [Arquitectura Detallada](ARCHITECTURE.md) - Información técnica profunda sobre cómo funciona el sistema

## FAQ

### ¿Cómo se calculan los besitos?
Los besitos se otorgan automáticamente cuando un usuario recibe reacciones positivas en sus mensajes. El sistema anti-spam evita duplicados en el mismo mensaje y aplica límites diarios.

### ¿Qué pasa cuando un usuario sube de nivel?
Al subir de nivel, el usuario puede recibir recompensas especiales configuradas por el administrador y se visualizan cambios en su perfil y badges.

### ¿Cómo se configuran nuevas misiones?
Las misiones se pueden crear usando el wizard de administración o aplicando plantillas predefinidas desde el panel de administración.

### ¿Qué son las plantillas?
Las plantillas son conjuntos preconfigurados de misiones, recompensas y configuraciones que facilitan la implementación inicial del sistema.