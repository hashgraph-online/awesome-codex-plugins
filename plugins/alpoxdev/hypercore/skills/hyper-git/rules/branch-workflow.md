# Branch Workflow

Use this rule when the workflow mode of `hyper-git` is active: choosing or documenting a branching model, creating or syncing a working branch, opening a pull request, merging one, merging a branch into another and pushing, or cleaning up after a merge.

## 1. Read the Repository First

The repository's own settings decide the workflow; this rule never imposes one. Before acting, read:

```bash
git rev-parse --show-toplevel
git status --short --branch
git remote -v
git branch -a
git symbolic-ref --short refs/remotes/origin/HEAD   # default branch
gh repo view --json defaultBranchRef,mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge
```

Also read a contributing guide, `AGENTS.md`, or branch notes when present. Without `gh` or a remote, the workflow is local-only: report that pull requests and remote settings could not be read.

Branch protection and required checks are read through the pull request (`gh pr checks`, `gh pr view --json mergeStateStatus,reviewDecision`). A rejected push is evidence of protection; never retry it with a weaker form.

## 2. Branching Models

When the user asks which model to use, recommend from the repository's evidence, not from preference:

| Model | Fits when | Shape |
|---|---|---|
| GitHub flow | One deployable line, continuous delivery, pull-request review | short branch from the default branch -> pull request -> checks and review -> merge -> delete the branch |
| Trunk-based | Small team or strong CI, integration at least daily | very short branches or direct commits to trunk; release branches cut just in time |
| Integration branch (`dev`) plus deploy branches | The repository already has `dev`, `deploy/*`, or `release/*` branches | work branch from `dev` -> merge into `dev` -> promote to deploy or default branch on request |
| Git Flow | Explicitly versioned software that must support several released versions at once | `develop`, `feature/*`, `release/*`, `hotfix/*`, `main` |

Report the chosen model, the branches that prove it, and what would change if the user picked another. Writing the choice into a contributing document is a separate, explicit request.

## 3. Working Branches

- Base: the branch the user named; otherwise the integration branch (`dev` when it exists), otherwise the default branch.
- Name: `<type>/<short-slug>` with Conventional Commit types (`feat/`, `fix/`, `refactor/`, `docs/`, `chore/`), or `<type>/<issue-number>-<slug>` for issue work, unless the repository documents another convention. Validate with `git check-ref-format --branch <name>`.
- Create without disturbing a dirty checkout: `git switch -c <name> <base>` only in a clean checkout; otherwise create a worktree through the worktree mode.
- Sync: `git fetch origin <base>`, then `git merge origin/<base>` on a shared branch, or `git rebase origin/<base>` only on a branch nobody else has pulled and only when the user or repository prefers linear history. After a rebase of a pushed branch, push with `--force-with-lease`, never with bare `--force`, and never on `main`, `master`, or the default branch.

## 4. Pull Requests

```bash
git push -u origin <branch>
gh pr create --base <base> --head <branch> --title "<conventional subject>" --body-file <file>
gh pr view <n> --json state,mergeStateStatus,reviewDecision,statusCheckRollup
gh pr checks <n> --watch
```

- Title: the Conventional Commit subject of the change. Body: what changed, why, how it was verified, and `Closes #<n>` lines for issues read from `gh issue view` (closing keywords work only when the base is the default branch; see `rules/issue-workflow.md`).
- `--fill` is acceptable for a single-commit branch; check the generated text before publishing.
- Opening a pull request publishes to collaborators: open one only when the user asked for a pull request or for delivery that the repository routes through pull requests.
- Request reviewers only when the user named them.

## 5. Merging

Use the merge method the repository allows and the user asked for; when several are allowed and the user named none, follow the repository's documented convention, else prefer squash for a work branch into an integration branch.

| Route | Command | Use when |
|---|---|---|
| Pull request merge | `gh pr merge <n> --squash|--merge|--rebase [--delete-branch]` | a pull request exists and its checks and reviews pass |
| Auto-merge | `gh pr merge <n> --auto --squash` | the user wants it merged once required checks pass |
| Local merge and push | `git switch <target> && git pull --ff-only && git merge --no-ff <branch>` then `git push origin <target>` | the user asked to merge into a named branch directly and no rule requires a pull request |
| Propagate new commits only | the commit mode's `&& <branch>` targets | only the commits this run created should reach other branches |

Rules for every merge:

- Merge into `main`, `master`, the default branch, or a deploy branch only when the user named that branch in this conversation.
- Never use `gh pr merge --admin`, never bypass required checks or reviews, and never change branch protection or merge settings; report what would have to change instead.
- Before a local merge, the target must fast-forward from its remote (`git pull --ff-only`); a diverged target stops the merge and is reported.
- Resolve conflicts with the commit mode's intent-preserving conflict rule (`rules/commit-and-push-policy.md`), run the repository's checks on the merged result, and push only after they pass.
- When several targets are named ("dev, main"), merge and push them left to right; a failure stops the later targets.
- Never force-push a merge result.

## 6. After the Merge

- Confirm the merge on the remote: `git fetch origin <target>` and `git branch -r --contains <commit>`, or for squash merges `git cherry origin/<target> <branch>` showing no `+` lines, or the pull request state `MERGED`.
- Delete the work branch locally (`git branch -d`, or `-D` after a squash merge was confirmed) and remotely (`git push origin --delete <branch>`) only after the merge is confirmed and no open pull request uses it.
- Remove the worktree through the worktree mode's removal checks.
- Report open issues that the merge did not close.

## 7. Report

Report in Korean: the model or branches read, each branch created, pushed, merged, or deleted with commit SHAs, the pull request URL and state, check results, and every action that a gate stopped.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The GitHub flow steps | <https://docs.github.com/en/get-started/using-github/github-flow> |
| The Git Flow author's 2020 note that continuously delivered software should prefer a simpler flow | <https://nvie.com/posts/a-successful-git-branching-model/> |
| Trunk-based development with short-lived branches and just-in-time release branches | <https://trunkbaseddevelopment.com/> |
| Merge commit, squash, and rebase behavior on GitHub | <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github> |
| Protected branches block force pushes and deletion and can require checks and reviews | <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches> |
| `gh pr create` base resolution and `--fill` | <https://cli.github.com/manual/gh_pr_create> |
| `gh pr merge` methods, `--auto`, `--delete-branch`, and `--admin` | <https://cli.github.com/manual/gh_pr_merge> |
| `--force-with-lease` versus `--force` | <https://git-scm.com/docs/git-push> |

The model-selection table, the branch naming default, and the squash default for work branches are this package's design, not an external requirement.
