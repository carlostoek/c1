# FASE 1: LA VOZ DE LUCIEN - TRACKING DE AVANCE

**Objetivo:** Transformar todos los mensajes del bot de genéricos a la voz de Lucien.

---

## ESTADO DEL SISTEMA ANTES DE FASE 1

### Archivos Base Existentes (FASE 0)
- [x] `bot/utils/lucien_messages.py` - Biblioteca de mensajes con voz de Lucien
- [x] `bot/gamification/config/archetypes.py` - 6 arquetipos expandidos
- [x] `bot/gamification/config/economy.py` - Economía de besitos y niveles
- [x] `bot/shop/config/initial_inventory.py` - Items del Gabinete

### Handlers Existentes (por revisar)
- [x] `bot/handlers/user/start.py` - Comando /start (usa mensajes genéricos)
- [x] `bot/handlers/user/dynamic_menu.py` - Menú dinámico
- [x] `bot/gamification/handlers/user/profile.py` - Vista de perfil
- [x] `bot/shop/handlers/user/shop.py` - Tienda (se llama "Tienda", no "Gabinete")
- [x] `bot/gamification/handlers/user/missions.py` - Misiones (se llama "Misiones", no "Encargos")
- [ ] Handler de besitos (por crear o actualizar)

---

## TAREAS FASE 1

### F1.1 - Reescribir /start
**Estado:** Pendiente

- [ ] Importar LucienMessages
- [ ] Implementar flujo para usuario completamente nuevo
- [ ] Implementar flujo para usuario que regresa (< 7 días)
- [ ] Implementar flujo para usuario inactivo (7-14 días)
- [ ] Implementar flujo para usuario muy inactivo (14+ días)
- [ ] Implementar flujo para usuario VIP
- [ ] Implementar flujo para admin
- [ ] Actualizar menú principal con botones correctos
- [ ] Actualizar última actividad del usuario

---

### F1.2 - Reescribir menú dinámico
**Estado:** Pendiente

- [ ] Importar LucienMessages
- [ ] Actualizar callback "dynmenu:back"
- [ ] Reemplazar mensajes de error
- [ ] Actualizar respuestas a items de menú
- [ ] Agregar mensajes de transición en navegación

---

### F1.3 - Reescribir mensajes de perfil
**Estado:** Pendiente

- [ ] Importar LucienMessages y EconomyConfig
- [ ] Mostrar estructura de expediente
- [ ] Implementar barra de progreso visual
- [ ] Agregar comentarios de Lucien según nivel
- [ ] Verificar/arreglar mensajes faltantes en lucien_messages.py

---

### F1.4 - Reescribir tienda/Gabinete
**Estado:** Pendiente

- [ ] Renombrar "Tienda" → "El Gabinete" en UI
- [ ] Renombrar "Comprar" → "Adquirir" u "Obtener"
- [ ] Renombrar "Productos" → "Artículos" u "Objetos"
- [ ] Mensaje de bienvenida al Gabinete
- [ ] Categorías con descripciones de Lucien
- [ ] Vista de item con description_lucien
- [ ] Flujo de compra (confirmación, éxito, sin fondos)
- [ ] Actualizar botones

---

### F1.5 - Reescribir misiones/Encargos
**Estado:** Pendiente

- [ ] Renombrar "Misiones" → "Encargos"
- [ ] Renombrar "Completar" → "Cumplir"
- [ ] Renombrar "Recompensa" → "Reconocimiento"
- [ ] Mensaje de bienvenida a Encargos
- [ ] Estructura de lista agrupada por tipo
- [ ] Mensajes de progreso
- [ ] Mensaje de encargo completado
- [ ] Mensaje sin encargos disponibles
- [ ] Actualizar botones

---

### F1.6 - Comando /besitos
**Estado:** Pendiente

- [ ] Buscar handler existente o crear `bot/handlers/user/besitos.py`
- [ ] Vista de balance con comentarios contextuales
- [ ] Comentarios según cantidad (low, growing, good, high, hoarder)
- [ ] Notificación al ganar besitos
- [ ] Notificación al alcanzar hitos
- [ ] Historial reciente (opcional)
- [ ] Botones de navegación

---

### F1.7 - Centralizar mensajes de error
**Estado:** Pendiente

- [ ] Buscar mensajes genéricos de error en proyecto
- [ ] Reemplazar ERROR_GENERIC
- [ ] Reemplazar ERROR_NOT_FOUND
- [ ] Reemplazar ERROR_PERMISSION
- [ ] Reemplazar ERROR_RATE_LIMITED
- [ ] Reemplazar ERROR_INVALID_INPUT
- [ ] Reemplazar ERROR_TIMEOUT
- [ ] Reemplazar ERROR_MAINTENANCE
- [ ] Crear versiones SHORT para callbacks (< 200 chars)

---

### F1.8 - Centralizar confirmaciones
**Estado:** Pendiente

- [ ] Buscar mensajes genéricos de confirmación
- [ ] Reemplazar CONFIRM_ACTION
- [ ] Reemplazar CONFIRM_SAVED
- [ ] Reemplazar CONFIRM_PURCHASE
- [ ] Reemplazar CONFIRM_MISSION_COMPLETE
- [ ] Reemplazar CONFIRM_LEVEL_UP
- [ ] Reemplazar CONFIRM_REGISTRATION

---

## CRITERIOS DE ACEPTACIÓN

### Funcionalidad
- [ ] /start muestra mensajes de Lucien
- [ ] Flujos diferenciados funcionan
- [ ] Menú principal tiene botones correctos
- [ ] Perfil muestra información con voz de Lucien
- [ ] Gabinete tiene descripciones narrativas
- [ ] Encargos usan terminología correcta
- [ ] Balance de besitos tiene comentarios contextuales

### Consistencia de Voz
- [ ] Ningún mensaje usa "tú" (siempre "usted")
- [ ] Ningún mensaje tiene emojis excesivos en el texto
- [ ] Tono consistente: formal, elegante, evaluador
- [ ] No hay mensajes genéricos tipo "✅ Éxito!" o "❌ Error!"

### Técnico
- [ ] Todos los imports de LucienMessages funcionan
- [ ] No hay errores de formato
- [ ] parse_mode="HTML" donde se usa formato
- [ ] Callbacks responden correctamente

---

*Archivo de tracking simple para seguimiento de avance de FASE 1*
