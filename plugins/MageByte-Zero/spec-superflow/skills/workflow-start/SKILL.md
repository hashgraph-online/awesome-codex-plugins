---
name: workflow-start
description: Primary entry point for the spec-superflow state-machine workflow. Invoke only when the user explicitly requests spec-superflow or an active change contains .spec-superflow.yaml and the user asks to continue that change. Generic proposal, specs, design, task, or contract files are not activation signals.
---

# Workflow Start

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

## Workflow routing

A new request follows this file without loading legacy instructions. For an existing change, inspect the recorded state and receipt/plan (available through `SSF workflow show <change-dir> --json` and `SSF execution show <dir> --json` when needed). Current paths are `workflow_variant: direct` with a valid workflow-selection receipt `schema_version: 3`, or `workflow_variant: planned` with an execution plan `schema_version: 2`. Older receipts (schema 1/2), legacy plans and other recorded variants use the matching section of `SSF runtime asset read docs/legacy-workflow.md`; follow that section for this change. A direct variant alone is insufficient: legacy Quick/Hotfix/Lightweight can also record it. The internal `workflow: full` value alone is not a legacy signal. Missing or corrupt state, receipt or a required plan is a recovery problem; preserve evidence rather than reinitialize or downgrade the change.

Use only for an explicit spec-superflow request or an existing change. Ordinary coding does not require a spec workflow.

## Resume

Run `SSF resume <change-dir> --json` once. It combines state, handoffs, checkpoints and current-plan inspection. Use the returned absolute `change.path` for all subsequent operations: recovery may redirect a stale source copy into its recorded worktree. Follow `next_action`; do not repeat all component commands unless diagnosing that result. A blocked continuation is not a retry instruction; resolve its named cause before running it again. Read only the artifacts relevant to the next action.

- `debugging`: diagnose first, even if a plan is stale. Never dispatch an eligible wave during diagnosis.
- `closing`: logical completion. If a recorded isolation still has physical finish pending, route to release-archivist for that remaining action, subject to existing merge authorization. Otherwise stop.
- `abandoned`: stop.
- A ready handoff needs review through `SSF handoff resolve`; an active handoff is non-blocking. Stale checkpoints are history, not current evidence.
- A missing/stale planned execution plan blocks implementation, not investigation. Direct changes do not require a plan.

Update checks are optional (`SSF runtime check-update`), cached and non-blocking. Never make network access a recovery prerequisite.

## New request

Infer scope and risks from the request and repository; do not turn CLI fields into a questionnaire. Validate the change name as a single safe relative path segment under `changes/` and create only that directory. Reuse authorization already given. Never infer approval from artifact existence.

Offer only two paths, without a mode-selection interview:

- **Direct**: clear requested change with a bounded proof. In the same turn run `SSF workflow start <dir> --path direct --scope "<requested outcome and bounds>"`. No planning pack, recommendation receipt or execution plan is needed. Use affected tests or checks; `--verification` can record tdd/new-test/bounded when relevant. Task/file counts are advisory, not hard limits.
- **Planned**: uncertain behavior, architecture or a user-requested plan. Draft proposal.md (scope, acceptance, risks) and tasks.md (ordered tasks and proof) together. Add specs/design only when their information is needed. Check shared interfaces against actual code once. Present one concrete plan for approval, reusing approval already covering it. Then run `SSF workflow start <dir> --path planned --confirm --reason "<existing approval>"`. The CLI derives the execution plan and enters executing; no handwritten contract or intermediate approval sequence is required. Native + final is the default; add `--mode sdd` only for explicit delegation.

Continue to build-executor without another question. Ordinary debugging stays in executing. Scope changes update the affected planning sections and repeat planned start once with actual reapproval; do not traverse intermediate states. Nonsemantic corrections can use execution resync with a recorded reason, retaining review history.

Completion uses `SSF workflow complete <dir> --verification-command "<required check command>"`. It runs the check once and preserves failures. Planned work also requires its current review and completed tasks; existing delta specs require synchronization. A user can explicitly accept known risks with `workflow complete --accept-risk --confirm --reason "<decision and remaining issues>"`; this records accepted-risk, never pass, and does not authorize integration.

Continue authorized internal work without phase-by-phase handoff questions. For all paths, read only the current task's source and evidence. Progress updates use one short paragraph; ask only for a new material decision, never “continue?” for authorized work.
