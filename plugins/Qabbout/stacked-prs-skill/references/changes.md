# Changing a stack that already exists

Situations the normal flow doesn't cover. The rules still apply to all of them: no force-push, no rebase of a pushed branch, every push approved, no PR closed by accident, and the user approves every host or tracker action.

## A reviewer wants code moved to another slice

**Down** (from slice k to a lower slice j):
1. On slice j, add the files as a new commit (`git checkout $REF -- <files>`, or a three-way merge for files the base also changed; see `splitting.md` step 5).
2. Carry j up as usual (B4). When the merge reaches slice k, the files are already there, so k's diff shrinks.
3. Update both descriptions, after approval.

**Up** (from slice j to a higher slice k):
1. On slice j, commit the removal. Restore the base's version (`git checkout origin/<base> -- <files>`), or `git rm` the files if the base doesn't have them.
2. Carry j up. Every branch between j and k now loses the files too. Check nothing there still references the moved code.
3. On slice k, after merging, add the files back from the reference as a new commit.
4. Run `split-coverage.sh` again, then update the descriptions.

## A slice must be dropped or reordered

- **Reordering:** avoid it. Treat it as moving code between slices (above), then renumber the `[k/N]` titles in one pass, after approval.
- **Dropping a slice whose code is still needed:** move its files into a neighbouring slice, then close the empty slice.
- **Dropping a slice whose code shouldn't ship:**
  1. If it's merged into the stack-base, revert that merge on the stack-base (`git revert -m 1 <merge commit>`) and carry the stack-base up. Otherwise, on the first slice that depends on it, add a commit that reverts its changes (`git revert --no-edit <its commits>`, or `git revert -m 1 <merge>`). Carry that up.
  2. **Before** touching the dropped PR, retarget every PR that targets its branch to that branch's own target, after approval (rule 10).
  3. Ask the user whether to close the dropped PR, and keep its branch until no PR targets it.

## A slice PR was closed

Reopen it if the host allows; GitHub and GitLab usually do, but Bitbucket may not offer it for declined PRs. Otherwise:
1. Check the branch still exists, and recreate it from its last known commit if it doesn't (`git reflog`, or someone's local copy). Get that push approved.
2. With approval, open a new PR from the same branch to the same target, and copy the description.
3. Update every description that mentions the old number, and say why it happened in the report.

## A hotfix on the base touches stack files

Merge the base into the integration branch and into the independent slices the hotfix conflicts with, then carry those merges up, including copied dependents. Reconcile affected behavior and callers even when Git reports no conflict (`reconciliation.md`); update the porting log and checks against the new tips. Approve each push. From now on, pass `-i` to `split-coverage.sh`, recording that it skips base-changed paths and cannot verify their preservation.

## CI fails on slice k because of slice j below it

The bug belongs to slice j, so fix it there (B1–B4). Mention on k's PR that the fix is coming from j.

## The base moves while the slices are being cut

Keep cutting from the pinned `BASE`. Bring the newer base in after the PRs exist, through normal merges, and only where conflicts or CI need it.

## The base branch changes

Ask the user first: branches can't be rebased onto a new base (rule 3). Either keep the current base, or, with approval, cut new branches from the new base by cherry-picking each slice's commits, and open new PRs for them. Leave the old PRs open until the user decides what to do with them.

## Two people work on the same stack

Run phase 0 at the start of every session. `safe-push.sh` refuses when the remote has commits you don't have. Merge them in, check again, and get a new push approval. Agree with the user who owns which branches.

## A slice is too big to review

Inside the PR, use one commit per area, and ask reviewers to go commit by commit. Split it into more slices only if each half builds and passes without temporary code. A temporary bridge needs the user's agreement.

## Descriptions go stale

After any change to the stack's shape (N, targets, merged PRs, PR numbers, the integration branch's contents) or to its build claims, update every affected description in one pass, after approval. Watch for these:
- "Part k of N"
- "Stacked PR … targets …"
- "Not in this PR"
- "How this branch is built"
- "Expected conflicts"
- "Local checks"
