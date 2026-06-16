---
name: ship
description: "Ship phase. Runs isolated integration test in a fresh worktree, creates a PR with full spec + check report in the body, watches CI, and auto-fixes failures."
---

# Ship — Ship It

**CRITICAL**: Run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

## Process

### Step 0: Prerequisites

Load the spec for PR content:
```bash
ls -t $HARNESS_DIR/specs/SPEC-*.md | head -1
```

**Gate: check must have passed.** If no check report exists, invoke the **check** skill before continuing.

### Step 1: Pre-ship Verification

**1a. Isolated Integration Test**
Launch an agent with `isolation: "worktree"` to verify in a clean environment:
- Run full build from scratch (`cargo build --release` / `npm run build` / etc.)
- Run complete test suite
- Run linter and formatter checks
- Verify no uncommitted artifacts

**Gate:** If isolated test fails → STOP. **"Fix with `/go`, then re-run `/check` before shipping."**

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

## Check Report
<paste full Check Report>

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual verification done
EOF
)"
```

### Step 4: CI Verification

```bash
gh pr checks <PR_NUMBER> --watch
```

If CI fails, diagnose and fix automatically. Retry up to 2 times.

### Step 5: Report

```
## Ship Report
- Spec: SPEC-{timestamp} ({goal_slug})
- PR: <URL>
- CI: [PASS/FAIL/N/A]
- Ready to merge: [YES/NO]
- Action needed: <if any>
```

**If inside `/orbit`**: Return control to orbit — it will run evolve automatically.

**If standalone**: Suggest **"Run `/evolve` to analyze this session."**

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "CI will catch it" | CI doesn't catch everything | Run isolated test locally first |
| "The PR description doesn't matter" | It's the permanent record of why | Include spec + check report |
| "I'll merge without CI" | CI is a safety net | Wait for CI, fix failures |

## Evidence Required

- [ ] Isolated test passed in clean worktree
- [ ] PR created with spec + check report in body
- [ ] CI status checked (PASS, FAIL with fix, or N/A)
- [ ] All Conventional Commits applied

## Red Flags

- Shipping without a PASS check report
- PR description that says "various fixes" or "updates"
- Force-pushing to main
- Merging with failing CI
- PR body missing the Check Report section
