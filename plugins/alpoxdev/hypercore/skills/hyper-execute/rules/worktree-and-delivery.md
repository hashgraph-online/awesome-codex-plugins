# Worktree And Delivery

Use this rule file before creating the first wave worktree, before landing a wave, and before cleanup. It owns the integration base, the worktree lifecycle, landing, the three delivery modes, and cleanup. Selection and dispatch live in `rules/execution-loop.md`; gates and verdicts live in `rules/verification-gates.md`.

## 1. Record The Integration Base

At phase 0, record the branch checked out in the main worktree as `integration_base`, with its commit sha, in `state.json`.

- Every wave branches from the base recorded for that wave, and a local wave lands back onto `integration_base`.
- A detached HEAD is recorded by sha, with a warning in the completion block: later merges have no branch to advance.
- The base never changes mid-run. If the user moves it, stop and ask once whether to reset the run's base or restart.

## 2. Create The Wave Worktree

One worktree per wave, at a fixed place and on a fixed branch:

```bash
git worktree add -b hyper/<slug>/w<N> <repo-root>/.hyper/worktree/<slug>-w<N> <wave_base>
```

- Path: `<repo-root>/.hyper/worktree/<slug>-w<N>`. Branch: `hyper/<slug>/w<N>`.
- `<repo-root>` is the main checkout's absolute path, the same value recorded as `main_root`.
- Before the first worktree, run `git check-ignore -q --no-index .hyper/`. A non-zero exit means `.hyper/` is not ignored: add one `.hyper/` line to the repository root `.gitignore` (create it when absent) and record that edit as part of this run. Never un-track files already committed under `.hyper/`.
- A wave that runs parallel lanes uses one worktree per lane at `<repo-root>/.hyper/worktree/<slug>-w<N>-l<M>`, on branch `hyper/<slug>/w<N>-l<M>`, created from the same `<wave_base>`.
- `<wave_base>` is the branch this wave starts from, and it is recorded per wave in `state.json` as `wave_bases`:

| Wave | Base |
|---|---|
| Wave 1 | `integration_base` |
| Lane `M` inside wave `N` | the wave's own base, never another lane's branch |
| Wave `N+1` under `local` | `integration_base`, already holding wave `N` |
| Wave `N+1` under `--make-pr` | `hyper/<slug>/w<N>`, the previous wave's pull-request branch |
| Wave `N+1` under `--ship` | `integration_base`, only after wave `N`'s pull request merged |

- Verify with `git worktree list --porcelain` before dispatch, and store the absolute path in `state.json` as `worktree_path`, or the per-lane paths as `lane_worktrees`.
- With `--worktree <absolute-path>`, verify the path appears in that porcelain output and sits on a branch owned by this slug. Never create, move, or repurpose a worktree the user pointed at. A path that is not a worktree, or is on another branch, is a stop.

## 3. Work Inside Only

- Every edit, command, test, and evidence capture runs with the wave worktree as the working directory.
- The main checkout carries exactly three writes for this run: the landing merge, `.hyper/` state and ledger files, and the plan checkbox flips. Implementation and review never happen there, and no other path in it is written.
- The plan, state, ledger, and evidence paths always resolve against `main_root`, the main checkout's absolute path recorded in `state.json`. `.hyper/` may be gitignored and absent inside a worktree, so never resolve those paths relative to the worktree.
- Record the main checkout's `git status --porcelain` output at the start. Never stash, reset, checkout, or clean it. If it changes during the run, list the changed paths in the completion block and attribute nothing to this run.
- Stage only the paths named in the row's `Write scope`, in the worktree and in the main checkout alike. Never `git add -A`, `git add .`, or `git commit -a`.
- A linked worktree is an isolation convenience, not a security boundary. Do not treat it as protection against a hostile repository.

## 4. Non-Git And In-Place

- Not a git repository and no `--in-place`: stop and report that a worktree cannot be created. Do not initialize a repository.
- Not a git repository with `--in-place`: work in the current directory, record `isolation: in-place (no vcs)` in `state.json`, skip branch, landing, and cleanup steps, and name the caveat in the completion block. Every other rule stands, including evidence capture.
- A git repository with `--in-place`: first run `git status --porcelain`. A non-empty result stops the run before any work, with the dirty paths reported; never stash, reset, or revert them to make room. On a clean checkout, work in place, land by committing on the current branch with the declared `Write scope` paths staged, skip worktree creation and removal, and record the reduced isolation in the completion block.

## 5. Land The Wave

Land once, when every row in the wave is `[x]` or `[~]`, every verdict is `confirmed` or the row is `[~]`, and every cleanup receipt exists.

1. Revert each `[~]` row's unverified changes inside the wave worktree: restore tracked files and remove files that row created. Record the revert in that row's `Unmet:` line.
2. Commit the remaining changes in the worktree, staging only the declared `Write scope` paths, with one commit per plan `Commit:` line where the rows are separable.
3. Under `local`, check the main checkout is clean and on `integration_base`. If it is dirty, stop and report the dirty paths; do not stash and do not merge.
4. Under `local`, land by the landing policy: `merge` uses the repository's merge policy, defaulting to `--no-ff`; `cherry-pick` applies the wave's commits in order onto `integration_base`. Record the landed sha, or shas, in the ledger against the wave's base.
5. Under `--make-pr` and `--ship`, a wave lands by opening its pull request, and under `--ship` by merging it; the next wave's base follows the table in section 2. Never merge a `--make-pr` wave into the integration base.
6. Only the orchestrator merges. Workers never merge, never push the base, and never resolve a sibling's conflict.
7. When the wave ran in parallel lanes, land the wave in two steps: cherry-pick each lane's commits onto the wave branch in the lane order recorded in `state.json`, then land the wave branch by the policy in force. A lane whose cherry-pick conflicts is paused; the orchestrator resolves it, reruns that lane's affected gates, and records the extra verification. Never drop a lane's commits to avoid a conflict.

A merge conflict is the orchestrator's job. Resolve it in the wave branch, rerun the affected gates, and record that the landing preceded a fresh verification.

## 6. Deliver

| Mode | Actions |
|---|---|
| `local` (default) | Commit on the wave branch, land into the integration base locally by the landing policy, no push |
| `--make-pr` | Push the wave branch and open a pull request against that wave's base, naming the plan, the rows, and the evidence paths; hand off the URL; do not merge |
| `--ship` | Everything in `--make-pr`, then watch CI and review, fix inside the worktree with fresh QA evidence, push again, and merge per the repository's policy when green; wave `N+1` opens only after wave `N` merged |

### Landing policy

`--land <merge|cherry-pick>` selects how a wave's commits reach `integration_base`. The default is `merge`.

| Policy | When to use it | What it records |
|---|---|---|
| `merge` (default) | The integration base is the only target and its history should show the wave as one merge | The merge commit sha as the landed sha |
| `cherry-pick` | The same commits must also reach other branches, or the base must stay linear | Each cherry-picked sha, in order, as the landed shas |

Under `cherry-pick`, never test the wave branch tip for ancestry: the picked commits are new objects, so test each landed sha instead.

- Push and pull-request creation happen only under `--make-pr` or `--ship`. No flag means nothing leaves the machine.
- Under `--make-pr`, waves stack. Wave `N+1` branches from `hyper/<slug>/w<N>` and its pull request targets that branch, while the first pull request targets the integration base. Never branch wave `N+1` from an integration base that does not contain wave `N`, and record every wave's base in `wave_bases`.
- Under `--ship`, wave `N+1` does not open until wave `N`'s pull request merged, so its base is the updated integration base. The CI cap below still bounds the wait.
- CI repair rounds are capped at 3 per pull request. A round is one fix plus fresh QA evidence plus a push, and it does not count against row attempts. On the third round that is still red, stop with the pull-request URL, set `ci: failing` in `state.json`, and report it in the completion block.
- Never force-push. A rejected push is reported with the remote's message, not overridden.
- Never push the integration base directly.
- `--ship` when the runtime offers no CI or review watch capability: record `ci: unverified` in `state.json`, stop with the pull-request URL, and say plainly that green was not observed. Do not claim a merge you did not make.
- One pull request per wave by default. When the repository expects one pull request per run, keep the wave branch open, extend it, and open the pull request at the last wave; record the choice.

## 7. Clean Up After A Confirmed Landing

Only after the landing is confirmed on the wave's own base - a local merge, or a merged pull request:

1. Copy the wave's evidence into `.hyper/execute/<slug>/evidence/` under `main_root`, and confirm the copies exist.
2. `git worktree remove <path>` without `--force`.
3. If the removal is refused because of dirty, untracked, or locked state, stop and report the paths. Keep the worktree. Never escalate to `--force`.
4. Delete the branch only after confirming the landed commit is on that wave's base: for a local wave the integration base, for a stacked wave its parent wave branch. Under the `merge` policy test it with `git merge-base --is-ancestor <landed-sha> <wave_base>`; under `cherry-pick` test each picked sha with `git merge-base --is-ancestor <landed-sha> <base>`; never test the wave branch tip, which is not an ancestor after a pick. After a squash merge the branch tip is not an ancestor, so confirm the merge on the base by the landed commit or the pull request's merged state instead. Never use `git branch --merged` as the test.
5. Delete the remote branch only when it was pushed and its pull request is merged.
6. Remove `<repo-root>/.hyper/worktree/` when it is empty; keep the rest of `.hyper/`.
7. Append a `cleanup` ledger row with each path and branch removed, and each item kept with its reason.

## 8. Failure Handling

| Symptom | Response |
|---|---|
| `git worktree add` fails | Report the git error verbatim and stop; do not fall back to editing the main checkout |
| The `--worktree` path is not listed, or is on another branch | Stop and report the mismatch |
| The main checkout is dirty at landing | Stop; list the dirty paths; leave them untouched |
| The main checkout is dirty before `--in-place` | Stop before any work; list the dirty paths; never stash or revert them |
| Merge conflict | Resolve in the wave branch, rerun the affected gates, record the extra verification |
| Push rejected | Report the remote message; never force-push |
| CI red | Fix inside the worktree, produce fresh QA evidence, push again; count a CI repair round, not a row attempt |
| CI red after three repair rounds | Stop with the pull-request URL, set `ci: failing`, and report it in the completion block |
| `git worktree remove` refused | Keep the worktree and stop; never use `--force` |
| The landed commit cannot be found on the base | Treat the landing as unconfirmed, keep the worktree, and report |
| A lane cherry-pick conflicts | Pause that lane, resolve in the wave worktree, rerun the lane's affected gates, record the extra verification |

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| Per-wave worktrees, the branch naming, landing on an integration base, the three delivery modes, and cleanup without `--force`, adapted from the `ulw-execute` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| A linked worktree is not a security boundary | `instructions/autoresearch/references/safety-and-observability.md` |
| A stop condition needs an observable check, and a failed guard stops rather than escalates | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| Keep the parent as the only integrator, with the parent verifying the join | `instructions/context-engineering/references/parallel-workflows.md` |

### Evidence grade

`LOCAL` - this file states this package's own procedure, adapted from the upstream skill named above. The default `--no-ff` merge, the one-pull-request-per-wave default, and the branch-deletion test after a squash merge are this package's choices, made so that a squashed landing cannot leave a branch that looks unmerged.
