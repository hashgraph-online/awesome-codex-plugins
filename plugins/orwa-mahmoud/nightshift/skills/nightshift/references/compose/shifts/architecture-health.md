# Architecture health — finite — concrete dependency and boundary cost from repository evidence

Use when the owner wants a reviewable picture of dependency, boundary, ownership, and cycle cost
in the repository — not architectural taste. Review-first is the default; direct edits are small
and reversible only.

Write receipts from `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/receipts/cycle-specialist-evidence.md`.
The model writes the receipt. Unparsed tool output is `unavailable`, never "no findings".

Supported on repositories with inspectable structure (packages, modules, manifests, CI). Never
select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **Architecture health — report concrete dependency and boundary cost.**
  - Never select this entry when work mode is artifact.
  - Discovery: inspect repository-owned structure only — manifests, package boundaries, import
    graphs the project already generates, CI topology, and ownership files. Record each finding in a
    `mode: architecture-findings` receipt from `receipts/cycle-specialist-evidence.md` and accept only findings with
    concrete dependency, boundary, ownership, or measured cycle cost. Reject taste-only observations.
  - Review first writes the findings report only. Direct mode may apply one small, reversible edit
    per cycle, and only where the finding names the exact files it touches and the item gate covers
    them; never perform broad refactors unattended.
  - Park ownership disputes, platform choices, and product tradeoffs in parking-lot.md with evidence.
  - Never present architectural preference as proof or claim whole-system health from one pass.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected).
  - Ends when every accepted finding is dispositioned (fixed, rejected, or parked) and no open
    taste-only rows remain.
  - Verify: the item gate is green at every commit; a second inspection pass over the scoped area
    accepts no new findings.
```
