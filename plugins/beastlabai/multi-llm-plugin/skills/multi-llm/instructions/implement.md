# Implement Mode Instructions

Executes implementation tasks from a plan by spawning subagents.

## Usage

```bash
<dispatcher> implement <plan_path> [--resume] [--fresh] [--task T001] [--dry-run] [--yes] [--no-confirm] [--force-strategy <strategy>] [--human-task ID=done|skip|retry] [--skip-prerequisites]
```

## Options

- `--resume`: Resume from previous session state (skip completed tasks). A task recorded with `util batch-done` (step 5) is skipped when `completed` and dispatched again when `failed`, and so is a check recorded with findings (`--check findings`) that holds back the tasks depending on it, unless it was answered `--human-task <id>=done` — but only once the files git sees changed since the run that recorded the findings ended (or with `--human-task <id>=retry`): on unchanged files it would report the same, so step 2 prints `[CHECK_NOT_RERUN]`, leaves it and the tasks it holds out of the batches, and names them in `not_rerun_checks` / `held_tasks`; a task the prior-changes log names that no record says finished is refused — exit 3 with a `[RESUME_REFUSED]` block naming the task and the `util batch-done` call that records it — because re-emitting it would run it twice.
- `--fresh`: Start over: dispatch every task again, ignoring the tasks an earlier run of this implement finished. Without `--resume` or `--fresh`, a run on an implement that started and did not finish continues it as `--resume` (it prints one `resume: implement started earlier and did not finish …` line naming the tasks it kept), unless the task list was regenerated since; an implement that finished starts over either way. `--resume` wins over `--fresh`. A `--human-task` answer for a code task still needs `--resume` typed. A run that starts over (`--fresh`, or a plain run on an implement that finished) sets aside what earlier runs recorded for each code task: it is pending again, its result file is kept as `<name>.rerun-<time>` and its kept prompt in `prompts/` is removed, so a later `--resume` keeps only what this run finished (it prints `start over: …` lines naming them). A `--task` rerun leaves implement started until step 10 closes it: a plain run after a `--task` rerun whose phase was never closed continues it, and when every task is already done it hands out nothing and only asks for the summary and the close (`--fresh` starts over instead).
- `--task T001`: Execute only a specific task
- `--dry-run`: Show task summary without executing
- `--yes` / `--no-confirm`: Skip all advisory prompts (e.g., unapplied task suggestions) and proceed silently. `--yes` additionally resolves every gate this mode reaches from flags and config: the plan-review prerequisite becomes exit 3 rather than a question (D6 row 6), the task-suggestion advisory resolves to "skip, recorded" (row 7), and the human-task strategy resolves to `skip-dependents` (row 8).
- `--force-strategy <strategy>`: Skip the human task strategy prompt and use the given strategy directly. Valid values: `pause-and-ask`, `skip-continue`, `skip-dependents`. Useful for scripted/non-interactive runs. `pause-and-ask` together with `--yes` is exit 3 at parse time — it promises a gate that an unattended run can never render.
- `--human-task ID=done|skip|retry` (repeatable): Answer one human task without a prompt (D6 row 9), e.g. `--human-task T004=done`. Recorded in `state.json` under `human_task_decisions`. An empty or unrecognized value is exit 3 at parse time. With `--resume` it also answers a code task the last run recorded `failed` (a check that failed, say), or a check whose findings hold back the tasks that depend on it: `done` treats it as satisfied and the tasks after it run (a check's findings stay listed for the code review), `skip` leaves it and the tasks that depend on it undone (under every human-task strategy — `skip-continue` treats only a manual task's edges as satisfied), `retry` runs a check again even though nothing in the repository changed since it ran (`retry` is never recorded). A recorded answer answers one stop: once its task runs again (`--task {id}`, a `retry`, a resume that hands it out) the answer is dropped, so a later failure or new findings of that task stop and ask again. Without `--exec-subagents` the answer is applied to the task JSON step 2 prints: a task answered `done` is recorded completed in `state.json`, left out of the batches and named in the top-level `accepted_tasks` map with its reason (do not dispatch or record it); one answered `skip`, and each task that depends on it, is left out of the batches and named in the top-level `skipped_tasks` map.
- `--skip-prerequisites`: Proceed even though plan-review suggestions were never applied. Loud and recorded; **never implied by `--yes`**.

## Process

1. **Generate Task JSON**: The orchestrator parses the plan and outputs task definitions to JSON
2. **The agent reads the JSON**: the driving agent reads the task definitions
3. **Execute Batches**: the driving agent executes each batch sequentially by spawning subagents
4. **Parallel Execution**: Tasks within a batch can run in parallel (no dependencies between them)
5. **State Updates**: the driving agent updates the state file after each task completes
6. **Generate Implementation Summary**: after all tasks complete, the driving agent creates `{plan}_implementation_summary.md`
7. **Update Plan**: Add reference to the implementation summary in the original plan
8. **Report Results**: Summary of completed/failed tasks

## Output Files

After implementation, files are organized into phase-based subdirectories:

```
plans/my-feature.md                                     # Original plan (updated with summary reference)
plans/my-feature/                                       # Output folder
├── state.json                                          # Session state (plan-local)
├── tasks/
│   └── tasks.md                                        # Task breakdown (from --generate-tasks)
└── implement/
    └── summary.md                                      # Implementation summary
```

The implementation summary (`{plan}/implement/summary.md`) contains:
- Summary of what was implemented
- List of all files created/modified
- Any deviations from the planned tasks
- Task completion status
- Useful context for the code review phase

## Subagent Routing

Each task includes an `executor_role` field:

| executor_role | Usage |
|---------------|-------|
| `general-purpose` | All implementation tasks (default) |
| `human` | Manual steps (API keys, config, manual testing) |

A host whose subagent mechanism takes no role parameter simply ignores this column.

## State Management

State is persisted in `{plan}/state.json` (plan-local):

- Tracks task completion status (pending, in_progress, completed, failed)
- Records files modified per task
- Stores git HEAD at session start for diff comparison
- Enables resume after interruption
- Automatically migrates from old hash-based location on first access

---

## Critical Subagent Delegation Rules

**MANDATORY**: These rules MUST be followed:

1. **ALWAYS delegate**: When implementing tasks, ALWAYS run the task as a subagent (`executor_role: "agent"`). NEVER implement code manually.

2. **OUTPUT TRACKING**: After completing tasks:
   - Update state file with task status (completed/failed)
   - Generate `{plan}_implementation_summary.md` with results
   - Update the original plan file to reference the implementation summary

---

## Step-by-Step Execution

### 0. Check Prerequisites

The implement orchestrator checks prerequisites and may output special markers. Handle them as follows:

#### If output contains `[PREREQUISITE_UNMET]` (under `--yes`):

There are unapplied suggestions from plan review and this run is unattended, so
the orchestrator has already **exited 3** without producing anything — no phase
dir, no task JSON, no `state.json` mutation (D6a). Print the block verbatim and
stop. It names both fixes:

```
[PREREQUISITE_UNMET] implement: 7 HIGH / 3 MEDIUM suggestions in
/abs/plans/x/review-plan/validation.json have not been applied.
  1) Apply them first — <dispatcher> apply-suggestions /abs/plans/x.md --yes
     then re-run      — <dispatcher> implement /abs/plans/x.md --yes
  2) Proceed on unapplied review output (recorded) —
     <dispatcher> implement /abs/plans/x.md --yes --skip-prerequisites
```

`--yes` never implies `--skip-prerequisites`: consent to run unattended is not
consent to stale input. With `--skip-prerequisites` the orchestrator prints
`[PREREQUISITE_SKIPPED] implement: …(reason: explicit --skip-prerequisites)`,
records the skip in `state.json`, and proceeds.

**`--implement` gates on its own prerequisite only.** It does not re-litigate how
the tasks it is about to implement were produced: if `generate-tasks` ran under
`--skip-prerequisites`, that shows up as one
`[PREREQUISITE_SKIPPED_UPSTREAM apply-suggestions: …]` line quoting the recorded
reason and the run proceeds — re-asking would make the recorded skip meaningless.

#### If output contains `[PREREQUISITE_CHECK]` (no `--yes`):

There are unapplied suggestions from plan review. Parse the JSON that follows the marker.

1. **Ask the user**:
   - "Review found N suggestions. Apply them before implementation?"
   - Options: "Apply suggestions first", "Skip suggestions, proceed", "Cancel"

2. Handle the response:
   - **"Apply suggestions first"**: Stop and instruct the user to run this in a separate context:
     ```
     ## Apply Suggestions First

     To keep the implementation context clean, please run in order:

     1. Run: `<dispatcher> apply-suggestions $PLAN_PATH`
     2. Run: `/clear`
     3. Run: `<dispatcher> implement $PLAN_PATH`
     ```
     **Do NOT** proceed further. Stop execution after displaying this message.

   - **"Skip suggestions, proceed"**: Run `uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions --plan-file "$PLAN_PATH" --skip`, then re-run implement orchestrator (this is lightweight — no context bloat)
   - **"Cancel"**: Stop and inform user

#### If output contains `[TASKS_MISSING]`:

No implementation tasks exist. To avoid context bloat from codebase exploration, do NOT auto-run generate-tasks in this context. Instead, stop and instruct the user to run it separately.

**Output the following to the user:**

```
## Tasks Missing

No implementation tasks found for this plan. To keep the implementation context clean,
please run task generation in a separate context:

1. Run: `<dispatcher> generate-tasks $PLAN_PATH`
2. Run: `/clear`
3. Run: `<dispatcher> implement $PLAN_PATH`

The `/clear` step ensures the implementation phase starts with a fresh context,
free from the codebase exploration data generated during task creation.
```

**Do NOT** proceed further. Stop execution after displaying this message.

#### If output contains `[TASK_SUGGESTIONS_ADVISORY]`:

There are unapplied task suggestions from `review-tasks`. This is an **advisory only** — it does NOT block implementation. Parse the JSON that follows the marker to get the `actionable_count`.

**If `--yes` or `--no-confirm` was passed** (D6 row 7): the orchestrator has
already resolved this — it records `apply-task-suggestions` as skipped in
`state.json` and prints
`[AUTO_RESOLVED] task-suggestion-advisory: skipped; apply-task-suggestions
recorded as skipped`. Proceed with implementation and do NOT prompt. The phase is
*recorded* skipped rather than merely ignored, so `--status`, the implementation
summary and any later review can all see that the task-review findings were never
applied.

**Otherwise**, **ask the user**:
- "There are N unapplied task suggestions from review-tasks. Apply them first? [y/N]"
- Options: "Apply task suggestions first", "Skip, proceed to implement" (default), "Cancel"

Handle the response:
- **"Apply task suggestions first"**: Stop and instruct the user to run this in a separate context:
  ```
  ## Apply Task Suggestions First

  To keep the implementation context clean, please run in order:

  1. Run: `<dispatcher> apply-task-suggestions $PLAN_PATH`
  2. Run: `/clear`
  3. Run: `<dispatcher> implement $PLAN_PATH`
  ```
  **Do NOT** proceed further. Stop execution after displaying this message.

- **"Skip, proceed to implement"** (default): Run `uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions --plan-file "$PLAN_PATH" --skip` to mark the phase as skipped, then continue with implementation.

- **"Cancel"**: Stop and inform user.

**Important**: The `[TASK_SUGGESTIONS_ADVISORY]` marker does NOT cause the orchestrator to exit early. The orchestrator continues and produces the full task JSON output. Check for this marker in the complete output alongside the other markers.

#### If output contains no blocking markers (`[PREREQUISITE_CHECK]` or `[TASKS_MISSING]`):

Prerequisites are met. If `[TASK_SUGGESTIONS_ADVISORY]` was present, handle it as described above, then proceed with normal implementation flow.

---

1. **Validate plan file exists**

2. **Resolve the project root, then run the orchestrator to generate task JSON:**

   Intermediate artifacts live in the **workspace temp dir** `$PROJECT_ROOT/.multi-llm/tmp/` — never the system temp dir, so Bash commands, native processes and a host's own file tools resolve the same file on every OS. Resolve the root first and treat failure as a hard prerequisite failure:
   ```bash
   PROJECT_ROOT="$(git rev-parse --show-toplevel)"
   ```
   If the command fails or `$PROJECT_ROOT` is empty, STOP with the error: "multi-llm requires running inside a git repository." Never fall back to a relative path or `$PWD`.

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" implement --plan-file "$PLAN_PATH" [--resume]
   ```
   Do NOT pass `--output` — the orchestrator computes the workspace default itself: `$PROJECT_ROOT/.multi-llm/tmp/implementation_tasks_{plan_stem}_{hash8}.json`, where `{plan_stem}` is the plan filename without extension and `{hash8}` is the first 8 hex characters of the SHA-256 of the repo-relative plan path. The hash makes the name deterministic AND unique per plan *path* (same-stem plans such as `plans/api/index.md` and `plans/ui/index.md` get distinct artifacts, so concurrent runs cannot clobber each other), while a re-run for the same plan simply overwrites the previous artifact — there is no cleanup step; the orchestrator writes `.multi-llm/tmp/.gitignore` containing `*` so the directory ignores itself, and the user may delete `.multi-llm/tmp/` at any time — the next run recreates it. The orchestrator prints the exact absolute path on its `Output file:` summary line — note that path for step 4; never reconstruct the filename or compute the hash yourself.

   **IMPORTANT**: Pass `$PLAN_PATH` as given — the orchestrator resolves it to an OS-native absolute path itself. Do NOT wrap it in `$(realpath ...)`: on Git for Windows, `realpath` emits a POSIX `/c/...` path that a native Windows Python process cannot use.

   **IMPORTANT**: Run this command in the foreground — do **not** run it detached. The orchestrator runs quickly — it only generates task JSON, it does not execute tasks — so 10 minutes is far more than enough.

3. **Check for prerequisite markers in orchestrator output** (see Step 0 above)

   When step 2 ended with `Nothing is left to run: implement stays completed`, the run only recorded answers for an implement that already completed (a `--resume --human-task {id}=done` closing a deferred manual task, say): report the answers it recorded (`[HUMAN_TASK_ANSWERED]`) and end the report with the command `util next-command` prints, as step 11 does. Skip steps 4 to 10: dispatch nothing, write no summary (the completed run's `summary.md` stays as it is) and run no `util finalize-tracking`.

   When step 2 ended with a `[MANUAL_GATE]` line (exit 3), every code task left waits on a manual task not recorded done, so this run hands out nothing and implement is not finished: report that line and the deferred tasks, and end the report with the section `util next-command` prints, as step 11 does (the resume that records only that manual task done, which runs the code tasks waiting on it, and the `--human-task <id>=skip` answer that skips it and them if the user will not do it, the user's call). Skip steps 4 to 10: spawn no subagent, write no summary and run no `util metrics` or `util finalize-tracking`.

4. **Read the task JSON file:**
   ```
   Read the absolute path printed on the orchestrator's `Output file:` line in step 2
   ```
   Reading a file requires an **absolute** path: use the `Output file:` path exactly as the orchestrator printed it (it is already absolute and OS-native, e.g. `{PROJECT_ROOT}/.multi-llm/tmp/implementation_tasks_{plan_stem}_{hash8}.json`). Do NOT rebuild the path yourself — the filename embeds a hash of the repo-relative plan path that only the orchestrator computes.

#### 4a. Human Task Strategy (if applicable)

After reading the task JSON, scan all batches for tasks with `is_human: true`. If any are found, determine the strategy:

**Strategy resolution order** (the orchestrator resolves and persists this; read
`human_task_strategy` from the task JSON rather than re-deriving it):

1. **`--force-strategy` flag**: If provided, use that strategy directly (no prompt).
2. **`--resume` with saved strategy**: On resume, load the saved strategy from state.json (`human_task_strategy` field). If present, use it without re-prompting.
3. **`--yes` / `--non-interactive`** (D6 row 8): resolves to
   **`skip-dependents`**, recorded as
   `[AUTO_RESOLVED] human-task-strategy: skip-dependents for N human task(s)` and
   persisted to `state.json` exactly as `--force-strategy` does, so `--resume`
   stays stable. Why the strictest option: an unattended run cannot perform manual
   steps, so code tasks that depend on them cannot be assumed valid —
   `skip-continue` would run them anyway against unmet preconditions. An explicit
   `--force-strategy` still wins.
4. **Prompt the user** (no `--yes`): **ask the user** how to handle them:

- Question: "This plan contains N human task(s) requiring manual action (e.g., {list first 2-3 titles}). How should these be handled?"
- Options:
  1. **"Pause and ask me" (Recommended)** — Stop at each human task, show what needs to be done, and wait for confirmation before continuing. Dependent tasks block until confirmed.
  2. **"Skip all, continue anyway"** — Skip all human tasks but continue executing all dependent code tasks as normal. List human tasks in the implementation summary for the user to complete later.
  3. **"Skip all, skip dependents too"** — Skip all human tasks AND skip any code tasks that depend on them. List everything skipped in the implementation summary.
  4. **"Cancel"** — Stop implementation.

**The orchestrator records the strategy and every skip; you never write them.** With a strategy resolved (rungs 1-3), step 2 already saved it in `state.json`, recorded every task it skips there (each manual task, and under `skip-dependents` every task that depends on one) and listed them in the task JSON: each such task is left out of `batches`, and the top-level `skipped_tasks` map names them all with their reasons. When `human_task_strategy` in the task JSON is `null` (rung 4) and the user picks a strategy, re-run step 2 with `--force-strategy <answer>` added (`pause-and-ask`, `skip-continue` or `skip-dependents`; "Cancel" stops here) and read the task JSON that run prints instead: that run records the strategy and the skips. Never edit `state.json` by hand — a manual task with no record is still named as owed when the workflow completes, but its dependents are not.

#### 4b. The Python write executor: `--exec-subagents` (an alternative to steps 5-10)

Steps 5 through 10 below are the **native-subagent** path: this agent walks the
batches, spawns a subagent per task, updates state, records metrics, finalizes
tracking, writes the implementation summary and inserts the plan-side reference.

A host with no native subagent tool runs the *same* loop in Python. Add
`--exec-subagents` to the step-2 invocation and the phase schedules itself in one
process:

- batches in ascending `batch_index`, with each batch's snapshot/diff verification
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
  `finalize_tracking.py`, the implementation summary (including its
  `## Manual Tasks (Deferred)`, `## Dependency Override Warnings` and `## Cancelled`
  sections) and `insert_implementation_summary_reference` — as part of the loop's
  contract. A run that dispatched every batch and produced none of those is a
  **failed** run, not a partial one.

Do **not** combine the two: with `--exec-subagents` the phase finishes in that one
invocation and there is no batch left for this agent to run.

On a stop: a partial application halts at the batch boundary, keeps every pre-batch
snapshot under `{phase}/pre_batch/{task_id}/`, leaves the phase **not** completed,
and exits 3 naming the exact re-invocation plus the rollback command
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
says what ran the repository's tests, if anything did, and that the plugin ran none (its log, `notice` and `summary.md`, and
at the end of the stop's own line, the result's `error`), as a finished run does.

A check that ran and reported problems (`check-findings`, also from a reply that said `failed` but listed findings and not `could_not_run`) is not a stop: the tasks that
do not depend on it run. The tasks that depend on it, directly or through another task,
are not run — each is recorded `not run — upstream check <id> reported problems` in
`state.json`, `summary.md` (`## Not Run: Upstream Check Reported Problems`),
`write_batch_report.json` (`blocked_by_check`, `not_run_tasks`, `stop`) and `status` —
and once every other task has run, implement ends needing a human (exit 3, the phase not
completed) with the same three ways forward: fix the code and `--resume`, accept the
findings with `--human-task <id>=done` (the waiting tasks run, their prompts say the
findings were accepted, and the findings stay listed for review-code), or `--human-task <id>=skip`.

`--dry-run-subagents` renders every command, applies every admission and policy
check, writes `{phase}/subagent_dry_run.json` and starts no child.
`--detach` self-daemonizes the phase and reports per-task progress in
`{phase}/.status.json` under `progress.write_subagents`; never combine it with a
host's own background mechanism, whichever *run detached* resolves to for
your host.

5. **Execute batches sequentially (batches have dependencies):**

   Before the loop, take `{tasks_to_dispatch}` from the task JSON's `tasks_to_dispatch` (step 2's `Tasks to dispatch:` line; never count it yourself, and never take the `Organized into …` batch count) and mark the phase start. The `[ETA]` line counts tasks, one `util metrics record` per task you dispatch; pass this same number every time, and `util batch-done` takes out of it a task its record keeps from running (one a check holds back, one after a failed task):
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics start \
     --state-file "$STATE_FILE" --phase "implement" --total-batches {tasks_to_dispatch}
   ```

   `batches` holds exactly the tasks you dispatch (and a manual task still waiting for its answer); its count is the `Pending tasks:` line. Step 2 left out, and named in top-level maps with their reasons, every task you must neither dispatch nor record: `skipped_tasks`, `accepted_tasks` and `completed_manual_tasks` (above); `refused_tasks`, a task the write policy (`driver.write_paths`) does not allow, already recorded `failed` as the `--exec-subagents` leg refuses it before dispatch, and `not_run_tasks`, the tasks that depend on one; `not_rerun_checks`, a check whose findings stand because nothing changed since they were recorded (`[CHECK_NOT_RERUN]`), and `held_tasks`, the tasks a check with findings holds back. List them in the summary (refused: `Failed`, refused before dispatch; the others: `Not run`). A task named in `waiting_on_checks` (step 2's "Waiting on a check's verdict" list) is in `batches`, after the check task it depends on, because that check's verdict is not known until it runs: dispatch it once the check is recorded `--check passed`; if the check is recorded with findings, `util batch-done` prints `[CHECK_BLOCKED]` for it, so do not dispatch it — it stays pending, the summary lists it as `Not run`, and step 10 runs without `--mark-completed`. When `batches` is empty step 2 says `Nothing to dispatch`: spawn nothing and go on to step 7 (this run reopened implement; one that printed `Nothing is left to run` ended at step 3).

   For each batch in `batches` array:
   - Execute all tasks in the batch (can be parallel if `can_parallelize` is true)
   - For each task, bind its prompt first:
     ```bash
     uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util write-prompt \
       --phase-dir "{plan}/implement" --task-id "{task.id}"
     ```
     The orchestrator materialized `{plan}/implement/write_tasks.json` (printed as `[WRITE_TASKS_FILE]`) beside the task JSON, one entry per task under the task's own `id`. This rewrites the task's prompt with the prior-task context bound **now** — from `{plan}/prior_changes.jsonl` as it is at this moment, i.e. the tasks already appended below — and the result contract appended: exactly the text the `--exec-subagents` executor would dispatch. It writes it to `{plan}/implement/prompts/{task.id}.prompt.txt` and prints `[WRITE_PROMPT] <path>`, `[WRITE_PROMPT_LINES] <n>` and `[WRITE_PROMPT_CONTEXT] …`. Never hand a subagent `task["prompt"]` from the JSON: it carries a literal `{prior_changes_context}` token that must never reach a subagent. An exit 3 names the problem (no `write_tasks.json` — re-run step 2; an unknown id — the known ids are listed; `[WRITE_PROMPT_BLOCKED]` — the task depends on a check that reported problems, see the check task record below: do not dispatch it; `[WRITE_PROMPT_REFUSED]` — the write policy (`driver.write_paths`) does not allow a file the task declares, as the `--exec-subagents` leg refuses it before dispatch: do not dispatch it, record it with the `util batch-done … --status failed` line the refusal prints, skip the tasks that depend on it and report the way forward it names); do not fall back to the raw prompt. Run each `util write-prompt` as a command of its own, never chained after the records of the tasks before it: its exit 3 refuses that one task, and at the end of a chain it reads as the failure of the calls before it, while `util batch-done` exits 0 whenever it recorded the task (`[CHECK_BLOCKED]` included) and each call's own `MULTI_LLM_RESULT` line names its own exit. A `[WRITE_PROMPT_ORDER]` line (on stderr; the prompt is still written) names an earlier task whose summary this prompt does not carry — recorded but not appended yet, or not finished: do what it says, then run this `util write-prompt` again before spawning the subagent.
   - Then spawn one subagent:
     ```
     Spawn one subagent with:
     - executor_role: task["executor_role"]  (always "agent" here; a "human" task never reaches this step)
     - description: task["title"]
     - prompt: read the file at the [WRITE_PROMPT] path in full — through line [WRITE_PROMPT_LINES], paging if a single read stops short — and follow it verbatim
     ```
     That is the entire prompt: do not paste the file's text or add to it. The subagent's reply ends with one JSON object (`{"status", "ids", "files_touched", "summary", "notes"}`); its `summary` is the task's one-line record below, and its `status` (`applied` / `no-op` / `failed`) and `files_touched` are what you record for the task.

   - **Wait for every task in the batch, inside this turn.** A later batch depends
     on this one, so do not start the next batch — or end your turn — with a
     task still outstanding. **You** record each task's status and metrics below,
     not the subagent, and a host that runs one headless turn has no second turn in
     which to record them: a reply that lands after the turn ends leaves the task
     unrecorded in `state.json` while its code is already on disk, and that is the
     one state a later `--resume` cannot tell apart from work that never started.

   - **Human task handling** (tasks with `is_human: true`):

     **"Pause and ask me" strategy:**

     Unreachable under `--yes` (D6 row 9): the strategy never resolves to
     `pause-and-ask` unattended, and `--force-strategy pause-and-ask` together
     with `--yes` is **rejected at parse time with exit 3** rather than hanging
     forever on a stdin nobody is on.

     On a host with no structured ask tool, answer it with the flag instead — the
     pause becomes a process boundary rather than a blocked stdin. Print the task
     plus its two re-invocations, exit 0 with the batch pending, and be re-invoked:

     ```
     <dispatcher> implement /abs/plan.md --resume --human-task T004=done
     <dispatcher> implement /abs/plan.md --resume --human-task T004=skip
     ```

     (Repeatable; "cancel" is simply not re-invoking. `--human-task T004=` or any
     value other than `done`/`skip` is exit 3 at parse time, never a guess. Answers
     are recorded in `state.json` under `human_task_decisions` and echoed as
     `[HUMAN_TASK_ANSWERED] T004=done`, so a re-invocation does not re-ask.)

     Where a structured ask tool exists and `--yes` was not passed:
     - Do NOT spawn a subagent for human tasks
     - **Ask the user**, presenting the task:
       - Question: "Task {id}: {title} requires manual action. Please complete the following and confirm when done:\n\n{description}\n\nAcceptance criteria:\n{acceptance_criteria}"
       - Options: "Done — I've completed this task", "Skip this task", "Cancel implementation"
     - Handle each response by recording it through step 2, never by hand:
       - **Done**: re-run step 2 with `--resume --human-task {id}=done` added; it records the task completed.
       - **Skip**: re-run step 2 with `--resume --human-task {id}=skip` added; it records the task skipped with reason "skipped by user during pause-and-ask" and skips every task that depends on it (the **transitive skip propagation** below). That is your decision, not deferred work: step 2 lists it, and the tasks skipped with it, under "Skipped at your request", and the summary files them under a `## Skipped at your request` section — never under `## Manual Tasks (Deferred)`, which the workflow's closing `[MANUAL_TASK]` lines read as owed.
       - Then read the task JSON that run prints and continue with its batches.
       - **Cancel**: Execute **cancellation semantics** (see below)
     - Human tasks within a parallelizable batch: execute all non-human tasks in parallel first, then present human tasks sequentially

     **"Skip all, continue anyway" strategy:**
     - The orchestrator already recorded every human task as "skipped" in state (its `skip_reason` starts "deferred — manual task") and a dependency override for each code task that depends on one. Do not record either yourself.
     - Treat human task dependencies as satisfied — dependent code tasks proceed as normal
     - After all tasks complete, include a "## Manual Tasks (Deferred)" section in the implementation summary, ending with the text of step 2's `[MANUAL_TASK_NOTE]` line (the task JSON's `manual_tasks_note`), verbatim: it says how to record them done
     - Also include a "## Dependency Override Warnings" section listing each code task that ran with overridden human dependencies:
       ```markdown
       ## Dependency Override Warnings

       The following tasks ran with skipped human-task dependencies (skip-continue strategy):

       | Task | Overridden Dependencies | Risk |
       |------|------------------------|------|
       | T003: Build API client | T002: Create API key | Task may fail at runtime without API key |
       | T005: Deploy service | T004: Configure DNS | Service may not be reachable |
       ```

     **"Skip all, skip dependents too" strategy:**
     - The orchestrator already recorded every human task, and every task that depends on one, as "skipped" in state; the task JSON leaves them out of `batches` and names them in `skipped_tasks`. Do not dispatch them and do not record them yourself.
     - After remaining tasks complete, include a "## Manual Tasks (Deferred)" section listing each human task and each skipped dependent (step 2 prints them under "Deferred tasks") and ending with the text of step 2's `[MANUAL_TASK_NOTE]` line (the task JSON's `manual_tasks_note`), verbatim: it says how to record them done; a task step 2 printed under "Skipped at your request" (a failed task, or a manual task the user will not do, answered `--human-task {id}=skip`, and its dependents) goes under a `## Skipped at your request` section instead, and one it printed under "Accepted after failing" is listed as accepted after failing, and one it printed under "Completed by hand" (a manual task answered `--human-task {id}=done`) is listed as completed by hand

     #### Transitive Skip Propagation Algorithm

     The orchestrator runs this walk itself (under "skip dependents too", and for a "Skip" answered with `--human-task {id}=skip`); it is described here so the summary can report it:

     1. Start with the set of skipped human task IDs as the **seed set**
     2. Use BFS forward walk: for each task in the seed set, find all tasks that have it in their `depends_on`
     3. Each discovered dependent is recorded "skipped" with reason: "skipped — depends on skipped task {parent_id} ({parent_title})"
     4. Add the newly skipped task to the queue and continue until no more dependents are found
     5. Report the full skip chain: `T001 (human, skipped) → T003 (skipped, depends on T001) → T005 (skipped, depends on T003)`

     #### Cancellation Semantics

     When the user chooses "Cancel" (either at the strategy prompt or during pause-and-ask):

     1. Mark all already-completed tasks as "completed" (preserve their status)
     2. Mark all not-yet-attempted tasks as "pending" (NOT "skipped" — they were never reached)
     3. Mark the current task (if any) as "pending"
     4. Do NOT mark the implement phase as completed (step 10 runs without `--mark-completed`, so the phase stays `in_progress`)
     5. Write a partial implementation summary with a "## Cancelled" header:
        ```markdown
        ## Cancelled

        Implementation was cancelled by user after completing {N} of {total} tasks.

        ### Completed Tasks
        | Task | Status |
        |------|--------|
        | T001: Setup DB | Completed |

        ### Remaining Tasks (not attempted)
        | Task | Status |
        |------|--------|
        | T002: Create API key | Pending |
        | T003: Build feature | Pending |
        ```
     6. The partial summary allows `--resume` to pick up where it left off

   - **Record the task outcome** — after the task's subagent returned and you classified its outcome (its reply's `status` and `files_touched`, checked against the files on disk), run:
     ```bash
     uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util batch-done \
       --phase-dir "{plan}/implement" --task-id "{task_id}" --status {batch_status} {check_flags}
     ```
     `{check_flags}` is the result the reply's `check` object reports, never left out when the reply carries one: `--own-check passed`, `--own-check findings` (with one `--finding` per failing check) or `--own-check none` for a task that edits files, read off its `check` by the rules in `references/own-check.md`, plus `--note "{note}"` when that `check` carries a `note` (the subagent's own words about its checks, never a `--finding`), and `--check passed` (or `--check findings`, or `--status failed --check could-not-run`) for a check task, each explained below; empty only when the reply carries no `check`. Pass each `--finding` exactly as the reply wrote it, adding no words of your own. A `completed` record without it prints `[OWN_CHECK_NOT_RECORDED]` (`[CHECK_NOT_RECORDED]` for a check task) naming the call that records it, the same flags plus the result: run that call before the append below.
     `{batch_status}` is `completed` for an applied task (a verified no-op included) and `failed` for one that failed — add `--reason "{compact reason}"` to a `failed` one, and `--partial` when its subagent changed files before it failed (its reply's `files_touched`, or files you see changed on disk): its edits are half-applied, `batch-done` says so, and the stop offers no `--human-task` answer for it until the user has inspected them, as the `--exec-subagents` leg's stop offers none for a partial application. A reply that says `applied` while none of the files its task declares changed did not do the task: dispatch it once more, with one sentence added to the prompt saying its previous attempt answered `applied` but changed no file, and if that changes nothing either, record it `failed` (`--reason "said applied, no file changed"`), never `completed` (fix round 14). It prints one `[BATCH_DONE] {task_id} {batch_status}` line and writes `task_status[{task_id}]` into `state.json`, the same entry the `--exec-subagents` executor writes: what `--resume` reads to skip the task (a `failed` task is dispatched again) and what `status` counts as progress. Run it **before** the append below — a run that dies between the two leaves a record `--resume` honours, never a log entry `--resume` would re-run — and never retype this as a hand-rolled JSON edit of the state file.
     For a **check task** (an agent task that declares no files) its reply carries a `check` object: add `--check passed` when it says `"passed": true` with no findings (a bare `findings` of `"none"`, `"n/a"`, `"no problems found"`, `""` or `0` beside it lists none), else `--check findings` and one `--finding "{finding}"` per entry of its `findings` list, with `--status completed`. A check that ran, changed no file and reported problems is not a failed task: `status`, the workflow notice and the code review are told the findings. A check task whose `check` says `"could_not_run": true` is a check that could not run (a missing command, a crash, a timeout), whatever its `status` says: record it `--status failed --check could-not-run` (add `--reason` naming the check and why), never as findings. A reply that says `"status": "failed"` but lists findings in its `check` and does not say `could_not_run` is a check that ran and found problems: record it `--status completed --check findings` like any other. A `failed` reply that lists no finding is a failed task: record it `failed`. Use `failed` for a check task also when its subagent changed a file, with `--partial`. `batch-done` holds a check to that: when a file git sees changed after the check's `util write-prompt` and no other task of the phase declares it, `--status completed` is refused (exit 3, naming the files); record the check `--status failed`, or, if something other than its subagent changed them, run its `util write-prompt` again and run the check again. A check recorded with findings holds back the tasks that depend on it: `batch-done` prints a `[CHECK_BLOCKED]` line naming them and records each `pending` with the reason `not run — upstream check {id} reported problems`. Do not dispatch them and record nothing for them (their `util write-prompt` exits 3); run every task that does not depend on the check. At the end, write the summary and close the phase without `--mark-completed` (step 10 refuses it while a held task is left), and report the held tasks and the way forward: fix what the check reported (by hand, or review-code then apply-code-fixes) and run this phase with `--resume` (the check runs again), or accept its findings with `--resume --human-task {id}=done` (the held tasks then run, and their prompts say the findings were accepted), or `--resume --human-task {id}=skip`. Its prior-changes summary is `(check findings — {n} problem(s): {findings}; no file changed)`.
     For a task that **edits files** (it declares files, even when its title calls it a check), its reply carries a `check` object naming in `ran` the checks its subagent ran on its own edits (a test, a build, a syntax check): record it with the `--own-check` flags the rules in `references/own-check.md` give for that object, the reading the `--exec-subagents` leg applies to the same reply, with `--status completed`: `--own-check passed`, `--own-check findings` and one `--finding "{finding}"` per entry they list, or `--own-check none` (it ran no check, which is not a pass); never `--check`, which records only a check task's verdict (`batch-done` refuses it on such a task and names the call to make). A recorded `--own-check findings` prints a `[BATCH_CHECK_FAILED]` line and records the failure in `state.json`, where `status` and the code review read it: the edits are kept and nothing waits for the task, but it is not a clean success — list it in the summary's `## Check Findings` (step 9) and say in your report that its check fails. When every finding it reports only repeats what the user accepted for a check (`--human-task <check>=done`) that the task depends on and whose failure is not the task's own job (the same command, all of one accepted finding or its first words, every number the same), `batch-done` prints `[BATCH_CHECK_ACCEPTED]` for those findings instead and records no failure for the task: name it under that check's accepted findings in `## Check Findings`, never as its own failing check, and the phase stays a clean finish; any other finding still prints `[BATCH_CHECK_FAILED]`. A `[FINDING_RESTATE]` line after it names a finding that holds an accepted one word for word with words added, and gives the call that records the task again with the accepted finding alone and those words as `--note`: run it only when those words are the subagent's comment, never when they report something the check printed beyond the accepted finding (a note is a comment, never a failure: every failure the check printed stays a finding).
   - **Append to prior changes** — record the task's one-line `summary` (normalized: one line, at most 200 characters; for a failed task `(task failed — {compact reason})`) so every later task's bound prompt sees it, as the `--exec-subagents` leg records it. `--id` is the task id, `--phase` is `implement`, and `--output-dir` is the plan directory `{plan}` (the one holding `state.json`: the one log every write phase shares and the one `util write-prompt` binds from):
     ```bash
     uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util prior-changes append \
       --output-dir "{plan}" --id "{task_id}" --phase "implement" --summary-stdin <<'SUMMARY_EOF'
     {normalized_summary}
     SUMMARY_EOF
     ```
     Append again whenever you record a task again (a failed task a `--resume` ran again, a check that ran again after its findings were fixed, a task refused before dispatch that later ran): the newer summary replaces the earlier one in every later task's prompt (`Replaced entry …` on stderr). The same summary twice is written once (a `Notice:`, exit 0). An empty `--id` writes nothing and exits 3: run the append again with the task id. If it fails otherwise, log a warning and continue.
   - **Record metrics**: Run the metrics utility to store the subagent's metrics:
     ```bash
     uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics record \
       --state-file "$STATE_FILE" --phase "implement" \
       --label "{task_id}: {task_title}" --task-id "{task_id}" --subagent-type "{executor_role}" \
       --tokens {token_count} --tool-uses {tool_uses} --duration-ms {duration_ms} \
       --total-batches {tasks_to_dispatch} --batch-index {N}
     ```
     Where `token_count`, `tool_uses`, `duration_ms` come from whatever your subagent mechanism reports, and `{N}` is the cumulative 1-based index of the tasks you dispatched, across all batches. Omit any flag it does not report. Never pass `0` for an unknown value; omit the flag — a made-up zero is averaged into the phase totals as a real measurement. The script prints an `[ETA]` line to stderr after each call; for a task `util batch-done` recorded `failed` it says the task failed and why, never "done".

   **The last subagent returning is not the end of the phase.** Steps 6 through 11
   still owe work — the finalization that computes which files this phase
   changed, the regression run, the summary, the plan link and the completion
   record. Do not end your turn between the last task and step 11, and do not
   announce the implementation as done before it: on a host that runs one headless
   turn the announcement *is* the end of the run, and a phase whose code landed but
   whose tracking never ran hands the code review phase no file list to review.

6. **Handle errors:**
   - If a task fails, mark it as "failed" in state
   - Continue with independent tasks (skip tasks that depend on failed ones, or on a check recorded with findings)
   - Log the error for reporting

7. **Finalize file tracking:**
   After all tasks complete (before generating summary), mark the phase finish and run finalization:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics finish \
     --state-file "$STATE_FILE" --phase "implement"
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util finalize-tracking --state-file "$STATE_FILE"
   ```
   Where `$STATE_FILE` is the `state_file` path from the JSON output.

   This deterministically computes which files were changed during implementation
   by comparing current git changes against pre-existing changes recorded at startup.
   The tracked files are stored in state and used by the code review phase to focus
   only on implementation changes (ignoring unrelated uncommitted changes).

   **Add `--touched "<repo-relative path>"` (repeatable) for every file your
   subagents reported changing** — e.g. `… --state-file "$STATE_FILE" --touched
   "src/game.js" --touched "index.html"`. The census is `git status
   --porcelain`, which reports a *new* directory as one `newdir/` entry (that
   one is expanded back to its files for you) and cannot tell an edit inside an
   already-untracked tree from the rest of it. A file the run edited that was
   **already dirty when the phase started** is subtracted as pre-existing
   unless `--touched` names it, and is then invisible to the code review.

8. **Run post-implementation regression tests:**
   After all tasks complete, run the project's test suite **once** to catch any integration issues:

   - Use **the repository's `driver.verify_command` if one is configured** in its
     `.multi-llm/providers.yaml`. That key is the repo's own answer to "what checks
     this?", it is what the `--exec-subagents` leg runs, and running it here keeps
     both legs reporting the same check.
   - Only if none is configured, detect the target repository's own test runner
     (never this skill's — the suite under test is the one the plan changed):
     - If `package.json` exists with a `test` script: `npm test`
     - If `pytest.ini`, `pyproject.toml` with `[tool.pytest]`, or `conftest.py` exists: `pytest -v --tb=short`
   - Run that command bare, exactly as the repository defines it: no `| tail`, `| head` or `| grep`, no `2>&1 |`, nothing chained before or after it. Read its whole output and take pass or fail from its own exit code: a pipe reports the last command's exit code, not the check's, and a trim drops the failures above the cut. A long output is saved to a file: read it to the end.
   - Record pass/fail results for inclusion in the implementation summary, naming
     the command you ran (or `not configured` when nothing was)
   - When no `driver.verify_command` is configured, say so in one plain line of your
     report — nothing in the plugin ran the repository's tests — naming the setting to
     add (`verify_command` under `driver:` in `.multi-llm/providers.yaml`) and the
     command you detected as its value when there was one; never write the config
   - A failing **`driver.verify_command`** is the repo's own contract failing: do
     not revert anything, do not mark the phase completed (run step 10 without
     `--mark-completed`), and hand it to a human with the command and the tail
     of its output. That is what the `--exec-subagents` leg does (exit 3), and
     the two legs must agree.
   - A failing **detected** runner is a guess, not a contract: record the results
     and continue to summary.

9. **Generate implementation summary:**
   After all tasks complete, create the implementation summary file using the `summary_file` path from the JSON output.
   Use `summary_file_relative` for links within the file (relative to plan's parent directory).
   In `## Task Results`, an agent task that declares no files (`Files to modify` and `Files to create` both none) is a verification-only check: its Status is `Verified` when its subagent changed no file and `Partial` when it changed one (name the files), the words the executor leg's summary uses (`verified` / `partial-application`); a human task is not one of these, it is deferred. A task that declares files is never `Verified`, even when its title calls it a check and its own check passed: its Status is `Completed`.
   A check whose reply said `"passed": false` or listed findings is never `Verified`: its Status is `Check findings` (the executor leg's `check-findings`), and a `## Check Findings` section after `## Task Results` lists each such task under a `### {task_id}` heading with one bullet per finding, so the reader and the code review see them. A check step 2 names in `accepted_tasks` (findings the user accepted with `--human-task {id}=done`) is listed there too, saying the user accepted its findings and naming the tasks that waited on it and ran because of that; never write that no task waits for it. A task such a check held back is `Not run` in `## Task Results`, and a `## Not Run: Upstream Check Reported Problems` section lists each one beside the check it waits for.
   A task that edits files and whose own check failed (`[BATCH_CHECK_FAILED]`, step 5) is `Applied, its check fails` in `## Task Results`, and `## Check Findings` lists it under a `### {task_id}: a check it ran fails` heading with one bullet per finding. A task whose `batch-done` printed `[BATCH_CHECK_ACCEPTED]` instead is `Applied` in `## Task Results`, and `## Check Findings` adds one line under the accepted check's heading: `{task_id} ran this check again, and its own report says only what you accepted: not counted as {task_id}'s own failure.` A task's `--note`, when it gave one, goes under its finding or that line as `its note (not a finding): {note}`. A task whose `batch-done` printed `[BATCH_CHECK_REPEATED]` (its own check reported only what a check task reported, whichever of the two you recorded first) is `Applied` too, never `Applied, its check fails`, and `## Check Findings` adds one line under that check's heading: `{task_id} ran this check too, and its own report says only what {check_id} reported: it repeats {check_id}'s finding, not counted as {task_id}'s own failure.`

   Write the summary to the path specified in `summary_file` from the JSON:
   Describe each file under `## Files Modified` and `## Files Created` as it is on disk now: when you quote a value it holds, read the file for it. A task's prompt, its prior-changes summary and an earlier summary.md describe the file as it was when that task ran, and before a `--resume` the user may have changed it (fixing what a check reported, say), so a value copied from them can be out of date.
   ```markdown
   # Implementation Summary: {plan_name}

   *Generated: {timestamp}*

   **Plan**: [{plan_name}](../{plan_name})
   **Tasks**: [{tasks_file_relative}](./{tasks_file_name})

   ## Summary

   Brief description of what was implemented...

   ## Task Results

   | Task | Status | Notes |
   |------|--------|-------|
   | T001: Task title | Completed | ... |
   | T002: Task title | Completed | ... |

   ## Files Modified

   - `path/to/file1.ts` - Description of changes
   - `path/to/file2.ts` - Description of changes

   ## Files Created

   - `path/to/new-file.ts` - Description

   ## Test Results

   {Pass/fail results from regression test run, or "No test runner detected"}

   ## Deviations from Plan

   List any changes that deviated from the original task plan...
   (Or "None - implementation followed the plan exactly.")

   Before writing the summary, generate the resource usage section:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics report \
     --state-file "$STATE_FILE" --phase "implement"
   ```
   Include the output (if non-empty) in the summary before "## Notes for Code Review".

   ## Notes for Code Review

   Any important context for the code review phase...
   ```

10. **Update the original plan and mark the phase completed:**
   Add a reference to the implementation summary in the original plan. This is the
   same command as step 7 with three more flags — it is deterministic, so it is
   Python's job and not a block of inline code for you to retype. Pass the
   task JSON's `plan_arg` (the plan as the user typed it) as `$PLAN_ARG` and the
   `summary_file_relative` value exactly as the orchestrator printed them; the
   insertion is idempotent, so re-running it on an already-updated plan is a no-op:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util finalize-tracking \
     --state-file "$STATE_FILE" --plan-file "$PLAN_ARG" \
     --summary-file-relative "$SUMMARY_FILE_RELATIVE" --mark-completed
   ```
   `--mark-completed` is the phase's completion record. The orchestrator recorded
   the phase *started* when it wrote the task JSON (step 2), and this is the only
   command that records it *completed* — **pass it only when every task ran and
   step 8's `driver.verify_command` (if configured) passed** (it is refused, exit 3,
   while a task a check with findings held back is left: after a `[CHECK_BLOCKED]` line, a failed task or a stop, run it without `--mark-completed`); on a cancelled run,
   a failed contract check or a loop that stopped early, run the command without
   it, so the phase stays `in_progress` and `status` offers `--resume` instead of
   calling it done.

11. **Report results** following `references/summary-format.md`, including:
   - Number of tasks completed/failed
   - Each check task that reported problems, with its findings (the code review is told about them), and the tasks it held back (the closing section gives the resume and each `--human-task` answer: write none of them here)
   - Each task whose own check failed after its edits (`[BATCH_CHECK_FAILED]`), with what failed: the phase applied it but is not a clean finish
   - Each task recorded with `--partial`: it failed with its edits half-applied; name the files its subagent changed and say the user inspects them (keeps or undoes them) and fixes the cause before the resume, which dispatches it again
   - At a stop after a code task completed, with no `driver.verify_command` configured: the `[TESTS_NOT_RUN]` line the next-step lookup prints, the text after its tag verbatim, as plain text — it says what checks the tasks ran, that the plugin itself ran none, and names the setting to add (step 8 itself does not run at a stop); never write a line of your own in its place
   - Each manual task step 2 deferred, as the user's to do: the next-step lookup's section that ends the report lists them, then the `[MANUAL_TASK_NOTE]` text verbatim and its `[MANUAL_TASK_COMMAND]` alone in a fenced block (the lookup prints the tasks as `[MANUAL_TASK]` lines below its commands), which say how to record them done; give them there only, never a second time above it
   - At a stop (step 10 ran without `--mark-completed`) the next-step lookup of `references/summary-format.md` still runs: its section between `[NEXT_STEP_MARKDOWN]` and `[NEXT_STEP_MARKDOWN_END]` is the resume command and, when tasks wait for an answer, each `--human-task` answer the stop offers, each with its why. End the report with that section, copied as it is, whys included; never write a resume or `--human-task` command of your own, nor a list, recap or summary of the ways forward in its place or above it
   - Implementation summary file location
   - State file location
   - Any errors encountered
   - Files modified
   - Resource usage summary (if metrics were captured)
   - The `[MANUAL_TASK_NOTE]` text, wherever you give it, as plain text and never in a fenced block: a fenced block holds one command and nothing else, such as the `[MANUAL_TASK_COMMAND]`
   - Never edit `driver.write_paths`, or any other multi-llm setting in `.multi-llm/providers.yaml`, yourself. At a stop, offer only the ways forward the stop itself names, as it words them: when it names a change to `driver.write_paths` that lets a refused file be written (adding it to `allow`, or removing or narrowing a deny rule that covers it), that is one of them and the user's call; add no advice about the write policy of your own. The ways forward a stop names are its commands below and the fixes its text names. For a task the write policy refused, its refusal (the emit's `refused_tasks` line, or `[WRITE_PROMPT_REFUSED]`) names the change to `driver.write_paths` that lets its file be written (none for a file outside the repository, which no rule can allow) and resuming, and the next-step lookup's answers name `--human-task <id>=skip`, or `=done` once the user did the task by hand: relay them as the user's choice, in those words

**IMPORTANT:** You orchestrate the execution by **spawning subagents**. Do NOT implement the code yourself — delegate every task to a subagent.

---

## Example Execution

```
User: <dispatcher> implement plans/my-feature.md

Agent:
1. Runs: PROJECT_ROOT="$(git rev-parse --show-toplevel)" (prerequisite check)
   then: uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" implement --plan-file plans/my-feature.md
2. Orchestrator outputs:
   - Output file: {PROJECT_ROOT}/.multi-llm/tmp/implementation_tasks_my-feature_1a2b3c4d.json (5 tasks in 3 batches; the _1a2b3c4d suffix is the orchestrator-computed hash of the repo-relative plan path)
   - State file: plans/my-feature/state.json
   - Summary file path: plans/my-feature/my-feature_implementation_summary.md
   - Tasks file path: plans/my-feature/my-feature_tasks.md
   - Summary file relative: my-feature/my-feature_implementation_summary.md
3. the agent reads the `Output file:` path exactly as printed in step 2 (absolute path)
4. For each batch, the agent binds each task's prompt with `util write-prompt` and spawns subagents that read the bound file:
   - Batch 0 (1 task): subagent reading T001's `[WRITE_PROMPT]` file ("Create database schema...")
   - Batch 1 (2 tasks, parallel):
     - subagent reading T002's file ("Implement service layer...")
     - subagent reading T003's file ("Create form component...")
   - Batch 2 (2 tasks, parallel):
     - subagent reading T004's file ("Add API routes...")
     - subagent reading T005's file ("Write E2E tests...")
5. After each task, the agent records its outcome with `util batch-done` and appends its summary to the prior-changes log
6. After all tasks complete, Claude generates:
   - plans/my-feature/my-feature_implementation_summary.md (summary of what was done)
7. Claude updates the original plan to link to the summary using relative path
8. Reports: 5 tasks completed, summary file, state file, files modified
```
