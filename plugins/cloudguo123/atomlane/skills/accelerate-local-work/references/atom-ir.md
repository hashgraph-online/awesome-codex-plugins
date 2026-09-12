# Atomic Plan Contract

This reference defines the safety and semantic contract for the v2 atomic
planner and executor. Read it when a task contains a composite shell command,
package script, Make target, Compose application, test suite, build pipeline,
long-running service, or a proposed split/fusion transformation.

The planner is a compiler. It must preserve the observable behavior of the
requested entrypoint unless the user explicitly authorizes a different mode.
The executor consumes the compiled artifact; it does not reinterpret source
commands or repair an incomplete plan.

## Compilation boundary

```text
task intent + entrypoints + project evidence
                    |
                    v
            atomic_task_plan
                    |
                    v
       immutable compiled_plan + plan_hash
                    |
                    v
              atomic_exec
```

Treat the complete `atomic_task_plan` result as an opaque `compiled_plan`.
Invoke `atomic_exec` with both that exact object and its returned `plan_hash`:

```text
compiled = atomic_task_plan(...)
atomic_exec({
  "compiled_plan": compiled,
  "plan_hash": compiled["plan_hash"]
})
```

Do not copy selected fields into a new object, reorder atoms, edit argv or
environment values, add dependencies, weaken effects, or recompute the hash.
Optional execution-only limits documented by `atomic_exec`, such as output
caps or an ordinary-task measured serial baseline, may be supplied outside
`compiled_plan`. Native pytest pools reject bare baseline seconds and instead
consume session-attested evidence from a matching serial plan. Any semantic
change requires a new `atomic_task_plan` call.

The hash is a time-of-check/time-of-use boundary. A missing hash, mismatch,
unsupported plan version, changed project evidence, or failed execution
precondition must stop execution rather than fall back to an unverified plan.

The v2 hash also binds a platform contract: OS family, native/WSL/container
realm, architecture, path flavor, argv transport, process-tree backend, and
required terminal modes, including whether ConPTY stdin is available, plus
resource-control semantics. A plan compiled for macOS, native Windows, WSL, or
a different architecture must be recompiled in its execution realm.

## Atom model

An atom is the smallest operation for which the planner can state a complete
semantic contract. It is not necessarily one process, one source line, one
test file, or one container.

Each executable atom needs enough information to establish these dimensions:

| Dimension | Required meaning |
| --- | --- |
| Operation | Exact argv transport, cwd, environment delta, stdin/terminal policy, process-tree resource limits, and operation kind |
| Control | Conditions under which it may start: hard/success/failure/order/data/stream, finally, or a lifecycle event |
| Artifacts | Inputs and outputs, including access mode and relevant sidecars |
| Resources | Capacity or exclusivity requirements such as CPU, memory, ports, database scope, volume, lock, device, or host timing |
| Lifecycle | Bounded process, one-shot initializer, daemon, supervisor, or native compound executor |
| Semantics | Determinism, idempotence, retryability, cacheability, failure behavior, and ordering sensitivity |
| Policy | Authorization, provenance, formal-evidence, post-candidate, or other task-specific fences |
| Cost | Estimated duration, memory, nested worker demand, and startup overhead when known |

For pipe mode, `operation.stdin` is optional UTF-8 text capped at 1 MiB. Its
exact value—including the distinction between omission and an empty string—is
part of the canonical plan hash. The executor writes the bounded payload and
then closes the pipe so EOF is observable. Explicit ConPTY stdin, including an
empty string, is rejected before target creation.

### Artifact effects

Do not collapse all filesystem activity into a `writes` boolean. The 0.9
`accesses[].mode` vocabulary is exact:

| Mode | Contract |
| --- | --- |
| `read` | Reads existing content or directory membership without mutation |
| `snapshot` | Reads content that is also an execution precondition |
| `create` | Creates a path in a namespace proven disjoint from other writers |
| `append` | Adds to an existing artifact without replacing it |
| `overwrite` | May replace all or part of an existing artifact |
| `delete` | Removes a path or subtree |
| `transaction` | Owns a multi-path or replace-style update as one effect boundary |

`unknown` is an effect-assurance state, not an access mode. Metadata-only
mutation is represented as an effect in an appropriate domain; an atomic
replacement is a `transaction` and must include its deterministic temporary
path or namespace. For example, two writers of `result.csv` that both use
`result.csv.tmp` conflict even if the final rename is atomic. Resolve relative
paths against the atom's cwd, account for path ancestry and known globs, and do
not assume a symlink target or a dynamically constructed path is harmless.

Read/read sharing is normally compatible. Write/read and write/write overlap
are ordered or isolated. Append is concurrent only when the owning format and
writer provide a proven synchronization protocol. `create` outputs are
compatible only when their namespaces are disjoint.

Non-filesystem effects use `effects[]` with a `domain`, `key`, and one of
`read`, `write`, `append`, `transaction`, `lease`, or `consume`. Effect
assurance is independently one of `complete_declared`, `complete_static`,
`partial`, or `unknown`; only the complete states are execution-eligible.

### Logical resources

Resources may be mutexes, reader/writer locks, or capacity constraints:

- Git index and refs
- database server, database, schema, table, or migration authority
- TCP/UDP port leases
- Docker project, container name, named volume, or BuildKit capacity
- external account or rate-limit bucket
- GPU, ANE, media engine, memory bandwidth, or accelerator slot
- native test-runner worker pool
- formal benchmark host and timing-validity fence

Do not treat Docker `cpuset` as stable physical-host affinity. Docker Desktop
schedules Linux vCPUs inside its VM, which is distinct from native Windows,
macOS, or a WSL distro.

## Edge semantics

Keep different dependencies typed. The 0.9 dependency vocabulary is:

| Kind | Meaning |
| --- | --- |
| `hard` | Required predecessor; downstream needs successful completion |
| `success` | Downstream runs only when the predecessor succeeds |
| `failure` | Downstream runs only when the predecessor fails |
| `order` | Completion order without success gating |
| `data` | Producer output is a consumer input and must succeed |
| `stream` | Producer/consumer streaming contract owned as one preserved boundary |
| `after_ready` | Dependent starts after a service-ready event |
| `after_healthy` | Dependent starts after a declared health event |
| `after_completion` | Dependent starts after successful one-shot service completion |
| `finally` | Cleanup or reporting runs after termination regardless of outcome |

Resource conflicts are not forged into source dependencies. The planner emits
deterministic `resource_serialization` schedule edges while the executor also
checks live access/effect conflicts and capacity claims.

`a && b` creates `success`; `a || b` creates `failure`; sequential shell or
Make recipe lines create `order`. A pipe is a `stream` compound operation
unless a frontend can preserve producer, consumer, backpressure, exit-status,
and signal semantics explicitly.

Exact mode is the default. Do not speculate across success/failure edges or
turn fail-fast validation into run-everything diagnostics. If a future mode
permits speculation, it must be explicit in the plan and visibly reported as
different observable behavior.

## Unknown effects fail closed

Unknown never means empty, read-only, independent, deterministic, or safe.

An atom with an unresolved effect is ineligible for parallel fan-out, fusion,
caching, automatic retry, or reordering. The planner may preserve the original
authorized entrypoint as one opaque serial compound atom only when doing so
retains its original control flow and isolation boundary. If even that boundary
is unknown, planning must return a blocker and `atomic_exec` must not run it.

Do not repair unknown effects in the caller by guessing paths or setting
`side_effect=false`. Supply additional evidence and replan.

## Frontend rules

### Shell and package scripts

Parse shell syntax rather than splitting text on separators. Preserve quoting,
redirection, cwd changes, environment assignments, substitutions, pipelines,
background processes, traps, and exit-status behavior. Recursively expand
package scripts with a depth/node budget and cycle detection. Keep lifecycle
hooks and the selected package-manager semantics intact.

A script such as `prisma migrate deploy && next start -p 3001` is a database
mutation followed by a daemon that leases port 3001. A health-dependent smoke
test waits for readiness, not for the server process to exit.

This frontend is POSIX-specific. Native Windows Preview does not reinterpret
it as PowerShell or `cmd.exe`. A supported PowerShell entrypoint is one
snapshotted `.ps1` file invoked by PowerShell 7 with `-File`; it remains one
atom and requires complete declared effects. Inline PowerShell, Windows
PowerShell 5.1, `.cmd`, and `.bat` lowering fail closed.

Windows file resources recognize drive, UNC, and extended-path forms before
logical resource schemes. Drive-relative paths such as `C:output.txt` are
ambiguous and rejected. Case/slash aliases, parent-child overlap, and alternate
data streams conflict conservatively.

### Make

Make prerequisites are unordered unless the Make graph says otherwise;
recipe lines within one target remain ordered. Preserve variables, target-
specific environment, recursive Make, phony targets, order-only prerequisites,
and native jobserver ownership.

Infer artifact edges when reliable evidence exposes them. If inferred dataflow
contradicts a Make graph, add the safe ordering to the compiled plan and emit a
diagnostic. Do not blindly use `make -j` on a graph known to be incomplete.
Literal Python CLI recipes may be inspected with a bounded, non-importing AST
pass that relates argparse path defaults or literal overrides to selected
read/write sinks. Treat unsupported syntax, aliases, or dynamic paths as no
evidence; the recipe remains partial and native/opaque rather than being
promoted to an executable exact atom.
When Make already owns a sound graph, emit a native Make delegate and budget
outer concurrency to avoid nested oversubscription. Do not lower its graph into
independent subprocess atoms merely to make it executable. If the installed
executor cannot honor a returned native delegate exactly, that plan remains
advisory and execution fails closed.

### Docker Compose

Resolve the selected profiles and service closure. Preserve the difference
between `service_started`, `service_healthy`, and
`service_completed_successfully`. Model fixed host ports, container names,
volumes, database migration authority, one-shot initializers, health checks,
restart policy, and long-lived service leases.

Prefer one native Compose operation for a compatible service set. Do not turn
each service into an unrelated `docker compose up` process. If lifecycle event
handling is unavailable, the plan must stop at the native-delegate boundary
instead of pretending that process exit means readiness. BuildKit may share
layers, but identical context alone does not prove two image outputs or build
arguments are interchangeable.

### Tests and builds

Vitest, Jest, pytest, compiler drivers, BuildKit, and similar tools may already
own an internal worker pool. Represent them as exact native invocations or
native compound delegates when that preserves semantics and avoids multiplying
worker pools. External sharding is legal only with disjoint
output/report/cache paths and an explicit deterministic merge. Coverage
directories, JUnit files, compiler build-info files, and build caches are
effects, not incidental implementation details.

Tests that share a database need isolated databases or schemas per shard.
Skipped tests remain skipped evidence and must be reported; they are not
equivalent to executed passing tests.

The pytest native-worker frontend keeps one selected suite as one outer atom
and delegates collection, fixtures, independent-case scheduling, and worker
lifecycle to pytest-xdist. A suite of 100 decoupled cases is therefore not 100
external AtomLane processes. The compiled plan binds the exact runner prefix,
selectors, xdist worker count and distribution, per-run base-temp and hash-bound
JUnit paths, effective configuration and caller-selected source snapshots,
suite timeout, declared effects, and shared CPU/memory claims. The effective
project-local config is passed with `-c`; valid config `addopts` and
`PYTEST_ADDOPTS` remain active and their exact tokens are bound into the
selection fingerprint. A plain `pyproject.toml` selected only as pytest 8.4's
rootdir fallback is bound as `config_selection_kind=fallback_pyproject` and is
accepted at runtime only while it remains free of pytest configuration.
Ambiguous discovery requires `config_path`, and Python
3.10 requires importable `tomli` for `pyproject.toml`. AtomLane owns its pytest
controls and rejects conflicting worker/output/non-executing/plugin controls.
Selectors, config `testpaths`/`pythonpath`, and explicit snapshots must be
existing project-local paths whose lexical and final identities agree; links
are rejected and all paths are revalidated before launch. A link discovered
inside the audited collection tree makes serial-baseline coverage false. The exact argv includes
`--confcutdir=<project_root>` to prevent pytest from executing conftests above
the declared project boundary. AtomLane explicitly loads xdist even
when plugin autoloading is disabled, disables the shared pytest cache provider,
and rejects cache-dependent selection options. Unknown third-party pytest
options that consume values must use `--option=value`; separated values are
ambiguous with positional selectors.
JUnit and base-temp paths cannot overlap snapshotted inputs, the config, the
runner executable, or each other. Explicit JUnit output must also remain
outside every selected collection directory in every suite; the default uses a
unique system temporary path. Compilation and runtime compare this boundary in
both cross-suite directions using a case-folded, Unicode-NFC identity plus
physical ancestor/file identities for firmlink and mount aliases. Existing
reports must be single-link regular files. Windows
explicit report paths also reject trailing-space/dot aliases, alternate data
streams, reserved devices, and device namespaces. `worksteal` is the independent-case default, while grouped
schedulers are fixture-affinity opt-ins. pytest-xdist is required by both the
serial-baseline and multi-worker routes. The 0.16 release gate covers
`macos-14` and `windows-2025`, CPython 3.10–3.13, pytest 8.4.2, and
pytest-xdist 3.8.0; other dependency versions are not part of that verified
claim.
At runtime, every JUnit and base-temp path is a separately keyed lease resource.
The executor globally sorts and acquires non-blocking cross-process leases,
revalidates the plan while holding them, and releases only after stable report
parsing and evidence generation. A collision fails fast rather than entering
the measured execution interval. Every output contributes a normalized path
key, a physical parent-plus-basename key, and an existing-target key; the full
set is recomputed while held. Windows constructs the private lease root from
the profile directory bound to the current process token, independent of
profile environment variables.

The runner prefix must use an exact Python `-m pytest` module invocation;
direct `pytest` and `py.test` console scripts are rejected. AtomLane preserves
the selected virtual-environment invocation path while hash-attesting and
revalidating its resolved interpreter, forces
`PYTHONPATH`/`PYTHONHOME`/`PYTHONOPTIMIZE` empty, and rejects
project/config-pythonpath candidates that could shadow the trusted `pytest` or
`xdist` modules. The optimization reset also keeps ordinary assertions outside
pytest's rewrite boundary semantically active. The selected environment and installed packages
remain caller-trusted rather than becoming part of AtomLane's trust root.

Compilation must not run a hidden `pytest --collect-only`, import a test module,
or install pytest-xdist. Complete file and non-file effect declarations plus an
explicit `independence_declared=true` assertion remain a multi-worker execution
precondition; a count hint is not independence evidence. A serial baseline can
be attested only when every suite sets
`baseline_source_closure_declared=true`, supplies `snapshot_paths` covering
every semantically relevant selected test, source, helper, project-local plugin, and
`conftest`, and passes AtomLane's bounded static coverage checks. The effective
pytest config is bound and snapshotted separately. Static checks cover direct
selectors, configured paths, and discoverable `conftest` files, but cannot prove
closure over dynamic imports or plugin loading. The declaration is therefore a
caller assertion and the attestation describes execution over that declared
closure, not proof of complete semantic closure. Worker capacity is not CPU
affinity: xdist and the operating system schedule the worker processes, and the
plan makes no physical-core placement claim.
Installed pytest/xdist distributions and plugins outside the project are not
content-attested; the caller must keep that trusted environment unchanged
between the attested serial run and its parallel comparison.

Native-pool reporting keeps configured and observed evidence separate.
`native_workers_configured` is hash-bound configuration;
`outer_peak_concurrency` is the observed AtomLane atom count; and
`native_workers_observed` is unavailable without compatible runtime
instrumentation. Neither a case-count hint nor JUnit testcase count proves the
number of worker processes actually active. Native-pool parallel efficiency is
therefore also unavailable until inner-worker activity is observed.

## Legal transformations

A transformation is legal only when its proof obligations are present in the
compiled plan:

- Parallelize atoms whose control/data predecessors are satisfied and whose
  leases and artifact effects are compatible.
- Fuse tiny atoms only when their combined control flow, failure reporting,
  environment, and authorization remain equivalent.
- Shard a loop only when each shard has disjoint outputs and deterministic
  inputs; merge in a stable canonical order.
- Cache only deterministic, cacheable atoms whose declared inputs and execution
  environment are part of the cache key.
- Retry only idempotent, retryable atoms. Never infer retryability from a zero
  exit code or an atomic file rename.
- Preserve timing/provenance fences. A correctness-only replay may relax a
  timing fence only when the user requests it and outputs are marked ineligible
  for the original performance claim.

The scheduler should release an atom as soon as its own typed predecessors and
leases permit; it should not wait for an unrelated stage-wide barrier. Allocate
one hierarchical concurrency budget across outer processes and native inner
workers.

At execution, the invocation-local ready set is compiled into one conflict-free
ordered admission batch before consulting host capacity. `atomic_exec` submits
that batch to a shared cross-process ledger under one state lock. Generic
worker, CPU, memory, and accelerator claims are host-wide; project artifacts,
typed effects, and control edges remain plan-local semantic contracts. The host
layer may admit a subset for capacity or fair sharing, but it must not reorder,
rewrite, or invent atoms. It may restore capacity after pressure clears only up
to the immutable compiled envelope.

Native macOS/Windows, WSL, and Docker daemon/VM capacity are distinct ledgers.
The host coordinator is not evidence of CPU affinity, native-worker observation,
or containment of broker-created work.

## Reference acceptance cases

These cases are useful forward tests for planner changes:

1. `lint && typecheck && build && test` remains a success-gated chain in exact
   mode.
2. TypeScript reading `.next/types/**` conflicts with a Next build writing
   `.next/**`, even when `tsc` uses `--noEmit`.
3. Two CI Vitest invocations writing the same JUnit path conflict; one native
   Vitest invocation may use its own workers.
4. A Make aggregate that lists calibration, validation, and report as siblings
   is reordered into a data chain when the latter commands consume the former
   commands' default outputs.
5. Two `latexmk` invocations with distinct job names may share one output
   directory; identical job names conflict.
6. A formal single-thread benchmark owns an exclusive timing-validity lease
   even when its result files are disjoint from other work.
7. A Compose database migration waits for PostgreSQL health; an application
   waits for migration completion and its backend's health.
8. A post-candidate policy may forbid bytecode generation entirely rather than
   merely forcing it to run serially.

## Execution reporting

For a run expected to exceed ten seconds, execution must remain visibly live.
Show elapsed time, running/ready/completed/failed counts, and current estimated
time saved during execution. At completion report observed peak concurrency,
elapsed time, failures and skips, output locations, per-invocation
`time_saved_seconds` with `measured_time_saved_seconds` or
`estimated_time_saved_seconds`, credit eligibility/write status, primary
`cumulative_saved_seconds`, and separate
`cumulative_estimated_saved_seconds`.

On native Windows, ordinary tasks use separate pipes below a kill-on-close Job
Object. Optional CPU-rate and job-memory limits cover the supervisor plus the
normally inherited target tree. In pipe mode, `max_processes` is the exact
Job-wide active-member ceiling (minimum 2) and includes the supervisor; it is
not a target-only allowance. ConPTY with `max_processes` fails closed because
console-host Job membership is not proven, while ConPTY with CPU or memory
limits remains supported. ConPTY reports one combined VT stream; MCP and
live-runner progress do not require it. Explicit ConPTY stdin fails before
target creation because no verified terminal-input and EOF contract is
implemented; use pipes for bounded stdin.

A supplied serial baseline supports a measured comparison for ordinary work.
Otherwise label savings and multiplier as estimates derived from observed atom
durations for ordinary multi-atom execution. A native pytest pool rejects bare
seconds. A measured comparison requires session-attested evidence from a
matching `worker_count=1` run plus a fresh parallel JUnit whose non-empty,
passing, counter-consistent testcase identities and outcomes match. Issuance
also requires `baseline_source_closure_declared=true` and a passing bounded
static coverage check; this attests only the caller-declared source closure.
Without that attestation, only complete, runtime-plausible testcase durations
from the fresh validated JUnit may form an explicitly estimated comparison.
Otherwise savings remain pending and are not credited to the cumulative
ledger. Estimated observations are recorded only in the estimated bucket.
Ledger v2 defines the compatible primary cumulative total as new measured
credits plus pre-v2 `legacy_unclassified` values; it never reclassifies that
history as measured or overwrites an invalid existing ledger. Do not rerun
side-effecting work merely to benchmark it.
