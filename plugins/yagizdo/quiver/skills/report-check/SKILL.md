---
name: report-check
description: Analyze a review report for quality -- detects noise, false positives, overkill suggestions, and findings that exist to appear thorough. Usage: /report-check <path-to-report>
when-to-use: "user wants to audit a review report for noise or false positives -- '/report-check', 'check this report', 'is this review good', 'verify the review findings'"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

---

# Report Quality Check

Analyze a review report for quality issues -- noise, false positives, overkill suggestions, and findings that exist to appear thorough rather than to help the developer.

**Announce:** "Using the report-check skill to audit report quality."

---

## Step 0 -- Validate Input

If `$ARGUMENTS` is empty, print:

> Usage: `/report-check <path-to-review-report.md>`
> Analyzes a review report for quality issues -- noise, false positives, overkill suggestions.

**Stop here.**

If `$ARGUMENTS` contains a file path:
1. Read the file using the Read tool.
2. If the file does not exist or is not readable, print:
   > Report file not found: `{path}`
**Stop here.**

---

## Step 1 -- Read Report

1. Read the full report file.
2. Extract the branch name from the `## Review Context` section if present (look for a `Branch:` line).
3. Note the report structure: findings grouped by severity, verdict, filtered findings section.

---

## Step 2 -- Reconstruct Diff (optional)

If git is available AND a branch name was extracted from the report:

1. Determine the base branch:
   ```
   !`git rev-parse --verify main 2>/dev/null || echo "NO_MAIN"`
   ```
   Use `main` if it exists, otherwise `master`.

2. Get the diff:
   ```
   !`git diff {base}...{branch} 2>/dev/null || echo "NO_DIFF"`
   ```

3. If the diff is non-empty, it will be passed to the agent for cross-referencing.

Print status:
- With diff: `Analyzing report with diff cross-reference...`
- Without diff: `Analyzing report (no diff available for cross-reference)...`

If git is unavailable or no branch info exists, proceed without diff. The agent works report-only -- Phase 2 accuracy checks will be limited.

---

## Step 3 -- Dispatch Agent

Spawn the `quiver:report-checker` agent with a self-contained prompt containing:

1. The full report content, clearly delimited:
   ```
   <report>
   {full report markdown}
   </report>
   ```

2. The diff (if available), clearly delimited:
   ```
   <diff>
   {full diff output}
   </diff>
   ```
   If no diff is available, include:
   ```
   <diff>
   No diff available for cross-referencing.
   </diff>
   ```

3. Instruction: "Audit this review report for quality. Apply all three phases (substance verification, accuracy check, proportionality audit). Return structured findings using your output format."

---

## Step 4 -- Present Results

If agent returns zero issues:
> Report passed quality audit -- no issues found.

If agent returns issues, display the structured findings to the user.

Use `AskUserQuestion`:
> Quality audit found {N} issues in the report. What would you like to do?

Buttons:
- `Apply fixes to the report`
- `Show details only`
- `Skip -- keep as-is`

Handle each option:

<!-- SYNC: The apply-fixes procedure below (REMOVE/DOWNGRADE/REWRITE actions + recalculation steps) is duplicated in skills/review/SKILL.md Step 3.5 "Handle results" block. Keep both in sync. -->
**Apply fixes:**
1. For each issue with action REMOVE: delete the finding from the report file.
2. For each issue with action DOWNGRADE: change the finding's severity and move it to the correct severity section.
3. For each issue with action REWRITE: replace the finding's recommendation text with the corrected version.
4. After applying all fixes, recalculate:
   - Findings overview counts in `## Review Context`
   - Disposition counts in `## Review Context`, and the `**Deferred:**` line under the fix order table
   - Severity section contents (move downgraded findings, remove deleted ones)
   - Recommended Fix Order table (remove entries for deleted/downgraded findings)
   - Verdict line (recompute based on remaining finding severities)
5. Write the updated report back to the same file path.
6. Proceed to Step 5.

**Show details:**
1. Print the full audit output.
2. Re-ask via `AskUserQuestion`:
   > Apply the suggested fixes?
   Buttons: `Apply fixes` / `Skip -- keep as-is`

**Skip:**
Stop. Report unchanged.

---

## Step 5 -- Verify (if fixes applied)

1. Read the modified report file back using the Read tool.
2. Confirm no `{placeholder}` text remains in the report.
3. Print:
   > Report updated: {N} findings removed, {M} downgraded, {K} rewritten.
