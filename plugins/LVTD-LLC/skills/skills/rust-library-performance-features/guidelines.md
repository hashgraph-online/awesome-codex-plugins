# Rust Library Performance Features Guidelines

Use this router before editing benchmarks, features, or performance-sensitive
library APIs.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Adding Criterion benchmarks | `references/performance-feature-patterns.md`, `workflows/benchmark-feature-matrix.md` |
| Comparing algorithm changes | `workflows/benchmark-feature-matrix.md` |
| Adding optional dependencies | `references/performance-feature-patterns.md` |
| Checking default/no-default feature builds | `workflows/benchmark-feature-matrix.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Performance claim has no benchmark | `workflows/benchmark-feature-matrix.md` |
| Feature flag breaks docs or tests | `references/performance-feature-patterns.md` |
| Optional dependency is always compiled | `references/performance-feature-patterns.md` |
| Benchmark uses unrealistic tiny inputs only | `references/performance-feature-patterns.md` |

## Decision Tree

```text
Library performance or features?
|
+-- No benchmark? -> add benchmark before optimizing
+-- Optional capability? -> gate dependency behind feature
+-- Public API changes for speed? -> measure and document tradeoff
+-- Many feature combinations? -> test minimal, default, and all-features
+-- Publishing soon? -> record commands and baseline results
```

## File Index

| File | Purpose |
|------|---------|
| `references/performance-feature-patterns.md` | Benchmark and Cargo feature patterns |
| `workflows/benchmark-feature-matrix.md` | Step-by-step benchmark and feature validation |
