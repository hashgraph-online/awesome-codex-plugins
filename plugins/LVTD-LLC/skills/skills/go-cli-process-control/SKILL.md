---
name: go-cli-process-control
description: Execute and supervise external programs safely from Go CLIs with explicit arguments, typed failure classification, working directories, environments, bounded streams, deadlock-safe pipes, contexts, timeouts, signals, platform adapters, descendant cleanup, runner seams, and lifecycle tests. Use when wrapping a command, diagnosing start or exit failures, hangs, deadlocks, or orphan processes, or implementing cancellable cross-platform CLI workflows.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.3.0"
  displayName: Go CLI Process Control
  category: Go
  tags: go,golang,cli,os-exec,subprocess,signals,cancellation
---

# Go CLI Process Control

Treat child-process lifecycle as correctness. Observe the terminal result,
propagate cancellation, and clean up every process, pipe, and temporary resource.

## Core Workflow

1. Define the child executable, argv, environment, directory, streams, and success contract.
2. Use an explicit shell only when shell semantics are actually required.
3. Inject a runner boundary and propagate the caller's context.
4. Observe startup and completion; preserve status and useful redacted stderr.
5. Bound captured output, cancellation, and shutdown time.
6. Account for descendants and wait for every pipeline stage.
7. Test missing tools, bad exits, malformed output, cancellation, signals, and cleanup.

## Read Next

| Task | Load |
|---|---|
| Implement or repair process supervision | `guidelines.md`, `workflows/supervise-external-command.md` |
| Apply modern execution and cancellation rules | `references/process-control/rules.md` |
| Use runner, pipeline, signal, or cleanup patterns | `references/process-control/patterns.md` |
| Start from focused code examples | `references/process-control/examples.md` |
| Review a subprocess boundary | `references/process-control/checklist.md` |
| Understand lifecycle and shell semantics | `references/process-control/knowledge.md` |

## Guardrails

- Pass executable arguments separately; never assume `exec.Command` invokes a shell.
- Do not treat `Start` as success; inspect the terminal result.
- Do not assume context cancellation terminates an entire process tree.
- Close owned pipes and wait for every started process.
- Distinguish lookup, start, exit, timeout, cancellation, and cleanup failures.
- Treat `Cmd.String()` as diagnostic text, never shell-safe replay or secret-safe output.
- Avoid mutable package-level command hooks in concurrent tests.

## Source Notes

Guidance is transformed and paraphrased from Ricardo Gerardi,
*Powerful Command-Line Applications in Go* (Pragmatic Bookshelf, 2021),
especially Chapter 6. Examples are original adaptations.

Book: https://pragprog.com/titles/rggo/powerful-command-line-applications-in-go/

Verify current behavior against https://pkg.go.dev/os/exec and
https://pkg.go.dev/os/signal, including `Cmd.Cancel`, `WaitDelay`, and
`signal.NotifyContext`.

Failure taxonomy, pipe ordering, and platform-adapter guidance also incorporates
transformed material from Marian Montagnino, *Building Modern CLI Applications
in Go* (Packt, 2023), especially Chapter 6.

In-process cancellation boundary guidance also incorporates transformed
material from Inanc Gumus, *Go by Example: Programmer's Guide to Idiomatic and
Testable Programs* (Manning, 2025), Chapters 6-7.
