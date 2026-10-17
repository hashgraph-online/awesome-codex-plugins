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

Use FastMCP to expose small, typed Django application capabilities to agents.
Keep Django as the source of truth for auth, permissions, validation, models,
transactions, and business rules. Treat FastMCP as the protocol layer around
existing application services.

## Tool Choice

- Prefer the standalone `fastmcp` package (`from fastmcp import FastMCP`) for
  new Python MCP work in Django.
- Use the official MCP Python SDK (`from mcp.server.fastmcp import FastMCP`)
  when the project has already standardized on it, needs lower-level protocol
  control, or a host explicitly requires SDK behavior.
- Consider `django-mcp-server` only when the project needs a Django-native
  package that works inside WSGI or declaratively exposes models/DRF APIs. Audit
  generated tool contracts and permissions before exposing private data.
- If the app already has a deliberate public OpenAPI surface, generated or
  proxied tools can help for a first pass. For production agents, prefer
  hand-curated tools with purpose-built names, schemas, permissions, and bounded
  outputs.

FastMCP docs track the project's `main` branch, so re-check current docs when
relying on recently added features or version badges.

## Resource Routing

Load only the files needed for the current task:

| Need | Read |
| --- | --- |
| Step-by-step implementation in an existing Django app | `workflows/add-fastmcp-to-django.md` |
| Stdio, HTTP sidecar, ASGI mount, and path-prefix examples | `references/transports.md` |
| Tool contract design, ORM boundaries, async rules, resources, and prompts | `references/tool-design.md` |
| Auth, deployment, tests, local checks, and debugging symptoms | `references/auth-deployment-testing.md` |

## Implementation Workflow

1. Read existing Django entrypoints first: `manage.py`, settings, `asgi.py`,
   `wsgi.py`, URL routing, auth middleware, APIs, background jobs, and
   deployment files.
2. Choose the transport boundary:
   - Use stdio for local desktop/editor MCP servers that run beside the app.
   - Use a separate FastMCP HTTP sidecar when Django is WSGI-only or MCP should
     scale independently.
   - Mount FastMCP into the Django ASGI process when the app already runs under
     ASGI and sharing process/domain is intentional.
3. Put MCP server registration in a small module such as `apps/core/mcp.py` or
   `project/mcp.py`.
4. Keep tool bodies thin. Call existing services, selectors, forms,
   serializers, policy methods, or domain functions.
5. Add tests through `fastmcp.Client` before wiring the transport. Most behavior
   should be tested in memory without a running web server.

## Core Rules

- Make every exposed capability explicit. Avoid generic SQL, generic model
  browsing, arbitrary imports, file path access, or "admin" tools unless the
  project has a clear allowlist and authorization plan.
- Use typed parameters, Pydantic constraints, return type annotations,
  docstrings, and small JSON-serializable return values.
- Pass durable identifiers, not Django model instances, request objects, lazy
  querysets, open files, or huge payloads.
- Paginate and cap list/search tools. Return stable IDs and summaries, not full
  model dumps.
- Inject the current user/account from validated auth context or a trusted
  dependency. Never let the model provide privileged identity fields in
  production.
- Use synchronous `def` FastMCP tools for ordinary Django ORM work unless the
  project has a clear async design.
- For long-lived MCP processes, call `close_old_connections()` around ORM work
  or centralize connection cleanup in a thin helper.
- Add timeouts to slow or externally dependent tools. Enqueue long-running work
  instead of holding MCP requests open.

## Verification

- Inspect tool names, schemas, and descriptions with `fastmcp list` or
  `fastmcp inspect` when tool contracts matter.
- Test allowed and denied users for every permissioned tool.
- Test invalid inputs, missing objects, pagination caps, destructive action
  confirmation, database state changes, and `transaction.on_commit` side
  effects.
- Add one HTTP transport smoke test when ASGI mounting, auth headers, proxy
  behavior, or URL paths changed.

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
