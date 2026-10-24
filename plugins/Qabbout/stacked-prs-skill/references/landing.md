# Phase C: Land the stack

Every action on the host here (merging a PR, changing a target, closing a PR, deleting a branch) and every tracker change needs the user's authorization for that scope; one authorization may cover a concrete batch. Every push needs an approved `safe-push.sh` plan (rule 4).

## 0. Retargeting: let the host do it, and check every time

When a merge deletes the merged PR's branch, some hosts move every open PR that targeted it to the merged PR's target. In `a ← b ← c`, merging `b` into `a` makes `c` target `a`.

| Host | Retargets when a merge deletes the branch? | Do |
|---|---|---|
| GitHub | Yes ([documented](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request)) | Merge with "delete branch" on |
| Bitbucket | Unverified; confirm current behavior for this repository | Retarget dependents before deleting the parent unless verified |
| GitLab, others | Check current documentation or an authorized test, then record it in the stack map | If unverified, retarget by hand before merging |

- **Before merging**, note the open PRs that target the branch about to merge (the stack map's "Other PRs target it?" column).
- **Right after merging**, check each of those PRs:
  - **open, and targets the merged PR's target:** continue with step 3.
  - **open, but still targets the deleted branch:** retarget it by hand now (with approval), and tell the user.
  - **closed:** stop and tell the user, then follow `changes.md`, "A slice PR was closed".
- **No merge, no retarget.** An integration branch, or a slice dropped without merging, is never merged through a PR. Retarget its dependents by hand (with approval) before the branch goes away. Never delete a branch by hand while an open PR targets it.
- **The reference PR is closed only when the user decides to.**

## 1. Know how the host merges

```bash
git log --oneline --first-parent -10 origin/<base>
```

- **Merge commit** ("Merge pull request #N" or "Merged in …"): the PR's commits stay in the base's history. The PRs above it only need retargeting and a merge of the base.
- **Squash or rebase merge** (one new commit per PR): the PR's original commits don't exist on the base. The PRs above it still contain them, so their diffs show the landed changes again until step 3 fixes them.

If you can choose, a merge commit is better for a stack. Squash is fine for the last PR, or for a slice nothing else depends on.

## 2. Merge order

- A PR merges only after every PR it depends on has merged.
- Independent slices that target the base can merge in any order once they're approved.
- Before a PR merges, check that its diff against its target is only its own slice (`git diff --stat origin/<target>...origin/<branch>`), and that CI is green.
- For a cutover carrying copied slices or porting newer base code, complete `reconciliation.md` against the current base/cutover tips first. Inspect the full patch, retain the porting log, and report missing provenance, unresolved preservation, or required checks not run as blockers.

## 3. After each PR lands

```bash
git fetch origin
$SKILL/scripts/stack-status.sh <branch>:<target> …
```

1. **PRs whose target was the merged branch:** confirm step 0's retarget happened. On a host that doesn't retarget, retarget each one to the base by hand, after approval.
2. **Bring them up to date** by merging the base: `git merge --no-ff -m "Merge <base> into <branch>" origin/<base>`. Include branches with copied dependencies on the landed slice even if they already target the base; use section 5 for cutovers.
   - After a merge-commit landing, shared ancestry is preserved; newer base or child edits can still cause conflicts.
   - After a squash or rebase landing, the base has the parent's changes under new commits and may include fixes absent from the child's copies. Compare the original/copied patch, newer base changes and the child's own edits; preserve both intents using `reconciliation.md`, rather than choosing a side from line ownership. Inspect relevant clean merges too. Confirm the full diff against the base contains only the child's intended work and explained adaptations. There's no rebase and no force push; the branch history keeps the old commits, and that's fine.
3. Get each push approved and push it. Check each PR's diff is now only its own slice, then carry the merges up the rest of the stack (B4).
4. **Integration branch:** merge the base into it, and get that push approved.
5. If the merge didn't delete the branch, delete it only after no open PR targets it, and after approval.

## 4. When every slice in the integration branch has landed

The integration branch is never merged through a PR, so nothing retargets for it. Retarget the PRs that target it to the base by hand, after approval, check they're still open, and only then delete it.

## 5. A cutover built from the fork point

Once the slices it carries have landed, follow `reconciliation.md`:

1. Recover the copied-dependency map and pin the current source/base/cutover tips. Identify later source-slice review fixes and relevant base changes since the recorded copy baseline, including new callers outside the reference diff. Do not assume copies match the landed content.
2. Merge the pinned base into the cutover if it is not already included, preserving its pre-merge tip for comparison. When resuming a tentative merge, inspect that candidate instead of repeating it. Reconcile stale copies, newer upstream changes and intentional cutover edits at hunk level, even where Git merges cleanly. Preserve documentation and test intent alongside behavior; make pending decisions with the user only where existing authorization does not settle them.
3. Complete the porting log: each relevant upstream change's outcome, current destination and verification. Check current-tree references to removed types/APIs. Run permitted checks and report skipped or unavailable required gates; unresolved items prevent a ready-to-land claim.
4. Review the full cutover diff and update the draft description with the checked tips, map/log location, outcomes and blockers. Get the push and description writes authorized before publishing. Reconcile any later tip changes before relying on this evidence.

## 6. After the last PR lands

1. **Check that the base contains the reference's intended changes**, on the reference's own files. Collect paths using `git diff --name-only --no-renames -z <fork> origin/<reference>`, preserve NUL delimiters, and compare those paths between `origin/<base>` and `origin/<reference>` with a path-safe script. Do not expand the path list through unquoted command substitution. Explain remaining differences as review fixes, follow-up slices, planned exclusions, and the base's own newer changes. Also verify the porting log's outcomes against the landed base, including relevant files outside the reference diff and references to removed APIs; reference equality alone is insufficient.
2. **The reference PR:** report the result and ask the user whether to close it (with a comment listing the slice PRs) or leave it open. Do only what they choose.
3. **Clean up**, within the authorized scope, and only once no open PR targets the branch: remote slice branches and the integration branch, local branches (including `work/` and `parked/`), the slicing worktree (`git worktree remove …`), and its build caches.
4. **Tracker:** after approval, comment with the PR list and move the ticket on.
5. **Final report:** a table of PRs (number, title, merged on), plus anything deferred. Retain the stack map and porting log; include their location, checked SHAs, preservation outcomes and validation limitations in the handoff before deleting worktrees or scratch artifacts.
