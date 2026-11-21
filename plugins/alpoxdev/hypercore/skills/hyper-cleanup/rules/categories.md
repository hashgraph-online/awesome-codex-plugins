# Categories

Read this before naming a line as slop. It owns the nine categories, the KEEP exceptions that outrank them, and the proof each removal needs before it is written.

## 1. The Nine Categories

A candidate is a category plus a KEEP check plus a proof. Failing the KEEP check moves the line out of scope; a missing proof keeps the line where it is.

| # | Category | Group | Proof before the edit |
|---|---|---|---|
| 1 | Comment echo | stylistic | the comment restates the line below it, and the line is not load-bearing why |
| 2 | Over-defensive code | stylistic | the guard's subject cannot be absent, or a remaining guard inside the same boundary covers the same input |
| 3 | Excess complexity | stylistic | the flattened form is readable to the same reader with no behavior change |
| 4 | Needless abstraction | structural | one caller, one implementer, no seam: the wrapper disappears and every caller still reads plainly |
| 5 | Boundary violation | structural | the misplaced responsibility has a named owner layer, and moving it does not create an import cycle |
| 6 | Dead code | structural | nothing reaches it: no caller, no reflective or string lookup, no flag that still flips |
| 7 | Duplication | hidden cost | the copies serve one intent and will not diverge; the merged form keeps every caller's input |
| 8 | Behavior-equivalent cost | hidden cost | equivalence is obvious, not argued: the output set is identical for every input the owner accepts |
| 9 | Test junk | tests | the class's proof in [test-junk.md](test-junk.md), or the mark it earns |

Categories 4, 5, and 7 are the ones where a wrong call does damage: a seam, a layer, or an accidental duplication that a future change was going to split. When the intent is not visible in the code, the candidate stays.

## 2. Stylistic

### 1. Comment echo

Restating the line, trivial docstrings, banner dividers, commented-out code, and a vague `TODO` or `NOTE` with no owner.

KEEP:

- a comment that says why: the business rule, the edge case, the platform workaround, the ordering constraint
- a ticket or issue link, a regex or algorithm explanation, a unit or sign convention
- behavior-first markers that name the scenario (`# given`, `# when`, `# then`)

A comment whose removal would make a future reader re-derive a constraint is not an echo, even when it repeats the code's shape.

### 2. Over-defensive code

Null or undefined checks on values the type or caller guarantees, `try`/`catch` around code that cannot raise, a default for a required parameter, a backwards-compatibility shim for a caller that no longer exists, the same validation repeated at three layers, and a broad catch that swallows every failure.

KEEP: validation at a system boundary (user input, an external API response, a file or network read), I/O error handling, nullable storage fields, and one top-level boundary catch that logs and re-raises.

A guard is load-bearing until its redundancy is proven. Proof means a hostile or malformed input that the outer layer rejects while the inner guard is removed, and that same input reaching the owner when the outer layer is removed. No proof, no removal: an unproven guard is a boundary, not noise.

Narrowing a catch is a behavior change when the broad form documented what the surface swallows. Narrow only when the documented exception set is the same.

### 3. Excess complexity

Nesting past three levels, chained ternaries, boolean expressions that combine four or more independent predicates, parameter lists past five without a named struct, functions that do several unrelated jobs, and one-liners that cost the reader more than the lines they save.

KEEP: the established idiom of this codebase, a hot path whose complex form is the measured reason it is fast, and a boolean `if`/`else` or range check that reads plainly as written.

Flattening is safe when the guards become early returns with the same order and the same effect, and no branch starts depending on state it did not read before.

## 3. Structural

### 4. Needless abstraction

A pass-through wrapper, a single-use helper, an interface with one implementer that adds no test seam, a factory that only calls a constructor, and indirection kept for a future that has not arrived.

KEEP: a seam that a test substitutes at a real boundary, a shape with two or more live implementers, and a framework-required type or lifecycle.

Removing the wrapper means every caller still names the same operation. An inlined body that makes a caller read worse is not a cleanup.

### 5. Boundary violation

A layer reaching across: UI code importing a driver, a handler carrying business rules that belong to a service, one module reading another's private state, a side effect inside a function named as pure.

KEEP: a short-circuit the codebase already uses as a pattern, and a deliberate coupling documented in place.

This category is reported, not silently moved, when the target layer is outside the authorized file set. Moving code across a module boundary is a separate change with its own plan.

### 6. Dead code

An unused import, an unreachable branch, a private function with no caller, a stale feature flag, a debug print left in the tree, and a symbol that was removed but is still referenced.

KEEP: anything reached by reflection, dynamic dispatch, a string lookup, a template, or a configuration key at runtime, and a flag whose rollback path is still live.

Proof is a reference search over the whole repository, not the current file: definition sites, call sites, string forms of the name, and the build system's own entry points. A reference search that could not run leaves the code in place and the reason in the report.

### 7. Duplication

Copy-pasted branches that differ only in a literal, two helpers that do the same thing, and the same magic sequence in several places.

KEEP: two similar bodies that serve different intents and may legitimately diverge, and a repeated literal that names different concepts in each place.

Merging two bodies into one parameterized helper is a change to both callers. It is authorized only when both callers are in the file set.

## 4. Hidden Cost

### 8. Behavior-equivalent cost

A quadratic scan that becomes a set lookup, a recomputation inside a loop that hoists out, an eager intermediate collection that becomes a single pass, string concatenation in a loop that becomes a join, a repeated call that batches, and a deep copy that is not needed.

The hard rule: apply only when equivalence is obvious for every input the owner accepts. A change to an algorithm whose edge cases are not fully read is out of scope, and a micro-optimization with no measurement is not this category.

## 5. Tests

### 9. Test junk

A declaration that cannot fail, restates an implementation, pins prose, mirrors a copied inventory, or greps source text. [test-junk.md](test-junk.md) owns the classes, the marks, and the proof each one needs.

KEEP: a test that independently guards a public API, a protocol, a config schema or default, a migration, a storage format, a security boundary, a platform behavior, shipped-copy equality between real artifacts, an issue regression, or a machine-consumed token. Say which one in the ledger row.

A test that is red on the unchanged base is a product bug. It is reported and excluded from every proof; it is never deleted and never edited to pass.

## 6. KEEP Outranks the Category

The KEEP lists are not suggestions. A public signature, an exception behavior, a side effect, a security guard, an accessibility affordance, and a supported environment are contracts even when the code that holds them looks redundant.

When two categories disagree, the stricter proof wins. When the KEEP list and the category both apply, the line stays and the report records it under preserved code.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Nine slop categories with a KEEP exception list per category, and tests as one category | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Adversarial proof before removing a duplicate boundary guard, and the requirement to keep a documented exception set | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Behavior-equivalent performance changes applied only when equivalence is obvious | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| The KEEP list for tests: public API, protocol, config, migration, storage, security, platform, shipped-copy equality, issue regressions, machine-consumed text | `dbc-hbin/omp-ulw@74df40f programming/references/testing/junk-classes.md` (mechanism reference, re-authored) |
| The nine-category delivery shape and the file-set authorization | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - the category numbering, the proof column, and the boundary-violation rule that reports instead of moving are this package's design. The category set and the KEEP exceptions are re-authored from a repository with no license; no text or code is copied.
