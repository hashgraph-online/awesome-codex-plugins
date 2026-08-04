---
name: using-git-worktrees
description: "Use when a coding task needs a concurrent checkout, unrelated dirty state blocks safe branch switching, or the user or repository explicitly requires a worktree."
---

# Using Git Worktrees

## Overview

A worktree is an exception for simultaneously checking out another Git history,
not a general safety badge. Prefer the current workspace and reuse an existing
suitable worktree. A branch decision and a worktree decision are separate.

**Core principle:** create only with necessity and ownership evidence; pair every
created worktree with a cleanup path.

**Announce at start:** explain which concrete checkout conflict requires a
worktree.

## Step 0: Environment Detection

Before mutation, record the repository root, `HEAD`, branch/detached state,
staged/unstaged/untracked paths, active Git operations, and:

```bash
git worktree list --porcelain
```

Stop on detached HEAD, unresolved conflicts, or an active merge/rebase/
cherry-pick/revert/bisect. Preserve user state: no automatic stash, reset,
clean, broad staging, or commit.

Before deciding necessity or placement, read the smallest relevant project
`AGENTS.md`, `CLAUDE.md`, current authority, and existing worktree convention.
Repository policy may require or forbid isolation and owns any approved
in-repo location; do not discover that policy after creating the checkout.

## Step 1: Necessity Decision

Create at most one task-owned worktree only when one of these is true:

- another branch must remain checked out while this task proceeds;
- unrelated dirty state prevents a safe checkout in the current workspace;
- explicit user or current repository authority requires it.

Task complexity, planning, TDD, use of subagents, or a `main`/`master` branch
name is not sufficient. Same-task subagents share one workspace; do not create
per-subagent or nested worktrees. If independent history is unnecessary, do not
create a branch either.

Record: reason, branch, exact path, creating coordinator, and expected cleanup
event. If the owner or cleanup condition is unknown, stop before creation.

## Step 2: Safe Placement

Use an existing repository convention only when the target directory is already
ignored (`git check-ignore`). Never edit or commit `.gitignore` solely to host a
worktree. If no safe in-repo convention exists, use a task-specific external
user-level temporary directory outside the repository. Resolve and verify the
exact path before creation; do not target a broad home, workspace, or repo root.

## Step 3: Create the Minimum Checkout

Prefer reusing an existing branch carrying the same goal. Create a branch only
when the approved Git lifecycle requires independent history.

```bash
# Existing branch
git worktree add <exact-path> <branch>

# New independently justified branch
git worktree add -b <branch> <exact-path> <start-point>
```

Read back `git worktree list --porcelain`, the new worktree's `HEAD`/branch, and
its status. Do not use force flags.

## Step 4: Authority-Led Setup and Baseline

Read the project's install docs, lockfiles, and existing setup scripts. Run
only setup the project explicitly requires. Do not infer `npm install`,
`cargo build`, `pip install`, `poetry install`, or dependency downloads merely
from manifest presence.

Run the smallest relevant baseline verification. If setup or tests fail, report
the exact failure and preserve the worktree; do not hide it by mutating unrelated
files.

## Step 5: Handoff and Cleanup Ownership

Report the exact path, branch, start `HEAD`, baseline result, owner, and cleanup
trigger. The creating coordinator remains responsible until it proves cleanup
or explicitly hands ownership off.

Use `finishing-a-development-branch` after the task commit or integration
decision. A worktree may usually be removed while its unmerged branch remains;
an open PR does not require a permanent checkout.

## Red Flags

Never:

- create a worktree only because a task modifies code;
- modify `.gitignore` merely to make worktree creation possible;
- install dependencies blindly;
- create one worktree per subagent;
- run global prune or force cleanup as routine hygiene;
- remove dirty, untracked, locked, user-owned, or ownership-unknown resources.

## Integration

Called conditionally by planning/execution workflows only after the necessity
decision. Pairs with `finishing-a-development-branch` for evidence-led cleanup.
