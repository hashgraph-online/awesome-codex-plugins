# Context and identity

Read this before any check. A review that does not name what it judged cannot be trusted later, and a review whose scope was guessed can pass the wrong change.

## Contents

1. Resolve the target
2. Recover the goal and the constraints
3. Compute the content identity
4. Staleness
5. Reportable gaps

## 1. Resolve the target

Turn the request into one target block. Record it at the top of the report.

| Kind | How to resolve the base | The reviewed content |
|---|---|---|
| Working tree | The repository default branch, or the merge base the request names | Staged and unstaged changes plus untracked files that belong to the change |
| Named diff, commit range | The range the user named, verbatim | Every commit in the range |
| Branch | The branch upstream or the repository default branch | The merge base to the branch tip |
| Pull request | The pull request's base branch | The commits the pull request adds over its base |

Rules:

- Resolve the repository default branch with `git symbolic-ref --short refs/remotes/origin/HEAD` and fall back to `main`, then `master`. Do not assume.
- For a branch or a pull request, use the merge base rather than the base branch tip, so unrelated commits that landed on the base are not reviewed as part of the change.
- List the changed paths with the command that produced them, for example `git diff --name-status <base>...<target>`.
- Untracked files are part of a working-tree review. Use the project's ignore rules to separate build output and caches from files that belong to the change.
- A request that names several unrelated changes, a whole repository, or nothing at all is not a target. Ask which change once, then stop as `awaiting_input`.
- Never normalize the tree to make the diff cleaner, and never stash, reset, or check out another branch to review it.

## 2. Recover the goal and the constraints

The rubric's first two items need a goal to compare against. Collect it from the request first, then the issue or pull request description, the plan or specification, and the commit messages, in that order.

- Write the goal as one sentence a stranger could check.
- List every explicit constraint: a compatibility promise, a performance ceiling, a naming rule, an interface that must not change, a migration that must stay reversible.
- Mark which statements are claims by the author and which were confirmed by the user. A claim is a thing to check, not a requirement.
- If no goal exists anywhere, say so and treat the change's own stated intent as the goal, labelled `goal inferred`. An inferred goal lowers confidence but does not block the run.

## 3. Compute the content identity

Record one line before the first check:

```sh
git rev-parse HEAD
git diff --binary HEAD | shasum -a 256
git ls-files --others --exclude-standard -z | xargs -0 shasum -a 256 2>/dev/null | shasum -a 256
git ls-files --others --exclude-standard | wc -l
```

The report line is:

```text
Identity: HEAD <sha> | diff sha256:<hex> | untracked sha256:<hex> (n files) | base <ref>
```

Notes:

- Hash the concatenation of the untracked digests with paths included, ordered as `git ls-files` lists them, so two files swapping contents do not produce the same identity.
- The diff digest covers staged and unstaged tracked changes against `HEAD`. Untracked content is covered by the second digest.
- For a commit range, hash the range patch instead of the working diff and say so in the line: `diff sha256:<hex> (range <a>..<b>)`.
- If a digest command is unavailable, record the exact reason and depend on `HEAD` plus the changed-path list. Say the identity is weaker.

## 4. Staleness

A verdict belongs to an identity, not to a commit id and not to a branch name.

- Recompute the identity immediately before writing the verdict. If it differs from the line the matrix was built on, the affected rows are stale.
- Re-run only the rows the new change touches, then re-issue the verdict with the new identity.
- A stored report whose identity differs from the current content is `stale`. Name both identities and the paths that moved.
- A verdict is never carried across a rebase, a squash, a force update of the branch, or a pull request whose head moved, because the reviewed content changed even when the message did not.
- Reviewing a second time on purpose to overturn a `failed` verdict is not allowed. The allowed replacement is the single review described in [verdicts.md](verdicts.md).

## 5. Reportable gaps

When a capability is missing, the report says which row it affects and what would settle it. Common cases:

| Gap | Row outcome |
|---|---|
| No browser or driver for a rendered surface | `unproven`, with the static checks that did run listed separately |
| No credentials or a service that is not running | `unproven`, with the exact command and its error |
| No hardware the change targets | `unproven`, with the target named |
| No subagent capability for the reviewer lane | `review: self`, with the full rubric still applied |
| A test that needs a network call which is blocked | `unproven`, with the blocked host named |

A gap never becomes `N/A`. `N/A` means the criterion does not apply to this goal, with a reason specific to that goal.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Content identity as `HEAD` plus a digest of the working diff and untracked inputs | `dbc-hbin/omp-ulw@74df40f review-work` (mechanism reference, re-authored) |
| Binding review results to a content identity so a later change makes the result stale | same source, re-authored |
| Merge base rather than base tip for branch and pull request scope | standard git practice; `git merge-base` and `git diff A...B` documentation |
| Untracked files as part of a working-tree review | this package's chosen design |

### Evidence grade

`MECHANISM` for the identity binding. `LOCAL` for the line format, the untracked digest construction, and the gap table. The identity line is a chosen design, not a validated optimum.
