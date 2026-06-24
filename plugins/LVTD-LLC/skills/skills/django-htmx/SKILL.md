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

## Baseline

Use HTMX to keep Django templates, views, forms, permissions, and server-side validation in charge while adding focused partial-page updates. Prefer plain Django first, then add the smallest HTMX behavior that improves the workflow.

In generated django-saas-starter projects:

- `django-htmx` is installed and `django_htmx.middleware.HtmxMiddleware` adds `request.htmx`.
- `htmx.min.js` is copied from npm to `frontend/static/vendors/js/` and loaded by `frontend/templates/base_app.html` and `frontend/templates/base_landing.html`.
- The base templates already add `X-CSRFToken` during `htmx:configRequest` and set `window.htmx.config.historyRestoreAsHxRequest = false`. Do not duplicate this setup in feature templates.
- Use Alpine.js only for browser-local state such as menus, modals, disclosure state, and lightweight transitions. If Alpine behavior grows beyond coordination with an HTMX swap, use the separate Alpine skill when present.

## Implementation Workflow

1. Find the server state owner: model, queryset, form, service, permission, or session value.
2. Choose the smallest URL boundary:
   - Reuse an existing view with `request.htmx` branching when the full page and partial share the same query and permissions.
   - Create a dedicated endpoint when the interaction has a narrow component contract or different mutation rules.
3. Put reusable fragments in partial templates, commonly `frontend/templates/<app>/partials/...` or the local app template folder.
4. Render the full page by including the same partial that the HTMX response returns.
5. Preserve non-HTMX fallback behavior for links and forms whenever practical.
6. Add tests for both normal and HTMX requests when the view branches on `request.htmx`.

## View Patterns

Branch on `request.htmx` only after the same auth, permission, and data-loading path has run:

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django_htmx.http import trigger_client_event
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET", "POST"])
def profile_panel(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        if not request.htmx:
            return redirect("settings")
        form = ProfileForm(instance=profile)
        response = render(request, "core/partials/profile_panel.html", {"form": form})
        return trigger_client_event(response, "profile:saved", after="swap")

    template_name = (
        "core/partials/profile_panel.html"
        if request.htmx
        else "pages/user-settings.html"
    )
    return render(request, template_name, {"form": form})
```

Use `@vary_on_headers("HX-Request")` on cacheable views that return different full-page and partial content for the same URL.

For mutations that should redirect a normal browser but update the current page for HTMX, return separate responses:

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django_htmx.http import trigger_client_event
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET", "POST"])
def create_note(request):
    form = NoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        note = form.save(commit=False)
        note.user = request.user
        note.save()
        if request.htmx:
            response = render(request, "core/partials/note.html", {"note": note})
            return trigger_client_event(response, "note:created", {"id": note.pk})
        return redirect("notes")

    template_name = "core/partials/note_form.html" if request.htmx else "core/note_form.html"
    return render(request, template_name, {"form": form})
```

Prefer `django_htmx.http` helpers over hand-writing HTMX headers:

- `HttpResponseClientRedirect` for `HX-Redirect`.
- `HttpResponseClientRefresh` for `HX-Refresh`.
- `HttpResponseLocation` for `HX-Location`.
- `HttpResponseStopPolling` or status `286` for stopping polling.
- `push_url()`, `replace_url()`, `retarget()`, `reswap()`, `reselect()`, and `trigger_client_event()` for response header modifiers.

## Template Patterns

Keep forms valid without JavaScript, then add HTMX attributes:

```django
<form
  method="post"
  action="{% url 'profile_panel' %}"
  hx-post="{% url 'profile_panel' %}"
  hx-target="#profile-panel"
  hx-swap="outerHTML"
>
  {% csrf_token %}
  {% include "core/partials/profile_fields.html" with form=form %}
  <button type="submit">Save</button>
</form>
```

Use stable targets:

- Use `hx-target="#component-id"` with IDs that appear exactly once.
- Use `hx-swap="outerHTML"` when replacing the target element itself.
- Ensure partials returned to an `outerHTML` swap include the target root element with the same ID.
- Use `hx-swap="innerHTML"` when replacing only the target contents.
- Use `hx-select` or `reselect()` when the server returns a larger HTML response but only one fragment should be swapped.
- Use `hx-indicator` for visible pending states and `hx-disabled-elt` for controls that must not be clicked twice.
- Use `hx-confirm` for simple confirmation. Use an Alpine-controlled modal only when the confirmation has real UI complexity.

Use out-of-band swaps for shared chrome, messages, counters, and badges that are outside the main target:

```django
<div id="messages" hx-swap-oob="true">
  {% include "components/messages.html" with messages=messages %}
</div>
```

For lists, return the row or item fragment after create/update/delete instead of rebuilding a full page unless the queryset ordering, filters, totals, or pagination also change.

## Forms And Validation

- Keep Django forms as the validation source of truth.
- Include `{% csrf_token %}` in forms even though the base HTMX header is configured. It preserves non-HTMX fallback and standard Django behavior.
- For invalid HTMX form submissions, return a rendered bound form with normal status `200` unless the project has explicit `htmx:beforeSwap` or response-target handling for `4xx` and `422` responses.
- For successful create/update, either return the updated component or return an empty `HttpResponse(status=204)` plus `HX-Trigger` when another element should refresh.
- For destructive actions, require POST unless the project has a deliberate method override pattern for `DELETE`. Django does not parse form bodies for `PUT`, `PATCH`, or `DELETE` the way it does for POST.

## Events And Alpine Coordination

Use HTMX events to connect server results to local browser state:

```python
response = render(request, "core/partials/dialog_body.html", context)
return trigger_client_event(response, "dialog:saved", after="swap")
```

```html
<div
  x-data="{ open: true }"
  @dialog:saved.window="open = false"
>
  <div x-show="open" id="dialog-body">
    ...
  </div>
</div>
```

Keep the ownership line clear:

- HTMX owns server trips, fresh HTML, history updates, and cross-component server facts.
- Alpine owns local-only state, keyboard/menu behavior, temporary UI state, and transitions.
- Do not mirror server truth into Alpine stores unless there is a clear reason and synchronization plan.
- After swapping content that contains Alpine components, rely on the loaded Alpine build to initialize new markup. Avoid manually calling Alpine lifecycle APIs unless a bug proves it is necessary.

## History, Navigation, And Boosting

- Use `hx-push-url="true"` only when the new state deserves a real browser URL.
- Ensure every pushed URL can render a full page on direct load and refresh.
- Use `push_url()` or `replace_url()` when the server decides which URL should appear after a swap.
- Keep `historyRestoreAsHxRequest = false` so htmx history-cache misses are sent as normal full-page requests rather than HX requests.
- Use `hx-boost` sparingly. Confirm forms still send CSRF tokens and links still render useful full pages.

## Security Rules

- Let Django autoescape user content. Avoid `safe`, `mark_safe`, and raw user-provided HTML.
- If trusted product requirements allow sanitized rich HTML, strip or whitelist attributes so injected `hx-`, `data-hx-`, `hx-on`, `hx-vals`, and script-bearing content cannot create requests or execute code.
- Do not put secrets, private object IDs, or authorization decisions in HTMX attributes. Enforce permissions in the view.
- Avoid `js:` prefixes in `hx-headers` and `hx-vals`. Prefer plain JSON attributes or server-rendered hidden inputs.
- Keep HTMX requests same-origin unless there is a deliberate CORS and CSRF design.
- Use `hx-history="false"` on sensitive pages or containers that should not be stored in the browser history cache.

## Testing Checklist

- Test the normal browser path and the HTMX path.
- Send `HTTP_HX_REQUEST="true"` in Django tests for HTMX responses.
- Assert the partial response contains the expected fragment and omits full-page chrome when appropriate.
- Assert redirects, refreshes, retargeting, triggers, and status codes through response headers.
- Assert invalid forms re-render errors into the intended target.
- Add `@vary_on_headers("HX-Request")` coverage when cache headers are involved.

Example:

```python
def test_profile_panel_htmx_renders_partial(client, user):
    client.force_login(user)

    response = client.get("/settings/profile/", HTTP_HX_REQUEST="true")
    content = response.content.decode("utf-8").lower()

    assert response.status_code == 200
    assert b'id="profile-panel"' in response.content
    assert "<html" not in content
```

## Avoid

- Do not return JSON for UI updates unless a non-HTMX API truly needs JSON.
- Do not add React, Vue, or a client router for ordinary partial updates.
- Do not place business logic in templates or browser event handlers.
- Do not create one generic "htmx endpoint" that switches behavior based on arbitrary request parameters. Use explicit URLs and views.
- Do not attach `hx-trigger="keyup"` or polling without debounce, throttle, or a clear stop condition.
- Do not use HTMX to bypass Django's normal authentication, authorization, CSRF, form, or message patterns.

## Reference Docs

- HTMX docs: https://htmx.org/docs/
- HTMX repository: https://github.com/bigskysoftware/htmx
- django-htmx middleware: https://django-htmx.readthedocs.io/en/latest/middleware.html
- django-htmx HTTP helpers: https://django-htmx.readthedocs.io/en/latest/http.html
