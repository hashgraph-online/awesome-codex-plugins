---
name: optimize-python-parallelism
description: Analyze and, when the task authorizes source optimization, refactor a concrete long-running Python entrypoint containing repeated independent work. Use for explicit Python speedup or parallelization requests and evidence-backed long-running entrypoints; skip ordinary Python edits, test execution alone, short scripts, and projects that merely contain Python files.
license: MPL-2.0
---

# AtomLane Python Advisor

Improve a program only after separating three questions: where time is spent,
whether iterations are semantically independent, and whether the proposed
executor is likely to beat its overhead. A long runtime is a reason to inspect,
not proof that parallel execution is legal or useful.

## Keep analysis and execution separate

Use `python_parallel_advisor` for bounded source analysis. It reads strict
project-local UTF-8 Python, builds a conservative same-module call/effect
summary, and may return a source-hash-bound rewrite preview. It never imports
or executes target code and never changes files.

Read [references/python-program-ir.md](references/python-program-ir.md) before
interpreting or applying a candidate. It defines classification, proof gates,
GIL/spawn constraints, rewrite validity, and the verification certificate.

Call the advisor with:

- an absolute `project_path`;
- concrete `paths` when the entrypoint is known, otherwise bounded discovery;
- caller-observed hotspots only when they are real serial measurements;
- the actual `execution_context`, so an inner pool is not multiplied by an
  AtomLane or native worker pool;
- an explicit worker ceiling only as a ceiling, never as a safety override.
- `target_platform` when the optimized program will deploy somewhere other
  than the analysis host.

Do not run a workload merely to obtain a profile when repeating it may mutate
state, incur cost, or affect an external system.

## Treat each classification precisely

- `reviewable_rewrite` is the strongest static result, not a runtime proof.
  Its patch is still conditional on pickling, import, memory, correctness, and
  measured-performance checks.
- `advisory_only` identifies a plausible I/O, network, subprocess, or otherwise
  conditional opportunity. Explain the missing guarantees; do not apply its
  outline as an automatic transformation.
- `prefer_native` means vectorization or a library-owned worker pool should be
  considered before another Python pool.
- `already_parallel` requires one coordinated outer/inner resource budget.
- `blocked` remains serial until every hard blocker is removed by evidence or a
  semantics-preserving redesign. A confidence score cannot override a blocker.

If the current task does not authorize editing source, stop at advice. A
request to analyze performance alone does not authorize a refactor.

## Apply only a minimal, current rewrite

Before using a preview, recompute the source SHA-256 and require an exact match.
If source, runtime evidence, executor choice, or resource assumptions changed,
discard the preview and analyze again.

For the initial supported CPU pattern, preserve ordered map semantics with
`ProcessPoolExecutor.map`; require a module-level worker and a spawn-safe
`if __name__ == "__main__"` boundary. Do not move logging, file writes,
database work, randomness, environment reads, or unknown calls into speculative
workers. Keep exception, cancellation, result order, and deterministic merge
behavior explicit.

Choose by workload rather than syntax:

- pure Python CPU work: processes, after spawn and pickling review;
- blocking read-only I/O: bounded threads, after exception and resource review;
- established async call chains: bounded async tasks and cancellation design;
- NumPy, BLAS, OpenMP, PyTorch, and similar native kernels: vectorize or use
  their own workers, then cap outer concurrency;
- subprocess batches: prefer AtomLane task atoms with declared effects when
  source modification adds no value.

## Verify before claiming an improvement

After an authorized edit:

1. Compile the source without importing it.
2. Run focused unit/integration tests.
3. Differentially compare serial and parallel return values, ordering,
   exceptions, stdout/stderr, files, hashes, random seeds, and numeric tolerance.
4. Exercise process candidates with an explicit `multiprocessing` `spawn`
   context on every platform. Windows process pools have a 61-worker ceiling;
   treat it as an upper bound, not a useful default.
5. For safe repeatable work, compare multiple serial and parallel samples and
   report p50/p90, throughput, peak memory, worker count, and break-even size.
6. Revert only the newly proposed refactor if correctness fails or measured
   performance regresses; preserve unrelated user changes.

Use the existing AtomLane plan/execution path when several validation commands
are independently runnable, but treat a Python program that owns an inner pool
as one native-parallel compound atom unless the combined budget proves nested
concurrency safe.

Finish with a parallelization certificate containing the source and candidate
hashes, satisfied and unresolved proof obligations, executor/resource choice,
correctness evidence, measured or explicitly modeled benefit, limitations, and
rollback boundary. Never describe a modeled projection as measured speedup.
