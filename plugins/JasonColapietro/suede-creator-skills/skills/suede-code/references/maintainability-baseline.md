# Suede Maintainability Baseline

Twelve structural checks the review carries even when a repo documents no
coding standards. Load on `--standard` and `--deep`. Match them against the
diff only: flag what the change introduces or makes worse, never the whole file.

## Rules that travel with the baseline

1. **The repo wins.** A documented project rule outranks this list. If the repo
   endorses a pattern a check below would flag, stay silent.
2. **Label it as judgment.** Every finding here reads "possible <check name>",
   never as a hard violation. Default severity is P3. Raise to P2 only when the
   pattern sits on a changed critical path and you can name how it raises
   defect risk there. Confidence is `medium` at most, because these are read,
   not executed.
3. **Leave tooling's job to tooling.** If a linter, formatter, or type checker
   already catches it, do not report it by hand.
4. **Stay inside the diff.** Pre-existing patterns outside the changed lines
   are not findings. At most, add one "residual risk" line when the change
   builds on top of one.

## The twelve checks

Each entry names the pattern, then the usual repair.

- **Name hides the job.** A function, variable, or type whose name does not
  say what it does or holds. Rename it. If no accurate name comes, report the
  muddy design instead.
- **Logic pasted twice.** The same shape of logic appears in more than one hunk
  or file in this change. Extract it once and call it from both places.
- **Method lives in the wrong place.** A method that reads another object's
  fields more than its own. Move it next to the data it keeps reaching for.
- **Fields that always travel together.** The same three or four values move
  through several signatures side by side. Give them one type and pass that.
- **String standing in for a concept.** A raw string or number carries a domain
  idea (currency, status, ID kind) that deserves its own small type.
- **Same branch ladder in several places.** An identical `switch` or `if` chain
  on the same value recurs across the change. Replace with one lookup map both
  sites share, or with polymorphism.
- **One change, many scattered edits.** A single logical change forces small
  edits across many files. Gather what changes together into one module.
- **One file, many unrelated reasons.** A module edited for several unrelated
  purposes in the same diff. Split it so each module changes for one reason.
- **Built for a future nobody asked for.** Parameters, hooks, or abstraction
  layers the spec does not need. Delete them and inline until a real need shows.
- **Long navigation chains.** Callers walk `a.b().c().d()` through internals
  they should not depend on. Hide the walk behind one method on the first object.
- **Pass-through layer.** A class or function that mostly forwards calls. Cut
  it and call the real target.
- **Inheritance mostly ignored.** A subclass or implementer that overrides or
  discards most of what it inherits. Drop the inheritance and compose instead.

## Output shape

Report as a normal P2 or P3 finding, with the check named and the hunk cited:

```
[P3] lib/orders.ts:88, possible Fields that always travel together: (currency,
amount, region) pass through 3 signatures in this diff; bundle as a Money type.
Confidence: medium
```

These findings feed the Technical Debt read inside the grade. They never
outnumber or outrank correctness findings, and they never move the ship gate
unless rule 2's P2 condition holds.
