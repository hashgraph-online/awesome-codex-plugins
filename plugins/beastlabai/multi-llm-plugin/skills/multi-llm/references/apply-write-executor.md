# The Python write executor (apply modes)

Read this only when an apply core's command for the phase carries `--exec-subagents`,
`--detach` or `--dry-run-subagents`; a command with none of `--exec-subagents`,
`--detach` and `--dry-run-subagents` never needs this file.

## The loop it runs

The executor runs the core's batch loop in Python, in one process: batches in
ascending `batch_index`, each one's snapshot/diff classification completed and
recorded **before** the next is dispatched, the prior-batch context bound late per
dispatch (the literal `{prior_changes_context}` token never reaches a runner),
`prior_changes.py append` and `metrics.py record` per batch, and the phase marked
completed only after every batch verified. The runner is `driver.subagent_runner` in
`providers.yaml`; write concurrency is `driver.max_concurrent_write_subagents`
(default **1**), pinned to 1 on the two suggestion modes, whose batches all edit one
artifact. apply-code-fixes' batches are partitioned by file, so it may be raised
there, and even then two batches co-schedule only when their declared file sets are
provably disjoint.

It also does the core's closing steps: the outcome block names every item the judge
decided, `{phase}/summary.md` gets the sections of the core's *Generate Summary
Report*, the decisions are overlaid onto the review report, and the run prints step
3's breakdown itself (batches ok/failed with duration and runner, the count applied,
each skipped item with its status, group id and reason). On apply-code-fixes it runs
`driver.verify_command` once after the last batch (the core's step 7), records the
result in `summary.md` and `.status.json`, and ends the phase at exit 3 when it fails.

## Its flags

- `--dry-run-subagents`: full preflight, **zero dispatch**. It renders the exact
  command per batch, applies the invocation profile, the co-scheduling admission
  check and the `driver.write_paths` policy, writes `{phase}/subagent_dry_run.json`
  and exits 0, having started no child and changed nothing else: report what that
  file holds. The recommended first unattended run on a new host.
- `--detach`: the phase self-daemonizes; it is how step 2 runs on this path.
  Per-batch progress lands in `{phase}/.status.json` under
  `progress.write_subagents`, so an unattended run is observable with no chat
  context. A host that resolves *run detached* to its own background mechanism uses
  that and never passes `--detach`.
- Rollback, when a batch half-applies: `multi_llm.py util restore-batch --phase-dir
  <dir> --task-id <id>` (or `--all-failed`), through the dispatcher like every mode.
  It restores exactly the files `{phase}/subagent_audit.jsonl` recorded as touched,
  from `{phase}/pre_batch/{task_id}/`, and **refuses** a file whose hash no longer
  matches what the audit recorded at completion unless `--force` is passed. A partial
  application never reverts itself: the run exits 3 naming this command, since a
  revert would destroy the half-applied state a human needs to inspect.
