# Review Code Mode Instructions

Reviews code changes made during implementation against the original plan.

## Usage

```bash
/multi-llm:multi-llm --review-code <plan_path> [--models model1 model2] [--base-ref REF] [--quick]
```

## Options

- `--models`: Models to use for review (default: claude-sonnet)
- `--base-ref`: Git ref to compare against (default: from state file)
- `--files <path>` (repeatable) / `--files-from <file>` (one path per line, `-` for stdin): review exactly these repo-relative paths, ahead of the implement phase's `tracked_files` and the `git diff` fallback. The list is saved in the state file so a later `--reaggregate` reviews the same scope, and a later run without the flag clears it.
- `--skip-validation`: Skip the LLM validation step (faster but no false-positive filtering)
- `--validation-model <model>`: Model to use for validation (default: "auto")
- `--apply-fixes`: Prepare fix tasks for subagents to apply
- `--quick` / `-q`: Use quick_models from providers.yaml for lightweight reviews (2 models)

## Process

1. **Get Diff**: Compare current code against base ref, and write the scope manifest (`code-review/review-scope.md`) and one whole diff per source or test file (`code-review/diff/`) before any reviewer starts
2. **Run Reviews**: Each model reviews the diff against the plan, reading those files (a model that cannot open them gets them inline when they fit, and is reported as unable to review otherwise)
3. **Aggregate Issues**: Collect and prioritize issues by severity
4. **Validate Issues**: Filter out false positives and invalid issues
5. **Prepare Fix Tasks** (if `--apply-fixes`): Generate fix tasks JSON for subagents
6. **Apply Fixes** (if `--apply-fixes`): the agent spawns one subagent per valid issue
7. **Update Plan**: Document what was fixed in the original plan
8. **Generate Report**: Create review report with all findings

## Output Files

All output files are organized into phase-based subdirectories:

```
plans/todo/my-feature.md                      # Original plan (updated with fixes if --apply-fixes)
plans/todo/my-feature/                        # Output folder
├── state.json                                # Session state (plan-local)
└── code-review/                              # Code review phase outputs
    ├── report.md                             # Review report
    ├── review-scope.md                       # Scope manifest: every path under review, its diff file or why it has none
    ├── diff/                                 # One whole diff per source/test file (git-ignored by its own .gitignore)
    ├── .review-scope.json                    # Which scope each model's result reviewed (resume check)
    ├── issues.json                           # Raw issues
    ├── grouped.json                          # Grouped issues
    ├── validation.json                       # Validation results
    ├── fix_tasks.json                        # Fix tasks for subagents (if --apply-fixes)
    ├── {model}.json                          # Per-model results
    ├── log_{model}.txt                       # Agent output logs (for debugging)
    ├── error_{model}.log                     # Error logs (if failed)
    └── salvage_{model}.json                  # Salvage requests (if JSON parse failed)
```

## Report Format and User Skip Functionality

The generated `report.md` uses a checkbox-based format that allows users to mark issues they want to skip:

### Issue Format

```markdown
### 1. Missing null check in user validation
- [ ] Skip
**Validation:** ✓ Valid | **File:** `src/auth.ts:42-50` | **Type:** bug | **Model:** gpt-4

Description of the issue...

---
```

### Validation Status Display

Each issue shows explicit validation status:
- `**Validation:** ✓ Valid` - LLM confirmed this is a real issue
- `**Validation:** ✗ Invalid` - LLM determined this is a false positive
- `**Validation:** ? Needs Review` - Requires human judgment
- `**Validation:** ? Unknown` - Validation status not available

### Marking Issues to Skip

To skip an issue when applying fixes later:
1. Open `{plan}/code-review/report.md` in any editor
2. Change `- [ ] Skip` to `- [x] Skip` for issues you want to exclude
3. Save the file
4. Run `--apply-code-fixes` - marked issues will be filtered out

The report numbers **issues** (one block per model finding) while a fix is
applied per **group**, so a block carrying `_Same finding as #7, #11_` is one of
several views of a single finding: marking `Skip`, `Mark valid` or `Mark
invalid` on any of them marks the whole group. The header's `**Groups:**` line
says how many distinct findings the issue count collapsed into, and the
validation counts are per group.

This is useful for:
- Skipping valid issues that are intentional or out of scope
- Excluding issues you've already fixed manually
- Filtering out low-priority items you don't want to address

## Debug Logs

Each model invocation generates a log file (`log_{model}.txt`) in the `code-review/` directory containing:
- Timestamp and duration
- The prompt sent to the agent
- Full stdout/stderr output
- Success/failure status and error details

These logs are useful for debugging why an agent failed or what thinking/tools it used.

## Validation Statuses

Each suggestion/issue group receives a validation status:

- **valid** (checkmark): Issue is real and should be addressed
- **invalid** (x): False positive, can be ignored
- **needs-human-decision** (?): Requires human judgment

Items with `needs-human-decision` status are included in the report for the user to review. Human decisions are handled later in the **apply-code-fixes** phase — do NOT prompt the user for decisions during review-code.

---

## Critical Subagent Delegation Rules

**MANDATORY**: These rules MUST be followed when applying fixes:

1. **ALWAYS delegate**: When applying fixes, ALWAYS run the fix task as a subagent (`executor_role: "agent"`). NEVER implement fixes manually.

2. **OUTPUT TRACKING**: After applying fixes (with `--apply-fixes`):
   - Update `{plan}_code_review.md` to mark issues as fixed with summaries
   - Update the original plan file to reference the code review file

---

## Step-by-Step Execution

**Prerequisite — `uv` (D6 row 1).** Every command below runs through `uv run`.
If it is absent the resolution is fail-closed: print `hosts/uv-missing.txt`
verbatim and **stop with exit 3** — never install it, never ask, never fall back
to bare `python`.

1. **Validate plan file exists**

2. **Model selection:**
   - If `--models` provided in args: use those directly
   - **With `--yes` (or `--non-interactive`)**: never ask. Pass no model flag and
     let the orchestrator resolve `defaults.models` from the config layering
     (it prints `[AUTO_RESOLVED] model-selection: …`). If nothing resolves, it
     exits **3** naming the flags that answer the gate — do not substitute a
     question (D6 row 2). `--interactive` with `--yes` is exit 3 at parse time.
   - If NO models provided and NOT `--yes`: **ask the user** to select models
     - Present available models from `providers.yaml` (multi-select)
     - Then run orchestrator with `--models <selected>`
   - **Partial results** (D6 row 3): under `--yes`, a model that produced nothing
     is re-run once via `--force` with the original run's full `--models`
     selection (only the missing model actually runs; the run's report covers
     only the models passed; the retry prints `[SKIP] <model> - already has
     results` for each model it keeps, so tell the user which model re-ran and
     which kept its result) and never with `--rerun-all`; a second failure
     is reported as `[PARTIAL_RESULTS: <model>,…]` with
     `MULTI_LLM_RESULT.state: "partial"` and exit **0**. Zero results is exit
     **3** naming the retry command.

3. **Determine base-ref (handled automatically by orchestrator):**
   - If `--base-ref` provided in CLI: it will be used
   - Otherwise: the orchestrator automatically loads the state file from `{plan}/state.json` and retrieves `head_at_start`
   - If neither exists: falls back to HEAD~1

   **IMPORTANT**: Do NOT manually search for state files. The orchestrator handles state loading automatically via `get_or_create_state(plan_path)`.

   **If implementation ran outside the `implement` phase.** Nothing recorded the
   files it changed, so the review falls back to every change since the base
   ref (`[SCOPE_FALLBACK]`), which can be far wider than the implementation.
   Record the exact scope first, with the files the implementation changed:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util finalize-tracking \
     --state-file "{plan}/state.json" --only-touched --touched <path> [--touched <path> …]
   ```

   `--only-touched` makes `tracked_files` exactly those paths. Plain `--touched`
   (without `--only-touched`) does **not** narrow the scope: it only adds its
   paths to the dirty-tree census, so every unrelated modified or untracked
   path stays in. It is exact only when a `pre_existing_changes` baseline
   already covers every unrelated dirty path. The one-step alternative is to
   pass the scope to the review itself: `review-code --files <path>` (repeatable)
   or `--files-from <file>` (one path per line, `-` for stdin). Those paths win
   over `tracked_files`, and a later `--reaggregate` reviews the same scope.

4. **Resume Detection** (check BEFORE running orchestrator)

   Check for existing output to avoid expensive duplicate runs. Follow the detection cases in `references/resume-detection.md`, using `{plan}/code-review/` as the phase directory.

   **Note**: The orchestrator has TWO guards as defense-in-depth:
   - **Primary**: Exits with code 2 if phase is already marked complete in state.json. Use `--force` to override.
   - **Secondary**: Exits with code 3 if partial completion artifacts exist (validation_tasks.json, grouped.json, or per-model .json files) without the phase being complete. This prevents expensive re-runs when the previous run was interrupted.

   This instruction-level resume detection is the FIRST line of defense. The orchestrator guards are backup protection.

5. **Run the code review orchestrator (DETACHED):**

   A fan-out review over many models routinely outlives any single shell command a host is willing to wait for, so **run detached**, redirecting stdout+stderr to a log file in the phase dir and setting `PYTHONUNBUFFERED=1`:
   ```bash
   PYTHONUNBUFFERED=1 uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code \
     --plan-file "$PLAN_PATH" --models <selected> [--base-ref REF] [--apply-fixes] \
     > "{plan}/code-review/orchestrator-run.log" 2>&1
   ```

   **IMPORTANT**: Pass `$PLAN_PATH` as given — the orchestrator resolves it to an OS-native absolute path itself (do NOT wrap it in `$(realpath ...)`; on Git for Windows that emits a POSIX `/c/...` path a native process cannot use). Use `--project` (not `--directory`).

   **Run detached.** A detached run is not subject to your host's shell-command cap, so the orchestrator survives long multi-model runs. A host's own background mechanism has a time limit of its own, though: give that launch call the longest timeout the mechanism takes, as your host's *run detached* answer states, or the run is stopped mid-fan-out. `PYTHONUNBUFFERED=1` is required so Python streams output to the log instead of block-buffering it (block-buffering leaves the log empty for minutes when stdout is a non-TTY pipe) — and it is what puts each `[PROGRESS]` ticker line in the log *while* the run is still going, instead of all at once at the end. Launching is not the end of this step: poll while it runs (below), and when the loop ends read all markers and output paths **from `{plan}/code-review/orchestrator-run.log`**, not from terminal stdout.

   **Say which models, before the loop starts.** The launch says a fan-out began; it
   does not say what it is over. Make **one** non-waiting status call — no `--wait`,
   no `--timeout`, so it is a file read that answers in well under a second — and
   relay its `models:` table once:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" status "$PLAN_PATH" --phase code-review --host <host-id> --view run --exit-zero
   ```

   `--exit-zero` makes this read exit `0` whenever the status was read, so a host that shows a non-zero exit as an error shows none here; without it the call exits `2` while the run is live — `status`'s poll contract, not a failure. Read the table, not the code (only `1`, unreadable, is an error), and keep the flag off any poll whose loop reads the exit code.

   That table is the roster: one row per model, and a row's spec *is* the CLI and
   the model it runs, so nothing has to be derived — `codex:gpt-6-astra:xhigh` is
   the codex CLI running gpt-6-astra at xhigh effort. How many models the fan-out
   is over is the `progress:` line's own `models 0/N done`, printed directly above
   the table, so relay that line with it. It is a call of its own rather than the
   first poll's job because the first poll waits 120 to 300 s, and a roster that
   reaches the user three minutes after launch is not a roster. If it prints no
   `models:` table the run has not written its roster yet — the child writes it a
   few seconds in, behind a cold Python start — so make that same call once more
   before entering the loop; if there is still none, go on and the table arrives on
   a later poll. A table that *does* print can still be the **previous** run's: the
   phase dir is re-used, and the write that claims it for this fan-out — the one
   that drops the predecessor's `progress` — lands about 0.2 s in on a warm start
   and later on a cold one, so a call that beats it reads a checkpoint that is
   wholly the last run's and therefore agrees with itself. Two things print, and
   only one of them is a test. The head line's tense — a finished predecessor
   reads `finished in foreground (2/2 models, …)`, or a terminal verdict word,
   where this run reads `running` — is not that test: the claim write drops the
   predecessor's `progress`, but only a **detached** run's claim drops its `run`
   record as well, so over a dir an earlier detached run used a foreground
   fan-out keeps that record and the head line reads the predecessor's terminal
   verdict for this whole run. The test is the `progress:` step: this fan-out's
   is `fanout`, a finished predecessor's is `complete`. A roster whose step is
   not `fanout` is the previous run in this dir — make the call again rather than
   relaying it. The one predecessor that test does not catch is one **aborted**
   mid-fan-out, which can still look live; there the row elapsed is the only
   tell, an aged row reading at its budget (`30m00s/30m`) where a fresh one reads
   `0m00s/30m` — so read that as likely, never as certain, and let the next call
   settle it. Relay it **once**: what the loop below reports is movement, not the
   roster.

   **Poll while it runs, and relay one line per poll.** A fan-out that runs for ten
   to thirty minutes with nothing on screen reads as a hang, so launching the run is
   only half of this step; relaying its progress is the other half. Each poll is one
   foreground call:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" status "$PLAN_PATH" --phase code-review --host <host-id> --view run --wait --timeout <interval>
   ```

   `<host-id>` is the same host id your dispatcher command carries; `<interval>`
   is **120 to 300 seconds** (rule 5). There are two ways to reach that line.
   Where the run was launched with `--detach`, poll the `status` command the
   launcher printed rather than composing one: it carries the `--host` the
   launch itself carried — which your dispatcher command always does, and which
   is omitted when the launch recorded none — and `--run-id` on an `ask` run,
   where `--phase ask` names every question ever asked under the plan and the
   run id is the only selector left that names this one invocation; on the other
   three modes the phase selector already names exactly one dir. It carries
   `--wait` too, with no `--timeout` of its own, so its wait resolves to
   `progress.poll_s` and is clamped under the `--host` it is already carrying.
   Where *run detached* resolves to your host's own background mechanism nothing
   printed a command, so compose the line above, and keep `--host` on it — the
   wait is clamped under the shell ceiling that flag names, and without it the
   clamp falls back to the tightest ceiling on record and silently shortens
   every poll. Add `--exit-zero` to that composed line too: on such a host
   only exit `1` decides anything (rule 2), and the flag keeps every normal
   poll from showing as an error. Then give the **call itself** a timeout of at least `<interval>`
   plus 30 seconds, **in whatever unit that parameter takes** — your host's
   *run detached* answer states it, and a host whose unit is not seconds needs
   that number scaled to it rather than copied. Get it wrong and the call asks
   for a fraction of a second: it dies before `status` answers, rule 2 below
   has you re-issue it, and the loop spins instead of polling. That is a second
   number, separate from the one inside the command: a host of that shape caps
   one foreground call at about 120 s unless the call asks for longer (about
   600 s is the ceiling on the request), so without it a `--wait --timeout 300`
   is killed on every poll starting with the first and the run reads as broken
   rather than slow.

   Five rules govern the loop:

   1. **Relay the rendered line, and only that.** Per poll: the `progress:` line the
      run view already prints, the `running in foreground (…)` head line when it
      prints one, and the `just finished:` line when it prints one — all of them
      **copied through and never reworded**. A reworded count is a count you can get
      wrong, and the whole point of the status file is that the numbers *and the
      names* come from it. `just finished: codex:gpt-6-astra:xhigh (4m12s, done)` is
      the run's own answer to *which* of them finished — the CLI, the model, what
      it cost, and the reason on a slot that failed — and it is the one thing
      `models 4/5 done` cannot give; several that land in the same wait share the
      one line, joined with `; `.
      **Its absence claims nothing.** That line is a difference between two readings
      taken *inside one `--wait` call*, so a model that finishes in the gap between
      polls — your own relay turn, plus the next call's process start — is already
      terminal when that poll takes its baseline, and no poll ever names it:
      measured 2026-09-20 against the real CLI, a model finished between two polls
      and the next poll printed `progress: fanout, models 1/2 done, 1 ok, 0 failed`
      with no `just finished:` line at all. So on **every** poll, compare the
      `models:` table with the previous poll's — you are already holding that map,
      because rule 3 has you compare the two — and
      name the row or rows that are newly terminal and that no `just finished:` line
      named, **copying the spec and the state word straight out of the row**
      (`codex:gpt-6-astra:xhigh  done`) and adding nothing to either. That
      comparison is not conditional on the line being absent: one model finishing in
      the gap and a second finishing during the wait give one `just finished:` line
      naming only the second, so the first reaches the user through the comparison
      or never. That is a copy, not a recomputation: every count still comes from
      the rendered `progress:` line and is never re-derived by counting rows, which
      is the rule that has not moved. Those two are the whole of what the `models`
      table is relayed for — the roster, once, before the loop, and naming a row no
      `just finished:` line named. Never the rest: no partial results, no
      speculation about what a slow model is doing, and never the table re-listed in
      full on a later poll.
   2. **Exit code to action, never prose.** `2` — non-terminal: relay the line and
      poll again. `0` — terminal: stop polling and read the markers and output paths
      from `{plan}/code-review/orchestrator-run.log`. `3` — the run needs a human: stop and surface the
      message **verbatim**, because it names the flag or command that answers it.
      `1` — the run state is unreadable: stop and report. The loop condition is the
      exit code; the rendered text is for the user, not for the decision. **Where
      *run detached* is your host's own background mechanism only `1` holds**: no
      selector on that host names this invocation, so `2` is the steady state, a `0`
      or a `3` is an earlier run's record left in the same phase dir and names no
      verdict for this run — the exit code is read as nothing, so relay the rendered
      line exactly as on a `2` and keep polling — and the loop ends on the
      background mechanism's own completion or error signal instead.
      An **instant** return is itself a reading, and exactly one reading: `--wait`
      holds its whole deadline for a selection that is still empty and for a
      checkpoint still doing work, so the only way back early is a terminal `run`
      record over a checkpoint that has stopped as well. That is a terminal
      *record*, which is not the same claim as a finished *phase*. A phase dir is
      re-used run after run and the write that claims it for this run is what drops
      the predecessor's halves, so until that write lands the whole checkpoint is
      the earlier run's and its halves agree with each other. The `phase state:`
      line and the `models` table are the halves this run writes, and they are what
      to read before believing an instant `0`:
      `models_running` over rows with a fresh elapsed is this run,
      `complete` over rows aged to their budget is the last one. And a poll your
      host killed at its own time limit is **not** exit `1`: it returns no exit code
      at all, the two are indistinguishable afterwards, so a killed poll is relayed
      as nothing and re-issued with the right call timeout — never reported as the
      run failing.
   3. **No movement is reported, not judged.** Nothing here tells "thinking" from
      "stuck", so do not try to. The rule is mechanical: when two consecutive polls
      show the same `models` map — same states, same `attempt`, nothing newly
      terminal, and a live row's elapsed advancing on its own is not a state
      change — add one clause to that poll's line naming the row it is about, `no
      state change in the last N minutes; <model spec>'s budget runs to
      <timeout_s>`, and keep polling. With several rows still live, name the one
      that has been running longest: a bare `<timeout_s>` and no row beside it is a
      deadline the user cannot attach to anything. A silent provider is not an
      error until its slot's deadline says so.
   4. **A ceiling, and the kill path in the first line.** Stop once the longest
      slot's `timeout_s` plus one interval has passed with **no movement in
      `progress` at all** — neither a `models` transition nor a `step` change,
      because a run that is grouping or validating after its last model has a frozen
      map and is not stuck — and still no terminal verdict; report the run as
      unfinished rather than polling forever. Where the verdict can never turn
      terminal, that ceiling is the backstop for a completion signal that never
      arrives rather than the normal exit. The **first** relayed line names the kill
      path, so the user has a way out from the start without having to ask for one;
      later lines do not repeat it. Which command that is follows the *run detached*
      verb and nothing else: where the run was launched with `--detach`, it is `…
      multi_llm.py status "<plan>" --abort`; where *run detached* is your host's own
      background mechanism the run holds no `run` record for `--abort` to reach —
      it answers `nothing was running (no_run)` and exits 2 — so the kill path there
      is stopping that background job by the handle you launched it with.
   5. **The interval is a UX cost, and that is what sets it.** Each poll is one
      foreground call that blocks for its whole duration, and the user cannot
      interrupt you mid-call — at 300 s someone who wants to abort waits up to five
      minutes for you to come back. That is the argument for 120 to 300 seconds and
      against pushing the interval to your host's hard cap, and it is what
      `<interval>` is set from on the command you compose. State in the first
      relayed line the gap you will **actually** wait, so it is expected rather than
      read as a hang — and that is `<interval>` only on the command you composed. A
      poll of the command the launcher printed carries no `--timeout` of its own and
      waits whatever `progress.poll_s` resolves to, 90 s unless the project
      configured it; state that number there instead. Announcing an interval you are
      not waiting is worse than announcing none.

   **Resume**: re-invoking with `--force` RESUMES (keeps already-completed per-model result files, runs only the missing models); `--rerun-all` forces a full re-run discarding existing per-model results. Pass the **same `--models` selection as the original run** (`models_requested` in `{plan}/code-review/.status.json`), never only the missing ones: the orchestrator skips the models that already have a result, and the run's report covers only the models passed. A kept result must have reviewed the current scope: when the change moved since it was written, the model re-runs (`[SCOPE_CHANGED]`) and its old file is kept as `{model}.json.stale-<scope id>`.

   The orchestrator will output (to the log):
   - `Git base reference: {commit}` - showing which base ref is being used
   - Where the scope came from, one of: `Using N files given with --files (…)`;
     `Using N tracked files from implementation phase`; or, when neither exists,
     `No tracked files in state, falling back to git diff from {base_ref}`
     followed by `[SCOPE_FALLBACK]` lines (the file count per group — source,
     tests, fixtures, generated — whether a `pre_existing_changes` baseline
     existed, and the worktree-wide count of untracked files the diff left out,
     with a sample) and, above 200 source and test files, `[SCOPE_LARGE]` with
     its remedy. Relay a `[SCOPE_FALLBACK]` or `[SCOPE_LARGE]` line to the user:
     the review is over a guessed scope.
   - `Left out N of the workflow's own file(s) …` - the plan, its task list, its
     output folder and commit reviews are never code under review, whichever
     source named them.
   - `Files to review: N` - the resolved scope every reviewer is given, source
     files first
   - `Review scope written (scope <id>, coverage complete|partial, …)` - the
     manifest and diffs every reviewer is pointed at. `[DIFF_FAILED]` and
     `[DIFF_PARTIAL]` mean git produced no diff for some files (reviewers
     without a shell cannot review those), and `[REVIEW_UNSUPPORTED] <model>`
     means that model could not open the files and they did not fit inline, so
     it was not run and is listed as failed. Relay any of the three to the user.

6. **Salvage Handling (Post-Orchestrator):**

   When the poll loop above ends, check the log file `{plan}/code-review/orchestrator-run.log` for `[SALVAGE_NEEDED]` markers. Follow the salvage process in `references/salvage-handling.md`.

   The reaggregation command for this mode is:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code \
     --plan-file "$PLAN_PATH" \
     --reaggregate
   ```

7. **Validation Handling (Post-Orchestrator):**

   When the poll loop above ends, check the log file `{plan}/code-review/orchestrator-run.log` for validation markers.

   #### The task file

   `validation_tasks.json` carries `tasks_schema_version: 2` and one complete
   task per batch under `batches` — each with `prompt`, `output_name`, the
   derived `output_path`, `prompt_path` and `prompt_lines`,
   `result_channel: file`, `context_mode`, `capability_tier`,
   `executor_role` and `task_id`. The sidecar at `prompt_path` holds exactly the
   bytes of `prompt` (`prompt_lines` is its line count), so the two are
   interchangeable and a host that would otherwise re-emit the whole prompt can
   point the subagent at the file instead. The plan excerpt, this batch's issue
   records (including each issue's `file` and `line_range`) and the
   code-inspection guidance all travel **inside** `prompt`. A plan within the
   inline limit is complete there, and the task is `context_mode: inline`. A
   larger plan keeps a head excerpt and is also named once under
   `## Plan file`: a hash-bound snapshot, `validation-snapshot.md` in this phase
   dir, and the task is `context_mode: workspace-read`. The subagent must be able to read
   that path, so do not run it where it cannot. Never treat such a batch as
   having the full plan inline. The reviewed-code block is never named by path.

   **For each task in the file: when the task carries `prompt_path`, run a
   subagent that reads that file in full — through line `prompt_lines`, paging
   if a single read stops short — and follows it verbatim; otherwise, or if the
   file is absent, run `task.prompt` as a subagent. Either way, write the JSON
   it returns to `task.output_path`.** That is the whole contract — do not
   assemble a prompt beyond that one read instruction, and do not tell the
   subagent to write the file itself. The file's bytes are exactly
   `task.prompt`; the two are interchangeable.

   A file whose `tasks_schema_version` is missing or not `2`, or whose recorded
   `inputs` hashes no longer match the plan and grouped.json, is refused with
   exit 3: re-run the phase with `--force` to re-materialize it. A
   `--reaggregate` of a review completed before the latest implement is
   refused the same way (exit 3, naming the `--force` re-run): its results
   judge an earlier state of the code, and reaggregating would only re-stamp
   them.

   #### Single Batch: `[VALIDATION_PENDING]`

   If `[VALIDATION_PENDING]` marker is present:
   1. Read `validation_tasks.json` from `{plan}/code-review/`
   2. Run the single task as the contract above says — the sidecar at
      `prompt_path` when it has one, `task.prompt` otherwise — and write its
      JSON reply to that task's `output_path`; do not run the next step, or end your turn, until that file exists and is not empty

   **Record metrics** for each validation subagent. When the validation phase used multiple batches, include the cumulative `--batch-index` (1..N across waves) and `--total-batches` so the script prints an `[ETA]` line:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics record \
     --state-file "$STATE_FILE" --phase "code-review" \
     --label "Validation batch {N}" --subagent-type "agent" \
     --tokens {token_count} --tool-uses {tool_uses} --duration-ms {duration_ms} \
     --total-batches {total_batches} --batch-index {N}
   ```
   Where `token_count`, `tool_uses`, `duration_ms` come from whatever your subagent mechanism reports. Omit any flag it does not report. Never pass `0` for an unknown value; omit the flag — a made-up zero is averaged into the phase totals as a real measurement. Single-batch validation runs may omit `--total-batches`/`--batch-index`.

   3. Run the reaggregation command under **Reaggregation (After Validation)** below. `validation_tasks.json` records `reaggregate_mode` + `plan_file`, never a resolved command, so the command is rebuilt from those two values

   #### Multiple Batches: `[VALIDATION_BATCHES_PENDING]`

   If `[VALIDATION_BATCHES_PENDING]` marker is present (for 5+ issue groups):
   1. Read `validation_tasks.json` once from `{plan}/code-review/`
   2. Count the number of batches as `{total_batches}` and mark the phase start:
      ```bash
      uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics start \
        --state-file "$STATE_FILE" --phase "review-code-batches" --total-batches {total_batches}
      ```
   3. Choose a strategy:

   **Strategy A: Direct parallel spawning (≤ 4 batches)**

   For each task in the `batches` array, run the task exactly as the contract above says — the sidecar at `prompt_path` when it has one, `task.prompt` otherwise — and write the JSON it returns to that task's `output_path`.

   **Run all batches in parallel** (one batch of parallel subagent spawns).

   **Strategy B: Wave-based parallel spawning (> 4 batches)**

   Follow the wave-based spawning strategy in `references/wave-batching.md`.

   **Check each reply right after you write it.** Run
   `uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util check-reply --tasks-file "{plan}/code-review/validation_tasks.json" --task-id <task_id>`
   (omit `--task-id` to check every batch, and only once every batch's subagent has
   returned: a reply not written yet prints `[REPLY_MISSING]`, which is no bad reply and
   no re-ask). `[REPLY_INVALID]` means the subagent's reply
   did not parse or did not cover its groups — Sonnet subagents lost a closing `]` on 3 of
   14 batches in the 2026-10-01 Claude Code run. Re-ask the same subagent once for the
   whole reply and write the new reply over the file. Never edit, trim or complete a reply
   yourself, and never assemble one from the parts of two replies. A batch still
   `[REPLY_INVALID]` after that one re-ask is a failed batch: leave its file as it is and say so.

   **Before you continue: verify every batch wrote its file, and do not end your turn before it has.** Confirm that each task's `output_path` exists and is not empty. Re-dispatch any task whose file is missing — exactly as the contract above says — and write its reply yourself; only a batch that comes back empty-handed a second time is a failed batch, and a batch nobody re-dispatched is not one. Spawn batches so their replies return inside this turn, and stay in the turn until the last file is on disk: **you** write these files, not the subagents, and a host that runs one headless turn has no second turn in which to write them — a reply that lands after the turn ends is a batch lost with nothing on disk to say so. Naming the batch you are waiting on is not waiting for it.

   3. After ALL batches complete, run the reaggregation command below (rebuilt from `reaggregate_mode` + `plan_file`)

   #### Reaggregation (After Validation)

   After validation completes, rebuild the reaggregation command from `reaggregate_mode` + `plan_file` in validation_tasks.json — the file stores that durable pair rather than a resolved command, so a skill dir that moved with a plugin update cannot leave a dead path behind:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code \
     --plan-file "$PLAN_PATH" --reaggregate
   ```
   Run it bare, exactly as shown: no `| tail` or any other pipe, no `2>&1`, nothing chained before it. A pipe reports the last command's exit code, not this one's, and a trim drops the `[MODEL_FAILED]` and `[NEXT_COMMAND]` lines above its result line. Only the detached launch redirects its output (into `orchestrator-run.log`); this call runs in the foreground.

   After reaggregation, mark the validation phase finish (only if `start` was called above):
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics finish \
     --state-file "$STATE_FILE" --phase "review-code-batches"
   ```

   **CRITICAL**: Do NOT report results to the user until reaggregation is complete.

8. **If `--apply-fixes` was used, apply fixes by spawning subagents:**

   After the orchestrator outputs `{prefix}_fix_tasks.json`, **spawn one subagent per issue**.

   Before the fix loop, mark the phase start where `{total_fixes}` is the number of fix tasks:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics start \
     --state-file "$STATE_FILE" --phase "review-code-fixes" --total-batches {total_fixes}
   ```

   For each fix task in the JSON file:

   a. Read the fix tasks JSON file to get the list of issues to fix
   b. For each task, spawn a subagent:
      ```
      Spawn one subagent with:
      - executor_role: "agent"
      - description: "Fix: {task.title}"
      - prompt: |
          Fix the following code issue:

          **Issue**: {task.title}
          **Type**: {task.type}
          **Importance**: {task.importance}
          **Description**: {task.description}
          **Location hints**: {task.location_hints}

          Plan file for context: {task.plan_path}

          1. Read the relevant files and understand the issue
          2. Make the necessary code changes to fix it
          3. Verify your changes don't break anything

          After fixing, report what you changed.
      ```
   c. Track fix results (success/failure) for each task

   **Record metrics** for each fix subagent:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics record \
     --state-file "$STATE_FILE" --phase "code-review" \
     --label "Fix: {task_title}" --subagent-type "{executor_role}" \
     --tokens {token_count} --tool-uses {tool_uses} --duration-ms {duration_ms} \
     --total-batches {total_fixes} --batch-index {N}
   ```
   Where `token_count`, `tool_uses`, `duration_ms` come from whatever your subagent mechanism reports, and `{N}` is the 1-based fix index. Omit any flag it does not report. Never pass `0` for an unknown value; omit the flag — a made-up zero is averaged into the phase totals as a real measurement. The script prints an `[ETA]` line to stderr after each call.

   d. After all fixes are attempted, mark the phase finish:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics finish \
     --state-file "$STATE_FILE" --phase "review-code-fixes"
   ```

   e. Update the plan file with a "Review Fixes Applied" section documenting what was fixed

## Post-Fix Workflow

After spawning subagents to apply fixes:

1. **Wait for all subagents to complete**
   - Track success/failure of each fix

2. **Run verification**
   Run the repository's own typecheck/lint commands, if any (for example
   `pnpm typecheck` and `pnpm lint:fix` in a pnpm project) — this plan may
   have neither.

3. **Update `{plan}_code_review.md`** with implementation status for each issue:

   For each issue in the code review file, add an "Implementation" subsection:

   ```markdown
   ### Issue N: [Original Title]
   **Type**: security | **Importance**: HIGH
   **Description**: [original description]
   **Location Hints**: [original hints]

   #### Implementation Status: FIXED
   **Files Modified**:
   - `path/to/file1.ts` - Added input validation
   - `path/to/file2.ts` - Updated error handling

   **Summary**: Added proper input sanitization to prevent SQL injection...
   ```

   Or if not fixed:
   ```markdown
   #### Implementation Status: NOT FIXED
   **Reason**: Requires architectural changes beyond scope of this review
   ```

4. **Update the original plan file** by appending a reference section:

   ```markdown
   ---
   ## Code Review Applied

   A code review was performed on this implementation. See the full review and implementation details at:
   **[{plan}_code_review.md](./{plan}/{plan}_code_review.md)**

   **Summary**: X of Y issues were fixed.
   **Date**: [timestamp]
   ```

6. **Report results** following `references/summary-format.md`, including files in `{plan}/code-review/`:

   Generate resource usage:
   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util metrics report \
     --state-file "$STATE_FILE" --phase "code-review"
   ```
   Include the output (if non-empty) in the results report.

   - `report.md` - Review report
   - `issues.json` - Raw issues
   - `grouped.json` - Grouped issues
   - `validation.json` - Validation results
   - `fix_tasks.json` (if --apply-fixes)
   - Summary of issues by severity
   - Summary of fixes applied (if --apply-fixes)

   Report the verdict counts from `MULTI_LLM_RESULT.validation_counts` (`{valid, invalid, needs_human_decision, validation_failed}`, present only when validation ran, and carried by `status --view run` too). If `needs_human_decision` or `validation_failed` is non-zero, point at `report.md` for those groups; they are decided in apply-code-fixes.

   Name every reviewer that produced nothing, with its reason (`references/summary-format.md`). `report.md` lists them on its `**Models failed:** N of M requested — …` line, directly under `**Models:**`. A `--reaggregate` also prints one `[MODEL_FAILED] <model>: <reason>` line per requested reviewer that still has no result, and, when any is left, prints `[PARTIAL_RESULTS: <model>,…]` and sets `MULTI_LLM_RESULT.state: "partial"` with exit **0**: the phase is still complete and `next` stays `null`, so nothing is retried — report the failures from those lines (or from the `failed` rows of `progress.models`). A `--reaggregate` that finds no readable result at all while reviewers are recorded failed exits **3** naming them and the `--force` retry, and records no completed phase.

   A reviewer can write its result under the wrong file name. The plugin then says what it did, in a line you give as printed: `[RESULT_FILE_MISNAMED] <model> wrote its result to <file> instead of <file>; …` (it read the result from there, so that reviewer did not fail), or `[RESULT_SET_ASIDE] <file> is not the result file of any model this review ran (…)` (left out of the report and renamed, nothing deleted). `report.md`'s `**Result files:**` line has the same words. Never guess where such a file came from, and never call it a leftover of an earlier run unless the plugin says so.

---

## Example Executions

### Example 1: Review Code (no models provided)

```
User: /multi-llm:multi-llm --review-code plans/my-feature.md

Agent:
1. No models in args, so the agent asks the user:
   "Which models would you like to use for the code review?" (multi-select)
   Options: auto, gpt-5.2, gemini-3-pro, grok, gemini-3-flash, kimi-k2
2. User selects: gpt-5.2
3. Runs: uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code --plan-file plans/my-feature.md --models gpt-5.2
4. Claude reports review findings and output files
```

### Example 2: Review Code with --apply-fixes

```
User: /multi-llm:multi-llm --review-code --apply-fixes plans/my-feature.md

Agent:
1. No models in args, so the agent asks the user to select models
2. User selects: gemini-3-pro
3. Runs: uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code --plan-file plans/my-feature.md --models gemini-3-pro --apply-fixes
4. Orchestrator outputs:
   - my-feature_code_review.md (report)
   - my-feature_fix_tasks.json (3 valid issues to fix)
5. Claude reads fix_tasks.json and spawns subagents for each fix:
   - Task 1: "Fix: Missing null check in user validation" -> Subagent fixes it
   - Task 2: "Fix: SQL injection vulnerability" -> Subagent fixes it
   - Task 3: "Fix: Incorrect error message" -> Subagent fixes it
6. Claude updates the plan file with "Review Fixes Applied" section:
   - Successfully Fixed: 3 issues
   - Files modified: auth.ts, db.ts, errors.ts
7. Reports final summary including fixes applied
```
