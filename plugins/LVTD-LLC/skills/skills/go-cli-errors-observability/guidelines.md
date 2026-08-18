# Go CLI Errors and Observability Guidelines

## Workflows

| Task | Workflow |
|---|---|
| Create actionable failure semantics | `workflows/design-error-recovery.md` |
| Add debug logs or diagnostic bundles | `workflows/add-safe-diagnostics.md` |

## By Symptom

| Symptom | Load |
|---|---|
| Every failure exits the same way | `references/errors-observability/knowledge.md` |
| Error text is duplicated or brittle | `references/errors-observability/examples.md` |
| Debug logs corrupt JSON | `references/errors-observability/rules.md` |
| Support bundle leaks tokens or paths | `workflows/add-safe-diagnostics.md` |
| Timeout is reported as an internal defect | `references/errors-observability/rules.md` |
| Inbound HTTP status mapping or response handling | Use `go-http-server-applications` |
| Local benchmarks or performance profiles | Use `go-performance-testing` |
| Joined errors evade classification | `references/errors-observability/knowledge.md` |

## Decision

```text
Can the caller recover?
├─ yes → stable class + concise message + next action
└─ no
   ├─ expected dependency/cancellation failure → bounded diagnostics
   └─ suspected defect → correlation ID + opt-in safe evidence
```

## File Index

| File | Purpose |
|---|---|
| `references/errors-observability/knowledge.md` | Error layers, logs, diagnostics |
| `references/errors-observability/rules.md` | Safety and implementation rules |
| `references/errors-observability/examples.md` | Go patterns and anti-patterns |
