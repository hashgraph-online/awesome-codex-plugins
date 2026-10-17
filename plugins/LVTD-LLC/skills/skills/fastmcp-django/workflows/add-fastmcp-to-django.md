# Add FastMCP To Django

Use this workflow when adding or changing an MCP server in an existing Django
application.

## Workflow

1. Read the current application boundary:
   - `manage.py`
   - settings modules
   - `asgi.py` and `wsgi.py`
   - URL routing
   - auth middleware
   - DRF/Ninja/OpenAPI surfaces
   - Celery, Django Q, or other background workers
   - deployment files
2. Choose the transport:
   - stdio for local desktop/editor MCP.
   - HTTP sidecar for WSGI deployments or independent MCP scaling.
   - ASGI mount for existing ASGI deployments where same-process sharing is
     intentional.
3. Create one small MCP registration module, commonly `apps/core/mcp.py` or
   `project/mcp.py`.
4. Build tools around existing application services. Keep permission checks,
   transactions, validation, and business rules in their existing Django owner.
5. Design tool contracts before writing transport code:
   - name
   - purpose
   - typed inputs
   - trusted identity source
   - permission checks
   - bounded output
   - timeout and failure behavior
6. Add in-memory `fastmcp.Client` tests for tool behavior.
7. Wire the transport only after tool behavior and permissions are covered.
8. Add an HTTP smoke test when auth headers, ASGI mounting, path prefixes, proxy
   behavior, or production deployment changed.

## Done Criteria

- Tool list is small and intentional.
- No generic model browser, SQL runner, arbitrary file access, or admin escape
  hatch is exposed without an explicit allowlist and authorization plan.
- List/search tools are paginated and capped.
- Writes are permissioned, transactional where needed, and idempotent where
  retries are likely.
- Tool schemas do not expose `user_id`, `organization_id`, `is_staff`, scopes,
  or other privileged identity fields as model-controlled parameters.
- Local checks inspect the actual tool schema, not only Python import success.
