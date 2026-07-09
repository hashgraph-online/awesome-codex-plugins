---
name: build-executor
description: Govern implementation from an approved execution contract. Invoke when execution-contract.md is approved and the user wants disciplined build work, TDD execution, or guarded batch-by-batch implementation.
---

# Build Executor

Controls the implementation phase. Uses `execution-contract.md` as the workflow authority.

## Required Inputs

Read: `execution-contract.md`, `tasks.md`, relevant `specs/`, relevant `design.md`. (Skip contract/spec requirements when workflow is `tweak`.)

Check workflow mode first: `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state get <change-dir> workflow`. If `tweak` → direct edit mode. If `hotfix` or `full` → standard contract-first discipline.

Config check: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/get-config" execution.inlineThreshold` (default: 3).

Branch/worktree preflight before ANY implementation edit (mandatory — do not skip):
1. Run the isolation check:
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" isolate <change-dir>
   ```
   This script enforces git isolation: if you are on `main`/`master` it creates a
   git worktree (preferred) or a new branch, and exits non-zero if it cannot and you
   have not approved `--force`.
2. If `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" isolate` exits non-zero: STOP. Do not edit `main`/`master` in place.
   Ask the user for explicit approval (and re-run with `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" isolate <change-dir> --force`
   only after they approve).
3. If it succeeds, report the chosen branch/worktree and make all implementation
   edits there.

## Core Laws

### Law 1: Contract First
The execution contract is the approved handoff artifact, not chat history.

### Law 2: TDD Iron Law — No Production Code Without a Failing Test First
RED (write test, see it fail) → GREEN (write minimal code, see it pass) → REFACTOR (clean up, suite stays green).

**Red Flags**: "Quick implementation first, test later" / "Skip the test, manually verify" / "I already know it works" / "Just this one time without tests." ALL mean STOP and write the test first.

### Law 3: Review Before Drift
Block on: logic defects, spec violations, missing required tests, unintended scope expansion.

### Law 4: Rewind on Contract Break
Return to `specifying` or `bridging` if: new behavior appears, interfaces change materially, design assumptions fail, artifacts no longer define intended implementation.

## Execution Mode Selection

Auto-selection based on: task count, cross-module dependencies, risk indicators (new API/schema/config, open questions, unimplemented dependencies).

| Mode | Criteria |
|------|----------|
| **Inline** | ≤3 tasks, no cross-module deps |
| **Batch Inline** | >3 tasks, same module, no risk indicators, ≤15 min effort |
| **SDD** (default) | Everything else |

Report mode + reasoning before executing. User can override: "use SDD", "use inline", or "use batch inline".

## Batch Inline Execution

For low-risk, same-module tasks. Current agent executes directly. TDD Iron Law still applies.

Procedure: announce mode → write failing test → confirm failure → implement → run suite → refactor → lightweight checkpoint (files exist, no placeholders, test passed, no unintended changes) → report.

Boundaries: if any task touches >1 module, involves schema/API/config changes, or has open questions → downgrade to Inline or SDD.

## SDD Workflow

For changes with multiple execution batches. Dispatch implementer subagent per task, review each task, final broad review after all batches.

### Per-Task Loop
1. **Dispatch implementer**: Use `${CLAUDE_PLUGIN_ROOT}/skills/build-executor/implementer-prompt.md` template. Extract task brief with `scripts/task-brief PLAN_FILE N`. Include: where task fits, brief path, interfaces from prior tasks, report file path.
2. **Handle response**: DONE → generate review package + dispatch reviewer. DONE_WITH_CONCERNS → assess. NEEDS_CONTEXT → provide context. BLOCKED → re-dispatch with better model or escalate.
3. **Review**: Use `skills/build-executor/task-reviewer-prompt.md`. Reviewer returns spec compliance + code quality verdicts.
4. **Fix**: If Critical or Important issues, dispatch fix subagent, re-review.
5. **Mark complete**: Append to `.superpowers/sdd/progress.md`: `Task N: complete (commits <base7>..<head7>, review clean)`

### Model Selection
Use least powerful model per role: mechanical (cheap), integration/judgment (standard), architecture/design (most capable), review (match diff), final review (most capable). Always specify model explicitly.

### Progress Ledger
Track in `.superpowers/sdd/progress.md`. Check for existing ledger — completed tasks are done. After each batch: `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> batches_completed <N>`.

## Inline Execution Mode

For ≤3 tasks, no cross-module deps. Executes in current session.

Per-task: extract brief → write failing test → confirm failure → implement → confirm green → checkpoint review (done-when criteria, SHALL/MUST verification) → commit → append to progress ledger.

If task hits BLOCKED (3+ fix failures or changes outside declared scope), escalate to SDD.

## Tweak Mode

Skip TDD. Apply changes directly. Verify file integrity (exists, non-empty, valid syntax). No batch execution — sequential changes.

## DP Records

DP-4 (execution mode): `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_4_result "<mode>: <rationale>"` + timestamp.
DP-5 (debug escalation): `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_5_result "<resolution>"` + timestamp.

## Completion Standard

Don't report completion until: tests pass, contract obligations satisfied, review blockers resolved, all batches reviewed (per-task + final), workflow ready for `release-archivist`.

## Exception Handling

- **Parse failures**: Stop and report exact line/format issue. Route back to `contract-builder`.
- **Missing artifacts**: Route back to appropriate upstream skill. Don't guess.
- **User interruption**: Progress ledger enables recovery. Check ledger on resume.
