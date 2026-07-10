# Django HTMX View Patterns

Branch on `request.htmx` only after the same auth, permission, and data-loading
path has run.

## Shared Full-Page And Partial View

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

Use `@vary_on_headers("HX-Request")` on cacheable views that return different
full-page and partial content for the same URL.

## Mutation With HTMX Partial And Normal Redirect

For mutations that should redirect a normal browser but update the current page
for HTMX, return separate responses.

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

## Response Helpers

Prefer `django_htmx.http` helpers over hand-writing HTMX headers:

- `HttpResponseClientRedirect` for `HX-Redirect`.
- `HttpResponseClientRefresh` for `HX-Refresh`.
- `HttpResponseLocation` for `HX-Location`.
- `HttpResponseStopPolling` or status `286` for stopping polling.
- `push_url()`, `replace_url()`, `retarget()`, `reswap()`, `reselect()`, and
  `trigger_client_event()` for response header modifiers.

## Forms And Validation

- Keep Django forms as the validation source of truth.
- Include `{% csrf_token %}` in forms even though the base HTMX header is
  configured. It preserves non-HTMX fallback and standard Django behavior.
- For invalid HTMX form submissions, return a rendered bound form with normal
  status `200` unless the project has explicit `htmx:beforeSwap` or
  response-target handling for `4xx` and `422` responses.
- For successful create/update, either return the updated component or return an
  empty `HttpResponse(status=204)` plus `HX-Trigger` when another element should
  refresh.
- For destructive actions, require POST unless the project has a deliberate
  method override pattern for `DELETE`. Django does not parse form bodies for
  `PUT`, `PATCH`, or `DELETE` the way it does for POST.
