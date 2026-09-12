# Requirements Cascade Track — Sources Discovery and ISO 29148 Gate Flows

Plugin runtime asset. Loaded by the `plan` skill (`/archcore:plan`) when routing
resolves to the `requirements-cascade` track. Gate records follow `skills/_shared/gate-contract.md`;
interview mechanics live in `skills/_shared/elicitation-contract.md`.

## Modes

The track runs in one of two modes. The gate name identifies the stage and
therefore the mode; the state block carries no mode field.

- `mode: sources` — the acquisition instrument; peer documents in recommended
  order: `requirements-cascade.mrd` → `requirements-cascade.brd` →
  `requirements-cascade.urd`. The conductor engages it on a product-scale
  `intent_gap` per `skills/_shared/delta-routing.md`; the user engages it via
  expert invocation.
- `mode: iso` — iso links, ISO 29148 decomposition with traceability:
  `requirements-cascade.brs` → `requirements-cascade.strs` →
  `requirements-cascade.syrs` → `requirements-cascade.srs`. The conductor
  engages the links per `security-compliance`-flagged capability, and the
  chain then scopes to the flagged capabilities only — partial formality; the
  user invokes the full chain via expert invocation.

### Mode selection

Entry comes from the conductor (`skills/_shared/delta-routing.md`) or from an
expert invocation. The `plan` skill resolves a direct entry from routing
signals — never by asking the user — in this order: explicit expert
invocation, document-graph state. Branch state contributes no mode signal in
this track.

1. Explicit expert invocation naming a document type: `mrd`, `brd`, or `urd` selects sources; `brs`, `strs`, `syrs`, or `srs` selects iso.
2. Document-graph state: a `brs`, `strs`, `syrs`, or `srs` on the topic selects
   iso; an incomplete `mrd`/`brd`/`urd` set on the topic with no iso-mode document
   selects sources; a complete `mrd`, `brd`, and `urd` set on the topic with no
   iso-mode document selects iso.
3. Request wording: contributes no mode signal — WHEN neither signal above
   resolves the entry, the conductor's route computation decides per
   `skills/_shared/delta-routing.md`.

Sources mode enters at `requirements-cascade.mrd`; iso mode enters at
`requirements-cascade.brs`. WHEN an explicit expert invocation names `brd` or
`urd`, sources mode enters at that document's gate instead — the three source
documents are peers (the source flow fixed no order among them). Before the first gate, the `plan` skill calls
`list_documents` for this track's document types plus `prd` and checks the topic for duplicates.

WHEN the first gate closes, the `plan` skill MUST record the chosen mode and its
selecting signal as one line under `## Clarifications` in the draft artifact —
for example `mode: iso — request names a regulated system` [assumption: the wording of this record].

## Track-wide knob values

- Per-gate question maximum: 2. Each budget knob states this value. In auto mode
  every question draws down the per-invocation ceiling in `skills/_shared/elicitation-contract.md`.
- Taxonomy knob values map each ported stage's content list onto coverage
  categories; these mappings are new in this track file [assumption].
- The most recently produced draft carries the `archcore:track` state block;
  WHEN a gate produces the next document, the `plan` skill moves the block to
  the new draft during that gate's close [assumption].

### gate: requirements-cascade.mrd

- Purpose: Produce the market requirements document.
- Entry conditions:
  - skip_when: an `mrd` covering the topic exists in `.archcore/`.
  - The request names the market under analysis and the key opportunity.
- Elicitation knobs:
  - trigger: grounding does not resolve the market under analysis or the key opportunity.
  - taxonomy: Functional Scope & Behavior, Constraints & Tradeoffs from `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: mrd
  - status: draft
  - relations: none
- Exit checks:
  - blocking: the draft carries the sections Market Landscape, TAM/SAM/SOM, Competitive Analysis, Market Needs, Opportunity and Timing.
  - advisory: each TAM/SAM/SOM figure carries a value or an `[assumption]` marker.
- Next: `requirements-cascade.brd`.

### gate: requirements-cascade.brd

- Purpose: Produce the business requirements document.
- Entry conditions:
  - skip_when: a `brd` covering the topic exists in `.archcore/`.
  - The `mrd` or the request states the business objectives and the expected ROI.
- Elicitation knobs:
  - trigger: grounding does not resolve the business objectives or the expected ROI.
  - taxonomy: Completion Signals, Integration & External Dependencies from `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: brd
  - status: draft
  - relations: `related` → the `mrd` (peer source documents), when one exists.
- Exit checks:
  - blocking: the draft carries the sections Business Objectives, Stakeholders, Business Rules, Success Metrics and ROI, Dependencies.
  - advisory: each success metric carries a measurable value or an `[assumption]` marker.
- Next: `requirements-cascade.urd`.

### gate: requirements-cascade.urd

- Purpose: Produce the user requirements document.
- Entry conditions:
  - skip_when: a `urd` covering the topic exists in `.archcore/`.
  - The `mrd`, the `brd`, or the request identifies the users and their key needs.
- Elicitation knobs:
  - trigger: grounding does not resolve who the users are or their key needs.
  - taxonomy: Interaction & UX Flow, Completion Signals from `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: urd
  - status: draft
  - relations: `related` → the `mrd` and `related` → the `brd`, when they exist.
- Exit checks:
  - blocking: the draft carries the sections User Personas, User Journeys, User Requirements, Usability Requirements, Acceptance Criteria.
  - advisory: each acceptance criterion is testable.
- Next: exit. Report follow-ups through `/archcore:plan`: a `prd` via the intent instrument (`skills/_shared/tracks/sdd.md`), or a `brs` via this track's iso mode; WHEN a `prd` on the topic already exists, link the source documents to it with `related` via `add_relation`.

### gate: requirements-cascade.brs

- Purpose: Formalize business goals into the business requirements specification that opens the ISO 29148 chain.
- Entry conditions:
  - skip_when: a `brs` covering the topic exists in `.archcore/`.
  - Existing `mrd`/`brd` documents or the request state the business goals.
- Elicitation knobs:
  - trigger: grounding does not resolve the business goals this specification formalizes.
  - taxonomy: Functional Scope & Behavior, Constraints & Tradeoffs from `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: brs
  - status: draft
  - relations: `implements` → the `mrd` and `implements` → the `brd`, when they exist.
- Exit checks:
  - blocking: the draft states the business goals and enumerates the business requirements derived from them.
  - blocking: each requirement carries a stable identifier for traceability.
- Next: `requirements-cascade.strs`.

### gate: requirements-cascade.strs

- Purpose: Produce the stakeholder requirements specification.
- Entry conditions:
  - skip_when: an `strs` covering the topic exists in `.archcore/`.
  - A `brs` on the topic exists.
- Elicitation knobs:
  - trigger: grounding does not resolve the stakeholder classes or their distinct requirements.
  - taxonomy: Functional Scope & Behavior, Interaction & UX Flow from `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: strs
  - status: draft
  - relations: `implements` → the `brs`; `implements` → the `urd`, when one exists.
- Exit checks:
  - blocking: the draft names each stakeholder class and states that class's requirements.
  - blocking: each requirement carries a stable identifier for traceability.
- Next: `requirements-cascade.syrs`.

### gate: requirements-cascade.syrs

- Purpose: Produce the system requirements specification.
- Entry conditions:
  - skip_when: a `syrs` covering the topic exists in `.archcore/`.
  - An `strs` on the topic exists.
- Elicitation knobs:
  - trigger: grounding does not resolve the system boundary, the key interfaces, or the operational modes.
  - taxonomy: Domain & Data Model, Integration & External Dependencies from `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: syrs
  - status: draft
  - relations: `implements` → the `strs`.
- Exit checks:
  - blocking: the draft states the system boundary, the interfaces, and the operational modes.
  - blocking: each requirement carries a stable identifier for traceability.
- Next: `requirements-cascade.srs`.

### gate: requirements-cascade.srs

- Purpose: Produce the software requirements specification.
- Entry conditions:
  - skip_when: an `srs` covering the topic exists in `.archcore/`.
  - A `syrs` on the topic exists.
- Elicitation knobs:
  - trigger: grounding does not resolve the software components to specify or their functional and non-functional requirements.
  - taxonomy: Functional Scope & Behavior, Non-Functional Quality Attributes from `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: srs
  - status: draft
  - relations: `implements` → the `syrs`.
- Exit checks:
  - blocking: the draft states functional and non-functional requirements for each named software component.
  - blocking: each requirement carries a stable identifier for traceability.
  - advisory: the report names existing `spec`, `plan`, or `prd` documents linked to the `srs`, or states that none exist.
- Next: exit. WHEN an existing `spec` or `plan` document covers the topic, the `plan` skill creates the `related` link via `add_relation` at the track exit; WHEN none exists, the report states that none exist and names a `prd` through `/archcore:plan`'s intent instrument as the follow-up.
