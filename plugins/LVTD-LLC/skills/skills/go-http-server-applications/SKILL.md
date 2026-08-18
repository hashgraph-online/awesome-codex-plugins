---
name: go-http-server-applications
description: Design, build, test, and review production Go HTTP servers covering inbound adapters, modern ServeMux routing, middleware, strict bounded request decoding, response commitment, transparent ResponseWriter wrapping, server timeouts, health semantics, graceful shutdown, shared-state safety, and httptest verification. Use when implementing an HTTP service, API handler, middleware stack, server lifecycle, health endpoint, or inbound JSON boundary in Go.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.2.0"
  displayName: Go HTTP Server Applications
  category: Go
  tags: go,golang,http,server,middleware,httptest
---

# Go HTTP Server Applications

Keep handlers thin, bound untrusted input, configure the server explicitly, and
make startup and shutdown part of the tested application contract.

## Core Workflow

1. Separate domain behavior from the inbound HTTP adapter.
2. Define routes, methods, media types, limits, and error mappings.
3. Build an explicit mux and ordered middleware stack.
4. Decode requests strictly and within endpoint-specific byte/time budgets.
5. Encode complete responses before committing headers where practical.
6. Configure listener, server timeouts, header limits, and health semantics.
7. Serve under a lifecycle that observes errors and drains with a deadline.
8. Test handlers, routing, middleware, shared state, and real loopback behavior.

## Read Next

| Task | Load |
|---|---|
| Build a server | `guidelines.md`, `workflows/build-http-server.md` |
| Test handlers or lifecycle | `workflows/test-http-server.md` |
| Review routing, middleware, JSON, or shutdown | `references/http-server/rules.md` |
| Understand server and writer contracts | `references/http-server/knowledge.md` |
| Review patterns | `references/http-server/examples.md` |

## Guardrails

- Do not use `http.DefaultServeMux` for application composition.
- Do not expose a public server with zero-value timeout policy by accident.
- Do not read request bodies without an endpoint-specific bound.
- Do not assume a wrapped `ResponseWriter` preserves optional capabilities.
- Do not call readiness an unconditional liveness response.
- Do not let the process exit before graceful shutdown finishes.

## Source Notes

Guidance is transformed and paraphrased from Inanc Gumus, *Go by Example:
Programmer's Guide to Idiomatic and Testable Programs* (Manning, 2025),
Chapters 8-9. Examples are original.

Terminal-response control-flow and timeout guidance also incorporates
transformed material from Teiva Harsanyi, *100 Go Mistakes and How to Avoid
Them* (Manning, 2022), Chapter 10.

Book: https://www.manning.com/books/go-by-example

Verify current routing and lifecycle behavior against https://pkg.go.dev/net/http
and https://pkg.go.dev/net/http/httptest for the pinned Go version.
