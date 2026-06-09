---
name: review
description: Use before merge, after subagents, or for spec/plan review.
---
# Review

Check in order:
1. **Spec match** (if spec exists) - diff does what the spec/plan said? List drift.
2. **Documentation** (always) - README/comments reflect actual behavior?
3. **Tests** - new behavior covered, all green?
4. **Edges** - null, empty, large, concurrent, malformed, unicode, timezone.
5. **Security** - input validation, secrets, authz, injection, path traversal.
6. **Scope** - unrelated changes? Revert. Implementation >2x necessary? Flag as FIX.

For spec/plan reviews, also block unresolved implementation notes, plan assumptions absent from spec, vague acceptance, or premature `[parallel]`.

Report:
```
BLOCK: <must fix>
FIX:   <should fix>
NIT:   <optional>
```
BLOCKs resolved before merge. FIX resolved or explicitly deferred with reason.