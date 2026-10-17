---
name: wrap-up-branch
description: "Finish a feature branch: add missing tests, review and fix the code, align docs, then merge only after explicit confirmation."
argument-hint: "[target-branch]"
user-invocable: true
disable-model-invocation: true
effort: xhigh
---

# Wrap up branch

Finish the current feature branch so it can land safely.
Invoking the skill authorizes in-scope edits, their commits on the feature branch, and merging the target into the feature branch.
Merging into the target and pushing wait for the final question.
Run the steps in order. Stop on a failed gate.
Each step that changes files ends with `development-skills:commit` and the matching Conventional Commit type.

## 1. Resolve scope

- The feature branch is the current `HEAD`. Stop on a detached `HEAD` or when `HEAD` is already the target.
- The target is `$ARGUMENTS`. Without it, inspect `dev`, `develop`, and `development`; otherwise use the default branch.
- Name `main` or `master` as protected in the final question.
- A dirty working tree needs one decision: commit the listed paths or stop. Never stash without permission.
- Fetch `origin`, then use `git diff <merge-base>...HEAD` as the scope. Keep temporary review files outside the repository.
- Run the project's checks as a baseline. Stop if the branch is already red.
- State the target and merge-base before changing the branch.

## 2. Tests

Invoke `development-skills:create-test` for the branch scope.
Add missing proof for the branch's behavior and relevant rejection, limit, timeout, retry, permission, concurrency, and partial-failure cases.

Judge proof by failures caught, not counts.
A new failing test exposes a defect. Fix it only when the fix stays inside branch scope; otherwise stop and report it.
Run focused tests, then project checks.

## 3. Review and fix

Invoke `development-skills:staff-review` on the merge-base range.
Provide the plan, issue, or pull request description as the requirement when available.
Fix every `MISSING` or `EXTRA` finding and every CRITICAL or HIGH quality finding.
Report MEDIUM and LOW findings unchanged.
Run affected checks and re-review the fix diff. Stop after three failed fix rounds or a conflict with an existing decision.

## 4. Documentation

Invoke `development-skills:align-docs` with the branch scope.
When the repository has a `CHANGELOG.md`, invoke `development-skills:changelog` in `from-commits` mode.

## 5. Bring the target into the branch

Merge `origin/<target>` or the local target into the feature branch first.
On conflict, invoke `development-skills:resolve-merge` and complete the merge commit it prepares.
Run project checks on the merged tree. Stop on failure.

## 6. Merge

Present the target and protection, added commits, checks, review verdict, remaining findings, and documentation changes.
Then ask once: `Merge`, `Merge and push`, or `Stop`.

On `Merge` or `Merge and push`:

1. Check out the target and update it with `git merge --ff-only origin/<target>` when a remote exists.
2. Stop if the local target diverged.
3. Run `git merge --no-ff <feature-branch>`.
4. On `Merge and push`, run `git push origin <target>`. Never force a rejected push.

Leave the feature branch in place. Deletion is the user's choice.

Report the result, commits, checks, open findings, and evidence limits.
Translate platform tools with [Codex tools](../using-development-skills/references/codex-tools.md).
