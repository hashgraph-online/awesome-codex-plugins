# Python: Django, Flask, FastAPI

## Entry points
- Django: `urls.py` (`path`, `re_path`, `include`), class-based views (`View`, DRF `ViewSet`/`APIView`, routers register viewsets), admin, signals, Celery tasks (`@shared_task`), management commands, middleware.
- Flask: `@app.route`, `@bp.route`, blueprints registered with `url_prefix`, `app.add_url_rule`, CLI commands, `before_request`.
- FastAPI: `@app.get/post/...`, `APIRouter` with `include_router(prefix=, dependencies=[...])`, `WebSocket` routes, `BackgroundTasks`.
- Enumerate:
  - `grep -rnE "path\(|re_path\(|url\(" --include=urls.py`
  - `grep -rnE "@(app|bp|\w+)\.route|add_url_rule"`
  - `grep -rnE "@(app|router)\.(get|post|put|patch|delete)"`, `grep -rn "include_router"`
  - `grep -rn "csrf_exempt"` and `grep -rn "AllowAny"`

## Where auth and authorization live
- Django: `LoginRequiredMixin`/`@login_required`, `@permission_required`, DRF `permission_classes` (per view) and `DEFAULT_PERMISSION_CLASSES` in settings (default is `AllowAny` if unset). `has_object_permission` runs only when `get_object()`/`check_object_permissions` is called; custom `get_queryset` must scope by user. Mixin order matters: `LoginRequiredMixin` must come first in the MRO. Overriding `dispatch`/`get` can skip checks.
- Admin and `@staff_member_required` guard views, not model data reachable elsewhere.
- Flask: `@app.route` must be the OUTERMOST decorator; a guard placed above it decorates a function that was already registered, so it never runs. `before_request` guards need an explicit exemption list; check blueprint scope.
- FastAPI: `Depends(get_current_user)` in the function signature or in router `dependencies=`; verify the dependency raises (not just returns None) and that it is on THIS route (router-level dependencies do not apply to routes on another router or to mounted sub-apps). Authorization of the object (owner/tenant) is separate from authentication.
- Verify `csrf_exempt` usage and `CsrfViewMiddleware` presence in `MIDDLEWARE`; DRF `SessionAuthentication` enforces CSRF, `TokenAuthentication` does not need it.

## Data access
| Safe | Unsafe |
| --- | --- |
| ORM filters `Model.objects.filter(owner=request.user)`, `.raw(sql, [params])`, `cursor.execute(sql, params)`, SQLAlchemy expression API / `text(...).bindparams()` | `.raw(f"..")`, `.extra(where/select)` with formatted strings, `RawSQL`, `cursor.execute(f"...")`, `text(f"...")`, `order_by(user_value)` from user input unrestricted (Django `order_by` can traverse relations, e.g. `user__password`: allowlist) |
| Pydantic/DRF serializers with explicit fields | `ModelSerializer` with `fields='__all__'` or `exclude=[...]` on writable models; `Model(**request.json)`; `update(**request.data)` |
See `classes/sql-nosql.md`, `classes/access-control.md`.

## Rendering and output
- Django templates and Jinja2 (Flask) autoescape HTML templates by default; hatches: `|safe`, `mark_safe`, `Markup`, `{% autoescape off %}`, `render_template_string` with user data in the template string (template injection), Jinja environments created manually (`Environment()` has autoescape off unless set).
- DRF serializers: `fields='__all__'` exposes new columns when the model changes; check read-only fields for privileged attributes (`is_staff`, `role`).
- FastAPI `response_model` filters output fields; without it, returned ORM/dict objects serialize everything.
- `JsonResponse(safe=False)` etc. are fine; raw `HttpResponse(user_html)` is not escaped.

## Framework-specific pitfalls
- Django `DEBUG=True`, empty `ALLOWED_HOSTS` handling, `SECRET_KEY` committed (signs sessions/cookies; pickle serializer historically made this code execution: check `SESSION_SERIALIZER`).
- `redirect(request.GET['next'])` without `url_has_allowed_host_and_scheme`.
- File serving: `FileResponse(open(user_path))`, `send_file(user_path)` vs `send_from_directory`; `MEDIA_ROOT` served as static; upload name used raw.
- FastAPI: sync endpoint calling blocking code is not a security issue; body models allow extra fields unless `extra='forbid'`, so mass assignment follows when the model is later splatted into the ORM.
- `yaml.load`, `pickle`, `eval` in utility modules (see `classes/deserialization.md`).
- Celery tasks: arguments serialized as JSON by default; pickle serializer enabled in config is a risk; tasks run later with stored ids (re-authorize).
- Flask `app.secret_key` default or weak: forged sessions; `SESSION_COOKIE_*` flags.
