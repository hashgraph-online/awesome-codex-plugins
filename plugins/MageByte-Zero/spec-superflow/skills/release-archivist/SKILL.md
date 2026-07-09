---
name: release-archivist
description: Close out a spec-superflow change with verification, summary, and archive readiness. Invoke when implementation is complete, verification is underway, or the user asks for a final wrap-up.
---

# Release Archivist

Finish a spec-superflow change cleanly with verification evidence.

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
- Run `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" audit <change-dir>` — include `decision-point-audit.md` in archive

### DP-6 (Verification Outcome)
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_6_result "<pass|conditional|fail>: <summary>"
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_6_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
If FAIL, do NOT proceed to DP-7. Route back or ask about abandonment.

After recording a PASS outcome, also record it as the verification gate so the
`executing → closing` transition is allowed (the guard accepts either
`test_result: pass` or a `dp_6_result` starting with `pass`):
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> test_result pass
```

### DP-7 (Archive Confirmation)
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_7_result "confirmed: <archive summary>"
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_7_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```
Verify DP-0 through DP-6 are recorded before DP-7.

## Archive Rule

If implementation diverged from the contract, return to `bridging` before closure.

## Post-Verification

Run `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state transition <change-dir> closing`. If delta specs exist, route to `spec-merger`.

## Lightweight Closure (hotfix/tweak)

Verify files exist and are non-empty, run `node --check` on code files, skip 5-step verification. Still record DP-6 and DP-7.

## Exception Handling

- **Parse failures**: Report exact file and section
- **Missing files**: If audit can't generate, run `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" audit` manually
- **User interruption**: Re-run verification from the beginning on resume
- **DP gaps**: Flag missing DPs during DP-6; ask user whether to proceed or return
