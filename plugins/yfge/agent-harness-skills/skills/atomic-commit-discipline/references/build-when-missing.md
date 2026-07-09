# Build When Missing

Use this when a repository has no commit discipline beyond informal convention. Pattern sources include Conventional Commit policies, exact-path staging rules, task-state coupling, ledger coupling, and validation-before-commit checklists.

## Equivalent Artifacts

- Contributor guides, pull request templates, protected-branch rules, or existing release policies may already satisfy parts of the commit discipline role.
- Record the chosen artifacts under `Detected Mapping` before adding new policy text.
- Add default policy sections only where no equivalent rule exists.

## Minimum Files

- Commit policy section in `AGENTS.md`, `CONTRIBUTING.md`, or an explicitly mapped equivalent.
- Task-state policy section in the mapped work-state surface or planning documentation.
- Optional `.github/pull_request_template.md`.
- Optional `docs/commit-checklist.md` if the policy is too long for the entrypoint.
- Optional CI commit-message or ledger-coupling checker.

## Bootstrap Steps

1. Map existing commit, review, and task-state rules.
2. State only the missing commit rules: one logical purpose per commit and exact-path staging.
3. Require reading `git status`, `git diff`, and `git diff --cached` before staging.
4. State the task coupling rule: when a commit completes, changes, or invalidates a tracked task, include the task-state update in the same logical commit.
5. Define the commit subject format, preferably Conventional Commits when no repository format exists.
6. Define minimum validation evidence for docs, tests, implementation, harness, task-state, and ledger changes.

## Validation

- Before commit, confirm staged files match one logical group.
- Confirm task-state updates are included only when related to that logical group.
- Run the minimum validation command for that group.
- After commit, run `git show --stat --oneline HEAD` and `git status --short`.

## Do Not Include

- Permission to use `git add .` by default.
- A rule that every commit must have a task entry unless the repository explicitly requires it.
- Commit messages such as "fix" or "update" without behavioral detail.
- Rules that allow unrelated user changes to be staged silently.
