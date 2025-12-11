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
- T7: Gestión de suscriptores VIP: creación, extensión y expiración automática
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

### Changed
- Refactorización completa de la arquitectura de servicios para usar el contenedor
- Optimización de consumo de memoria mediante lazy loading de servicios
- Mejora en la estructura de gestión de suscripciones VIP y Free

### Fixed
- Problemas de consumo de memoria en entornos con recursos limitados como Termux
- Implementación robusta de tokens únicos y de un solo uso
- Sistema de expiración automática de suscripciones VIP

---