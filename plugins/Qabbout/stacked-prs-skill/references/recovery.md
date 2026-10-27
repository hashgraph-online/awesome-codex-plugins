# Recovery

The rules still apply here: no force-push, no rebase of a pushed branch, and every push approved (`safe-push.sh`'s plan shown to the user first).

## Push refused: the remote has commits you don't have

Someone else pushed to the branch.

```bash
git fetch origin <branch>
git log --oneline HEAD..origin/<branch>
git merge --no-ff -m "Merge origin/<branch> into <branch>" origin/<branch>
```

Run the checks again, then run a new `safe-push.sh` dry run and get a new approval.

## Push refused: HEAD or the remote moved since the approval

`safe-push.sh` refuses a stale plan when its preflight observes that HEAD, the push destination, or the remote branch has moved. Run the dry run again, show the new plan, and obtain any missing authorization. A concurrent remote update after preflight is still possible; the source commit is pinned and the server's normal non-fast-forward checks apply.

## The test run "passed" but ran nothing

Signs of this:
- the exit code was 0 only because of a pipe
- zero tests, or an unknown status
- no pass marker
- the log ends early

Common causes are a full disk, a stale generated project (missing input files), a target or filter typo, and a simulator, device, or service that failed to start. Find the first real `error:` in the raw log, fix the cause, and run it again. Never push on a run like this.

## Stale generated project

Missing input files or missing-symbol errors right after a branch switch mean the generated project still lists files from the previous branch. Regenerate with the generator directly (`tuist generate --no-open`, `xcodegen`, `cmake`, codegen). Then check that the missing path is gone from the generated project before rebuilding.

## Disk full

Check `df -h` first. Then list the biggest folders and what each belongs to:

- Build caches: Xcode DerivedData (`info.plist` → `WorkspacePath` names the checkout), `node_modules/.cache`, `target/`, `.gradle`, `build/`.
- Old worktrees: `git worktree list`. `git worktree prune` only clears records of worktrees that are already gone; it frees no space.
- Simulators, emulators, device support files, and package caches.

Show the user a table (size, what it is, what happens if it's deleted) and delete only what they choose.

## Cherry-pick conflict

Resolve by keeping both intents, then run `git cherry-pick --continue`. If the branch has rewritten that code entirely, write the fix again in its terms as a separate commit, and record the original change, destination and checks in the porting log (`reconciliation.md`). To back out, run `git cherry-pick --abort`. A cherry-pick that needed conflict fixes shows as "probably" (or "no") in `stack-status.sh -c`; inspect the current result rather than treating history as proof of preservation.

## A parent PR was merged (or squash-merged) into the base

Follow `landing.md` steps 0 and 3: check target dependents were retargeted and are still open (retarget by hand, with approval, where the host didn't), and include copied dependents even if their targets did not change. Merge the base into them, reconcile newer upstream fixes with each child's intentional edits, and inspect the full PR diff. Use `reconciliation.md` for copied slices or ports; neither side wins automatically. Get the pushes approved and carry updates through both kinds of dependency. There's never a rebase or a force push.

## Copied slices are stale or their provenance is missing

Recover the original-to-copy map and historical baseline from available commits, patches and landing evidence (`stack-map.md`). Mark unavailable facts unknown rather than guessing from subjects or substituting the current base. Use `reconciliation.md` to inventory relevant review/base changes, adapt their intent and check removed-API references, including new base files. Record each outcome and actual evidence in the porting log. A clean merge or reduced-coverage `split-coverage.sh -i` run cannot close these items; keep unresolved preservation and missing validation visible as readiness blockers.

## A branch was pushed before its checks finished

Tell the user straight away. Run the checks on the pushed commit. If they fail, push a fix on top, with approval. Don't revert anything without the user's agreement.

## Something besides your fix makes the checks fail

Run the same suite on the commit before yours. If it fails there too, the failure isn't from your fix. Report it separately and leave it out of the fix commit.

## A local branch diverged from its remote

Stop and show the user both sides (`git log --oneline origin/<b>...<b> --left-right`). Usually the fix is to merge the remote into the local branch, then run a dry run and get approval. Never overwrite the remote.
