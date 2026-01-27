# Roadmap: Telegram Bot VIP/Free - Sistema de Menus

## Milestones

- ✅ **v1.0 LucienVoiceService** - Phases 1-4 (shipped 2026-01-24)
- 🚧 **v1.1 Sistema de Menús** - Phases 5-11 (in progress)
- 📋 **v2.0 Future Enhancements** - Phases 12+ (planned)

## Phases

<details>
<summary>✅ v1.0 LucienVoiceService (Phases 1-4) - SHIPPED 2026-01-24</summary>

### Phase 1: Service Foundation & Voice Rules
**Goal**: BaseMessageProvider abstract class enforcing stateless interface with template composition utilities
**Plans**: 3 plans

Plans:
- [x] 01-01: BaseMessageProvider abstract class with stateless interface
- [x] 01-02: Template composition engine with variable interpolation
- [x] 01-03: HTML formatting standards across all message types

### Phase 2: Template Organization & Admin Migration
**Goal**: Admin message providers and handler migration demonstrating voice consistency
**Plans**: 3 plans

Plans:
- [x] 02-01: AdminMainProvider and AdminVIPProvider
- [x] 02-02: AdminFreeProvider with Free menu variations
- [x] 02-03: Admin handlers migration (main, vip, free)

### Phase 3: User Flow Migration & Testing Strategy
**Goal**: User message providers and handler migration with semantic test helpers
**Plans**: 4 plans

Plans:
- [x] 03-01: UserStartProvider with welcome messages
- [x] 03-02: UserFlowProvider with VIP/Free flow messages
- [x] 03-03: User handlers migration (start, vip_flow, free_flow)
- [x] 03-04: Semantic test helpers and variation-safe testing

### Phase 4: Advanced Voice Features
**Goal**: Session-aware variation selection preventing repetition with voice linter
**Plans**: 4 plans

Plans:
- [x] 04-01: SessionHistoryProvider for exclusion window tracking
- [x] 04-02: Session context integration in ServiceContainer
- [x] 04-03: AST-based voice linter for consistency enforcement
- [x] 04-04: Message preview CLI tool and E2E test validation

</details>

---

## 🚧 v1.1 Sistema de Menús (In Progress)

**Milestone Goal:** Sistema de menús contextuales según rol (Admin/VIP/Free) completamente integrado con LucienVoiceService, con gestión de contenido y notificaciones de interés.

### Phase 5: Role Detection & Database Foundation
**Goal**: Sistema detecta automáticamente rol del usuario (Admin/VIP/Free) con modelos de base de datos para contenido, intereses y cambios de rol.
**Status**: ✅ Complete
**Completed**: 2026-01-25
**Plans**: 5 plans completed

Plans:
- [x] 05-01-PLAN.md — Role detection service with automatic role calculation
- [x] 05-02A-PLAN.md — Database enums and ContentPackage model
- [x] 05-02B-PLAN.md — UserInterest and UserRoleChangeLog models with table creation
- [x] 05-03-PLAN.md — ContentService with CRUD operations for content packages
- [x] 05-04-PLAN.md — MenuRouter and role-based menu routing
- [x] 05-05-PLAN.md — RoleChangeService for audit logging (MENU-04)

### Phase 6: VIP/Free User Menus
**Goal**: Menús de usuario VIP y Free con información de suscripción, contenido Premium y botones "Me interesa" que notifican al admin.
**Status**: ✅ Complete
**Completed**: 2026-01-25
**Requirements**: VOICE-01, VOICE-02, VOICE-06, VIPMENU-01, VIPMENU-02, VIPMENU-03, VIPMENU-04, FREEMENU-01, FREEMENU-02, FREEMENU-03, FREEMENU-04, FREEMENU-05, CONTENT-07, NAV-04, NAV-05
**Success Criteria** (what must be TRUE):
  1. Usuario VIP abre menú con su información de suscripción (expiración, plan actual)
  2. Usuario VIP ve opción "Premium" con paquetes y botones "Me interesa"
  3. Usuario Free abre menú con "Mi Contenido" listando paquetes disponibles
  4. Cada paquete muestra información con botón "Me interesa" que crea registro de interés
  5. Menú Free tiene opción "Canal VIP" con información de suscripción
**Plans**: 4 plans

Plans:
- [x] 06-01-PLAN.md — UserMenuProvider with VIP and Free menu messages
- [x] 06-02-PLAN.md — VIP menu handlers with subscription info and Premium section
- [x] 06-03-PLAN.md — Free menu handlers with content browsing and VIP upgrade option
- [x] 06-04-PLAN.md — Menu navigation with back buttons replacing hardcoded keyboards.py

### Phase 7: Admin Menu with Content Management
**Goal**: Menú admin con gestión completa de paquetes de contenido (crear, editar, desactivar) y navegación centralizada.
**Depends on**: Phase 5
**Requirements**: ADMIN-CONTENT-01, ADMIN-CONTENT-02, ADMIN-CONTENT-03, ADMIN-CONTENT-04, ADMIN-CONTENT-05, CONTENT-04, CONTENT-05, CONTENT-06, NAV-01, NAV-02, NAV-03
**Success Criteria** (what must be TRUE):
  1. Admin abre menú con opción "Paquetes de Contenido"
  2. Admin puede listar todos los paquetes (activos e inactivos)
  3. Admin puede crear nuevo paquete con wizard paso a paso
  4. Admin puede editar paquete existente (nombre, descripción, precio, categoría)
  5. Admin puede desactivar paquete (soft delete con is_active)
  6. Sistema de callbacks unificado para navegación (menu:main, menu:vip, menu:free)
**Plans**: 4 plans

Plans:
- [ ] 07-01-PLAN.md — AdminContentMessages provider with Lucien's voice for content UI
- [ ] 07-02-PLAN.md — Content navigation handlers (menu, list, detail, pagination)
- [ ] 07-03-PLAN.md — ContentPackageStates FSM state group for creation wizard
- [ ] 07-04-PLAN.md — Content CRUD operations (create wizard, edit prompts, toggle active/inactive)

### Phase 8: Interest Notification System
**Goal**: Botón "Me interesa" crea registro de interés y envía notificación privada al admin con información del usuario y paquete.
**Depends on**: Phase 7
**Requirements**: INTEREST-01, INTEREST-02, INTEREST-03, INTEREST-04, INTEREST-05, ADMIN-INT-01, ADMIN-INT-02, ADMIN-INT-03, ADMIN-INT-04, ADMIN-INT-05
**Success Criteria** (what must be TRUE):
  1. Usuario marca "Me interesa" en paquete y sistema crea registro en UserInterest
  2. Admin recibe mensaje privado con nombre de usuario, link al perfil y paquete de interés
  3. Admin puede ver lista de intereses organizada por fecha (último arriba)
  4. Admin puede marcar interés como "Atendido"
  5. InterestService existe para gestionar intereses con deduplicación
**Plans**: TBD

Plans:
- [ ] 08-01: Interest notification handler with deduplication
- [ ] 08-02: Admin notification sender with user info and package details
- [ ] 08-03: Interest list viewer for admins with pagination
- [ ] 08-04: Mark interest as attended functionality

### Phase 9: User Management Features
**Goal**: Admin puede gestionar usuarios (ver info, cambiar rol, bloquear, expulsar) con registro de auditoría.
**Depends on**: Phase 8
**Requirements**: ADMIN-USR-01, ADMIN-USR-02, ADMIN-USR-03, ADMIN-USR-04, ADMIN-USR-05, MENU-03
**Success Criteria** (what must be TRUE):
  1. Admin abre menú con opción "Gestión de Usuarios"
  2. Admin puede ver información detallada de cualquier usuario (rol, suscripción, estado)
  3. Admin puede cambiar rol de usuario (Free↔VIP) con confirmación
  4. Admin puede bloquear usuario (impide usar el bot) con confirmación
  5. Admin puede expulsar usuario (elimina del canal) con confirmación
  6. Admin puede ver rol de cualquier usuario en el sistema
**Plans**: TBD

Plans:
- [ ] 09-01: User management service with role change, block, and expel operations
- [ ] 09-02: User info viewer handler showing detailed user information
- [ ] 09-03: Role change functionality with confirmation and audit logging
- [ ] 09-04: User block and expel functionality with confirmation

### Phase 10: Free Channel Entry Flow
**Goal**: Flujo de ingreso al canal Free con voz de Lucien, redes sociales de la creadora, tiempo de espera y aprobación automática.
**Depends on**: Phase 6
**Requirements**: FLOW-FREE-01, FLOW-FREE-02, FLOW-FREE-03, FLOW-FREE-04, FLOW-FREE-05, FLOW-FREE-06, VOICE-03, VOICE-04, VOICE-05
**Success Criteria** (what must be TRUE):
  1. Mensaje de solicitud de acceso usa voz de Lucien explicando tiempo de espera
  2. Mensaje incluye redes sociales de la creadora con links clickeables
  3. Mensaje sugiere seguir redes sociales para acelerar ingreso
  4. Mensaje de aprobación incluye botón de acceso directo al canal
  5. Aprobación automática después de tiempo configurado (5 min actual)
  6. Mensaje de bienvenida al canal VIP con voz de Lucien
**Plans**: TBD

Plans:
- [ ] 10-01: UserFlowProvider with Free entry flow messages and social media links
- [ ] 10-02: Free entry request handler with wait time explanation
- [ ] 10-03: Free entry approval handler with channel invite button
- [ ] 10-04: VIP welcome message handler with Lucien's voice
- [ ] 10-05: Automatic approval background task integration

### Phase 11: Documentation
**Goal**: Documentación exhaustiva del sistema de menús en código y archivos .md con guía de integración para agregar nuevas opciones.
**Depends on**: Phase 10
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Success Criteria** (what must be TRUE):
  1. Todos los servicios y handlers tienen docstrings exhaustivos
  2. Documentación en .md sobre arquitectura de menús existe
  3. Guía de integración para agregar nuevas opciones de menú existe
  4. Ejemplos de uso del sistema de menús están documentados
**Plans**: TBD

Plans:
- [ ] 11-01: Code documentation with comprehensive docstrings
- [ ] 11-02: Architecture documentation for menu system
- [ ] 11-03: Integration guide for adding new menu options
- [ ] 11-04: Usage examples and documentation

---

## Progress

**Execution Order:**
Phases execute in numeric order: 5 → 6 → 7 → 8 → 9 → 10 → 11

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Service Foundation & Voice Rules | v1.0 | 3/3 | Complete | 2026-01-23 |
| 2. Template Organization & Admin Migration | v1.0 | 3/3 | Complete | 2026-01-23 |
| 3. User Flow Migration & Testing Strategy | v1.0 | 4/4 | Complete | 2026-01-24 |
| 4. Advanced Voice Features | v1.0 | 4/4 | Complete | 2026-01-24 |
| 5. Role Detection & Database Foundation | v1.1 | 5/5 | Complete | 2026-01-25 |
| 6. VIP/Free User Menus | v1.1 | 4/4 | Complete | 2026-01-25 |
| 7. Admin Menu with Content Management | v1.1 | 0/4 | Not started | - |
| 8. Interest Notification System | v1.1 | 0/TBD | Not started | - |
| 9. User Management Features | v1.1 | 0/TBD | Not started | - |
| 10. Free Channel Entry Flow | v1.1 | 0/TBD | Not started | - |
| 11. Documentation | v1.1 | 0/TBD | Not started | - |

**v1.1 Progress:** ████░░░░░░░ 20% (9/60 requirements complete)
