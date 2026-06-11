---
name: perf
description: "Run perf."
---
# Perf Skill

> Quick Ref: `$perf profile <target>` | `$perf bench <target>` | `$perf compare <baseline> <candidate>` | `$perf optimize <target>`

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Performance profiling, benchmarking, regression detection, and optimization recommendations for any language runtime. Produces actionable metrics, not vague advice.

## Modes

| Mode | Command | Purpose |
|------|---------|---------|
| **Profile** | `$perf profile <target>` | Profile execution, find hotspots |
| **Benchmark** | `$perf bench <target>` | Create or run benchmarks |
| **Compare** | `$perf compare <baseline> <candidate>` | Compare two runs for regression |
| **Optimize** | `$perf optimize <target>` | Analyze and apply optimizations |

If no mode is specified, default to **profile**.

---

## Step 0: Detect Language and Tooling

Identify the language/runtime from file extensions, `go.mod`, `package.json`, `pyproject.toml`, `Cargo.toml`, or explicit user input. Select the profiling stack:

If the symptom may be host pressure rather than target-code performance, read [references/system-pressure-triage.md](references/system-pressure-triage.md) before benchmarking.

For the repeatable measurement loop, profiler selection, and report metrics, read [references/profiling-playbook.md](references/profiling-playbook.md).

| Language | Benchmarking | CPU Profile | Memory Profile | Comparison |
|----------|-------------|-------------|----------------|------------|
| **Go** | `go test -bench` | `go tool pprof` (cpu) | `go tool pprof` (alloc) | `benchstat` |
| **Python** | `pytest-benchmark`, `timeit` | `cProfile`, `py-spy` | `memory_profiler`, `tracemalloc` | manual diff |
| **Node** | `benchmark.js`, `vitest bench` | `--prof`, `clinic.js` | `--heap-prof`, `0x` | manual diff |
| **Rust** | `criterion`, `cargo bench` | `cargo flamegraph` | `heaptrack`, `DHAT` | `critcmp` |
| **Shell** | `hyperfine` | `time`, `strace` | N/A | `hyperfine` built-in |

Check which tools are actually installed. If a preferred tool is missing, fall back to standard-library alternatives before asking the user to install anything.

---

## Step 1: Establish Baseline

Run existing benchmarks first. If none exist, create them.

### 1a. Find Existing Benchmarks

```bash
# Go
grep -r "func Benchmark" --include="*_test.go" -l .

# Python
find . -name "test_*" -exec grep -l "benchmark\|@pytest.mark.benchmark" {} +

# Rust
grep -r "#\[bench\]" --include="*.rs" -l .

# Node
find . -name "*.bench.*" -o -name "*.benchmark.*"
```

### 1b. Run or Create Benchmarks

If benchmarks exist for the target, run them and capture output. If none exist, write benchmarks covering the target function or module.

**Benchmark requirements:**
- Measure wall-clock time (ops/sec or ns/op)
- Measure memory allocations (bytes/op, allocs/op)
- Run enough iterations for statistical stability (Go: `-benchtime=3s -count=5`)
- Record latency percentiles where applicable: p50, p95, p99

Save raw baseline output to `.agents/perf/baseline-YYYY-MM-DD.txt`.

### 1c. Go Benchmark Template

```go
func BenchmarkTargetFunction(b *testing.B) {
    // Setup outside the loop
    input := prepareInput()
    b.ResetTimer()
    b.ReportAllocs()
    for i := 0; i < b.N; i++ {
        TargetFunction(input)
    }
}
```

### 1d. Python Benchmark Template

```python
import pytest

@pytest.mark.benchmark(group="target")
def test_target_benchmark(benchmark):
    input_data = prepare_input()
    result = benchmark(target_function, input_data)
    assert result is not None
```

---

## Step 2: Profile and Identify Hotspots

### CPU Profiling

Find functions consuming the most CPU time.

**Go:**
```bash
go test -bench=BenchmarkTarget -cpuprofile=cpu.prof ./...
go tool pprof -top cpu.prof
go tool pprof -text -cum cpu.prof   # cumulative view
```

**Python:**
```bash
python -m cProfile -s cumulative target_script.py
# Or for running processes:
py-spy top --pid <PID>
py-spy record -o profile.svg --pid <PID>
```

### Memory Profiling

Find allocation hotspots and potential leaks.

**Go:**
```bash
go test -bench=BenchmarkTarget -memprofile=mem.prof ./...
go tool pprof -top -alloc_space mem.prof
```

**Python:**
```bash
python -m memory_profiler target_script.py
# Or with tracemalloc in code:
# tracemalloc.start(); ...; snapshot = tracemalloc.take_snapshot()
```

### I/O Profiling

Identify blocking operations in hot paths.

- Check for synchronous file I/O, network calls, or database queries inside loops.
- Look for missing connection pooling, unbuffered writes, or serial HTTP calls that could be concurrent.

### Hotspot Summary

After profiling, produce a ranked list:

```
HOTSPOTS (by cumulative CPU time):
1. pkg/engine.Process       42.3%  (1.2s)   — main processing loop
2. pkg/engine.parseRecord   28.1%  (0.8s)   — record deserialization
3. pkg/io.ReadBatch         15.7%  (0.45s)  — disk reads
```

---

## Step 3: Analyze and Recommend

Classify each finding by estimated impact:

| Impact | Criteria | Action |
|--------|----------|--------|
| **High** | >20% of total time or >50% of allocations | Fix immediately |
| **Medium** | 5-20% of total time or notable allocation waste | Fix in this session |
| **Low** | <5% of total time, minor inefficiency | Log for later |

### Common Anti-Patterns

Check the profiled code against these known performance killers:

1. **Unnecessary allocations** — allocating inside hot loops, string concatenation in loops (use `strings.Builder` / `[]byte` / `io.StringWriter`)
2. **N+1 queries** — database call per item instead of batch query
3. **Missing caching** — recomputing expensive results that rarely change
4. **Blocking I/O in hot path** — synchronous network/disk calls where async or buffered I/O would work
5. **Excessive copying** — passing large structs by value, copying slices instead of slicing
6. **Suboptimal data structures** — linear search where a map lookup works, unbounded slice growth without pre-allocation
7. **Lock contention** — mutex held across I/O or long computation
8. **Regex compilation in loops** — compile once, reuse the compiled pattern
9. **Reflection in hot paths** — replace with code generation or type switches
10. **Unbuffered channels** — causing goroutine scheduling overhead in Go

For each finding, state:
- **What**: the specific code location and pattern
- **Why**: how it hurts performance (with numbers from profiling)
- **Fix**: concrete code change recommendation

---

## Step 4: Optimize (optimize mode only)

**Critical rule: ONE optimization at a time.**

For each optimization:

1. **Describe** the change before making it
2. **Apply** the single change
3. **Re-run** the benchmark suite
4. **Compare** results against baseline using `benchstat` (Go) or manual diff
5. **Keep or revert** — only keep changes that measurably improve metrics
6. **Commit** with message format: `perf(<scope>): <description> (+X% throughput)` or `perf(<scope>): <description> (-X% latency)`

For high-effort optimization work, load [references/optimization-proof-loop.md](references/optimization-proof-loop.md) before changing code. It defines the proof contract for isomorphic rewrites, benchmark deltas, and keep/revert decisions.

### Acceptance Criteria

- Improvement must be statistically significant (p < 0.05 for `benchstat`, or >5% consistent change for manual comparison)
- No correctness regressions — all existing tests must still pass
- No readability destruction for marginal gains (<2% improvement does not justify obfuscated code)

### Optimization Order

Apply optimizations in this order (highest expected impact first):

1. Algorithmic improvements (O(n^2) to O(n log n), etc.)
2. Allocation reduction (pre-allocate, pool, reuse buffers)
3. I/O batching and buffering
4. Caching and memoization
5. Concurrency improvements (parallelize independent work)
6. Micro-optimizations (only if profiling confirms they matter)

---

## Step 5: Output Report

Write the report to `.agents/perf/YYYY-MM-DD-perf-<target>.md`.

### Report Template

```markdown
# Performance Report: <target>
Date: YYYY-MM-DD
Mode: <profile|bench|compare|optimize>
Language: <detected>

## Summary
<1-2 sentence summary of findings>

## Baseline Metrics
| Metric | Value |
|--------|-------|
| ops/sec | ... |
| ns/op | ... |
| B/op | ... |
| allocs/op | ... |
| p50 latency | ... |
| p95 latency | ... |
| p99 latency | ... |

## Hotspots
<ranked list from Step 2>

## Findings
<classified findings from Step 3>

## Optimizations Applied (if optimize mode)
| Change | Before | After | Improvement |
|--------|--------|-------|-------------|
| ... | ... | ... | +X% |

## After Metrics (if optimize mode)
<same table as baseline, with new values>

## Recommendations
<remaining opportunities not addressed in this session>
```

---

## Compare Mode Details

When running `$perf compare <baseline> <candidate>`:

1. Locate or re-run benchmarks for both versions
2. Use language-native comparison tools:
   - **Go**: `benchstat baseline.txt candidate.txt`
   - **Rust**: `critcmp baseline candidate`
   - **Other**: side-by-side table with percentage deltas
3. Flag regressions (>5% slower or >10% more allocations) as **REGRESSION**
4. Flag improvements (>5% faster or >10% fewer allocations) as **IMPROVEMENT**
5. Flag statistically insignificant changes as **NOISE**

Output a summary table:

```
COMPARISON: baseline vs candidate
| Benchmark | Baseline | Candidate | Delta | Verdict |
|-----------|----------|-----------|-------|---------|
| BenchmarkProcess | 1.2ms | 0.9ms | -25% | IMPROVEMENT |
| BenchmarkParse | 450ns | 480ns | +6.7% | REGRESSION |
| BenchmarkIO | 3.1ms | 3.0ms | -3.2% | NOISE |
```

---

## Edge Cases

- **No benchmarks and no clear target**: Run `$complexity` first to identify hot paths, then benchmark those.
- **Flaky benchmarks**: Increase iteration count, pin to a single core (`GOMAXPROCS=1`), close competing processes.
- **Cannot install profiling tools**: Fall back to `time` for wall-clock and manual instrumentation for allocation counts.
- **Target is a CLI command**: Use `hyperfine` for wall-clock benchmarking across any language.

## See Also

- [complexity](../complexity/SKILL.md) — Find high-complexity code to target
- [standards](../standards/SKILL.md) — Language-specific optimization patterns
- [vibe](../vibe/SKILL.md) — Validate optimized code quality

## Reference Documents

- [references/profiling-playbook.md](references/profiling-playbook.md)
- [references/system-pressure-triage.md](references/system-pressure-triage.md)
- [references/optimization-proof-loop.md](references/optimization-proof-loop.md)
