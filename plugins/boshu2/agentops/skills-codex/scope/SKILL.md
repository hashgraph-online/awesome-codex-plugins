---
name: scope
description: Review the bead or caller intent write scope
---
# Scope — Review a proposed write scope

Review the write scope in the existing bead or caller intent. This skill is
advisory: it does not create a second planning artifact, write a lock, install
a hook, block an edit, or claim paths.

## Inputs

- One active behavior and its acceptance scenarios.
- Proposed include and exclude patterns.
- Known generated companions and fixture/projection paths.
- Explicit non-goals.

## Procedure

1. Map each acceptance criterion to the smallest source paths that may change.
2. Add owned generated companions that must move with those sources.
3. Check whether any include/exclude patterns overlap or are too broad to prove.
4. Identify likely paths the proposal omitted.
5. Return a corrected proposal and the reasons for each change, then stop.

The caller decides whether to adopt the proposal in the original intent source,
and Validate independently compares runtime-derived changed paths with that scope.

## Axiom-kernel framing

Derive the scope from axioms, not enumeration instinct. State the small set of
facts the acceptance makes true — "behavior X lives in root A", "projection B
is generated from A", "history under C is frozen" — and derive every include
and exclude pattern from exactly one axiom. A pattern with no supporting axiom
is unjustified breadth; an axiom with no pattern is a gap. Both go in the
review output. Scopes assembled by listing directories that feel related are
the **vibes perimeter** failure mode: they cannot be defended when Validate
finds a path on the boundary, because nobody can say why the line is where it
is. Stop condition: the review is complete when the axiom-to-pattern mapping
has no unmapped members on either side.

## Byte-verified recovery ceremony

When the review finds that protected paths were already touched — or the
caller asks how a scope violation should be unwound — the advisory answer is a
ceremony, not a hand-wave: identify the known-good source for each affected
path (committed state, snapshot, or generated-from-source), restore, then
verify byte-for-byte that restored content matches the known-good bytes
(content hash comparison, not visual diff or "looks right"). Recovery declared
on inspection alone is the **eyeballed restore** failure mode: a file that
looks restored can still differ in bytes that matter. The ceremony's stop
condition is a hash match for every affected path; any path with no
known-good source to verify against is reported as unrecoverable-as-scoped,
and the caller decides.

## Output

```yaml
write_scope:
  include: ["bounded/source/**"]
  exclude: ["bounded/source/generated-by-other-owner/**"]
generated_companions: ["bounded/generated/**"]
gaps: []
ambiguities: []
```

## Checks

- Patterns are normalized repository-relative paths.
- Includes cover the behavior without granting unrelated directories.
- Excludes do not contradict required changes.
- Generated companions are explicit.
- No ownership, scheduling, Git, hook, retry, release, or delivery state is
  introduced.

## Failure behavior

If the scope cannot be made unambiguous from the supplied acceptance, report
the missing facts and stop. The caller may revise the intent in a new action.
