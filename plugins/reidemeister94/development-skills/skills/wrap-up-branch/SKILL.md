---
name: wrap-up-branch
description: "Use when the user asks to finish a feature branch: missing regression tests, review fixes, docs, and the merge into dev or the given target."
argument-hint: "[target-branch]"
user-invocable: true
disable-model-invocation: true
effort: high
---

# Wrap up branch

Finish the feature branch on the current checkout so it can land safely.
Invoking the skill authorizes the in-scope edits, their commits on the feature branch, and the merge of the target into the feature branch (step 5).
The merge into the target and any push wait for the final question (step 6).
Run the steps in order. A failed gate stops the run with a report, because a merge with red checks or open findings moves the problem to the whole team.
Each step that changes files ends with `development-skills:commit` and a Conventional Commit type that matches it: `test`, `fix`, `docs`, `chore`.

## 1. Resolve the branch, the target, and the scope

- The feature branch is the current `HEAD`. Stop on a detached `HEAD` or when `HEAD` already is the target.
- The target is `$ARGUMENTS`. Without it, look for `dev`, `develop`, and `development` locally and on `origin`: one candidate is the target; several candidates need one question; none means the default branch.
- Name a `main` or `master` target as protected in the final question; the answer there is the explicit confirmation those branches require.
- A dirty working tree stops the discovery: ask once whether to commit the listed paths onto the branch or stop. Never stash on the user's behalf.
- Run `git fetch origin`, then take the scope as `git diff <merge-base>...HEAD` with `git merge-base origin/<target> HEAD` (the local target when no remote exists). Save the diff and the commit list in a temp directory outside the repository. Every following step receives this scope, not the whole repository.
- Run the project's own checks (tests, lint, type checks from its Makefile, `pyproject.toml`, or `package.json`) as the baseline. A red baseline stops the run: the branch must be green before anything is added to it.
- State the resolved target and merge-base in chat before step 2, so the user can interrupt before step 5 changes the branch.

## 2. Tests

Invoke `development-skills:create-test` in implementation mode with the branch scope.
Ask it for the regression proof the branch's new behavior still lacks. Include the failure and boundary cases the diff crosses:

- rejection and empty input;
- limits, timeout, and retry;
- permission, concurrency, and partial failure.

Judge the result by failures caught, not by counts. When the project runs a coverage tool, report the coverage of the changed files before and after, without chasing a number.
A new test that fails against the branch reveals a defect. Fix it when the fix stays within the branch scope; otherwise stop and report it, because widening the branch is the user's decision.
Run the focused tests, then the project checks.

## 3. Review and fix

Invoke `development-skills:staff-review` on the merge-base range. Give it the linked plan, issue, or pull request description as the requirement when one exists; otherwise it skips the specification verdict.
Fix every `MISSING` or `EXTRA` specification finding and every CRITICAL or HIGH quality finding with the [severity scale](../../shared/review-categories.md). Report MEDIUM and LOW findings unchanged.
Fix a CRITICAL or HIGH design finding when it stays within the branch's requirement; bring one that challenges the requirement or a plan decision to the user with its alternative.
Run the affected checks, then re-review the fix diff with the prior findings. Stop and ask after three fix rounds, or when a finding conflicts with a decision the branch already made.

## 4. Documentation

Invoke `development-skills:align-docs` in normal mode with the branch scope as task context. It repairs the entry layer, routes, plans, and chronicles the change invalidates, and archives a plan the branch completed.
When the repository keeps a `CHANGELOG.md`, invoke `development-skills:changelog` in `from-commits` mode for the branch commits.

## 5. Bring the target into the branch

Merge `origin/<target>` (or the local target) into the feature branch first. Conflicts then get resolved on the feature branch, and the checks run on the exact tree that will land.
On a conflict, invoke `development-skills:resolve-merge`; complete the merge commit it hands off. A skipped conflict stops the run.
Run the project checks again on the merged tree. A failure stops the run.

## 6. Merge

Present the summary in chat:

- the target and its protection;
- the commits this run added;
- the checks run and their result;
- the review verdict and the remaining MEDIUM and LOW findings;
- the documents changed.

Then ask once with the question tool: `Merge`, `Merge and push`, or `Stop`. Printing the options in chat does not count as asking.

On `Merge` or `Merge and push`:

1. Check out the target; create it from `origin/<target>` when it exists only there. Update it with `git merge --ff-only origin/<target>` (skip without a remote). A diverged local target stops the run.
2. Run `git merge --no-ff <feature-branch>`. The merge commit keeps the feature as one unit that one revert can undo.
3. On `Merge and push`, run `git push origin <target>`. A rejected push, such as branch protection, is reported with the pull request alternative; never force it.

Leave the feature branch in place: deleting it is the user's choice.

## Report

Lead with the result: merged and pushed, merged locally, or stopped at which gate and why.
Then list the commits added, the checks with their evidence, the findings left open, and what the run did not verify.

On Codex, translate skill and question tools with [codex-tools.md](../using-development-skills/references/codex-tools.md).
