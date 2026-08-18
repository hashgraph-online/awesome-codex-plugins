---
name: go-cobra-applications
description: Build, refactor, test, and review Cobra-based Go applications with intentional command trees, fresh constructors, suggestions, typed boundaries, scoped flags, local or remote configuration, explicit precedence, safe live reload, context propagation, stable streams, shell completion, and generated documentation. Use for Cobra or Viper CLI architecture and implementation.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.4.0"
  displayName: Go Cobra Applications
  category: Go
  tags: go,golang,cli,cobra,viper,command-tree,configuration
---

# Go Cobra Applications

Keep Cobra and Viper at the application edge. Construct a fresh command tree
per execution and translate CLI state into typed application calls.

## Core Workflow

1. Model the tree around user resources, workflows, and operations.
2. Define invocation contracts, argument validation, examples, and flag scope.
3. Construct fresh root and subcommands with explicit dependencies and streams.
4. Keep handlers thin, propagate context, and return errors.
5. Resolve defaults, config, environment, and flags into a validated typed config.
6. Test parsing, inheritance, precedence, help, errors, and repeated execution.
7. Generate completion and documentation from the same runtime tree.

## Read Next

| Task | Load |
|---|---|
| Build or restructure a Cobra application | `guidelines.md`, `workflows/build-cobra-command-tree.md` |
| Apply command-tree, flag, config, and testing rules | `references/cobra-applications/rules.md` |
| Use constructors and focused implementation examples | `references/cobra-applications/examples.md` |
| Inject services or resolve configuration | `references/cobra-applications/patterns.md` |
| Review a Cobra/Viper application | `references/cobra-applications/checklist.md` |
| Understand architecture, completion, and docs | `references/cobra-applications/knowledge.md` |

## Guardrails

- Avoid mutable package-global commands and `init`-driven application wiring.
- Domain packages must not import Cobra or Viper.
- Use persistent flags only when descendants genuinely share the option.
- Treat configuration as validated runtime policy, not mutable application storage.
- Validate reload candidates and atomically publish only last-known-good state.
- Show usage for syntax errors, not routine operational failures.
- Verify generator, completion, docs, and configuration APIs against pinned versions.

## Source Notes

Guidance is transformed and paraphrased from Ricardo Gerardi,
*Powerful Command-Line Applications in Go* (Pragmatic Bookshelf, 2021),
especially Chapter 7. Examples are original adaptations.

Book: https://pragprog.com/titles/rggo/powerful-command-line-applications-in-go/

The book's 2021 generator flow is historical. Verify current APIs and tooling
against https://cobra.dev/ and https://github.com/spf13/viper before use.

Suggestion, remote configuration, and live-reload guidance also incorporates
transformed material from Marian Montagnino, *Building Modern CLI Applications
in Go* (Packt, 2023), especially Chapter 4.

Parser-boundary guidance also incorporates transformed material from Inanc
Gumus, *Go by Example: Programmer's Guide to Idiomatic and Testable Programs*
(Manning, 2025), Chapter 4.
