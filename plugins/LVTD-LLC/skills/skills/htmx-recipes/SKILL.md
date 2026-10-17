---
name: htmx-recipes
description: Implement common htmx interaction recipes in server-rendered web apps. Use when building lazy loading, boosted links/forms, active search, inline validation, delete buttons, CSS transitions, form reset, optimistic updates, pagination, infinite scroll, toggled selection, polling, custom dialogs, request headers, click-to-edit, or HTML/JSON endpoint splits.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: htmx Recipes
  category: Frontend
  tags: htmx,frontend,server-driven-ui,ui-patterns,html
---

# htmx Recipes

Use this skill when the feature is a recognizable htmx interaction pattern. Start from the recipe shape, then adapt it to the framework's routing, forms, templates, and tests.

## Recipe Selection

| Need | Pattern |
| --- | --- |
| Enhance normal links/forms | `hx-boost` with full-page fallback |
| Load content on reveal or page load | lazy loading with `hx-get` and a non-chatty trigger |
| Validate an input or form section | targeted validation request with debounce |
| Remove an item | mutation endpoint plus target removal or refreshed list |
| Animate an inserted/removed fragment | CSS transitions coordinated with swap timing/classes |
| Clear a successful form | return a fresh form fragment or trigger local reset |
| Search as the user types | debounced active search into a results target |
| Show success before server confirms | optimistic update with explicit rollback/reconcile plan |
| Page through results | links/buttons that replace the list and pagination controls |
| Append more results | infinite scroll sentinel that appends and replaces itself |
| Toggle selected state | server-owned selection for durable state, local state for transient UI |
| Poll for changing state | bounded polling with a stop condition |
| Open custom dialogs | server-rendered modal body plus events for close/focus |
| Add request headers | one global hook for cross-cutting headers |
| Click to edit | display fragment -> edit form fragment -> display fragment |
| Serve both HTML and JSON | separate endpoints or explicit content negotiation |

## General Workflow

1. Build the plain server-rendered version first.
2. Identify the smallest component whose HTML changes.
3. Add htmx attributes to the existing link, form, button, or sentinel.
4. Return partials that match stable targets.
5. Add loading, disabled, empty, and error states.
6. Add accessibility checks for focus, keyboard, labels, and announcements.
7. Test the fragment response and the fallback path.

## Boosting

- Use `hx-boost` when links/forms already work without htmx.
- Confirm boosted forms still include CSRF and validation behavior.
- Avoid boosting pages with large script-driven lifecycle assumptions.
- Use real URLs because boosted navigation still represents navigation.

## Lazy Loading

- Use lazy loading for expensive panels, secondary data, or below-the-fold content.
- Show a stable placeholder with the same dimensions as the loaded content.
- Avoid lazy loading critical content that affects initial accessibility or SEO.
- Cache server work when repeated reveals would otherwise be expensive.

## Validation

- Keep server validation authoritative.
- Use debounce for per-field requests.
- Target the field wrapper or form section that contains the error message.
- Return normal form markup with errors; avoid a JSON validation side channel.
- Ensure full submit performs the same validation.

## Delete And Reset

- Require a mutation method for destructive actions.
- Use `hx-confirm` for simple confirmations and a custom dialog only when design demands it.
- For delete, either remove the item target or return a refreshed list when counts/order/filtering change.
- For reset, prefer returning a fresh form fragment after success so server defaults are preserved.

## Search, Pagination, And Infinite Scroll

- Put query state in the URL when users should be able to share or refresh it.
- Debounce active search and cancel stale work where the framework supports it.
- Replace the result list for search/filter/sort changes.
- Append for infinite scroll only when ordering is stable.
- Include a fresh sentinel or "next" control in the appended response until there are no more pages.

## Optimistic Updates

Use optimistic UI only when the failure mode is acceptable and reversible.

- Mark optimistic elements so they can be reconciled with the server response.
- Disable repeat actions while a request is in flight.
- Return the canonical server-rendered component after success.
- Show a visible rollback/error state after failure.

## Polling

- Use polling for short-lived background state, not for every realtime problem.
- Choose a reasonable interval and stop when the work is done.
- Return a small fragment, not an entire page.
- Escalate to `htmx-realtime` when updates are frequent, multi-client, or event-driven.

## Dialogs And Click-To-Edit

- Render modal/dialog contents on the server when they include server-owned data.
- Keep the dialog shell stable if local focus/escape behavior owns it.
- Use events to close the dialog after successful save.
- For click-to-edit, keep display and edit fragments symmetrical and test save/cancel/error paths.

## Avoid

- Do not attach immediate `keyup` or `input` triggers without debounce.
- Do not mix optimistic updates with irreversible destructive actions unless rollback is designed.
- Do not use infinite scroll when users need stable pagination, footer access, or precise result position.
- Do not hide server errors by swapping empty fragments.
- Do not copy a recipe blindly without deciding who owns state: server, htmx, Alpine/plain JS, or the browser.
