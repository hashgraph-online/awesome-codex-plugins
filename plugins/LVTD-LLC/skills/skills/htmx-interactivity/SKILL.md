---
name: htmx-interactivity
description: Coordinate htmx with lightweight browser-side interactivity. Use when adding Alpine.js, _hyperscript, local UI state, custom events, dialogs, transitions, keyboard behavior, or browser-only state around htmx swaps in a server-rendered app.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: htmx Interactivity
  category: Frontend
  tags: htmx,alpinejs,hyperscript,frontend,ui-state
---

# htmx Interactivity

Use this skill when htmx handles server trips but the page still needs local browser behavior. Keep the ownership line explicit so server-rendered HTML and client-side state do not fight each other.

## Ownership Rules

- htmx owns server requests, fragment swaps, history updates, and server-triggered events.
- The server owns durable state, validation, permissions, and canonical HTML.
- Alpine or plain JavaScript owns local state such as menu open/closed, tabs, disclosure state, temporary filters, focus helpers, and small transitions.
- `_hyperscript` is best for short event-driven behaviors attached to markup.
- Do not mirror the same durable state in both server data and a client store unless there is a reconciliation plan.

## Use Alpine When

- A component has local state that changes without a server request.
- You need a dropdown, popover, modal shell, tab set, disclosure, or preview toggle.
- You need to coordinate htmx lifecycle events with UI state.
- The state naturally belongs near the markup and is simple enough to read inline.

Keep persistent Alpine state outside htmx targets that will be replaced. If htmx swaps the element that owns `x-data`, that state resets.

## Use _hyperscript When

- The behavior is a small event script, such as adding a class, waiting, then removing it.
- The script reads like a local interaction, not application business logic.
- The team accepts `_hyperscript` syntax as part of the template layer.

Avoid `_hyperscript` for complex state machines, security-sensitive logic, large data transforms, or behavior that needs substantial tests.

## Event Boundary Pattern

Use events as the bridge between server results and local browser state:

1. The htmx request submits to the server.
2. The server returns HTML and optionally triggers a domain event.
3. Alpine, `_hyperscript`, or plain JavaScript listens for the event.
4. Local UI state updates, such as closing a modal or focusing a saved row.

Prefer domain event names over implementation names:

```html
<section x-data="{ open: true }" @profile-saved.window="open = false">
  <form hx-post="/profile" hx-target="#profile-panel" hx-swap="outerHTML">
    ...
  </form>
</section>
```

## htmx Lifecycle Hooks

Use lifecycle events for cross-cutting behavior:

- `htmx:configRequest` for headers such as CSRF when the framework needs them.
- `htmx:beforeRequest` and `htmx:afterRequest` for instrumentation and loading behavior that attributes cannot express.
- `htmx:beforeSwap` for exceptional status handling.
- `htmx:afterSwap` or `htmx:load` for initializing third-party widgets in swapped content.
- WebSocket extension events only in code that owns realtime behavior.

Prefer htmx attributes such as `hx-indicator` and `hx-disabled-elt` before writing lifecycle JavaScript.

## Swaps And Local State

- Keep long-lived local state outside replaceable htmx targets.
- If a target contains initialized third-party widgets, define how they are destroyed or re-initialized.
- After injecting htmx-enabled markup outside an htmx request, use `htmx.process` from the `htmx-js-api` skill.
- Avoid global listeners that accumulate every time a fragment is swapped.

## Data From The Server

- Prefer HTML attributes or inert JSON script blocks for server-provided data.
- Escape all server-rendered values before they enter JavaScript expressions.
- Use text binding APIs for untrusted display text.
- Avoid embedding secrets, signed tokens, or authorization facts in local state.

## Accessibility

- Use real buttons for local actions.
- Bind `aria-expanded`, `aria-controls`, `aria-selected`, and `aria-hidden` from local state.
- Preserve focus when opening/closing dialogs and after successful htmx swaps.
- Support Escape for dismissible overlays.
- Avoid replacing focused elements without a plan to move focus somewhere sensible.

## CSP And Security

Alpine, `_hyperscript`, inline event attributes, and `hx-on` can all affect Content Security Policy. Use `htmx-security` when adding or tightening CSP, accepting user-authored HTML, or choosing CSP-compatible builds.

## Avoid

- Do not restart Alpine after every htmx swap.
- Do not put durable server truth in a client store just to avoid a small htmx request.
- Do not let local scripts bypass server authorization or validation.
- Do not place broad event handlers in fragments that may be swapped repeatedly.
- Do not use `x-html` or equivalent APIs for untrusted content.
