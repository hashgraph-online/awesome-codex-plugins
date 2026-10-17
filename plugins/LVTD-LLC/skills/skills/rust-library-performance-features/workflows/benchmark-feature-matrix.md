# Benchmark Feature Matrix Workflow

Use this workflow when optimizing a Rust library or adding Cargo features that
change behavior, dependencies, or performance.

## Prerequisites

- A focused operation or API path.
- Expected user input sizes.
- Current Cargo features and dependencies.

**Reference**: `references/performance-feature-patterns.md`

## Workflow Steps

### Step 1: Define the Measurement

**Goal**: Measure what matters to callers.

- [ ] Identify the operation under optimization.
- [ ] Choose representative inputs.
- [ ] Exclude unrelated setup from measured code.

### Step 2: Add Baseline Benchmarks

**Goal**: Capture current behavior before changing implementation.

- [ ] Add Criterion or project-standard benchmarks.
- [ ] Run the baseline and save command/results in notes or PR description.
- [ ] Confirm benchmark output is stable enough for comparison.

### Step 3: Optimize or Gate

**Goal**: Make the smallest justified change.

- [ ] Optimize one concern at a time.
- [ ] Preserve public API unless measurements justify a change.
- [ ] Gate optional dependencies behind capability-named features.

### Step 4: Validate Feature Combinations

**Goal**: Avoid publishing broken feature sets.

- [ ] Run `cargo test`.
- [ ] Run `cargo test --no-default-features`.
- [ ] Run `cargo test --all-features`.
- [ ] Run important named feature combinations.
- [ ] Run docs for the relevant feature set.

### Step 5: Report Evidence

**Goal**: Make performance claims auditable.

- [ ] Include benchmark command and feature set.
- [ ] Summarize baseline versus candidate results.
- [ ] State caveats such as hardware, input shape, or variance.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Optimizing without baseline | No proof of improvement | Benchmark first |
| Testing only defaults | Feature-specific regressions | Run feature matrix |
| Claiming broad speedups | Misleads users | Scope claims to measured cases |

## Exit Criteria

- [ ] Benchmarks exist for the claimed hot path.
- [ ] Feature combinations compile and test.
- [ ] PR or docs include reproducible measurement commands.
