# Django HTMX Testing And Security

## Security Rules

- Let Django autoescape user content. Avoid `safe`, `mark_safe`, and raw
  user-provided HTML.
- If trusted product requirements allow sanitized rich HTML, strip or whitelist
  attributes so injected `hx-`, `data-hx-`, `hx-on`, `hx-vals`, and
  script-bearing content cannot create requests or execute code.
- Do not put secrets, private object IDs, or authorization decisions in HTMX
  attributes. Enforce permissions in the view.
- Avoid `js:` prefixes in `hx-headers` and `hx-vals`. Prefer plain JSON
  attributes or server-rendered hidden inputs.
- Keep HTMX requests same-origin unless there is a deliberate CORS and CSRF
  design.
- Use `hx-history="false"` on sensitive pages or containers that should not be
  stored in the browser history cache.

## Testing Checklist

- Test the normal browser path and the HTMX path.
- Send `HTTP_HX_REQUEST="true"` in Django tests for HTMX responses.
- Assert the partial response contains the expected fragment and omits full-page
  chrome when appropriate.
- Assert redirects, refreshes, retargeting, triggers, and status codes through
  response headers.
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

## Reference Docs

- HTMX docs: https://htmx.org/docs/
- HTMX repository: https://github.com/bigskysoftware/htmx
- django-htmx middleware: https://django-htmx.readthedocs.io/en/latest/middleware.html
- django-htmx HTTP helpers: https://django-htmx.readthedocs.io/en/latest/http.html
