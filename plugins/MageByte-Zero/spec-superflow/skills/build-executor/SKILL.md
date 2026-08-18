---
name: build-executor
description: Govern implementation from an approved execution contract. Invoke when execution-contract.md is approved and the user wants disciplined build work, TDD execution, or guarded batch-by-batch implementation.
---

# Build Executor

Controls the implementation phase. Uses `execution-contract.md` as the workflow authority.

## Required Inputs

For Full or legacy Hotfix, read `execution-contract.md`, `tasks.md`, relevant `specs/`, and relevant `design.md`. Quick, direct incident Hotfix, and Tweak require only their receipt, request boundary, changed files, and verification command.

Check workflow mode and receipt first. Tweak → direct edit mode. Quick or a valid direct incident Hotfix → Direct Quick and Hotfix. Full or legacy Hotfix → standard contract-first discipline.

Branch/worktree preflight before ANY implementation edit (mandatory — do not skip):
1. Run the isolation check:
   ```bash
   ssf isolate <change-dir>
   ```
   This script enforces git isolation: if you are on `main`/`master` it creates a
   git worktree (preferred) or a new branch, and exits non-zero if it cannot and you
   have not approved `--force`.
2. If `ssf isolate` exits non-zero: STOP. Do not edit `main`/`master` in place.
   Ask the user for explicit approval (and re-run with `ssf isolate <change-dir> --force`
   only after they approve).
3. If it succeeds, report the chosen branch/worktree and make all implementation
   edits there.

## Core Laws

### Law 1: Contract First (Full and legacy Hotfix)
For Full and legacy Hotfix, the execution contract is the approved handoff artifact, not chat history. Direct Quick and incident Hotfix use their valid direct receipt plus bounded verification instead; they must not create or require a contract.

### Law 2: TDD Iron Law — Full and legacy Hotfix
RED (write test, see it fail) → GREEN (write minimal code, see it pass) → REFACTOR (clean up, suite stays green).

Quick follows the verification strategy persisted in its receipt: `tdd`, `new-test`, or `bounded` (targeted test, syntax/static check, or other stated evidence). A direct Hotfix must still demonstrate that the original symptom is gone.

**Red Flags**: ignoring the selected verification strategy, reporting a manual check as if it were automated evidence, or silently expanding a bounded Quick change. Full and legacy Hotfix still require RED → GREEN → REFACTOR.

### Test Quality Reference

Before selecting or reviewing test evidence, read
`skills/build-executor/writing-good-tests.md`. Apply its behavior-falsifiability
rules to Full and legacy Hotfix work without changing the persisted Quick
strategy or the Tweak boundary. Documentation-only work uses appropriate
format, link, lint, or build evidence; do not require invented unit tests.

### Law 3: Review Before Drift
Block on: logic defects, spec violations, missing required tests, unintended scope expansion.

### Law 4: Rewind on Contract Break — Full and legacy Hotfix
Return to `specifying` or `bridging` if: new behavior appears, interfaces change materially, design assumptions fail, artifacts no longer define intended implementation.

For Quick/direct Hotfix, stop instead of creating or rewinding a contract; refresh
`workflow recommend` with the observed risk, then select `full --confirm`.

## Controller Continuity Protocol

This protocol is a host controller responsibility. The skill does not create autonomous background execution, retain control after a host turn ends, or guarantee that a dispatched subtask continues without the host.

- While an active subtask exists or a planned wave has a pending wave receipt,
  the controller remains in execution. Send only concise commentary progress;
  do not send a final response or end the control turn as though the change
  were waiting for the user.
- On a user interruption or resume, first read `ssf execution show <change-dir>
  --json` and the progress ledger at `.superpowers/sdd/progress.md`. Reconcile
  those records before dispatching anything, then continue the current eligible
  repair or eligible task according to the persisted plan. Do not restart a
  completed task, skip a retryable repair, or infer completion from chat text.
- A controller may end its control turn or request user input only when the
  change is completed, an external blocker prevents meaningful progress, or
  user authorization is genuinely required. A dispatched task, pending review,
  or routine internal transition is not a terminal condition.
- Commentary must state the current wave/task, evidence or receipt status, and
  the automatic next gate. It must not imply that the skill itself will run in
  the background after the host has ended the turn.

## Planning-document boundary

Treat proposal, design, and tasks as reader-facing decision records. Do not add
per-test RED/GREEN ritual, receipt paths, or dispatch scripts to them during
implementation; keep that evidence in the execution contract, task brief, and
review report. For a Full change, confirm that the one DP-2 blind-reader result
is recorded before treating the contract as the implementation authority.

## Execution Mode Selection

For Full or legacy Hotfix, generate proposed waves from the approved contract, then use the recommendation as a decision aid rather than silently defaulting a mode:

```bash
ssf execution recommend <change-dir> \
  --wave <wave-id>:<parallel|serial>:<task,...>[:<depends-on,...>] --json
# Show every available mode, the observed facts, and the recommendation to the user.
# The command writes a receipt tied to the artifacts, contract, and waves. After the user chooses, record that explicit confirmation:
ssf execution plan <change-dir> \
  --mode <selected-mode> --confirm --reason "user-selected execution mode" \
  --wave <wave-id>:<parallel|serial>:<task,...>[:<depends-on,...>]
# Add --acknowledge-recommendation when the selection differs from the recommendation.
ssf execution show <change-dir> --json
```

The optional fourth `--wave` segment names prerequisite wave IDs. `execution show --json` reports `current`, plus each wave's `depends_on`, `receipt`, `blockers`, `retryable`, and `eligible` status. A wave with `retryable: true` has a current `fail` receipt and is eligible only for its focused repair and re-review; its dependents remain blocked until its replacement `pass` receipt. Report the saved plan revision, selected mode, ordered waves, dependencies, and whether every `parallel` wave can actually be dispatched concurrently on the current platform. If concurrency is unavailable, state the capability and reason plainly; retain the planned `parallel` strategy and do not silently execute it as a serial or Batch Inline plan.

The recommendation uses task count, configured `execution.inlineThreshold`, and declared wave strategy. It never auto-selects: present every available mode and the recommendation to the user. `--confirm` records any user-selected mode; a choice that differs from the recommendation requires `--acknowledge-recommendation` so the plan captures an informed risk decision.

| Mode | Criteria |
|------|----------|
| **SDD** | Recommended for parallel waves, multiple waves, or work beyond the inline threshold |
| **Inline** | Recommended for a single sequential task; always available for a user-confirmed choice |
| **Batch Inline** | Recommended for a bounded sequential batch; it remains serial and is never presented as parallel |

Do not transition to `executing` until `execution show` reports `current: true` and the phase guard passes. A revised plan must repeat `ssf execution recommend` and use `ssf execution revise --confirm`; it creates a new revision and invalidates receipts from the prior revision.

## Batch Inline Execution

Only when the user explicitly confirms `batch-inline` after seeing the recommendation. Current agent executes directly and serially. TDD Iron Law still applies.

Procedure: announce mode → write failing test → confirm failure → implement → run suite → refactor → lightweight checkpoint (files exist, no placeholders, test passed, no unintended changes) → report.

Boundaries: if any task touches >1 module, involves schema/API/config changes, or has open questions → downgrade to Inline or SDD.

## SDD Workflow

For Full/legacy Hotfix by default. Dispatch according to the persisted plan, review each planned wave, and run a final broad review after all waves.

### Planned-Wave Loop
1. Read the current plan with `ssf execution show <change-dir> --json`; only waves shown with `current: true` and `eligible: true` may start. A `retryable: true` wave may only be repaired and re-reviewed; do not dispatch its dependents until its replacement receipt is `pass`. The CLI encodes dependencies in `--wave <id>:<strategy>:<tasks>[:<depends-on,...>]` and rejects a review receipt for a wave whose prerequisites lack current `pass` receipts.
2. A `parallel` wave may dispatch independent tasks simultaneously only when the platform supports concurrent dispatch. If it does not, disclose the unavailable capability and execute the same wave one task at a time without changing its stored strategy.
3. A `serial` wave dispatches one task at a time in listed order.
4. After every wave, write a non-empty persisted regular-file review report (separate from the implementer's report), then record exactly one receipt that names that review report:
   ```bash
   ssf execution review <change-dir> \
     --wave <wave-id> --base <sha> --head <sha> --report .superpowers/sdd/reviews/<wave-id>.md --verdict <pass|fail>
   ```
   `ssf execution plan` creates this review overlay. Store report evidence in it; paths outside the overlay are rejected for audit safety.
   Do not begin a dependent wave until its predecessor receipt is `pass`.
5. Critical/Important findings require a `fail` receipt, a focused repair, re-review, then a replacement `pass` receipt. Never advance or close with a missing or failed receipt.

### Repair and focused re-review protocol

Before dispatching any repair, read `ssf execution show <change-dir> --json` and
use the CLI-provided `waves[].repair` state together with `eligible` and
`retryable`. The controller does not infer a repair round from filenames or
history, and must not write, edit, or modify a repair-state file directly.

- **Rounds 1–2 — recovery:** dispatch only the focused repair for the current
  wave. Give the implementer the CLI repair round, previous review report, and
  the prior review head. Generate a scoped diff from that head, then dispatch
  the `re-review-prompt.md` reviewer against the prior finding and that scoped
  diff. Do not redispatch dependent waves.
- **Third unresolved failure — stop:** the third unresolved receipt yields CLI
  status `adjudication-required`. Stop automatic dispatch and request a human
  adjudication rather than attempting a fourth repair.
- Every focused re-review still writes its separate persisted report and is
  recorded only through `ssf execution review <change-dir> --wave <id> --base
  <sha> --head <sha> --report .superpowers/sdd/reviews/<wave-id>-rereview.md --verdict <pass|fail>`.
  A replacement `pass` receipt is the only evidence that resolves the wave.

### Per-Task Loop
1. **Dispatch implementer**: Load the template with `ssf runtime asset read skills/build-executor/implementer-prompt.md`. Extract task brief with `scripts/task-brief PLAN_FILE N`. Include: where task fits, brief path, interfaces from prior tasks, report file path.
2. **Handle response**: DONE → generate review package + dispatch reviewer.
   DONE_WITH_CONCERNS → assess. For NEEDS_CONTEXT, BLOCKED, or another
   unresolved failure, append `Task N: failed attempt X/3 — <reason>` to the
   existing progress ledger. Retry only when the controller can name new
   evidence, new context, or a specific strategy change. The retry brief contains
   the prior failure reason, the single objective, and the necessary file paths;
   do not repeat the planning pack or conversation history. After
   the third unresolved failure, stop automatic dispatch, enter DP-5, and ask
   the user for a decision.
3. **Review**: Load `ssf runtime asset read skills/build-executor/task-reviewer-prompt.md`. Reviewer returns spec compliance + code quality verdicts with the wave ID, git range, report path, and `pass`/`fail` receipt command.
4. **Fix**: If Critical or Important issues, write the `fail` receipt, read the
   CLI repair state, then dispatch only the focused repair and re-review path
   permitted by the repair protocol above. Write the replacement `pass` receipt
   only after that re-review passes.
5. **Mark complete**: Append to `.superpowers/sdd/progress.md`: `Task N: complete (commits <base7>..<head7>, review clean)`

### Model Selection
Use the configured profile that matches the task role. Resolve it before dispatch:

```bash
ssf runtime config --resolve-model <profile>
```

| Profile | Role |
|---|---|
| `mechanical` | Cheap, routine edits |
| `standard` | Integration and judgment work |
| `strong` | Architecture, design, and final review |
| `review` | Review that matches the diff |

For platforms whose dispatch supports a `model` field, explicitly pass the resolved `model` value. If the result is `configured: false`, automatic selection is unavailable: do not invent a provider model and do not bypass the existing requirement to specify `model` explicitly. Resolution only reads configuration; it does not switch models.

### Progress Ledger
Track in `.superpowers/sdd/progress.md`. Check for existing ledger — completed tasks are done. After each batch: `ssf state set <change-dir> batches_completed <N>`.

## Inline Execution Mode

Only after a user-confirmed `inline` selection is recorded by `ssf execution plan --confirm`; a non-recommended selection also records `--acknowledge-recommendation`. Executes in the current session and still writes one review receipt per planned wave.

Per-task: extract brief → write failing test → confirm failure → implement → confirm green → checkpoint review (done-when criteria, SHALL/MUST verification) → commit → save a task-level recovery checkpoint when another task remains → append to progress ledger.

After a task is committed and reviewed, when another task remains, save the
recovery context with real evidence:

```bash
ssf checkpoint save <change-dir> \
  --task <completed-task-id> --next "<next task>" --completed "<completed work>" \
  --verification "<verification report path>" --review "<review report path>" \
  --risk "<open risk or None>" --commit-start <base-sha> --commit-end <head-sha>
```

This augments `.superpowers/sdd/progress.md`; it does not replace the progress
ledger or add a new core workflow state. Do not claim a checkpoint is current
when `ssf checkpoint list` reports it as stale.

If a task reaches three unresolved failures, stop at DP-5 and request a human
decision. If work moves outside the declared scope, replan instead of retrying.

## Tweak Mode

Skip TDD. Apply changes directly. Verify file integrity (exists, non-empty, valid syntax). No batch execution — sequential changes.

## Direct Quick and Hotfix

Quick direct execution requires the valid receipt, a bounded diff, the receipt's selected verification strategy, and a persisted `test_result: pass`; do not create a contract, execution plan, wave review, DP-6, or DP-7. Direct Hotfix follows the same route only for an incident-backed receipt and must run a regression that demonstrates the original symptom is fixed. If scope grows or risk appears, refresh `workflow recommend`, show the revised risk, and wait for the user to choose Quick or Full before resuming. A legacy Hotfix without a direct receipt remains subject to the contract, DP-3, execution plan, and review receipts.

## DP Records

DP-4 is written by `ssf execution plan`; do not write it with raw `state set`.
DP-5 (debug escalation): bug-investigator records each failed fix through `ssf debug attempt record`; after at least three distinct attempts and explicit user confirmation, use `ssf debug escalate <change-dir> --decision <continue|abandon> --reason "<resolution>" --confirm`. Raw `state set dp_5_*` is blocked.

## Completion Standard

For Full or legacy Hotfix, do not report completion until tests pass, contract obligations are satisfied, review blockers resolved, every planned wave has a current `pass` receipt, and final review is complete. For Quick/direct Hotfix/Tweak, report completion only after bounded verification and persisted `test_result: pass`; do not require contract or review receipts.

## Exception Handling

- **Parse failures**: Stop and report exact line/format issue. Route back to `contract-builder`.
- **Missing artifacts**: Route back to appropriate upstream skill. Don't guess.
- **User interruption**: Progress ledger enables recovery. Check ledger on resume.

## Standard User-Facing Handoff

End every user-facing phase report with this concise handoff. Only a successfully
persisted `closing` state and `abandoned` are terminal.

### Normal report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<completed work>`.
- Next stage: `<next workflow stage or skill>`.
- Entry condition: `<what must be true to enter it>`.

### Blocked report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<blocking fact or missing evidence>`.
- Next stage: `<stage that resumes after the blocker>`.
- Entry condition: `<the approval, artifact, validation, or fix required>`.

### Approval-wait report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<work ready for the named decision>`.
- Next stage: `<stage that follows approval>`.
- Entry condition: `<explicit user approval or recorded decision>`.

### Successful terminal report

- Current stage: successfully persisted `closing` or `abandoned`.
- Completed / blocker: `<persisted terminal outcome>`.
- Next stage: `none`.
- Entry condition: no further transition exists.
