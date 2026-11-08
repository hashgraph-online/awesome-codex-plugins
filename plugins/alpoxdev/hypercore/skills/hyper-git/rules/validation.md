# Validation

Run these checks before declaring a change to `hyper-git` complete or before reporting a run of any mode as successful.

## Skill Quality Checks

- The description names the four results (pushed commits, a worktree operation, an issue operation, a branch, pull request, or merge operation) and states every boundary (local commit only, history rewrite, release, CI, container isolation) by the requested result, never by naming another skill.
- `SKILL.md` decides the mode in one table and points each mode at exactly one owning rule: commit -> `rules/commit-and-push-policy.md`, worktree -> `rules/worktree-lifecycle.md`, issue -> `rules/issue-workflow.md`, workflow -> `rules/branch-workflow.md`.
- `assets/evals/hyper-git-cases.jsonl` composes should-trigger, should-not-trigger, boundary, near-miss, safety, adversarial, and regression cases for every mode, plus mode-routing cases; every case states its own `intent`, `runs`, `threshold`, and `metrics`. Add a case only when it probes something the existing cases do not.
- The core stays lean and points to rules and scripts without duplicating them; subagent lane rules live only in `rules/agent-parallelism.md`.
- Script additions are justified by deterministic speed or safety improvements.
- Linked worktrees are valid contexts in every mode: checkout roots stay separate and `.git` is not assumed to be a directory.
- Missing arguments and `current`/`CURRENT` select current-session changes; `all`/`ALL` select every uncommitted change; `&&` targets are validated before mutation.
- Every publishing action (issue create, edit, comment, close, reopen; pull request open; merge into a named branch) is gated on the user's request for that action.

## Runtime Checks: Commit Mode

- `bash -n skills/hyper-git/scripts/git-fast.sh` passes from the repository root.
- `scripts/git-fast.sh inspect . --jobs 2` emits `repos|begin`, `repo-status|begin`, and file inventory blocks; inside a linked worktree it shows `worktree|linked` and a `repo|...` path at the linked checkout root.
- The push helper is not tested against a real remote unless the user asked to push; behavior checks use local fixtures.
- Commits use targeted staging and one logical change each, and messages are English Conventional Commits: imperative subject, lowercase after the colon, no trailing period, at most 72 characters, a blank line before any body, and no sign-off or attribution trailer the user or repository did not request.
- Push runs automatically only after every commit group succeeds; force push stays blocked on `main` and `master`.
- Only commits created by the run reach each `&&` target, in left-to-right order; one mechanical conflict is resolved and validated without asking, while an ambiguous behavior conflict asks one focused question before later targets.
- If subagents were used, their work was read-only and the main integrator alone staged, committed, and pushed.

## Runtime Checks: Worktree Mode

- `git rev-parse --show-toplevel` succeeds and `git worktree list --porcelain` is read before path construction or mutation.
- A direct `hyper-git worktree <ARGUMENT>` creates from the argument without asking what worktree to create; otherwise a missing work intent gets one localized question.
- `.hyper/worktree/` is ignored or locally excluded before nested creation.
- After creation, follow-up commands ran from the new path (persistent `cd` or `workdir=<path>`), and the report says which.
- Removal read `git -C <path> status --short` first, refused the main worktree, and used `--force` only on explicit request; cleanup ran `git worktree prune --dry-run` before `git worktree prune`.

## Runtime Checks: Issue Mode

- `gh auth status` and `gh repo view` succeeded before any issue command, or the run stopped and named the failed check.
- Every published text matches what the report shows, and nothing was published without the user's request for that action.
- No label, milestone, issue number, or owner was invented.
- When a pull request targets a non-default branch, the report says the linked issue stays open.

## Runtime Checks: Workflow Mode

- The default branch, allowed merge methods, and branch list were read before a model recommendation or a merge.
- No merge reached `main`, `master`, the default branch, or a deploy branch unless the user named it; no `--admin`, no bypassed check, no settings change.
- Every merge target fast-forwarded from its remote before the merge, the repository's checks ran on the merged result, and the push output confirms each target.
- Branch and worktree deletion happened only after the merge was confirmed on the remote.

## Readback Checks

Read as:

1. a trigger model: commit-only, conceptual questions, plan execution, and release work do not activate the skill; each activating request lands in one mode.
2. a rushed operator: the fastest safe command for each mode is obvious.
3. a commit reviewer: generated subjects read as English imperative changes.
4. a maintainer: each rule has one home, and a new behavior has an obvious file.
5. a branch operator: `hyper-git && dev`, `hyper-git CURRENT && dev && deploy/staging`, and "merge into dev and main, then push" have unambiguous scope, order, and stop behavior.

## Sources

> No external sources were used. Content checked 2026-11-07.

This rule set is authored in this package from repository practice. It makes no external claim, so no external source is cited.
