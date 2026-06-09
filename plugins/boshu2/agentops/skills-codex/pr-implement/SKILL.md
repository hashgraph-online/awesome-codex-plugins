---
name: pr-implement
description: "Run pr implement."
---
# PR Implement Skill

Fork-based implementation for open source contributions with mandatory isolation check.

## Overview

Execute a contribution plan with fork isolation. Ensures PRs are clean
and focused by running isolation checks before and during implementation.

**Input**: Plan artifact from `$plan` (after `$pr-research`) or repo URL

**When to Use**:
- Implementing a planned OSS contribution
- Need isolation enforcement for clean PRs
- After completing `$pr-research` and `$plan`

**When NOT to Use**:
- Internal project work (use `$implement`)
- Haven't planned yet (run `$pr-research` then `$plan` first)

---

## Workflow

```
-1. Prior Work Check      -> BLOCKING: Check for competing PRs
0.  Input Discovery       -> Find plan artifact or repo
1.  Fork Setup            -> Ensure fork exists and is current
2.  Worktree Creation     -> Create isolated worktree
3.  Isolation Pre-Check   -> BLOCK if mixed concerns
4.  Implementation        -> Execute plan
5.  Isolation Post-Check  -> BLOCK if scope creep
6.  Commit Preparation    -> Stage with proper commit type
7.  Handoff               -> Ready for $pr-prep
```

---

## Phase -1: Prior Work Check (BLOCKING)

```bash
# Search for open PRs on this topic
gh pr list -R <owner/repo> --state open --search "<topic>" --limit 10

# Check target issue status
gh issue view <issue-number> -R <repo> --json state,assignees
```

| Finding | Action |
|---------|--------|
| Open PR exists | Coordinate or wait |
| Issue assigned | Coordinate or find alternative |
| No competing work | Proceed |

---

## Phase 3: Isolation Pre-Check (BLOCKING)

```bash
# Commit type analysis
git log --oneline main..HEAD | sed 's/^[^ ]* //' | grep -oE '^[a-z]+(\([^)]+\))?:' | sort -u

# File theme analysis
git diff --name-only main..HEAD | cut -d'/' -f1-2 | sort -u
```

| Check | Pass Criteria |
|-------|---------------|
| Single commit type | 0 or 1 prefix |
| Thematic files | All match plan scope |
| Branch fresh | Based on recent main |

**DO NOT PROCEED IF PRE-CHECK FAILS.**

---

## Phase 4: Implementation

### Guidelines

| Guideline | Why |
|-----------|-----|
| **Single concern** | Each commit = one logical change |
| **Match conventions** | Follow project style exactly |
| **Test incrementally** | Run tests after each change |

### Commit Convention

```bash
git commit -m "type(scope): brief description

Longer explanation if needed.

Related: #issue-number"
```

---

## Phase 5: Isolation Post-Check (BLOCKING)

```bash
# Commit type analysis
git log --oneline main..HEAD | sed 's/^[^ ]* //' | grep -oE '^[a-z]+(\([^)]+\))?:' | sort -u

# Summary stats
git diff --stat main..HEAD
```

| Check | Pass Criteria |
|-------|---------------|
| **Single commit type** | All commits share same prefix |
| **Thematic files** | All files relate to PR scope |
| **Atomic scope** | Can explain in one sentence |

---

## Phase 7: Handoff

```
Implementation complete. Isolation checks passed.

Branch: origin/$BRANCH_NAME
Commits: N commits, +X/-Y lines

Next step: $pr-prep
```

---

## Anti-Patterns

| DON'T | DO INSTEAD |
|-------|------------|
| Skip isolation pre-check | Run Phase 3 FIRST |
| Skip isolation post-check | Run Phase 5 before push |
| Mix concerns in commits | One type prefix per PR |
| Implement without plan | Run $pr-research then $plan first |

## Examples

### Implement From Contribution Plan

**User says:** "Implement this external PR plan with isolation checks."

**What happens:**
1. Run pre-checks for branch and scope isolation.
2. Implement only in planned files/areas.
3. Run post-checks and prepare handoff for PR prep.

### Enforce Single-Concern Commit Set

**User says:** "Make sure this branch is still single-purpose before I prep the PR."

**What happens:**
1. Inspect commit/file patterns against stated scope.
2. Flag mixed concerns and suggest extraction steps.
3. Produce a clean handoff to `$pr-prep`.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Isolation check fails | Unrelated changes on branch | Move unrelated edits to separate branch/PR |
| Commits mix concerns | Implementation drifted from plan | Re-split commits by concern and revalidate |
| Scope keeps expanding | Weak boundaries in plan | Re-anchor to `Out of Scope` and stop additional changes |
| Hard to hand off | Missing summary/test context | Add concise change summary and verification notes |

## Local Resources

### scripts/

- `scripts/validate.sh`


