# Performance Testing Knowledge

## Evidence Layers

Use the least expensive evidence that answers the question:

1. End-to-end timing for user-visible impact.
2. Package benchmarks for controlled comparison.
3. Allocation metrics for memory-pressure hypotheses.
4. CPU, heap, block, and mutex profiles for cost location.
5. Execution traces for scheduler, latency, and goroutine interactions.

Microbenchmarks isolate mechanisms but can misrepresent application impact.
Representative end-to-end workloads protect against optimizing the wrong path.

## Benchmark Semantics

On Go 1.24 and newer, `B.Loop` manages timed setup and cleanup and helps prevent
the loop body from being eliminated. It does not disable normal optimization.
Use the exact `for b.Loop()` form. Preserve a `b.N` pattern only for older
supported toolchains.

Use repeated samples and `benchstat`; one before/after line does not describe
noise or uncertainty. Compare on equivalent machines, power modes, workloads,
toolchains, and build flags.

## Profile Interpretation

CPU profiles sample active CPU work. Heap profiles can answer allocation-space
or in-use-space questions; state which one. Block and mutex profiles add
instrumentation cost. Flat cost belongs directly to a symbol; cumulative cost
includes callees.

## PGO

Profile-guided optimization needs representative CPU profiles. Production
profiles are preferable; a representative CLI workload can substitute when
production collection is impossible. Narrow microbenchmarks are usually poor
PGO inputs.

Treat the selected profile as a versioned build input. Compare the final
artifact against `-pgo=off`, record profile provenance and digest, and
re-profile the optimized binary. Representative whole-program CLI workloads
are usually better inputs than narrow microbenchmarks.

## Locality, Escape, and Allocation

Cache locality and false sharing depend on target architecture and workload.
Prefer compact hot data and per-worker local reduction before guessed padding.
Measure final artifacts on supported targets rather than encoding a remembered
cache-line width.

Escape analysis describes a compiler decision for the current build. Use
scoped compiler diagnostics after allocation evidence identifies a material
cost. Reduce avoidable allocation before introducing `sync.Pool`; a pool is
temporary scratch reuse, not a cache, ownership system, or retention guarantee.

## Runtime and Containers

Tune GC only after measuring allocation rate, live heap, latency, and CPU.
`GOMEMLIMIT` is a soft limit on runtime-managed memory, not RSS or a container
hard cap, so retain headroom.

Go 1.25+ can choose container-aware `GOMAXPROCS` defaults on Linux. Check the
pinned runtime and explicit environment or API overrides before adding a
third-party adjustment. Measure worker counts under the deployment CPU quota.

Use `runtime/trace.FlightRecorder` only when the minimum Go version supports it
and preceding events in a long-lived agent or daemon matter. The Go 1.26
goroutine-leak profile is experimental and build-gated; it cannot identify
every long-lived goroutine.
