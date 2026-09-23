# Activation And Recovery

Read this file only for first activation, cancellation, or recovery.

## Entry Parsing

The Skill is already explicit when this flow starts. Treat repeated identical marker lines in one
message as one invocation. Remove every line whose trimmed value is exactly
`$codex-goal-progress:goal-progress`. Preserve all other lines in order as one objective body.

Call `goal_progress_activate` with `{}`. It reads the trusted current native Goal; model-written
Goal text is never an activation argument. The result does not mean the Contract is active.

## Activation Results

| Current state | Result | Action |
| --- | --- | --- | --- |
| No native Goal | `NATIVE_GOAL_REQUIRED` | Create a native Goal from the marker-free user body, then activate once more. If the body is empty, ask for it. |
| Native Goal without Contract | `initialize` | Prepare a Checklist for `currentNativeGoal`, then initialize. |
| Native Goal with matching Contract | `get` | Reuse the existing Contract. |
| Native Goal changed after binding | `rescope-or-replace` | Preserve the existing Checklist where it still applies; rescope a minor change or initialize a major replacement. |

## Progress Action

Follow `progressAction` exactly:

- `get`: call `goal_progress_get`. Do not rebuild Checklist or contributions.
- `initialize`: do not call `goal_progress_get`. Read the Checklist reference, prepare one Contract,
  and call `goal_progress_initialize` with `source` and `objectives`, omitting `contractId`.
  The plugin generates the Contract ID and binds the current native Goal itself.
- `rescope-or-replace`: first preserve the existing Checklist. If the Goal only changed wording,
  keep the Checklist. For a minor scope change, change only affected objectives with
  `goal_progress_rescope`. For a major change, initialize a fresh Contract and Checklist.
- `none`: stop Goal Progress tool calls for this activation.

When the first activation returns `NATIVE_GOAL_REQUIRED`, the allowed sequence is:

```text
goal_progress_activate
create_goal
goal_progress_activate
goal_progress_initialize
```

Both activation calls use `{}`. Goal text is supplied only to the Codex native Goal tool.

## Lifecycle Reports

- `planned`: activate returned an action, but no Contract is proven.
- `preparing`: Goal or Checklist preparation is running.
- `active`: `goal_progress_get` or `goal_progress_initialize` succeeded.

After activate, say Goal Progress is being prepared. Do not say it is active yet.
After get, say the existing Contract was restored or connected.
After initialize, say Goal Progress is active.

## Cancellation And Recovery

`ACTIVATION_CANCELLED` means the user explicitly closed the current preparation. Do not retry or
reactivate until the user explicitly selects the Skill again.

These conditions are not user cancellation:

- an old Contract was detached as stale;
- the native Goal ended or was replaced;
- the Goal anchor was rebuilt;
- Helper or native Goal reads are temporarily unavailable.

Continue the current preparation after a trusted native Goal update. For temporary infrastructure
failure, report the exact code and use doctor or a bounded retry without changing the user's
activation fact. Do not blame the user or ask for another Skill selection.

When trusted SessionStart context reports an active Contract, call only `goal_progress_get`.
Do not call activate, regenerate the Checklist, or reevaluate contributions.
