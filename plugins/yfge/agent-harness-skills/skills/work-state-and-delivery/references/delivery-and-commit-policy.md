# Delivery And Commit Policy

Use this when a repository needs durable links among tracked work, logical commits, reviews, handoffs, and delivery artifacts.

## Commit Policy

- One commit should express one logical purpose.
- Read `git status`, relevant unstaged diffs, and staged diffs before committing.
- Stage exact paths in mixed worktrees; do not use `git add .` by default.
- Include a tracked task-state update when the same change completes, changes, or invalidates that task.
- Use the repository's subject format; prefer Conventional Commits only when no stronger local convention exists.

## Delivery Coupling

- Choose an advisory, commit-coupled, review-coupled, task-linked, or gate-coupled policy based on audit need.
- Delivery evidence should name goal, changes, validation, artifacts, risks, and linked tasks or commits.
- Review and handoff notes must not claim validation absent from the underlying record.
- Skips must be explicit and searchable; emergency skips need a follow-up owner or task.

## Artifact Evidence

- Record an artifact identity such as version, tag, package, bundle, run ID, or report path.
- Include build and validation commands plus result classification.
- Link large artifacts by stable path or run ID instead of committing them by default.
- Include rollback or follow-up notes when delivery can affect users.

## Validation

- Confirm staged paths match one logical purpose and exclude unrelated work.
- Confirm task state, review notes, and delivery evidence agree with the actual change.
- Confirm artifacts are reproducible from committed sources and documented commands.
- After a commit, inspect its stat and the remaining worktree state.

## Do Not Include

- Silent skips, vague commit subjects, or claims without artifact identity.
- Unrelated formatting, generated caches, or local-only build products.
- Two active ledger formats without a deprecation rule.
