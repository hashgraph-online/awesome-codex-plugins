# Verification policy

Verification should match risk and changed surface.

## Level 1 — touched-file checks

Examples: formatter, syntax parser, compile one target, schema validate one file.

## Level 2 — focused behavior checks

Run the closest unit/component/integration test for the changed behavior.

## Level 3 — package checks

Run package-level typecheck/lint/test when shared contracts or dependencies changed.

## Level 4 — full-suite checks

Use for cross-cutting changes, migrations, release gates, or when package checks reveal hidden coupling.

## Retry policy

When a check fails:

1. inspect the exact failure,
2. patch the likely cause,
3. rerun the smallest failing check,
4. only return to broad checks after focused success.

Do not rerun an expensive full suite after each small patch.
