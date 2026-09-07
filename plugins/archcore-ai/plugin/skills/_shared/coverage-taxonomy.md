# Coverage Taxonomy — Per-Family Categories for Gate Coverage Scans

Plugin runtime asset. Loaded by the skill that executes a gate whose record
sets the taxonomy elicitation knob (`skills/_shared/gate-contract.md`).

## Purpose

1. The taxonomy elicitation knob in a gate record names categories from this
   file. The knob's shape and states are defined in
   `skills/_shared/gate-contract.md`.
2. WHEN a gate record names categories, the executing skill MUST scan the
   draft artifact against each named category.
3. The executing skill MUST mark each named category `Covered`, `Missing`, or
   `Not applicable`.
4. A `Missing` mark on a material category is an elicitation trigger. The
   trigger and response rules are defined in
   `skills/_shared/elicitation-contract.md`.
5. Before the scan, the executing skill MUST drop categories that the
   applicability table below excludes for the produced document's family.

## Categories

Category names are quoted exactly from the source template.

- **Functional Scope & Behavior** — core user goals and success criteria;
  explicit out-of-scope declarations; user roles and personas.
- **Domain & Data Model** — entities, attributes, relationships; identity and
  uniqueness rules; lifecycle and state transitions; data volume and scale
  assumptions.
- **Interaction & UX Flow** — critical user journeys and sequences; error,
  empty, and loading states; accessibility and localization notes.
- **Non-Functional Quality Attributes** — performance targets; scalability
  limits; reliability and availability; observability; security and privacy;
  compliance and regulatory constraints.
- **Integration & External Dependencies** — external services and APIs with
  their failure modes; data import/export formats; protocol and versioning
  assumptions.
- **Edge Cases & Failure Handling** — negative scenarios; rate limiting and
  throttling; conflict resolution (for example, concurrent edits).
- **Constraints & Tradeoffs** — technical constraints (language, storage,
  hosting); explicit tradeoffs and rejected alternatives.
- **Terminology & Consistency** — canonical glossary terms; avoided synonyms
  and deprecated terms.
- **Completion Signals** — acceptance-criteria testability; measurable
  Definition of Done indicators.
- **Misc / Placeholders** — TODO markers; unresolved decisions; ambiguous
  adjectives lacking quantification. The source template lists this entry
  last in its ten-entry taxonomy.

Source: Spec Kit `clarify` command template,
<https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/clarify.md>,
fetched 2026-08-05.

## Per-family applicability

Family membership is derived from the produced document's type:

| Family | Document types |
|---|---|
| vision | prd, idea, plan, rnd, mrd, brd, urd, brs, strs, syrs, srs |
| knowledge | adr, rfc, rule, guide, doc, spec |
| experience | cpat, task-type |

`Yes` — the coverage scan applies the category to drafts of this family.
`—` — the family's types do not carry this content; the scan skips the
category.

| Category | vision | knowledge | experience |
|---|---|---|---|
| Functional Scope & Behavior | Yes | Yes | Yes [assumption] |
| Domain & Data Model | Yes | Yes | — [assumption] |
| Interaction & UX Flow | Yes | — [assumption] | — [assumption] |
| Non-Functional Quality Attributes | Yes | Yes | Yes [assumption] |
| Integration & External Dependencies | Yes | Yes | — [assumption] |
| Edge Cases & Failure Handling | Yes | Yes | Yes [assumption] |
| Constraints & Tradeoffs | Yes | Yes | Yes [assumption] |
| Terminology & Consistency | Yes | Yes | Yes |
| Completion Signals | Yes | Yes | Yes [assumption] |
| Misc / Placeholders | Yes | Yes | Yes |

Basis per family:

- **vision** — every category applies. The requirement types (brs, strs,
  syrs, srs) carry scope, data-model, quality-attribute, integration, and
  acceptance content; prd, urd, and idea carry goal, journey, and scope
  content; plan and rnd carry constraint, tradeoff, and completion content.
- **knowledge** — Interaction & UX Flow is excluded: adr, rfc, rule, guide,
  doc, and spec record decisions, proposals, standards, procedures,
  reference content, and contracts, not user journeys [assumption].
  Constraints & Tradeoffs is core adr content (rejected alternatives);
  Completion Signals applies through acceptance criteria in rule and spec;
  Domain & Data Model applies through spec contracts and doc reference
  content.
- **experience** — cpat carries Before/After code pattern changes; task-type
  carries typical task patterns. Domain & Data Model, Interaction & UX Flow,
  and Integration & External Dependencies are excluded: pattern records do
  not carry entity models, user journeys, or external-service contracts
  [assumption]. Non-Functional Quality Attributes applies when a pattern
  change states a measured motivation; Completion Signals applies through a
  task pattern's verification steps; Edge Cases & Failure Handling applies
  through negative examples and failure-handling steps [assumption].

Terminology & Consistency and Misc / Placeholders apply to all families: the
repository writing policy and `skills/_shared/precision-rules.md` bind every
document type to stable terminology, `[assumption]` markers, and the
forbidden vagueness lexicon.

## One category, different destinations

A category names what to scan for, not where the answer is written. WHEN a track
produces more than one document on one topic, the content-kind ownership table
in `skills/_shared/prd-contract.md` names the section each category lands in per
type, and a category marked `Covered` for one document stays open for a document
of another type on the same topic.
