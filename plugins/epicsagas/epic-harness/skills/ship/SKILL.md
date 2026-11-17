---
name: ship
description: "Ship phase. Runs isolated integration test in a fresh worktree, creates a PR with full spec + audit report in the body, watches CI, and auto-fixes failures."
---

# Ship — Ship It

**CRITICAL**: Run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

## Process

### Step 0: Prerequisites

Load the spec for PR content:
```bash
ls -t $HARNESS_DIR/specs/SPEC-*.md | head -1
```

**Gate: audit must have passed.** If no audit report exists, invoke the **audit** skill before continuing.

### Step 1: Pre-ship Verification

**1a. Isolated Integration Test**
Launch an agent with `isolation: "worktree"` to verify in a clean environment:
- Run full build from scratch (`cargo build --release` / `npm run build` / etc.)
- Run complete test suite
- Run linter and formatter checks
- Verify no uncommitted artifacts

**Gate:** If isolated test fails → STOP. **"Fix with `/go`, then re-run `/audit` before shipping."**

### Step 2: Git Hygiene

- Ensure all changes are committed (Conventional Commits)
- Rebase on latest base branch if needed
- Squash fixup commits if appropriate

### Step 3: Create PR

```bash
gh pr create --title "<goal from spec>" --body "$(cat <<'EOF'
## Summary
<Goal from spec — what and why, not how>

## Spec
- Spec ID: SPEC-{timestamp}
- Requirements: R1, R2, ...

## Changes
<bullet list of key changes>

## Acceptance Criteria Verified
- AC1: ✅
- AC2: ✅

## Audit Report
<paste full Audit Report>

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual verification done
EOF
)"
```

Register the PR in the merge-outcome ledger (orbit pipelines are picked up
automatically; standalone ships need this one-liner):

```bash
epic-harness evolve record-pr <PR_URL> [--goal <goal_slug>] [--branch <branch>]
```

### Step 4: CI Verification

```bash
gh pr checks <PR_NUMBER> --json name,state
```

- Checks exist: run `gh pr checks <PR_NUMBER> --watch`. If CI fails, diagnose and fix automatically. Retry up to 2 times.
- Empty result: an empty list does not prove that no CI exists, because workflow runs that need maintainer approval create no checks. Look up the runs for the PR head:

  ```bash
  HEAD=$(gh pr view <PR_NUMBER> --json headRefOid --jq .headRefOid)
  gh run list --commit "$HEAD" --json databaseId,name,status,conclusion,url
  ```

  - Any run with conclusion `action_required`: skip the watch (it can never finish), report CI as BLOCKED (not PASS, not N/A) with the run URLs, and note that a maintainer must approve the runs. Inside `/orbit`, record `"ci_status": "approval_required"` with the run URLs in `phase_history`.
  - No runs: report CI as N/A (no CI configured) and skip the watch.
  - Runs exist without `action_required`: do not call `gh pr checks --watch` (with no checks it exits at once with "no checks reported" and reads as a failure, which is not a CI failure). Watch each run for the HEAD commit with `gh run watch <run-id>` (the `databaseId` above) and treat its result as the CI result. If the runs cannot be watched, report CI as BLOCKED.

### Step 5: Report

```
## Ship Report
- Spec: SPEC-{timestamp} ({goal_slug})
- PR: <URL>
- CI: [PASS/FAIL/BLOCKED/N/A]
- Ready to merge: [YES/NO]
- Action needed: <if any>
```

**If inside `/orbit`**: Return control to orbit — it will run evolve automatically.

**If standalone**: Suggest **"Run `/evolve` to analyze this session."**

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "CI will catch it" | CI doesn't catch everything | Run isolated test locally first |
| "The PR description doesn't matter" | It's the permanent record of why | Include spec + audit report |
| "I'll merge without CI" | CI is a safety net | Wait for CI, fix failures |

## Evidence Required

- [ ] Isolated test passed in clean worktree
- [ ] PR created with spec + audit report in body
- [ ] CI status checked (PASS, FAIL with fix, BLOCKED on approval, or N/A)
- [ ] All Conventional Commits applied

## Red Flags

- Shipping without a PASS audit report
- PR description that says "various fixes" or "updates"
- Force-pushing to main
- Merging with failing CI
- PR body missing the Audit Report section
