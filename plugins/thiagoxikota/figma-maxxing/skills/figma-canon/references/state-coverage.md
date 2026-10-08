# State coverage

Load before creating a new screen and during handoff prep. Required states per screen class (Default / Loading / Empty / Error / Success / Edge / Permission-denied / Offline), with a decision table by screen type: list, detail, form, dashboard, settings, onboarding, search, modal, empty workspace.

## The rule

Happy path is NOT enough. Every screen handles multiple states by user-facing class. Skipping a required state = handoff gate fail.

## Decision table by screen class

Legend:

- `Required` = the state must be designed for that screen class; the text after the colon says which form it takes.
- `n/a` = the state does not apply.
- A value in parentheses is not required for every screen of the class. `(rare)` = seldom needed: design it only when the screen has that case. `(toast)` = when present, the state is a toast. `(if multi-user)` = only when the workspace has several users.
- `if role-gated` = required only when access to the screen depends on the user's role. `per-section role` = the same, checked per settings section.
- Plain text in the Edge column names the edge cases to design for that class.
- Offline has no column: the table does not mark it per screen class. Apply the Offline section below wherever the project map requires it.

| Screen class | Default | Loading | Empty | Error | Success | Edge | Permission |
|---|---|---|---|---|---|---|---|
| List view | Required | Required: skeleton | Required | Required | (toast) | long-text trunc + pagination | if role-gated |
| Detail view | Required | Required: skeleton | (rare) | Required | (toast) | long content + many sections | if role-gated |
| Form | Required | Required: submit spinner | (rare) | Required: inline + form-level | Required: confirmation | per-field validation | (rare) |
| Dashboard | Required | Required: widget skeletons | Required: all-zero | Required: per-widget | (toast) | data outliers + missing source | if role-gated |
| Settings | Required | Required: section spinners | (rare) | Required: inline | Required: toast | n/a | per-section role |
| Onboarding flow | Required: step | Required: between-step | n/a | Required: retry | Required: completion | back-nav + skip | n/a |
| Search results | Required | Required: skeleton | Required: no-results | Required: search-failed | n/a | many-results pagination | n/a |
| Modal / dialog | Required | (rare) | n/a | Required: inline | Required: closes on success | confirmation-required actions | (rare) |
| Empty workspace | Required | n/a | Required: primary | n/a | n/a | n/a | (if multi-user) |

## What each state needs

### Default

- Standard rendering with realistic data
- All interactive elements at rest
- Primary CTA visible above the fold

### Loading

- Skeleton (preferred for structured content) OR spinner (preferred for single-action waits)
- Same layout as default (the skeleton mimics the real shape)
- Loading state is not empty state: do not confuse "still fetching" with "no data"

### Empty

- Illustration / icon
- Message ("you don't have any X yet")
- Primary CTA to populate (or guidance if the user cannot create)
- Optional: tertiary link to docs/help

### Error

- User-friendly message (NOT a stack trace)
- What went wrong (in plain terms)
- Recovery action: Retry / Go back / Contact support
- Do not dead-end the user

### Success

- Visible feedback (toast, inline banner, confirmation screen)
- Does not auto-disappear before the user notices (min 5s OR manual dismiss)
- Next-action hint where relevant

### Edge

- Long text: truncation pattern with ellipsis + tooltip OR full text on click
- Many items: pagination, infinite scroll, OR virtualized list
- Slow network: graceful degradation
- Stale data: "last updated X ago" indicator

### Permission-denied

- Clear explanation of why the user is blocked
- Path to gain access (request, upgrade, contact admin)
- DO NOT just show empty/error: be explicit

### Offline

- Banner indicating offline mode
- Read-only cached content
- Pending actions queued visibly
- Reconnection feedback when online again

## Anti-patterns

- "Loading..." text instead of a skeleton (low-effort, no shape info)
- Empty state with only "No data" (no CTA, no guidance)
- Error with the stack trace exposed (security + UX fail)
- Success auto-dismissed in <2s (the user missed the confirmation)
- Permission-denied returning to an empty list (the user thinks it is empty when it is blocked)

## Codification

Each project's required states by screen are encoded in:

- The project map: a `figma-map.md` file kept in the project (default `docs/figma-map.md`), or the agent's own memory system if it has one. It holds the project-specific state requirements.
- This canon reference: universal patterns.
- The `figma-slop-check` skill, which checks each screen against this table for its screen class.
- The `figma-handoff-gate` skill, which then checks before ship that every trigger, bypass and error path has its own frame.
