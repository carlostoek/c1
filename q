* [33m8015ce3[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mdev[m[33m, [m[1;31morigin/dev[m[33m)[m feat: integrate PointsService with ServiceContainer and add complete tests/docs
* [33m4010237[m feat: Phase 2.3 - Implement PointsService history and advanced queries
* [33m0461044[m feat: Phase 2.1 - Implement PointsService core structure
* [33md2ed1d5[m feat: Phase 1 - Implement Points Service database models and migrations
* [33m2562dd7[m fixes reaction
* [33mc6f578f[m fix: Corregir firma de award_besitos y llamadas a event_bus.publish
* [33m36aff7d[m docs: Add comprehensive documentation for reaction system implementation
* [33m2e8a327[m feat: Implement user reaction handlers
* [33m580fce9[m feat: Integrate reaction and protection options into broadcasting
* [33m6605a48[m feat: Implement reaction configuration handlers
* [33m86d8ca2[m feat: Phase 2.3 - Integrate ReactionService in ServiceContainer
* [33m867f27b[m feat: Phase 1 - Add reaction system database models and migrations
* [33m4d0d2bb[m Update CLAUDE.md
* [33m15d1783[m docs: Add comprehensive documentation for new features
* [33mdaf0dea[m docs: add comprehensive gamification documentation to reference guide
* [33m1da9e3d[m feat: implement complete gamification system with Besitos, badges, and daily login
* [33mf82af15[m docs: add notification service documentation to reference guide
* [33mffbb687[m feat: implement notification service with reward batch system
* [33m0bdcbff[m update docs
* [33m8caea6b[m docs: reorganizar documentación en archivos especializados
* [33m7d4e785[m docs: add B1 event bus system documentation
* [33mee4aba2[m refactor: make event bus non-blocking (fire-and-forget pattern)
* [33mfbde8c8[m feat: implement complete event bus system (B1) with pub/sub architecture
* [33m098a977[m fix: apply PR#8 review suggestions - database integrity and transaction management
* [33m2535de7[m fix: agregar soporte para botones URL en create_inline_keyboard
* [33mfa792e7[m docs: Add Pricing System (A1), User Roles (A2), and Deep Links (A3) documentation
* [33m59bc132[m docs: actualizar CLAUDE.md con documentación A3 completada
* [33m8206ca3[m feat: implementar generación de tokens con deep links y activación automática (A3)
* [33m69c141c[m feat: implementar sistema completo de roles de usuario (A2)
* [33mfa38f6c[m feat: implementar sistema completo de tarifas/planes de suscripción (A1)
* [33m09818d5[m docs: actualizar CLAUDE.md - ONDA 2 COMPLETADA
* [33m2e99e11[m feat: implementar testing E2E ONDA 2 (T29)
* [33m08e410b[m docs: actualizar CLAUDE.md con ONDA 2 y T28 completado
* [33m207ab77[m feat: implementar formatters y helpers reutilizables (T28)
* [33m24f7d67[m docs: Add Complete Status Dashboard documentation (T27)
* [33m61bce2c[m fix: resolver error de datetime naive vs aware en dashboard
* [33m1313638[m fix: corregir claves de configuración en dashboard
* [33m3335f99[m feat: implementar dashboard estado completo (T27)
* [33m105e193[m fix: resolver timeouts y mejorar error handling de callbacks expirados
* [33md95f064[m docs: Add Pagination System (T24), Paginated VIP Management (T25), and Free Queue Visualization (T26)
* [33m9194fd2[m feat: implementar visualización cola Free con paginación y filtros (T26)
* [33m3a28472[m feat: implementar gestión paginada de suscriptores VIP (T25)
* [33mc1ca4e7[m feat: implementar sistema de paginación reutilizable (T24)
* [33mb58bbd8[m docs: Add FSM States for Broadcasting (T21), Broadcasting Handler (T22), and Automatic Reactions (T23)
* [33mf20c3b3[m feat: implementar configuración de reacciones automáticas (T23)
* [33m61f5f47[m feat: implementar handler broadcasting con preview (T22)
* [33maec6488[m chore: limpiar archivos temporales de tests
* [33m184feb2[m feat: implementar estados FSM para broadcasting multimedia (T21)
* [33m98cc73d[m feat: mejorar handlers estadísticas detalladas (T20) - Análisis contextual y tasas
* [33m11688f7[m docs: Add General Statistics Handler documentation (T19)
* [33mf17c427[m feat: implementar handler estadísticas generales (T19) - Dashboard de stats
* [33m8280a76[m docs: Add StatsService documentation (T18) to SERVICES.md
* [33m6bbc44e[m feat: implementar StatsService (T18) - Motor de estadísticas del sistema
* [33mf8570d7[m fix: resolver error de timezone al calcular dias restantes VIP
* [33m535970f[m fix: importar handlers vip_flow y free_flow para activar decoradores
* [33m2f6d2af[m fix: activar timeout solo durante shutdown, no al inicio
* [33m8c7cbcd[m feat: registrar handlers admin y user en dispatcher
* [33m1a4b655[m fix: mejorar manejo de shutdown y reintentos de conexión en startup
* [33m96dcfba[m docs: actualizar CLAUDE.md con T16 completado
* [33m59b88ee[m ONDA 1 Fase 1.5: T16 - Integracion Final y Testing E2E
* [33m885815a[m docs: actualizar documentación con Background Tasks (T15)
* [33meeee716[m docs: actualizar documentación con handlers User (T14) - /start y flujos
* [33m5fc772c[m docs: actualizar CLAUDE.md con T15 completado
* [33mdaed270[m ONDA 1 Fase 1.4: T15 - Background Tasks (Expulsion VIP + Procesamiento Free)
* [33mfdb6a7b[m docs: actualizar CLAUDE.md con T14 - Handlers User completado
* [33m29cb6e8[m ONDA 1 Fase 1.3: T14 - Handlers User (/start, Canje Token, Solicitud Free)
* [33m381d5d1[m docs: actualizar CLAUDE.md con T13 - Handlers VIP y Free completado
* [33m0a67180[m ONDA 1 Fase 1.3: T13 - Handlers VIP y Free (Setup + Token Generation)
* [33m067e924[m docs: actualizar documentación con handler /admin (Menú Principal) (T12)
* [33mb2db4ff[m docs: actualizar CLAUDE.md con T12 - Handler /admin completado
* [33m8a3451e[m ONDA 1 Fase 1.3: T12 - Handler /admin (Menú Principal)
* [33m45752ee[m docs: actualizar documentación con FSM States para Admin y User (T11)
* [33m2050e31[m docs: actualizar CLAUDE.md con T11 - Estados FSM completado
* [33m954dbf7[m ONDA 1 Fase 1.3: T11 - Estados FSM para Admin y User
* [33m0f7cbc3[m docs: actualizar documentación con middlewares AdminAuth y Database (T10)
* [33m59a1b25[m docs: actualizar CLAUDE.md con T10 - Middlewares completado
* [33md423664[m ONDA 1 Fase 1.3: T10 - Middlewares (AdminAuth + Database)
* [33m61d3163[m docs: actualizar documentación con ConfigService (T9)
* [33m3166f4c[m docs: actualizar CLAUDE.md con flujo de desarrollo completo ONDA 1
* [33m0bc06d5[m ONDA 1 Fase 1.2: T9 - Config Service (Gestion de Configuracion)
* [33mfa8e607[m docs: actualizar documentación con ChannelService (T8)
* [33m8e7ed92[m ONDA 1 Fase 1.2: T8 - Channel Service (Gestión de Canales)
* [33m336919d[m docs: actualizar documentación con T6 y T7 - Service Container y Subscription Service
* [33m44b434b[m ONDA 1 Fase 1.2: T7 - Subscription Service (Lógica VIP/Free/Tokens)
* [33m22396ff[m ONDA 1 Fase 1.2: T6 - Service Container con Dependency Injection
*   [33m1d7ef80[m Merge pull request #1 from carlostoek/main
[32m|[m[33m\[m  
[32m|[m * [33m94b9355[m ONDA 1 Fase 1.1: Documentación Completa
[32m|[m * [33m4c76ab2[m ONDA 1 Fase 1.1: Setup y Fundamentos - MVP Completo
[32m|[m[32m/[m  
* [33m6047e45[m first commit
