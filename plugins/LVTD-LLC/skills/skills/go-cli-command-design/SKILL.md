---
name: go-cli-command-design
description: Design and review predictable Go command-line interfaces with canonical names and flags; explicit inputs and precedence; human, plain, and structured output; safe prompting; stdout and stderr contracts; help; errors; exit codes; cancellation; dependency injection; and platform behavior. Use when creating a Go CLI, changing its public command contract, making command code testable, or reviewing compatibility for people, scripts, AI agents, and CI.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.4.0"
  displayName: Go CLI Command Design
  category: Go
  tags: go,golang,cli,command-design,flags,streams,portability
---

# Go CLI Command Design

Design the command as a public interface before treating it as an implementation.
Keep results pipeable, failures diagnosable, and process-global state at the edge.

## Core Workflow

1. State the command purpose, invocation syntax, callers, and compatibility promises.
2. Assign each input to a flag, operand, stdin, environment, or config source.
3. Define precedence, validation, conflicts, defaults, and blocking behavior.
4. Reserve stdout for results and requested help; use stderr for diagnostics,
   invalid-usage help, and progress.
5. Return errors from command logic and map exit codes at the process boundary.
6. Inject streams, configuration, and effects behind a small testable runner.
7. Verify help, invalid usage, operational failures, and supported target behavior.
8. Verify noninteractive, color-disabled, canceled, and short-reading pipe behavior.

## Read Next

| Task | Load |
|---|---|
| Design or change a complete command contract | `guidelines.md`, `workflows/design-command-interface.md` |
| Implement flags, streams, environment, or errors | `references/command-interface/rules.md`, `references/command-interface/examples.md` |
| Understand the design rationale | `references/command-interface/knowledge.md` |
| Review an existing command | `references/command-interface/checklist.md` |

## Guardrails

- Prefer a dedicated `flag.FlagSet` over package-global flags in reusable code.
- Do not read stdin unless the documented invocation requires it.
- Do not call `os.Exit` below the outer process boundary.
- Treat structured output, exact text, and exit codes as APIs when automation relies on them.
- Never prompt, animate, or emit ANSI sequences in structured or noninteractive mode.
- Treat closed downstream pipes as normal pipeline termination when appropriate.
- Cross-compilation does not replace target-level smoke testing.

## Source Notes

Guidance is transformed and paraphrased from Ricardo Gerardi,
*Powerful Command-Line Applications in Go* (Pragmatic Bookshelf, 2021),
especially Chapters 1-2. Examples are original adaptations.

Modern interaction, cancellation, and output-mode guidance also incorporates
transformed material from Marian Montagnino, *Building Modern CLI Applications
in Go* (Packt, 2023), especially Chapters 1, 5, 8, and 10.

Book: https://pragprog.com/titles/rggo/powerful-command-line-applications-in-go/

Modern API details should be verified against https://pkg.go.dev/flag and the
current Go documentation before implementation.

Parser grammar and validation guidance also incorporates transformed material
from Inanc Gumus, *Go by Example: Programmer's Guide to Idiomatic and Testable
Programs* (Manning, 2025), Chapter 4.
