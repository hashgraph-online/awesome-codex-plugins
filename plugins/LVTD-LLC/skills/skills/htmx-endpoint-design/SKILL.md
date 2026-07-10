---
name: htmx-endpoint-design
description: Design and review htmx endpoint contracts for server-rendered HTML fragments. Use when adding or debugging hx-get, hx-post, hx-put, hx-patch, hx-delete, hx-target, hx-swap, hx-select, out-of-band swaps, HX-Trigger events, partial template responses, redirects, retargeting, or response headers.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: htmx Endpoint Design
  category: Frontend
  tags: htmx,endpoints,html,server-driven-ui,frontend
---

# htmx Endpoint Design

Use this skill when the hard part is the server/browser contract: which element makes the request, which endpoint handles it, what HTML comes back, and where that HTML lands.

## Contract First

Define the endpoint contract before writing attributes:

- **Request source**: the element that sends the request.
- **HTTP method**: `GET` for safe reads; `POST`, `PUT`, `PATCH`, or `DELETE` for mutations when the server/framework supports them.
- **Input data**: normal form fields, included elements, path params, or explicit values.
- **Response shape**: full page, partial fragment, empty response, redirect, or event-only response.
- **Swap target**: the element to replace or update.
- **Follow-up effects**: events, out-of-band fragments, URL changes, focus changes, and messages.

## Endpoint Workflow

1. Run the same auth, permission, and data-loading logic for full-page and htmx requests.
2. Branch late on whether the request is an htmx request.
3. Reuse the same partial in the full-page render and the htmx response.
4. Return a fragment whose root matches the intended `hx-target` when using `outerHTML`.
5. Use response headers or events for cross-component effects instead of coupling unrelated targets.
6. Test the normal request and the htmx request separately.

## Requests

- Prefer normal form encoding so server validation, CSRF, and file limitations are explicit.
- Keep mutation requests same-origin unless the project has a deliberate CORS and CSRF design.
- Use `hx-include` when one control must submit data from a nearby form or filter panel.
- Use `hx-vals` only for small explicit values. Avoid secrets and avoid executable `js:` values; prefer form fields, hidden inputs, or URL parameters instead.
- Debounce or throttle chatty triggers such as `keyup`, `input`, and polling.
- Use real links and forms when possible, then enhance them with htmx attributes.

## Responses

Choose the smallest response that keeps the UI honest:

| Situation | Response |
| --- | --- |
| Replace one component | Return that component fragment |
| Update several unrelated components | Return primary fragment plus `hx-swap-oob` fragments |
| Mutation succeeds and another element should refresh | Return `204` plus an event/header when supported |
| Validation fails | Return the bound form fragment with errors |
| Browser should navigate | Return a normal redirect for non-htmx, and an htmx redirect/location response for htmx |
| Server needs a different target/swap | Use framework helpers or htmx response headers where available |

## Targeting And Swapping

- Use stable IDs for durable targets and keep them unique.
- Use `hx-target="this"` for self-contained components.
- Use `outerHTML` when replacing the target element itself.
- Use `innerHTML` when preserving the target shell and replacing only its contents.
- Use insert swaps such as `beforeend` for appending rows, log entries, or feed items.
- Use `hx-select` when the server returns a larger document but the client should extract one fragment.
- Do not swap a parent that contains long-lived local browser state unless that state is intentionally reset.

## Out-Of-Band Updates

Use out-of-band swaps for shared chrome and secondary facts:

- flash messages
- cart counts
- notification badges
- summary totals
- list counters
- modal shells outside the main target

Keep out-of-band fragments small and predictable. If many out-of-band updates are required for one action, consider returning the larger owner component instead.

## Events

Use events to decouple server results from browser-local behavior:

- Fire a server-triggered event after save/delete when another component should refresh.
- Listen for htmx lifecycle events for instrumentation, custom confirmation, and cleanup.
- Use custom events as boundaries between htmx and Alpine, plain JavaScript, or `_hyperscript`.
- Keep event names domain-specific, such as `invoice:saved` or `filters:changed`.

## Status Codes

- Use `200` for normal fragment replacement, including many invalid form responses.
- Use `204` when no visible fragment should be swapped.
- Use redirects deliberately; do not let htmx silently insert a login page into a small target.
- For polling, use the framework or htmx convention that stops polling when the server says the job is done.

## Testing Checklist

- Assert status code and key response headers.
- Assert the partial contains the intended root element.
- Assert the partial omits full-page chrome when it should.
- Assert invalid forms render errors into the expected target.
- Assert out-of-band fragments are present when secondary UI must change.
- Assert redirects or client events are represented in headers, not only in body text.

## Avoid

- Do not create one endpoint that performs unrelated actions based on arbitrary request parameters.
- Do not let templates become the authorization layer.
- Do not return raw JSON for htmx UI updates unless the same endpoint must serve a real API client.
- Do not use broad selectors that can hit multiple targets by accident.
- Do not mix server-rendered truth with stale client-side copies of the same state.
