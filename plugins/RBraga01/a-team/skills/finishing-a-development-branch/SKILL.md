---
name: finishing-a-development-branch
description: Complete a development branch before merge — verify tests pass, update documentation, ensure quality gate passes, and prepare a clean PR.
---

# Finishing a Development Branch

Complete all final steps before merging a feature branch.

**Announce at start:** "I'm using the finishing-a-development-branch skill."

## Checklist (Complete in Order)

### 1. Verify Tests Pass
```bash
npm test           # or pytest, go test, cargo test
npm run test:coverage
```
- All tests must pass (no skips, no TODOs in critical paths)
- Coverage must be ≥ 80%
- If tests fail → stop and fix before continuing

### 2. Verify Build
```bash
npm run build      # or go build ./..., cargo build --release
npx tsc --noEmit
```
- Build must succeed with zero errors

### 3. Quality Gate
- Run `/quality-gate` (code review + security review in parallel)
- Block MUST be resolved before merge
- Warn can merge with documented issue

### 4. Clean Up
- Remove all `console.log` and debug statements
- Remove all commented-out code
- Remove all TODO/FIXME without issue references

### 5. Update Documentation
- Update CLAUDE.md or README.md if setup changed
- Run `doc-updater` agent if codemaps are out of date
- Update CHANGELOG if project uses one

### 6. Prepare PR
```bash
git log --oneline [base-branch]..HEAD    # Review all commits
git diff [base-branch]...HEAD            # Review all changes
```

Write PR body with:
- Summary (3-5 bullet points of what changed and why)
- Test plan (checkboxes for manual verification steps)
- Screenshots if UI changed

### 7. Final Commit
- All changes staged and committed
- Commit message follows conventional format
- Branch is up to date with base

## Hard Rules

- Never merge with failing tests
- Never merge with CRITICAL review findings
- Never merge to main/master directly (use PR)
- Never skip the quality gate

The branch is done when every checkbox above is checked.
