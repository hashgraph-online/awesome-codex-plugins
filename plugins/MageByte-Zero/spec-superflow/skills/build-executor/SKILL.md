---
name: build-executor
description: Execute an active direct request or approved planned change. Native continuous implementation is the default; existing legacy changes retain their recorded contract obligations.
---

# Build Executor

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

## Workflow routing

A new request follows this file without loading legacy instructions. For an existing change, inspect the recorded state and receipt/plan (available through `SSF workflow show <change-dir> --json` and `SSF execution show <dir> --json` when needed). Current paths are `workflow_variant: direct` with a valid workflow-selection receipt `schema_version: 3`, or `workflow_variant: planned` with an execution plan `schema_version: 2`. Older receipts (schema 1/2), legacy plans and other recorded variants use the matching section of `SSF runtime asset read docs/legacy-workflow.md`; follow that section for this change. A direct variant alone is insufficient: legacy Quick/Hotfix/Lightweight can also record it. The internal `workflow: full` value alone is not a legacy signal. Missing or corrupt state, receipt or a required plan is a recovery problem; preserve evidence rather than reinitialize or downgrade the change.

For planned execution, read the generated execution plan and current task; approval is already in the plan. Run `SSF isolate <change-dir>` before code edits, defaulting to a feature branch, and use its returned checkout path. Preserve existing isolation; diagnose failures before editing a protected branch. Create a worktree only when explicitly selected. Direct execution reads its bounded request receipt and does not require a plan or isolation.

## Native first

Native means the current agent implements continuously; persisted mode is `inline`. Task count, file count and number of waves do not justify delegation. `batch-inline` remains compatible serial execution. Select SDD only when the user explicitly chooses delegation for this change and independently scoped work has a concrete benefit. Tool availability, many tasks, a long context, or generic implementation approval never authorize subagents. This includes reviewer and exploratory subagents.

Reuse the user's existing mode choice. New Native plans default to `final` review; SDD defaults to `wave`. `--review-policy wave` is available for explicit risk boundaries.  Mode and review granularity are separate.

Use `SSF execution show <dir> --json` to resolve uncertainty, interruptions and repair status, not as a ritual before every edit. A Native wave's dependencies are completed tasks; checked tasks never substitute for the final whole-range review.

## One bounded preflight

Before the first edit, inspect only shared producer/consumer interfaces and the test entry points the approved tasks depend on. Check that named symbols, payload fields and acceptance tests can be located. Record mismatches in the existing progress entry; resolve implementation details within approved behavior. Ask only when resolving a mismatch changes behavior, scope, permissions or external effects. Do not dispatch an exploration agent or create another planning pack for this check.

## Implementation loop

1. Implement tasks in dependency order. Use a failing behavioral regression for behavior changes, confirm RED, make the minimal fix, then confirm GREEN. Documentation changes use format/link/build checks instead of invented unit tests.
2. Run affected tests per task, integration tests at meaningful boundaries, and the required complete checks once at the final code snapshot. Reuse a result only when code, environment and command match; changes invalidate affected evidence.
3. Mark completed tasks and append a brief progress entry: outcome, files/commit, verification, next action, unresolved risk. Do not create a task book, delivery report and checkpoint for every small task. Save `SSF checkpoint save` when interruption or long-running work needs recovery.
4. Continue without requesting permission between authorized tasks. A pending task or review is not a reason to end the controller turn. Reuse existing authorizations; never ask “continue?” for the next authorized task. Give concise progress commentary; do not promise autonomous background execution.

For new direct/planned changes, diagnose an ordinary defect in executing: reproduce, trace the cause, repair and verify. Do not create another state transition, task report or debug ledger. Escalate only when the same issue remains unresolved without a new useful approach. Expected RED is test evidence, not an unexpected defect. Scope changes update the plan and require approval of the changed scope through workflow-start; ordinary repair stays in executing.

Read `SSF runtime asset read skills/build-executor/writing-good-tests.md` when selecting uncertain test evidence.

## Reviews

Direct changes use their receipt's bounded checks and proceed to release-archivist without a plan or review receipt. The review policies below apply to planned execution.

For Native `final`, the current executor performs one whole-range review after implementation and required tests, covering spec compliance and code quality. Do not start a reviewer subagent. Commit the code and bind the report to its actual Git range. Record through:

```bash
SSF execution review <dir> --wave final --base <base-sha> --head <head-sha> --report .superpowers/sdd/reviews/final.md --verdict <pass|fail>
```

For `wave`, review once per planned wave, using its ID instead of `final`; dependencies require a current passing receipt. SDD may use one reviewer subagent per wave because the user authorized delegation. Do not add per-task and final duplicates. Critical/Important findings require fail → focused repair → one focused re-review → pass.

Read the CLI repair status before a retry. Never edit repair-state files. In new plans, record a stable `--issue <finding-id>` on failed reviews and keep that ID for the same unresolved defect. Three failures for that issue require human adjudication; different findings do not share the budget. After adjudication, `SSF execution adjudicate <dir> --wave <id> --decision allow-review --confirm --reason <text>` records permission for one further review, never a pass. Preserve the prior review head so repair ranges remain continuous. For a final review, re-review the original complete range plus fixes when needed to certify the final snapshot.

## Optional SDD

Only load dispatch material when SDD is selected. Load the reviewer prompt only when a wave reaches review:

- `SSF runtime asset read skills/build-executor/implementer-prompt.md`
- `SSF runtime asset read skills/code-reviewer/code-reviewer-prompt.md`

Send only the task's objective, bounded files, interfaces, relevant requirement IDs and test command. Reuse an implementer for its focused repair; no nested delegation or repeated full planning packs. Batch closely related small tasks. Dispatch concurrently only for independent work with platform support; otherwise report the limitation and execute serially.

Profiles: `mechanical`, `standard`, `strong`, `review`. Resolve `SSF runtime config --resolve-model <profile>` once per role. Pass the configured model if supported. With `configured: false`, inherit the host model; do not invent a model or block execution. Retry blocked work only with new evidence, context or strategy; escalate when the same issue remains unresolved without a new useful approach.

## Plan correction and completion

Nonsemantic planning corrections use `SSF execution resync <dir> --confirm --reason <text>`, retaining review and failure history. Semantic changes return to workflow-start for approval of the concrete revised plan; never infer approval from changed files.

Before completion, satisfy tasks, the current review policy and any delta-spec synchronization. Use workflow complete with the final verification command through release-archivist. Merge, push or publication require their own existing authorization.
