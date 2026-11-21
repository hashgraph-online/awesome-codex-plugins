# Implement prerequisite markers

Read this only when the implement orchestrator's output (the core's step 2) carries
one of `[PREREQUISITE_UNMET]`, `[PREREQUISITE_CHECK]`, `[TASKS_MISSING]` or
`[TASK_SUGGESTIONS_ADVISORY]`; an output with none of these four has its
prerequisites met: go on with the rest of the core's step 3.

**Commands.** This file is read as it is, so its commands are spelled from the
mode word on: `<prefix>` stands for the dispatcher prefix every command in the
core starts with (`uv run … --project "<skill dir>" -- python "<skill dir>/multi_llm.py"`,
flags and paths exactly as the core prints them). Copy it from any command in
the core, unchanged, and run each command bare, as the core runs its own. A
`<dispatcher>` in a block shown to the user is that block's own placeholder, as
the block prints it.

## If output contains `[PREREQUISITE_UNMET]` (under `--yes`):

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

## If output contains `[PREREQUISITE_CHECK]` (no `--yes`):

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

   - **"Skip suggestions, proceed"**: Run `<prefix> apply-suggestions --plan-file "$PLAN_PATH" --skip`, then re-run implement orchestrator (this is lightweight — no context bloat)
   - **"Cancel"**: Stop and inform user

## If output contains `[TASKS_MISSING]`:

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

## If output contains `[TASK_SUGGESTIONS_ADVISORY]`:

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

- **"Skip, proceed to implement"** (default): Run `<prefix> apply-task-suggestions --plan-file "$PLAN_PATH" --skip` to mark the phase as skipped, then continue with implementation.

- **"Cancel"**: Stop and inform user.

**Important**: The `[TASK_SUGGESTIONS_ADVISORY]` marker does NOT cause the orchestrator to exit early. The orchestrator continues and produces the full task JSON output. Check for this marker in the complete output alongside the other markers.

## If output contains no blocking markers (`[PREREQUISITE_CHECK]` or `[TASKS_MISSING]`):

Prerequisites are met. If `[TASK_SUGGESTIONS_ADVISORY]` was present, handle it as described above, then proceed with normal implementation flow: the rest of the core's step 3, then step 4.
