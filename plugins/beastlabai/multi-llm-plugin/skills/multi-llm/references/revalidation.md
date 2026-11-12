# Revalidation (apply-suggestions, apply-code-fixes)

Read this only when an apply core sends you here, in one of two cases:
- **Failed items to recover:** validation left items `validation_failed`
  (`summary.validation_failed_count` above 0). No marker prints for these until
  a retry is requested. Start at *When validation fails*.
- **Revalidation pending:** a run with `--revalidate` (or `--revalidate-model`)
  printed `[REVALIDATION_PENDING]` or `[REVALIDATION_BATCHES_PENDING]`. Start at
  *Running the revalidation subagents*.

A run with no item `validation_failed` and neither `[REVALIDATION_PENDING]` nor
`[REVALIDATION_BATCHES_PENDING]` printed never needs this file.

The core names two values: `{mode}`, the apply mode you are running
(`apply-suggestions` or `apply-code-fixes`), and `{review}`, the review phase
directory it reads (`review-plan` or `code-review`).

**Commands.** This file is read as it is, so its commands are spelled from the
mode word on: `<prefix>` stands for the dispatcher prefix every command in the
core starts with (`uv run … --project "<skill dir>" -- python "<skill dir>/multi_llm.py"`,
flags and paths exactly as the core prints them). Copy it from any command in
the core, unchanged, and run each command bare, as the core runs its own.

## When validation fails

If validation left items `validation_failed` (parse errors, timeouts, rate
limits), the two ways forward are these. Offer them; run one only when the
user picks it or the run's own flags already chose it.

```bash
# Option 1: re-run validation on the failed items, here with a different model
<prefix> {mode} --plan-file "$PLAN_PATH" --revalidate --revalidate-model cursor-agent:opus

# Option 2: bulk approve the validation failures (if you trust the items)
<prefix> {mode} --plan-file "$PLAN_PATH" --approve-validation-failed
```

## Running the revalidation subagents

A run with `--revalidate` prints a revalidation marker and exits 0 without
applying anything: the batches below are yours to run.

### The task file

`revalidation_tasks.json` (in `{plan}/{review}/`) carries `tasks_schema_version: 2`
and one complete task per batch under `batches`, each with `prompt`,
`output_name`, the derived `output_path`, `prompt_path` and `prompt_lines`,
`result_channel: file`, `context_mode`, `capability_tier`, `executor_role` and
`task_id`. The sidecar at `prompt_path` holds exactly the bytes of `prompt`
(`prompt_lines` is its line count), so the two are interchangeable and a host that
would otherwise re-emit the whole prompt can point the subagent at the file
instead. The context excerpt and this batch's item records travel **inside**
`prompt`; `item_indices` and `original_validation` stay on the file for the merge
step.

- **apply-suggestions**: a plan within the inline limit is complete in `prompt`
  (`context_mode: inline`). A larger plan keeps a head excerpt and is also named
  once under `## Plan file`: a hash-bound snapshot, `revalidation-snapshot.md` in
  the phase dir, and the task is `context_mode: workspace-read`.
- **apply-code-fixes**: the context is the fix diff, which is never named by path.
  Only when the diff is missing and the plan stands in can a plan over the inline
  limit be named once under `## Plan file` (a hash-bound snapshot in the phase
  dir), making the task `context_mode: workspace-read`.

A `workspace-read` subagent must be able to read that path, so do not run it where
it cannot. Never treat such a batch as having the full plan inline.

Read `revalidation_tasks.index.json` beside it instead: the same tasks without
their prompts (`task_id`, `batch_index`, `prompt_path`, `prompt_lines`,
`output_path`, `context_mode`) and `total_batches`. Read `revalidation_tasks.json`
only when there is no index.

**For each task in the file: when the task carries `prompt_path`, run a subagent
that reads that file in full (through line `prompt_lines`, paging if a single read
stops short) and follows it verbatim; otherwise, or if the file is absent, run
that task's `prompt` from `revalidation_tasks.json` as a subagent. Either way,
write the JSON it returns to `task.output_path`.** That is the whole contract: do
not assemble a prompt beyond that one read instruction, and do not tell the
subagent to write the file itself.

A file whose `tasks_schema_version` is missing or not `2`, or whose recorded
`inputs` hashes no longer match their sources, is refused with exit 3: re-run the
phase with `--force` to re-materialize it.

**Check each reply right after you write it.** Run
`<prefix> util check-reply --tasks-file "{plan}/{review}/revalidation_tasks.json" --task-id <task_id>`
(omit `--task-id` to check every batch, and only once every batch's subagent has
returned: a reply not written yet prints `[REPLY_MISSING]`, which is no bad reply and
no re-ask). `[REPLY_INVALID]` means the subagent's reply
did not parse or did not cover its groups — Sonnet subagents lost a closing `]` on 3 of
14 batches in the 2026-10-01 Claude Code run. Re-ask the same subagent once for the
whole reply and write the new reply over the file. Never edit, trim or complete a reply
yourself, and never assemble one from the parts of two replies. A batch still
`[REPLY_INVALID]` after that one re-ask is a failed batch: leave its file as it is and say so.

### Single batch: `[REVALIDATION_PENDING]`

1. Read `revalidation_tasks.index.json` from `{plan}/{review}/` (no index: `revalidation_tasks.json`).
2. Run the single task as the contract above says (the sidecar at `prompt_path`
   when it has one, `task.prompt` otherwise) and write its JSON reply to that
   task's `output_path`.
3. After the result file is written, run the orchestrator again, without
   `--revalidate`.

### Multiple batches: `[REVALIDATION_BATCHES_PENDING]`

1. Read `revalidation_tasks.index.json` from `{plan}/{review}/` (no index: `revalidation_tasks.json`).
2. Count the batches and choose a strategy:
   - **Strategy A (≤ 4 batches):** for each task in `batches`, run it exactly as the
     contract above says and write the JSON it returns to its `output_path`. Run
     all batches in parallel (one message with several subagent calls).
   - **Strategy B (> 4 batches):** follow the wave-based spawning strategy in
     `references/wave-batching.md`.
3. **Before you continue: verify every batch wrote its file, and do not end your
   turn before it has.** Confirm that each task's `output_path` exists and is not
   empty. Re-dispatch any task whose file is missing, exactly as the contract above
   says, and write its reply yourself; only a batch that comes back empty-handed a
   second time is a failed batch, and a batch nobody re-dispatched is not one.
   Spawn batches so their replies return inside this turn, and stay in the turn
   until the last file is on disk: **you** write these files, not the subagents,
   and a host that runs one headless turn has no second turn in which to write
   them. Naming the batch you are waiting on is not waiting for it.
4. After ALL batches complete, run the orchestrator again, without `--revalidate`,
   to merge and continue.
