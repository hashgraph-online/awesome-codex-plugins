---
name: go-performance-testing
description: Design, run, compare, and interpret Go performance evidence using benchmarks, B.Loop, benchstat, pprof, traces, escape analysis, cache locality, false sharing, sync.Pool, GC limits, container CPU behavior, and PGO. Use when investigating Go latency, throughput, CPU, memory, allocations, contention, runtime behavior, performance regressions, or optimization claims.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.2.0"
  displayName: Go Performance Testing
  category: Go
  tags: go,golang,benchmarks,profiling,pprof,performance
---

# Go Performance Testing

Optimize only after establishing a representative, repeatable measurement and a
specific hypothesis.

## Core Workflow

1. Define the user-visible metric and representative workload.
2. Stabilize correctness before measuring performance.
3. Write focused benchmarks with realistic inputs and controlled setup.
4. Collect repeated baseline samples in comparable conditions.
5. Use allocations, profiles, and traces to form a causal hypothesis.
6. Make one bounded change.
7. Compare repeated before/after samples statistically.
8. Recheck correctness and the end-to-end workload.

## Read Next

| Task | Load |
|---|---|
| Benchmark a function or package | `guidelines.md`, `workflows/benchmark-code.md` |
| Investigate a regression | `workflows/investigate-performance.md` |
| Evaluate profile-guided optimization | `workflows/evaluate-pgo.md` |
| Choose benchmark and profile controls | `references/performance-testing/rules.md` |
| Interpret metrics and profiles | `references/performance-testing/knowledge.md` |
| Review benchmark patterns | `references/performance-testing/examples.md` |

## Guardrails

- Do not optimize from one benchmark line or an unrepresentative microbenchmark.
- Do not compare runs made under materially different environments.
- Do not treat coverage or race detection as performance evidence.
- Name the profile sample type and distinguish flat from cumulative cost.
- Prefer `B.Loop` only when the pinned Go version supports it.
- Keep production profile endpoints protected and operationally controlled.
- Do not encode cache-line size, escape output, or inliner budgets as portable facts.
- Do not use `sync.Pool` as a cache or resource owner.

## Source Notes

Guidance is transformed and paraphrased from Inanc Gumus, *Go by Example:
Programmer's Guide to Idiomatic and Testable Programs* (Manning, 2025),
especially Chapter 3. Examples are original.

Diagnostics, locality, allocation, GC, and container guidance also incorporates
transformed material from Teiva Harsanyi, *100 Go Mistakes and How to Avoid
Them* (Manning, 2022), Chapter 12.

Book: https://www.manning.com/books/go-by-example

Verify current behavior against https://pkg.go.dev/testing,
https://go.dev/doc/diagnostics, and https://go.dev/doc/pgo.
