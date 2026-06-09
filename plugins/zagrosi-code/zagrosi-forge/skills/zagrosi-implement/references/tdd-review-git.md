# TDD, Review, and Git Protocol

## TDD

1. Read the section and identify expected behavior.
2. Create skeleton files only when needed for imports.
3. Write tests first.
4. Run the smallest meaningful test command and confirm failure.
5. Implement the behavior.
6. Run targeted tests until passing.
7. Run the configured full test command when practical.

If tests cannot be written first because the repo lacks test infrastructure,
create the minimum test harness or document the blocker before implementation.

## Review

Review staged changes against the section:

- missed requirements
- incorrect edge cases
- security or authorization gaps
- data loss and migration risks
- brittle tests
- unnecessary scope expansion
- inconsistency with repo patterns

Save review artifacts under `implementation/code_review/`.

## Git

Use one commit per section. Stage intentionally:

```bash
git add <section files>
git diff --cached
git commit
```

If hooks modify files, inspect the changes, rerun tests as needed, re-stage, and
commit again. If hooks fail, ask the user whether to fix, stop, or explicitly
skip hooks.
