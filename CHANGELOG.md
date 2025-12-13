# Changelog

Todos los cambios notables en este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- T6: Service Container - Contenedor de servicios con patrón Dependency Injection + Lazy Loading para reducir consumo de memoria en Termux
- T7: Subscription Service - Gestión completa de suscripciones VIP (tokens, validación, canjes) y cola de acceso Free
- T8: Channel Service - Gestión completa de canales VIP y Free con verificación de permisos y envío de publicaciones
- T9: Config Service - Gestión de configuración global del bot, tiempos de espera, reacciones y tarifas
- T10: Middlewares - Implementación de AdminAuthMiddleware y DatabaseMiddleware para autenticación de administradores e inyección automática de sesiones de base de datos
- T11: FSM States - Implementación de estados FSM para administradores y usuarios para flujos de configuración y canje de tokens
- T12: Admin Handler - Handler del comando /admin que muestra el menú principal de administración con navegación, verificación de estado de configuración y teclado inline
- T13: Handlers VIP y Free - Submenú VIP (gestión del canal VIP con generación de tokens de invitación), Configuración del canal VIP (configuración del canal VIP por reenvío de mensajes), Generación de tokens de invitación (creación de tokens VIP con duración configurable), Submenú Free (gestión del canal Free con configuración de tiempo de espera), Configuración del canal Free (configuración del canal Free por reenvío de mensajes), Configuración de tiempo de espera (configuración de tiempo de espera para acceso Free)
- T15: Background Tasks - Tareas programadas que expulsan VIPs expirados del canal, procesan la cola Free para enviar invite links a usuarios que completaron tiempo de espera, limpian datos antiguos y usan APScheduler con configuración de intervalos mediante variables de entorno
- T24: Pagination System - Sistema de paginación reutilizable con clase Paginator genérica, teclado de navegación paginado y formateadores de contenido para listas largas de elementos
- T25: Paginated VIP Subscriber Management - Gestión paginada de suscriptores VIP con listado, filtrado por estado (activos, expirados, próximos a expirar, todos), vistas detalladas y expulsión manual de suscriptores
- T26: Free Queue Visualization - Visualización paginada de cola de solicitudes Free con filtrado por estado (pendientes, listas para procesar, procesadas, todas) y monitoreo del tiempo de espera configurado

## [1.0.0] - 2025-12-11

### Added
- T6: Implementación del Service Container con 4 servicios disponibles: subscription, channel, config, stats
- T6: Patrón DI + Lazy Loading para optimizar uso de memoria en Termux
- T6: Método get_loaded_services() para monitoreo de uso de memoria
- T7: SubscriptionService con 14 métodos asíncronos para gestión de suscripciones
- T7: Flujos completos: generar token → validar → canjear → extender
- T7: Sistema de cola Free con wait_time configurable
- T7: Invite links de un solo uso (member_limit=1)
- T7: Gestión de tokens VIP: generación, validación, canje y extensión
- T7: Gestión de suscriptores VIP: creación, extención y expiración automática
- T7: Gestión de solicitudes Free: creación y procesamiento automático
- T7: Limpieza automática de datos antiguos
- T8: ChannelService con métodos para gestión de canales VIP y Free
- T8: Configuración de canales con verificación de existencia y permisos
- T8: Verificación de permisos del bot (can_invite_users, can_post_messages)
- T8: Envío de contenido multimedia a canales (texto, fotos, videos)
- T8: Reenvío y copia de mensajes a canales
- T8: Validación de configuración de canales
- T9: ConfigService con métodos para gestión de configuración global
- T9: Obtención y actualización de configuración de BotConfig (singleton)
- T9: Gestión de tiempos de espera para acceso al canal Free
- T9: Gestión de reacciones personalizadas para canales VIP y Free
- T9: Configuración y gestión de tarifas de suscripción
- T9: Validación de configuración completa y resumen de estado
- T9: Métodos para resetear configuración a valores por defecto
- T11: ChannelSetupStates - Estados para configurar canales VIP y Free con extracción de ID de canal desde reenvío de mensajes
- T11: WaitTimeSetupStates - Estados para configurar tiempo de espera del canal Free con validación de entrada numérica
- T11: BroadcastStates - Estados para envío de publicaciones a canales con soporte para diferentes tipos de contenido
- T11: TokenRedemptionStates - Estados para canje de tokens VIP con validación de formato y vigencia
- T11: FreeAccessStates - Estados para solicitud de acceso Free con manejo de solicitudes pendientes
- T11: Implementación de ejemplos de uso de estados FSM en handlers de administración y usuarios
- T11: Documentación completa de estados FSM con ejemplos de implementación y flujos de usuario
- T12: Admin Handler - Handler del comando /admin que muestra el menú principal de administración con navegación, verificación de estado de configuración y teclado inline
- T12: Implementación de navegación del menú principal con estado de configuración
- T12: Aplicación de middlewares AdminAuthMiddleware y DatabaseMiddleware al router de admin
- T12: Verificación de estado de configuración del bot en el menú principal
- T12: Callback handlers para navegación entre menús
- T12: Teclado inline con opciones de administración
- T12: Documentación completa del handler admin con ejemplos de uso
- T13: Handlers VIP y Free - Submenú VIP (gestión del canal VIP con generación de tokens de invitación), Configuración del canal VIP (configuración del canal VIP por reenvío de mensajes), Generación de tokens de invitación (creación de tokens VIP con duración configurable), Submenú Free (gestión del canal Free con configuración de tiempo de espera), Configuración del canal Free (configuración del canal Free por reenvío de mensajes), Configuración de tiempo de espera (configuración de tiempo de espera para acceso Free)
- T13: Implementación de submenú VIP con opciones de generación de tokens y reconfiguración de canal
- T13: Implementación de submenú Free con opciones de configuración de tiempo de espera y reconfiguración de canal
- T13: Implementación de flujo de configuración de canales por reenvío de mensajes con validación de permisos
- T13: Implementación de generación de tokens VIP con duración configurable
- T13: Implementación de configuración de tiempo de espera para acceso Free con validación de entrada numérica
- T13: Implementación de teclados inline específicos para los menús VIP y Free
- T13: Documentación completa de los handlers VIP y Free con ejemplos de uso
- T14: Handlers User (/start, flujos) - Handler /start con detección de rol (admin/VIP/usuario), Flujo VIP (canje de tokens VIP con validación y generación de invite links), Flujo Free (solicitud de acceso Free con tiempo de espera y notificaciones automáticas), Middleware de base de datos (inyección de sesiones sin autenticación de admin), FSM para validación de tokens (estados para manejo de entrada de tokens), Validación de configuración (verificación de canales configurados antes de procesar)
- T14: Implementación del handler /start con detección de rol de usuario (admin, VIP, normal)
- T14: Implementación del flujo VIP para canje de tokens con validación y generación de invite links únicos
- T14: Implementación del flujo Free para solicitud de acceso con tiempo de espera configurable
- T14: Aplicación de DatabaseMiddleware a handlers de usuario sin autenticación de admin
- T14: Uso de TokenRedemptionStates para manejo de entrada de tokens VIP
- T14: Validación de configuración de canales antes de procesar solicitudes de usuarios
- T14: Documentación completa de los handlers User con ejemplos de uso

### Changed
- Refactorización completa de la arquitectura de servicios para usar el contenedor
- Optimización de consumo de memoria mediante lazy loading de servicios
- Mejora en la estructura de gestión de suscripciones VIP y Free
- Actualización de documentación para incluir los nuevos handlers User

### Fixed
- Problemas de consumo de memoria en entornos con recursos limitados como Termux
- Implementación robusta de tokens únicos y de un solo uso
- Sistema de expiración automática de suscripciones VIP

---