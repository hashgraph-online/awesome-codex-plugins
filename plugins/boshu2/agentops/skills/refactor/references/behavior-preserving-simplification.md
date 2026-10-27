# Behavior-Preserving Simplification

Use this reference when `/refactor` is asked to simplify code, remove AI-writing artifacts, reduce indirection, or make a module easier to maintain without changing behavior.

## Contract

The external behavior must remain the same. The refactor `SKILL.md` owns what counts as behavior, the procedure and the report shape. A bug found on the way is reported separately for the caller, not fixed inside the refactor.

## Good Targets

- Redundant branches that return the same result.
- Over-abstracted helpers with one call site.
- Names that hide domain meaning.
- Deep nesting that can become guard clauses.
- Duplicated logic that has the same inputs and outputs, including local code that redoes an existing helper or a standard-library facility (see Substitute Existing Code).
- Comments that narrate obvious code instead of explaining constraints. A comment that a tool reads is code, not prose: build constraints, compiler directives, lint or type suppressions, doctests and generated-file markers stay.
- AI-style verbose prose in docs or comments that can be made precise. User-visible messages are behavior, not prose to tidy.

## Red Flags

- Tests need broad rewrites to pass.
- The new abstraction has no second use or clear contract (the report's `abstraction:` line names it).
- The simplification deletes context that future maintainers need.

---

**Source:** Adapted from an external skill corpus / `simplify-and-refactor-code-isomorphically` and `de-slopify`. Pattern-only, no verbatim text.

## Refactoring Catalog

Use these patterns only after the procedure has recorded a baseline, named the observable behavior, and chosen one transformation.

### Extract Method

Use when a function contains a cohesive block with clear inputs and outputs that reads as one named step.

```text
Before: longFunction() { blockA; blockB; blockC }
After:  longFunction() { doA(); doB(); doC() }
```

Safety checks:

- pass shared locals explicitly or return values;
- preserve error propagation and cleanup order;
- document side effects and mutation ownership;
- reject an extraction that merely moves complexity behind an opaque name.

### Move, or Extract Module or Class

Use when code sits in a module that does not own its concern, a file owns multiple unrelated concerns, or a cohesive type has a stable boundary.

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
- add characterization tests for each moved condition before the change and include them in the step-2 baseline;
- do not replace explicit domain states with a clever boolean expression.

### Reduce Parameters

Use an options or request type when parameters travel together and form one concept.

Safety checks:

- update every caller and preserve defaults;
- distinguish required fields from optional zero values;
- avoid a generic bag that hides unrelated responsibilities;
- preserve public API compatibility or make migration explicit.

### Encapsulate

Use when callers read or write a field or shared state directly and one owner should guard its invariants.

Safety checks:

- find every direct reader and writer, including reflection, serialization and tests;
- keep serialized and persisted names, defaults and zero values unchanged;
- narrowing an exported symbol's visibility is an interface change (SKILL.md, What counts as behavior): keep it reachable or report it.

### Substitute Existing Code

Use when local code redoes what the repository already defines (a helper, constant, enum or type) or what the standard library, runtime or framework provides.

Safety checks:

- find the existing symbol and name it in the report;
- show equivalence for the inputs this code actually receives: ordering of equal elements, locale and case rules, rounding, encoding, and how each value type serializes;
- replace a raw literal with a constant or type only when the emitted value stays identical;
- when a framework or downstream layer already performs a step, delete only that step and keep any transformation it does not do; a protective check (SKILL.md, What counts as behavior) stays even then;
- a branch that a removed guard or filter now lets through is live code; check it rather than treat it as dead.

### Remove Dead Code

Use static analysis plus repository-wide search. For CLI commands, flags, or cross-language surfaces in the AgentOps repository, run the following; elsewhere, search every tracked file with the repository's own tools:

```bash
bash scripts/check-removed-symbol-refs.sh -- <removed-command-or-flag>
```

Safety checks:

- rule out reflection, string dispatch, interfaces, plugins, build tags, generated callers, and external packages;
- search source, shell, workflows, docs, skills, and tests;
- exclude historical release material only when the removal checker documents that policy;
- keep any remaining hit blocking unless an explicit exclusion is justified in the summary;
- an alias, adapter or old field that only bridges a shape from earlier in the current unmerged work is not a public interface when the base branch and every release lack that shape and no dependent branch or stored data uses it. Remove it when every caller update fits the scope; otherwise report it. A shape that ever merged or shipped keeps its compatibility contract.

### Complexity

Cyclomatic complexity is at most a signal inside the area the caller selected, never a reason to pick a target or a success metric. A refactor is better only when the behavior proof remains green and the resulting boundary is easier to understand, test, and change.
