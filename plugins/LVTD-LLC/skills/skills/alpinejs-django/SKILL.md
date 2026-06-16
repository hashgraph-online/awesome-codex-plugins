---
name: alpinejs-django
description: Use when adding, changing, or debugging Alpine.js behavior in this Django SaaS Starter project, especially in Django templates that may also use HTMX partial updates.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Alpine.js Django
  category: Django
  tags: alpinejs,django,frontend,htmx
---

# Alpine.js with Django

Use this skill for local browser state in Django-rendered templates: dropdowns,
modals, tabs, disclosures, inline filters, disabled/loading states, small
preview interactions, and client-only toggles. Use Django views/forms/models as
the source of truth for durable state. Use HTMX when the server needs to return
fresh HTML.

## Project setup

- Alpine is installed from npm and copied by `scripts/copy-vendor-assets.mjs`
  to `frontend/static/vendors/js/alpine.min.js`.
- `base_app.html` and `base_landing.html` load HTMX first, Alpine second, and
  `frontend/static/js/app.js` third.
- The loaded Alpine file is the self-starting CDN build. Do not call
  `Alpine.start()` from `frontend/src/js/app.js`.
- Simple Alpine behavior should usually live inline in the Django template with
  `x-data`.
- If a reusable component or store is worth extracting, register it before
  Alpine starts. With the current script order, `frontend/src/js/app.js` runs too
  late for reliable `document.addEventListener("alpine:init", ...)`
  registration unless the script order is changed.
- When reusable Alpine registration is needed, add a dedicated classic script
  such as `frontend/src/js/alpine-components.js`, register components/stores
  inside `document.addEventListener("alpine:init", ...)`, and include the copied
  `frontend/static/js/alpine-components.js` before `vendors/js/alpine.min.js` in
  both base templates. Keep `app.js` after Alpine, keep the self-starting Alpine
  build, and still do not call `Alpine.start()` manually.

## Ownership rules

- Django owns persistence, authorization, validation, redirects, and rendered
  HTML.
- HTMX owns server round trips and DOM swaps.
- Alpine owns ephemeral state already present in the browser.
- Plain modules in `frontend/src/js/` own shared DOM behavior that is not
  naturally scoped to one Alpine component.
- Do not duplicate the same behavior in Alpine and a plain JS module.

## Template patterns

Use a small `x-data` object near the markup it controls:

```html
<div
  x-data="{ open: false }"
  @keydown.escape.window="open = false"
  @click.outside="open = false"
>
  <button
    type="button"
    :aria-expanded="open.toString()"
    @click.stop="open = !open"
  >
    Menu
  </button>

  <div x-cloak x-show="open" x-transition>
    ...
  </div>
</div>
```

Prefer Alpine directives over manual DOM manipulation:

- `x-show` for toggling visibility while keeping the element in the DOM.
- `x-if` on a `<template>` when the element should be created and destroyed.
- `x-model` for client-only input state; Django form submission and validation
  still happen on the server.
- `:class`, `:disabled`, `:aria-expanded`, and `:hidden` for state-derived
  attributes.
- `$watch` for one named state transition; `x-effect` only when the dependency
  set is simple and intentional.
- `$dispatch` for browser events between Alpine components or from Alpine to
  HTMX triggers.

Use `x-cloak` for anything hidden by default. The base templates already include
the required `[x-cloak] { display: none !important; }` CSS.

## Django data

Keep Django interpolation out of complex JavaScript expressions when possible.

For simple values, prefer HTML attributes:

```html
<div
  data-initial-label="{{ object.name }}"
  x-data="{ label: '' }"
  x-init="label = $el.dataset.initialLabel"
>
  <span x-text="label"></span>
</div>
```

For structured values, prefer Django's `json_script` and parse it in `x-init`:

```html
{{ rows|json_script:"rows-data" }}

<div
  x-data="{ rows: [] }"
  x-init="rows = JSON.parse(document.getElementById('rows-data').textContent)"
>
  <template x-for="row in rows" :key="row.id">
    <span x-text="row.name"></span>
  </template>
</div>
```

Avoid `|safe` inside Alpine expressions. If the browser must display text, use
`x-text`. Use `x-html` only for trusted, already-sanitized HTML; most HTML should
be rendered by Django or returned through HTMX.

## Alpine and HTMX

When HTMX swaps a fragment containing `x-data`, Alpine should initialize the new
component automatically. Do not restart Alpine after HTMX swaps.

Keep persistent Alpine state outside HTMX targets that will be replaced:

```html
<section x-data="{ panelOpen: false }">
  <button type="button" @click="panelOpen = !panelOpen">Filters</button>

  <div id="results" hx-get="{% url 'search_results' %}" hx-trigger="change from:#filters">
    ...
  </div>
</section>
```

Use events as the boundary between HTMX responses and Alpine state. From Django,
set an `HX-Trigger` or `HX-Trigger-After-Swap` response header, then listen from
Alpine:

```html
<div x-data="{ open: true }" @profile-saved.window="open = false">
  <form hx-post="{% url 'profile_update' %}" hx-target="#profile-panel" hx-swap="outerHTML">
    ...
  </form>
</div>
```

Listen for HTMX lifecycle events in kebab case from Alpine, such as
`@htmx:after-swap.window`, because HTML attributes are case-insensitive.

If Alpine dispatches an event that HTMX should react to, make the trigger
explicit:

```html
<button type="button" x-data @click="$dispatch('refresh-results')">
  Refresh
</button>

<div hx-get="{% url 'results' %}" hx-trigger="refresh-results from:body">
  ...
</div>
```

## Accessibility

- Keep real buttons as `<button type="button">` unless submitting a form.
- Bind ARIA state from Alpine state, especially `aria-expanded`,
  `aria-controls`, `aria-selected`, and `aria-hidden`.
- Support `@keydown.escape.window` for dismissible overlays.
- Use `@click.outside` for popovers and menus, paired with a visible trigger.
- Preserve focus behavior for modals, menus, and swapped HTMX content. If focus
  trapping is needed, add a focused plain JS module or Alpine plugin deliberately
  instead of hand-rolling a brittle trap in attributes.

## Security and CSP

- Treat all Alpine expressions as JavaScript running in the user's browser.
- Do not put secrets, signed tokens, or privileged data into `x-data`,
  `data-*`, `json_script`, or hidden inputs unless the user is allowed to see
  them.
- If strict Content Security Policy without `unsafe-eval` is required, switch
  deliberately to Alpine's CSP build and retest Alpine expressions. The default
  `alpinejs/dist/cdn.min.js` build is not the CSP build.
- If Alpine code makes `fetch()` requests, include Django CSRF headers or use
  existing HTMX/Django forms instead.

## Validation

- For template-only Alpine changes, run the Django template or view tests that
  cover the page, plus `npm run lint` if JavaScript modules changed.
- For HTMX interactions, test the full page and the partial response path.
- For generated projects, run `npm run build` before relying on static output.
- Manually verify stateful controls in light and dark mode when changing visible
  UI behavior.
