---
name: release-archivist
description: Close out a spec-superflow change with verification, summary, and archive readiness. Invoke when implementation is complete, verification is underway, or the user asks for a final wrap-up.
---

# Release Archivist

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

## Workflow routing

A new request follows this file without loading legacy instructions. For an existing change, inspect the recorded state and receipt/plan (available through `SSF workflow show <change-dir> --json` and `SSF execution show <dir> --json` when needed). Current paths are `workflow_variant: direct` with a valid workflow-selection receipt `schema_version: 3`, or `workflow_variant: planned` with an execution plan `schema_version: 2`. Older receipts (schema 1/2), legacy plans and other recorded variants use the matching section of `SSF runtime asset read docs/legacy-workflow.md`; follow that section for this change. A direct variant alone is insufficient: legacy Quick/Hotfix/Lightweight can also record it. The internal `workflow: full` value alone is not a legacy signal. Missing or corrupt state, receipt or a required plan is a recovery problem; preserve evidence rather than reinitialize or downgrade the change.

Read `SSF resume <change-dir> --json`. In `executing`, complete verification and logical closure. In `closing`, perform only recorded pending physical finish, if merging is authorized. `abandoned` or a completed finish requires no work. Other states route through workflow-start.

## New direct/planned changes

Use `SSF workflow complete <dir> --verification-command "<required check command>"`. It runs final verification once; do not run the identical full suite immediately before invoking it. Planned execution additionally checks completed tasks, current full-range/wave review and any delta-spec publication. Direct execution needs no plan or review receipt. Ordinary failures stay in executing for focused repair. Reuse authorization already covering code delivery.

If the user explicitly accepts unfinished work or failed verification, use `SSF workflow complete <dir> --accept-risk --confirm --reason "<decision and remaining issues>"`. Preserve every failure and report accepted-risk, not verified success. This ends code delivery without merging or deleting the branch. A plain closing transition cannot bypass failed checks. For verified work, physical integration remains a separate authorized operation.

## Physical finish and delivery

Logical closure does not claim merge or cleanup succeeded. For verified changes with recorded isolation and authorized integration, use `SSF finish <dir> [--test-cmd <command>]`. It verifies the recorded target and preserves isolation on failure. Cleanup failure remains cleanup-pending. Resume only the recorded pending operation; do not guess the target or reopen completed work.

For branch delivery, leave the branch/worktree intact. Report outcome, key verification, unresolved risks and integration status. Logical closure does not authorize merge, push or release; accepted-risk delivery is not eligible for physical integration.
