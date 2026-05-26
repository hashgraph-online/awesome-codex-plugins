# Profiling Playbook

Use this reference when `/perf` needs a repeatable measurement workflow instead of ad hoc timing.

## Required Sequence

1. State the scenario being measured.
2. Establish a baseline with repeatable inputs.
3. Capture CPU and allocation profiles when tooling supports it.
4. Rank hotspots by cumulative cost.
5. Apply one optimization at a time.
6. Re-measure with the same inputs.
7. Keep only changes that improve the metric without hurting correctness or readability.

## Metrics To Report

Always report the metrics the runtime can provide:

- Wall-clock latency or throughput.
- CPU hot functions by cumulative cost.
- Memory allocations or heap growth.
- I/O wait or external-call count when relevant.
- Variance across repeated runs.

## Common Pitfalls

- Optimizing without a baseline.
- Measuring a different scenario after the change.
- Keeping a micro-optimization that makes code harder to maintain.
- Comparing warm-cache output to cold-cache output.
- Ignoring allocation regressions after CPU improves.

## Report Table

```markdown
## Measurement

| Metric | Before | After | Delta | Verdict |
|---|---:|---:|---:|---|
| <metric> | <value> | <value> | <delta> | improve/regress/noise |
```

---

**Source:** Adapted from an external skill corpus / `profiling-software-performance`. Pattern-only, no verbatim text.
