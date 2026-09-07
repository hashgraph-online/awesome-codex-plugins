---
name: go-cli-errors-observability
description: Design and review recoverable Go CLI errors, exit semantics, structured logging, debug modes, traces, profiles, redaction, and user-consented diagnostic bundles. Use when a CLI needs actionable failures, safe support evidence, production troubleshooting, or observability that does not corrupt command output or expose secrets.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.3.0"
  displayName: Go CLI Errors and Observability
  category: Go
  tags: go,golang,cli,errors,observability,logging,diagnostics
---

# Go CLI Errors and Observability

Design failures for recovery first, then add the minimum safe evidence needed to
diagnose them. Keep internal detail out of the normal user contract.

## Core Workflow

1. Classify failures by user action, dependency, cancellation, and internal defect.
2. Preserve machine-checkable causes with wrapping, types, or sentinels.
3. Map causes to concise user messages and stable exit behavior at the boundary.
4. Assign one terminal owner to render, log, and map each failure.
5. Preserve material cleanup failures without hiding the primary cause.
6. Add opt-in verbosity and structured logs on stderr or a dedicated sink.
7. Allowlist and redact diagnostic evidence; require consent before collection or upload.
8. Test recovery guidance, output separation, redaction, and cancellation.

## Read Next

| Task | Load |
|---|---|
| Design error taxonomy and recovery | `guidelines.md`, `workflows/design-error-recovery.md` |
| Add logging or support diagnostics | `references/errors-observability/rules.md`, `workflows/add-safe-diagnostics.md` |
| Review code patterns | `references/errors-observability/examples.md` |
| Understand layering and privacy | `references/errors-observability/knowledge.md` |

## Guardrails

- Never log secrets, authorization headers, raw config, or unreviewed environment data.
- Do not make normal stdout depend on log level.
- Preserve cancellation and timeout identity with `errors.Is`.
- Do not both log and return the same failure at intermediate layers.
- Do not use panic for ordinary validation, dependency, or user errors.
- Do not collect or upload diagnostics without a visible allowlist and consent.
- Protect profiling or debug servers; default them off and bind locally.

## Source Notes

Guidance is transformed and paraphrased from Marian Montagnino,
*Building Modern CLI Applications in Go* (Packt, 2023), especially Chapter 9,
and Ricardo Gerardi, *Powerful Command-Line Applications in Go* (2021).

Handler composition, context correlation, and joined-error guidance also
incorporates transformed material from Inanc Gumus, *Go by Example:
Programmer's Guide to Idiomatic and Testable Programs* (Manning, 2025),
Chapter 9.

Error ownership, panic boundaries, and cleanup-failure guidance also
incorporates transformed material from Teiva Harsanyi, *100 Go Mistakes and
How to Avoid Them* (Manning, 2022), Chapter 7.

Verify current logging APIs against https://pkg.go.dev/log/slog and error APIs
against the current Go standard library documentation.
