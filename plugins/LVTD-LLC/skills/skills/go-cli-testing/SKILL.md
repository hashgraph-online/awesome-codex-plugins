---
name: go-cli-testing
description: Design, implement, stabilize, and review Go CLI tests across fresh command trees, pure logic, table-driven cases, streams, typed configuration, files, environment, function-backed HTTP fakes, repositories, subprocesses, capability profiles, race checks, and artifact behavior. Use when adding command tests, diagnosing flaky Go tests, choosing test boundaries, or verifying human-, agent-, and CI-facing CLI contracts.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.4.0"
  displayName: Go CLI Testing
  category: Go
  tags: go,golang,cli,testing,table-tests,integration-tests,subprocess
---

# Go CLI Testing

Test observable behavior at the narrowest boundary that proves it. Isolate every
mutable resource and reserve executable tests for process-level semantics.

## Core Workflow

1. Inventory success, invalid, boundary, dependency-failure, and cancellation behavior.
2. Map each case to a pure, command, adapter, integration, or binary test.
3. Inject arguments, streams, configuration, clocks, and effectful dependencies.
4. Isolate files, environment, servers, repositories, ports, and subprocesses.
5. Assert stdout, stderr, exit behavior, and errors according to the public contract.
6. Gate live or platform-specific tests and make their changes reversible.
7. Run standard, race, tagged, and relevant platform checks.
8. Execute every supported build profile and smoke-test final artifacts.
9. Interpret coverage gaps without treating execution as behavioral proof.

## Read Next

| Task | Load |
|---|---|
| Build or overhaul a CLI test suite | `guidelines.md`, `workflows/test-cli-command.md` |
| Stabilize a flaky asynchronous test | `workflows/stabilize-flaky-test.md` |
| Write focused command tests | `references/cli-testing/rules.md`, `references/cli-testing/examples.md` |
| Add subprocess, HTTP, repository, or integration tests | `references/cli-testing/patterns.md` |
| Review coverage, isolation, or flakiness | `references/cli-testing/checklist.md` |
| Choose the right test boundary | `references/cli-testing/knowledge.md` |
| Benchmark or profile performance | Use `go-performance-testing` |

## Guardrails

- Do not mutate developer data or depend on fixed temporary paths and ports.
- Do not run parallel tests that replace process-global state.
- Replace timing sleeps with synchronization, deadlines, or fake clocks.
- Use `testing/synctest` only when the minimum Go version supports it and the
  behavior fits an isolated bubble.
- Inspect wrapped errors structurally unless exact diagnostics are contractual.
- Prefer one valuable executable flow over many slow end-to-end tests.
- Construct a fresh command tree and typed configuration for every test.
- Assert both `Execute` errors and stream output.

## Source Notes

Guidance is transformed and paraphrased from testing material throughout
Ricardo Gerardi, *Powerful Command-Line Applications in Go* (Pragmatic
Bookshelf, 2021), especially Chapters 1-7 and 11. Examples are original.

Book: https://pragprog.com/titles/rggo/powerful-command-line-applications-in-go/

Modern test APIs should be verified against https://pkg.go.dev/testing and the
current Go documentation before implementation.

Fresh command-tree, HTTP fake, configuration, and build-profile guidance also
incorporates transformed material from Marian Montagnino, *Building Modern CLI
Applications in Go* (Packt, 2023), especially Chapters 4, 6, and 11.

Subtest, coverage, parser, concurrency, HTTP server, and SQL adapter guidance
also incorporates transformed material from Inanc Gumus, *Go by Example:
Programmer's Guide to Idiomatic and Testable Programs* (Manning, 2025),
Chapters 2-10.

Test categorization, race/shuffle execution, deterministic time, `iotest`, and
benchmark-correctness guidance also incorporates transformed material from
Teiva Harsanyi, *100 Go Mistakes and How to Avoid Them* (Manning, 2022),
Chapter 11.
