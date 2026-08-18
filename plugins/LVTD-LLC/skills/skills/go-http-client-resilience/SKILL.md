---
name: go-http-client-resilience
description: Design, implement, test, and review resilient Go HTTP client boundaries with context propagation, layered timeouts, transport reuse, request construction, authentication, status classification, bounded bodies, retry safety, backoff, rate limits, pagination, observability, and deterministic fakes. Use when a Go CLI or service calls remote APIs or when HTTP behavior is slow, flaky, unsafe, or hard to test.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.3.0"
  displayName: Go HTTP Client Resilience
  category: Go
  tags: go,golang,http,client,resilience,retries,api
---

# Go HTTP Client Resilience

Treat HTTP as a failure-prone boundary with a finite time and resource budget.
Retry only when both the failure and the operation are safe.

## Core Workflow

1. Define operation semantics, total deadline, idempotency, and response limits.
2. Reuse a configured client and transport; propagate context into every request.
3. Construct URLs, headers, authentication, and bodies without secret leakage.
4. Classify transport, timeout, status, protocol, and decode failures.
5. Add bounded retries with jitter only for safe transient cases.
6. Drain or close bodies correctly and bound all reads.
7. Test with a function-backed transport and focused integration server.

## Read Next

| Task | Load |
|---|---|
| Build or overhaul an HTTP client | `guidelines.md`, `workflows/build-http-client.md` |
| Configure deadlines, retries, or pagination | `references/http-client-resilience/rules.md` |
| Review Go patterns | `references/http-client-resilience/examples.md` |
| Understand failure and budget models | `references/http-client-resilience/knowledge.md` |

## Guardrails

- Never use an unbounded body read or an unbounded retry loop.
- Do not retry unsafe operations without an idempotency mechanism.
- Do not create a new transport per request.
- Do not log authorization headers, cookies, tokens, or unreviewed bodies.
- Close every non-nil response body, including non-2xx responses.

## Source Notes

Guidance is transformed and paraphrased from Marian Montagnino,
*Building Modern CLI Applications in Go* (Packt, 2023), especially Chapter 6,
and Ricardo Gerardi, *Powerful Command-Line Applications in Go* (2021).

Streaming, transport-pool, and HTTP test guidance also incorporates transformed
material from Inanc Gumus, *Go by Example: Programmer's Guide to Idiomatic and
Testable Programs* (Manning, 2025), Chapter 7.

Body ownership and client-timeout guidance also incorporates transformed
material from Teiva Harsanyi, *100 Go Mistakes and How to Avoid Them* (Manning,
2022), Chapter 10.

Verify behavior against https://pkg.go.dev/net/http and current API-specific
rate-limit, pagination, and idempotency documentation.
