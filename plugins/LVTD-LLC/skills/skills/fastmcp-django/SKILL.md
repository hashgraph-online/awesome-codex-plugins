---
name: fastmcp-django
description: Use when adding, changing, deploying, testing, or debugging FastMCP MCP servers in existing Django apps, including ASGI mounting, stdio or sidecar servers, Django ORM access from MCP tools, auth and permissions, Streamable HTTP deployment, and MCP client tests.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: FastMCP Django
  category: Django
  tags: fastmcp,django,mcp,asgi
---

# FastMCP with Django

Use this when exposing Django application capabilities to agents through MCP.
Keep Django as the source of truth for auth, permissions, validation, models,
transactions, and business rules. Use FastMCP as the protocol layer around
small, typed capabilities.

## Tool Choice

- Prefer the standalone `fastmcp` package (`from fastmcp import FastMCP`) for
  new Python MCP work in Django. It is the actively maintained FastMCP project
  and includes HTTP transport, clients, auth helpers, CLI tooling, testing
  utilities, server composition, and OpenAPI/FastAPI conversion features.
- Use the official MCP Python SDK (`from mcp.server.fastmcp import FastMCP`)
  when the project has already standardized on it, when you need lower-level
  protocol control, or when a host explicitly requires SDK behavior.
- Consider `django-mcp-server` only when the project needs a Django-native
  package that works inside WSGI or declaratively exposes models/DRF APIs. Audit
  its security model and generated tool contracts before exposing private data.
- If the app already has a deliberate public OpenAPI surface, generating or
  proxying tools from that API can be useful for a first pass. For production
  agents, prefer hand-curated tools with purpose-built names, input schemas,
  permission checks, and bounded outputs.

FastMCP docs track the project's `main` branch, so re-check the current docs
when relying on recently added features or version badges.

## Implementation Workflow

1. Read the existing Django entrypoints first: `manage.py`, `settings.py`,
   `asgi.py`, `wsgi.py`, URL routing, auth middleware, DRF/Ninja APIs, Celery or
   Django Q tasks, and deployment files.
2. Choose the transport boundary:
   - Use stdio for a local desktop/editor MCP server that runs beside the app.
   - Use a separate FastMCP HTTP sidecar when the Django deployment is WSGI-only
     or when MCP should scale independently.
   - Mount FastMCP into the Django ASGI process when the app already runs under
     ASGI and sharing the same domain/process is intentional.
3. Put MCP server registration in a small module such as `apps/core/mcp.py` or
   `project/mcp.py`. Keep tool bodies thin and call existing services,
   selectors, forms, serializers, policies, or domain functions.
4. Make every exposed capability explicit. Avoid generic SQL, generic model
   browsing, arbitrary imports, file path access, or "admin" tools unless the
   project has a clear allowlist and authorization plan.
5. Add tests through `fastmcp.Client` before wiring the transport. Most behavior
   should be tested in-memory without a running web server.

## Stdio Server Pattern

For local agent clients, create a standalone script that initializes Django
before importing models or tool modules.

```python
# mcp_server.py
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django

django.setup()

from apps.core.mcp import mcp

if __name__ == "__main__":
    mcp.run()
```

This shape also works well with the FastMCP CLI because the file fully prepares
Django when loaded by `fastmcp list`, `fastmcp call`, or an MCP inspector.

## HTTP Sidecar Pattern

Use a sidecar when Django is still deployed through WSGI, when MCP needs
separate scaling, or when you want a clear operational boundary. The sidecar is
a separate process that initializes Django, imports the same MCP server object,
and serves Streamable HTTP.

```python
# mcp_http_server.py
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django

django.setup()

from apps.core.mcp import mcp

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8765,
        path="/mcp",
    )
```

Run the Django web process and MCP process independently:

```text
web: gunicorn project.wsgi:application
mcp: python mcp_http_server.py
```

Point the reverse proxy or internal client at the sidecar's `/mcp` endpoint.
Keep the sidecar on a private interface unless it has production-grade TLS,
auth, rate limits, logging, and monitoring. Give it the same settings module,
database URL, cache/broker settings, secrets, and migrations as the web process.
Do not try to mount FastMCP inside WSGI middleware; use ASGI mounting only when
the combined process is actually served by an ASGI server.

## ASGI Mount Pattern

For a Django app already served by ASGI, make FastMCP a sibling ASGI app and
route `/mcp` before the Django catch-all. Pass the FastMCP lifespan to the outer
Starlette app; otherwise Streamable HTTP session management may not initialize.

```python
# project/asgi.py
import os

from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django_app = get_asgi_application()

from apps.core.mcp import mcp

mcp_app = mcp.http_app(path="/")

application = Starlette(
    routes=[
        Mount("/mcp", app=mcp_app),
        Mount("/", app=django_app),
    ],
    lifespan=mcp_app.lifespan,
)
```

If the project uses Channels, keep websocket routing in `ProtocolTypeRouter` and
put the Starlette HTTP router in the `"http"` branch. If the project already has
an app lifespan, compose it with the FastMCP lifespan instead of replacing it.

Do not set both the mount prefix and `http_app(path=...)` to `/mcp` unless the
intended endpoint is `/mcp/mcp`. When mounting at `/mcp`, use
`mcp.http_app(path="/")`; when running FastMCP as the whole HTTP app, use a path
such as `mcp.http_app(path="/mcp")` or `mcp.run(transport="http", path="/mcp")`.

## Tool Design

Create tools as narrow application actions, not generic database access.

```python
# apps/core/mcp.py
from collections.abc import Callable
from typing import Annotated

from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, transaction
from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field


class ResourceNotFound(Exception):
    """Safe not-found error for MCP clients."""


def get_current_actor_id() -> int:
    """Return the authenticated Django user ID from trusted MCP auth context."""
    raise PermissionDenied("Authentication is required")


def _order_summary(order_id: int, actor_id: int) -> dict:
    from apps.orders.models import Order

    try:
        order = Order.objects.select_related("customer").get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise ResourceNotFound("Order not found") from exc

    if not order.can_be_viewed_by_id(actor_id):
        raise PermissionDenied("Not allowed to view this order")

    return {
        "id": order.pk,
        "status": order.status,
        "customer": order.customer.name,
        "total_cents": order.total_cents,
    }


def create_mcp(
    actor_id_dependency: Callable[[], int] = get_current_actor_id,
) -> FastMCP:
    mcp = FastMCP("Project MCP", on_duplicate_tools="error")

    @mcp.tool(timeout=10)
    def get_order_summary(
        order_id: Annotated[int, Field(gt=0, description="Internal order ID")],
        actor_id: int = Depends(actor_id_dependency),
    ) -> dict:
        """Return a concise order summary the actor is allowed to view."""
        close_old_connections()
        try:
            return _order_summary(order_id=order_id, actor_id=actor_id)
        except ResourceNotFound:
            return {"error": "not_found", "message": "Order not found"}
        except PermissionDenied:
            return {
                "error": "forbidden",
                "message": "Not allowed to view this order",
            }
        finally:
            close_old_connections()

    @mcp.tool(timeout=20)
    def cancel_order(
        order_id: Annotated[int, Field(gt=0)],
        reason: Annotated[str, Field(min_length=3, max_length=500)],
        actor_id: int = Depends(actor_id_dependency),
    ) -> dict:
        """Cancel an order if the actor is allowed to do so."""
        close_old_connections()
        try:
            with transaction.atomic():
                from apps.orders.services import cancel_order_for_actor

                order = cancel_order_for_actor(
                    order_id=order_id,
                    actor_id=actor_id,
                    reason=reason,
                )
                transaction.on_commit(lambda: order.enqueue_cancellation_email())
                return {"id": order.pk, "status": order.status}
        except PermissionDenied:
            return {
                "error": "forbidden",
                "message": "Not allowed to cancel this order",
            }
        except ValueError:
            return {
                "error": "invalid_state",
                "message": "Order cannot be cancelled",
            }
        finally:
            close_old_connections()

    return mcp


mcp = create_mcp()
```

Rules for tool contracts:

- Use typed parameters, Pydantic `Field` constraints, docstrings, return type
  annotations, and small JSON-serializable return values.
- Use existing Django services and policy methods. Do not duplicate permission
  logic inside MCP modules when a project already has one source of truth.
- Keep writes idempotent where possible. Include explicit confirmation fields or
  idempotency keys for costly/destructive tools.
- Pass durable identifiers, not Django model instances, request objects, lazy
  querysets, open files, or huge payloads.
- Paginate and cap every list/search tool. Return stable IDs and summaries, not
  entire model dumps.
- Add `timeout=...` on slow or externally dependent tools and make long-running
  work enqueue a background job instead of holding the MCP request open.
- Never let the model provide privileged identity fields in production. Inject
  the current user/account from validated auth context or a trusted dependency.

## Django Async Rules

- A synchronous `def` FastMCP tool is usually simplest for Django ORM work.
  FastMCP dispatches sync tools without blocking the event loop, and the tool
  can use normal ORM, transactions, forms, and serializers.
- In an `async def` tool, do not call sync ORM or other async-unsafe Django code
  directly. Use Django async ORM methods (`aget`, `acreate`, `asave`,
  `async for`) when they cover the operation.
- Transactions do not work in Django async mode. Put transactional work in one
  synchronous helper and call it with `sync_to_async(..., thread_sensitive=True)`
  from the async tool.
- Do not set `DJANGO_ALLOW_ASYNC_UNSAFE` to make MCP tools work. Fix the calling
  boundary instead.
- Because MCP calls are not Django requests, there is no normal request
  lifecycle to clean database connections. For long-lived MCP processes, call
  `close_old_connections()` around ORM work or centralize connection cleanup in
  a thin helper that preserves function signatures.

## Auth And Permissions

- Treat MCP auth separately from Django browser auth. Django session middleware,
  login decorators, and CSRF middleware do not automatically protect a mounted
  Starlette/FastMCP sub-application.
- Prefer bearer/JWT/OAuth-style auth for remote HTTP MCP servers. FastMCP auth
  only applies to HTTP-based transports; stdio inherits the local process
  security model.
- Map validated token claims to Django users, organizations, and scopes before
  calling domain services. Enforce object-level permissions inside each tool.
- Do not expose `user_id`, `organization_id`, `is_staff`, scope lists, or
  permission flags as LLM-controlled parameters. Use FastMCP dependency
  injection or request/auth context to hide trusted values from the tool schema.
- Do not rely on CORS or CSRF as an auth mechanism. Add CORS only when a browser
  MCP client or inspector needs it, and keep allowed origins and headers narrow.
- Mask sensitive error details in production. Return explicit, safe errors for
  denied permissions and validation failures; log full exceptions server-side.

## Resources And Prompts

- Use tools for permissioned data, mutations, searches, and any result that
  depends on the current user.
- Use resources for bounded, read-only, low-risk content such as public docs,
  product metadata, or static schemas. Do not publish private model tables as
  global resources unless every client may read them.
- Use prompts for reusable agent workflows such as "triage this customer", but
  keep prompts free of secrets and make them call tools rather than embedding
  stale database facts.

## Deployment

- Streamable HTTP is the preferred remote transport. SSE is legacy; stdio is for
  local tools.
- If Django is still WSGI-only, either run FastMCP as a separate HTTP sidecar or
  migrate the deployment to ASGI before mounting it into the same process.
- Run remote MCP behind TLS and real authentication. Avoid exposing unauthenticated
  internal tools on a public domain.
- For nginx or another reverse proxy, disable response buffering for MCP/SSE
  streams and raise read/send timeouts for long operations.
- If OAuth discovery is used under a mount prefix, verify well-known discovery
  URLs and avoid double-prefixing `base_url` and MCP paths.
- Keep environment parity: the MCP process needs the same `DJANGO_SETTINGS_MODULE`,
  database URL, cache/broker settings, secret management, logging, and migrations
  as the Django process.

## Testing

Use in-memory FastMCP clients for most tests. Async tests require
`pytest-asyncio` or an equivalent async pytest plugin. Either set
`asyncio_mode = "auto"` in pytest configuration or mark async tests explicitly
with `@pytest.mark.asyncio`.

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

```python
import pytest
from fastmcp import Client

from apps.core.mcp import create_mcp


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_get_order_summary(order, user):
    mcp = create_mcp(actor_id_dependency=lambda: user.pk)

    async with Client(mcp) as mcp_client:
        result = await mcp_client.call_tool(
            "get_order_summary",
            {"order_id": order.pk},
        )

    assert result.data["id"] == order.pk
    assert result.data["status"] == order.status
```

Testing checklist:

- Assert `list_tools()` output for names, descriptions, and schemas when tool
  contracts matter.
- Test allowed and denied users for every permissioned tool.
- Test invalid inputs, missing objects, pagination caps, and destructive action
  confirmation paths.
- Test write tools against database state and `transaction.on_commit` side
  effects.
- When tools use auth-injected dependencies, test through the same auth path or
  build the server through a factory that accepts a test auth resolver. Do not
  expose `actor_id` as an LLM parameter just to make tests easier.
- Add one HTTP transport smoke test only when ASGI mounting, auth headers, proxy
  behavior, or URL paths changed.
- Use `pytest.mark.django_db(transaction=True)` when a separate server process
  or background worker must observe committed rows.

Useful local checks:

```bash
DJANGO_SETTINGS_MODULE=project.settings fastmcp list mcp_server.py
DJANGO_SETTINGS_MODULE=project.settings fastmcp inspect mcp_server.py --format json
fastmcp call http://localhost:8000/mcp get_order_summary order_id=1 --auth "Bearer $TOKEN"
```

## Debugging Checklist

- `AppRegistryNotReady`: initialize Django before importing models, or move model
  imports inside tools/helpers.
- `SynchronousOnlyOperation`: sync Django code is running in an async tool. Use a
  sync tool, async ORM methods, or `sync_to_async(..., thread_sensitive=True)`.
- HTTP 404 or `/mcp/mcp`: check the ASGI mount prefix versus `http_app(path=...)`.
- Session manager or stream errors: make sure the outer ASGI app uses
  `mcp_app.lifespan`.
- Client connects but receives no streamed results: check proxy buffering and
  timeout settings.
- Tool list is huge or unsafe: replace generic model/API exposure with a small
  allowlist of agent-focused capabilities.
- Tool schema is wrong: remove `*args`/`**kwargs`, add type annotations, avoid
  wrappers that hide the original function signature, and inspect with
  `fastmcp inspect`.
- Auth appears bypassed: remember that Django middleware may not run for mounted
  FastMCP routes. Validate tokens and enforce permissions inside the MCP layer
  and domain services.

## References

- FastMCP docs: https://gofastmcp.com/getting-started/welcome
- FastMCP GitHub: https://github.com/PrefectHQ/fastmcp
- FastMCP HTTP deployment: https://gofastmcp.com/deployment/http
- FastMCP tests: https://gofastmcp.com/development/tests
- FastMCP tools: https://gofastmcp.com/servers/tools
- FastMCP authentication: https://gofastmcp.com/servers/auth/authentication
- FastMCP dependency injection: https://gofastmcp.com/servers/dependency-injection
- Django async support: https://docs.djangoproject.com/en/5.2/topics/async/
- Django ASGI deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
