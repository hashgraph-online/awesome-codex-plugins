---
name: htmx-foundations
description: Plan and bootstrap server-driven web applications with htmx. Use when choosing htmx versus an SPA framework, setting up htmx in a server-rendered app, designing the first CRUD workflow, explaining the htmx mental model, or deciding how much JavaScript a server-driven feature needs.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: htmx Foundations
  category: Frontend
  tags: htmx,server-driven-ui,frontend,web-development,architecture
---

# htmx Foundations

Use this skill before implementation details get scattered across endpoints, templates, and browser scripts. The goal is to keep the server in charge of durable state while htmx adds targeted interactivity through HTML attributes.

## Core Model

- The server owns persistence, authorization, validation, and rendered HTML.
- The browser sends normal HTTP requests from annotated HTML elements.
- Endpoints return HTML fragments when updating part of a page and full pages when supporting direct navigation.
- htmx swaps response HTML into a selected target instead of expecting JSON plus client-side rendering.
- Add browser-side JavaScript only for local state, specialized widgets, or imperative integration points.

## When htmx Fits

Use htmx when the workflow is mostly:

- Forms, CRUD, search, filtering, pagination, inline editing, modals, dashboards, or admin UI.
- Server-authoritative data with existing auth, permissions, and validation.
- HTML-first pages where direct load, refresh, and non-JavaScript fallback matter.
- Small interactive islands rather than a full client-side application shell.

Consider a richer client app when the product needs:

- Offline-first behavior, heavy canvas/WebGL interaction, complex local document editing, or deep client-side routing.
- Large amounts of optimistic state that must survive many server round trips before reconciliation.

## Setup Checklist

1. Load htmx once in the base layout, preferably from a vendored static asset or a CDN with integrity protection.
2. Configure cross-cutting request headers once, such as CSRF headers in frameworks that need them.
3. Keep URLs meaningful. Every pushed or boosted URL should render a full page on direct load.
4. Create reusable server-rendered partials for fragments that htmx swaps.
5. Render the initial full page by including the same partials that htmx endpoints return.
6. Add tests for both the full-page path and the htmx partial path when they differ.

## Attribute Mental Model

| Need | Common attributes |
| --- | --- |
| Make a request | `hx-get`, `hx-post`, `hx-put`, `hx-patch`, `hx-delete` |
| Decide when it fires | `hx-trigger` |
| Choose what changes | `hx-target`, `hx-select` |
| Choose how it changes | `hx-swap`, `hx-swap-oob`, `hx-select-oob` |
| Include extra data | `hx-include`, `hx-vals` |
| Improve UX during requests | `hx-indicator`, `hx-disabled-elt`, `hx-confirm` |
| Intercept events inline | `hx-on` |
| Extend behavior | `hx-ext` |

Start with request, trigger, target, and swap. Add the rest only when the interaction asks for it.

## First Feature Workflow

1. Identify the durable server state and its owner: model, query, form, session, or service.
2. Design the full-page route first so refresh and direct navigation work.
3. Extract the area that changes into a partial template.
4. Add the smallest htmx attributes needed to request and swap that partial.
5. Return validation errors as HTML in the same target that contains the form.
6. Add loading, disabled, empty, and error states after the basic path works.
7. Verify keyboard, focus, and non-JavaScript fallback where the interaction replaces a normal form or link.

## CRUD Shape

- List pages usually own filters, search, sort order, pagination, and item containers.
- Create actions often return the new row/card, the refreshed list, or `204` plus an event that causes another component to refresh.
- Update actions should return the changed component or a validation form.
- Delete actions can return an empty response for the removed target, or an out-of-band fragment that updates counters/messages.
- Inline edit works best when display and edit modes are separate fragments for the same resource.

## Stack Selection

Choose server tooling based on boring operational fit, not htmx novelty:

- Can it render partial templates cleanly?
- Does it expose request headers and response headers easily?
- Does it have mature form validation and CSRF support?
- Can tests exercise both normal and htmx requests?
- Can static assets be pinned, copied, or bundled predictably?

## Avoid

- Do not introduce a client router for ordinary partial updates.
- Do not return JSON for UI fragments unless a non-htmx client also needs the API.
- Do not hide authorization or validation decisions in HTML attributes.
- Do not create generic catch-all htmx endpoints that branch on arbitrary parameters.
- Do not add htmx before a plain server-rendered version of the workflow is clear.

## Related Skills

- Use `htmx-endpoint-design` for request/response contracts, swaps, out-of-band updates, and events.
- Use `htmx-recipes` for common interaction patterns.
- Use `htmx-security` before accepting user HTML, adding CDN assets, or tightening CSP.
- Use `htmx-interactivity` for coordinating Alpine.js, `_hyperscript`, or plain JavaScript with htmx swaps.
- Use `htmx-js-api` for programmatic requests, dynamic markup processing, and event wiring.
- Use `htmx-realtime` for polling, SSE, and WebSocket transport decisions.
