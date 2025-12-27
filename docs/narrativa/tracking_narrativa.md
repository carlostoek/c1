# 📖 Tracking - Módulo Narrativa

## FASE N1: Modelos y Migración (Fundación) ✅
- [x] Estructura `bot/narrative/`
- [x] Enums (ChapterType, RequirementType, ArchetypeType)
- [x] Modelos de BD (6 modelos)
- [x] Migración Alembic (010_add_narrative_module.py)
- [x] NarrativeContainer base
- [x] Tests modelos (5/5 pasando)

**Entregable:** ✅ BD lista, container funcional, tests pasando

---

## FASE N2: Servicios Core ✅
- [x] FragmentService (CRUD fragmentos)
- [x] ProgressService (avance usuario)
- [x] DecisionService (procesar decisiones)
- [x] Tests unitarios servicios (6/6 pasando)

**Entregable:** ✅ Servicios funcionando sin UI, tests validados

---

## FASE N3: Integración con Orquestadores ✅
- [x] Extender RequirementType con tipos narrativos
- [x] Extender validate_unlock_conditions
- [x] NarrativeOrchestrator
- [x] Extender RewardOrchestrator con parámetros narrativos
- [x] Extender ConfigurationOrchestrator con property narrative
- [x] Extender check_unlock_conditions en RewardService
- [x] ChapterService creado
- [x] Tests integración (13/13 pasando)

**Entregable:** ✅ Narrativa integrada con gamificación, 13 tests pasando

---

## FASE N4: Handlers Usuario ✅
- [x] user/story.py - Mostrar fragmento actual
- [x] user/decisions.py - Procesar decisiones
- [x] Botón "📖 Historia" en /start (penúltimo, antes de Juego Kinky)
- [x] narrative_router integrado en dispatcher
- [x] NarrativeContainer.chapter property agregada
- [x] FragmentService.get_entry_point_by_type() implementado
- [x] Tests de handlers (9/9 pasando)

**Entregable:** ✅ Usuario puede navegar historia desde menú principal, 9 tests pasando

---

## FASE N5: Admin + Contenido
- [ ] Wizard crear fragmentos
- [ ] Seed data (narrativa de narrativo.md)
- [ ] Estadísticas básicas

**Entregable:** Admin puede crear contenido, historia base cargada

---

## FASE N6: Arquetipos (Simple)
- [ ] ArchetypeService básico
- [ ] Detección por tiempo de respuesta
- [ ] Ramificaciones por arquetipo

**Entregable:** Sistema detecta arquetipos y adapta caminos
