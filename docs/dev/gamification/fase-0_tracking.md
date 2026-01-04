# FASE 0: TRACKING DE IMPLEMENTACIÓN
## Hoja de Ruta - Fundamentos del Sistema

**Documento base:** `fase-0.md` (referencia)
**Fecha inicio:** 2025-01-03

---

## ✅ ESTADO GENERAL

- [x] F0.2: Biblioteca de Mensajes de Lucien V1 ✅
- [x] F0.3: Mapeo de Arquetipos Expandido ✅
- [x] F0.4: Inventario del Gabinete (Tienda) ✅
- [x] F0.5: Estructura de Contenido Narrativo ✅

**Progreso:** 4/4 completados (100%) ✅

---

## 📋 F0.2: BIBLIOTECA DE MENSAJES DE LUCIEN V1 ✅

**Archivo creado:** `bot/utils/lucien_messages.py`

### Tareas

- [x] Crear clase `LucienMessages`
- [x] Categoría: ONBOARDING (4 mensajes)
  - [x] WELCOME_FIRST
  - [x] WELCOME_RETURNING
  - [x] FIRST_ACTION_ACKNOWLEDGED
  - [x] PROTOCOL_EXPLANATION
- [x] Categoría: BESITOS (6 mensajes)
  - [x] FAVOR_EARNED
  - [x] FAVOR_EARNED_MILESTONE
  - [x] FAVOR_BALANCE
  - [x] FAVOR_INSUFFICIENT
  - [x] FAVOR_SPENT
- [x] Categoría: NIVELES (8 mensajes)
  - [x] LEVEL_UP_BASE
  - [x] LEVEL_UP_2 a LEVEL_UP_7 (mensajes específicos)
  - [x] LEVEL_PROGRESS
- [x] Categoría: ARQUETIPOS (6 mensajes)
  - [x] ARCHETYPE_DETECTED_EXPLORER
  - [x] ARCHETYPE_DETECTED_DIRECT
  - [x] ARCHETYPE_DETECTED_ROMANTIC
  - [x] ARCHETYPE_DETECTED_ANALYTICAL
  - [x] ARCHETYPE_DETECTED_PERSISTENT
  - [x] ARCHETYPE_DETECTED_PATIENT
- [x] Categoría: ERRORES (5 mensajes)
  - [x] ERROR_GENERIC
  - [x] ERROR_NOT_FOUND
  - [x] ERROR_PERMISSION_DENIED
  - [x] ERROR_RATE_LIMITED
  - [x] ERROR_MAINTENANCE
- [x] Categoría: TIENDA/GABINETE (4 mensajes)
  - [x] SHOP_WELCOME
  - [x] SHOP_ITEM_PURCHASED
  - [x] SHOP_ITEM_NOT_AVAILABLE
  - [x] SHOP_BROWSE_CATEGORY
- [x] Categoría: MISIONES (4 mensajes)
  - [x] MISSION_NEW_AVAILABLE
  - [x] MISSION_PROGRESS_UPDATE
  - [x] MISSION_COMPLETED
  - [x] MISSION_FAILED
- [x] Categoría: RETENCIÓN (4 mensajes)
  - [x] INACTIVE_3_DAYS
  - [x] INACTIVE_7_DAYS
  - [x] INACTIVE_14_DAYS
  - [x] WELCOME_BACK
- [x] Categoría: CONVERSIÓN (5 mensajes)
  - [x] VIP_TEASER
  - [x] VIP_INVITATION_INTRO
  - [x] VIP_INVITATION_DETAIL
  - [x] VIP_INVITATION_CTA
  - [x] VIP_DECLINED_GRACEFUL
- [x] Helpers: format_progress_bar, format_coins

**Total mensajes:** 45 (41 + 4 helpers)
**Estado:** ✅ COMPLETADO
**Fecha:** 2025-01-03

---

## 📋 F0.3: MAPEO DE ARQUETIPOS EXPANDIDO ✅

**Archivos creados/modificados:**
- `bot/narrative/config/archetypes.py` (NUEVO)
- `bot/narrative/database/enums.py` (MODIFICADO)
- `bot/narrative/config/__init__.py` (ACTUALIZADO)

### Tareas

- [x] Crear archivo `bot/narrative/config/archetypes.py`
- [x] Crear enum `ExpandedArchetype` con 6 valores:
  - [x] EXPLORER
  - [x] DIRECT
  - [x] ROMANTIC
  - [x] ANALYTICAL
  - [x] PERSISTENT
  - [x] PATIENT
- [x] Crear clase `ArchetypeDetectionRules` con reglas para los 6 arquetipos
- [x] Crear mapeo de compatibilidad (arquetipos antiguos → nuevos)
- [x] Crear clase `ArchetypeScorer` con métodos de cálculo
  - [x] calculate_response_time_score()
  - [x] calculate_engagement_score()
  - [x] calculate_archetype_scores()
  - [x] get_dominant_archetype()
  - [x] get_archetype_confidence()
- [x] Crear diccionario `ARCHETYPE_TRAITS` con características narrativas
  - [x] lucien_tone, narrative_style, mission_type, conversion_trigger
  - [x] lucien_phrases, preferred_rewards, shop_preferences
- [x] Modificar `bot/narrative/database/enums.py`:
  - [x] Agregar 6 nuevos valores a `ArchetypeType`
  - [x] Mantener compatibilidad con IMPULSIVE, CONTEMPLATIVE, SILENT
  - [x] Agregar métodos is_expanded, is_legacy, get_expanded_archetypes(), get_legacy_archetypes()
- [x] Crear funciones helpers: map_legacy_archetype(), get_archetype_traits(), calculate_archetype_scores(), format_archetype_name(), get_archetype_description()

**Total:** 6 arquetipos expandidos + 3 legacy (compatibilidad)
**Estado:** ✅ COMPLETADO
**Fecha:** 2025-01-03

---

## 📋 F0.4: INVENTARIO DEL GABINETE (TIENDA) ✅

**Archivo creado:** `bot/shop/config/initial_inventory.py`

### Tareas

- [x] Crear mapeo `CATEGORY_MAPPING` (4 categorías)
- [x] Crear descripciones `CATEGORY_DESCRIPTIONS`
- [x] Crear lista `INITIAL_ITEMS` con 9 items:
  - [x] Sello del Visitante (COSMETIC, COMMON, 2 besitos)
  - [x] Susurro Efímero (CONSUMABLE, UNCOMMON, 3 besitos)
  - [x] Pase de Prioridad (CONSUMABLE, RARE, 5 besitos, stock: 50)
  - [x] Insignia del Observador (COSMETIC, UNCOMMON, 5 besitos)
  - [x] Llave del Fragmento Oculto (NARRATIVE, RARE, 10 besitos)
  - [x] Vistazo al Sensorium (CONSUMABLE, EPIC, 15 besitos, stock: 100)
  - [x] El Primer Secreto (NARRATIVE, EPIC, 20 besitos)
  - [x] Marca del Confidente (COSMETIC, LEGENDARY, 25 besitos, stock: 25)
  - [x] Reliquia de Diana (DIGITAL, LEGENDARY, 40 besitos, stock: 10)
- [x] Crear función `get_seed_data()`
- [x] Crear función `validate_item()`
- [x] Crear funciones helpers adicionales (get_items_by_type, get_items_by_rarity, get_featured_items, get_category_summary)
- [x] Verificar compatibilidad con modelos `ShopItem` existentes
- [x] Verificar que precios estén en rango definido (2-40 besitos)

**Total items:** 9
**Distribución:** 3 Consumibles, 3 Cosméticos, 2 Narrativos, 1 Digital
**Rango precios:** 2-40 besitos
**Estado:** ✅ COMPLETADO
**Fecha:** 2025-01-03

---

## 📋 F0.5: ESTRUCTURA DE CONTENIDO NARRATIVO ✅

**Archivos creados:**
- `bot/narrative/config/story_content.py`
- `bot/narrative/config/__init__.py`

### Tareas

- [x] Crear diccionario `SPEAKERS` (Diana, Lucien, Narrador)
- [x] Crear diccionario `CHALLENGE_TYPES` (6 tipos)
- [x] Crear estructura `CHAPTERS_FREE` (Niveles 1-3):
  - [x] Capítulo 1: "Los Kinkys - Bienvenida" (level 1) - 6 fragmentos completos
  - [x] Capítulo 2: "Los Kinkys - Observación" (level 2) - 2 fragmentos esqueleto
  - [x] Capítulo 3: "Los Kinkys - Perfil de Deseo" (level 3) - 2 fragmentos esqueleto
- [x] Crear estructura `CHAPTERS_VIP` (Niveles 4-6):
  - [x] Capítulo VIP 1: "El Diván - Entrada" (level 4) - 2 fragmentos completos
  - [x] Capítulo VIP 2: "El Diván - Profundización" (level 5) - esqueleto
  - [x] Capítulo VIP 3: "El Diván - Confidencias" (level 6) - esqueleto
- [x] Crear función `get_chapter_by_level()`
- [x] Crear función `get_fragments_for_chapter()`
- [x] Crear función `get_next_chapter()`
- [x] Crear funciones adicionales (get_entry_fragment, get_all_chapters, get_chapter_by_slug, get_fragment_by_key, validate_chapter, validate_fragment, get_content_summary)
- [x] Verificar compatibilidad con modelos `Chapter`, `Fragment` existentes

**Total:** 6 capítulos (3 FREE + 3 VIP), 12 fragmentos (8 completos + 4 esqueleto)
**Estado:** ✅ COMPLETADO
**Fecha:** 2025-01-03
**Nota:** El contenido completo de todos los fragmentos se completará en Fase 5.

---

## 📊 RESUMEN DE TAREAS

| Entregable | Archivos | Tareas | Estado |
|------------|----------|--------|--------|
| F0.2 | 1 archivo | 45 mensajes (41 + 4 helpers) | ✅ Completado |
| F0.3 | 3 archivos (1 nuevo, 2 modificados) | 6 arquetipos + scoring + traits | ✅ Completado |
| F0.4 | 1 archivo | 9 items + 6 funciones | ✅ Completado |
| F0.5 | 2 archivos | 6 capítulos + 9 funciones | ✅ Completado |

---

## 🚀 ORDEN RECOMENDADO DE IMPLEMENTACIÓN

1. **F0.2** - Lucien Messages (base para todo lo demás)
2. **F0.4** - Shop Inventory (depende de F0.2 para descripciones)
3. **F0.5** - Story Content (depende de F0.2 para mensajes)
4. **F0.3** - Arquetipos (más complejo, al final)

---

## 📝 NOTAS

- F0.1 (Economy Config) está OMITIDO porque ya está implementado en `bot/gamification/config.py`
- F0.3 requiere migración de enum, mantener compatibilidad con arquetipos existentes
- Todos los archivos deben tener type hints y docstrings
- No modificar modelos existentes, solo crear configuración

---

**Última actualización:** 2025-01-03

---

## 📝 LOG DE CAMBIOS

### 2025-01-03
- ✅ **F0.2 COMPLETADO**
  - Creado `bot/utils/lucien_messages.py`
  - 45 mensajes implementados (41 categorías + 4 helpers)
  - 9 categorías: ONBOARDING, BESITOS, NIVELES, ARQUETIPOS, ERRORES, TIENDA, MISIONES, RETENCIÓN, CONVERSIÓN
  - 2 helpers: `format_progress_bar()`, `format_coins()`
  - Sintaxis validada ✅
  - Todos los mensajes exportables ✅

- ✅ **F0.3 COMPLETADO**
  - Creado `bot/narrative/config/archetypes.py` (670 líneas)
  - Expandido `ArchetypeType` en `bot/narrative/database/enums.py` de 3 → 10 valores
  - 6 arquetipos expandidos: EXPLORER, DIRECT, ROMANTIC, ANALYTICAL, PERSISTENT, PATIENT
  - 3 arquetipos legacy mantenidos para compatibilidad: IMPULSIVE, CONTEMPLATIVE, SILENT
  - ArchetypeDetectionRules con reglas específicas por arquetipo
  - ArchetypeScorer con 5 métodos de cálculo de scores
  - ARCHETYPE_TRAITS con características narrativas por arquetipo
  - Mapeo de compatibilidad legacy → expandido
  - 7 funciones helpers: calculate_archetype_scores, map_legacy_archetype, get_archetype_traits, format_archetype_name, get_archetype_description, etc.
  - Compatibilidad con ArchetypeService existente ✅

- ✅ **F0.4 COMPLETADO**
  - Creado `bot/shop/config/initial_inventory.py`
  - 9 items implementados con distribución balanceada
  - 4 categorías con mapeos narrativos: Efímeros, Distintivos, Llaves, Reliquias
  - 6 funciones: get_seed_data(), validate_item(), get_items_by_type(), get_items_by_rarity(), get_featured_items(), get_category_summary()
  - Rango de precios: 2-40 besitos
  - Compatibilidad con modelos ShopItem validada ✅
  - Todos los items validados ✅

- ✅ **F0.5 COMPLETADO**
  - Creados `bot/narrative/config/story_content.py` y `__init__.py`
  - 6 capítulos implementados (3 FREE + 3 VIP)
  - 12 fragmentos (8 completos con contenido + 4 esqueleto para Fase 5)
  - 3 speakers definidos: Diana, Lucien, Narrador
  - 6 challenge types definidos
  - 9 funciones: get_chapter_by_level(), get_fragments_for_chapter(), get_next_chapter(), get_entry_fragment(), get_all_chapters(), get_chapter_by_slug(), get_fragment_by_key(), validate_chapter(), validate_fragment(), get_content_summary()
  - Compatibilidad con modelos Chapter/Fragment validada ✅
  - Estructura lista para contenido completo en Fase 5 ✅
