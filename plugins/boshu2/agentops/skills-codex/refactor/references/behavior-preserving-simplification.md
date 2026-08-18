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

## Refactoring Catalog

Use these patterns only after the kernel has established a green baseline, an observable behavior contract, and an atomic transformation plan.

### Extract Method

Use when a function exceeds roughly 30 lines or contains a cohesive block with clear inputs and outputs.

```text
Before: longFunction() { blockA; blockB; blockC }
After:  longFunction() { doA(); doB(); doC() }
```

Safety checks:

- pass shared locals explicitly or return values;
- preserve error propagation and cleanup order;
- document side effects and mutation ownership;
- reject an extraction that merely moves complexity behind an opaque name.

### Extract Module or Class

Use when a file owns multiple unrelated concerns or a cohesive type has a stable boundary.

Safety checks:

- map imports before moving code and reject circular dependencies;
- expose package-level state deliberately rather than duplicating it;
- preserve initialization order, registration, reflection, and serialization names;
- run callers in every affected package, not only the extracted unit.

### Rename

Use when a name is misleading, ambiguous, or hides domain meaning.

Safety checks:

- use language tooling where available and search every tracked reference;
- include strings, configuration, docs, tests, generated surfaces, and scripts;
- treat exported symbol, CLI, JSON, database, metric, and event names as public API;
- avoid preference-only churn that does not improve comprehension.

### Inline

Use when a single-use helper or temporary adds indirection without a contract.

Safety checks:

- preserve evaluation count and order;
- make sure the inlined expression has no hidden side effect;
- reject inlining that duplicates behavior or makes the caller harder to test.

### Simplify Conditional

Use guard clauses, early returns, or table-driven logic when nesting obscures mutually exclusive behavior.

```text
if err == nil: succeed and return
if not retryable or attempts exhausted: fail and return
retry
```

Safety checks:

- preserve branch priority, error identity, logging, and side-effect order;
- add boundary tests for every moved condition;
- do not replace explicit domain states with a clever boolean expression.

### Reduce Parameters

Use an options or request type when more than four parameters travel together and form one concept.

Safety checks:

- update every caller and preserve defaults;
- distinguish required fields from optional zero values;
- avoid a generic bag that hides unrelated responsibilities;
- preserve public API compatibility or make migration explicit.

### Remove Dead Code

Use static analysis plus repository-wide search. For CLI commands, flags, or cross-language surfaces, run:

```bash
scripts/check-removed-symbol-refs.sh -- <removed-command-or-flag>
```

Safety checks:

- rule out reflection, string dispatch, interfaces, plugins, build tags, generated callers, and external packages;
- search source, shell, workflows, docs, skills, Codex skills, and tests;
- exclude historical release material only when the removal checker documents that policy;
- keep any remaining hit blocking unless an explicit exclusion is justified in the summary.

### Complexity Interpretation

| Cyclomatic complexity | Interpretation |
|---:|---|
| 1–5 | Simple; usually leave alone |
| 6–10 | Manageable |
| 11–20 | Refactor candidate |
| 21–30 | Urgent |
| 31+ | Critical; split carefully |

Complexity is a targeting signal, not a success metric by itself. A refactor is better only when the behavior proof remains green and the resulting boundary is easier to understand, test, and change.
