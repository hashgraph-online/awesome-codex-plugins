---
name: using-git-worktrees
description: Create or verify an isolated git worktree before starting any development work. Prevents main branch contamination, enables parallel feature development, and gives subagents a clean baseline. Use at the start of every feature branch.
---

# Using Git Worktrees

## Why Worktrees

A worktree is a second checkout of the same repo in a separate directory. Each worktree has its own working tree and HEAD, but shares the git object store. This means:

- Subagents work in isolation — no interference with your main session
- You can switch tasks without stashing
- Parallel features develop independently
- Clean rollback: abandon the worktree, nothing pollutes main

## When to Use

Use at the START of every feature or bug fix. Do NOT start implementation until a clean worktree exists or you've confirmed you're already in one.

Mandatory before:
- `subagent-driven-development` skill
- `executing-plans` skill
- Any work touching more than one file

## The Process

### Step 1: Detect Existing Isolation

First check — are you already isolated?

```bash
# Check if current directory is a worktree (not the main checkout)
git worktree list
pwd
```

If you're already in a worktree for this feature: proceed to Step 3 (verify clean baseline).
If you're in the main checkout: proceed to Step 2.

### Step 2: Create the Worktree

```bash
# Create worktree + new branch in one command
git worktree add ../worktrees/<feature-name> -b feat/<feature-name>

# Examples:
git worktree add ../worktrees/stripe-billing -b feat/stripe-billing
git worktree add ../worktrees/fix-auth-bug -b fix/auth-token-expiry
```

The worktree is created at `../worktrees/<feature-name>` (sibling of the project root).
If the project uses `.claude/worktrees/`, use that path instead:

```bash
git worktree add .claude/worktrees/<feature-name> -b feat/<feature-name>
```

### Step 3: Verify Clean Baseline

Move into the worktree and confirm it starts clean:

```bash
cd ../worktrees/<feature-name>   # or .claude/worktrees/<feature-name>
git status                        # Should show: "nothing to commit"
git log --oneline -3              # Confirm you branched from the right point
```

If status shows unexpected changes: something is wrong — investigate before proceeding.

### Step 4: Run Project Setup

Install dependencies and confirm the baseline builds:

```bash
npm install          # or pip install -r requirements.txt / go mod download
npm run build        # Confirm baseline build passes BEFORE any changes
npm test             # Confirm baseline tests pass BEFORE any changes
```

If baseline build or tests fail: STOP. Fix the issue on main first, then recreate the worktree.

### Step 5: Proceed with Work

Now development starts. The worktree is isolated, the baseline is confirmed clean.

## Cleanup After Work Completes

After the branch is merged or abandoned:

```bash
# From the main checkout (not from inside the worktree)
git worktree remove ../worktrees/<feature-name>
git branch -d feat/<feature-name>   # Only after merge
```

## Common Issues

| Issue | Fix |
|-------|-----|
| "already checked out" error | The branch exists in another worktree — use a different branch name |
| Worktree has unexpected changes | Run `git status` to investigate; never force-remove with uncommitted work |
| Setup script fails in worktree | Check for absolute paths in scripts; worktrees use different working directories |
| Submodules not initialized | Run `git submodule update --init --recursive` in the new worktree |

## Worktree vs Branch Checkout

| | `git worktree` | `git checkout -b` |
|--|----------------|-------------------|
| Main session disrupted | No | Yes |
| Parallel work possible | Yes | No |
| Independent node_modules | Yes (separate dir) | Shared |
| Subagent isolation | Clean | Risk of contamination |

Always use worktrees for subagent work. The isolation is the point.
