---
name: bug-hunt
description: "Run bug hunt."
---
# Bug Hunt Skill

> **Quick Ref:** 4-phase investigation (Root Cause → Pattern → Hypothesis → Fix). Output: `.agents/research/YYYY-MM-DD-bug-*.md`

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Systematic investigation to find root cause and design a complete fix — or proactive audit to find hidden bugs before they bite.

**Requires:**
- writable `.agents/` output directories; create them explicitly if absent
- bd CLI (beads) for issue tracking if creating follow-up issues

## Modes

| Mode | Invocation | When |
|------|------------|------|
| **Investigation** | `$bug-hunt <symptom>` | You have a known bug or failure |
| **Audit** | `$bug-hunt --audit <scope>` | Proactive sweep for hidden bugs |

Investigation mode uses the 4-phase structure below. Audit mode uses systematic read-and-classify — see [Audit Mode](#audit-mode).

---

## The 4-Phase Structure (Investigation Mode)

| Phase | Focus | Output |
|-------|-------|--------|
| **1. Root Cause** | Find the actual bug location | file:line, commit |
| **2. Pattern** | Compare against working examples | Differences identified |
| **3. Hypothesis** | Form and test single hypothesis | Pass/fail for each |
| **4. Implementation** | Fix at root, not symptoms | Verified fix |

**For failure category taxonomy and the 3-failure rule, read `references/failure-categories.md`.**

**For audits or pre-release sweeps that need more than one pass, route through `references/audit-fix-rescan-cycle.md` (multi-pass methodology) and use `references/convergence-criteria.md` to decide when to stop.**

For proactive sweeps that need fresh-eyes rescans, also load [references/multi-pass-bug-hunting.md](references/multi-pass-bug-hunting.md).

For stuck commands, deadlocks, retry storms, blocked subprocesses, or hangs, load [references/deadlock-and-hang-triage.md](references/deadlock-and-hang-triage.md) before changing code.

When the target process is live, hung, or only reproducible under debugger observation, load [references/debugger-attach-triage.md](references/debugger-attach-triage.md) before attaching or changing ptrace/sysctl settings.

## Execution Steps

Given `$bug-hunt <symptom>`:

---

## Phase 1: Root Cause Investigation

### Step 1.1: Confirm the Bug

First, reproduce the issue:
- What's the expected behavior?
- What's the actual behavior?
- Can you reproduce it consistently?

**Read error messages carefully.** Do not skip or skim them.

If the bug can't be reproduced, gather more information before proceeding.

### Step 1.2: Locate the Symptom

Find where the bug manifests:
```bash
# Search for error messages
grep -r "<error-text>" . --include="*.py" --include="*.ts" --include="*.go" 2>/dev/null | head -10

# Search for function/variable names
grep -r "<relevant-name>" . --include="*.py" --include="*.ts" --include="*.go" 2>/dev/null | head -10
```

### Step 1.3: Git Archaeology

Find when/how the bug was introduced:

```bash
# When was the file last changed?
git log --oneline -10 -- <file>

# What changed recently?
git diff HEAD~10 -- <file>

# Who changed it and why?
git blame <file> | grep -A2 -B2 "<suspicious-line>"

# Search for related commits
git log --oneline --grep="<keyword>" | head -10
```

### Step 1.4: Trace the Execution Path

- Find the entry point where the bug manifests
- Trace backward to find where bad data/state originates
- Identify all functions in the path and recent changes to them
- Return: execution path, likely root cause location, responsible changes

### Step 1.5: Identify Root Cause

Based on tracing, identify:
- **What** is wrong (the actual bug)
- **Where** it is (file:line)
- **When** it was introduced (commit)
- **Why** it happens (the logic error)

---

## Phase 2: Pattern Analysis

### Step 2.1: Find Working Examples

Search the codebase for similar functionality that WORKS:
```bash
# Find similar patterns
grep -r "<working-pattern>" . --include="*.py" --include="*.ts" --include="*.go" 2>/dev/null | head -10
```

### Step 2.2: Compare Against Reference

Identify ALL differences between:
- The broken code
- The working reference

Document each difference.

---

## Phase 3: Hypothesis and Testing

### Step 3.1: Form Single Hypothesis

State your hypothesis clearly:
> "I think X is wrong because Y"

**One hypothesis at a time.** Do not combine multiple guesses.

### Step 3.2: Test with Smallest Change

Make the SMALLEST possible change to test the hypothesis:
- If it works → proceed to Phase 4
- If it fails → record failure, form NEW hypothesis

### Step 3.3: Check Failure Counter

Check failure count per `references/failure-categories.md`. After 3 countable failures, escalate to architecture review.

---

## Phase 4: Implementation

### Step 4.1: Design the Fix

Before writing code, design the fix:
- What needs to change?
- What are the edge cases?
- Will this fix break anything else?
- Are there tests to update?

### Step 4.2: Create Failing Test (if possible)

Write a test that demonstrates the bug BEFORE fixing it.

### Step 4.3: Implement Single Fix

Fix at the ROOT CAUSE, not at symptoms.

### Step 4.4: Verify Fix

Run the failing test - it should now pass.

If the bug is in a high-complexity function, consider `$refactor` after fix to prevent recurrence.

---

## Audit Mode

When invoked with `--audit`, bug-hunt switches to a proactive sweep. No symptom needed — you're hunting for bugs that haven't been reported yet.

```bash
$bug-hunt --audit cli/internal/goals/     # audit a package
$bug-hunt --audit src/auth/               # audit a directory
$bug-hunt --audit .                        # audit recent changes in repo
```

### Audit Step 1: Scope

Identify target files from the scope argument:

```bash
# Find source files in scope
find <scope> -name "*.go" -o -name "*.py" -o -name "*.ts" -o -name "*.rs" | head -50
```

If scope is `.` or broad (>50 files), narrow to recently changed files:

```bash
git log --since="2 weeks ago" --name-only --pretty=format: -- <scope> | sort -u | head -30
```

### Audit Step 2: Systematic Read

Read **every file** in scope line by line. For each file, check:

| Category | What to Look For |
|----------|-----------------|
| **Resource Leaks** | Unclosed handles, orphaned processes, missing cleanup/defer |
| **String Safety** | Byte-level truncation of UTF-8, unsanitized input |
| **Dead Code** | Unreachable branches, unused constants, shadowed variables |
| **Hardcoded Values** | Paths, URLs, repo-specific assumptions that won't work elsewhere |
| **Edge Cases** | Empty input, nil/zero values, boundary conditions |
| **Concurrency** | Unprotected shared state, goroutine leaks, missing signal handlers |
| **Error Handling** | Swallowed errors, missing context, wrong error types |

**Key discipline:** Read line by line. Do not skim. The proven methodology (5 bugs found, 0 hypothesis failures) came from careful reading, not heuristic scanning.

### Bug-Finding Pyramid Modes (BF1–BF5)

When running `--audit`, check for missing bug-finding test coverage:

**BF4 — Chaos/Negative Testing (highest bug-finding power):**
For every file that makes external calls (APIs, databases, filesystems), verify:
- [ ] Timeout injection test exists
- [ ] Connection failure test exists
- [ ] Permission denied test exists
- [ ] Corrupt input test exists

If any boundary lacks failure injection → flag as finding (severity: significant).

**BF5 — Script Functional Testing:**
For every .sh script that calls external tools (oc, kubectl, helm):
- [ ] Stub-based functional test exists
- [ ] JSON output schema validated
- [ ] Both healthy and unhealthy stub paths tested

If scripts lack functional tests → flag as finding (severity: moderate).

**BF1 — Property-Based Testing:**
For every data transformation (parse/render/serialize):
- [ ] Property test with randomized inputs exists

**Reference:** The standards skill contains full BF level definitions and per-language tooling.

---

### Audit Step 3: Classify Findings

For each finding, assign severity:

| Severity | Criteria | Examples |
|----------|----------|---------|
| **HIGH** | Data loss, security, resource leak, process orphaning | Zombie processes, SQL injection, file handle leak |
| **MEDIUM** | Wrong output, incorrect defaults, silent data corruption | UTF-8 truncation, hardcoded paths, wrong error code |
| **LOW** | Dead code, cosmetic, minor inconsistency | Unreachable branch, unused import, style violation |

Performance bugs (slow queries, memory leaks, N+1) → escalate to `$perf` for deeper analysis.

### Audit Step 4: Write Audit Report

**For audit report format, read `references/audit-report-template.md`.**

Write to `.agents/research/YYYY-MM-DD-bug-<scope-slug>.md`.

Report to user with a summary table:

```
| # | Bug | Severity | File | Fix |
|---|-----|----------|------|-----|
| 1 | <description> | HIGH | <file:line> | <proposed fix> |
```

Include failure count (hypothesis tests that didn't confirm). Zero failures = clean audit.

---

## Step 5: Write Bug Report

**For bug report template, read `skills/bug-hunt/references/bug-report-template.md`.**

### Step 6: Report to User

Tell the user:
1. Root cause identified (or not yet)
2. Location of the bug (file:line)
3. Proposed fix
4. Location of bug report
5. Failure count and types encountered
6. Next step: implement fix or gather more info

## Key Rules

- **Reproduce first** - confirm the bug exists
- **Use git archaeology** - understand history
- **Trace systematically** - follow the execution path
- **Identify root cause** - not just symptoms
- **Design before fixing** - think through the solution
- **Document findings** - write the bug report

## Quick Checks

Common bug patterns to check:
- Off-by-one errors
- Null/undefined handling
- Race conditions
- Type mismatches
- Missing error handling
- State not reset
- Cache issues

## Examples

### Investigating a Test Failure

**User says:** `$bug-hunt "tests failing on CI but pass locally"`

**What happens:**
1. Agent confirms bug by checking CI logs vs local test output
2. Agent uses git archaeology to find recent changes to test files
3. Agent traces execution path to identify environment-specific differences
4. Agent forms hypothesis about missing environment variable
5. Agent creates failing test locally by unsetting the variable
6. Agent implements fix by adding default value
7. Bug report written to `.agents/research/2026-02-13-bug-test-failure.md`

**Result:** Root cause identified as missing ENV variable in CI configuration. Fix applied and verified.

### Tracking Down a Regression

**User says:** `$bug-hunt "feature X broke after yesterday's deployment"`

**What happens:**
1. Agent reproduces issue in current state
2. Agent uses `git log --since="2 days ago"` to find recent commits
3. Agent uses `git bisect` to identify exact breaking commit
4. Agent compares broken code against working examples in codebase
5. Agent forms hypothesis about introduced type mismatch
6. Agent implements minimal fix and verifies with existing tests
7. Bug report documents commit sha, root cause, and fix

**Result:** Regression traced to commit abc1234, type conversion error fixed at root cause in validation logic.

### Proactive Code Audit

**User says:** `$bug-hunt --audit cli/internal/goals/`

**What happens:**
1. Agent scopes to all `.go` files in the goals package
2. Agent reads each file line by line, checking for resource leaks, string safety, dead code, etc.
3. Agent finds 5 bugs: zombie process groups (HIGH), UTF-8 truncation (MEDIUM), hardcoded paths (MEDIUM), lost paragraph breaks (LOW), dead branch (LOW)
4. All findings confirmed on first pass — 0 hypothesis failures
5. Audit report written to `.agents/research/2026-02-24-bug-goals-go.md`

**Result:** 5 concrete bugs with severity, file:line, and proposed fix — ready for implementation without debugging.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Can't reproduce bug | Insufficient environment context or intermittent issue | Ask user for specific steps, environment variables, input data. Check for race conditions or timing issues. |
| Git archaeology returns too many commits | Broad search or high-churn file | Narrow timeframe with `--since` flag, focus on specific function with `git blame`, search commit messages for related keywords. |
| Hit 3-failure limit during hypothesis testing | Multiple incorrect hypotheses or complex root cause | Escalate to architecture review. Read `failure-categories.md` to determine if failures are countable. Consider asking for domain expert input. |
| Bug report missing key information | Incomplete investigation or skipped steps | Verify all 4 phases completed. Ensure root cause identified with file:line. Check git blame ran for responsible commit. |

## See Also

- [refactor](../refactor/SKILL.md) — Safe, verified refactoring for complexity targets
- [perf](../perf/SKILL.md) — Performance profiling and benchmarking

## Reference Documents

- [references/audit-report-template.md](references/audit-report-template.md)
- [references/bug-report-template.md](references/bug-report-template.md)
- [references/failure-categories.md](references/failure-categories.md)
- [references/audit-fix-rescan-cycle.md](references/audit-fix-rescan-cycle.md)
- [references/convergence-criteria.md](references/convergence-criteria.md)
- [references/multi-pass-bug-hunting.md](references/multi-pass-bug-hunting.md)
- [references/deadlock-and-hang-triage.md](references/deadlock-and-hang-triage.md)
- [references/debugger-attach-triage.md](references/debugger-attach-triage.md)

## Local Resources

### references/

- [references/audit-report-template.md](references/audit-report-template.md)
- [references/bug-report-template.md](references/bug-report-template.md)
- [references/failure-categories.md](references/failure-categories.md)
- [references/audit-fix-rescan-cycle.md](references/audit-fix-rescan-cycle.md)
- [references/convergence-criteria.md](references/convergence-criteria.md)
- [references/multi-pass-bug-hunting.md](references/multi-pass-bug-hunting.md)
- [references/deadlock-and-hang-triage.md](references/deadlock-and-hang-triage.md)
- [references/debugger-attach-triage.md](references/debugger-attach-triage.md)

### scripts/

- `scripts/validate.sh`
