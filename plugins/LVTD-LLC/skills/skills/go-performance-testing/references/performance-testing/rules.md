# Performance Testing Rules

## Workload

- Define latency, throughput, memory, or allocation success before measuring.
- Use stable inputs that represent real data sizes and distributions.
- Include setup in the measurement only when users pay that setup cost.
- Keep external networks and shared services out of microbenchmarks.

## Benchmark Construction

- Prefer `for b.Loop()` on Go 1.24 or newer.
- Use subbenchmarks for meaningful input-size or strategy matrices.
- Use `b.ReportAllocs` or `-benchmem` for allocation hypotheses.
- Use `b.SetBytes` when throughput per input byte is meaningful.
- Use `B.RunParallel` only when measuring a genuinely parallel workload.
- Avoid logging, assertions, and one-time fixture construction in timed code.
- Benchmark construction separately from steady-state reuse when callers pay
  those costs differently.
- For pre-`B.Loop` toolchains, use the `b.N` loop and retain an observable
  result so the compiler cannot eliminate the work.

## Comparison

- Run repeated samples with identical commands and controlled conditions.
- Save raw output and compare with `benchstat`.
- Report magnitude, uncertainty, workload, toolchain, and command.
- Reject changes that improve a microbenchmark but degrade the real workflow.

## Profiling

- Profile a workload long enough to produce useful samples.
- Collect one intrusive profile type at a time when interactions matter.
- Inspect top, graph, and source views before changing code.
- Validate the hypothesis with a fresh benchmark after the change.
- Protect profiles and traces as potentially sensitive artifacts.
- Prefer a bounded ordinary trace for one-shot CLIs; reserve flight recording
  for supported long-lived processes and delayed-onset failures.

## Runtime and Compiler

- Do not encode cache-line width or struct alignment as portable facts.
- Prefer ownership changes and per-worker reduction over manual padding.
- Do not treat every reported escape as a defect.
- Do not rely on inliner budgets, generated instructions, or conversion elision
  across toolchains and targets.
- Do not use `sync.Pool` as a cache, resource owner, or secret-bearing store.
- Reject oversized pooled buffers and reset state before reuse.
- Reduce allocations before changing `GOGC` or `GOMEMLIMIT`.
- Treat `GOMEMLIMIT` as soft runtime-managed memory and leave container headroom.
- Check the pinned runtime before prescribing container CPU helpers.
- Measure concurrency under the deployment cgroup and supported architectures.

## PGO

- Compare the final PGO artifact with a matching `-pgo=off` build.
- Record profile workload, revision, digest, main package, and privacy classification.
- Use separate profiles/build decisions for distinct main packages when necessary.
- Re-profile after optimization and reject representative workload regressions.
