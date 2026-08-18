# Go CLI Process Control Guidelines

Use this routing guide for external commands, pipelines, cancellation, and signals.

## Workflows

| Task | Workflow |
|---|---|
| Implement or repair supervised external-command execution | `workflows/supervise-external-command.md` |

## By Task

| Task | Load |
|---|---|
| Design an external-command boundary | `references/process-control/knowledge.md`, `references/process-control/rules.md` |
| Implement execution or a pipeline | `references/process-control/examples.md`, `references/process-control/patterns.md` |
| Implement an in-process channel pipeline | Use `go-concurrency-pipelines` |
| Add timeout, cancellation, or signal handling | `references/process-control/patterns.md`, `references/process-control/rules.md` |
| Review process cleanup and failure handling | `references/process-control/checklist.md` |

## By Code Element

| Element | Primary | Secondary |
|---|---|---|
| `exec.Cmd` | `references/process-control/rules.md` | `references/process-control/examples.md` |
| stdin/stdout/stderr pipe | `references/process-control/patterns.md` | `references/process-control/checklist.md` |
| `context.Context`, `Cancel`, or `WaitDelay` | `references/process-control/rules.md` | `references/process-control/patterns.md` |
| `signal.NotifyContext` and shutdown logic | `references/process-control/patterns.md` | `references/process-control/checklist.md` |

## By Problem or Symptom

| Symptom | Load |
|---|---|
| Child process hangs after cancellation | `references/process-control/rules.md`, `references/process-control/checklist.md` |
| Descendant processes survive shutdown | `references/process-control/knowledge.md`, `references/process-control/patterns.md` |
| Exit status or stderr is lost | `references/process-control/examples.md`, `references/process-control/rules.md` |
| Shell quoting or pipelines behave inconsistently | `references/process-control/knowledge.md`, `references/process-control/patterns.md` |

## Decision Tree

```text
What boundary are you controlling?
├─ One direct command → rules.md + examples.md
├─ OS process pipeline or pipe I/O → patterns.md + examples.md
├─ In-process goroutine/channel pipeline → go-concurrency-pipelines
├─ Timeout, cancellation, or signal → patterns.md + checklist.md
└─ Diagnosing a leak or hang → checklist.md
   └─ Need lifecycle rationale → knowledge.md
```

## File Index

| File | Purpose |
|---|---|
| `references/process-control/knowledge.md` | Process lifecycle, shells, streams, exit semantics, and cleanup |
| `references/process-control/rules.md` | Correctness rules for modern `os/exec`, context, and signals |
| `references/process-control/examples.md` | Original execution and cancellation examples |
| `references/process-control/patterns.md` | Pipelines, adapters, supervision, and shutdown patterns |
| `references/process-control/checklist.md` | Review and verification checks |

## Common Combinations

| Scenario | Files |
|---|---|
| Safe subprocess wrapper | `rules.md` + `examples.md` + `checklist.md` |
| Graceful shutdown | `patterns.md` + `checklist.md` |
| Diagnose process-tree behavior | `knowledge.md` + `rules.md` |
