---
name: finishing-a-development-branch
description: "Use when verified work needs integration or cleanup of an existing task-created branch/worktree, or the user explicitly requests merge, PR, or branch lifecycle handling."
---

# Finishing a Development Branch

## Overview

Integration choice and checkout lifetime are separate. Verify first, mutate only
task-owned resources, then prove what was removed or retained.

**Core principle:** fresh evidence -> authorized integration -> ownership-aware
cleanup -> Git/path readback.

**Announce at start:** explain which branch/worktree lifecycle is being closed.

## Step 1: Environment and Ownership Detection

Read the task's `TaskStartSnapshot` and current repository state. Record:

- root, `HEAD`, branch/detached state, upstream divergence, and active Git ops;
- staged/unstaged/untracked paths and the task-owned delta;
- `git worktree list --porcelain`;
- branch/worktree creator, task ownership, base branch, and cleanup trigger.

Stop on conflicts, detached state, failed verification, dirty/untracked state in
a cleanup target, or unknown ownership. Do not infer the base from the names
`main` or `master`; use task records, repository authority, or explicit user
direction. Never auto-stash, reset, clean, pull, rebase, amend, force-push, or
bypass hooks.

If no task-created branch/worktree exists and integration was not requested,
skip this workflow: report the local task commit plus `Task clean` and
`Repository clean`; do not invent merge/PR ceremony.

## Step 2: Fresh Verification

Run the smallest current-authority test set that proves the completed task. If
it fails, preserve all work and return to diagnosis. Do not present the branch
as ready.

## Step 3: Choose the Authorized Outcome

When a task branch actually needs disposition, present only applicable choices:

1. merge into the recorded base locally;
2. push and create/update a PR;
3. keep the branch for later integration;
4. discard the exact task-owned branch/worktree.

Push, PR, remote deletion, release, and force operations require explicit user
authorization. Discard requires a fresh, exact typed confirmation naming branch,
worktree path, and commits/delta to lose. Generic agreement is insufficient.

## Step 4: Execute Without Hidden Mutation

### Local merge

Verify the target checkout is safe, switch to the recorded base, merge without an implicit pull,
and rerun verification on the merged result. If integration
or verification fails, preserve both histories and stop.

### Push or PR

Push only the authorized task branch and create/update the PR with summary and
fresh test evidence. PR creation does not itself prove merge and does not
require the temporary worktree to remain.

### Keep branch

Retain the branch. Remove a clean task-created temporary worktree by default;
retain it only for an explicit ongoing-checkout need and report why.

### Discard

After exact confirmation, remove only the named clean task-owned worktree, then
the named branch. If either differs from the confirmation, stop and ask again.

## Step 5: Prove Integration Before Branch Deletion

Use evidence matching the merge strategy:

- merge/fast-forward: prove the task tip is an ancestor of the recorded base;
- squash/rebase: use fresh PR merge metadata plus strategy-appropriate patch
  equivalence (`git cherry` for rebased commits; stable patch-id or bounded
  changed-path/tree comparison for squashes), not an ancestor-only test;
- unmerged/open PR: keep the branch unless discard was exactly confirmed.

Never delete a branch merely because a PR was opened or a similarly named
commit exists.

## Step 6: Cleanup in Dependency Order

For a clean task-owned resource:

1. move to another safe registered checkout; never remove the current working directory;
2. remove/unregister the worktree first with `git worktree remove <exact-path>`;
3. read back `git worktree list --porcelain`;
4. verify the exact path no longer exists;
5. only then delete an integrated or exactly confirmed branch;
6. read back branch refs, `HEAD`, and repository status.

Do not use routine `--force`, global `git worktree prune`, wildcard deletion, or
cleanup of resources absent from the task ownership record. On Windows, Git may
unregister a worktree while its directory remains locked: re-check registration
and the exact resolved path, remove only a proven task-owned clean residual when
safe, otherwise retain it and report the lock/path. Never widen deletion scope.

## Final Git Receipt

Report:

- current branch and commit SHA/message, or the reason no commit exists;
- `Task clean: yes|no` and `Repository clean: yes|no` independently;
- branch/worktree created, removed, or retained, with evidence/reason;
- integration evidence and any remaining user action.

`Task clean` means no uncommitted task-owned delta remains. `Repository clean`
means no staged, unstaged, or untracked repository state remains.

This is a local Git receipt, not authoritative completion or merge truth beyond
the evidence read back.

## Integration

Called only when branch/worktree integration or explicit lifecycle handling is
in scope. Pairs with `using-git-worktrees` and
`verification-before-completion`.
