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
`npx --yes --package spec-superflow@0.11.0 ssf state get <change-dir> state`.
Continue only when the persisted state is exactly `executing`. If it is
`closing` → STOP: "Closing is terminal; release, audit, and archival work were
completed before this transition." For any other state, or if the state cannot
be read → STOP and route through `workflow-start`; do not perform side effects.

## The Iron Law: Verification Before Completion

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

## Verification Steps

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

## Final Checks

- Tests passing? (cite command and output)
- All batches complete? (cite batch status)
- Scope added without artifact updates?
- Unresolved blockers or known risks?
- Delta specs exist that need merging?
- Run `npx --yes --package spec-superflow@0.11.0 ssf audit <change-dir>` — include `decision-point-audit.md` in archive

### DP-6 (Verification Outcome)
```bash
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_6_result "<pass|conditional|fail>: <summary>"
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_6_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
If FAIL, do NOT proceed to DP-7. Route back or ask about abandonment.

After recording a PASS outcome, also record it as the verification gate so the
`executing → closing` transition is allowed (the guard accepts either
`test_result: pass` or a `dp_6_result` starting with `pass`):
```bash
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> test_result pass
```

### DP-7 (Archive Confirmation)
```bash
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_7_result "confirmed: <archive summary>"
npx --yes --package spec-superflow@0.11.0 ssf state set <change-dir> dp_7_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
Verify DP-0 through DP-6 are recorded before DP-7.

## Archive Rule

If implementation diverged from the contract, return to `bridging` before closure.

## Finalize While Executing

Complete every release, delta-spec synchronization, and audit action while the
state remains `executing`. If delta specs exist, invoke `spec-merger` and
resolve its outcome before the final `executing → closing` transition. Then
run `npx --yes --package spec-superflow@0.11.0 ssf state transition <change-dir> closing`.
`executing → closing` is the final action: once it succeeds, select no next
skill and run no recovery scans.

## Lightweight Closure (hotfix/tweak)

Verify files exist and are non-empty, run `node --check` on code files, skip 5-step verification. Still record DP-6 and DP-7.

## Exception Handling

- **Parse failures**: Report exact file and section
- **Missing files**: If audit can't generate, run `npx --yes --package spec-superflow@0.11.0 ssf audit` manually
- **User interruption**: Re-run verification from the beginning on resume
- **DP gaps**: Flag missing DPs during DP-6; ask user whether to proceed or return
