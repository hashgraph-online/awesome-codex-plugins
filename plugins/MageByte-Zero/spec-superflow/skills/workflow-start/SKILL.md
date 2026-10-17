---
name: workflow-start
description: Primary entry point for the spec-superflow state-machine workflow. Invoke only when the user explicitly requests spec-superflow or an active change contains .spec-superflow.yaml and the user asks to continue that change. Generic proposal, specs, design, task, or contract files are not activation signals.
---

# Workflow Start

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

Use only for an explicit spec-superflow request or an existing change. Ordinary coding does not require a spec workflow.

## Resume

Run `SSF resume <change-dir> --json` once. It combines state, handoffs, checkpoints and current-plan inspection. Use the returned absolute `change.path` for all subsequent operations: recovery may redirect a stale source copy into its recorded worktree. Follow `next_action`; do not repeat all component commands unless diagnosing that result. A blocked continuation is not a retry instruction; resolve its named cause before running it again. Read only the artifacts relevant to the next action.

- `debugging`: diagnose first, even if a plan is stale. Never dispatch an eligible wave during diagnosis.
- `closing`: logical completion. If a recorded isolation still has physical finish pending, route to release-archivist for that remaining action, subject to existing merge authorization. Otherwise stop.
- `abandoned`: stop.
- A ready handoff needs review through `SSF handoff resolve`; an active handoff is non-blocking. Stale checkpoints are history, not current evidence.
- Missing/stale Full plans block implementation, not investigation. Valid short paths and Tweak do not require plans.

Update checks are optional (`SSF runtime check-update`), cached and non-blocking. Never make network access a recovery prerequisite.

## New request

Infer scope and risks from the request and repository; do not turn CLI fields into a questionnaire. Validate the change name as a single safe relative path segment under `changes/` and create only that directory. Reuse authorization already given. Never infer approval from artifact existence.

Offer only two paths, without a mode-selection interview:

- **Direct**: clear requested change with a bounded proof. In the same turn run `SSF workflow start <dir> --path direct --scope "<requested outcome and bounds>"`. No planning pack, recommendation receipt or execution plan is needed. Use affected tests or checks; `--verification` can record tdd/new-test/bounded when relevant. Task/file counts are advisory, not hard limits.
- **Planned**: uncertain behavior, architecture or a user-requested plan. Draft proposal.md (scope, acceptance, risks) and tasks.md (ordered tasks and proof) together. Add specs/design only when their information is needed. Check shared interfaces against actual code once. Present one concrete plan for approval, reusing approval already covering it. Then run `SSF workflow start <dir> --path planned --confirm --reason "<existing approval>"`. The CLI derives the execution plan and enters executing; no contract-builder, handwritten contract, DP-0..DP-4 sequence or execution recommend is required. Native + final is the default; add `--mode sdd` only for explicit delegation.

Continue to build-executor without another question. Ordinary debugging stays in executing. Scope changes update the affected planning sections and repeat planned start once with actual reapproval; do not traverse intermediate states. Nonsemantic corrections can use execution resync with a recorded reason, retaining review history.

Completion uses `SSF workflow complete <dir> --verification-command "<required check command>"`. It runs the check once and preserves failures. Planned work also requires its current review and completed tasks; existing delta specs require synchronization. A user can explicitly accept known risks with `workflow complete --accept-risk --confirm --reason "<decision and remaining issues>"`; this records accepted-risk, never pass, and does not authorize integration.

## Legacy changes

Do not convert an active legacy change or discard its receipts automatically. Resume its recorded obligations: Full/legacy Hotfix may still need contract-builder and old approval/review gates; old Quick/Tweak/Lightweight/direct Hotfix use their existing receipts. Read docs/decision-points.md only for the applicable old decision, not for every task. Use `SSF runtime asset read docs/state-machine.md` only when a legacy transition is unclear. Legacy `SSF state init` precedes `SSF workflow recommend`; a nonrecommended choice requires acknowledgment. Legacy Quick/direct Hotfix use `workflow accept --verification` and persist `test_result: pass` before closing; use `SSF state set <change-dir> dp_0_timestamp now` for portable timestamps.

Continue authorized internal work without phase-by-phase handoff questions. For all paths, read only the current task's source and evidence. Progress updates use one short paragraph; ask only for a new material decision, never “continue?” for authorized work.
