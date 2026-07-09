## Scope

Standalone: ask the user which diff to review if the scope is not clear:

- `staged` — review only the staged diff;
- `unstaged` — review only the unstaged diff;
- uncommitted changes — staged plus unstaged;
- branch-vs-base — compare the current branch against its base branch (state the
  base branch used; infer from upstream, remote default, or common names: `main`,
  `master`, `develop`, `trunk`);
- commit, branch comparison, file list, or PR-like scope — review exactly that.

Do not pick a scope yourself unless the user already made it clear. If the
resulting diff is empty, stop and say there is nothing to review.

Inside `/reviewer_review-pr`: the orchestrator provides the diffs of all units (path + patch)
— review those.