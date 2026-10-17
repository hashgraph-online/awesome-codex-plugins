# Go HTTP Server Applications Guidelines

| Situation | Load |
|---|---|
| New API or service binary | `workflows/build-http-server.md` |
| Handler or mux tests | `workflows/test-http-server.md` |
| JSON rejection or body-limit bug | `references/http-server/rules.md` |
| Middleware order or response metrics | `references/http-server/knowledge.md`, `references/http-server/examples.md` |
| Shutdown, timeout, or readiness problem | `references/http-server/rules.md`, `workflows/test-http-server.md` |

## Boundary

- Use `go-cli-application-architecture` for general core and adapter direction.
- Use `go-http-client-resilience` for outbound HTTP clients.
- Use `go-cli-errors-observability` for safe fields, logging, and diagnostics.
- Use this skill for inbound HTTP semantics and server lifecycle.
