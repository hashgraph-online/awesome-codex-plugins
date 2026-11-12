# Interrupted-run Recovery (review fan-outs)

Read this only when a review core sends you here: its detached orchestrator was
interrupted (the session ended, the background process was killed), or the poll
loop ended and `{plan}/{phase}/orchestrator-run.log` shows neither a validation
marker nor a clean completion. `{phase}` is the phase directory the core names
(`review-plan`, `review-tasks`). A run that was not interrupted and whose
`orchestrator-run.log` shows a validation marker or a clean completion never
needs this file.

1. Read `{plan}/{phase}/.status.json`.
2. Determine progress from its `state` field:
   - `models_running`: check which `{model}.json` files exist in `{plan}/{phase}/`
     (those models completed).
   - `models_complete` / `grouping_complete`: check for `grouped.json` and
     `validation_tasks.json`.
   - `validation_pending`: the orchestrator completed normally; go on to the core's
     validation step using `validation_tasks_path` from the status file, then
     reaggregate. Both the status file and the tasks file record the mode and plan
     path (`reaggregate_mode`, `plan_file`) rather than a resolved command, so a
     plugin update cannot leave a stale skill-dir path behind; `multi_llm.py status
     <plan> --view run` prints the command resolved against the running skill dir.
   - `complete`: report results.
3. With no `.status.json`, fall back to the file-based detection in
   `references/resume-detection.md` (the core's resume-detection step).
4. **With `--yes` (or `--non-interactive`): always resume, never ask** (D6 row 3).
   Re-run with `--force` and the original run's full `--models` selection
   (`models_requested` in `.status.json`). Only the missing models actually run:
   the retry prints `[SKIP] <model> - already has results` for each model it keeps,
   so tell the user which model re-ran and which kept its result. Never
   `--rerun-all`: it discards work that succeeded. If a model fails a second time
   in the same run, reaggregate with what exists: the orchestrator (the fan-out or
   `--reaggregate` alike) prints `[PARTIAL_RESULTS: <model>,…]`, names the failed
   models and their reasons on the report's `**Models failed:**` line and in
   `.status.json` (`models_failed`, and the `failed` rows of `progress.models`),
   sets `MULTI_LLM_RESULT.state: "partial"` and exits **0**: a partial aggregate is
   usable output, the phase is recorded complete and `next` stays `null`. The one
   exception: if *no* model produced a result there is nothing to aggregate, so it
   exits **3** naming the retry command (a `--reaggregate` does so when the
   checkpoint records failed models) and records no completed phase.
5. Without `--yes`, **ask the user**, showing:
   - which models completed successfully;
   - which models failed or were interrupted;
   - the options: (a) proceed with partial results (`--reaggregate`), (b) resume,
     re-running only the missing models (`--force` with the original full
     `--models` selection), (c) re-run everything from scratch
     (`--force --rerun-all`).

Then return to the core's next step (salvage, then validation).
