# Documentación del Bot VIP/Free - ONDA 1 (MVP)

Guía completa de arquitectura, configuración, uso y desarrollo del bot de administración de canales VIP/Free para Telegram.

## Índice de Documentación

### Inicio Rápido
- **[SETUP.md](./SETUP.md)** - Instalación, configuración y ejecución del bot
- **[README.md](../README.md)** - Descripción general del proyecto (en raíz)

### Arquitectura y Diseño
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Descripción técnica de la arquitectura, estructura de directorios y flujo de datos
- **[DESIGN.md](./DESIGN.md)** - Decisiones de diseño, patrones utilizados y justificaciones

### Funcionalidades Implementadas
- **[COMMANDS.md](./COMMANDS.md)** - Lista completa de comandos disponibles y su uso
- **[HANDLERS.md](./HANDLERS.md)** - Documentación de todos los handlers (admin y user)
- **[STATES.md](./STATES.md)** - Documentación de máquinas de estado (FSM)

### Datos y Servicios
- **[DATABASE.md](./DATABASE.md)** - Documentación de modelos de base de datos y relaciones
- **[SERVICES.md](./SERVICES.md)** - Documentación de servicios y lógica de negocio
- **[API.md](./API.md)** - API interna, métodos principales y dependencias

### Módulo Narrativo
- **[narrativa/README.md](./narrativa/README.md)** - Documentación general del módulo narrativo
- **[narrativa/API.md](./narrativa/API.md)** - Referencia de API del módulo narrativo
- **[narrativa/SETUP.md](./narrativa/SETUP.md)** - Guía de instalación del módulo narrativo
- **[narrativa/HANDLERS.md](./narrativa/HANDLERS.md)** - Documentación de handlers narrativos
- **[narrativa/DATABASE.md](./narrativa/DATABASE.md)** - Documentación de modelos narrativos

### Módulo de Tienda y Mochila
- **[shop/README.md](./shop/README.md)** - Documentación general del módulo de tienda y mochila
- **[shop/API.md](./shop/API.md)** - Referencia de API del módulo de tienda y mochila
- **[shop/SETUP.md](./shop/SETUP.md)** - Guía de instalación del módulo de tienda y mochila
- **[shop/HANDLERS.md](./shop/HANDLERS.md)** - Documentación de handlers de tienda e inventario
- **[shop/DATABASE.md](./shop/DATABASE.md)** - Documentación de modelos de tienda y mochila
- **[shop/tracking.md](./shop/tracking.md)** - Tracking del desarrollo del módulo de tienda

### Operación y Mantenimiento
- **[TESTING.md](./TESTING.md)** - Guía de testing y configuración
- **[MAINTENANCE.md](./MAINTENANCE.md)** - Procedimientos de mantenimiento y troubleshooting
- **[CHANGELOG.md](./CHANGELOG.md)** - Historial de cambios y versiones

## Resumen Ejecutivo

**Proyecto:** Bot de Administración de Canales VIP/Free para Telegram
**Versión:** ONDA 1 (MVP) - Fase 1.1
**Plataforma:** Termux (Android) / Linux
**Stack:** Python 3.11+ | Aiogram 3.4.1 | SQLAlchemy 2.0.25 | SQLite 3.x

### Características Principales

1. **Canales VIP** - Acceso por invitación con tokens únicos
2. **Canales Free** - Acceso con tiempo de espera configurable
3. **Gestión de Suscripciones** - Expiración automática y renovación
4. **Panel de Administración** - Interfaz para gestionar canales y tokens
5. **Base de Datos Asincrónica** - SQLAlchemy 2.0 con aiosqlite

## Estructura de Directorios

```
/data/data/com.termux/files/home/repos/c1/
├── docs/                           # Esta documentación
├── bot/
│   ├── database/                   # Modelos SQLAlchemy y engine
│   ├── services/                   # Servicios (pendiente de implementar)
│   ├── handlers/                   # Handlers admin/ y user/
│   ├── middlewares/                # Middlewares (pendiente de implementar)
│   ├── states/                     # Estados FSM (pendiente de implementar)
│   ├── utils/                      # Utilidades (pendiente de implementar)
│   └── background/                 # Tareas programadas (pendiente de implementar)
├── main.py                         # Entry point del bot
├── config.py                       # Configuración centralizada
├── requirements.txt                # Dependencias pip
├── .env                           # Variables de entorno (NO commitear)
└── .env.example                    # Template para .env
```

## Requiere Lectura Previa

Antes de trabajar en este proyecto, familiarízate con:

1. **[SETUP.md](./SETUP.md)** - Instrucciones de instalación y ejecución
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Entender la arquitectura general
3. **[DATABASE.md](./DATABASE.md)** - Familiaridad con los modelos de datos

## Fases Planificadas

### ONDA 1: MVP Funcional (Actual)
- [ ] **Fase 1.1** (Completada): Setup y Fundamentos - Base datos, Config, Entry point
- [ ] **Fase 1.2** (Próxima): Handlers Admin - Crear/gestionar tokens, canales
- [ ] **Fase 1.3** (Próxima): Handlers User - Canjear tokens, solicitar acceso Free
- [ ] **Fase 1.4** (Próxima): Middlewares y FSM - Auth, DB injection, Estados
- [ ] **Fase 1.5** (Próxima): Background Tasks - Limpieza, procesamiento colas

### ONDA 2: Features Avanzadas
- [ ] Servicios reutilizables
- [ ] Sistema de pagos/suscripción
- [ ] Estadísticas y reportes
- [ ] Notificaciones avanzadas

### ONDA 3: Optimización
- [ ] Redis para cache
- [ ] Webhook updates (vs polling)
- [ ] Testing completo
- [ ] Documentación adicional

## Convenciones del Proyecto

Este proyecto sigue las convenciones definidas en [CLAUDE.md](../CLAUDE.md):

- **Naming:** PascalCase para clases, snake_case para funciones
- **Async:** TODO es async/await
- **Type Hints:** Obligatorio en todas las funciones
- **Docstrings:** Google Style
- **Imports:** Estándar → Third-party → Local

## Información de Contacto y Contribución

Para reportar bugs o contribuir:
1. Revisa [CONTRIBUTING.md](./CONTRIBUTING.md) (si existe)
2. Crea un issue en el repositorio
3. Sigue las convenciones del proyecto

## Licencia

MIT License - Ver archivo LICENSE (si existe)

---

**Última actualización:** 2025-12-11
**Versión documentación:** 1.0.0
