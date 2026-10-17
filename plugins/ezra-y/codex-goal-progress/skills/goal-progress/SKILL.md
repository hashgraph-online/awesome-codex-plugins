---
name: goal-progress
description: Explicitly attach verified checklist progress to one native Codex Goal. Use only when the user explicitly selects Goal Progress or invokes $codex-goal-progress:goal-progress. Do not use for an ordinary Goal, a status question, or update_plan.
---

# Goal Progress

Goal Progress adds verified checklist progress to one native Codex Goal.
The Skill is the only user-facing activation entry. Internal tools never activate it by themselves.

## Entry

Start only after explicit Skill selection or the canonical marker. Do not activate for an ordinary
Goal, a status question, `update_plan`, or a general mention of progress.
After the explicit start, continue for the bound Goal without requiring the marker on every later turn.
When trusted SessionStart context says the Contract is active, call `goal_progress_get` and continue
without asking the user to repeat the marker. Do not call `goal_progress_activate` again.

Keep progress work in the current thread and current model. Never start a hidden thread, child Agent,
external model, or model API call for progress. Only the main execution Agent may use write tools; a
nested or child Agent must not initialize, update, rescope, or set phase.
Hooks supply `_runtimeContext` and `_runtimeProof`; omit both from authored arguments.
Read revisions from tool results. Core calculates every percentage.

## Start Or Resume

Read [Activation and recovery](references/activation-and-recovery.md) for a first activation,
cancellation, or recovery.

1. Remove every pure Skill marker line and preserve all other body lines in order.
2. If the user explicitly asks to change an existing native Goal, use Codex `update_goal` first.
   Goal text goes only to the native Goal tool.
3. Call `goal_progress_activate` with an empty object as the first Goal Progress tool.
4. Follow `progressAction` exactly:
   - `get`: call `goal_progress_get` and reuse the existing Contract.
   - `initialize`: prepare the Checklist and call `goal_progress_initialize` with `source` and
     `objectives`. Omit `contractId`; the plugin generates and returns it. Do not call `goal_progress_get` first.
   - `rescope-or-replace`: compare the current native Goal with the existing Checklist. Rescope
     only affected results, or initialize a fresh Contract for a major change.
   - `none`: do not call another Goal Progress tool.
5. Report active only after `goal_progress_get` or `goal_progress_initialize` succeeds.

If activation returns `NATIVE_GOAL_REQUIRED`, create a native Goal from the marker-free user body
with Codex `create_goal`, then call empty `goal_progress_activate` once more. If the body is empty,
ask the user for the Goal instead of creating an empty one.

## IDs At A Glance

- First initialization: omit `contractId`. Later writes copy the returned `contractId` unchanged.
- Objective IDs: `C1`, `C2`. Child IDs: `C1.1`, `C1.2`, `C2.1`. These are not UUIDs.
- Reuse IDs for existing results, even after reordering or renaming. Correct only the field named
  in a validation error; leave the native Goal and accepted Checklist unchanged.

## Checklist

Before generating a Checklist for the first time, changing the acceptance scope, or replacing a
Contract, read [Checklist organization and scope changes](references/checklist-and-scope.md).

When restoring existing progress or updating completion status, continue using the existing
Checklist, IDs, and weights.

## Work Loop

Keep `update_plan` as an execution plan. Never turn its steps into the Goal denominator.
Complete normal Goal work. After a concrete fact is completed or verified, call
`goal_progress_get`, then `goal_progress_update` with stable target IDs and the returned revision.
Leave uncertain work unchanged. Active work alone does not earn progress.
Never call a model merely to refresh progress. Core computes every percentage.
On a revision conflict, review the returned current summary before retrying.

## Native Goal Changes

The model may create or update the native Goal with Codex native Goal tools. Goal Progress follows
the trusted current native Goal after that change.
When the trusted native Goal changes, classify the change as minor or major in the current model.
Do not use text similarity, another model, or another thread.
Do not ask the user to invoke Goal Progress again.
A wording-only change keeps the existing Checklist. A minor scope change keeps the Contract and
uses `goal_progress_rescope` for affected results only.
A major change prepares a fresh Contract and uses `goal_progress_initialize`.
Ordinary implementation, bug-fix, or `update_plan` changes do neither.

## Finish

Run final verification and update only verified remaining targets.
Mark the native Goal complete only when its objective is achieved.
Set Goal Progress to `completed` only after both the Contract and native Goal are complete.

## References

- [Activation and recovery](references/activation-and-recovery.md)
- [Checklist and scope](references/checklist-and-scope.md)
- [Contract examples](references/contract-examples.md)

## Uninstall

For an explicit request to uninstall the source plugin, call `goal_progress_uninstall` when available. It removes this plugin, its Helper and its progress data while keeping native Goals and other plugins. Do not use uninstall to finish or hide a Goal. The first response means removal has started; the returned status log contains the final result.
