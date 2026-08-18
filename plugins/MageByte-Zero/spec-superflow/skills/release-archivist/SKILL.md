---
name: release-archivist
description: Close out a spec-superflow change with verification, summary, and archive readiness. Invoke when implementation is complete, verification is underway, or the user asks for a final wrap-up.
---

# Release Archivist

Finish a spec-superflow change cleanly with verification evidence. This skill
operates while the change state is `executing`; it is not an active skill after
the final transition to `closing`.

## Execution-State Guard

Before verification, `ssf audit`, any DP state write, or delta-spec merge, run
`ssf state get <change-dir> state`.
Continue only when the persisted state is exactly `executing`. If it is
`closing` → STOP: "Closing is terminal; release, audit, and archival work were
completed before this transition." For any other state, or if the state cannot
be read → STOP and route through `workflow-start`; do not perform side effects.

## Direct Short-Path Closure (run before the Full checklist)

For Quick, Tweak, or a valid direct incident Hotfix receipt, skip the Full verification, audit, delta merge, DP-6, and DP-7 sections below. Record changed files, the focused verification command and result, then persist `test_result: pass` and transition to closing. Quick requires a targeted test or syntax/static check; direct Hotfix requires an original-symptom regression. A legacy Hotfix stays on the Full checklist.

## Full/Legacy Verification Before Completion

The Full checklist below applies only to Full and legacy Hotfix. Direct Short-Path Closure above takes precedence for Quick, Tweak, and valid direct Hotfix.

Claiming work is complete without verification is dishonesty, not efficiency. Before claiming any status:
1. IDENTIFY the command that proves the claim
2. RUN the full command fresh
3. READ output, check exit code
4. VERIFY output confirms the claim
5. Only THEN make the claim

**Forbidden before evidence**: "should", "probably", "seems to", expressions of satisfaction without output.

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check |
| Build succeeds | Build exit 0 | Linter passing |
| Bug fixed | Original symptom passes | Code changed |
| Requirements met | Line-by-line checklist | Tests passing |

## Full/Legacy Verification Steps

### Step 1: Test Suite
Run full test suite. Record total/passed/failed/skipped. Zero failures = PASS.

### Step 2: Completeness
Compare contract batches against actual diff. Every SHALL/MUST must have implementation evidence. Missing = Critical severity.

### Step 3: Coherence
Compare design decisions against code. Check naming consistency. Inconsistencies = IMPORTANT.

### Step 4: Unintended Scope
Check for files modified outside scope fence, new dependencies not in design. Unplanned = WARN.

### Step 5: Report

| Dimension | Status | Findings |
|-----------|--------|----------|
| Completeness | PASS/FAIL/WARN | [list] |
| Correctness | PASS/FAIL/WARN | [list] |
| Coherence | PASS/FAIL/WARN | [list] |

**Verdict**: PASS (all PASS) / CONDITIONAL (WARN only) / FAIL (any FAIL).
- FAIL → fix issues or route back to build-executor
- CONDITIONAL → present WARNs, proceed only with user acceptance
- PASS → proceed to final checks

## Full/Legacy Final Checks

- Tests passing? (cite command and output)
- All batches complete? (cite batch status)
- Scope added without artifact updates?
- Unresolved blockers or known risks?
- Delta specs exist that need merging?
- Run `ssf audit <change-dir>` — include `decision-point-audit.md` in archive

### DP-6 (Verification Outcome, Full/legacy Hotfix)
```bash
ssf state set <change-dir> dp_6_result "<pass|conditional|fail>: <summary>"
ssf state set <change-dir> dp_6_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
If FAIL, do NOT proceed to DP-7. Route back or ask about abandonment.

After recording a PASS outcome, also record it as the verification gate so the
`executing → closing` transition is allowed (the guard accepts either
`test_result: pass` or a `dp_6_result` starting with `pass`):
```bash
ssf state set <change-dir> test_result pass
```

### DP-7 (Archive Confirmation, Full/legacy Hotfix)
```bash
ssf state set <change-dir> dp_7_result "confirmed: <archive summary>"
ssf state set <change-dir> dp_7_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
Verify DP-0 through DP-6 are recorded before DP-7.

## Archive Rule (Full/legacy Hotfix)

If implementation diverged from the contract, return to `bridging` before closure.

## Finalize While Executing (Full/legacy Hotfix)

Complete every release, delta-spec synchronization, and audit action while the
state remains `executing`. If delta specs exist, invoke `spec-merger` and
resolve its outcome before the final `executing → closing` transition. Then
run `ssf state transition <change-dir> closing`.
`executing → closing` is the final action: once it succeeds, select no next
skill and run no recovery scans.

## Lightweight Closure (Quick/direct Hotfix/tweak)

Quick and direct Hotfix use a concise verification summary: changed files, focused command, result, and persisted `test_result: pass`. Quick runs targeted tests or syntax/static checks; direct Hotfix proves the original symptom regression. Do not require a contract, execution plan, review receipt, DP-6, or DP-7. A legacy Hotfix remains on the full contract/DP/review closure path. Tweak verifies file integrity and also persists `test_result: pass`.

## Exception Handling

- **Parse failures**: Report exact file and section
- **Missing files**: If audit can't generate, run `ssf audit` manually
- **User interruption**: Re-run verification from the beginning on resume
- **DP gaps**: Flag missing DPs during DP-6; ask user whether to proceed or return

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

### Closing-in-progress report

- Current stage: `executing`; release verification or archive work is still running.
- Completed / blocker: `<completed release work or remaining release blocker>`.
- Next stage: complete the remaining release or archive step, then transition to `closing` (not `none`).
- Entry condition: all release and archive work is complete and the transition succeeds.

### Successful terminal report

- Current stage: successfully persisted `closing` or `abandoned`.
- Completed / blocker: `<persisted terminal outcome>`.
- Next stage: `none`.
- Entry condition: no further transition exists.
