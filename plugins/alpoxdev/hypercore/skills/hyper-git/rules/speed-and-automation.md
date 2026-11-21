# Speed And Automation

Use this rule when the commit mode of `hyper-git` feels slow or the user explicitly asks for a faster commit-and-push path.

## Fast Path

Prefer this path before the verbose manual workflow:

```bash
scripts/git-fast.sh inspect . --jobs 4
```

Then commit each logical group with the existing commit helper:

```bash
scripts/git-commit.sh "<type>(<scope>): <imperative summary>" path/to/file1 path/to/file2
scripts/git-commit.sh --repo path/to/repo "<type>(<scope>): <imperative summary>" path/to/file1
```

After all commits succeed, reuse the inspected repo list instead of rediscovering:

```bash
scripts/git-fast.sh push /absolute/repo/path
scripts/git-fast.sh push --force /absolute/repo/path
```

If the fast helper fails or omits needed detail, fall back to `repo-discover.sh`, `repo-status.sh`, `git-commit.sh`, and `git-push.sh`.

## What The Fast Helper Automates

| Step | Automation |
|------|------|
| repository discovery | current repo/worktree short-circuit; descendant discovery prunes heavy generated directories and recognizes linked worktree `.git` files |
| multi-repo inspection | parallel per-repo status blocks via `--jobs` / `HYPER_GIT_JOBS` |
| file inventory | captures one porcelain status snapshot per repo and derives staged, unstaged, and untracked lists from it instead of running three duplicate file scans |
| legacy helpers | `repo-discover.sh` prunes generated trees, `repo-status.sh` reuses captured status/stat output, and `git-push.sh` independently preserves the same safe-push policy |
| worktree context | emits `worktree|primary` or `worktree|linked` plus git dir metadata so operators keep checkout roots separate from the common git dir |
| push | accepts explicit repo paths, uses `GIT_TERMINAL_PROMPT=0`, skips detached HEAD, blocks protected force pushes |

## Parallelization Rules

- Parallelize read-only inspection across repositories.
- Do not parallelize commits inside the same repository; staging/index state is shared.
- Repositories may be committed independently, but only when file groups and repo boundaries are already clear.
- Push only after all intended commits have succeeded.

## Slow Path Triggers

Use the slower full workflow when:

- partial hunks require `git add -p`
- staged and unstaged changes are intentionally mixed
- hooks fail and require diagnosis
- filter arguments do not clearly map to files
- a push failure needs remote/auth investigation

## Timing Expectations

The helper is meant to remove avoidable overhead, not bypass safety. It speeds up:

- duplicated repository discovery between commit and push
- large descendant tree scans by pruning common generated folders
- linked worktree runs by resolving the checkout root without assuming `.git` is a directory
- multiple-repository status checks by parallelizing read-only work
- single-repository inspection by reusing one status snapshot for both raw status and grouped file inventory
- commit-message validation in Bash without spawning `grep`

It does not remove the need to inspect diffs, group logical changes, write correct commit messages, or handle hook failures.

## Sources

> No external sources were used. Content checked 2026-09-22.

This rule set is authored in this package from repository practice. It makes no external claim, so no external source is cited.
