# Phase 07: Admin Menu with Content Management - Research

**Researched:** 2026-01-25
**Domain:** Aiogram 3 FSM wizards + Admin CRUD + ContentPackage management
**Confidence:** HIGH

## Summary

Phase 7 implements a complete admin interface for managing content packages with CRUD operations. The phase builds upon existing infrastructure: `ContentService` (Phase 5), `MenuRouter` (Phase 6), and pagination utilities. Key patterns include FSM wizards for multi-step creation, inline keyboard editing for updates, and soft delete (is_active flag) for deactivation.

**Primary recommendation:** Use existing FSM wizard patterns from `PricingSetupStates` (pricing.py) as template, implement with `ContentService` methods already available, follow admin callback pattern `admin:content:*` for navigation consistency.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.4.1 | FSM States + Router + CallbackQuery handlers | Project framework already using this |
| sqlalchemy | 2.0.25 | AsyncSession for database operations | Existing ORM with ContentPackage model |
| ContentService | Phase 5 | CRUD operations for content packages | Already implemented with all required methods |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| bot.utils.pagination | Existing | `Paginator`, `create_pagination_keyboard` | For listing packages with Next/Prev navigation |
| bot.utils.keyboards | Existing | `create_inline_keyboard`, helper functions | For all inline keyboards |
| bot.states.admin | Existing | `PricingSetupStates` pattern | Template for new FSM states |
| bot.services.message | Existing | Message providers with Lucien's voice | For consistent admin messaging |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FSM wizard with states | Single message with all fields | FSM is better for validation and error recovery |
| Soft delete (is_active) | Hard delete (DELETE from table) | Soft delete preserves purchase history, reactivatable |
| Inline prompt editing | Full wizard for edits | Inline prompt is faster for single-field changes |

**Installation:**
No new packages required - all dependencies already installed.

## Architecture Patterns

### Recommended Project Structure
```
bot/handlers/admin/
├── content.py          # NEW - Content management handlers
├── main.py             # EXISTING - Admin menu router
└── menu.py             # EXISTING - Admin menu handler

bot/states/admin.py     # EXTEND - Add ContentPackageStates

bot/services/message/
├── admin_content.py    # NEW - Content admin message provider
└── __init__.py         # UPDATE - Register AdminContentMessages
```

### Pattern 1: FSM Wizard for Multi-Step Creation
**What:** FSM states collect data step-by-step with validation at each stage
**When to use:** Creating new content packages (name → type → price → description)
**Example:**
```python
# Source: bot/states/admin.py (PricingSetupStates pattern)
class ContentPackageStates(StatesGroup):
    """FSM states for content package creation wizard."""
    waiting_for_name = State()        # Step 1: Package name
    waiting_for_type = State()        # Step 2: Type selection (inline buttons)
    waiting_for_price = State()       # Step 3: Price (optional)
    waiting_for_description = State() # Step 4: Description (optional)

# Handler flow:
# 1. Callback triggers FSM: await state.set_state(ContentPackageStates.waiting_for_name)
# 2. Message handler captures input: @router.message(ContentPackageStates.waiting_for_name)
# 3. Validate input, store in state.data, advance to next state
# 4. After final step, call ContentService.create_package() and clear state
```

### Pattern 2: Callback Navigation Hierarchy
**What:** Unified callback pattern `admin:content:action` for admin content navigation
**When to use:** All admin content management navigation
**Example:**
```python
# Source: bot/handlers/admin/main.py (callback_admin_config pattern)
# Main menu → Content submenu
@admin_router.callback_query(F.data == "admin:content")
async def callback_content_menu(callback: CallbackQuery, session: AsyncSession):
    """Show content management submenu."""
    text, keyboard = container.message.admin.content.content_menu()
    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")

# List packages (paginated)
@admin_router.callback_query(F.data == "admin:content:list")
async def callback_content_list(callback: CallbackQuery, session: AsyncSession):
    """Show first page of content packages."""
    packages = await container.content.list_packages(is_active=None, limit=10, offset=0)
    # Format and paginate...

# Navigate back to main
@admin_router.callback_query(F.data == "admin:main")
async def callback_admin_main(callback: CallbackQuery, session: AsyncSession):
    """Return to admin main menu."""
    # ...
```

### Pattern 3: Pagination with Inline Keyboards
**What:** Use `Paginator` and `create_pagination_keyboard` for large lists
**When to use:** Listing content packages (potentially 100+)
**Example:**
```python
# Source: bot/utils/pagination.py (existing utility)
from bot.utils.pagination import Paginator, create_pagination_keyboard, format_page_header

@admin_router.callback_query(F.data.startswith("admin:content:page:"))
async def callback_content_page(callback: CallbackQuery, session: AsyncSession):
    """Show specific page of content packages."""
    # Extract page number from callback
    page_num = int(callback.data.split(":")[-1])

    # Get all packages (TODO: optimize with DB-level pagination)
    all_packages = await container.content.list_packages(is_active=None)
    paginator = Paginator(items=all_packages, page_size=10)
    page = paginator.get_page(page_num)

    # Format display
    header = format_page_header(page, "Paquetes de Contenido")
    packages_text = format_items_list(page.items, _format_package_summary)

    # Create keyboard with pagination
    keyboard = create_pagination_keyboard(
        page=page,
        callback_pattern="admin:content:page:{page}",
        back_callback="admin:content"
    )

    await callback.message.edit_text(
        text=f"{header}\n\n{packages_text}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
```

### Pattern 4: Inline Prompt Editing
**What:** Prompt admin "Send new name (or /skip to keep current)" for single-field updates
**When to use:** Editing existing package fields (name, price, description)
**Example:**
```python
# From detail view, admin clicks "Edit Name"
@admin_router.callback_query(F.data.startswith("admin:content:edit:"))
async def callback_content_edit_field(callback: CallbackQuery, state: FSMContext):
    """Prompt for field value edit."""
    # Extract package_id and field from callback
    # Example: "admin:content:edit:123:name" → package_id=123, field=name
    parts = callback.data.split(":")
    package_id = int(parts[3])
    field = parts[4]

    await state.update_data(package_id=package_id, field=field)

    text = (
        f"✏️ <b>Editar {field}</b>\n\n"
        f"Envía el nuevo valor (o /skip para mantener actual)."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": f"admin:content:view:{package_id}"}]
        ]),
        parse_mode="HTML"
    )

# Process the edit
@admin_router.message(ContentPackageStates.waiting_for_edit)
async def process_content_edit(message: Message, state: FSMContext, session: AsyncSession):
    """Process field edit and update package."""
    data = await state.get_data()
    package_id = data["package_id"]
    field = data["field"]

    if message.text.startswith("/skip"):
        # Skip edit, return to detail view
        await state.clear()
        # Show detail view...
        return

    # Update using ContentService
    container = ServiceContainer(session, message.bot)
    await container.content.update_package(package_id, **{field: message.text})

    await state.clear()
    # Show updated detail view...
```

### Anti-Patterns to Avoid
- **Hardcoded pagination in DB**: Don't implement DB-level pagination if `Paginator` works - stick with in-memory pagination for simplicity unless dataset grows large (>1000 packages)
- **Type changes after creation**: Don't allow editing `category` or `type` fields - these are locked per CONTEXT.md decisions to preserve data integrity
- **Hard delete**: Don't use `session.delete()` - always use `deactivate_package()` for soft delete
- **Commit in service methods**: Don't call `await session.commit()` in handlers - let SessionContextManager handle it

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pagination | Custom offset/limit logic | `bot.utils.pagination.Paginator` | Handles page math, has_prev/has_next, edge cases |
| Inline keyboards | Manual keyboard construction | `create_inline_keyboard(buttons)` | Consistent format, less error-prone |
| FSM state management | Custom state tracking | `aiogram.fsm.state.State`, `StatesGroup` | Built-in timeout, automatic cleanup |
| Navigation callbacks | String parsing everywhere | Unified callback pattern `admin:content:action` | Easier to route, debug, extend |
| Message formatting | f-strings everywhere | Message providers with Lucien's voice | Consistency across all admin interfaces |

**Key insight:** All problems in this phase have existing solutions in the codebase. Focus on composition over custom implementation.

## Common Pitfalls

### Pitfall 1: FSM State Not Cleared on Cancel
**What goes wrong:** Admin cancels wizard but FSM state remains, blocking other operations
**Why it happens:** Cancel handler forgets `await state.clear()`
**How to avoid:**
```python
@admin_router.callback_query(F.data == "content:create:cancel")
async def callback_content_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel creation wizard and clear state."""
    await state.clear()  # CRITICAL: Always clear FSM state
    # Return to main menu...
    await callback.answer()
```
**Warning signs:** User reports "bot doesn't respond to commands" after canceling wizard

### Pitfall 2: Callback Answer Not Called
**What goes wrong:** Inline button shows loading spinner indefinitely
**Why it happens:** Handler forgets `await callback.answer()` after processing
**How to avoid:** Always call `await callback.answer()` at end of callback handlers
**Warning signs:** Buttons stay "pressed" with spinning icon

### Pitfall 3: Message Edit Without Content Change
**What goes wrong:** Bot crashes with "message is not modified" error
**Why it happens:** `callback.message.edit_text()` called with identical content
**How to avoid:**
```python
try:
    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
except Exception as e:
    if "message is not modified" not in str(e):
        logger.error(f"❌ Error editando mensaje: {e}")
    # else: silently ignore - message already in correct state
```
**Warning signs:** Logs show "message is not modified" errors

### Pitfall 4: Type Validation Missing in Wizard
**What goes wrong:** Admin enters "abc" for price field, wizard crashes
**Why it happens:** FSM message handler doesn't validate input type before storing
**How to avoid:**
```python
@admin_router.message(ContentPackageStates.waiting_for_price)
async def process_content_price(message: Message, state: FSMContext):
    """Process price input with validation."""
    price_text = message.text.strip()

    # Validate: must be numeric
    try:
        price = float(price_text)
        if price < 0:
            raise ValueError("Price cannot be negative")
    except ValueError:
        # Error message and retry
        await message.answer(
            "❌ <b>Precio inválido</b>\n\n"
            "El precio debe ser un número positivo (ej: 9.99).\n\n"
            "Intenta de nuevo:",
            parse_mode="HTML"
        )
        return  # Keep state active for retry

    # Store valid price
    await state.update_data(price=price)
    # Advance to next step...
```
**Warning signs:** Bot crashes when admin enters non-numeric data

### Pitfall 5: Session Commit in Handler
**What goes wrong:** Transaction errors, data inconsistency
**Why it happens:** Handler calls `await session.commit()` manually
**How to avoid:** Never commit in handlers - rely on SessionContextManager in middleware
**Warning signs:** Multiple "Transaction already committed" errors in logs

## Code Examples

Verified patterns from official sources:

### FSM Wizard Initialization
```python
# Source: bot/handlers/admin/pricing.py (lines 97-132)
@admin_router.callback_query(F.data == "pricing:create")
async def callback_pricing_create_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia flujo de creación de tarifa."""
    await state.set_state(PricingSetupStates.waiting_for_name)

    text = (
        "➕ <b>Crear Nueva Tarifa</b>\n\n"
        "Paso 1/3: <b>Nombre de la Tarifa</b>\n\n"
        "Envía el nombre del plan de suscripción.\n\n"
        "<b>Ejemplos:</b>\n"
        "• Plan Mensual\n"
        "• Plan Trimestral\n"
        "• Plan Anual"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "pricing:cancel"}]
        ]),
        parse_mode="HTML"
    )

    await callback.answer()
```

### Soft Delete Pattern
```python
# Source: bot/services/content.py (lines 298-323)
async def deactivate_package(self, package_id: int) -> Optional[ContentPackage]:
    """Desactiva un paquete (soft delete)."""
    package = await self.get_package(package_id)

    if not package:
        logger.warning(f"📦 Paquete no encontrado para desactivar: {package_id}")
        return None

    package.is_active = False
    package.updated_at = datetime.utcnow()

    # NO commit - dejar que el handler gestione la transacción
    logger.info(f"✅ Paquete desactivado: {package_id} - {package.name}")
    return package
```

### Callback Navigation with Hierarchy
```python
# Source: bot/handlers/admin/main.py (lines 60-104)
@admin_router.callback_query(F.data == "admin:main")
async def callback_admin_main(callback: CallbackQuery, session: AsyncSession):
    """Handler del callback para volver al menú principal."""
    container = ServiceContainer(session, callback.bot)
    config_status = await container.config.get_config_status()

    session_history = container.session_history
    text, keyboard = container.message.admin.main.admin_menu_greeting(
        is_configured=config_status["is_configured"],
        missing_items=config_status.get("missing", []),
        user_id=callback.from_user.id,
        session_history=session_history
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            logger.error(f"❌ Error editando mensaje: {e}")

    await callback.answer()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard delete packages | Soft delete (is_active flag) | Phase 5 (ContentPackage model) | Preserves purchase history, allows reactivation |
| Single callback string | Hierarchical callbacks (admin:content:action) | Phase 6 (menu:free:action pattern) | Clearer routing, easier to extend |
| Manual pagination | Paginator utility class | Phase 6 (bot/utils/pagination.py) | Consistent pagination, less code |
| Inline message text | Message providers with Lucien's voice | Phase 2-3 (bot/services/message) | Consistent admin voice across all interfaces |

**Deprecated/outdated:**
- Manual FSM state tracking without StatesGroup: Use `StatesGroup` pattern for all wizards
- Direct keyboard construction: Use `create_inline_keyboard()` helper
- String formatting for currency: Use `bot.utils.formatters.format_currency()`

## Open Questions

1. **DB-level pagination vs in-memory pagination**
   - What we know: Current pagination is in-memory (fetches all, then slices)
   - What's unclear: When dataset grows large (>1000 packages), this becomes inefficient
   - Recommendation: Start with in-memory (simpler), optimize to DB-level pagination in Phase 8+ if needed

2. **Message provider for content admin**
   - What we know: Other admin areas have message providers (AdminMainMessages, AdminVIPMessages)
   - What's unclear: Should AdminContentMessages be in separate file or integrated into existing providers
   - Recommendation: Create separate `admin_content.py` provider following existing pattern (AdminMainMessages structure)

3. **Search functionality for content**
   - What we know: ContentService has `search_packages()` method
   - What's unclear: UI pattern for search (separate command? filter in list view?)
   - Recommendation: Add search button in content menu that prompts for search term, shows results with pagination

## Sources

### Primary (HIGH confidence)
- [Finite State Machine - aiogram 3.24.0 documentation](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html) - FSM states and transitions
- [Scenes Wizard - aiogram 3.24.0 documentation](https://docs.aiogram.dev/en/v3.24.0/dispatcher/finite_state_machine/scene.html) - Wizard patterns
- [Callback Data Factory & Filter](https://docs.aiogram.dev/en/latest/dispatcher/filters/callback_data.html) - Callback data patterns
- bot/services/content.py - ContentService implementation (416 lines)
- bot/states/admin.py - Existing FSM state patterns (PricingSetupStates)
- bot/handlers/admin/pricing.py - FSM wizard example (150+ lines)
- bot/utils/pagination.py - Pagination utilities (396 lines)

### Secondary (MEDIUM confidence)
- [Simple CallbackData Factory Example](https://gist.github.com/Birdi7/d5249ae88015a1384b7200dcb51e85ce) - CallbackData pattern usage
- bot/handlers/admin/main.py - Admin menu callback patterns (186 lines)
- bot/services/message/admin_main.py - Admin message provider pattern (256 lines)
- [Exploring Finite State Machine in Aiogram 3](https://medium.com/sp-lutsk/exploring-finite-state-machine-in-aiogram-3-a-powerful-tool-for-telegram-bot-development-9cd2d19cfae9) - FSM concepts

### Tertiary (LOW confidence)
- [Problems with pagination/callbacks in aiogram3?](https://stackoverflow.com/questions/77256562/problems-with-pagination-callbacks-in-aiogram3) - Pagination issues (verified with official docs)
- [How to use CallbackQuery properly? #1169](https://github.com/aiogram/aiogram/discussions/1169) - Best practices discussion (April 2023)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries/frameworks already in use in project
- Architecture: HIGH - Existing patterns (FSM wizards, callbacks, pagination) verified in codebase
- Pitfalls: HIGH - Common issues documented in official docs and existing code

**Research date:** 2026-01-25
**Valid until:** 30 days (until 2026-02-24) - Aiogram 3.x is stable, patterns won't change significantly
