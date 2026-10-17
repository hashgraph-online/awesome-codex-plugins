---
name: review
description: Use before merge, after subagents, or for spec/plan review.
---
# Review

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`. Review each module diff in its owning repository first, then review the workspace as one change set. Block missing repositories, copied or divergent shared contracts, undeclared cross-module edits, overlapping writers, incomplete local acceptance, or integration results that do not identify the tested workspace combination.

Check in order:
1. **Spec match** (if spec exists) - diff does what the spec/plan said? List drift.
2. **Standards** — lint/format/typecheck green? Code matches `convention`, idiomatic for the stack? (see `../references/quality.md`)
3. **Tests** - new behavior covered, all green?
4. **Doc-coverage & Living docs** — `contract` covers full public surface? Env vars/config/error modes documented? README commands runnable? Living docs honor North Star (atemporal ground truth, modular specs; see `../references/quality.md`)?
5. **Edges** - null, empty, large, concurrent, malformed, unicode, timezone.
6. **Security** - input validation, secrets, authz, injection, path traversal.
7. **Scope** - unrelated changes? Revert. Implementation >2x necessary? Flag as FIX.
8. **Integration** (multi-module) - dependency order, compatibility, failure propagation, and coordinator acceptance cover the exact participating modules?

For spec/plan reviews, also block unresolved implementation notes, plan assumptions absent from spec, vague acceptance, or premature `[parallel]`.

Report:
```
BLOCK: <must fix>
FIX:   <should fix>
NIT:   <optional>
```
BLOCKs resolved before merge. FIX resolved or explicitly deferred with reason.
