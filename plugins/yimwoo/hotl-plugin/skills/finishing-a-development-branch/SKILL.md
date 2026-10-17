---
name: finishing-a-development-branch
description: Use after execution is complete or intentionally stopped — decide whether to merge back, publish a PR branch, keep the execution checkout, or discard it, and record that disposition in HOTL state.
---

# Finishing A Development Branch

Use this after `loop-execution`, `executing-plans`, or `subagent-execution` when the run already has a `run_id` and you need to decide what happens to the execution branch/worktree next.

## Core Idea

HOTL distinguishes between:

- **Authoring checkout** — where the workflow was written (`source_branch`, `source_head`)
- **Execution checkout** — where the workflow ran (`branch`, `execution_root`, `worktree_path`)

Finishing is the stage that closes that loop intentionally. Do not silently merge, delete, or abandon the execution worktree.

## Step 1: Read Execution Provenance

Run:

```bash
hotl-rt summary <run-id> --json
```

Surface these fields before presenting options:

- `status`
- `source_branch`
- `branch`
- `execution_root`
- `worktree_path`
- `finish.disposition` (if already recorded)
- controller owner/status and receipt reasons

If `finish.disposition` is already set, stop and tell the user the run is already finished.

A successful execution must be `ready_to_finish` before merge or publish. `ready_to_finish` means execution evidence is complete but the run is not yet `completed`. Keep the existing controller lease active and retain `HOTL_OWNER_TOKEN`; if a different controller is finishing, use explicit owner handoff/takeover rules from `resuming` first. Run `owner heartbeat` before a long finish operation.

## Step 2: Present The 4 Finish Options

Use these options:

1. **Merge back locally**
   - Default target: `source_branch` when present and different from the execution branch
   - Fallback target: `main` or `master`
2. **Publish branch / create PR**
   - Push the execution branch to a remote
   - If `gh` is available and the user wants a PR, create it against the chosen target branch
3. **Keep as-is**
   - Preserve the execution branch/worktree for later review or follow-up changes
4. **Discard**
   - Remove the execution branch/worktree after explicit confirmation

Explain the target branch explicitly when merge or PR target is inferred from `source_branch`.

## Step 3: Authorize External Effects

For publish/PR, record one bounded `external_write` with the exact target `publish <branch> to <remote>` (append ` and create PR against <target-branch>` when `--create-pr` is used), pass `--idempotency-key <stable-key>`, obtain human `action decide ... approved --mode human`, and pass the returned action id and key to the helper. If a merge is classified as `production_change`, use the exact target `merge <branch> into <target-branch>`. The helper verifies kind, target, key, approval, and not-started status; it then performs `action begin` immediately before the effect and `action complete` with observed evidence before recording finish.

Approval is not effect evidence. If the helper stops after a push, PR attempt, or merge may have started, leave the action unresolved, inspect the target, and use `action reconcile`. Never rerun the helper while the effect is `in_progress` or `uncertain`.

## Step 4: Execute Via The Helper

Use the repo-owned helper:

```bash
scripts/hotl-finish-execution.sh --run-id <run-id> --mode <keep|merge|publish|discard> ...
```

Mappings:

- Keep → `--mode keep`
- Merge locally → `--mode merge [--target-branch <branch>]`
- Publish / PR → `--mode publish [--remote origin] [--target-branch <branch>] [--create-pr]`
- Discard → `--mode discard --confirm discard`

For an approved merge/publish effect, also pass `--effect-action-id <id> --idempotency-key <key>`. The helper records intent with `action begin`, executes the bounded effect, persists `action complete` evidence, then records the finish disposition with `hotl-rt finish ...`. It enforces safety checks around branch switching, merging, cleanup, and destructive discard. `HOTL_OWNER_TOKEN` must remain in the helper environment.

## Step 5: Report The Outcome

After the helper succeeds, show:

- Finish disposition
- Target branch / PR URL if applicable
- Whether the execution worktree was kept or removed
- Where the durable report lives

Then run `owner release` and derive a fresh receipt. Claim completion only when the run is `completed` and `sufficiency.sufficient` is true. A failed helper must leave finish unset; use `action reconcile` before another attempt when an external effect may have occurred.

Important behavior:

- Merge and discard preserve `.hotl/state/<run-id>.json` and `.hotl/reports/<run-id>.md` back into the repo checkout before removing an isolated execution worktree
- Publish keeps the execution worktree by default so review follow-ups can continue on the same branch
- Shared-checkout same-branch runs are intentionally conservative; discard and merge may require manual handling if automation would be ambiguous or destructive

## Guardrails

- Do not auto-merge after execution just because tests passed
- Do not auto-delete work without explicit user confirmation
- Do not create a PR unless the user chose the publish/PR path
- If merge conflicts occur, stop and leave the execution branch/worktree intact
- If a chosen PR operation cannot run because `gh` is unavailable or fails after push, do not silently downgrade the approved target. Leave finish unset, reconcile the observed push, and ask whether the user wants a new bounded push-only action.
