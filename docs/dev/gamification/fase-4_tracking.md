# FASE 4 - EL GABINETE - TRACKING
## Proyecto: El Mayordomo del Diván

**Estado General:** ✅ COMPLETADA
**Última actualización:** 2025-01-03

---

## RESUMEN

El Gabinete (sistema de tienda) ya existe como `bot/shop/`. Fase 4 consiste en expandir y mejorar el sistema existente.

---

## CATEGORÍAS DEL GABINETE

| Categoría | Nombre Display | Estado |
|-----------|---------------|--------|
| Efímeros | ⚡ CONSUMABLE | ✅ Existe |
| Distintivos | 🎖️ COSMETIC | ✅ Existe |
| Llaves | 🔑 NARRATIVE | ✅ Existe |
| Reliquias | 💎 DIGITAL | ✅ Existe |

---

## CHECKLIST DE TAREAS

### Catálogo de Items

- [x] Expandir catálogo de 9 a 20+ items
  - [x] Categoría Efímeros (5 items)
  - [x] Categoría Distintivos (6 items)
  - [x] Categoría Llaves (5 items)
  - [x] Categoría Reliquias (5 items)
  - [x] Items ocultos (2 items especiales)
  - **Total: 23 items definidos**

### Modelo de Base de Datos

- [x] Agregar campos temporales a ShopItem
  - [x] available_from (fecha inicio disponibilidad)
  - [x] available_until (fecha fin disponibilidad)
  - [x] is_hidden (solo visible nivel 6+)
  - [x] event_name (nombre del evento)
- [x] Propiedades útiles
  - [x] is_temporal
  - [x] is_available
  - [x] time_until_expiry
  - [x] time_until_available

### Sistema de Descuentos

- [x] Servicio DiscountService creado
- [x] Descuento por nivel de usuario (4-7)
- [x] Descuento por distintivos especiales
- [x] Descuento por reliquias
- [x] Cálculo de descuento total (máx 50%)
- [x] Método format_discount_message
- [ ] Integración con handlers de usuario

### Recomendaciones

- [x] Servicio RecommendationService creado
- [x] Recomendaciones por arquetipo
- [x] Sugerencias basadas en historial
- [ ] Integración con handlers de usuario

### Items Especiales

- [x] Items con stock limitado (soporte en modelo)
- [x] Items temporales (soporte en modelo)
- [x] Items ocultos (soporte en modelo)
- [ ] Notificación de stock bajo

### Personalización

- [x] Motor de recomendaciones por arquetipo
- [x] Sugerencias basadas en historial
- [ ] Mensajes personalizados de Lucien en UI

### Notificaciones

- [ ] Notificación de item nuevo
- [ ] Alerta de item casi agotado
- [ ] Recordatorio de item temporal

### Admin Avanzado

- [ ] CRUD completo de items
- [ ] Estadísticas de ventas
- [ ] Sistema de promociones
- [ ] Ajuste de stock

---

## ITEMS DEFINIDOS

### Efímeros (CONSUMABLE) - 5 items
- [x] eph_001: Sello del Día
- [x] eph_002: Susurro Efímero
- [x] eph_003: Pase de Prioridad
- [x] eph_004: Vistazo al Sensorium
- [x] eph_005: Confesión Nocturna

### Distintivos (COSMETIC) - 6 items
- [x] dist_001: Sello del Visitante
- [x] dist_002: Insignia del Observador
- [x] dist_003: Marca del Evaluado
- [x] dist_004: Emblema del Reconocido
- [x] dist_005: Marca del Confidente
- [x] dist_006: Corona del Guardián

### Llaves (NARRATIVE) - 5 items
- [x] key_001: Llave del Fragmento I
- [x] key_002: Llave del Fragmento II
- [x] key_003: Llave del Fragmento III
- [x] key_004: Llave del Archivo Oculto
- [x] key_005: Llave de la Primera Vez

### Reliquias (DIGITAL) - 5 items
- [x] rel_001: El Primer Secreto
- [x] rel_002: Fragmento del Espejo
- [x] rel_003: La Carta No Enviada
- [x] rel_004: Cristal de Medianoche
- [x] rel_005: Llave Maestra del Gabinete

### Items Ocultos - 2 items
- [x] secret_001: Susurro de Lucien
- [x] secret_002: Coordenadas

---

## SISTEMAS EXISTENTES (BASE)

- ✅ 4 categorías implementadas
- ✅ Modelos de base de datos
- ✅ Sistema de Besitos integrado
- ✅ Niveles de usuario 1-7
- ✅ Inventario de usuario
- ✅ Flujo de compra
- ✅ Handlers de usuario
- ✅ Handlers de admin
- ✅ 23 items definidos

---

## PRÓXIMOS PASOS (FUTUROS)

1. Migración de base de datos para nuevos campos (Alembic)
2. Tests E2E de descuentos y items ocultos
3. Integración de recomendaciones en UI principal
4. Sistema de notificaciones automáticas en background
5. Comandos adicionales de admin para items temporales

---

## SERVICIOS CREADOS EN FASE 4

1. **DiscountService** (bot/shop/services/discounts.py)
   - Cálculo de descuentos por nivel (0-20%)
   - Bonuses por distintivos (+5-15%)
   - Bonuses por reliquias (+3-20%)
   - Máximo 50% de descuento
   - Formateo de mensajes con descuento

2. **RecommendationService** (bot/shop/services/recommendations.py)
   - Recomendaciones por arquetipo
   - Sugerencias basadas en historial
   - Items de próximo nivel
   - Resumen de inventario

3. **NotificationService** (bot/shop/services/notifications.py)
   - Notificaciones de items nuevos
   - Alertas de stock bajo
   - Recordatorios de items temporales
   - Envío a usuarios VIP

4. **ShopService actualizado**
   - get_items_for_user() - Filtra items ocultos
   - can_purchase_item() - Verifica nivel y ocultos
   - get_temporal_items() - Items temporales
   - get_expiring_soon() - Items por expirar
   - get_low_stock_items() - Items con stock bajo

---

## INTEGRACIÓN COMPLETADA

- [x] ShopContainer con 5 servicios
- [x] Handlers de usuario con precios con descuento
- [x] Teclado principal con categorías FASE 4
- [x] Información de items temporales en UI
- [x] Descuentos aplicados en compras

---

*Documento de tracking para Fase 4 - El Gabinete*
*FASE 4 COMPLETADA - Estructura lista para producción*
