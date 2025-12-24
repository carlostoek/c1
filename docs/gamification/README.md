# Módulo de Gamificación

Sistema completo de gamificación para bots de Telegram que incentiva la participación activa de los usuarios a través de un sistema de puntos, niveles, misiones y recompensas.

## 🎯 Features

- ✅ **Sistema de besitos** - Moneda virtual para recompensar participación
- ✅ **Niveles y progresión automática** - Sistema de niveles basado en acumulación de puntos
- ✅ **Misiones** - Diversos tipos: diarias, semanales, rachas, una sola vez
- ✅ **Recompensas con unlock conditions** - Desbloqueo condicional de recompensas
- ✅ **Badges coleccionables** - Distintivos raros basados en logros
- ✅ **Leaderboards** - Rankings de usuarios más activos
- ✅ **Wizards de configuración** - Flujos conversacionales para admins
- ✅ **Plantillas predefinidas** - Configuraciones completas listas para usar
- ✅ **Background jobs automáticos** - Procesamiento asíncrono de tareas
- ✅ **Notificaciones inteligentes** - Alertas personalizadas para eventos importantes

## 🏗️ Arquitectura

El módulo sigue un patrón de 4 capas:

1. **Capa de Base de Datos** - 13 modelos SQLAlchemy con relaciones complejas
2. **Capa de Servicios** - 7 servicios especializados con inyección de dependencias
3. **Capa de Orquestación** - 3 orchestrators para workflows transaccionales
4. **Capa de Handlers** - Interfaces conversacionales administrativas y de usuario
5. **Background Jobs** - Procesos asíncronos para tareas periódicas

## 🚀 Quick Start

1. **Aplicar migraciones** - Configurar la base de datos
2. **Configurar reacciones** - Definir emojis que otorgan besitos
3. **Aplicar plantilla inicial** - Usar wizard para crear sistema base
4. **¡Listo para usar!** - El sistema comienza a funcionar automáticamente

## 📚 Documentación Completa

- [Guía de Arquitectura](ARCHITECTURE.md) - Diseño técnico detallado
- [Guía de Instalación](SETUP.md) - Pasos para configurar el módulo
- [Referencia de API](API.md) - Documentación de servicios
- [Guía de Administración](ADMIN_GUIDE.md) - Manual para administradores
- [Changelog](CHANGELOG.md) - Historial de cambios y versiones

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, lee nuestro [CONTRIBUTING.md](../../CONTRIBUTING.md) para más detalles.

---

**Versión:** 1.0  
**Estado:** Estable  
**Última actualización:** Diciembre 2024