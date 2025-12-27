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

## FASE N3: Integración con Orquestadores
- [ ] Extender RequirementType con tipos narrativos
- [ ] Extender validate_unlock_conditions
- [ ] NarrativeOrchestrator
- [ ] Extender RewardOrchestrator con parámetros narrativos
- [ ] Extender ConfigurationOrchestrator con property narrative
- [ ] Extender check_unlock_conditions en RewardService
- [ ] Tests integración

**Entregable:** Narrativa integrada con gamificación

---

## FASE N4: Handlers Usuario
- [ ] user/story.py - Mostrar fragmento actual
- [ ] user/decisions.py - Procesar decisiones
- [ ] Botón "📖 Historia" en /start
- [ ] FSM si necesario

**Entregable:** Usuario puede navegar historia

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
