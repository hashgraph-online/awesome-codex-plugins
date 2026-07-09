# Performance Feature Patterns

Patterns for measuring Rust library performance and managing optional Cargo
features.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| Benchmark baseline | Measured current behavior before optimization. |
| Representative input | Data size and shape matching downstream use. |
| Feature matrix | Set of Cargo feature combinations that must compile and test. |
| Optional dependency | Dependency enabled only when a feature needs it. |
| Performance claim | Statement tied to benchmark scope and command. |

## Core Rules

1. Benchmark before optimizing.
2. Include small, medium, and realistic large inputs when the operation scales.
3. Keep benchmark setup outside the measured operation.
4. Preserve API clarity unless the measured gain justifies complexity.
5. Gate optional dependencies with named features.
6. Test `--no-default-features`, defaults, and `--all-features`.
7. Document benchmark commands and environmental caveats.

## Pattern: Criterion Benchmark

```rust
use criterion::{criterion_group, criterion_main, Criterion};

fn bench_parse(c: &mut Criterion) {
    let input = include_str!("fixtures/medium.txt");
    c.bench_function("parse medium fixture", |b| {
        b.iter(|| parse_input(input))
    });
}

criterion_group!(benches, bench_parse);
criterion_main!(benches);
```

Use fixture data that represents real caller behavior. Avoid measuring file I/O
unless I/O is the operation under test.

## Pattern: Optional Feature

```toml
[features]
default = ["std"]
std = []
serde = ["dep:serde"]

[dependencies]
serde = { version = "1", optional = true, features = ["derive"] }
```

Use feature names that describe user-visible capability, not implementation
details.

## Feature Matrix Checklist

- [ ] `cargo test`
- [ ] `cargo test --no-default-features`
- [ ] `cargo test --all-features`
- [ ] `cargo test --features <each important feature set>`
- [ ] `cargo doc --no-deps --all-features`
- [ ] Benchmarks run against the feature set being claimed.

## Review Smells

| Smell | Risk | Fix |
|-------|------|-----|
| Benchmark added after optimization | Cannot verify improvement | Commit or record baseline first |
| Bench setup inside measured closure | Inflated or noisy timing | Move setup outside `b.iter` |
| Optional dependency not marked optional | Users always pay compile cost | Add `optional = true` and feature gate |
| Feature name matches crate internals | Hard for users to choose | Name by capability |
