# Python program parallelism contract

Use this reference when `python_parallel_advisor` is analyzing source or when a
returned rewrite is being reviewed, applied, or verified.

## Candidate IR

Each candidate is bound to a project-relative source path, SHA-256, AST span,
recognized pattern, same-module worker symbol, workload class, effect set,
proof obligations, blockers, resource ceiling, benefit evidence, and optional
unified diff. Candidate and analysis hashes are deterministic and change when
the relevant source or options change.

The advisor currently recognizes these ordered-map shapes:

```python
results = [worker(item) for item in items]
```

```python
return [worker(item) for item in items]
```

```python
results = []
for item in items:
    results.append(worker(item))
```

The loop must have one generator/statement, a simple loop variable, a direct
same-module call with one matching argument, no filter or loop `else`, and no
additional control flow. `executor.map` is used because it preserves input
result order.

## Classification and proof

`classification` is one of:

- `reviewable_rewrite`: no explicit effect found by the bounded same-module
  analysis for the supported CPU shape, a materialized/replayable iterable,
  module-level worker, linked main guard, standalone budget, and a syntax-valid
  source-hash-bound diff;
- `advisory_only`: plausible transformation whose I/O, rate-limit, exception,
  cancellation, subprocess, or resource semantics require design review;
- `prefer_native`: detected native/GIL-releasing work where vectorization or a
  native worker pool is usually the semantic owner;
- `already_parallel`: the module already exposes pool/async/native concurrency;
- `blocked`: an unresolved worker, observable effect, dependency, spawn issue,
  dynamic feature, tiny item set, complex enclosing control, or nested budget.

`proof_level` is independent of the numeric confidence. Hard semantic effects
always win over I/O, network, subprocess, or native advisory classification.
Process-specific spawn, binding, import, iterable, source-boundary, and resource
gates must all clear before a CPU candidate becomes `reviewable_rewrite`; the
same unresolved conditions remain visible as review blockers on advisory/native
candidates but never authorize a patch. Even `bounded_static_candidate` leaves runtime types, magic-method
dispatch, picklability, safe third-party imports, memory fit, exception
equivalence, and useful speedup unresolved.

Effects that fail closed include global/nonlocal or escaping writes, augmented
state updates, file writes, database operations, logging/printing, randomness,
time/UUID dependence, reflection/dynamic execution, generators, nested
functions, unknown calls, and dynamic call targets. Network, subprocess, and
read-only I/O remain conditional advice rather than automatic rewrites.

## Python executor rules

- Threads do not normally accelerate pure Python CPU bytecode because of the
  GIL. They can help blocking I/O and some native calls that release the GIL.
- CPU-bound Python workers normally require processes. On every supported
  target, spawned workers must be import-safe; the callable must be module-level and its
  arguments/results pickleable, and process creation must sit behind a safe
  main-entry boundary. Generated previews explicitly request the `spawn`
  context so Linux validation exercises the same import contract. Windows
  `ProcessPoolExecutor` plans must not exceed 61 workers.
- NumPy/BLAS/OpenMP, PyTorch, JAX, image/video codecs, and similar libraries may
  already own threads or devices. Do not multiply their pools by outer process
  concurrency without one CPU/memory/GPU budget.
- Async fan-out changes cancellation and exception aggregation. Use bounded
  task groups/semaphores only when the call chain is already async and its
  failure contract is understood.
- Reductions require an explicit associative/commutative rule and stable merge.
  Floating-point reassociation can change results and is not covered by the
  ordered-map rewrite.
- Random workloads require deterministic per-item seeds, not a shared global
  RNG stream.

## Rewrite contract

A `rewrite_preview`:

- is text for review, never an instruction to apply automatically;
- is valid only while `source_sha256` matches exactly;
- inserts collision-resistant executor and multiprocessing aliases, an
  explicit spawn context, and a bounded worker ceiling;
- must compile before it is surfaced;
- owns complete physical source lines and preserves comments, encoding/shebang
  placement, and final-newline state;
- does not authorize new dependencies, commands, execution, or external side
  effects;
- becomes stale after any relevant source or planning change.

After a patch is applied, analyze the new source again. The rewritten program
is then executed as an ordinary AtomLane atom; the static candidate is not
converted into imaginary command-level atoms.

## Benefit evidence

- `not_estimated`: no observed serial hotspot was supplied. Do not invent a
  speedup or time-saving value.
- `not_applicable_until_safety`: the candidate is blocked, advisory, native
  owned, or otherwise ineligible for a CPU-process projection; retain any
  observed serial fact but do not publish projected parallel time or savings.
- `measured_serial_modeled_parallel`: serial wall time was supplied by the
  caller, while parallel time is an Amdahl/overhead projection. Label only the
  serial value measured.
- A final measured claim requires repeatable serial and parallel runs of the
  same input, correctness success, environment/worker metadata, p50/p90,
  throughput, peak memory, and a stated break-even size.

Never benchmark non-repeatable or externally mutating work merely to improve a
performance claim.

## Verification certificate

Record:

- analysis hash, candidate ID, source hash, and applied patch ID;
- satisfied, failed, and unknown proof obligations;
- input identity and deterministic seed policy;
- executor, worker count, outer/native worker caps, and memory budget;
- compilation and test results;
- differential return/output/file/exception evidence and numeric tolerance;
- serial/parallel measurement method, samples, p50/p90, throughput, memory,
  speedup, time saved, and whether each value is measured or modeled;
- limitations, stale-source check, and the exact rollback boundary.
