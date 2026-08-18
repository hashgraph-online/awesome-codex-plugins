# Investigate Performance Workflow

## Steps

1. Record the command, fixture, Go/build/PGO state, target architecture, CPU
   quota, memory limit, and repeated representative baseline.
2. Separate CPU, allocation churn, retained memory, blocking, mutex contention,
   scheduler sequencing, GC, I/O, and quota-throttling hypotheses.
3. Capture the least intrusive CPU, heap, block, mutex, or execution-trace
   evidence that can distinguish them.
4. Inspect flat, cumulative, source, and call-path evidence.
5. Branch from evidence into locality, false sharing, escape, pooling, inlining,
   GC, container, or PGO experiments.
6. Make one bounded change at the measured bottleneck.
7. Rerun the profile, benchmark, correctness suite, and final CLI artifact.
8. Report output equivalence and a causal before/profile/change/after narrative.

## Common Mistakes

- Profiling a tiny workload that never reaches steady state.
- Reading allocation-space as retained memory.
- Optimizing the hottest function when its caller is avoidable.
- Reporting percentage gains without absolute user-visible impact.
- Exposing profile or trace artifacts without explicit protection and consent.
