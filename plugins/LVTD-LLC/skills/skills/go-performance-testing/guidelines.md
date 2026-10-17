# Go Performance Testing Guidelines

## Routing

| Situation | Load |
|---|---|
| Create or repair a benchmark | `references/performance-testing/rules.md`, `references/performance-testing/examples.md` |
| Compare an optimization | `workflows/benchmark-code.md` |
| CPU or allocation mystery | `workflows/investigate-performance.md`, `references/performance-testing/knowledge.md` |
| Escape, cache, false sharing, pool, GC, or container question | `workflows/investigate-performance.md` |
| Evaluate or release a PGO build | `workflows/evaluate-pgo.md` |
| Parallel workload | `references/performance-testing/rules.md` |
| Production profiling | `references/performance-testing/knowledge.md`, then `go-cli-errors-observability` |
| Evolve a public API for speed | Use `go-idiomatic-api-design`, then this skill |

## Boundary

- Use `go-cli-testing` for correctness, coverage interpretation, `t.Parallel`,
  and race remediation.
- Use this skill for benchmarks, allocation evidence, profiles, traces, and
  statistically grounded performance comparisons.
- Use `go-cli-errors-observability` for securing production diagnostic surfaces.
- Use `go-cli-distribution` and `go-cli-release-automation` to preserve selected
  PGO inputs and tested artifact provenance.
