---
name: release-archivist
description: Close out a spec-superflow change with verification, summary, and archive readiness. Invoke when implementation is complete, verification is underway, or the user asks for a final wrap-up.
---

# Release Archivist

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

Read `SSF resume <change-dir> --json`. In `executing`, complete verification and logical closure. In `closing`, perform only recorded pending physical finish, if merging is authorized. `abandoned` or a completed finish requires no work. Other states route through workflow-start.

## New direct/planned changes

Use `SSF workflow complete <dir> --verification-command "<required check command>"`. It runs final verification once; do not run the identical full suite immediately before invoking it. Planned execution additionally checks completed tasks, current full-range/wave review and any delta-spec publication. Direct execution needs no plan or review receipt. Ordinary failures stay in executing for focused repair. Do not add DP-6/DP-7 or another approval to authorized code delivery.

If the user explicitly accepts unfinished work or failed verification, use `SSF workflow complete <dir> --accept-risk --confirm --reason "<decision and remaining issues>"`. Preserve every failure and report accepted-risk, not verified success. This ends code delivery without merging or deleting the branch. A plain closing transition cannot bypass failed checks. For verified work, physical integration remains a separate authorized operation. The remaining closure steps are legacy compatibility.

## Bounded paths

Quick/direct Hotfix/Tweak record changed files, focused command and result, persist `test_result: pass`, then transition to closing. Hotfix must prove the original symptom fixed. Lightweight also needs its receipt's focused review and passing verification evidence. These paths require no contract, execution plan, wave reviews, audit, DP-6/DP-7 or `SSF finish`.

## Full / legacy Hotfix

1. Verify the final code snapshot with required build/test/validation commands. Reuse fresh results only when the code, environment and command are identical; don't rerun the same full suite just because the skill changed.
2. Check contract coverage, design consistency, scope and unresolved findings against the actual diff. Cite commands/results; do not infer success from edits or unchecked claims.
3. Require the current plan's review policy: one final whole-range review for Native `final`, or the required wave receipts for `wave`/legacy plans. Do not request a duplicate review of unchanged evidence.
4. Synchronize actual delta specs using spec-merger while executing. If specs were explicitly omitted and no delta exists, don't recreate them.
5. Run `SSF audit <dir>` and record verification outcome (`dp_6_result`, timestamp and `test_result`). Record DP-7 only with the user's archive authorization already obtained or explicitly requested. Do not fabricate missing decisions.
6. With blockers resolved, run `SSF state transition <dir> closing`. This is logical closure; it does not claim merge or cleanup succeeded.

Report only the outcome, key verification, unresolved risks and next action. Preserve the approved contract and implementation evidence; don't copy all planning files into a second summary.

## Physical finish

For authorized Full/legacy Hotfix integration, run `SSF finish <dir> [--test-cmd <command>]`. It uses recorded target checkout/branch, merges if necessary, verifies the target, and safely removes isolation. It verifies an archive of ignored change artifacts and preserves the previous target before cleanup. It never force-removes uncommitted work. Branch-only isolation never deletes the checkout.

Verification failure preserves isolation. For recorded `verify-pending`, recovery offers the guarded `closing -> debugging` transition; diagnose, repair within approved scope, reverify and review before closing again. Completed finish and abandoned changes cannot reopen. Cleanup failure remains cleanup-pending. Resume performs the remaining steps; each unfinished finish retry verifies once again because ignored dependencies, local configuration and external services may have changed even at the same HEAD. Completed finish does not rerun verification. Completed finish is idempotent. A missing or ambiguous target is a real blocker: recover provenance before merging, never guess the target from the current directory.

If the user requested branch delivery without merging, leave the branch/worktree intact and report that status. Do not treat logical closure as permission to merge, push or release.

Use `SSF state set <change-dir> dp_6_timestamp now` and `SSF state set <change-dir> dp_7_timestamp now` when recording those decisions.
