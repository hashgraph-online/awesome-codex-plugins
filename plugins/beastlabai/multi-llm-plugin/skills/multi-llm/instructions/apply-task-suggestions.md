# Apply Task Suggestions Mode Instructions

Applies validated suggestions from a task review to the tasks.md file, using smart batching to minimize subagent calls while maintaining edit safety.

## Usage

```bash
/multi-llm:multi-llm --apply-task-suggestions <plan_path> [options]
```

## Prerequisites

This mode requires a completed task review with validation. The following files must exist in `{plan}/review-tasks/`:
- `validation.json` - Validation results
- `grouped.json` - Grouped suggestions

If these files don't exist, run `--review-tasks` first.

### User Selections (Auto-Detected)

If available, the following file is auto-detected from `{plan}/review-tasks/`:
- `user_selections.json` - User decisions from the HTML report (skips, validation overrides, edited descriptions)

HTML selections take precedence over markdown checkbox selections.

### Consolidated Decisions (Auto-Detected)

If the review-tasks phase included a consolidation step, the following files are auto-detected from `{plan}/review-tasks/`:
- `consolidated-report.md` - Consolidated suggestion report
- `consolidated_user_selections.json` - User decisions on consolidated groups

No additional flags are needed — consolidation integration is automatic. Specifically:
- **C-level** (consolidated) decisions are merged with **G-level** (per-group) decisions automatically
- **C-level skips** are unioned with **G-level skips** (both sources contribute to the final skip set)
- **C-level validation overrides** cascade to all underlying groups, but **G-level overrides take precedence** (more specific wins)
- If `grouped.json` has changed since consolidation was run, the orchestrator will warn about staleness. Use `--accept-stale-consolidation` to proceed anyway.

## Smart Batching

The orchestrator groups related task suggestions into batches for efficient processing:

### Batching Heuristics

1. **Task Reference Proximity**: Suggestions targeting the same task (e.g., "Task T001") are grouped together
2. **Type Compatibility**:
   - Deletions are ALWAYS isolated (one per batch) to prevent conflicts
   - Additions, modifications, and clarifications can be batched together
3. **Size Limits**: Max 4 suggestions per batch, max 2500 chars total description
4. **Priority Ordering**: Batches are sorted by priority score (higher importance first)

### Efficiency Gains

With batching, 10 suggestions might become 3-4 batches:
- **Before**: 10 subagent calls (one per suggestion)
- **After**: 3-4 subagent calls (grouped by task reference)
- **Savings**: 60-70% reduction in API calls

## Process

1. **Load Validation Results**: Read the validation JSON to get validated suggestions
2. **Filter Suggestions**:
   - Only process suggestions with `status: "valid"`
   - Exclude suggestions marked `[x] Skip` in `report.md`
3. **Smart Batching**: Group related suggestions into batches by task reference
4. **Handle Human Decisions**: For `needs-human-decision` items, **ask the user** — each rendered question also offers a per-item **Let the agent decide** option that offloads just that one suggestion's judgment to a subagent. Or, if `--agent-decide` was passed, let the judge agent decide every suggestion up front — or pre-marked in the report's *Let the agent decide* dropdown/checkbox, which routes just those suggestions to the judge without prompting. See step 6. **Under `--yes` (or `--non-interactive`) this site is never rendered** (D6 row 10): `--yes` sets `--agent-decide` itself, so every item goes through the judged/deferred path up front and no item — and no batched approve-all/skip-all UI — can block.
5. **Batch Application**: Process each batch with a single subagent:
   - Spawn a subagent with the batch prompt
   - Wait for completion before moving to the next batch
   - This prevents conflicts from concurrent edits to tasks.md
6. **Generate Report**: Create `{prefix}_applied_task_suggestions.md` with results

## Output Files

```
plans/todo/my-feature/
├── state.json                           # Session state (plan-local)
├── review-tasks/                        # Input files from review phase
│   ├── grouped.json
│   ├── validation.json
│   └── backup.md
└── apply-task-suggestions/              # Output files from this phase
    ├── orchestrator_output.json         # Batch instructions for the agent
    ├── tasks-backup.md                  # Pre-modification backup of tasks.md
    └── summary.md                       # Summary of applied changes
```

## Options

### Basic Options
- `--dry-run`: Show what batches would be processed without making changes
- `--min-priority {low,medium,high}`: Minimum importance level to include (default: low = all valid suggestions)
- `--no-batch`: Disable smart batching (process each suggestion separately)
- `--max-batch-size N`: Maximum suggestions per batch (default: 4)

### Confirmation Behavior
- `--no-confirm`: Skip confirmation when no user selections are found (for unattended/silent operation)
- Also bypassed by: `--yes`, `--force`, `--approve-all`, `--skip-all-human`, `--approve-all-low`, `--approve-importance`, `--dry-run`

### Bulk Approval Options

These options reduce manual review for items with `needs-human-decision` status:

- `--agent-decide`: Let the judge agent evaluate each `needs-human-decision` suggestion with its own judgment instead of prompting you — the host's own agent on hosts with native subagents, or under `--exec-subagents` the model your session is running on (e.g. `codex:<chat model>` on Codex). An explicit `driver.subagent_runner` overrides the session model, and the host's floor runner (`codex:gpt-6-astra` on Codex) is used only when neither is available (see `references/human-decision-batch.md`). This is the non-interactive equivalent of choosing "Let the agent decide" in the review prompt. Unlike the blanket flags below, it is a **per-item** judgment that **salvages partially-valid suggestions** (trims them to their worthwhile core and applies that) rather than skipping them wholesale; only suggestions with nothing worthwhile are skipped (see "Let the Agent Decide" Mode in `references/human-decision-batch.md`). It does **not** bypass the no-selection confirmation for valid suggestions — combine with `--no-confirm` for fully unattended runs. `--claude-decide` / `--let-claude-decide` are accepted legacy spellings.
- `--approve-all-low`: Auto-approve all LOW importance items
- `--approve-all`: Auto-approve ALL items (requires `--yes` or `--force`)
- `--skip-all-human`: Skip all `needs-human-decision` and `validation_failed` items
- `--approve-importance LOW MEDIUM`: Auto-approve items at specified importance levels

### Safety Guardrails

- `--yes` / `-y`: Confirm bulk approval operations (required with `--approve-all`)
- `--force` / `-f`: Alias for `--yes`
- `--include-high`: Allow `--approve-all` to include HIGH importance items

### Resume/State Options

- `--resume`: Resume from last checkpoint, skip already-processed items
- `--fresh`: Discard this phase's recorded progress (decisions, processed items, prior-changes log) and dispatch every batch again. The target file must already be back at its pre-run bytes (copy it from the phase's backup, or roll the batches back with `util restore-batch`): a target still carrying the previous run's edits is refused (exit 3), since every batch would land twice. Earlier rollback points are kept aside, never overwritten.

### Batch Review Mode

- `--batch-review-mode {individual,by-importance,summary-only}`: How to present items for human review (default: by-importance)

### User Skip Filtering

If users have marked suggestions to skip in `report.md`, the orchestrator will:
1. Parse `{plan}/review-tasks/report.md` for `[x] Skip` markers
2. Filter out matching suggestions before processing
3. Report: `User skipped N suggestions: S001, S003, ...`

This happens automatically - no additional flags needed.

---

## Step-by-Step Execution

### 1. Validate Prerequisites

Check that required files exist:
```
{plan}/review-tasks/validation.json
{plan}/review-tasks/grouped.json
```

If not found, inform user to run `--review-tasks` first.

### 2. Run the Orchestrator

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions --plan-file "$PLAN_PATH" [options]
```

**IMPORTANT**: Pass `$PLAN_PATH` as given — the orchestrator resolves it to an OS-native absolute path itself. Do NOT wrap it in `$(realpath ...)`: on Git for Windows, `realpath` emits a POSIX `/c/...` path that a native Windows Python process cannot use.

**IMPORTANT**: Run this command in the foreground — do **not** run it detached. The orchestrator runs quickly — it only generates batch JSON, it does not apply changes — so 10 minutes is far more than enough.

The orchestrator will:
1. Load validation results and grouped suggestions
2. Filter to only `valid` suggestions
3. Group suggestions into efficient batches
4. Write output to `{plan}/apply-task-suggestions/orchestrator_output.json`
5. Exit — the driving agent handles the actual application

#### Zero-Finding and Zero-Selection Paths

The orchestrator handles four distinct no-op/early-exit scenarios:

1. **No valid findings** (`review-tasks/grouped.json` does not exist or contains zero suggestions): The orchestrator writes an empty `orchestrator_output.json` (with `batches: []`), marks the phase as **skipped** via `state_manager.mark_phase_skipped("apply-task-suggestions", reason="no actionable findings from review-tasks")`, calls `state.save()`, prints a user-facing message (`"No actionable task suggestions found — skipping apply-task-suggestions phase."`), and exits with code 0. No summary report is generated. `--status` shows the phase as `"skipped (no actionable findings from review-tasks)"`.

2. **All items user-skipped** (findings exist but every suggestion is marked as skipped in `user_selections.json` and/or `report.md`): The orchestrator writes an empty `orchestrator_output.json` (with `batches: []`), marks the phase as **skipped** via `state_manager.mark_phase_skipped("apply-task-suggestions", reason="all suggestions skipped by user")`, calls `state.save()`, prints `"All task suggestions were skipped by user — no changes applied."`, and exits with code 0. A minimal summary report is still generated (documenting what was skipped and why), so the user has an audit trail. `--status` shows `"skipped (all suggestions skipped by user)"`.

3. **No selection file exists** (`review-tasks/user_selections.json` missing AND no skip/approve marks in `report.md`): This is NOT a no-op — it means the user did not make any explicit selections. The orchestrator proceeds normally, treating all suggestions as approved (the default behavior, matching `apply-suggestions` semantics). However, unless `--no-confirm` or `--yes` is passed, the orchestrator triggers the no-selections confirmation prompt (step 2a) asking the user to confirm they want to apply all suggestions. If the user declines at the prompt, the phase is marked **skipped** via `state_manager.mark_phase_skipped("apply-task-suggestions", reason="user declined at no-selections prompt")`, `state.save()` is called, and the orchestrator exits with code 0.

4. **Suggestions exist but all are filtered out by CLI flags** (e.g., `--min-priority` filters everything): Same behavior as case 2 — write empty output, mark phase **skipped** with reason `"all suggestions filtered out by CLI flags"`, generate minimal summary report, exit 0. `--status` shows `"skipped (all suggestions filtered out by CLI flags)"`.

### 2a. Handle No-Selections Confirmation

After the orchestrator completes, check if its stdout contains `"status": "confirmation_needed"`.

**Under `--yes` / `--no-confirm` this marker is never emitted** (D6 row 11): the
orchestrator treats either flag as deliberate intent and applies the valid set
without asking, so there is nothing here to render. The prompt below is a
Python-emitted status, not a markdown judgment — if you see it, `--yes` was not
passed.

If present (attended runs only):
1. Display the warning message to the user
2. **Ask the user**:
   > "No user selections were found (no user_selections.json, consolidated_user_selections.json, or report.md edits detected). This will apply ALL {item_count} valid task suggestions. Continue?"
   > Options: "Yes, apply all" / "No, I need to make my selections first"
3. If user confirms: Re-run the orchestrator with `--no-confirm` appended
4. If user declines: Stop and inform the user to review the HTML report and export selections

If NOT present, proceed to step 3.

### 3. Display Decision Summary

After the orchestrator completes, run the display script to show the user which suggestions will be applied, skipped, need review, etc.:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util decisions --plan-file "$PLAN_PATH" --phase apply-task-suggestions
```

This prints a formatted summary with each suggestion's title and status. Display this output to the user before proceeding.

### 4. Read the Orchestrator Output

Read `{plan}/apply-task-suggestions/orchestrator_output.json`.

Extract the following key fields directly from the Read output (do NOT use Bash/python to parse — just read the JSON and understand it):
- `batches`: Array of batch objects, each with `prompt`, `section_key`, `prior_changes_id`, `suggestions`
- `needs_human_review`: Items requiring human decision
- `human_review_config`: Batch mode config for human review
- `summary`: Counts of valid, skipped, batches, etc.

### 5. Process Batches Sequentially

Use the batch data already loaded in step 4. Do NOT use Bash/python to re-parse or extract fields from the JSON file.

**Before the loop**, mark the phase start so ETA tracking has a wall-clock baseline. Run:
```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics start \
  --state-file "$STATE_FILE" --phase "apply-task-suggestions" --total-batches {total_batches}
```
Where `{total_batches}` is the length of the `batches` array.

### The Python write executor: `--exec-subagents` (an alternative to this loop)

Everything from here to the end of the batch loop is the **native-subagent** path:
this agent binds each batch's prompt with `util write-prompt`, snapshots the
artifact, spawns a subagent on the bound prompt file, diffs against the snapshot
and appends to the prior-changes log.

A host with no native subagent tool runs the *same* loop in Python instead. Add
`--exec-subagents` to the orchestrator invocation above and the phase schedules
itself in one process: batches in ascending `batch_index`, each one's snapshot/diff
classification completed and recorded **before** the next is dispatched, the
prior-batch context bound late per dispatch (the literal `{prior_changes_context}`
token never reaches a runner), `prior_changes.py append` and `metrics.py record`
called per batch, and the phase marked completed only after every batch verified.
The runner comes from `driver.subagent_runner` in `providers.yaml`; write
concurrency comes from `driver.max_concurrent_write_subagents` (default **1**, and
pinned to 1 for this phase regardless, because its batches all edit one artifact).

Do **not** combine the two: with `--exec-subagents` the phase finishes in that one
invocation and there is no batch left for this agent to run. It also writes this
phase's own summary report itself: the batch loop's outcome block names every item
the judge decided, `{phase}/summary.md` is written with the same sections the
*Generate Summary Report* step below describes, the recorded decisions are overlaid
onto the review report, and the phase is marked completed only once every batch
verified. Those steps below belong to the native path; do not run them a second time.

Three flags belong to that path and are worth knowing even on this one:

- `--dry-run-subagents` — full preflight, **zero dispatch**. Renders the exact
  command per batch, applies the invocation profile, the co-scheduling admission
  check and the `driver.write_paths` policy, writes
  `{phase}/subagent_dry_run.json` and exits 0 having started no child and changed
  nothing else. The recommended first unattended run on a new host.
- `--detach` — the phase self-daemonizes and returns a log path plus a `status`
  command to poll. Per-batch progress lands in `{phase}/.status.json` under
  `progress.write_subagents`, so an unattended write run is observable with no chat
  context at all. Never combine it with a host's own background primitive: on Claude
  host resolves *run detached* to its own background mechanism uses that
  mechanism and never passes `--detach`.
- Rollback, when a batch half-applies —
  `multi_llm.py util restore-batch --phase-dir <dir> --task-id <id>` (also
  `--all-failed`), invoked through the dispatcher the same way every other mode is.
  It restores exactly the files `{phase}/subagent_audit.jsonl` recorded as touched,
  from the pre-batch snapshot under `{phase}/pre_batch/{task_id}/`, and **refuses**
  a file whose current hash no longer matches what the audit recorded at completion
  (someone edited it since) unless `--force` is passed. A partial application never
  reverts itself: the run exits 3 naming this command, because an automatic revert
  would destroy the half-applied state a human needs to inspect.

For each batch (index N, starting at 1) returned by the orchestrator, you MUST:

1. **Bind the batch prompt** — Run:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util write-prompt \
     --phase-dir "{plan}/apply-task-suggestions" --task-id "{task.task_id}"
   ```
   `{task.task_id}` is this batch's `task_id` from `write_tasks.json` (`apply-task-batch-0`, `apply-task-batch-1`, … in dispatch order). The command rewrites the batch's prompt with the prior-batch context bound **now** — from `{plan}/prior_changes.jsonl` as it is at this moment, i.e. the batches step 8 has already appended — and the result contract appended: exactly the text the `--exec-subagents` executor would dispatch for this batch. It writes it to `{plan}/apply-task-suggestions/prompts/{task.task_id}.prompt.txt` and prints three lines: `[WRITE_PROMPT] <path>`, `[WRITE_PROMPT_LINES] <n>` and `[WRITE_PROMPT_CONTEXT] …`. Note the path and the line count for step 3. Never substitute `{prior_changes_context}` yourself and never hand the subagent `batch.prompt` from the JSON: the literal token must never reach a subagent.

   **Error handling**: an exit 3 names the problem (no `write_tasks.json` — re-run the orchestrator; an unknown task id — the known ids are listed). Do not fall back to the raw `batch.prompt`; stop and report.

   A `[WRITE_PROMPT_ORDER]` line (on stderr; the prompt is still written) names an earlier batch whose summary this prompt does not carry — recorded but not appended yet, or not finished: do what it says, then run this `util write-prompt` again before spawning the subagent.

2. **Read current tasks.md state and snapshot it** — Always read the latest version of tasks.md before each batch, then capture a pre-batch snapshot so the batch's effect can be verified in step 5 **without** relying on git. (tasks.md is frequently untracked — freshly created — and every `git diff` variant silently ignores fully-untracked files, so git CANNOT detect whether a batch changed it. Snapshot the file and diff against the snapshot instead.)

   The snapshot lives in the **workspace temp dir** at a deterministic path (each batch overwrites it; no cleanup step; the dir is self-gitignored). Resolve the project root first — if the command fails or prints nothing, STOP with the error: "multi-llm requires running inside a git repository". Use the `tasks_file` path from `orchestrator_output.json` as `$TASKS_PATH`:
   ```bash
   TASKS_PATH="<tasks_file from orchestrator_output.json>"
   PROJECT_ROOT="$(git rev-parse --show-toplevel)"
   BATCH_SNAPSHOT="$PROJECT_ROOT/.multi-llm/tmp/batch_snapshot_tasks_{plan_stem}.md"
   ```
   Where `{plan_stem}` is the plan filename without extension.

   Capture the snapshot with your host's file tools, not Bash: read `$TASKS_PATH`, then write its exact content to the snapshot path (use the absolute path — join the resolved project root with `.multi-llm/tmp/batch_snapshot_tasks_{plan_stem}.md`; a host file-write that creates parent directories needs no mkdir step and no Bash copy command). If `{PROJECT_ROOT}/.multi-llm/tmp/.gitignore` does not exist yet, also write it with content `*` so the temp dir ignores itself.

   This batch only ever touches the single `tasks.md` file, so one snapshot covers it. Keep `$BATCH_SNAPSHOT` for step 5.

3. **Spawn a subagent** whose whole prompt is: read the file at the `[WRITE_PROMPT]` path in full — through line `[WRITE_PROMPT_LINES]`, paging if a single read stops short — and follow it verbatim.
   - Use `general-purpose` subagent type
   - That is the entire contract: do not paste the prompt text, add instructions of your own, or hand the subagent the JSON. The file already contains all suggestions, the prior-batch context and the reply format (it ends with a JSON object the steps below read)
4. **Wait for completion** - Do NOT parallelize batch processing

5. **Verify batch outcome** — After the subagent completes (or fails), determine the batch outcome by inspecting actual file state rather than relying solely on the subagent's exit status. **Do NOT use `git diff` / `git diff --stat` as the change detector**: every `git diff` variant silently ignores fully-untracked files, and tasks.md is frequently freshly-created and untracked — so git would report "no changes" even when the subagent successfully edited it, producing a false clean-failure. Instead, diff the file against the pre-batch snapshot captured in step 2:
   ```bash
   diff -u "$BATCH_SNAPSHOT" "$TASKS_PATH"
   ```
   An empty diff means the file is byte-for-byte unchanged; a non-empty diff means it was modified. The snapshot diff is the authoritative, fully git-independent detector — no git intent-to-add step is needed here (flows that genuinely need untracked files visible to git diffs, like code review, handle that inside their Python orchestrator via `utils/git_utils.intent_to_add_untracked`). Classify the result:
   - **Success**: The snapshot diff is non-empty **and** the expected changes are present (grep spot-check the modified tasks.md for the intended task IDs / fields from the batch).
   - **Failure (clean)**: The subagent failed **and** the snapshot diff is empty (tasks.md is byte-for-byte identical to its pre-batch snapshot).
   - **Not applied**: The subagent reported `applied` **and** the snapshot diff is empty: its edits did not land. Dispatch the batch once more, with one sentence added to its prompt saying the previous attempt answered `applied` but changed no file, and verify again; if nothing changed this time either, it is a clean failure (record it `failed`), never a success.
   - **Partial application**: The snapshot diff is non-empty but the expected changes are incomplete, **or** the subagent failed but the snapshot diff is non-empty.
   - **Declined items** (fix round 18): an item the reply lists in `declined` with a reason was left unapplied on purpose (for example, the implementation record calls that code deliberate). It is never applied and never a partial application: a batch whose every item is in `ids` or in `declined` is a success (a no-op when it changed nothing), whatever word its `status` carries, `failed` included: record it `--status completed`. An item in neither list, an id in both, or a `declined` entry without a reason is a partial application.

   There is **no snapshot cleanup step**: the snapshot lives in the self-gitignored workspace temp dir and is simply overwritten by the next batch. On **partial application** the loop stops (below), so `$BATCH_SNAPSHOT` still holds the pre-batch content for a human to inspect.

   **Partial application handling**: If verification detects a partial application, **stop the batch loop and surface the issue for human review**. Do not continue to subsequent batches. Log the partial application details and prompt the human operator to resolve the state before resuming. When the reply's report attests at least one suggestion applied (in `ids`, with a `status` other than `failed`) and leaves others out of both `ids` and `declined`, give the user both ways forward and let them choose: restore the batch (`util restore-batch`) or fix the cause, then resume; **or** keep what the batch applied and go on without the suggestions it left out — record it with step 7's `util batch-done` as `--status completed` plus one `--skipped <id>` per suggestion left out, append its summary (step 8) and continue with the next batch. A resume that does neither hands the same batch out again and stops the same way.

6. **Extract summary** — The subagent's reply ends with one JSON object (`{"status", "ids", "declined", "files_touched", "summary", "notes"}`: the result contract the prompt file carries). Take its `summary` as the one-line summary; its `status` (`applied` / `no-op` / `failed`) and `files_touched` are evidence for step 5, never a substitute for the snapshot diff. If the reply carries no such object, compress the reply into a single sentence instead.

   **Normalize** the summary: collapse any newlines or multiple spaces to a single space, trim leading/trailing whitespace, and truncate to 200 characters if needed.

7. **Record the batch outcome (only after verification)** — This step runs **only** after step 5 has classified the batch as a success or a clean failure. It must **never** run for a partially-applied batch (the loop stops there). Run:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util batch-done \
     --phase-dir "{plan}/apply-task-suggestions" --task-id "{task.task_id}" --status {batch_status}
   ```
   `{batch_status}` is `completed` for a success (a verified no-op included) and `failed` for a clean failure — add `--reason "{compact reason}"` to a `failed` one. It prints one `[BATCH_DONE] {task.task_id} {batch_status} (N item(s) recorded)` line and writes the batch's record into `state.json`: the same `task_status` entry the `--exec-subagents` executor writes for this batch, plus every suggestion in it as processed. That record is what a later `--resume` reads to skip this batch (a `failed` record keeps it eligible for another try) and what makes `status` read the phase `in_progress`. Run it **before** step 8's append: a run that dies between the two leaves a record `--resume` honours, never a log entry `--resume` would re-apply. An exit 3 names the problem (no `write_tasks.json`, an unknown task id); treat it as a stop, not a warning.
   When the reply's `declined` lists suggestions (each `{"id", "reason"}`), add `--declined "{id}={reason}"` for each, with `--status completed`: each prints a `[BATCH_DECLINED]` line — list that suggestion in the summary under `## Declined by their batch (not applied)`, with its id and reason (never under `## Applied Changes`, not even marked "Not applied"), and name it in your report; it is never counted as applied. `--skipped {id}` records a suggestion the user chose to skip (above) the same way, as `[BATCH_SKIPPED]`, listed under `## Skipped at your request (not applied)`.

8. **Append to prior changes (only after verification)** — This step runs **only** after step 5 has confirmed success or clean failure. It must **never** run for partially-applied batches. Pass the summary via stdin:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util prior-changes append \
     --output-dir "{plan}" \
     --id "{batch.prior_changes_id}" --phase "apply-task-suggestions" --summary-stdin <<'SUMMARY_EOF'
   {normalized_summary}
   SUMMARY_EOF
   ```
   `--output-dir` is the plan directory `{plan}` (the one holding `state.json`): the one
   log every write phase of this plan shares, the one `util write-prompt` binds the next
   batch's prompt from, and the one the `--exec-subagents` executor appends to — scoped
   per phase by `--phase`, never a per-phase file.
   The `--id` is `batch.prior_changes_id` — read it off the batch (it is the same value in `write_tasks.json`), never construct one. An empty `--id` writes nothing and exits 3 naming the ids there: run the append again with the batch's id.
   The batcher emits **many** batches for the same `section_key`, and the log keeps one
   entry per `(id, phase)`, the newest: an id two batches share leaves only the last
   one's summary (exit 0), so every later batch reads a prior-changes context missing
   its predecessors. `prior_changes_id` is that key plus a digest of the
   batch's own items — unique per batch, and identical if the same batch is re-dispatched.
   Do **not** use the batch loop index. The `--phase` is `"apply-task-suggestions"`.

   For **clean failures**, use summary: `(batch failed — {compact reason}, verified no file changes)`
   When a `--resume` dispatches that batch again, append its new summary under the same `--id`: it replaces the failure line in every later batch's prompt (`Replaced entry …` on stderr).

   **Error handling**: If `append` fails, log a warning but do not abort the batch loop.

9. **Log the result** - Track success/failure for the summary
10. **Record metrics** — Run:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics record \
     --state-file "$STATE_FILE" --phase "apply-task-suggestions" \
     --label "Batch {N} ({section_key})" --task-id "{task.task_id}" --subagent-type "general-purpose" \
     --tokens {token_count} --tool-uses {tool_uses} --duration-ms {duration_ms} \
     --total-batches {total_batches} --batch-index {N}
   ```
   Where `token_count`, `tool_uses`, `duration_ms` come from whatever your subagent mechanism reports, and `{task.task_id}` is the id you gave `util batch-done`. Omit any flag it does not report. Never pass `0` for an unknown value; omit the flag — a made-up zero is averaged into the phase totals as a real measurement. The script prints an `[ETA]` line to stderr after each call; for a batch `util batch-done` recorded `failed` it says the batch failed and why, never "done".

**CRITICAL**: Process batches ONE AT A TIME. Never spawn multiple subagents simultaneously.

**The last subagent returning is not the end of the phase.** Every step below this loop still owes work — the human-decision items, the summary report, and whatever record this mode ends with. Do not end your turn between the last batch and that final step, and do not announce the work as done before it: on a host that runs one headless turn the announcement *is* the end of the run, and a phase whose bytes landed but whose record never did is indistinguishable afterwards from one that never ran. The loop itself takes the same rule — stay in the turn until the batch you dispatched has returned and been verified.

**After the loop completes**, mark the phase finish:
```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics finish \
  --state-file "$STATE_FILE" --phase "apply-task-suggestions"
```

### 6. Handle Human Decision Items

Follow the human decision batch mode process in `references/human-decision-batch.md`.

**Auto-route report-pre-marked suggestions first**: before prompting for anything, partition `needs_human_review` into (a) the **pre-marked judge set** — every suggestion whose `group_id` is in `human_review_config.judge_decide_item_ids` or that carries `decision_mode == "judge_auto_decide"` — and (b) the remaining **interactive set**. Run **"Let the Agent Decide" Mode** (per the criteria in `references/human-decision-batch.md`) on the pre-marked judge set **without any prompt**, then handle only the interactive set with the flow below. These suggestions were chosen in the report's "Let the agent decide" dropdown/checkbox; they are the per-item equivalent of `--agent-decide` scoped to just those suggestions.

**Check `human_review_config.decision_mode` first**: if it is `"judge_auto_decide"` (the user passed `--agent-decide`), do NOT prompt the user — go straight to "Let the Agent Decide" Mode and evaluate every `needs-human-decision` suggestion autonomously per the criteria in that reference. By default, **partially-valid suggestions are salvaged** (rewritten to their worthwhile core and applied) rather than skipped; only suggestions with nothing worthwhile are skipped entirely.

Context line for individual review display: `Type: {type}, Task: {task_reference}`

### 7. Generate Summary Report

After all batches are processed, create `{prefix}_applied_task_suggestions.md`:

```markdown
# Applied Task Suggestions Report

**Plan**: /path/to/plan.md
**Tasks file**: /path/to/tasks.md
**Generated**: YYYY-MM-DD HH:MM:SS

## Summary
- Batches processed: N
- Suggestions applied: N
- Suggestions declined by their batch (not applied): N — only when a batch declined any; each one is listed under `## Declined by their batch (not applied)` below, never under `## Applied Changes`
- Suggestions skipped at your request (not applied): N — only when you recorded one `--skipped`; each one is listed under `## Skipped at your request (not applied)` below, never under `## Applied Changes`
- Suggestions skipped: N
- Human decisions made: N
- Decided by the judge agent: N (A approved, V salvaged, S skipped) — includes `--agent-decide`, the batch "Let the agent decide" option, and per-item "Let the agent decide" selections

## Batching Efficiency
- Total suggestions: N
- Total batches: N
- Subagent calls saved: N (X% efficiency gain)

## Applied Changes

### Batch 1 (Task: T001)
**Suggestions**: 3
**Type**: modification

1. **[Suggestion Title]** - Applied
   Description: [Brief description of what was changed in tasks.md]

2. **[Suggestion Title]** - Applied
   ...

### Batch 2 (Task: T003)
...

## Declined by their batch (not applied)

(Only when a batch declined a suggestion — a `[BATCH_DECLINED]` line from `util batch-done`. Never list it under `## Applied Changes`, not even marked "Not applied": its batch's block above says `**Not applied**: 1 declined by the batch (listed under "Declined by their batch (not applied)" below)` instead.)

- **[Suggestion Title]** (`{id}`, apply-task-batch-0) — {the reason the batch gave}

## Skipped at your request (not applied)

(Only for a suggestion recorded `--skipped` — a `[BATCH_SKIPPED]` line; never under `## Applied Changes` either.)

- **[Suggestion Title]** (`{id}`, apply-task-batch-0) — skipped at your request

## Decided by the judge agent (N)

judge: {judge}

Suggestions whose decision was offloaded to the judge agent — via `--agent-decide`, the batch "Let the agent decide" option, or a per-item "Let the agent decide" selection. Read these from `state.json`: the `human_decisions_{phase}` entries whose `batch_context.decision_source` is `judge_auto_decide` or `judge_auto_decide_salvage` (a run recorded before the judge rename may carry them as `claude_auto_decide` / `claude_auto_decide_salvage`: the same two markers, read the same way). Omit this section if there are none. `{judge}` is the runner spec that actually judged (e.g. `codex:<chat model>`, the session model, under `--exec-subagents` on Codex — or an explicit `driver.subagent_runner` override, or the `codex:gpt-6-astra` host floor when that is what resolved), or, on a host with native subagents, the label recorded in the decision's `judge` field — the model the judging subagent reported, e.g. `claude-sonnet-5-5 (claude-code host agent)`. Print it as recorded; never write "claude" for a judge that was not Claude. A salvaged item is "Salvaged" everywhere, never "Approved", even though state.json stores it with `decision: approved` plus the `judge_auto_decide_salvage` marker.

### [Suggestion Title] ({importance}) — Approved
**Reason**: {reason}

### [Suggestion Title] ({importance}) — Salvaged
**Kept**: {salvaged_description}
**Dropped**: {dropped}

### [Suggestion Title] ({importance}) — Skipped
**Reason**: {reason}

## Skipped Suggestions

### [Suggestion Title]
**Reason**: Invalid / User skipped / Error
...
```

   Generate resource usage:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics report \
     --state-file "$STATE_FILE" --phase "apply-task-suggestions"
   ```
   Include the output (if non-empty) at the end of the summary report.

   **Check the task graph the batches left.** Each batch edited one corner of `tasks.md` and none saw the whole of it. Pass the `tasks_file` path from `orchestrator_output.json` (the path the orchestrator printed as `Tasks file:`), the same path the batch loop's snapshot step sets as `$TASKS_PATH`:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util check-tasks "<tasks_file from orchestrator_output.json>"
   ```
   Every `[TASKS_GRAPH_WARNING]` line goes into the summary report under a `## Consistency warnings` heading and into what you tell the user; do not edit `tasks.md` yourself to clear one. `[TASKS_GRAPH_OK]` needs no mention.

   **Then update the HTML review report** so the decisions show up there too. This overlays every human/judge-agent decision recorded in `state.json` onto the existing `{plan}/review-tasks/report.html`, giving each finding an **Approved / Salvaged / Skipped** badge plus an expandable detail with the kept/dropped notes:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util report \
     regenerate-decisions \
     --phase-dir "$(dirname "$STATE_FILE")/review-tasks" \
     --state-file "$STATE_FILE" \
     --apply-phase "apply-task-suggestions"
   ```
   Best-effort: if `report_data.json` is missing from the review dir (the review predates this feature), the command prints a notice and exits 0 without changing the report — just continue. The same holds when the phase recorded no human or judge decision: the report stays as the review wrote it, and the command says so (never edit the report yourself).

### 8. Mark Phase Completed

After the summary report is generated, mark the apply-task-suggestions phase as completed in state.json:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions --plan-file "$PLAN_PATH" --mark-completed
```

This ensures subsequent phases (e.g., `--implement`) recognize that task suggestions have been applied.

**Then report to the user** following `references/summary-format.md`, naming the summary report and every other file this phase wrote. The suggestions went to the task list, which that call's message names (`its batches edited …`), never to the plan: say so in those words.

---

## JSON Output Structure

The orchestrator outputs JSON with batches:

```json
{
  "plan_file": "/path/to/plan.md",
  "tasks_file": "/path/to/tasks.md",
  "tasks_file_backup": "/path/to/my-feature/apply-task-suggestions/tasks-backup.md",
  "prefix": "my-feature",
  "output_dir": "/path/to/my-feature/",
  "timestamp": "2024-01-21T12:00:00",
  "batches": [
    {
      "suggestions": [
        {
          "index": 0,
          "title": "Add integration test task",
          "description": "...",
          "type": "addition",
          "reference": "Task T001: Setup DB schema",
          "task_reference": "Task T001",
          "importance": "HIGH"
        },
        {
          "index": 1,
          "title": "Clarify acceptance criteria",
          "description": "...",
          "type": "clarification",
          "reference": "Task T001: Setup DB schema",
          "task_reference": "Task T001",
          "importance": "MEDIUM"
        }
      ],
      "section_key": "task_t001_setup_db_schema",
      "prior_changes_id": "task_t001_setup_db_schema#9ae4c73b",
      "batch_type": "mixed",
      "suggestion_count": 2,
      "priority_score": 5.0,
      "prompt": "Apply the following 2 related task suggestions..."
    }
  ],
  "to_apply": [...],
  "needs_human_review": [...],
  "batching_stats": {
    "total_suggestions": 8,
    "total_batches": 3,
    "subagent_calls_saved": 5,
    "efficiency_gain_percent": 62.5,
    "batching_enabled": true
  },
  "human_review_config": {
    "mode": "by-importance",
    "batch_enabled": true,
    "decision_mode": "interactive",
    "prompt_strategy": "single_batch",
    "by_importance": {
      "HIGH": [...],
      "MEDIUM": [...],
      "LOW": [...]
    },
    "total_count": 2,
    "batch_prompt_template": "batch_approval_v1"
  },
  "resume_info": {
    "previously_processed": [],
    "previous_decisions": {},
    "can_resume": false
  },
  "summary": {
    "total_groups": 10,
    "valid_count": 8,
    "needs_human_count": 2,
    "skipped_count": 0,
    "batch_count": 3,
    "validation_failed_count": 0,
    "auto_approved_count": 0
  }
}
```

---

## Example Execution

```
User: /multi-llm:multi-llm --apply-task-suggestions plans/my-feature.md

Agent:
1. Checks for prerequisite files - found
2. Runs orchestrator to get batched task suggestions
3. Gets 8 valid suggestions in 3 batches, 2 needs-human-decision

   Batch 1: 3 modifications for Task T001 (priority: 7.0)
   Batch 2: 2 additions for Plan Coverage (priority: 5.0)
   Batch 3: 1 deletion for Task T005 (isolated, priority: 4.0)

   Efficiency: 5 subagent calls saved (62.5% gain)

For each batch (sequentially):
- Reads current tasks.md
- Binds the batch's prompt with `util write-prompt` and spawns one subagent on the bound file
- Waits for completion
- Logs results

For needs-human-decision items:
- Asks the user for a decision
- Applies or skips based on response

4. Generates summary report
5. Reports completion with file paths
```

---

## Batch Prompt Format

Each batch carries a prompt template in its `prompt` field (unbound: `util write-prompt` is what binds it for a subagent). For single-suggestion batches:

```
Apply the following task suggestion to the tasks file:

**Plan file** (context only — do NOT modify): {plan_path}
**Tasks file** (target — apply changes HERE): {tasks_path}
**Suggestion**: {title}
**Type**: {type}
**Task reference**: {task_reference}
**Importance**: {importance}

**Details**:
{description}

## Type-Specific Instructions

### For "addition" type:
- Add new task(s) using `### Task T0XX:` format
- Assign the next available sequential task ID
- New tasks MUST include ALL canonical fields:
  - `files_to_modify`, `files_to_create`
  - `estimated_complexity`
  - `executor_role` (`agent`, or `human` for a manual step)
  - `depends_on`
  - Acceptance criteria
- After adding, regenerate the dependency graph and header metadata (task count, complexity summary)

### For "modification" type:
- Update the specified task fields (description, dependencies, acceptance criteria, etc.)
- Modified tasks MUST preserve or explicitly update ALL canonical fields — never silently drop fields
- If modifying `depends_on`, regenerate the dependency graph

### For "deletion" type:
- Remove the specified task entirely
- Scan ALL tasks globally for `depends_on` references to the deleted task ID(s) and remove them
- NEVER renumber surviving task IDs — gaps in ID sequence are acceptable and expected
- After deletion, regenerate the dependency graph and header metadata (task count, complexity summary)

### For "clarification" type:
- Rewrite the task description and/or acceptance criteria for clarity
- ALL canonical fields must be preserved — do not drop any fields during clarification

## General Instructions
1. Read the current tasks.md file first
2. Read the plan file for context (but do NOT modify it)
3. Apply the suggested change appropriately
4. Ensure the change integrates smoothly with existing tasks
5. Do NOT make any other changes beyond this suggestion

Return a brief summary of what was changed.
```

For multi-suggestion batches:

```
Apply the following N related task suggestions to the tasks file (Task reference: {task_reference}):

**Plan file** (context only — do NOT modify): {plan_path}
**Tasks file** (target — apply changes HERE): {tasks_path}
**Batch type**: {batch_type}
**Suggestions in this batch**: N

---
### Suggestion 1: {title}
- **Type**: {type}
- **Task reference**: {task_reference}
- **Importance**: {importance}

**Details**:
{description}

---
### Suggestion 2: {title}
...

---

## Type-Specific Instructions

### For "addition" type:
- Add new task(s) using `### Task T0XX:` format, assign next available ID
- New tasks MUST include ALL canonical fields: `files_to_modify`, `files_to_create`, `estimated_complexity`, `executor_role`, `depends_on`, and acceptance criteria
- After adding, regenerate the dependency graph and header metadata

### For "modification" type:
- Update the specified task fields
- MUST preserve or explicitly update ALL canonical fields — never silently drop fields
- If modifying `depends_on`, regenerate the dependency graph

### For "deletion" type:
- Remove the task and scan ALL tasks globally for `depends_on` references to the deleted ID(s)
- NEVER renumber surviving task IDs — gaps are acceptable
- After deletion, regenerate the dependency graph and header metadata

### For "clarification" type:
- Rewrite task description/criteria for clarity
- ALL canonical fields must be preserved

## General Instructions

1. Read the current tasks.md file first
2. Read the plan file for context (but do NOT modify it)
3. Apply ALL suggestions in this batch, processing them in order
4. For each suggestion:
   - Locate the referenced task
   - Apply the change according to its type
   - Ensure changes integrate smoothly
5. Do NOT make any changes beyond these specific suggestions
6. If suggestions affect the same task, apply them intelligently
7. Before applying each suggestion, check if tasks.md already reflects a similar change (from a previously applied batch). If a suggestion is already addressed, note it as "already applied" in the summary and move on

## Return Format

Return a brief summary for EACH suggestion applied:
```
Suggestion 1: [What was changed]
Suggestion 2: [What was changed]
Suggestion N: Already addressed by prior changes - skipped
...
```
```

---

## Critical Rules

1. **SEQUENTIAL BATCHES**: Never parallelize batch processing - one batch at a time
2. **ALWAYS READ FIRST**: Read tasks.md before each batch to get latest state
3. **USE THE BOUND PROMPT FILE**: hand each subagent only the `[WRITE_PROMPT]` file `util write-prompt` wrote — never the raw `prompt` field of the JSON, which carries an unbound `{prior_changes_context}` token
4. **USE SUBAGENTS**: always **spawn subagents** to do the work
5. **PRESERVE BACKUP**: The orchestrator automatically backs up tasks.md to `apply-task-suggestions/tasks-backup.md` before any modifications. Do not overwrite this backup. The `tasks_file_backup` field in orchestrator_output.json contains the path.
6. **TRACK EVERYTHING**: Log every applied/skipped suggestion for the report
7. **DELETIONS ARE ISOLATED**: Deletion suggestions are always in their own batch
8. **PLAN IS READ-ONLY**: The plan file is used for context only — never modify it during this phase
9. **STABLE TASK IDS**: Never renumber surviving task IDs after deletions — IDs are stable identifiers

---

## Disabling Batching

To process suggestions one-at-a-time (legacy mode):

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions --plan-file "$PLAN_PATH" --no-batch
```

This is useful for:
- Debugging issues with batched edits
- Very sensitive task definitions where each edit needs verification
- When batching produces unexpected results

---

## Recovery Workflows

### Resuming Interrupted Sessions

If a session is interrupted, progress is saved automatically:

`--resume` re-emits only what is left: every batch the loop recorded with `util batch-done` (step 5) is dropped, a batch recorded `failed` is dispatched again, and a batch the prior-changes log names that no record says finished is **refused** — exit 3 with a `[RESUME_REFUSED]` block naming the batch and the `util batch-done` call that records it (or `--fresh`, once the target is back at its pre-run bytes). Re-emitting such a batch would apply it twice.

```bash
# Resume from where you left off
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions \
  --plan-file "$PLAN_PATH" \
  --resume

# Or start fresh, clearing all previous progress
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions \
  --plan-file "$PLAN_PATH" \
  --fresh
```

### Bulk Approval Examples

```bash
# Approve all LOW importance items automatically
--approve-all-low

# Approve all MEDIUM and LOW importance items
--approve-importance MEDIUM LOW

# Approve everything (DANGEROUS - requires confirmation)
--approve-all --yes

# Skip all items requiring human review
--skip-all-human
```

---

## Workflow Comparison

### Full Workflow Mode
1. Run `full`: task review and apply happen as sequential phases of the
   workflow — Phase 3b reviews the tasks, Phase 3c applies the task suggestions
   automatically.

### Separate Mode
1. Run `review-tasks` (task review only).
2. The user reads the task suggestions in the generated report.
3. Run `apply-task-suggestions` later.

The separate mode gives users time to:
- Review task suggestions before deciding to apply them
- Skip certain suggestions manually via the HTML report
- Apply suggestions in a separate session
- Verify the validation results are accurate

---

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| No valid suggestions | Exit early with message, mark phase skipped |
| All needs-human-decision | Prompt user for each |
| tasks.md changed since review | Read latest version before each batch |
| Suggestion references deleted task | Note as "already addressed" or skip |
| Same task in multiple batches | Process sequentially, re-read tasks.md between batches |
| Missing validation file | Treat all as needs-human-decision |
| Task ID conflicts on addition | Assign next available ID based on current tasks.md state |

---

## Error Types and Recovery

The orchestrator distinguishes between different error types:

| Error Type | Status | Recoverable | Recovery Action |
|------------|--------|-------------|-----------------|
| Parsing error | `validation_failed` | Yes | Manual review or re-run review-tasks |
| Timeout | `validation_failed` | Yes | Re-run with increased timeout |
| Rate limited | `validation_failed` | Yes | Wait and re-run |
| Model failure | `needs-human-decision` | No | Review manually |
| Genuine ambiguity | `needs-human-decision` | No | Review manually |

The `validation_failed` status is different from `needs-human-decision`:
- `validation_failed`: Technical error during validation, can be retried
- `needs-human-decision`: LLM determined item genuinely requires human judgment
