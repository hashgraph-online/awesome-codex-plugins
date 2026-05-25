# Behavior-Preserving Simplification

Use this reference when `/refactor` is asked to simplify code, remove AI-writing artifacts, reduce indirection, or make a module easier to maintain without changing behavior.

## Contract

The external behavior must remain the same. If you discover a bug, file or switch to a bug-fix task instead of hiding the behavior change inside the refactor.

## Good Targets

- Redundant branches that return the same result.
- Over-abstracted helpers with one call site.
- Names that hide domain meaning.
- Deep nesting that can become guard clauses.
- Duplicated logic that has the same inputs and outputs.
- Comments that narrate obvious code instead of explaining constraints.
- AI-style verbose prose in docs or messages that can be made precise.

## Required Loop

1. Establish a green baseline.
2. Identify the exact behavior contract and tests that protect it.
3. Make one simplification.
4. Run focused tests immediately.
5. Keep the change only if behavior is unchanged and readability improves.
6. Record the simplification in the refactor summary.

## Red Flags

- The diff changes outputs, error messages, ordering, timing, or persistence.
- Tests need broad rewrites to pass.
- The new abstraction has no second use or clear contract.
- The simplification deletes context that future maintainers need.

## Summary Addendum

```markdown
## Simplification Checks

| Check | Result |
|---|---|
| Behavior unchanged | PASS/FAIL |
| Focused tests passed | PASS/FAIL |
| New abstraction justified | yes/no |
```

---

**Source:** Adapted from an external skill corpus / `simplify-and-refactor-code-isomorphically` and `de-slopify`. Pattern-only, no verbatim text.
