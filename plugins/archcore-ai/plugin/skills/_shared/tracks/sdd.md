# SDD Track — Frame, Require, Design, Decompose

Plugin runtime asset. Loaded by the `plan` skill (primary executor) when routing
resolves to the `sdd` track. Gate execution, state block, and resume rules:
`skills/_shared/gate-contract.md`. Interview mechanics and question ceilings:
`skills/_shared/elicitation-contract.md`. Coverage categories:
`skills/_shared/coverage-taxonomy.md`. Per-type content contracts:
`skills/_shared/prd-contract.md` (`prd`) and
`skills/_shared/spec-contract.md` (`spec`).

## Track notes

- Gate order: `sdd.frame` → `sdd.require` → `sdd.design` → `sdd.decompose`.
- Each `budget` knob states this track's per-gate maximum, reached only in
  expert invocation. Auto mode draws every question from the shared
  per-invocation ceiling in `skills/_shared/elicitation-contract.md`.
- Content voice for produced documents: `skills/_shared/precision-rules.md`
  Rule 6.
- Before the first gate, the `plan` skill calls `list_documents` for the types
  `idea`, `prd`, `rnd`, `mrd`, `brd`, `urd`, `spec`, and `plan` and checks the
  topic for duplicates and recorded discovery.
- WHEN a `brd` or `urd` covers the topic, `sdd.require` composes Goals and
  Success Metrics from the `brd`'s success metrics and Requirements from the
  `urd`'s acceptance criteria — recorded requirements are never re-asked.
- WHEN a check-existing search returns a global document (`source_kind:
  "global"`), the executing skill loads `skills/_shared/globals.md`.
  WHEN no result is global, the gates proceed unchanged.
- The `task-type` offer that followed the plan in the source feature flow
  belongs to the experience track (`skills/_shared/tracks/experience.md`),
  not to `sdd`.
- This track produces four documents on one topic. The content-kind ownership
  table in `skills/_shared/prd-contract.md` names the one document that owns
  each kind of statement; the `sdd.require`, `sdd.design`, and `sdd.decompose`
  exit checks apply it.
- [assumption] Taxonomy knob values are mapped from each source step's
  composed sections; the source flows predate
  `skills/_shared/coverage-taxonomy.md`.

### gate: sdd.frame

- Purpose: Establish the core concept, its beneficiary, and known risks — the
  framing the later gates implement.
- Entry conditions:
  - skip_when: an `idea`, `prd`, or `rnd` covering the topic exists in
    `.archcore/` — an `rnd`'s Recommendation frames the topic the way an
    `idea` does; a complete sources set (`mrd`, `brd`, `urd`) on the topic
    also closes this gate — the `urd` records the concept's beneficiary.
  - The request text names the core concept and who benefits from it.
- Elicitation knobs:
  - trigger: the request does not name the core concept or the beneficiary.
  - taxonomy: Functional Scope & Behavior, Constraints & Tradeoffs from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 3
- Produces:
  - type: idea
  - status: draft
  - relations: none
- Exit checks:
  - blocking: the idea draft contains the sections Idea, Value, Possible
    Implementation, and Risks and Constraints.
- Next: `sdd.require`.

### gate: sdd.require

- Purpose: Establish the problem, goals, success metrics, and requirements as
  a `prd` scoped to one unit of product decision — a whole product or a
  single feature; size never changes the type.
- Entry conditions:
  - skip_when: a `prd` covering the topic exists in `.archcore/`; or the
    request is feature-scoped and an `idea`, `rnd`, or `adr` covering the
    topic already records the problem and the goals — the compression path in
    `skills/_shared/prd-contract.md`.
  - The concept and beneficiary are recorded — in an `idea` or `rnd`
    document, in a `urd` or `srs` covering the topic (recorded requirement
    sources), under `## Clarifications`, or in the request text.
- Elicitation knobs:
  - trigger: the problem statement or the success metrics are not recorded.
  - taxonomy: Functional Scope & Behavior, Interaction & UX Flow,
    Non-Functional Quality Attributes, Completion Signals from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 5
- Produces:
  - type: prd
  - status: draft
  - relations: `implements` → the `idea` from `sdd.frame`; none when no
    `idea` exists. `related` → the `mrd`, `brd`, and `urd` on the topic, when
    they exist. A product-level `prd` additionally links each feature-scoped
    `prd` it covers.
- Exit checks:
  - blocking: the prd draft contains every mandatory section defined in
    `skills/_shared/prd-contract.md`.
  - blocking: every numbered requirement in the prd draft follows the
    requirement form in `skills/_shared/prd-contract.md`.
  - blocking: no statement in the prd draft belongs to another document under
    the content-kind ownership table in `skills/_shared/prd-contract.md`.
  - advisory: a feature-scoped prd draft holds the body target the scope rule
    in `skills/_shared/prd-contract.md` sets; a product-level prd carries no
    line target.
- Next: `sdd.design`.

### gate: sdd.design

- Purpose: Formalize the behavior consumers rely on as a `spec` implementing
  the `prd`, and edit the `prd` statements this `spec` takes over — this gate
  calls `update_document` on the `prd` as well as creating the `spec`, per
  ownership rule 2 in `skills/_shared/prd-contract.md`.
- Entry conditions:
  - skip_when: a `spec` covering the topic exists in `.archcore/`, or no
    consumer relies on the planned behavior as a contract, per the routing
    gate in `skills/_shared/spec-contract.md`.
  - A `prd` on the topic exists, or `sdd.require` closed through the
    compression path in `skills/_shared/prd-contract.md` and the `idea`,
    `rnd`, or `adr` that closed it records the problem and the goals.
- Elicitation knobs:
  - trigger: the dependents, the surface, the constraints and invariants, or
    the failure behaviors are not recorded.
  - taxonomy: Domain & Data Model, Integration & External Dependencies, Edge
    Cases & Failure Handling, Constraints & Tradeoffs from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 3
- Produces:
  - type: spec
  - status: draft
  - relations: `implements` → the `prd` from `sdd.require`; `implements` →
    the `idea`, `rnd`, or `adr` that closed `sdd.require`'s compression path
    when no `prd` exists.
- Exit checks:
  - blocking: the spec draft contains every mandatory section defined in
    `skills/_shared/spec-contract.md`.
  - blocking: no line in the spec draft restates a prd requirement; the
    content-kind ownership table in `skills/_shared/prd-contract.md` assigns
    each statement to one document.
  - blocking: WHEN this spec took over a prd statement, the executing skill
    edited that statement in the prd per ownership rule 2 of
    `skills/_shared/prd-contract.md`, in one `update_document` call.
- Next: `sdd.decompose`. WHEN an answer at this gate settles a choice between
  technical alternatives, record it via the decision track
  (`skills/_shared/tracks/decision.md`).

### gate: sdd.decompose

- Purpose: Decompose the recorded scope into a phased `plan` with acceptance
  criteria and dependencies, composed from upstream drafts, recorded
  clarifications, and matching `task-type` or `cpat` precedent surfaced by
  grounding — a matching `task-type`'s Steps seed the task breakdown.
- Entry conditions:
  - skip_when: a `plan` covering the topic exists in `.archcore/`.
  - A `prd` or a `spec` on the topic exists.
- Elicitation knobs:
  - trigger: none — the executing skill MUST NOT ask questions at this gate.
  - taxonomy: none.
  - budget: 0
- Produces:
  - type: plan
  - status: draft
  - relations: `implements` → the `spec` from `sdd.design` when it exists;
    `implements` → the `prd` from `sdd.require` otherwise.
- Exit checks:
  - blocking: the plan draft contains the sections Goal, Tasks (phased),
    Acceptance Criteria, and Dependencies.
  - blocking: no plan task and no acceptance criterion restates a prd
    requirement, a prd success metric, or a spec behavior line; the
    content-kind ownership table in `skills/_shared/prd-contract.md` assigns
    each statement to one document.
  - advisory: the closing report lists candidate `add_relation` targets among
    existing `adr`, `rule`, `spec`, and `plan` documents, or states that none
    match.
- Next: exit.
