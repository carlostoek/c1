# Phase 7: Admin Menu with Content Management - Context

**Gathered:** 2026-01-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Admin interface for managing content packages with full CRUD operations. Admin can list, create, edit, and deactivate packages. The interface integrates with existing menu system using unified callback navigation (menu:main, menu:vip, menu:free).

Content packages are categorized by type (VIP_PREMIUM, VIP_CONTENT, FREE_CONTENT) with optional pricing. Deactivation uses soft delete (is_active flag) — existing purchases remain valid, package only hidden from new buyers.

</domain>

<decisions>
## Implementation Decisions

### Content Listing
- **Hybrid summary layout**: Brief list first with tap-to-view-details. Each item shows: Name, Type, Price, Active status.
- **Sort order**: Newest first (most recently created at top)
- **Active/Inactive display**: All together in one unified list with visual indicators (✅ Active / 🚫 Inactive)
- **Pagination**: Message navigation with Next/Prev buttons. Shows current position (e.g., "3/12").
- **List entry**: Admin opens content list, sees summary view, taps package to view details.

### Creation Wizard
- **Fields collected (in order)**: Name (required) → Type (required) → Price (optional) → Description (optional). Core fields only for quick creation.
- **Type selection**: Inline buttons with three options: [VIP Premium] [VIP Content] [Free Content]. Visual and quick selection.
- **Cancel behavior**: Cancel button always visible on each wizard step. FSM state cleared, no partial data saved.
- **Completion flow**: After successful creation, offer action buttons: [View List] [Create Another] [Main Menu].

### Edit Workflow
- **Edit initiation**: From detail view. Admin taps package to see details, then [Edit] button available there.
- **Edit method**: Inline prompt. One field at a time: "Send new name (or /skip to keep current)".
- **Editable fields**: Name, Price, Description can be changed. **Type is locked after creation** (preserves data integrity).
- **Post-edit behavior**: Return to detail view showing updated package. Admin can continue editing or go back to list.

### Deactivation Flow
- **Deactivate location**: Detail view only. [Deactivate] button appears when viewing package details. Intentional access prevents accidental deactivation.
- **Confirmation**: Simple confirm dialog: "Deactivate [Package Name]? [Yes] [No]".
- **Reactivation**: Yes, inactive packages show [Reactivate] button in detail view. Symmetric to Deactivate behavior.
- **Existing purchases**: Users keep access to already-purchased packages. Deactivation only hides from new buyers.

### Claude's Discretion
- Exact button labels and Lucien's Spanish phrasing for admin messages
- FSM state names and structure for the creation wizard
- Error handling for invalid inputs during wizard (e.g., non-numeric price)
- Detail view layout and information density

</decisions>

<specifics>
## Specific Ideas

- Hybrid summary means: brief list first (one message with multiple packages), tap any package to see its details
- Type locked after creation = prevents accidentally changing package type which could affect user access logic
- Soft delete behavior (is_active flag) already exists in ContentPackage model from Phase 5
- Inline prompt editing = faster than full wizard for single-field changes

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-admin-menu-content-management*
*Context gathered: 2026-01-25*
