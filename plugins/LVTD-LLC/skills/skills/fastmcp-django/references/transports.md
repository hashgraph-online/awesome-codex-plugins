# FastMCP Django Transports

Use these patterns after selecting the transport boundary in `SKILL.md`.

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

This also works well with the FastMCP CLI because the file fully prepares
Django when loaded by `fastmcp list`, `fastmcp call`, or an MCP inspector.

## HTTP Sidecar Pattern

Use a sidecar when Django is still deployed through WSGI, when MCP needs
separate scaling, or when you want a clear operational boundary.

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

Do not try to mount FastMCP inside WSGI middleware. Use ASGI mounting only when
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
