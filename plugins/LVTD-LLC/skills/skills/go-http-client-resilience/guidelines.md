# Go HTTP Client Resilience Guidelines

## Workflow

| Task | Workflow |
|---|---|
| Build, refactor, or review a client operation | `workflows/build-http-client.md` |

## By Symptom

| Symptom | Load |
|---|---|
| Requests hang indefinitely | `references/http-client-resilience/knowledge.md` |
| Retries duplicate a mutation | `references/http-client-resilience/rules.md` |
| Tests require a live API | `references/http-client-resilience/examples.md` |
| Connections are not reused | `references/http-client-resilience/rules.md` |
| Error includes a token or huge body | `references/http-client-resilience/examples.md` |
| Pagination loops or exceeds deadline | `references/http-client-resilience/knowledge.md` |
| Inbound handler, middleware, or server shutdown | Use `go-http-server-applications` |
| Batch fan-out exceeds its concurrency budget | Use this skill with `go-concurrency-pipelines` |

## Retry Decision

```text
Did the attempt fail transiently?
├─ no → return classified failure
└─ yes
   ├─ operation idempotent or protected by idempotency key?
   │  ├─ no → return; do not guess
   │  └─ yes → budget remains? respect Retry-After, jitter, retry
   └─ context canceled/deadline exceeded → stop immediately
```

## File Index

| File | Purpose |
|---|---|
| `references/http-client-resilience/knowledge.md` | Budgets, failures, lifecycle |
| `references/http-client-resilience/rules.md` | Implementation and review rules |
| `references/http-client-resilience/examples.md` | Go patterns and deterministic fakes |
