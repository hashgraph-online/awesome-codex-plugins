# Branch State — Resolving the Branch Work Boundary

Plugin runtime asset. Loaded by the `review` skill to scope a branch review
and by the `plan` and `document` skills for grounding. Every step is a plain
git command run in the project working directory. No step contacts a remote;
the whole procedure runs offline.

## Purpose

Determine the branch work boundary: the current branch, the default branch,
the merge base, and the files changed since divergence. The `review` skill
uses the boundary as its review scope. The `plan` and `document` skills embed
the boundary into grounding.

A **sentinel** is a named terminal state. When a step yields a sentinel, stop
the procedure and apply the caller response from the sentinel table.

## Prerequisites

- A `git` executable, version 2.22 or later, on `PATH` (`git branch --show-current` requires 2.22).
- Run every command from the project working directory.

## Procedure

1. Run `git rev-parse --git-dir`.
   Expected result: the path of the git directory, exit code 0.
   If the command fails, stop with sentinel `no-repo`.
2. Run `git branch --show-current`.
   Expected result: one line with the current branch name.
   If the output is empty, stop with sentinel `detached-head`.
3. Resolve the default branch name `<name>` with this offline chain, in order:
   1. Run `git symbolic-ref --short refs/remotes/origin/HEAD`.
      Expected result: a ref such as `origin/main`. Strip the `origin/`
      prefix; the remainder is `<name>`.
   2. If step 3.1 fails, run `git rev-parse --verify --quiet <ref>` for each
      ref in this order: `origin/main`, `origin/master`, `main`, `master`.
      The first ref that succeeds wins. Strip an `origin/` prefix when
      present; the remainder is `<name>`.
   3. If every probe fails, stop with sentinel `no-default-branch`.
4. If the current branch equals `<name>`, stop with sentinel
   `on-default-branch`.
5. Select `<default-ref>`: if `git rev-parse --verify --quiet origin/<name>`
   succeeds, set `<default-ref>` to `origin/<name>`; otherwise set
   `<default-ref>` to `<name>`.
6. Run `git merge-base HEAD <default-ref>`.
   Expected result: one commit hash — the merge base `<merge-base>`.
   If the command fails, stop with sentinel `no-merge-base`.
7. Run `git diff --name-status <merge-base>..HEAD`.
   Expected result: zero or more lines; each line holds one status letter and
   one committed changed file.
8. Run `git status --porcelain`.
   Expected result: zero or more lines of uncommitted work, including
   untracked files.
9. If step 7 and step 8 both produced empty output, stop with sentinel
   `empty-diff`.

## Output block

On success, embed this block into grounding:

```text
branch-state
  current-branch:      <current branch>   # step 2
  default-branch:      <name>             # step 3
  merge-base:          <merge-base>       # step 6
  committed-changes:   <step 7 output>    # empty = none
  uncommitted-changes: <step 8 output>    # empty = none
```

## Sentinels

Caller responses mirror the failure behavior of the command-surface spec
(`command-surface-v2.spec.md`). The full failure flow belongs to that spec
and to the `review` skill, not to this file.

| Sentinel | Meaning | Caller response |
|---|---|---|
| `no-repo` | The working directory is not inside a git repository. | The skill requests an explicit path or topic from the user. |
| `detached-head` | `HEAD` points to a commit, not a branch. | The skill states the detached state and requests an explicit path, topic, or ref. |
| `no-default-branch` | No default branch resolves offline. | The skill requests an explicit path or topic from the user. |
| `on-default-branch` | The current branch is the default branch. | The `review` skill reports project health instead of a branch review. |
| `no-merge-base` | `HEAD` and `<default-ref>` share no common ancestor. | The skill requests an explicit path or topic from the user. |
| `empty-diff` | No committed and no uncommitted changes exist since the merge base. | The `review` skill reports project health instead of a branch review. |
