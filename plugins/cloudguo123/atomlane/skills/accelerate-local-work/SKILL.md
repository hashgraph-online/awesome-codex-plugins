---
name: accelerate-local-work
description: Use AtomLane to compile and execute safe atomic parallel plans on macOS and native Windows Preview for worthwhile independent argv tasks, dependency DAGs, supported platform entrypoints, or Apple-silicon operators. Use at task start or an execution boundary when structured local work may contain two or more worthwhile units; skip plain answers, one quick command, and work whose effects cannot be safely bounded.
license: MPL-2.0
---

# AtomLane: Accelerate Local Work

AtomLane parallelizes only what is proven safe. Preserve task semantics first:
parallelism is legal only when the compiled
control flow, effects, resources, and authorization boundaries prove it safe.

## Perform a cheap preflight

Use this skill when at least one condition holds:

- A composite command, package script, Make target, Compose application, test
  suite, or build pipeline may contain independent work.
- One meaningful operation repeats across independent inputs.
- A dependency graph has two or more potentially ready nodes.
- A numerical, image, signal, ML, video, compression, or custom-GPU operation
  may use an Apple-silicon backend.

Skip it for conversation, web research, one quick command, tiny work dominated
by startup, or a known fully serial mutation. Evaluation should be cheap; the
possibility of parallelism alone does not authorize execution.

If the requested optimization requires changing a long-running Python program
rather than scheduling its existing commands, route to
`$optimize-python-parallelism` and `python_parallel_advisor`. Do not treat a
source rewrite preview as an executable atomic plan.

Identify the execution realm before compiling. Native Windows, one WSL distro,
and one Docker daemon are distinct resource and path spaces; never mix them in
one plan without an explicit bridge. On native Windows Preview, use exact argv
atoms or the whole-file `powershell_file` adapter. POSIX shell, package-script,
Make-recipe, and Compose lowering are not Windows semantics and must fail
closed. Do not lower inline PowerShell or `cmd`/`.bat` syntax.

## Compile once, execute the exact plan

For local execution covered by this skill, use this invariant:

```text
atomic_task_plan -> immutable compiled_plan + plan_hash -> atomic_exec
```

1. Call `atomic_task_plan` before the first execution batch. Supply the active
   project, task intent, and concrete entrypoints or candidate operations known
   at that point. Use `scenario_plan` first only when an unfamiliar multi-stage
   project, preset optimization profile, or explicitly requested trace evidence
   would materially improve planning.
2. Inspect the returned blockers, diagnostics, effect certainty, native
   delegates, resource plan, estimated benefit, and `plan_hash`. Do not execute
   a plan that reports an unresolved safety blocker.
3. Treat the complete return value as `compiled_plan`. Pass that exact object
   and its hash to `atomic_exec`:

   ```text
   compiled = atomic_task_plan(...)
   atomic_exec({
     "compiled_plan": compiled,
     "plan_hash": compiled["plan_hash"]
   })
   ```

4. Do not reconstruct, trim, reorder, or edit the compiled object. Do not
   change argv, cwd, environment, effects, edges, resources, executor choice,
   or retry policy between planning and execution. Optional execution-only
   output caps and `serial_baseline_seconds` may be supplied outside the plan.
5. If the task, entrypoint, project evidence, resource assumptions, or desired
   behavior changes, discard the old result and call `atomic_task_plan` again.
   A hash mismatch or stale precondition must fail rather than fall back to an
   unverified command.

Read [references/atom-ir.md](references/atom-ir.md) before handling a composite
shell/package entrypoint, Make or Compose graph, native test/build executor,
long-running service, formal benchmark, or proposed split/fusion. It defines
the effect, edge, lifecycle, transformation, and plan/hash contract.

## Preserve exact control flow

Exact mode is the default:

- Preserve `hard`, `success`, `failure`, `order`, `data`, `stream`,
  `after_ready`, `after_healthy`, `after_completion`, and `finally` as distinct
  relationships. Keep resource conflicts as leases or deterministic scheduler
  serialization, not fabricated source control flow.
- `a && b` is success-gated; `a || b` is failure-gated. Shell sequences and
  recipe lines are not a bag of independent commands.
- Do not speculatively run later diagnostics merely because they appear
  read-only. That changes fail-fast behavior unless the user explicitly asks
  for a non-equivalent run-all diagnostic mode supported by the planner.
- A daemon dependent waits for a declared ready or healthy event, not for the
  daemon to exit.

Never interpret an unknown effect as no effect. Unknown-effect atoms cannot be
parallelized, reordered, fused, cached, or automatically retried. Preserve the
original authorized entrypoint as one opaque serial compound atom only when
the planner proves that this retains its original boundary; otherwise stop and
report what evidence is missing. Do not repair uncertainty by guessing paths
or setting a side-effect flag to false.

## Delegate concurrency to semantic owners

Follow the executor and native-delegate decisions in `compiled_plan`:

- Let a sound Make graph own jobs through its jobserver. Recipe lines remain
  ordered, prerequisites are unordered unless constrained, and inferred file
  dataflow may add a safe edge when the source graph is incomplete.
- Let Docker Compose resolve profiles, service closure, health/completion
  conditions, one-shot jobs, and long-lived services. Prefer one compatible
  Compose operation over unrelated `compose up` processes.
- Let Vitest, Jest, pytest, compiler drivers, BuildKit, and similar tools use
  their native worker pools when their output and failure semantics are safer
  than external sharding.
- Shard only when outputs, reports, caches, databases, and temporary paths are
  isolated and the plan contains a deterministic merge.

A native delegate is a plan contract, not permission to recreate its inner
jobs with legacy executors. If the returned plan is not execution-eligible
because this installed executor cannot honor its delegate, lifecycle, or event
semantics exactly, stop and report the blocker. Do not translate it into
`parallel_exec`, `parallel_map`, or `parallel_dag`.

Budget native inner workers together with outer concurrency. Do not multiply
Vitest, BLAS, BuildKit, compiler, or GPU worker pools until the host is
oversubscribed. Repeated tiny atoms should be fused or delegated to a native
batch when doing so preserves control flow and reporting.

## Respect resources and evidence fences

The plan must account for file access modes and sidecars, Git state, database
scope, ports, containers, volumes, devices, external accounts, accelerators,
memory, and native worker capacity. Read/read sharing is usually compatible;
write/read and write/write overlap require ordering or isolation.

Formal timing, append-only evidence, post-candidate bytecode, and similar
project policies are first-class resources or prohibitions. Independent output
paths do not make a timing-sensitive benchmark safe to overlap. Relax such a
fence only when the user requests a correctness-only replay and the plan marks
the output ineligible for the original performance claim.

Parallelism changes timing, not permission. It does not authorize new commands,
mutations, external actions, retries, or destructive cleanup. Retry only atoms
the compiled plan marks idempotent and retryable.

## Match the current host

Use `host_resource_plan` and the fresh resource observations embedded by the planner. An explicit
concurrency value is a ceiling, not an override of safety limits. Interactive
mode should retain CPU and memory headroom and reduce work under existing load,
battery use, Low Power Mode, memory pressure, or thermal pressure.

On native Windows, every target runs below a kill-on-close Job Object. Optional
`cpu_rate_percent` and `memory_limit_mb` limits apply Job-wide.
`max_processes` is available only with `terminal_mode: pipes`, where the Job
active-member ceiling includes the verified supervisor and must be at least 2;
it is not a target-only allowance. Combining it with ConPTY fails closed because
console-host Job membership is not yet proven. If Job assignment
fails, do not start target code and do not fall back to killing only the direct
child. Use `terminal_mode: conpty` only when output-side terminal behavior is
required; it combines stdout/stderr into one VT stream. Explicit ConPTY `stdin`
fails before target creation because the Preview has no verified terminal-input
and EOF contract; use pipes for bounded stdin and observable EOF semantics.
Ordinary tasks retain separate pipes, while MCP/live-runner heartbeats still
provide real-time elapsed, state, and saving updates.

For numerical or media implementation work, call `mac_accelerator_plan` before
choosing an Apple backend. On a non-macOS host it is explicitly unavailable:

- Accelerate/BNNS for suitable CPU-vector math, DSP, image, and neural-network
  operators.
- Core ML with all compute units for compatible inference.
- MLX or PyTorch MPS for compatible tensor workloads.
- Metal or MPSGraph for large custom data-parallel operators.
- VideoToolbox-backed codecs for supported media work.

Hardware availability does not prove that a program uses it. The invoked code
must implement or expose the backend. GPU, ANE, media engines, unified memory,
and memory bandwidth are shared; accelerator fan-out is normally low.

For container budgeting, use `container_resource_plan` when useful, but keep
the generated budgets inside a newly compiled plan. On Docker Desktop, allocate
from the identified Linux VM/daemon envelope. A cpuset identifies VM vCPUs,
not stable physical host cores. Native Windows, WSL, and the Docker Linux VM
must never share one inferred capacity. Windows-container or unavailable-daemon
results remain advisory rather than directly applicable.

## Keep long execution visibly live

For a plan expected to run longer than ten seconds, live display is mandatory.
Do not await `atomic_exec` as one blocking MCP call in Codex Desktop.

1. Place the exact `atomic_exec` arguments—unchanged `compiled_plan`, matching
   `plan_hash`, and only documented execution-only options—in a JSON file under
   the active workspace's `work/` directory.
2. Resolve this installed plugin's root and run:

   ```text
   python3 scripts/live_runner.py --mode atomic --input <absolute-json-path>
   ```

   through `exec_command` in a PTY, with the initial yield no longer than one
   second.
3. Poll the session with `write_stdin` about every five seconds. After each
   poll, send a short user-visible update with elapsed time,
   running/ready/completed/failed counts, and current estimated time saved.
4. Continue until `LIVE_RESULT_JSON=` and the process exit code arrive. Do not
   substitute a hand-built legacy exec/map/DAG payload for the compiled atomic
   plan.

For shorter work, a direct `atomic_exec` call is acceptable when it does not
hide meaningful progress.

## Verify and report the result

A successful scheduler call proves transport success, not task success.
Inspect every atom's status, return code, stderr, timeout, skip reason, and
truncation flags. Downstream work whose typed dependency failed must not run.

Start the final execution report with the returned compact indicator, such as
`⚡ 并行｜峰值 8 路｜估算 5.42×` or
`→ 串行｜峰值 1 路｜估算 0.98×`. Then report:

- elapsed time and observed peak concurrency;
- failed and skipped atom IDs and output locations;
- `time_saved_seconds` for this invocation;
- `cumulative_saved_seconds` across completed invocations.

When `serial_baseline_seconds` is supplied, label the comparison measured.
Otherwise label multiplier and savings estimated from observed non-skipped atom
durations. Never rerun side-effecting work merely to benchmark it, and never
present an estimate as a controlled benchmark.
