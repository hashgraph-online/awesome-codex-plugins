---
name: staff-review
description: "Use when user wants a code review, deep code review, or staff-level code review of a local branch, repo, directory, or file. Use when user says code review, deep code review, review this branch, review the branch X, review my code, staff review, review locally, or /staff-review."
user-invocable: true
effort: max
---

# Staff Review

Run a staff-level code review:

1. Work out what to review from what the user wrote after `/staff-review` (a branch, files, "my uncommitted changes", a module…). If they wrote nothing, ask them.
2. Find and read the plan (`docs/plans/`) or chronicle (`docs/chronicles/`) tied to that work, if one exists.
3. Dispatch the `development-skills:staff-reviewer` subagent on that scope, applying every Iron Rule — the goal is to simplify and find the best approach.
4. If anything is doubtful or ambiguous, use the other available skills to do additional online researches (e.g. official docs, libraries, github projects, articles, ...) to verify before concluding.
5. Findings grouped CRITICAL / HIGH / MEDIUM / LOW, each with `file:line` and `Fix: <action>`, then a 1-2 sentence summary. Actionable findings only — no praise, no filler.

## Critical Rules

- **No Mercy, but constructive**: every finding ends with a real improvement fix
- **Independence**: The diff (or in-scope code) is the artifact; patterns + Iron Rules are the contract. Don't validate the author's PR description, the orchestrator's summary, or a passing CI line — decide independently whether the artifact satisfies the contract.
