# Apply Suggestions Mode Instructions

Applies validated suggestions from a plan review to the original plan file, using smart batching to minimize subagent calls while maintaining edit safety.

## Usage

```bash
/multi-llm:multi-llm --apply-suggestions <plan_path> [options]
```

## Prerequisites

This mode requires a completed plan review with validation. The following files must exist in `{plan}/review-plan/`:
- `validation.json` - Validation results
- `grouped.json` - Grouped suggestions

If these files don't exist, run `--review-plan` first.

### User Selections (Auto-Detected)

If available, the following file is auto-detected from `{plan}/review-plan/`:
- `user_selections.json` - User decisions from the HTML report (skips, validation overrides, edited descriptions)

HTML selections take precedence over markdown checkbox selections.

### Consolidated Decisions (Auto-Detected)

If the review-plan phase included a consolidation step, the following files are auto-detected from `{plan}/review-plan/`:
- `consolidated-report.md` - Consolidated suggestion report
- `consolidated_user_selections.json` - User decisions on consolidated groups

No additional flags are needed — consolidation integration is automatic. Specifically:
- **C-level** (consolidated) decisions are merged with **G-level** (per-group) decisions automatically
- **C-level skips** are unioned with **G-level skips** (both sources contribute to the final skip set)
- **C-level validation overrides** cascade to all underlying groups, but **G-level overrides take precedence** (more specific wins)
- If `grouped.json` has changed since consolidation was run, the orchestrator will warn about staleness. Use `--accept-stale-consolidation` to proceed anyway.

## Smart Batching

The orchestrator now groups related suggestions into batches for efficient processing:

### Batching Heuristics

1. **Section Proximity**: Suggestions targeting the same section are grouped together
2. **Type Compatibility**:
   - Deletions are ALWAYS isolated (one per batch) to prevent conflicts
   - Additions, modifications, and clarifications can be batched together
3. **Size Limits**: Max 4 suggestions per batch, max 2500 chars total description
4. **Priority Ordering**: Batches are sorted by priority score (higher importance first)

### Efficiency Gains

With batching, 10 suggestions might become 3-4 batches:
- **Before**: 10 subagent calls (one per suggestion)
- **After**: 3-4 subagent calls (grouped by section)
- **Savings**: 60-70% reduction in API calls

## Process

1. **Load Validation Results**: Read the validation JSON to get validated suggestions
2. **Filter Suggestions**:
   - Only process suggestions with `status: "valid"`
   - Exclude suggestions marked `[x] Skip` in `report.md`
3. **Smart Batching**: Group related suggestions into batches
4. **Handle Human Decisions**: For `needs-human-decision` items, **ask the user** — each rendered question also offers a per-item **Let the agent decide** option that offloads just that one item's judgment to a subagent. Or, if `--agent-decide` was passed, let the judge agent decide every item up front — or pre-marked in the report's *Let the agent decide* dropdown/checkbox, which routes just those suggestions to the judge without prompting. See step 6. **Under `--yes` (or `--non-interactive`) this site is never rendered** (D6 row 10): `--yes` sets `--agent-decide` itself, so every item goes through the judged/deferred path up front and no item — and no batched approve-all/skip-all UI — can block.
5. **Batch Application**: Process each batch with a single subagent:
   - Spawn a subagent with the batch prompt
   - Wait for completion before moving to the next batch
   - This prevents conflicts from concurrent edits
6. **Generate Report**: Create `{plan}/apply-suggestions/summary.md` with results

## Output Files

```
plans/todo/my-feature/
├── state.json                           # Session state (plan-local)
├── review-plan/                         # Input files from review phase
│   ├── grouped.json
│   ├── validation.json
│   └── backup.md
└── apply-suggestions/                   # Output files from this phase
    ├── summary.md                       # Summary of applied changes
    └── results.json                     # Detailed application results
```

## Options

### Basic Options
- `--dry-run`: Show what batches would be processed without making changes
- `--min-priority {low,medium,high}`: Minimum importance level to include (default: low = all valid suggestions)
- `--include-low`: [DEPRECATED] No longer needed, low is now default. Use `--min-priority` to filter.
- `--no-batch`: Disable smart batching (process each suggestion separately)
- `--max-batch-size N`: Maximum suggestions per batch (default: 4)

### Scope Policy
- `--scope-policy expand|preserve`: which validated suggestions may be applied (D6 row 16, never asked). Pass it only when the user typed it. Left out, the apply keeps the policy on record for its review round: an earlier apply's typed override, else the review's, else `expand`. A typed value overrides the review's and is kept for this apply's later runs, `--resume` and `--mark-completed` included. Under `expand` nothing changes.
- Under `preserve` only suggestions validated `Within scope` for this review round, and unchanged since, are handed out. The rest are **deferred**: named on `[SCOPE_DEFERRED]` lines, in the result line's `notice` and in `summary.md`, never batched, and neither skipped, failed nor applied. Report them as deferred and never apply one yourself: no approval flag (`--yes`, `--approve-all`, `--agent-decide`, `--force`, …) releases them, and a later run with `--scope-policy expand` does. A phase whose eligible items are all done completes with its deferrals kept.
- A `preserve` writer declines an item it cannot complete inside the scope. A decline whose reason starts with `SCOPE BLOCKER:` (the agreed requirement itself cannot be met) stops the apply at exit 3 with `[SCOPE_BLOCKER]`, naming the ways forward.

### Confirmation Behavior
- `--no-confirm`: Skip confirmation when no user selections are found (for unattended/silent operation)
- Also bypassed by: `--yes`, `--force`, `--approve-all`, `--skip-all-human`, `--approve-all-low`, `--approve-importance`, `--approve-validation-failed`, `--dry-run`

### Bulk Approval Options

These options reduce manual review for items with `needs-human-decision` status:

- `--agent-decide`: Let the judge agent evaluate each `needs-human-decision` item with its own judgment instead of prompting you — the host's own agent on hosts with native subagents, or under `--exec-subagents` the model your session is running on (e.g. `codex:<chat model>` on Codex). An explicit `driver.subagent_runner` overrides the session model, and the host's floor runner (`codex:gpt-6-astra` on Codex) is used only when neither is available (see `references/human-decision-batch.md`). This is the non-interactive equivalent of choosing "Let the agent decide" in the review prompt. Unlike the blanket flags below, it is a **per-item** judgment that **salvages partially-valid items** (trims them to their worthwhile core and applies that) rather than skipping them wholesale; only items with nothing worthwhile are skipped (see "Let the Agent Decide" Mode in `references/human-decision-batch.md`). It does **not** bypass the no-selection confirmation for valid items — combine with `--no-confirm` for fully unattended runs. `--claude-decide` / `--let-claude-decide` are accepted legacy spellings.
- `--approve-all-low`: Auto-approve all LOW importance items
- `--approve-all`: Auto-approve ALL items (requires `--yes` or `--force`)
- `--skip-all-human`: Skip all `needs-human-decision` and `validation_failed` items
- `--approve-importance LOW MEDIUM`: Auto-approve items at specified importance levels
- `--approve-validation-failed`: Auto-approve items that had recoverable validation failures (parsing errors, timeouts)

### Safety Guardrails

- `--yes` / `-y`: Confirm bulk approval operations (required with `--approve-all`)
- `--force` / `-f`: Alias for `--yes`
- `--include-high`: Allow `--approve-all` to include HIGH importance items

### Revalidation Options

When validation failed due to parsing errors or timeouts, you can retry:

- `--revalidate`: Re-run validation only on items with `validation_failed` status
- `--revalidate-model MODEL`: Use a different model for retry (e.g., `cursor-agent:opus`)
- `--revalidate-all-human`: Also re-validate all `needs-human-decision` items

A run with `--revalidate` or `--revalidate-model` stops at a revalidation marker: see *When Validation Fails, and `--revalidate`* under Recovery Workflows.

### Resume/State Options

- `--resume`: Resume from last checkpoint, skip already-processed items
- `--fresh`: Discard this phase's recorded progress (decisions, processed items, prior-changes log) and dispatch every batch again. Put the plan back at its pre-run bytes first, or every batch lands twice: copy it from `{phase}/backup.md` (the plan as this phase found it when it emitted its batches); after an `--exec-subagents` run, `util restore-batch` can roll the batches back newest-first instead. The native loop keeps no rollback point per batch: its per-batch snapshot holds only the last bound batch's pre-batch bytes (the next batch replaces it), and `util restore-batch` has nothing of a native run's. Only after an `--exec-subagents` run is a target still carrying that run's edits refused (exit 3); after a native run, check the plan yourself. Earlier rollback points are kept aside, never overwritten.
- `--skip-human-review`: [DEPRECATED] Use `--skip-all-human` instead

### Batch Review Mode

- `--batch-review-mode {individual,by-importance,summary-only}`: How to present items for human review (default: by-importance)

### User Skip Filtering

If users have marked suggestions to skip in `report.md`, the orchestrator will:
1. Parse `{plan}/review-plan/report.md` for `[x] Skip` markers
2. Filter out matching suggestions before processing
3. Report: `User skipped N suggestions: S001, S003, ...`

This happens automatically - no additional flags needed.

---

## Step-by-Step Execution

### 1. Validate Prerequisites

Check that required files exist:
```
{plan}/review-plan/validation.json
{plan}/review-plan/grouped.json
```

If not found, inform user to run `--review-plan` first.

### 2. Run the Orchestrator

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions --plan-file "$PLAN_PATH" [options]
```

**IMPORTANT**: Pass `$PLAN_PATH` as given — the orchestrator resolves it to an OS-native absolute path itself. Do NOT wrap it in `$(realpath ...)`: on Git for Windows, `realpath` emits a POSIX `/c/...` path that a native Windows Python process cannot use.

**IMPORTANT**: Foreground or detached depends on who runs the batches. On the native-subagent path (no `--exec-subagents`), run this command in the foreground — do **not** run it detached: there the orchestrator only generates batch JSON, it does not apply changes, so 10 minutes is far more than enough (and `--detach` implies `--exec-subagents`, which would hand the batches to the executor). With `--exec-subagents` (the Python write executor, below) it is the other way round: this one command dispatches, verifies and records every batch itself, so it **does** apply the changes and runs as long as all the batches together. On that path **run detached**: add `--detach` (which implies `--yes`; see that flag below), poll the `status` command the launcher printed until the run is finished, and read the run's markers and output paths from the log it named.

The orchestrator will:
1. Load validation results and grouped suggestions
2. Filter to only `valid` suggestions
3. Group suggestions into efficient batches
4. Write output to `{plan}/apply-suggestions/orchestrator_output.json`
5. Exit — the driving agent handles the actual application

An exit 3 naming another review round is a stop, with nothing applied or recorded: the review's `validation.json` holds an earlier round's verdicts, and a later run of the review (`review-plan --force`, say) has not produced its own — it is still running, or it stopped before it validated. Report the two ways forward it names: let that run finish (`status`), or run the review again with `--force`; then run this phase again. Never apply the earlier round's suggestions by hand.

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
   > "No user selections were found (no user_selections.json, consolidated_user_selections.json, or report.md edits detected). This will apply ALL {item_count} valid items. Continue?"
   > Options: "Yes, apply all" / "No, I need to make my selections first"
3. If user confirms: Re-run the orchestrator with `--no-confirm` appended
4. If user declines: Stop and inform the user to review the HTML report and export selections

If NOT present, proceed to step 3.

### 3. Display Decision Summary

After the orchestrator completes, run the display script to show the user which suggestions will be applied, skipped, need review, etc.:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util decisions --plan-file "$PLAN_PATH" --phase apply-suggestions
```

This prints a formatted summary with each suggestion's title and status. Display this output to the user before proceeding.

### 4. Read the Orchestrator Output

Read `{plan}/apply-suggestions/orchestrator_summary.json`, written beside `orchestrator_output.json`: what the batch loop needs from that file and from `write_tasks.json`. When there is no summary, read `orchestrator_output.json` and `write_tasks.json` (printed as `[WRITE_TASKS_FILE]`: the same batches in the same order, with their task ids) instead.

Extract the following key fields directly from the Read output (do NOT use Bash/python to parse — just read the JSON and understand it):
- `batches`: one entry per batch, in dispatch order, with `task_id` (`apply-batch-0`, `apply-batch-1`, …), `batch_index`, `section_key`, `prior_changes_id`, `task_title` and `expected_ids`, the values `write_tasks.json` holds, and `detail_path`, the batch's detail file
- `needs_human_review`: Items requiring human decision
- `human_review_config`: Batch mode config for human review
- `summary`: Counts of valid, skipped, batches, etc.

The batch loop below is keyed on `task_id`. Each batch's `suggestions` are in its detail file at `detail_path` (`orchestrator_batches/<task_id>.json`: the batch's record in `orchestrator_output.json` without its prompt), read once at step 1 below and used again at step 5. The **unbound** `prompt` stays in `orchestrator_output.json` and is never handed to a subagent.

### 5. Process Batches Sequentially

Use the batch data already loaded in step 4. Do NOT use Bash/python to re-parse or extract fields from the JSON file.

**Before the loop**, mark the phase start so ETA tracking has a wall-clock baseline. Run:
```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics start \
  --state-file "$STATE_FILE" --phase "apply-suggestions" --total-batches {total_batches}
```
Where `{total_batches}` is the length of the `batches` array.

### The Python write executor: `--exec-subagents` (an alternative to this loop)

When the command that runs this phase carries `--exec-subagents`, `--detach` (which implies it) or `--dry-run-subagents`, however it got there (typed, printed by a resume or `util next-command`, forwarded by a workflow step, or as an abbreviation such as `--exec` or `--det`), the Python write executor runs the phase: read `references/apply-write-executor.md` in full before that command runs, or before your next command if it already ran. That one invocation is the whole phase; a dry run dispatched nothing and leaves no work either: do not run the loop below, step 3's `util decisions`, step 7's summary report or step 8's `--mark-completed`. A command with none of `--exec-subagents`, `--detach` and `--dry-run-subagents`, in any spelling, skips the reference and runs the loop below.

For each batch (index N, starting at 1) returned by the orchestrator, you MUST:

1. **Bind the batch prompt** — First read this batch's detail file at its `detail_path` (with no summary, its entry in `orchestrator_output.json`'s `batches`, already read): its `suggestions` are what the batch applies and what step 5 checks. Then run:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util write-prompt \
     --phase-dir "{plan}/apply-suggestions" --task-id "{task.task_id}"
   ```
   `{task.task_id}` is this batch's `task_id` from `write_tasks.json` (`apply-batch-0`, `apply-batch-1`, … in dispatch order). The command rewrites the batch's prompt with the prior-batch context bound **now** — from `{plan}/prior_changes.jsonl` as it is at this moment, i.e. the batches step 8 has already appended — and the result contract appended: exactly the text the `--exec-subagents` executor would dispatch for this batch. It writes it to `{plan}/apply-suggestions/prompts/{task.task_id}.prompt.txt` and prints three lines: `[WRITE_PROMPT] <path>`, `[WRITE_PROMPT_LINES] <n>` and `[WRITE_PROMPT_CONTEXT] …`, then the two snapshot lines step 2 describes. Note the path and the line count for step 3. Never substitute `{prior_changes_context}` yourself and never hand the subagent `batch.prompt` from the JSON: the literal token must never reach a subagent.

   **Error handling**: an exit 3 names the problem (no `write_tasks.json` — re-run the orchestrator; an unknown task id — the known ids are listed; no snapshot — a repository holding the plan's folder that git cannot pin (a `GIT_DIR` set, a `core.worktree` that disagrees), a plan it cannot read, a snapshot lock the file system cannot take at all (`Cannot lock …`), or a snapshot whose files are damaged or no longer the copy it took: the message names the files and the user's manual way out). Do not fall back to the raw `batch.prompt`; stop and report. Only two exits 3 are worth running this command again for; every other one is a stop. A batch whose review round was superseded (the message names the two rounds: a later run of the review started another) is a stop: dispatch nothing, record nothing for it, close the phase without `--mark-completed` and report the way forward it names. An earlier batch of this run has no step-7 record yet (the snapshot still belongs to it): run the batch the message names first — bind it with this command, then its steps, or the partial-application stop below — then run this command again. Another `util write-prompt` holds the snapshot's lock (it is binding a batch now): let it finish, then run this command again. One more needs no user: an earlier batch whose record carries no run stamp (an older plugin version made it). If this loop has not run that batch, run it first, as above; if it has (the loop began before the upgrade) or you cannot tell, re-run the phase's orchestrator with `--resume`, as the message says (it skips what is recorded and emits the rest as a new run), and continue the loop from that run's first batch.

   A `[WRITE_PROMPT_ORDER]` line (on stderr; the prompt is still written) names an earlier batch whose summary this prompt does not carry — recorded but not appended yet, or not finished: do what it says, then run this `util write-prompt` again before spawning the subagent.

2. **Note the pre-batch snapshot** — step 1's command has already copied the plan, byte for byte, to the workspace temp dir (`.multi-llm/tmp/batch_snapshot_plan_<plan stem>-…` under the root of the repository holding the plan's folder, or in the phase folder's own `snapshots/` when no repository holds it; a name of its own per plan and phase; the dir ignores itself) and printed `[WRITE_SNAPSHOT] <snapshot path>` and `[WRITE_ARTIFACT] <plan path>`, both absolute. Keep both paths for step 5; take no copy of your own. Step 5 diffs against this snapshot instead of asking git: plan files are frequently untracked (freshly created), and every `git diff` variant silently ignores fully-untracked files. The snapshot belongs to this batch: running `util write-prompt` for it again keeps it, and no later batch's call replaces it before this batch has its step-7 record. It is a convenience copy where the subagent can write too: its checksum catches an accidental change, not a deliberate one.

3. **Spawn a subagent** whose whole prompt is: read the file at the `[WRITE_PROMPT]` path in full — through line `[WRITE_PROMPT_LINES]`, paging if a single read stops short — and follow it verbatim.
   - Use `general-purpose` subagent type
   - That is the entire contract: do not paste the prompt text, add instructions of your own, or hand the subagent the JSON. The file already contains all suggestions, the prior-batch context and the reply format (it ends with a JSON object the steps below read)
4. **Wait for completion** - Do NOT parallelize batch processing

5. **Verify batch outcome** — After the subagent completes (or fails), determine the batch outcome by inspecting actual file state rather than relying solely on the subagent's exit status.

   **Do NOT use `git diff` / `git diff --stat` to detect whether the plan changed.** Plan files are frequently untracked (freshly created), and every `git diff` variant silently ignores fully-untracked files — it will report "no changes" even when the subagent edited the plan, producing a false clean-failure. Detect changes by diffing against the step-2 snapshot instead:
   ```bash
   diff -u "{snapshot_path}" "{plan_path}"   # empty output = byte-identical (unchanged); non-empty = file changed
   ```
   `{snapshot_path}` and `{plan_path}` are the `[WRITE_SNAPSHOT]` and `[WRITE_ARTIFACT]` paths from step 1, written out literally (a shell variable from an earlier Bash call does not exist in this one). If you no longer have them, run step 1's command again for this same batch: it keeps this batch's snapshot and prints the same two lines.
   Classify the result:
   - **Success**: The snapshot diff is non-empty AND the expected changes are present (spot-check by `grep`-ing the plan for distinctive text from this batch's suggestions, which its detail file lists: you read it at step 1; read it again only if it is no longer in your context).
   - **Failure (clean)**: The subagent reported failure AND the snapshot diff is empty (plan byte-identical to the pre-batch snapshot).
   - **Not applied**: The subagent reported `applied` **and** the snapshot diff is empty: its edits did not land. Dispatch the batch once more, with one sentence added to its prompt saying the previous attempt answered `applied` but changed no file, and verify again; if nothing changed this time either, it is a clean failure (record it `failed`), never a success.
   - **Partial application**: The snapshot diff shows some but not all expected changes, or the subagent failed but the snapshot diff is non-empty.
   - **Declined items**: an item the reply lists in `declined` with a reason was left unapplied on purpose (for example, the implementation record calls that code deliberate). It is never applied and never a partial application: a batch whose every item is in `ids` or in `declined` is a success (a no-op when it changed nothing), whatever word its `status` carries, `failed` included: record it `--status completed`. An item in neither list, an id in both, or a `declined` entry without a reason is a partial application.

   The snapshot diff is the authoritative, fully git-independent check — no git intent-to-add step is needed here (flows that genuinely need untracked files visible to git diffs, like code review, handle that inside their Python orchestrator via `utils/git_utils.intent_to_add_untracked`).

   There is **no snapshot cleanup step**: the snapshot lives in the self-gitignored workspace temp dir, and the next batch's `util write-prompt` replaces it once this batch is recorded. On **partial application** the loop stops (below), so the snapshot file still holds the pre-batch content for the human reviewer to inspect.

   **Partial application handling**: If verification detects a partial application, **stop the batch loop and surface the issue for human review**. Do not continue to subsequent batches. Log the partial application details and prompt the human operator to resolve the state before resuming. When the reply's report attests at least one suggestion applied (in `ids`, with a `status` other than `failed`) and leaves others out of both `ids` and `declined`, give the user both ways forward and let them choose: put the plan back and fix the cause, then resume — the step-2 snapshot holds the plan as it was before this batch, so read the step-5 diff and copy it back by hand (`cp "{snapshot_path}" "{plan_path}"`, which also undoes every edit made to the plan since the snapshot, the user's included). It is a convenience copy, not tamper-proof evidence: the batch's subagent could write it too, so read the diff before trusting it. This loop has no other per-batch rollback point — `util restore-batch` has nothing of a native batch's, and `{plan}/apply-suggestions/backup.md` holds the plan from before the whole phase; **or** keep what the batch applied and go on without the suggestions it left out — record it with step 7's `util batch-done` as `--status completed` plus one `--skipped <id>` per suggestion left out, append its summary (step 8) and continue with the next batch. A resume that does neither hands the same batch out again and stops the same way.

6. **Extract summary** — The subagent's reply ends with one JSON object (`{"status", "ids", "declined", "files_touched", "summary", "notes"}`: the result contract the prompt file carries). Take its `summary` as the one-line summary; its `status` (`applied` / `no-op` / `failed`) and `files_touched` are evidence for step 5, never a substitute for the snapshot diff. If the reply carries no such object, compress the reply into a single sentence instead.

   **Normalize** the summary: collapse any newlines or multiple spaces to a single space, trim leading/trailing whitespace, and truncate to 200 characters if needed.

7. **Record the batch outcome (only after verification)** — This step runs **only** after step 5 has classified the batch as a success or a clean failure. It must **never** run for a partially-applied batch (the loop stops there). Run:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util batch-done \
     --phase-dir "{plan}/apply-suggestions" --task-id "{task.task_id}" --status {batch_status}
   ```
   `{batch_status}` is `completed` for a success (a verified no-op included) and `failed` for a clean failure — add `--reason "{compact reason}"` to a `failed` one. It prints one `[BATCH_DONE] {task.task_id} {batch_status} (N item(s) recorded)` line and writes the batch's record into `state.json`: the same `task_status` entry the `--exec-subagents` executor writes for this batch, plus every suggestion in it as processed. That record is what a later `--resume` reads to skip this batch (a `failed` record keeps it eligible for another try) and what makes `status` read the phase `in_progress`. Run it **before** step 8's append: a run that dies between the two leaves a record `--resume` honours, never a log entry `--resume` would re-apply. An exit 3 names the problem (no `write_tasks.json`, an unknown task id); treat it as a stop, not a warning.
   When the reply's `declined` lists suggestions (each `{"id", "reason"}`), add `--declined "{id}={reason}"` for each, with `--status completed`: each prints a `[BATCH_DECLINED]` line — list that suggestion in the summary under `## Declined by their batch (not applied)`, with its id and reason (never under `## Applied Changes`, not even marked "Not applied"), and name it in your report; it is never counted as applied. `--skipped {id}` records a suggestion the user chose to skip (above) the same way, as `[BATCH_SKIPPED]`, listed under `## Skipped at your request (not applied)`.

8. **Append to prior changes (only after verification)** — This step runs **only** after step 5 has confirmed success or clean failure. It must **never** run for partially-applied batches. Pass the summary via stdin:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util prior-changes append \
     --output-dir "{plan}" \
     --id "{batch.prior_changes_id}" --phase "apply-suggestions" --summary-stdin <<'SUMMARY_EOF'
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
   Do **not** use the batch loop index. The `--phase` is `"apply-suggestions"`.

   For **clean failures**, use summary: `(batch failed — {compact reason}, verified no file changes)`
   When a `--resume` dispatches that batch again, append its new summary under the same `--id`: it replaces the failure line in every later batch's prompt (`Replaced entry …` on stderr).

   **Error handling**: If `append` fails, log a warning but do not abort the batch loop.

9. **Log the result** - Track success/failure for the summary
10. **Record metrics** — Run:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics record \
     --state-file "$STATE_FILE" --phase "apply-suggestions" \
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
  --state-file "$STATE_FILE" --phase "apply-suggestions"
```

### 6. Handle Human Decision Items

Follow the human decision batch mode process in `references/human-decision-batch.md`.

**Auto-route report-pre-marked items first**: before prompting for anything, partition `needs_human_review` into (a) the **pre-marked judge set** — every suggestion whose `group_id` is in `human_review_config.judge_decide_item_ids` or that carries `decision_mode == "judge_auto_decide"` — and (b) the remaining **interactive set**. Run **"Let the Agent Decide" Mode** (per the criteria in `references/human-decision-batch.md`) on the pre-marked judge set **without any prompt**, then handle only the interactive set with the flow below. These suggestions were chosen in the report's "Let the agent decide" dropdown/checkbox; they are the per-item equivalent of `--agent-decide` scoped to just those suggestions.

**Check `human_review_config.decision_mode` first**: if it is `"judge_auto_decide"` (the user passed `--agent-decide`), do NOT prompt the user — go straight to "Let the Agent Decide" Mode and evaluate every `needs-human-decision` item autonomously per the criteria in that reference. By default, **partially-valid items are salvaged** (rewritten to their worthwhile core and applied) rather than skipped; only items with nothing worthwhile are skipped entirely.

Context line for individual review display: `Type: {type}, Section: {reference}`

### 7. Generate Summary Report

After all batches are processed, create `{plan}/apply-suggestions/summary.md` — the
same path the *Output Files* tree above lists, and the same one the
`--exec-subagents` leg writes for itself:

```markdown
# Applied Suggestions Report

**Plan**: /path/to/plan.md
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

### Batch 1 (Section: step_3)
**Suggestions**: 3
**Type**: addition

1. **[Suggestion Title]** - Applied
   Description: [Brief description of what was changed]

2. **[Suggestion Title]** - Applied
   ...

### Batch 2 (Section: step_4)
...

## Declined by their batch (not applied)

(Only when a batch declined a suggestion — a `[BATCH_DECLINED]` line from `util batch-done`. Never list it under `## Applied Changes`, not even marked "Not applied": its batch's block above says `**Not applied**: 1 declined by the batch (listed under "Declined by their batch (not applied)" below)` instead.)

- **[Suggestion Title]** (`{id}`, apply-batch-0) — {the reason the batch gave}

## Skipped at your request (not applied)

(Only for a suggestion recorded `--skipped` — a `[BATCH_SKIPPED]` line; never under `## Applied Changes` either.)

- **[Suggestion Title]** (`{id}`, apply-batch-0) — skipped at your request

## Decided by the judge agent (N)

judge: {judge}

Items whose decision was offloaded to the judge agent — via `--agent-decide`, the batch "Let the agent decide" option, or a per-item "Let the agent decide" selection. Read these from `state.json`: the `human_decisions_{phase}` entries whose `batch_context.decision_source` is `judge_auto_decide` or `judge_auto_decide_salvage` (a run recorded before the judge rename may carry them as `claude_auto_decide` / `claude_auto_decide_salvage`: the same two markers, read the same way). Omit this section if there are none. `{judge}` is the runner spec that actually judged (e.g. `codex:<chat model>`, the session model, under `--exec-subagents` on Codex — or an explicit `driver.subagent_runner` override, or the `codex:gpt-6-astra` host floor when that is what resolved), or, on a host with native subagents, the label recorded in the decision's `judge` field — the model the judging subagent reported, e.g. `claude-sonnet-5-5 (claude-code host agent)`. Print it as recorded; never write "claude" for a judge that was not Claude. A salvaged item is "Salvaged" everywhere, never "Approved", even though state.json stores it with `decision: approved` plus the `judge_auto_decide_salvage` marker.

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
     --state-file "$STATE_FILE" --phase "apply-suggestions"
   ```
   Include the output (if non-empty) at the end of the summary report.

   **Then update the HTML review report** so the decisions show up there too. This overlays every human/judge-agent decision recorded in `state.json` onto the existing `{plan}/review-plan/report.html`, giving each finding an **Approved / Salvaged / Skipped** badge plus an expandable detail with the kept/dropped notes:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util report \
     regenerate-decisions \
     --phase-dir "$(dirname "$STATE_FILE")/review-plan" \
     --state-file "$STATE_FILE" \
     --apply-phase "apply-suggestions"
   ```
   Best-effort: if `report_data.json` is missing from the review dir (the review predates this feature), the command prints a notice and exits 0 without changing the report — just continue. The same holds when the phase recorded no human or judge decision: the report stays as the review wrote it, and the command says so (never edit the report yourself).

### 8. Mark Phase Completed

**Run this only if step 5's batch loop reached the end** — every batch dispatched and verified, and the human-decision items of step 6 handled. Then mark the apply-suggestions phase as completed in state.json:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions --plan-file "$PLAN_PATH" --mark-completed
```

The orchestrator recorded the phase *started* when it wrote the batches (step 2), and this is the only command that records it *completed* — it also re-stamps the plan hash, so the next phase does not read this phase's own edits as a human editing the plan. **Do NOT run it if the loop stopped early** — a clean failure you aborted on, a partial application you surfaced for human review (step 5.5), or an interrupted run. The phase then stays `in_progress`, which is what makes `status` and the next-step command offer `--resume` instead of calling the phase done.

**Then report to the user** following `references/summary-format.md`, naming the summary report and every other file this phase wrote.

---

## JSON Output Structure

The orchestrator outputs JSON with batches:

```json
{
  "plan_file": "/path/to/plan.md",
  "prefix": "my-feature",
  "output_dir": "/path/to/my-feature/",
  "timestamp": "2024-01-21T12:00:00",
  "batches": [
    {
      "suggestions": [
        {
          "index": 0,
          "title": "Add error handling",
          "description": "...",
          "type": "addition",
          "reference": "### Step 3",
          "importance": "HIGH"
        },
        {
          "index": 1,
          "title": "Add validation",
          "description": "...",
          "type": "addition",
          "reference": "### Step 3",
          "importance": "MEDIUM"
        }
      ],
      "section_key": "step_3",
      "prior_changes_id": "step_3#7c02e5d1",
      "batch_type": "addition",
      "suggestion_count": 2,
      "priority_score": 5.0,
      "prompt": "Apply the following 2 related suggestions..."
    }
  ],
  "to_apply": [...],  // Flat list for reference
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
User: /multi-llm:multi-llm --apply-suggestions plans/my-feature.md

Agent:
1. Checks for prerequisite files - found
2. Runs orchestrator to get batched suggestions
3. Gets 8 valid suggestions in 3 batches, 2 needs-human-decision

   Batch 1: 3 additions in step_3 (priority: 7.0)
   Batch 2: 2 modifications in step_4 (priority: 5.0)
   Batch 3: 3 additions in step_5 (priority: 4.0)

   Efficiency: 5 subagent calls saved (62.5% gain)

For each batch (sequentially):
- Reads current plan
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
Apply the following suggestion to the plan file:

**Plan file**: {plan_path}
**Suggestion**: {title}
**Type**: {type}
**Section**: {reference}
**Importance**: {importance}

**Details**:
{description}

Instructions:
1. Read the current plan file
2. Locate the section mentioned in the reference
3. Apply the suggested change appropriately
4. Ensure the change integrates smoothly
5. Do NOT make any other changes beyond this suggestion

Return a brief summary of what was changed.
```

For multi-suggestion batches:

```
Apply the following N related suggestions to the plan file (Section: step_3):

**Plan file**: {plan_path}
**Batch type**: addition
**Suggestions in this batch**: N

---
### Suggestion 1: {title}
- **Type**: addition
- **Section**: ### Step 3
- **Importance**: HIGH

**Details**:
{description}

---
### Suggestion 2: {title}
...

---

## Instructions

1. Read the current plan file first
2. Apply ALL suggestions in this batch, processing them in order
3. For each suggestion:
   - Locate the referenced section
   - Apply the change according to its type
   - Ensure changes integrate smoothly
4. Do NOT make any changes beyond these specific suggestions
5. If suggestions affect the same area, apply them intelligently
6. Before applying each suggestion, check if the plan already reflects a similar change (from a previously applied batch). If a suggestion is already addressed, note it as "already applied" in the summary and move on

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
2. **ALWAYS READ FIRST**: Read the plan before each batch to get latest state
3. **USE THE BOUND PROMPT FILE**: hand each subagent only the `[WRITE_PROMPT]` file `util write-prompt` wrote — never the raw `prompt` field of the JSON, which carries an unbound `{prior_changes_context}` token
4. **USE SUBAGENTS**: always **spawn subagents** to do the work
5. **PRESERVE BACKUP**: The original plan backup from review-plan should not be overwritten
6. **TRACK EVERYTHING**: Log every applied/skipped suggestion for the report
7. **DELETIONS ARE ISOLATED**: Deletion suggestions are always in their own batch

---

## Disabling Batching

To process suggestions one-at-a-time (legacy mode):

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions --plan-file "$PLAN_PATH" --no-batch
```

This is useful for:
- Debugging issues with batched edits
- Very sensitive plans where each edit needs verification
- When batching produces unexpected results

---

## Recovery Workflows

### When Validation Fails, and `--revalidate`

Two cases lead here, and in either you read `references/revalidation.md` in full, with `apply-suggestions` as its `{mode}` and `review-plan` as its `{review}`, and follow it before your next command. Skip this only when no item is `validation_failed` and no run printed `[REVALIDATION_PENDING]` or `[REVALIDATION_BATCHES_PENDING]`.
- **Failed items to recover:** validation left items `validation_failed` (`summary.validation_failed_count` above 0: a parse error, a timeout or a rate limit, unlike `needs-human-decision`; see Error Types below). No marker prints for these until a retry is requested. Start at the reference's *When validation fails*, which offers the two ways forward: `--revalidate` (optionally with `--revalidate-model`) and `--approve-validation-failed`.
- **Revalidation pending:** a run with `--revalidate` or `--revalidate-model` printed `[REVALIDATION_PENDING]` (one batch) or `[REVALIDATION_BATCHES_PENDING]` (several) and exited 0 having applied nothing. Start at the reference's *Running the revalidation subagents*.

### Resuming Interrupted Sessions

If a session is interrupted, progress is saved automatically:

`--resume` re-emits only what is left: every batch the loop recorded with `util batch-done` (step 5) is dropped, a batch recorded `failed` is dispatched again, and a batch the prior-changes log names that no record says finished is **refused** — exit 3 with a `[RESUME_REFUSED]` block naming the batch and the `util batch-done` call that records it (or `--fresh`, once the target is back at its pre-run bytes). Re-emitting such a batch would apply it twice.

```bash
# Resume from where you left off
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions \
  --plan-file "$PLAN_PATH" \
  --resume

# Or start fresh, clearing all previous progress
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions \
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

# Combine: approve validation failures, skip the rest
--approve-validation-failed --skip-all-human
```

---

## Error Types and Recovery

The orchestrator now distinguishes between different error types:

| Error Type | Status | Recoverable | Recovery Action |
|------------|--------|-------------|-----------------|
| Parsing error | `validation_failed` | Yes | Use `--revalidate` or `--approve-validation-failed` |
| Timeout | `validation_failed` | Yes | Use `--revalidate --revalidate-model faster-model` |
| Rate limited | `validation_failed` | Yes | Wait and use `--revalidate` |
| Model failure | `needs-human-decision` | No | Review manually |
| Genuine ambiguity | `needs-human-decision` | No | Review manually |

The `validation_failed` status is different from `needs-human-decision`:
- `validation_failed`: Technical error during validation, can be retried
- `needs-human-decision`: LLM determined item genuinely requires human judgment
