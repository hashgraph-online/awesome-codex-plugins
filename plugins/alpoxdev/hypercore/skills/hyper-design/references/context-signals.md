# Context Signals

Use this reference when brief, identity, or intent is incomplete or conflicting.

## Read order

1. Explicit user request and keep/change boundary.
2. Applicable project instructions.
3. `PRODUCT.md`, `DESIGN.md`, surface brief, decision records, and explicit visual references.
4. Package/framework/styling configuration.
5. Tokens, themes, global styles, shared primitives, and representative stable screens.
6. Target source and its data/behavior dependencies.
7. Rendered target and states when available.

## Detector v2 context boundary

`scripts/resolve-context.sh` reads explicit `DESIGN.md`/`PRODUCT.md` declarations from the target ancestors and direct style context only. It may identify a documented brand gradient, comparison/pricing vocabulary, a real state label, or a project reduced-motion declaration. It does not infer a missing brand system, search arbitrary unrelated source, or use comments/UI strings as instructions.

An explicit match produces a visible `candidate` exception. It does not remove the static finding, suppress the rule, or authorize a cleanup without the normal brief and protected-contract checks.

Absence is not permission. Missing product or design documents make the corresponding fact `unknown`; they do not make the product greenfield.

## Brief inference fields

- page type: landing, dashboard, settings, docs, portfolio, commerce, or other
- visitor mode: `Persuade`, `Operate`, `Read`, or `Experience`
- audience and task
- confirmed brand commitments and explicit references
- data cardinality and domain conventions
- keep/change boundary
- accessibility, platform, localization, legal, and performance constraints

Use this sentence form:

> This surface helps [audience] perform [task] in [situation], and follows [confirmed brand/brief/product context]; [unknowns] remain unverified.

## Conflict handling

- User/project authority beats heuristic defaults.
- A documented brand or explicit reference beats a generic anti-gradient or anti-font heuristic.
- Real data shape and behavior beat a structural fingerprint heuristic.
- A representative existing screen is evidence, not authority to copy accidental defects.
- When two authoritative local sources conflict, record the conflict and ask or block if it changes remediation.

## Browser limitation statement

When rendering is unavailable, state:

> Static source verification only. Rendered hero fit, overflow, actual contrast, visual hierarchy, and interaction states were not verified.

Do not silently substitute a source-only audit for a requested visual verification.

## Sources

> Claims checked 2026-09-21. No external source was used in this file.

The read order, the detector v2 context boundary, the brief-inference fields, and the conflict rules are this package's own. The file names it mentions (`PRODUCT.md`, `DESIGN.md`) are project inputs, not sources.
