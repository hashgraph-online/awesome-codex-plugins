---
name: product
description: 'Create or refine PRODUCT.md while separating Triggers: "product", "create PRODUCT.md", "product boundary".'
---
# Product

Create or refine a product contract with the user's authority.

The contract works because it forces every claim into evidence or labeled
aspiration; if a reader cannot tell which is which, the document has failed.

1. Inspect existing product, README, goals, release, and evidence sources.
2. Ask only for decisions that cannot be grounded safely from those sources.
3. State mission, users, pains, value, differentiation, and non-goals. For
   this repository's own product surfaces, start from the canonical category
   in `docs/contracts/ubiquitous-language.md` (AgentOps is the operations
   layer for agentic engineering) and preserve the small ownership boundary —
   never re-frame AgentOps as an execution orchestrator, factory, or loop.
4. Separate evidence from hope under two required headings. Put every grounded
   claim under `## Proven`, each carrying a resolvable citation (a README,
   release, test, or evidence source). Put unproven hopes, evidence gaps, and
   not-yet-measured success signals under `## Assumptions`. A claim that cannot
   cite a source belongs under `## Assumptions`, never `## Proven`.
5. Preserve an existing PRODUCT.md unless the user authorizes replacement.
6. Return the document to the caller; Plan may use it as intent context.

Named failure mode — **aspiration laundering**: an unproven hope written in the
`## Proven` section; once laundered, every downstream plan inherits a false
premise. Detector: any `## Proven` claim without a resolvable citation is a
laundered aspiration — move it to `## Assumptions` or cite it.

Anti-pattern: rewriting a healthy PRODUCT.md wholesale because the session has
fresh opinions. Corrective: refine only the sections the user asked to change
and preserve the rest byte-for-byte.

Product does not select work, invoke a loop, repair itself, validate itself, or
choose delivery.
