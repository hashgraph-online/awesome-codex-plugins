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
caps or a measured serial baseline, may be supplied outside `compiled_plan`.
Any semantic change requires a new `atomic_task_plan` call.

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
`time_saved_seconds`, and `cumulative_saved_seconds`.

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

A supplied serial baseline supports a measured comparison. Otherwise label
savings and multiplier as estimates derived from observed atom durations; do
not rerun side-effecting work merely to benchmark it.
