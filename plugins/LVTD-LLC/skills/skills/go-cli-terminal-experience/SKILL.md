---
name: go-cli-terminal-experience
description: Design and review adaptive Go CLI terminal experiences with explicit human, plain, and structured modes; per-stream TTY detection; color and accessibility controls; prompts; progress; secret input; cancellation; and broken-pipe handling. Use when a Go CLI must work safely for people, scripts, AI agents, CI, redirected streams, or interactive dashboards.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.2.0"
  displayName: Go CLI Terminal Experience
  category: Go
  tags: go,golang,cli,terminal,tty,accessibility,agents
---

# Go CLI Terminal Experience

Make interaction an explicit mode, not an accidental consequence of where the
process runs. Preserve stable data and failure contracts underneath rich output.

## Core Workflow

1. Identify the caller and choose `human`, `plain`, or `structured` mode.
2. Detect terminal capabilities separately for stdin, stdout, and stderr.
3. Define stable stdout data, stderr diagnostics, and noninteractive behavior.
4. Add color, prompts, progress, or a dashboard only in compatible modes.
5. Propagate cancellation and treat a downstream closed pipe as normal completion.
6. Test terminals, redirection, CI, agents, accessibility controls, and interruption.

## Read Next

| Task | Load |
|---|---|
| Choose output and interaction modes | `guidelines.md`, `workflows/design-output-modes.md` |
| Add prompts, progress, color, or secrets | `references/terminal-experience/rules.md`, `workflows/add-safe-interaction.md` |
| Build a full-screen terminal UI | `workflows/build-terminal-dashboard.md` |
| Review examples and edge cases | `references/terminal-experience/examples.md` |
| Understand capability detection | `references/terminal-experience/knowledge.md` |

## Guardrails

- Never prompt, animate, or emit ANSI control sequences in structured mode.
- Do not infer stdin capability from stdout; inspect each stream independently.
- Honor explicit flags first, then environment conventions such as `NO_COLOR`,
  then terminal detection.
- Keep secrets out of arguments, history, logs, errors, and diagnostic bundles.
- Make `Ctrl-C`, context cancellation, and broken pipes deterministic.

## Source Notes

Guidance is transformed and paraphrased from Marian Montagnino,
*Building Modern CLI Applications in Go* (Packt, 2023), especially Chapters 8
and 10, and Ricardo Gerardi, *Powerful Command-Line Applications in Go*
(Pragmatic Bookshelf, 2021). Examples are original adaptations.

Verify current APIs against https://pkg.go.dev/golang.org/x/term,
https://no-color.org/, and the selected terminal UI framework.

Renderer lifecycle and backpressure guidance also incorporates transformed
material from Inanc Gumus, *Go by Example: Programmer's Guide to Idiomatic and
Testable Programs* (Manning, 2025), Chapters 6-7.
