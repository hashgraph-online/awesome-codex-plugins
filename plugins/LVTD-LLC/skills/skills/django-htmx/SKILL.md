---
name: django-htmx
description: Build and review HTMX interactions in Django server-rendered projects, especially generated django-saas-starter apps. Use when adding hx attributes, partial template responses, request.htmx branching, django-htmx response headers, forms, swaps, triggers, redirects, polling, boosted links or forms, or coordinating HTMX with Alpine.js local state.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django HTMX
  category: Django
  tags: django,htmx,server-rendered-ui
---

# Django HTMX

Use HTMX to keep Django templates, views, forms, permissions, and server-side
validation in charge while adding focused partial-page updates. Prefer plain
Django first, then add the smallest HTMX behavior that improves the workflow.

In generated django-saas-starter projects:

- `django-htmx` is installed and `django_htmx.middleware.HtmxMiddleware` adds
  `request.htmx`.
- `htmx.min.js` is copied from npm to `frontend/static/vendors/js/` and loaded
  by `frontend/templates/base_app.html` and `frontend/templates/base_landing.html`.
- The base templates already add `X-CSRFToken` during `htmx:configRequest` and
  set `window.htmx.config.historyRestoreAsHxRequest = false`. Do not duplicate
  this setup in feature templates.
- Use Alpine.js only for browser-local state such as menus, modals, disclosure
  state, and lightweight transitions.

## Framework-Neutral HTMX Skills

Use these skills for deeper htmx guidance, then translate back to Django forms,
views, templates, permissions, and tests:

- `htmx-endpoint-design` for request/response contracts, targets, swaps,
  out-of-band updates, and events.
- `htmx-recipes` for active search, pagination, infinite scroll, polling,
  dialogs, click-to-edit, boosted links, and other common patterns.
- `htmx-security` for XSS, sanitization, CSP, CSRF, and htmx history-cache risk.
- `htmx-realtime` for polling, SSE, and WebSocket tradeoffs.
- `htmx-interactivity` for Alpine.js coordination, event boundaries, and local
  state outside replaceable targets.
- `htmx-js-api` for programmatic requests, `htmx.process`, and event wiring.

## Resource Routing

Load only the files needed for the current task:

| Need | Read |
| --- | --- |
| Django view branching, response helpers, forms, validation | `references/django-view-patterns.md` |
| Template targets, swaps, OOB updates, Alpine events, recipe notes | `references/template-interaction-patterns.md` |
| Security rules, Django tests, response assertions, reference docs | `references/testing-security.md` |

## Implementation Workflow

1. Find the server state owner: model, queryset, form, service, permission, or
   session value.
2. Choose the smallest URL boundary:
   - Reuse an existing view with `request.htmx` branching when the full page and
     partial share the same query and permissions.
   - Create a dedicated endpoint when the interaction has a narrow component
     contract or different mutation rules.
3. Put reusable fragments in partial templates, commonly
   `frontend/templates/<app>/partials/...` or the local app template folder.
4. Render the full page by including the same partial that the HTMX response
   returns.
5. Preserve non-HTMX fallback behavior for links and forms whenever practical.
6. Add tests for both normal and HTMX requests when the view branches on
   `request.htmx`.

## Django Rules

- Branch on `request.htmx` only after the same auth, permission, and data-loading
  path has run.
- Use `@vary_on_headers("HX-Request")` on cacheable views that return different
  full-page and partial content for the same URL.
- Prefer `django_htmx.http` helpers over hand-writing HTMX headers:
  `HttpResponseClientRedirect`, `HttpResponseClientRefresh`,
  `HttpResponseLocation`, `HttpResponseStopPolling`, `push_url()`,
  `replace_url()`, `retarget()`, `reswap()`, `reselect()`, and
  `trigger_client_event()`.
- Keep Django forms as the validation source of truth. Include `{% csrf_token %}`
  in forms even when the base HTMX header is configured.
- For invalid HTMX form submissions, return a rendered bound form with normal
  status `200` unless the project explicitly handles `4xx` or `422` swaps.
- For destructive actions, require POST unless the project has a deliberate
  method override pattern for `DELETE`.
- Keep the ownership line clear: HTMX owns server trips, fresh HTML, history
  updates, and cross-component server facts; Alpine owns local-only state,
  keyboard/menu behavior, temporary UI state, and transitions.
- Use `hx-push-url="true"` only when the new state deserves a real browser URL,
  and ensure the pushed URL can render a full page on direct load and refresh.

## Avoid

- Do not return JSON for UI updates unless a non-HTMX API truly needs JSON.
- Do not add React, Vue, or a client router for ordinary partial updates.
- Do not place business logic in templates or browser event handlers.
- Do not create one generic "htmx endpoint" that switches behavior based on
  arbitrary request parameters. Use explicit URLs and views.
- Do not attach `hx-trigger="keyup"` or polling without debounce, throttle, or a
  clear stop condition.
- Do not use HTMX to bypass Django's normal authentication, authorization, CSRF,
  form, or message patterns.
