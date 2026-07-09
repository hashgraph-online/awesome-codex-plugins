# FastMCP Django Auth, Deployment, Testing, And Debugging

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

## Deployment

- Streamable HTTP is the preferred remote transport. SSE is legacy; stdio is for
  local tools.
- If Django is still WSGI-only, either run FastMCP as a separate HTTP sidecar or
  migrate the deployment to ASGI before mounting it into the same process.
- Run remote MCP behind TLS and real authentication. Avoid exposing
  unauthenticated internal tools on a public domain.
- For nginx or another reverse proxy, disable response buffering for MCP/SSE
  streams and raise read/send timeouts for long operations.
- If OAuth discovery is used under a mount prefix, verify well-known discovery
  URLs and avoid double-prefixing `base_url` and MCP paths.
- Keep environment parity: the MCP process needs the same
  `DJANGO_SETTINGS_MODULE`, database URL, cache/broker settings, secret
  management, logging, and migrations as the Django process.

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
