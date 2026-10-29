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

**Note**: By default, revalidation is delegated to a subagent. Use `--internal-revalidation` to run revalidation inside the orchestrator (legacy mode).

### Resume/State Options

- `--resume`: Resume from last checkpoint, skip already-processed items
- `--fresh`: Discard this phase's recorded progress (decisions, processed items, prior-changes log) and dispatch every batch again. The target file must already be back at its pre-run bytes (copy it from the phase's backup, or roll the batches back with `util restore-batch`): a target still carrying the previous run's edits is refused (exit 3), since every batch would land twice. Earlier rollback points are kept aside, never overwritten.
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

**IMPORTANT**: Run this command in the foreground — do **not** run it detached. The orchestrator runs quickly — it only generates batch JSON, it does not apply changes — so 10 minutes is far more than enough.

The orchestrator will:
1. Load validation results and grouped suggestions
2. Filter to only `valid` suggestions
3. Group suggestions into efficient batches
4. Write output to `{plan}/apply-suggestions/orchestrator_output.json`
5. Exit — the driving agent handles the actual application

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

On the `--exec-subagents` leg (below) this step never runs — the phase finishes in
one invocation — so the run prints the same breakdown itself at the end: batches
ok/failed with duration and runner, the count applied, and every skipped
suggestion with its status, group id and reason.

### 4. Read the Orchestrator Output

Read `{plan}/apply-suggestions/orchestrator_output.json`.

Extract the following key fields directly from the Read output (do NOT use Bash/python to parse — just read the JSON and understand it):
- `batches`: Array of batch objects, each with `prompt`, `section_key`, `prior_changes_id`, `suggestions`
- `needs_human_review`: Items requiring human decision
- `human_review_config`: Batch mode config for human review
- `summary`: Counts of valid, skipped, batches, etc.

Also read `{plan}/apply-suggestions/write_tasks.json` (the orchestrator printed its path as `[WRITE_TASKS_FILE]`): its `batches` array is the same batch list in the same order, one entry per batch with `task_id` (`apply-batch-0`, `apply-batch-1`, …), `batch_index`, `task_title`, `expected_ids` and the same `prior_changes_id`. The batch loop below is keyed on `task_id`; `batch.prompt` in `orchestrator_output.json` is the **unbound** template and is never handed to a subagent.

### 5. Process Batches Sequentially

Use the batch data already loaded in step 4. Do NOT use Bash/python to re-parse or extract fields from the JSON file.

**Before the loop**, mark the phase start so ETA tracking has a wall-clock baseline. Run:
```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics start \
  --state-file "$STATE_FILE" --phase "apply-suggestions" --total-batches {total_batches}
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
     --phase-dir "{plan}/apply-suggestions" --task-id "{task.task_id}"
   ```
   `{task.task_id}` is this batch's `task_id` from `write_tasks.json` (`apply-batch-0`, `apply-batch-1`, … in dispatch order). The command rewrites the batch's prompt with the prior-batch context bound **now** — from `{plan}/prior_changes.jsonl` as it is at this moment, i.e. the batches step 8 has already appended — and the result contract appended: exactly the text the `--exec-subagents` executor would dispatch for this batch. It writes it to `{plan}/apply-suggestions/prompts/{task.task_id}.prompt.txt` and prints three lines: `[WRITE_PROMPT] <path>`, `[WRITE_PROMPT_LINES] <n>` and `[WRITE_PROMPT_CONTEXT] …`. Note the path and the line count for step 3. Never substitute `{prior_changes_context}` yourself and never hand the subagent `batch.prompt` from the JSON: the literal token must never reach a subagent.

   **Error handling**: an exit 3 names the problem (no `write_tasks.json` — re-run the orchestrator; an unknown task id — the known ids are listed). Do not fall back to the raw `batch.prompt`; stop and report.

   A `[WRITE_PROMPT_ORDER]` line (on stderr; the prompt is still written) names an earlier batch whose summary this prompt does not carry — recorded but not appended yet, or not finished: do what it says, then run this `util write-prompt` again before spawning the subagent.

2. **Read current plan state and snapshot it** — Always read the latest plan file version before each batch, then capture a pre-batch snapshot so the batch's effect can be verified in step 5 **without** relying on git. (Plan files are frequently untracked — freshly created — and every `git diff` variant silently ignores fully-untracked files, so git CANNOT detect whether a batch changed the plan. Snapshot the file and diff against the snapshot instead.)

   The snapshot lives in the **workspace temp dir** at a deterministic path (each batch overwrites it; no cleanup step; the dir is self-gitignored). Resolve the project root first — if the command fails or prints nothing, STOP with the error: "multi-llm requires running inside a git repository":
   ```bash
   git rev-parse --show-toplevel
   ```
   The snapshot path is `{project_root}/.multi-llm/tmp/batch_snapshot_plan_{plan_stem}.md`, where `{project_root}` is the output of the command above and `{plan_stem}` is the plan filename without extension.

   Also resolve the **plan file's absolute path** now — call it `{plan_abs}`. The plan argument is commonly relative (e.g. `plans/my-feature.md`), but a host's file-reading and file-writing tools require OS-native absolute paths, so a relative path cannot be handed to them directly. If the plan path is already absolute, use it as-is; otherwise join `{project_root}` with the relative plan path (e.g. `{project_root}/plans/my-feature.md`).

   **Shell variables do NOT survive between Bash calls** — each Bash invocation is a fresh process, so do not stash these values in variables like `PROJECT_ROOT` or `BATCH_SNAPSHOT` for later steps. Note the concrete absolute snapshot path and `{plan_abs}` now and substitute them literally wherever later steps reference them.

   Capture the snapshot with your host's file tools, not Bash: read `{plan_abs}`, then write its exact content to the snapshot path (use the absolute path — join the resolved project root with `.multi-llm/tmp/batch_snapshot_plan_{plan_stem}.md`; a host file-write that creates parent directories needs no mkdir step and no Bash copy command). If `{project_root}/.multi-llm/tmp/.gitignore` does not exist yet, also write it with content `*` so the temp dir ignores itself.

   Keep the concrete absolute snapshot path and `{plan_abs}` for step 5.

3. **Spawn a subagent** whose whole prompt is: read the file at the `[WRITE_PROMPT]` path in full — through line `[WRITE_PROMPT_LINES]`, paging if a single read stops short — and follow it verbatim.
   - Use `general-purpose` subagent type
   - That is the entire contract: do not paste the prompt text, add instructions of your own, or hand the subagent the JSON. The file already contains all suggestions, the prior-batch context and the reply format (it ends with a JSON object the steps below read)
4. **Wait for completion** - Do NOT parallelize batch processing

5. **Verify batch outcome** — After the subagent completes (or fails), determine the batch outcome by inspecting actual file state rather than relying solely on the subagent's exit status.

   **Do NOT use `git diff` / `git diff --stat` to detect whether the plan changed.** Plan files are frequently untracked (freshly created), and every `git diff` variant silently ignores fully-untracked files — it will report "no changes" even when the subagent edited the plan, producing a false clean-failure. Detect changes by diffing against the step-2 snapshot instead:
   ```bash
   diff -u "{snapshot_path}" "{plan_path}"   # empty output = byte-identical (unchanged); non-empty = file changed
   ```
   Substitute `{snapshot_path}` and `{plan_path}` with the **concrete absolute paths** noted in step 2 (the snapshot path and `{plan_abs}` — the same resolved absolute plan path used for the step-2 Read, not the possibly-relative plan argument). Do NOT write `$BATCH_SNAPSHOT` or `$PLAN_PATH` here — shell variables assigned in earlier Bash calls do not exist in this fresh Bash process, and an unset variable would make `diff` compare the wrong files or fail. If the snapshot path was not carried forward, recompute and diff in one single invocation, embedding the root as an inline command substitution (not as a `PROJECT_ROOT=...` assignment prefix, which the permission allowlist does not cover):
   ```bash
   diff -u "$(git rev-parse --show-toplevel)/.multi-llm/tmp/batch_snapshot_plan_{plan_stem}.md" "{plan_path}"
   ```
   Classify the result:
   - **Success**: The snapshot diff is non-empty AND the expected changes are present (spot-check by `grep`-ing the plan for distinctive text from this batch's suggestions).
   - **Failure (clean)**: The subagent reported failure AND the snapshot diff is empty (plan byte-identical to the pre-batch snapshot).
   - **Not applied**: The subagent reported `applied` **and** the snapshot diff is empty: its edits did not land. Dispatch the batch once more, with one sentence added to its prompt saying the previous attempt answered `applied` but changed no file, and verify again; if nothing changed this time either, it is a clean failure (record it `failed`), never a success.
   - **Partial application**: The snapshot diff shows some but not all expected changes, or the subagent failed but the snapshot diff is non-empty.
   - **Declined items** (fix round 18): an item the reply lists in `declined` with a reason was left unapplied on purpose (for example, the implementation record calls that code deliberate). It is never applied and never a partial application: a batch whose every item is in `ids` or in `declined` is a success (a no-op when it changed nothing), whatever word its `status` carries, `failed` included: record it `--status completed`. An item in neither list, an id in both, or a `declined` entry without a reason is a partial application.

   The snapshot diff is the authoritative, fully git-independent check — no git intent-to-add step is needed here (flows that genuinely need untracked files visible to git diffs, like code review, handle that inside their Python orchestrator via `utils/git_utils.intent_to_add_untracked`).

   There is **no snapshot cleanup step**: the snapshot lives in the self-gitignored workspace temp dir and is simply overwritten by the next batch. On **partial application** the loop stops (below), so the snapshot file still holds the pre-batch content for the human reviewer to inspect.

   **Partial application handling**: If verification detects a partial application, **stop the batch loop and surface the issue for human review**. Do not continue to subsequent batches. Log the partial application details and prompt the human operator to resolve the state before resuming. When the reply's report attests at least one suggestion applied (in `ids`, with a `status` other than `failed`) and leaves others out of both `ids` and `declined`, give the user both ways forward and let them choose: restore the batch (`util restore-batch`) or fix the cause, then resume; **or** keep what the batch applied and go on without the suggestions it left out — record it with step 7's `util batch-done` as `--status completed` plus one `--skipped <id>` per suggestion left out, append its summary (step 8) and continue with the next batch. A resume that does neither hands the same batch out again and stops the same way.

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

### When Validation Fails

If validation produces many `validation_failed` items due to parsing errors or timeouts:

```bash
# Option 1: Re-run validation with a different model
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions \
  --plan-file "$PLAN_PATH" \
  --revalidate \
  --revalidate-model cursor-agent:opus

# Option 2: Bulk approve validation failures (if you trust the suggestions)
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions \
  --plan-file "$PLAN_PATH" \
  --approve-validation-failed
```

### Handling Revalidation Subagent

When running with `--revalidate` (without `--internal-revalidation`), the orchestrator outputs a revalidation marker.

#### The task file

`revalidation_tasks.json` carries `tasks_schema_version: 2` and one complete task
per batch under `batches` — each with `prompt`, `output_name`, the derived
`output_path`, `prompt_path` and `prompt_lines`, `result_channel: file`,
`context_mode`, `capability_tier`, `executor_role` and `task_id`. The
sidecar at `prompt_path` holds exactly the bytes of `prompt` (`prompt_lines` is
its line count), so the two are interchangeable and a host that would otherwise
re-emit the whole prompt can point the subagent at the file instead. The plan
excerpt and this batch's suggestion records travel **inside** `prompt`;
`item_indices` and `original_validation` stay on the file for the merge step.
A plan within the inline limit is complete there (`context_mode: inline`). A
larger plan keeps a head excerpt and is also named once under `## Plan file`:
a hash-bound snapshot, `revalidation-snapshot.md` in the phase dir, and the
task is `context_mode: workspace-read`. The subagent must be able to read that
path, so do not run it where it cannot. Never treat such a batch as having the
full plan inline.

**For each task in the file: when the task carries `prompt_path`, run a subagent
that reads that file in full — through line `prompt_lines`, paging if a single
read stops short — and follows it verbatim; otherwise, or if the file is absent,
run `task.prompt` as a subagent. Either way, write the JSON it returns to
`task.output_path`.** That is the whole contract — do not assemble a prompt
beyond that one read instruction, and do not tell the subagent to write the file
itself. The file's bytes are exactly `task.prompt`; the two are interchangeable.

A file whose `tasks_schema_version` is missing or not `2`, or whose recorded
`inputs` hashes no longer match their sources, is refused with exit 3: re-run the
phase with `--force` to re-materialize it.

**Check each reply right after you write it.** Run
`uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util check-reply --tasks-file "{plan}/review-plan/revalidation_tasks.json" --task-id <task_id>`
(omit `--task-id` to check every batch, and only once every batch's subagent has
returned: a reply not written yet prints `[REPLY_MISSING]`, which is no bad reply and
no re-ask). `[REPLY_INVALID]` means the subagent's reply
did not parse or did not cover its groups — Sonnet subagents lost a closing `]` on 3 of
14 batches in the 2026-10-01 Claude Code run. Re-ask the same subagent once for the
whole reply and write the new reply over the file. Never edit, trim or complete a reply
yourself, and never assemble one from the parts of two replies. A batch still
`[REPLY_INVALID]` after that one re-ask is a failed batch: leave its file as it is and say so.

#### Single Batch: `[REVALIDATION_PENDING]`

If `[REVALIDATION_PENDING]` marker is present:
1. Read `revalidation_tasks.json` from `{plan}/review-plan/`
2. Run the single task as the contract above says — the sidecar at `prompt_path`
   when it has one, `task.prompt` otherwise — and write its JSON reply to that
   task's `output_path`
3. After the result file is written, run the orchestrator again (without `--revalidate`)

#### Multiple Batches: `[REVALIDATION_BATCHES_PENDING]`

If `[REVALIDATION_BATCHES_PENDING]` marker is present:
1. Read `revalidation_tasks.json` from `{plan}/review-plan/`
2. Count the number of batches and choose a strategy:

**Strategy A: Direct parallel spawning (≤ 4 batches)**

For each task in the `batches` array, run the task exactly as the contract above says — the sidecar at `prompt_path` when it has one, `task.prompt` otherwise — and write the JSON it returns to that task's `output_path`.

**Run all batches in parallel** (single message with multiple subagent calls).

**Strategy B: Wave-based parallel spawning (> 4 batches)**

Follow the wave-based spawning strategy in `references/wave-batching.md`.

**Before you continue: verify every batch wrote its file, and do not end your turn before it has.** Confirm that each task's `output_path` exists and is not empty. Re-dispatch any task whose file is missing — exactly as the contract above says — and write its reply yourself; only a batch that comes back empty-handed a second time is a failed batch, and a batch nobody re-dispatched is not one. Spawn batches so their replies return inside this turn, and stay in the turn until the last file is on disk: **you** write these files, not the subagents, and a host that runs one headless turn has no second turn in which to write them — a reply that lands after the turn ends is a batch lost with nothing on disk to say so. Naming the batch you are waiting on is not waiting for it.

3. After ALL batches complete, run the orchestrator again (without `--revalidate`) to merge and continue

**Legacy Mode**: Add `--internal-revalidation` to run revalidation inside the orchestrator instead of delegating to a subagent.

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
