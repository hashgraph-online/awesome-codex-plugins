# The Python write executor (implement)

Read this only when implement's step-2 command carries `--exec-subagents`, `--detach`
or `--dry-run-subagents`; a command with none of `--exec-subagents`, `--detach` and
`--dry-run-subagents` never needs this file.

## The loop it runs

The executor runs steps 5 to 10 in Python, in one process:

- batches in ascending `batch_index`, each batch's snapshot/diff verification
  completed and recorded **before** the next is dispatched (a partial application is
  never compounded by a concurrent one);
- tasks inside a batch dispatched together only when all three of `can_parallelize`,
  `driver.max_concurrent_write_subagents > 1` (default **1**) and a dispatch-time
  check that their declared file sets are pairwise disjoint agree — a task declaring
  no file set runs alone;
- the human-task strategy resolved **once** from `--force-strategy`, the value
  persisted in `state.json` on a resume, or `--yes`'s `skip-dependents` default, then
  applied as a graph walk: `skip-dependents` propagates transitively over
  `depends_on`, `skip-continue` records a dependency override per unblocked task,
  and `pause-and-ask` exits 3 naming both `--human-task <id>=done|skip`
  re-invocations rather than blocking on a stdin nobody is on;
- `prior_changes.py append`, `metrics.py record` and `update_task_status` per task;
- and finalization — `metrics.py finish`, `mark_phase_completed`,
  `finalize_tracking.py`, the implementation summary (with its
  `## Manual Tasks (Deferred)`, `## Dependency Override Warnings` and `## Cancelled`
  sections) and `insert_implementation_summary_reference`. A run that dispatched
  every batch and produced none of those is a **failed** run, not a partial one.

## On a stop

A partial application halts at the batch boundary, keeps every pre-batch snapshot
under `{phase}/pre_batch/{task_id}/`, leaves the phase **not** completed, and exits 3
naming the exact re-invocation plus the rollback command
(`multi_llm.py util restore-batch --phase-dir <dir> --task-id <id>`, which refuses a
file that changed after the run unless `--force`). `--resume` then re-dispatches only
the unfinished batches, replaying the prior-changes log from disk so the resumed
batch sees the context an uninterrupted run would have. The stop message, the
`## Cancelled` section of `summary.md`, `write_batch_report.json` (`not_run_tasks`,
`stop`) and the status mirror (`not_run_task_ids`) account for every task of the
decomposition — done, failed, not run (the stop came before they were dispatched),
accepted after failing, completed by hand, skipped at your request, skipped with a
skipped task, deferred manual — and the message names the way forward: for a failed
check (a task that declares no files), fix what it reported (by hand, or review-code
then apply-code-fixes) and `--resume`, which runs the check again and the tasks after
it; or accept the failure with `--human-task <id>=done` (`skip` leaves it and its
dependents undone, whatever the human-task strategy; a `--resume` after that keeps
them skipped). A `--resume` that changes nothing does not run a failed check
again: when the files git sees have the same sizes and timestamps as when it failed
(`verdict.tree_fingerprint` on its result file), the stop is repeated with the remedy
and no dispatch is spent; `--human-task <id>=retry` runs it anyway. A stop after a
code task of the phase completed, with no `driver.verify_command` configured, also
says what ran the repository's tests, if anything did, and that the plugin ran none
(its log, `notice` and `summary.md`, and at the end of the stop's own line, the
result's `error`), as a finished run does.

A check that ran and reported problems (`check-findings`, also from a reply that said
`failed` but listed findings and not `could_not_run`) is not a stop: the tasks that
do not depend on it run. The tasks that depend on it, directly or through another
task, are not run — each is recorded `not run — upstream check <id> reported
problems` in `state.json`, `summary.md` (`## Not Run: Upstream Check Reported
Problems`), `write_batch_report.json` (`blocked_by_check`, `not_run_tasks`, `stop`)
and `status` — and once every other task has run, implement ends needing a human
(exit 3, the phase not completed) with the same three ways forward: fix the code and
`--resume`, accept the findings with `--human-task <id>=done` (the waiting tasks run,
their prompts say the findings were accepted, and the findings stay listed for
review-code), or `--human-task <id>=skip`.

## Preflight and detach

`--dry-run-subagents` renders every command, applies every admission and policy
check, writes `{phase}/subagent_dry_run.json` and starts no child: report what that
file holds. `--detach` self-daemonizes the phase and reports per-task progress in
`{phase}/.status.json` under `progress.write_subagents`; it is how step 2 runs on
this path. Never combine it with a host's own background mechanism, whichever
*run detached* resolves to for your host.
