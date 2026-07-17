---
name: build-executor
description: Govern implementation from an approved execution contract. Invoke when execution-contract.md is approved and the user wants disciplined build work, TDD execution, or guarded batch-by-batch implementation.
---

# Build Executor

Controls the implementation phase. Uses `execution-contract.md` as the workflow authority.

## Required Inputs

Read: `execution-contract.md`, `tasks.md`, relevant `specs/`, relevant `design.md`. (Skip contract/spec requirements when workflow is `tweak`.)

Check workflow mode first: `npx --yes --package spec-superflow@0.10.0 ssf state get <change-dir> workflow`. If `tweak` → direct edit mode. If `hotfix` or `full` → standard contract-first discipline.

Branch/worktree preflight before ANY implementation edit (mandatory — do not skip):
1. Run the isolation check:
   ```bash
   npx --yes --package spec-superflow@0.10.0 ssf isolate <change-dir>
   ```
   This script enforces git isolation: if you are on `main`/`master` it creates a
   git worktree (preferred) or a new branch, and exits non-zero if it cannot and you
   have not approved `--force`.
2. If `npx --yes --package spec-superflow@0.10.0 ssf isolate` exits non-zero: STOP. Do not edit `main`/`master` in place.
   Ask the user for explicit approval (and re-run with `npx --yes --package spec-superflow@0.10.0 ssf isolate <change-dir> --force`
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

For `full`/`hotfix`, generate proposed waves from the approved contract, then use the recommendation as a decision aid rather than silently defaulting a mode:

```bash
npx --yes --package spec-superflow@0.10.0 ssf execution recommend <change-dir> \
  --wave <wave-id>:<parallel|serial>:<task,...>[:<depends-on,...>] --json
# Show every available mode, the observed facts, and the recommendation to the user.
# The command writes a receipt tied to the artifacts, contract, and waves. After the user chooses, record that explicit confirmation:
npx --yes --package spec-superflow@0.10.0 ssf execution plan <change-dir> \
  --mode <selected-mode> --confirm --reason "user-selected execution mode" \
  --wave <wave-id>:<parallel|serial>:<task,...>[:<depends-on,...>]
# Add --acknowledge-recommendation when the selection differs from the recommendation.
npx --yes --package spec-superflow@0.10.0 ssf execution show <change-dir> --json
```

The optional fourth `--wave` segment names prerequisite wave IDs. `execution show --json` reports `current`, plus each wave's `depends_on`, `receipt`, `blockers`, `retryable`, and `eligible` status. A wave with `retryable: true` has a current `fail` receipt and is eligible only for its focused repair and re-review; its dependents remain blocked until its replacement `pass` receipt. Report the saved plan revision, selected mode, ordered waves, dependencies, and whether every `parallel` wave can actually be dispatched concurrently on the current platform. If concurrency is unavailable, state the capability and reason plainly; retain the planned `parallel` strategy and do not silently execute it as a serial or Batch Inline plan.

The recommendation uses task count, configured `execution.inlineThreshold`, and declared wave strategy. It never auto-selects: present every available mode and the recommendation to the user. `--confirm` records any user-selected mode; a choice that differs from the recommendation requires `--acknowledge-recommendation` so the plan captures an informed risk decision.

| Mode | Criteria |
|------|----------|
| **SDD** | Recommended for parallel waves, multiple waves, or work beyond the inline threshold |
| **Inline** | Recommended for a single sequential task; always available for a user-confirmed choice |
| **Batch Inline** | Recommended for a bounded sequential batch; it remains serial and is never presented as parallel |

Do not transition to `executing` until `execution show` reports `current: true` and the phase guard passes. A revised plan must repeat `npx --yes --package spec-superflow@0.10.0 ssf execution recommend` and use `npx --yes --package spec-superflow@0.10.0 ssf execution revise --confirm`; it creates a new revision and invalidates receipts from the prior revision.

## Batch Inline Execution

Only when the user explicitly confirms `batch-inline` after seeing the recommendation. Current agent executes directly and serially. TDD Iron Law still applies.

Procedure: announce mode → write failing test → confirm failure → implement → run suite → refactor → lightweight checkpoint (files exist, no placeholders, test passed, no unintended changes) → report.

Boundaries: if any task touches >1 module, involves schema/API/config changes, or has open questions → downgrade to Inline or SDD.

## SDD Workflow

For full/hotfix by default. Dispatch according to the persisted plan, review each planned wave, and run a final broad review after all waves.

### Planned-Wave Loop
1. Read the current plan with `npx --yes --package spec-superflow@0.10.0 ssf execution show <change-dir> --json`; only waves shown with `current: true` and `eligible: true` may start. A `retryable: true` wave may only be repaired and re-reviewed; do not dispatch its dependents until its replacement receipt is `pass`. The CLI encodes dependencies in `--wave <id>:<strategy>:<tasks>[:<depends-on,...>]` and rejects a review receipt for a wave whose prerequisites lack current `pass` receipts.
2. A `parallel` wave may dispatch independent tasks simultaneously only when the platform supports concurrent dispatch. If it does not, disclose the unavailable capability and execute the same wave one task at a time without changing its stored strategy.
3. A `serial` wave dispatches one task at a time in listed order.
4. After every wave, write a non-empty persisted regular-file review report (separate from the implementer's report), then record exactly one receipt that names that review report:
   ```bash
   npx --yes --package spec-superflow@0.10.0 ssf execution review <change-dir> \
     --wave <wave-id> --base <sha> --head <sha> --report <review-report-path> --verdict <pass|fail>
   ```
   Do not begin a dependent wave until its predecessor receipt is `pass`.
5. Critical/Important findings require a `fail` receipt, a focused repair, re-review, then a replacement `pass` receipt. Never advance or close with a missing or failed receipt.

### Per-Task Loop
1. **Dispatch implementer**: Load the template with `npx --yes --package spec-superflow@0.10.0 ssf runtime asset read skills/build-executor/implementer-prompt.md`. Extract task brief with `scripts/task-brief PLAN_FILE N`. Include: where task fits, brief path, interfaces from prior tasks, report file path.
2. **Handle response**: DONE → generate review package + dispatch reviewer. DONE_WITH_CONCERNS → assess. NEEDS_CONTEXT → provide context. BLOCKED → re-dispatch with better model or escalate.
3. **Review**: Load `npx --yes --package spec-superflow@0.10.0 ssf runtime asset read skills/build-executor/task-reviewer-prompt.md`. Reviewer returns spec compliance + code quality verdicts with the wave ID, git range, report path, and `pass`/`fail` receipt command.
4. **Fix**: If Critical or Important issues, write the `fail` receipt, dispatch fix subagent, re-review, and write the replacement `pass` receipt.
5. **Mark complete**: Append to `.superpowers/sdd/progress.md`: `Task N: complete (commits <base7>..<head7>, review clean)`

### Model Selection
Use the configured profile that matches the task role. Resolve it before dispatch:

```bash
npx --yes --package spec-superflow@0.10.0 ssf runtime config --resolve-model <profile>
```

| Profile | Role |
|---|---|
| `mechanical` | Cheap, routine edits |
| `standard` | Integration and judgment work |
| `strong` | Architecture, design, and final review |
| `review` | Review that matches the diff |

For platforms whose dispatch supports a `model` field, explicitly pass the resolved `model` value. If the result is `configured: false`, automatic selection is unavailable: do not invent a provider model and do not bypass the existing requirement to specify `model` explicitly. Resolution only reads configuration; it does not switch models.

### Progress Ledger
Track in `.superpowers/sdd/progress.md`. Check for existing ledger — completed tasks are done. After each batch: `npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> batches_completed <N>`.

## Inline Execution Mode

Only after a user-confirmed `inline` selection is recorded by `npx --yes --package spec-superflow@0.10.0 ssf execution plan --confirm`; a non-recommended selection also records `--acknowledge-recommendation`. Executes in the current session and still writes one review receipt per planned wave.

Per-task: extract brief → write failing test → confirm failure → implement → confirm green → checkpoint review (done-when criteria, SHALL/MUST verification) → commit → save a task-level recovery checkpoint when another task remains → append to progress ledger.

After a task is committed and reviewed, when another task remains, save the
recovery context with real evidence:

```bash
npx --yes --package spec-superflow@0.10.0 ssf checkpoint save <change-dir> \
  --task <completed-task-id> --next "<next task>" --completed "<completed work>" \
  --verification "<verification report path>" --review "<review report path>" \
  --risk "<open risk or None>" --commit-start <base-sha> --commit-end <head-sha>
```

This augments `.superpowers/sdd/progress.md`; it does not replace the progress
ledger or add a new core workflow state. Do not claim a checkpoint is current
when `npx --yes --package spec-superflow@0.10.0 ssf checkpoint list` reports it as stale.

If task hits BLOCKED (3+ fix failures or changes outside declared scope), escalate to SDD.

## Tweak Mode

Skip TDD. Apply changes directly. Verify file integrity (exists, non-empty, valid syntax). No batch execution — sequential changes.

## DP Records

DP-4 is written by `npx --yes --package spec-superflow@0.10.0 ssf execution plan`; do not write it with raw `state set`.
DP-5 (debug escalation): `npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> dp_5_result "<resolution>"` + timestamp.

## Completion Standard

Don't report completion until: tests pass, contract obligations satisfied, review blockers resolved, every planned wave has a current `pass` receipt, final review is complete, and workflow is ready for `release-archivist`.

## Exception Handling

- **Parse failures**: Stop and report exact line/format issue. Route back to `contract-builder`.
- **Missing artifacts**: Route back to appropriate upstream skill. Don't guess.
- **User interruption**: Progress ledger enables recovery. Check ledger on resume.
