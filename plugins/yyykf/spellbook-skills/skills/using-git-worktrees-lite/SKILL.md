---
name: using-git-worktrees-lite
description: Use when creating an isolated git worktree from the current branch for parallel development and only a build/compile check is required (no tests)
---

# Using Git Worktrees Lite

## Overview
Create an isolated worktree from the current branch with a build/compile check instead of running tests.

**Core principle:** Confirm base branch + safe worktree directory + compile-only verification.

**Announce at start:** "I'm using the using-git-worktrees-lite skill to set up an isolated workspace."

## The Process

### Step 0: Normalize to Repo Root (Avoid CWD Pitfalls)

Worktrees are very sensitive to your current working directory (CWD) when you use relative paths like `.worktrees/...`.

Always capture the repo root and ensure you are operating from there before creating worktrees:

```bash
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
```

### Step 1: Capture Base Branch (Merge Target)

```bash
base_branch=$(git branch --show-current)
```

Confirm with the user that this is the branch to merge back into. Do not assume `main` or `master`.

### Step 2: Select Worktree Directory

Follow this priority order:

```bash
ls -d .worktrees 2>/dev/null
ls -d worktrees 2>/dev/null
```

If neither exists, check `AGENTS.md` for a preferred location. If still unknown, ask the user.

### Step 3: Verify Directory is Ignored (Project-Local Only)

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

If not ignored, add the directory to `.gitignore` and commit. If you cannot commit now, stop and ask.

### Step 4: Create Worktree From Base Branch

Use a naming convention to preserve the base branch in the worktree branch name:

```
<base-branch>__wt__<worktree-branch>
```

Example:

```
feature/auth__wt__login
```

```bash
# Example: git worktree add .worktrees/feature-auth__wt__login -b feature-auth__wt__login "$base_branch"
git worktree add "$path" -b "$branch_name" "$base_branch"
cd "$path"
```

### Step 5: Run Project Setup (Auto-detect)

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo fetch; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi

# Java (Maven)
# No dependency install step needed here
```

### Step 6: Build/Compile Check (No Tests)

1. Check `AGENTS.md` for project build/compile commands. If present, follow it.
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

If the build fails, report the failure and ask whether to proceed or investigate.

### Step 7: Report Result

```
Worktree ready at <path>
Base branch: <base-branch>
Build/compile: <result>
```

### Step 8: Return to Repo Root (Important)

Unless the user explicitly asks you to stay in the worktree to debug, return to the repo root at the end.

This prevents follow-up commands from accidentally running in the last worktree (and prevents creating nested worktrees due to relative paths).

```bash
cd "$repo_root"
```

## Quick Reference

| Step | Action |
| --- | --- |
| Base branch | Use current branch, confirm with user |
| Directory | Prefer `.worktrees/`, then `worktrees/`, else ask |
| Safety | `git check-ignore` for project-local directories |
| Build | Follow `AGENTS.md` or defaults; no tests |
| CWD | Normalize to repo root; return at end |
| Merge | Merge from the base-branch worktree, not the worktree branch |

## Common Mistakes

**Assuming main/master as base branch**
- **Problem:** Merges into the wrong branch
- **Fix:** Capture and confirm current branch as base

**Skipping ignore verification**
- **Problem:** Worktree files show up in git status
- **Fix:** `git check-ignore` before creating worktree

**Running tests instead of compile-only**
- **Problem:** Violates the lite workflow
- **Fix:** Only run build/compile checks

**Skipping build because no obvious command**
- **Problem:** Misses required compilation verification
- **Fix:** Ask for the project-specific build command

**Merging from the worktree branch directory**
- **Problem:** Base branch is already checked out elsewhere; merge fails
- **Fix:** Merge from the base-branch worktree directory

**Staying in the last worktree directory**
- **Problem:** Follow-up tasks run in the wrong directory; relative worktree paths can create nested worktrees
- **Fix:** Always `cd "$repo_root"` after setup/build unless debugging is needed

## Rationalization Table

| Excuse | Reality |
| --- | --- |
| "I'll just merge this into main later" | Base branch is the current branch; confirm it now |
| "Tests are easier than a build" | Lite workflow requires build/compile only |
| "No build command, so I'll skip it" | Ask for the correct build command |

## Red Flags

- "I'll just merge this back to main"
- "Tests are faster than figuring out the build"
- "No need to confirm the base branch"

## Example

```bash
base_branch=$(git branch --show-current)
# Confirm base_branch with user
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
mkdir -p .worktrees
path=.worktrees/feature-x
branch_name=feature-x

git worktree add "$path" -b "$branch_name" "$base_branch"
cd "$path"

npm install
npm run -s build

cd "$repo_root"
```
