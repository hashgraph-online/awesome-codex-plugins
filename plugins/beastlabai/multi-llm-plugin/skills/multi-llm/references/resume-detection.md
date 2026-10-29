# Resume Detection

Check for existing output BEFORE running the orchestrator to avoid expensive duplicate runs.

## Detection Cases

Check in this order:

a. If `{plan}/{phase}/validation.json` exists:
   -> Phase is complete. Report results from `{plan}/{phase}/report.md` (or `report.html`) and skip.

b. If `{plan}/{phase}/validation_tasks.json` exists AND `validation_batch_*.json` files exist:
   -> Validation ran partially or fully. Check if all batches complete.
   If all complete: run `--reaggregate` to finalize.
   If partial: re-run only missing validation batches, then reaggregate.

c. If `{plan}/{phase}/validation_tasks.json` exists but NO `validation_batch_*.json`:
   -> Orchestrator completed but validation was interrupted. Skip to Validation Handling.

d. If per-model `*.json` files exist in `{plan}/{phase}/` but no `grouped.json`:
   -> The fan-out stopped before grouping. Compare the files with `models_requested` in
   `{plan}/{phase}/.status.json`.
   If every requested model has its file: run `--reaggregate`.
   If some have none: run the orchestrator again with the same models. It keeps each
   file (`[SKIP]`) and runs only the missing ones; a `--reaggregate` would report
   without them. On review-code add `--force`, which a dir holding results needs
   (exit 3 otherwise); a composite's flags line already carries it. Never `--rerun-all`.

e. If none of the above: proceed to run the orchestrator.

f. If `.status.json` exists with `state: "validation_pending"`: equivalent to case (c) — skip to Validation Handling.

## Orchestrator Guards

The orchestrator has its own re-run protection as defense-in-depth:
- **Primary**: Exits with code 2 if phase is already marked complete in state.json. Use `--force` to override.
- **Secondary** (code-review only): Exits with code 3 if partial completion artifacts exist without the phase being complete.

This instruction-level resume detection is the FIRST line of defense; the orchestrator guards are backup protection.
