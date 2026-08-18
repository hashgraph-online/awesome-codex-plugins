---
name: finishing-a-development-branch-lite
description: Use when implementation is complete and you need to merge a worktree branch back into the original base branch with build/compile verification (no tests)
---

# Finishing a Development Branch Lite

## Overview
Finish development work by verifying a build/compile check, presenting merge options, and cleaning up the worktree.

**Core principle:** Build/compile first → confirm base branch → present options → execute → cleanup.

**Announce at start:** "I'm using the finishing-a-development-branch-lite skill to complete this work."

## The Process

### Step 1: Verify Build/Compile (No Tests)

1. Check `AGENTS.md` for build/compile commands. If present, follow it.
2. Otherwise use default build/compile commands:

```bash
# Node.js (requires build script)
if [ -f package.json ]; then npm run -s build; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Go
if [ -f go.mod ]; then go build ./...; fi

# Python
if [ -f pyproject.toml ] || [ -f requirements.txt ]; then python -m compileall .; fi

# Java (Maven)
if [ -f pom.xml ]; then mvn -q clean compile; fi
```

If no build command is available (e.g., no npm build script), ask the user for the correct command.

**If build fails:**
```
Build/compile failing (<N> failures). Must fix before completing.

[Show failures]
```

Stop. Do not proceed to Step 2.

### Step 2: Determine Base Branch (Merge Target)

Prefer extracting the base branch from the worktree branch name using the delimiter:

```
__wt__
```

Example:

```
feature/auth__wt__login -> base branch: feature/auth
```

If extracted, verify the **local** branch exists:

```bash
git show-ref --verify refs/heads/<base-branch>
```

If it exists, confirm with the user before merging. If it does not exist, ask the user to provide the base branch.

### Step 3: Present Options

Present exactly these 4 options:

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

### Step 4: Execute Choice

#### Option 1: Merge Locally

**Important:** Run the merge from the base-branch worktree (the directory where the base branch is checked out), not from the worktree branch directory.

```bash
# Switch to base branch
git checkout <base-branch>

# Pull latest (if appropriate)
git pull

# Merge feature branch
git merge <feature-branch>

# Verify build/compile on merged result
<build command>

# If build passes
git branch -d <feature-branch>
```

Then: Cleanup worktree (Step 5)

#### Option 2: Push and Create PR

```bash
# Push branch
git push -u origin <feature-branch>

# Create PR
gh pr create --title "<title>" --body "<summary and build steps>"
```

Then: Cleanup worktree (Step 5)

#### Option 3: Keep As-Is

Report: "Keeping branch <name>. Worktree preserved at <path>."

**Do not cleanup worktree.**

#### Option 4: Discard

**Confirm first:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Then: Cleanup worktree (Step 5)

### Step 5: Cleanup Worktree

**For Options 1, 2, 4:**

Before removing a worktree, change into a directory that will remain (e.g., the base-branch worktree). Removing the current directory will break the session.

```bash
git worktree list | grep $(git branch --show-current)
```

If yes:
```bash
git worktree remove <worktree-path>
```

**For Option 3:** Keep worktree.

## Quick Reference

| Option | Merge | Push | Keep Worktree | Cleanup Branch |
| --- | --- | --- | --- | --- |
| 1. Merge locally | ✓ | - | - | ✓ |
| 2. Create PR | - | ✓ | ✓ | - |
| 3. Keep as-is | - | - | ✓ | - |
| 4. Discard | - | - | - | ✓ (force) |

## Common Mistakes

**Assuming main/master as base branch**
- **Problem:** Merges into the wrong branch
- **Fix:** Confirm the original base branch

**Skipping build verification**
- **Problem:** Merge broken code
- **Fix:** Build/compile must pass before proceeding

**Discarding without confirmation**
- **Problem:** Permanent data loss
- **Fix:** Require typed 'discard'

**Skipping base-branch confirmation because "it should be obvious"**
- **Problem:** Merge target drifts
- **Fix:** Ask, then proceed

## Rationalization Table

| Excuse | Reality |
| --- | --- |
| "I'll merge this into main, it's fine" | Merge into the original base branch unless user says otherwise |
| "Build is optional" | Build/compile is the gate for completion |
| "Discard is reversible" | Discard is permanent and requires confirmation |

## Red Flags

- "I'll just merge to main/master"
- "Build can wait until after merge"
- "Discard without asking is faster"

## Example

```bash
# Build/compile
mvn -q clean compile

# Merge to base branch
base_branch=feature/auth
feature_branch=feature/auth-impl

git checkout "$base_branch"
git pull
git merge "$feature_branch"

# Verify build/compile again
mvn -q clean compile
```
