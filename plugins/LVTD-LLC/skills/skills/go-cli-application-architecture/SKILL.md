---
name: go-cli-application-architecture
description: Design and review maintainable Go CLI application boundaries, package layout, dependency direction, command factories, configuration ownership, adapters, services, storage, and composition roots. Use when starting a multi-command CLI, extracting business logic from Cobra, untangling globals, adding external dependencies, or deciding what belongs under cmd, internal, or reusable packages.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.3.0"
  displayName: Go CLI Application Architecture
  category: Go
  tags: go,golang,cli,architecture,packages,dependency-injection
---

# Go CLI Application Architecture

Organize around dependency direction and testable behavior, not a copied folder
template. Keep CLI framework code as an adapter around application services.

## Core Workflow

1. Identify commands, domain actions, external effects, and shared policies.
2. Separate parsing/rendering from application orchestration and adapters.
3. Define interfaces at the consumer that needs substitution.
4. Construct dependencies once in a composition root and pass them explicitly.
5. Keep configuration immutable after validation; give mutable state a dedicated store.
6. Record ownership and cleanup for every acquired resource and background task.
7. Test inward from pure logic to adapters and one assembled executable path.

## Read Next

| Task | Load |
|---|---|
| Design or refactor boundaries | `guidelines.md`, `workflows/design-application-boundaries.md` |
| Review ownership and cleanup | `workflows/review-resource-lifecycle.md` |
| Decide package and interface placement | `references/application-architecture/rules.md` |
| Review patterns and examples | `references/application-architecture/examples.md` |
| Understand dependency direction | `references/application-architecture/knowledge.md` |

## Guardrails

- Do not put domain behavior in Cobra `Run` functions.
- Avoid a central interfaces package and broad catch-all service abstractions.
- Do not use package globals or `init` for dependency construction.
- Keep fallible I/O and order-dependent startup out of `init`; use explicit composition.
- Keep runtime configuration distinct from mutable application storage.
- Add layers only when they create a real seam, invariant, or dependency boundary.

## Source Notes

Guidance is transformed and paraphrased from Marian Montagnino,
*Building Modern CLI Applications in Go* (Packt, 2023), especially Chapters
2-3, with original adaptations aligned to current Go conventions.

Concrete-first interfaces, dependency ownership, and adapter lifecycle guidance
also incorporates transformed material from Inanc Gumus, *Go by Example:
Programmer's Guide to Idiomatic and Testable Programs* (Manning, 2025),
Chapters 5 and 8-10.

Initialization and lifecycle guidance also incorporates transformed material
from Teiva Harsanyi, *100 Go Mistakes and How to Avoid Them* (Manning, 2022),
Chapters 2, 6, 7, and 10.
