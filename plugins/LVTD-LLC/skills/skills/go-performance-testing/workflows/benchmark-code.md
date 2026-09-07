# Benchmark Code Workflow

## Steps

1. **Define** the user-visible metric, representative input, and acceptable noise.
2. **Prove correctness** with ordinary tests before benchmarking.
3. **Check support** and prefer exact `for b.Loop()` on Go 1.24+; retain a
   measured `b.N` loop and observable result for older toolchains.
4. **Construct** a benchmark with controlled setup and realistic work. State
   whether it measures construction, fresh input, or steady-state reuse.
5. **Baseline** with repeated samples and preserved raw output.
6. **Change** one mechanism based on a stated hypothesis.
7. **Compare** repeated samples with `benchstat`.
8. **Validate** correctness and the end-to-end workload again.

## Exit Criteria

- [ ] Commands, workload, environment, and toolchain are recorded.
- [ ] Raw before/after samples are preserved.
- [ ] The result is statistically and practically meaningful.
- [ ] Correctness and user-visible performance still hold.
