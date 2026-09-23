---
name: build-executor
description: Execute an active direct request or approved planned change. Native continuous implementation is the default; existing legacy changes retain their recorded contract obligations.
---

# Build Executor

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

For workflow_variant planned, read the generated execution plan and current task only; approval is already in the plan. Run `SSF isolate <change-dir>` before code edits, defaulting to a feature branch. No contract, recommendation or DP-4 is required. For other paths read the workflow receipt first. Full/legacy Hotfix require the approved execution contract; read linked requirements/design only for the current task. Quick/direct Hotfix/Tweak use their bounded request and verification strategy. Lightweight follows its receipt's focused review and verification requirements.

## Preflight

Legacy Full/Hotfix run `SSF isolate <change-dir>` before edits and use the returned absolute checkout path for every command. The default is a feature branch in the current checkout; create a worktree only when the user explicitly selects `--worktree`. Failure blocks edits in protected branches; preserve an existing isolation and diagnose initialization failures. Direct paths do not require isolation or physical finish.

For legacy Full, honor DP-3 approval. When the record is missing but the user explicitly approved this exact contract in the conversation, persist that existing decision and continue. Never infer approval of unseen or changed behavior, or request the same unchanged approval again. Enter `executing` only with a current plan and passing guard; skip the transition if already executing.

## Native first

Native means the current agent implements continuously; persisted mode is `inline`. Task count, file count and number of waves do not justify delegation. `batch-inline` remains compatible serial execution. Select SDD only when the user explicitly chooses delegation for this change and independently scoped work has a concrete benefit. Tool availability, many tasks, a long context, or generic implementation approval never authorize subagents. This includes reviewer and exploratory subagents.

For legacy plans only (new planned changes already have their plan):

```bash
SSF execution recommend <dir> --wave <id>:serial:<task,...>[:<dependencies>] --json
SSF execution plan <dir> --mode inline --review-policy final --confirm --reason "<authorized choice>" --wave <id>:serial:<task,...>[:<dependencies>]
```

Reuse the user's existing mode choice. For a nonrecommended choice add `--acknowledge-recommendation`. New Native plans default to `final` review; SDD defaults to `wave`. `--review-policy wave` is available for explicit risk boundaries. Old plans with no policy retain wave review obligations. Mode and review granularity are separate.

Use `SSF execution show <dir> --json` to resolve uncertainty, interruptions and repair status, not as a ritual before every edit. A Native wave's dependencies are completed tasks; checked tasks never substitute for the final whole-range review.

## One bounded preflight

Before the first edit, inspect only shared producer/consumer interfaces and the test entry points the approved tasks depend on. Check that named symbols, payload fields and acceptance tests can be located. Record mismatches in the existing progress entry; resolve implementation details within approved behavior. Ask only when resolving a mismatch changes behavior, scope, permissions or external effects. Do not dispatch an exploration agent or create another planning pack for this check.

## Implementation loop

1. Implement tasks in dependency order. Full/legacy Hotfix use a failing behavioral regression, confirm RED, make the minimal fix, then confirm GREEN. Documentation changes use format/link/build checks instead of invented unit tests.
2. Run affected tests per task, integration tests at meaningful boundaries, and the required complete checks once at the final code snapshot. Reuse a result only when code, environment and command match; changes invalidate affected evidence.
3. Mark completed tasks and append a brief progress entry: outcome, files/commit, verification, next action, unresolved risk. Do not create a task book, delivery report and checkpoint for every small task. Save `SSF checkpoint save` when interruption or long-running work needs recovery.
4. Continue without requesting permission between authorized tasks. A pending task or review is not a reason to end the controller turn. Reuse existing authorizations; never ask “continue?” for the next authorized task. Give concise progress commentary; do not promise autonomous background execution.

For new direct/planned changes, diagnose an ordinary defect in executing: reproduce, trace the cause, repair and verify. Do not create another state transition, task report or debug ledger. Escalate only when the same issue remains unresolved without a new useful approach. Existing legacy changes may enter `debugging` and use bug-investigator. Expected RED is test evidence, not an unexpected defect. Scope changes rewind Full to specifying; contract drift to bridging. Short paths refresh their risk receipt instead of inventing a contract.

Read `SSF runtime asset read skills/build-executor/writing-good-tests.md` when selecting uncertain test evidence.

## Reviews

For Native `final`, the current executor performs one whole-range review after implementation and required tests, covering spec compliance and code quality. Do not start a reviewer subagent. Commit the code and bind the report to its actual Git range. Record through:

```bash
SSF execution review <dir> --wave final --base <base-sha> --head <head-sha> --report .superpowers/sdd/reviews/final.md --verdict <pass|fail>
```

For `wave`, review once per planned wave, using its ID instead of `final`; dependencies require a current passing receipt. SDD may use one reviewer subagent per wave because the user authorized delegation. Do not add per-task and final duplicates. Critical/Important findings require fail → focused repair → one focused re-review → pass.

Read the CLI repair status before a retry. Never edit repair-state files. In new plans, record a stable `--issue <finding-id>` on failed reviews and keep that ID for the same unresolved defect. Three failures for that issue require human adjudication; different findings do not share the budget. Legacy plans retain their recorded aggregate budget; `SSF execution adjudicate <dir> --wave <id> --decision allow-review --confirm --reason <text>` authorizes one further review, never a pass. Preserve the prior review head so repair ranges remain continuous. For a final review, re-review the original complete range plus fixes when needed to certify the final snapshot.

## Optional SDD

Only load dispatch material when SDD is selected. Load the reviewer prompt only when a wave reaches review:

- `SSF runtime asset read skills/build-executor/implementer-prompt.md`
- `SSF runtime asset read skills/code-reviewer/code-reviewer-prompt.md`

Send only the task's objective, bounded files, interfaces, relevant requirement IDs and test command. Reuse an implementer for its focused repair; no nested delegation or repeated full planning packs. Batch closely related small tasks. Dispatch concurrently only for independent work with platform support; otherwise report the limitation and execute serially.

Profiles: `mechanical`, `standard`, `strong`, `review`. Resolve `SSF runtime config --resolve-model <profile>` once per role. Pass the configured model if supported. With `configured: false`, inherit the host model; do not invent a model or block execution. Retry blocked work only with new evidence, context or strategy; after three unresolved attempts use DP-5.

## Plan correction and completion

Nonsemantic planning corrections use `SSF execution resync <dir> --confirm --reason <text>`, including during an open repair chain; history and failure counts remain binding. Semantic scope changes require reapproval and `execution revise`. Revisions may retain or change the authorized mode. Old receipts remain history and do not automatically certify changed scope or a new final snapshot.

Before completion, satisfy contract obligations, tests and the plan's review policy. Record `batches_completed` when useful. For new direct/planned changes use workflow complete with the final verification command; for legacy changes route to release-archivist. Merge, push or publication require their own existing authorization.

Quick/direct Hotfix persist `test_result: pass` after bounded verification; Hotfix must demonstrate the original symptom is fixed. Tweak verifies file integrity. They do not require DP-4, execution plans, wave receipts, DP-6 or DP-7. Lightweight additionally persists the focused review and passing command required by its receipt.

Quick follows the verification strategy persisted in its receipt. Tweak skips TDD. Full and legacy Hotfix use RED → GREEN → REFACTOR.
