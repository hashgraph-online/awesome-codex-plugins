# Existence Ladder

Read this before choosing what an in-scope unit becomes. It owns the four rungs, the order they are tried, and the proof that a unit earns deletion.

## 1. Four Rungs, In This Order

Every in-scope unit takes the highest rung it can prove, and the ladder is tried from the top.

| Rung | Decision | Proof it needs |
|---|---|---|
| 1 | Delete | nothing reaches the unit, or a keeper already owns its contract |
| 2 | Reuse | an existing helper, module, or pattern in this repository does the same job |
| 3 | Use the platform | the standard library, a native primitive, or an already-installed dependency covers it |
| 4 | Simplify in place | none of the above applies; the unit stays and only its body changes |

Rung 1 is the only rung that removes behavior, so it carries the heaviest proof. Rungs 2 and 3 remove code by replacing it, and rung 4 is the default for everything that survives.

The ladder is not a quota. A file that reaches rung 4 for every unit is a normal outcome, and a run that deletes nothing is a valid run.

## 2. Rung 1: Deletion

Deletion needs an authority, not an opinion.

- **No reference.** A repository-wide search for the definition, the call form, the string form of the name, and the build entry points returns nothing. The search covers generated code, templates, configuration keys, and test fixtures.
- **A keeper owns the contract.** When a test or a call path duplicates another, the stronger one stays and the weaker one goes. The report names the keeper.
- **Never reached.** A branch whose condition cannot hold for any input the owner accepts, proven from the caller's own type or validation.

A user-visible behavior is not speculative because you would not have written it. A public export, a documented flag, a supported platform path, and a script someone may run by hand are all live until a reference search says otherwise.

Deleting a file also removes its imports, its test references, its documentation links, and its configuration entry. A half-deleted unit is a broken build; finish the cut in one pass or do not start it.

## 3. Rung 2: Reuse

Before writing a replacement body, search for one that already exists.

- The same operation under another name in a shared module
- A helper in the same layer that takes one more parameter
- A pattern the codebase repeats deliberately, whose shape the new code should copy

Reuse means the caller reads the same operation it read before. If adopting the shared helper makes a call site need three lines of adaptation, the shared helper is not the same job, and the unit stays at rung 4.

Reuse never widens a public signature and never adds an optional parameter to a shared helper so one caller can use it. That is a new abstraction with a real cost, and it belongs in a separate change.

## 4. Rung 3: The Platform

The standard library, the language primitive, or a dependency the project already installs usually covers more than hand-written code does.

- A hand-rolled retry loop where the language has one
- A path join built from string concatenation where the platform has a join
- A custom parser for a format the runtime already reads
- A vendored helper for a function the already-installed dependency exposes

A native replacement must preserve the observable contract, including error behavior and the supported environment. A platform call that raises where the hand-written one returned a default is not equivalent, and the swap is not authorized.

Installing a new dependency is never a rung. The ladder moves toward less code with the same dependencies, and a new package is a decision outside a behavior-preserving cleanup.

## 5. Rung 4: Simplify In Place

Everything that survives keeps its place and its signature. Only the body changes, and only within the categories that [categories.md](categories.md) proves safe.

Simplify in place is where most of a healthy cleanup lands: an early return instead of a nested block, a guard that becomes a named predicate, a loop that reads in one pass, a duplicated literal that becomes a constant in the same file.

## 6. Record The Rung

The report gives one line per in-scope unit, with the rung and the reason. Rung 1 and rung 2 lines also name what proved them, because those are the two rungs a reviewer will challenge.

```text
path/to/file.ts:42  rung 4  nested ternary flattened to if/else; same branches, same order
path/to/helper.ts:8 rung 1  no reference in code, templates, config, or tests; keeper: tests/owner.spec.ts
```

A unit that was considered and left alone is recorded too, with the reason it stayed. The report is the record of the decisions, not only of the edits.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The deletion ladder: delete when unused or already owned, then reuse an existing helper, then the standard library or an installed dependency, then simplify in place | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| A user-visible existing behavior is not speculative just because the agent would not have written it | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| A native replacement must preserve the observable contract, accessibility, and supported environment | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| A test deletion requires a named keeper or a class proof | `dbc-hbin/omp-ulw@74df40f programming/references/testing/junk-classes.md` (mechanism reference, re-authored) |
| The four-rung reporting shape | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - the rung numbering, the rung-4 default, and the rule that a unit considered and kept is still reported are this package's design. The ladder order and the "no new dependency" limit are re-authored from a repository with no license; no text or code is copied.
