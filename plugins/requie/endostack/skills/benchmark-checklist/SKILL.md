---
name: benchmark-checklist
description: Seven evidence questions every performance number must pass before you report it or act on it. Use on /benchmark-checklist, whenever you produce a before/after timing, claim a speedup or regression, freeze a benchmark harness, or pick a library or setting for speed.
disable-model-invocation: true
---

# benchmark-checklist

A timing number can mislead in seven common ways. Each question below catches one of them, and each answer must come from run data, not from reasoning about what probably happened. If you cannot answer a question, the verdict is inconclusive.

Use it any time you produce a speed number: before/after figures in a PR, a claimed improvement or regression, building or freezing a harness for an optimization loop, or choosing a library or setting on speed. Skip it for discussion that involves no measurement.

## Rough estimates

If the user asked only for a ballpark figure, one run is enough. You still answer question 4 (failures) and question 7 (work actually done), and you tell the user it was a single run. Skip the rest unless the number looks wrong. A comparison that feeds a decision is never a rough estimate.

## Before you measure

1. Write the sentence you want to publish, with the metric, the percentile, the size of the effect, and the dataset. For example: "p95 latency of `POST /search` drops from 41 ms to 28 ms on the 2 million row fixture." The seven questions test that sentence.
2. Read the harness. List what it times, what it counts, and what it leaves out.
3. Check machine load and core count (`uptime`, `nproc` on Linux, `sysctl -n hw.ncpu` on macOS). On a loaded machine, identify the processes responsible. When they have to keep running, alternate the variants so each is exposed to the same noise, and note this in the report.

## The seven questions

**1. What is the bottleneck?** Name what stops the result from being twice as good. Profile in a separate run that you do not report, because profilers change timings. Useful views: CPU per process (`top`, `pidstat`), a language profiler (`perf`, `py-spy`, `--cpu-prof`, `pprof`), time blocked on I/O, and syscall counts (`strace -c`, `dtruss`). Trace the hottest frames back to source. Check whether the load generator saturated first; if it did, you measured the generator. A change that leaves the number flat is usually blocked by the bottleneck. Identify the bottleneck before you decide the change has no effect.

**2. Are both sides configured equally and like production?** Each variant runs as it would in production: optimized build, production flags and environment, real batch sizes and transaction modes, pooled connections, the cache temperature production sees, the same versions, the same data. When one variant uses out-of-the-box defaults, the result measures a difference in settings and tells you nothing about the implementations. If a variant is slow because of a setting (a commit per row, a debug build, a missing index), call it untuned, correct the setting, and measure again before you choose. Where fixing it is not possible, name no winner. "As currently configured" does not rescue a selection decision, because the user will adopt the option and can tune it afterwards.

**3. Is the number physically possible?** Compare throughput with disk and network bandwidth. Multiply operation rate by per-operation cost and compare with available cores. Compare a claimed saving with how long the changed part took to begin with. Amdahl's law sets the ceiling. Eliminating a step that took 10% of total runtime yields a speedup of 1/0.9, roughly 11%, and no more. A number past the ceiling means you timed something else, such as a cache hit, a no-op path, or a bug.

**4. Did anything fail?** Count errors, non-2xx responses, and other unsuccessful results. Check that outputs are correct, not merely present. Fast rejections make a variant look quick; timeouts and retries make it look slow. A `401` returned in 2 ms is a fast failure, not a fast endpoint. If the harness does not count failures, add the counting.

**5. Does it repeat?** Run each variant at least five times, interleaved (A B A B ...), so warm-up, lazy initialization, caches, and thermal drift do not favor one side. Report the median and the spread. A difference smaller than the run-to-run spread is no measurable difference. When the result is close, apply a Mann-Whitney U test, or whatever statistics the harness already reports.

**6. Would the user notice the gain?** Alongside every micro-benchmark, measure the full path the user actually waits on, with realistic data volume and concurrency, and express the micro result as a share of that total. A helper that takes 1% of request time can save at most 1%.

**7. Did the work happen?** Inside the timed window, confirm the request reached the server, rows were written, input was read, and the program used the result. A generator never iterated, a promise never awaited, a value the JIT eliminated, or a timeout all produce timings for work that did not happen.

## Benchmarks that touch the network

Point load at hosts you own or are authorized to test. Never aim a load generator at a third-party service, a shared staging environment, or production without written approval. Keep credentials the harness needs in environment variables, not in the harness file or the report.

## Reporting

- Open with one verdict: **faster**, **slower**, **no measurable change**, or **inconclusive**.
- Then one line with the figure and units, the number of runs, the spread, and the bottleneck. Example: "faster: p95 41 ms to 28 ms (n=7 each, IQR 2 ms), bottleneck moved from JSON encoding to the Postgres round trip."
- Mark the verdict inconclusive when a difference is claimed without an identified bottleneck, when either side ran untuned, or when question 4 or question 7 went unchecked. Say which.
- In a PR description, give one headline figure, as the opening-a-pr playbook in `tarique-mode` requires. Put per-run data, spread, and profiler evidence in a linked notes file or artifact.

## With playbooks

- **perf-issue** ([../tarique-mode/playbooks/perf-issue.md](../tarique-mode/playbooks/perf-issue.md)): vet the baseline with this checklist before the plan builds on it, and vet every number after it.
- **hillclimb**: vet the harness before you freeze it. Once frozen, the harness prints a failure count and a work count on every run, so each keep-or-revert decision answers questions 4 and 7 at no extra cost.

## Done when

Every relevant question has an answer backed by a run, or the verdict is inconclusive and names the missing piece.
