# FASE 2: ECONOMÍA DE BESITOS - TRACKING DE AVANCE

**Objetivo:** Implementar y conectar el sistema de economía con todos los servicios del bot.

---

## ESTADO DEL SISTEMA ANTES DE FASE 2

### Archivos Base Existentes (FASE 0 + FASE 1)
- [x] `bot/utils/lucien_messages.py` - Biblioteca de mensajes con voz de Lucien
- [x] `bot/gamification/config/archetypes.py` - 6 arquetipos expandidos
- [ ] `bot/gamification/config/economy.py` - POR CREAR (economía de besitos)
- [x] `bot/gamification/services/besito.py` - Servicio de besitos
- [x] `bot/gamification/services/daily_gift.py` - Sistema de regalo diario
- [x] `bot/gamification/services/level.py` - Servicio de niveles
- [x] `bot/gamification/services/reaction.py` - Servicio de reacciones

### Servicios Existentes (por revisar valores hardcodeados)
- [x] `bot/gamification/services/besito.py` - Valores por integrar
- [x] `bot/gamification/services/daily_gift.py` - Valores por integrar
- [x] `bot/gamification/services/reaction.py` - Valores por integrar
- [x] `bot/gamification/services/mission.py` - Valores por integrar

---

## TAREAS FASE 2

### F2.1 - Conectar Economy Config con Servicios
**Estado:** ✅ COMPLETADO

- [x] Crear `bot/gamification/config/economy.py` con EconomyConfig
- [x] Agregar valores de recompensas por acción
- [x] Agregar valores de bonificaciones de racha
- [x] Agregar umbrales de niveles (LEVELS)
- [x] Actualizar bot/gamification/config/__init__.py
- [x] Reemplazar valores hardcodeados en daily_gift.py
- [x] Reemplazar valores hardcodeados en reaction.py
- [x] Verificar que cambios en economy.py afectan comportamiento

---

### F2.2 - Sistema de Niveles del Protocolo de Acceso
**Estado:** ✅ COMPLETADO

- [x] Verificar que economy.py tiene LEVELS completo (7 niveles)
- [x] Level service ya existe con check_and_apply_level_up()
- [x] Integrar level-up en besito service (grant_besitos)
- [x] Crear scripts/seed_levels.py con upsert
- [x] Notificación de level-up a través de container.notifications
- [x] Niveles ya creados en BD (11 niveles totales)

---

### F2.3 - Sistema de Rachas Mejorado
**Estado:** Pendiente

- [ ] Crear/actualizar streak service
- [ ] Definir hitos de racha en economy.py
- [ ] Mensajes de Lucien para rachas (hitos, perdida, continuidad)
- [ ] Integrar con daily gift
- [ ] Mostrar racha en perfil

---

### F2.4 - Notificaciones Contextuales de Besitos
**Estado:** Pendiente

- [ ] Crear/actualizar notification service
- [ ] Mensajes según contexto (reacción, misión, regalo, racha)
- [ ] Mensajes de milestones de totales
- [ ] Integrar en besito service
- [ ] Reglas de no-spam

---

### F2.5 - Historial de Transacciones
**Estado:** Pendiente

- [ ] Agregar callback para historial en besitos handler
- [ ] Handler de historial con paginación
- [ ] Método get_recent_transactions en besito service
- [ ] Mensajes de Lucien para historial
- [ ] Integración en menú

---

### F2.6 - Panel de Economía Admin
**Estado:** Pendiente

- [ ] Crear handler economy_panel.py
- [ ] Agregar botón en menú admin
- [ ] Ver top usuarios
- [ ] Ajustar valores (FSM)
- [ ] Integración en menú admin

---

## CRITERIOS DE ACEPTACIÓN

### Funcionalidad
- [ ] Valores de economy.py se usan en todos los servicios
- [ ] Cambiar un valor en economy.py afecta el comportamiento
- [ ] Los 7 niveles funcionan correctamente
- [ ] Subir de nivel muestra notificación de Lucien
- [ ] Rachas se rastrean y dan bonificaciones
- [ ] Hitos de racha (7, 30 días) dan bonus
- [ ] Notificaciones varían según contexto
- [ ] Historial muestra últimas transacciones
- [ ] Panel admin muestra estadísticas

### Integración en Menús
- [ ] Historial accesible desde menú de besitos
- [ ] Panel economía accesible desde menú admin
- [ ] Todos los botones tienen callbacks correctos
- [ ] Navegación "Volver" funciona en todos los niveles

### Consistencia
- [ ] Todos los mensajes usan voz de Lucien
- [ ] Formato de besitos consistente
- [ ] Nombres de niveles consistentes en todo el bot

---

*Archivo de tracking simple para seguimiento de avance de FASE 2*
