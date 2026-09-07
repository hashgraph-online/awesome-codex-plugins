# AtomLane

**Parallelize only what is proven safe.**

**Universal safety core. Platform-native execution. Workload-tailored acceleration.**

AtomLane is a cross-platform parallelism compiler and runtime for coding agents.
Its shared typed core proves dependencies and preserves task semantics; its
adapters tailor discovery, containment, and resource budgets to each supported
workload and execution realm. macOS is Stable. Native Windows is a scoped,
fail-closed Preview.

[![CI](https://github.com/cloudguo123/atomlane/actions/workflows/ci.yml/badge.svg)](https://github.com/cloudguo123/atomlane/actions/workflows/ci.yml)
[![CodeQL](https://github.com/cloudguo123/atomlane/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/cloudguo123/atomlane/actions/workflows/github-code-scanning/codeql)
[![Five-minute benchmark](https://github.com/cloudguo123/atomlane/actions/workflows/long-benchmark.yml/badge.svg)](https://github.com/cloudguo123/atomlane/actions/workflows/long-benchmark.yml)
[![Test report](https://img.shields.io/badge/test_report-live-65e6b4.svg)](https://cloudguo123.github.io/atomlane/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)
[![Discussions](https://img.shields.io/github/discussions/cloudguo123/atomlane?color=80b7ff)](https://github.com/cloudguo123/atomlane/discussions)

[中文说明](README.zh-CN.md) · [Live report](https://cloudguo123.github.io/atomlane/) · [Report first run](https://github.com/cloudguo123/atomlane/issues/new?template=first-run.yml) · [Share a benchmark](https://github.com/cloudguo123/atomlane/issues/new?template=benchmark.yml)

**Open source under MPL-2.0—free for personal, research, educational, and
commercial use.** The current community release requires no AtomLane account
or payment. Possible future alternative commercial licensing or separately
licensed capabilities will not change the terms of code already released
under MPL-2.0. [Licensing details](LICENSING.md)

![AtomLane controlled five-minute parallel benchmark](assets/growth/social-preview.svg)

## Install in two commands

```bash
codex plugin marketplace add cloudguo123/atomlane
codex plugin add atomlane@atomlane
```

Open a new Codex task after installation or upgrade. Codex will list AtomLane's
bundled task-assessment hook in **Hooks** and require a one-time review of its
exact definition before it can run. Once trusted, every submitted task shows one
of three advisory preflight results: direct path, inspect at the execution
boundary, or likely parallel candidate. The hook reads only the submitted prompt;
it does not scan the project, execute commands, block the prompt, or claim that
parallelism is safe. The skill and atomic planner make that decision later from
real entrypoints, effects, dependencies, platform, and resources. See the
[Hooks and live indicator guide](docs/HOOKS.md).

You can then ask explicitly:

```text
Use $accelerate-local-work to inspect this project and run the safe parts in parallel.
Keep progress visible and report time saved for this run and cumulatively.
```

For a long-running Python program, ask instead:

```text
Use $optimize-python-parallelism to inspect scripts/job.py. Do not run or modify
the target while analyzing it; show proof obligations and a hash-bound preview.
```

Requirements: macOS Stable, or the scoped native Windows Preview, Codex with plugin
and MCP support, and Python 3.10+ available as the `python3` command on `PATH`
(`python3 --version` must succeed). The current
[Python Install Manager](https://docs.python.org/3/using/windows.html#python-install-manager)
includes this compatibility alias on Windows. Ruby is only needed for Compose YAML analysis
on macOS; Node.js 20+ is only needed to rebuild the browser indicator. Windows
release evidence currently comes from the `windows-2025` CI image; it does not
establish Windows 11 Desktop UI integration. See the
[Windows Preview guide](docs/WINDOWS_PREVIEW.md) before using Windows workflows.

The installable package is Codex-native: `.codex-plugin/plugin.json`,
`.mcp.json`, `skills/`, and `hooks/hooks.json` ship as one unit. The root
`mcp.json` remains an optional vendor-neutral local-stdio configuration. This
release intentionally does not include a root Agent Plugins manifest because
current Codex releases classify that format separately and suppress bundled
lifecycle hooks when it is present.

## One core, tailored at three layers

“Universal” does not mean guessing that every task or platform is supported.
It means every admitted task passes the same typed safety contract. “Tailored”
means the route, containment, and concurrency budget change with the real
platform and workload.

| Layer | Universal contract | Tailored behavior |
| --- | --- | --- |
| Safety | Typed Atom IR, immutable plan hash, effect/conflict checks, authorization boundaries, live progress, and savings accounting | Unsupported semantics fail closed instead of being translated approximately |
| Platform | One planner and scheduler across supported native realms | macOS uses POSIX process groups and Apple-silicon probes/backends; native Windows Preview uses NT path rules, Job Objects, UTF-8 pipes, optional ConPTY, and whole-file PowerShell atoms |
| Workload | The same proof gate for independence, ordering, outputs, and resources | Build/test tools keep semantic ownership; Docker uses daemon/VM budgets; research keeps timing fences; Python routing distinguishes CPU, blocking I/O, native kernels, existing pools, and unsafe effects |

WSL, native Windows, macOS, and Docker are distinct execution realms. AtomLane
recompiles for the active realm and never presents one host's proof or resource
budget as portable evidence for another.

| Capability | macOS Stable | Native Windows Preview |
| --- | --- | --- |
| Shared core | Atom IR, hashes, effect/conflict checks, scheduler, live progress, savings ledger | The same core and proof rules |
| Automatic entrypoints | Supported shell, package, Make, Compose, test, and build frontends | Exact argv and declared whole-file `.ps1`; shell/package/Make/Compose/`.cmd`/`.bat` automatic lowering is not yet supported |
| Process boundary | POSIX session/process group | Staged kill-on-close Job Object for the supervisor and normally inherited target tree |
| Terminal/output | Bounded pipes and live runner | Separate UTF-8 pipes or output-only ConPTY; ConPTY stdin is rejected |
| Published evidence | macOS 14 CI and retained five-minute benchmark | Windows Server 2025 CI and separate five-minute benchmark; not Windows 11 Desktop UI proof |

## Why this exists

Most “parallel” wrappers split command text and hope for the best. That can reorder `&&`/`||`, race `.next`, JUnit, database, Docker volume, or Git state, multiply nested worker pools, and hide failures until the end.

AtomLane first compiles the requested work into a typed Atom IR. Only atoms proven independent are admitted concurrently. Unknown effects, ambiguous writers, stale source snapshots, unsupported lifecycle events, and changed plans fail closed.

```text
shell · package scripts · Make · Compose · tests · builds · declared work
                              │
                              ▼
             static frontends → typed Atom IR
                              │
                              ▼
        conflict checks → resource-aware event scheduler
                              │
                              ▼
              exact verified execution + live savings
```

## What it accelerates

| Project situation | Optimization target | Platform route | Safety boundary |
| --- | --- | --- | --- |
| Web / TypeScript | Quality gates, package graphs, browser matrices | macOS automatic frontends; Windows explicit argv/PowerShell atoms | Preserves success gates; isolates `.next`, coverage, JUnit, and caches |
| Docker / Compose | Multi-image builds, health DAGs, test matrices | macOS Compose frontend; Windows Preview exposes Linux-daemon resource advice but not native Compose lowering | Honors VM CPU/memory envelope, ports, volumes, readiness, and migrations |
| Research / papers | Data preparation, validation, figures, document builds | macOS frontends; Windows explicit stage atoms | Infers data edges and preserves formal timing/provenance fences |
| Native builds / tests | Make, compiler drivers, test runners | Platform-supported frontends or exact native argv | Delegates to semantic owners and budgets nested workers |
| Batch media / data / ML | Independent inputs and deterministic merges | Exact isolated argv on both native realms; Apple-only backends stay advisory off macOS | Requires disjoint outputs, bounded resources, and explicit merge semantics |
| Long-running Python | Ordered CPU maps, blocking reads, native kernels, subprocess batches | Static advisor supports both; CPU previews use explicit portable `spawn` | Never imports or executes targets; unknown effects, shared state, stale hashes, and unsafe spawn paths fail closed |

The scenario catalog includes more than 50 presets covering software, research, containers, media, ML, release, database, and low-level CPU/GPU/I/O work.

## Python parallel refactor advisor

`$optimize-python-parallelism` adds a program-level analysis lane before task
execution. The `python_parallel_advisor` MCP tool parses bounded project-local
UTF-8 source with Python's AST; it does not import the module, execute target
code, install packages, or edit files.

The first supported rewrite shape is deliberately narrow: same-module,
ordered `worker(item)` maps expressed as a list comprehension, returned list
comprehension, or append loop. For each candidate AtomLane propagates effects
through the local call graph, checks loop control and observable ordering,
requires a portable `__main__` import path and an explicit `spawn` context for
CPU process pools, detects
existing/native parallelism, budgets nested workers, and returns one of:

- `reviewable_rewrite`: pure CPU candidate with a syntax-checked unified diff;
- `advisory_only`: I/O or externally constrained work needing human design;
- `prefer_native`: vectorize or use a library's own GIL-releasing workers;
- `already_parallel`: coordinate existing pools instead of nesting another;
- `blocked`: keep serial until every reported hazard is resolved.

Every preview is bound to the exact source SHA-256 and is never applied
automatically. A measured serial hotspot may produce a modeled projection,
clearly labeled as not being a benchmark. Acceptance still requires serial vs
parallel differential tests, deterministic fixtures under explicit `spawn`,
exception/output checks, memory measurement, and a repeatable performance win.
See the [Python Candidate IR and proof gates](skills/optimize-python-parallelism/references/python-program-ir.md).

## Live execution—not a blank spinner

![Twenty-second live execution demo showing running, ready, completed, failed, and estimated savings](assets/growth/demo.gif)

Long runs use the live runner and continuously show:

```text
elapsed 2m 15s · running 4 · ready 2 · completed 7 · failed 0
estimated saved this run 4m 31s · cumulative saved 19m 52s
```

At completion, every atom's status, return code, timeout, skip reason, output truncation, peak concurrency, per-run savings, and cumulative savings are checked.

On Windows, the live surface shows scheduler lifecycle counts and savings;
captured task stdout/stderr is returned with the completed result. Ordinary
commands drain through separate byte pipes, while commands needing
terminal-shaped output may opt into ConPTY and one combined VT stream. A
waiting supervisor is added
to the Job Object by PID before it receives the launch record and creates the
target. This is staged supervision, not atomic target creation. Job CPU and
memory budgets include the supervisor plus the normally inherited target tree.
Work created through WSL, Docker, WMI, services, scheduled tasks, or another
broker is explicitly outside that Job boundary.

## Windows Preview contract

The Preview shares the same Atom IR, immutable plan hash, effect checks,
scheduler, live progress, and savings ledger as macOS. The platform adapter
adds Windows-native CPU/memory/power probes, NT path conflict rules, staged Job
Object supervision, optional ConPTY, and a conservative `pwsh` file frontend.

- Native Windows, WSL, and Docker's Linux VM are distinct execution realms;
  plans cannot cross or be replayed between them.
- Exact argv tasks and declared `.ps1` files are supported. PowerShell files
  remain one opaque atom and require complete declared effects.
- POSIX shell, package-script, Make, Compose, `.cmd`, and `.bat` lowering fail
  closed on native Windows in this Preview. Run POSIX workflows inside WSL, or
  declare exact native atoms instead of relying on shell-text translation.
- Job-wide CPU rate and memory controls cover the supervisor and normally
  inherited target tree; the memory limit is at least 128 MiB. In pipe mode,
  `max_processes` is the exact active-member ceiling for the entire Job and is
  at least 2; the verified supervisor consumes one slot while it is alive.
  ConPTY with `max_processes` fails before target code starts because
  console-host Job membership is not yet proven; CPU and memory limits remain
  available. None of these limits constrain brokered work. Windows process-pool
  advice never exceeds the platform's 61-worker wait limit.
- ConPTY is output-only in this Preview. Explicit ConPTY `stdin` fails before
  target creation because a verified terminal-input and EOF contract is not
  implemented; use pipes for bounded stdin and observable EOF.

The complete boundary and troubleshooting notes are in
[Windows Preview](docs/WINDOWS_PREVIEW.md).

## Retained macOS five-minute benchmark

The retained public macOS run executed four isolated low-load workloads through
the real parallel executor. Every task ran for at least five minutes. Native
Windows Preview evidence is reported separately on the live dashboard.

| Evidence | Result |
| --- | ---: |
| Parallel wall time | **5m 10s** |
| Serial equivalent | **20m 40s** |
| Time saved | **15m 30s** |
| Observed speedup | **4.00×** |
| Parallel efficiency | **100.0%** |

The serial equivalent is the sum of the observed independent task runtimes; it is not a separately executed serial run. This demonstrates scheduler overhead and reporting behavior under controlled independent work, not a universal claim that every project will be 4× faster. See the [visual report](https://cloudguo123.github.io/atomlane/), [raw evidence](https://cloudguo123.github.io/atomlane/benchmark-results.json), and [benchmark protocol](BENCHMARKING.md).

## Execution contract

The safety handshake is deliberately strict:

```text
atomic_task_plan
  → complete immutable compiled_plan + plan_hash
  → atomic_exec with that exact object and hash
```

Plans are not translated back into hand-written waves or generic DAG calls. Typed control edges distinguish success, failure, order, data, stream, readiness, health, completion, and cleanup. Artifacts, non-file effects, capacity resources, lifecycle events, and source snapshots remain part of the execution contract.

## Privacy and authorization

- Project and optional trace inspection are local and bounded.
- Python advice is static and non-executing; target modules are never imported and rewrite previews never modify files.
- Trace analysis returns aggregate routing signals—not prompts, reasoning, command bodies, or tool outputs.
- Parallelism changes timing, never permission. Planning does not authorize new commands, remote mutations, destructive cleanup, or retries.
- No run result is uploaded automatically. Sharing is explicit and reviewable.
- Timeouts terminate the contained POSIX process group or Windows Job Object;
  timed-out side effects are treated as unknown and are not automatically retried.

Read [SECURITY.md](SECURITY.md) for the threat model and reporting process.

## Development

```bash
python3 -m compileall -q scripts
python3 -m unittest discover -s scripts -p 'test*.py' -v
python3 scripts/self_test.py
uvx ruff check scripts
npm ci && npm run build:indicator
```

Generate public verification and sharing assets:

```bash
python3 scripts/generate_test_report.py
python3 scripts/generate_growth_assets.py
python3 scripts/render_growth_media.py  # optional PNG/GIF, requires Chrome + ffmpeg
```

Useful references:

- [Architecture and safety invariants](DESIGN.md)
- [Atom IR reference](skills/accelerate-local-work/references/atom-ir.md)
- [Windows Preview contract](docs/WINDOWS_PREVIEW.md)
- [Benchmark and external-result protocol](BENCHMARKING.md)
- [Brand and compatibility guide](BRAND.md)
- [Contributing](CONTRIBUTING.md)
- [Release history](CHANGELOG.md)

## Help it grow

Try it on one real task, then share the sanitized result card or submit a benchmark. If the planner blocks work that should be safe, that report is just as valuable as a speedup—it identifies the next missing semantic rule.

[Report your first run](https://github.com/cloudguo123/atomlane/issues/new?template=first-run.yml) · [Open a benchmark report](https://github.com/cloudguo123/atomlane/issues/new?template=benchmark.yml) · [Ask a question](https://github.com/cloudguo123/atomlane/discussions) · [View the roadmap](ROADMAP.md)

[MPL-2.0](LICENSE) · [Licensing](LICENSING.md) · [Trademarks](TRADEMARKS.md) · [Privacy](PRIVACY.md) · [Terms](TERMS.md)
