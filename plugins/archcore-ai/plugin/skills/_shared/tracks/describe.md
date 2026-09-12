# Describe Track — Gates for Documenting Existing Code

Plugin runtime asset. Loaded by the `document` skill when its classification
resolves to code documentation — a module, component, API, system, or technical
topic. Gate record shape, state block, execution and resume rules:
`skills/_shared/gate-contract.md`. Interview mechanics:
`skills/_shared/elicitation-contract.md`. Budget values below are per-gate
maximums reached only in expert invocation; auto mode draws every question from
the shared per-invocation ceiling in `skills/_shared/elicitation-contract.md`.

Decision-shaped requests ("we chose X", standards, proposals) belong to the
decision track (`skills/_shared/tracks/decision.md`); the `document` skill
classifies before entering this file.

## Callable mode

WHEN the calling skill pre-fills the scope — the subject, its files, and the
evidence — `describe.read` runs question-free, and its entry conditions are
satisfied by the pre-filled scope. The conductor uses this entry on an
amendment route that finds no covering `spec` (sequencing rule 11 in
`skills/_shared/delta-routing.md`).

## Type heuristics

Ported from the v1 capture flow. Applied with the `describe.read` evidence in
hand; settled at `describe.draft`.

| Signal | Type |
|---|---|
| Behavior others rely on — an API, interface, schema, or protocol boundary, or a feature/subsystem with states, field-driven rules, and invariants | `spec` |
| Reference material — a registry, glossary, or lookup | `doc` |
| How-to instructions or procedures | `guide` |
| A module described comprehensively ("document everything about X") | `guide`, plus `spec` when others rely on the module's behavior, plus `doc` when the evidence includes reference material (a registry, glossary, or lookup). [assumption] The v1 flow also created an `adr` on this route; a settled decision surfaced by the evidence now routes to the decision track. |

Default after the one type question at `describe.draft`: `spec` when others
rely on the subject's behavior; `doc` otherwise. [assumption] The v1 default
was `adr`, a type the decision track now owns.

### gate: describe.read

- Purpose: Gather the evidence base — files, entry points, observed behavior — and rule out duplicate documents.
- Entry conditions:
  - skip_when: the request already carries the evidence — file paths, entry points, and a behavior description.
  - The request names a code subject locatable in the repository.
- Elicitation knobs:
  - trigger: none — this gate grounds from the codebase, git history, and `.archcore/` search; evidence-gap questions belong to `describe.clarify`.
  - taxonomy: none.
  - budget: 0
- Produces: none — the evidence and the duplicate-scan result feed `describe.draft`.
- Exit checks:
  - blocking: the gathered evidence names the subject's files, entry points, and observed behavior.
  - blocking: `list_documents` / `search_documents` results for the subject are recorded — existing documents to relate to, duplicates, and global matches to treat per `skills/_shared/globals.md`. No global match → proceed unchanged.
- Next: `describe.draft`.

### gate: describe.draft

- Purpose: Settle the document type — `spec`, `doc`, or `guide` — and compose the draft from the gathered evidence.
- Entry conditions:
  - skip_when: a non-global document found at `describe.read` already covers the subject — update that document via `update_document` instead of creating a duplicate. [assumption] Ported from the v1 duplicate-prevention step, which did not state the update path.
  - Evidence from `describe.read` or from the request covers the subject's files, entry points, and behavior.
- Elicitation knobs:
  - trigger: the type heuristics above match no single type.
  - taxonomy: `Functional Scope & Behavior` from `skills/_shared/coverage-taxonomy.md`. [assumption] The v1 flow named no coverage category for its type question.
  - budget: 1 — the ported type question: "Is this primarily a decision, a contract/behavior spec, reference material, or instructions?"
- Produces:
  - type: `spec`, `doc`, or `guide` per the type heuristics; the comprehensive route produces more than one document, and an over-cap subject one `spec` per separable sub-surface (`skills/_shared/spec-contract.md` "Over the cap").
  - status: draft
  - relations: `related` to the existing subject documents found at `describe.read` — the v1 relate step names the link to existing documents but not the relation type [assumption]; `related` between documents produced together; no relation to a global document per `skills/_shared/globals.md`.
- Exit checks:
  - blocking: a draft of the chosen type exists, created via `create_document`.
  - blocking: a `spec` draft carries the sections `skills/_shared/spec-contract.md` requires, composed after reading that contract and `skills/_shared/precision-rules.md`.
  - blocking: a `spec` draft over that contract's body cap was decomposed by separable sub-surface, or kept whole with the excess reported, per its "Over the cap" rules. Normative content is never deleted to fit the cap.
  - blocking: a `doc` draft covers Overview, Content, and Examples — a ported v1 composition target; no shared contract exists for this type.
  - blocking: a `guide` draft carries every section `skills/_shared/guide-contract.md` requires, composed after reading that contract.
- Next: `describe.clarify`. WHEN the type answer is "a decision", the executing skill records it via the decision track (`skills/_shared/tracks/decision.md`) instead of continuing on this track.

### gate: describe.clarify

- Purpose: Resolve evidence gaps — facts the code cannot answer — before the track exits.
- Entry conditions:
  - skip_when: the coverage scan of the draft reports no `Missing` mark on a material category.
  - A draft created at `describe.draft`, or the existing document updated under the `describe.draft` skip_when, exists.
- Elicitation knobs:
  - trigger: the coverage scan returns `Missing` on a material category and neither the code, git history, nor `.archcore/` can supply the fact.
  - taxonomy: `Integration & External Dependencies`, `Non-Functional Quality Attributes`, `Constraints & Tradeoffs`, `Edge Cases & Failure Handling`, `Completion Signals` from `skills/_shared/coverage-taxonomy.md`. [assumption] Mapped from the ported v1 question stock below.
  - budget: 2. [assumption] One question per produced document, up to the two documents (`guide` plus `spec`) of the comprehensive route; the v1 flow asked one composition question per document.
- Produces: none — accepted answers land in that document per `skills/_shared/elicitation-contract.md`.
- Exit checks:
  - blocking: every material `Missing` category has an accepted answer, an inline `[assumption]`, or a `deferred` entry in the state block.
  - advisory: the draft carries no TODO marker or unresolved placeholder.
  - advisory: the closing report lists document paths, relation edges, and one recommended next action.
- Next: exit.

## Ported question stock for describe.clarify

Ask only for a fact the `describe.read` evidence could not settle:

- `spec` — "Who depends on this, and what is its surface — the interface, or the parts, states, and fields that drive behavior? What are the key constraints, invariants, and failure behaviors?"
- `doc` — "What information should this reference contain?"
- `guide` — "What task does this guide walk through? What prerequisites exist?"
