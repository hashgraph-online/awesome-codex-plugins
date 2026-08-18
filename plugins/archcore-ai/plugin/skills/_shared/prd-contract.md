# PRD Content Contract

Plugin runtime asset. Loaded by the skill composing a `prd`: `plan` at the
`sdd.require` gate (`skills/_shared/tracks/sdd.md`). Companion to
`skills/_shared/spec-contract.md` and `skills/_shared/precision-rules.md`.

This contract also carries the content-kind ownership table that keeps a `prd`,
a `spec`, and a `plan` on the same topic from restating each other. The gates in
`skills/_shared/tracks/sdd.md` reference that table; they do not restate it.

## What a prd is

The record of **what the product must achieve and why** for one unit of product
decision — a whole product or a single feature. A `prd` states the problem, the
beneficiary, the measured outcome, and the requirements as outcomes. It is the
document a reader opens to learn what result the work owes the user and the
business, before any behavior is fixed.

**Routing gate:** if the document answers *"what behavior can consumers rely on
right now"* (surface, triggers and responses, invariants, error paths), it is a
`spec` — not a `prd`. If it answers *"in what order do we build it"*, it is a
`plan`. If it answers *"why did we pick this option over that one"*, it is an
`adr`. The list below carries the types that gate does not name.

This gate is the reverse direction of the routing gate in
`skills/_shared/spec-contract.md`. Both gates describe one boundary.

## When NOT to write a prd

- An unexplored concept and its value → `idea`
- Evidence gathered before a decision → `rnd`
- Market, business, or user discovery that opens a requirements cascade →
  `mrd`, `brd`, `urd`
- Regulated or traceable requirements → the ISO cascade `brs` → `strs` →
  `syrs` → `srs`

## Mandatory sections

1. **Vision** — the outcome this unit of product decision reaches, in one to
   three sentences. MUST name the product or feature and the result it produces.
2. **Problem Statement** — the current situation, its cost, and the beneficiary.
   MUST name who carries the problem today.
3. **Goals and Success Metrics** — the measured outcome that tells the team the
   product worked. Each metric carries a value with units, or an `[assumption]`
   marker per `skills/_shared/precision-rules.md` Rule 4.
4. **Requirements** — numbered outcomes the product owes. See Requirement form
   below.

A `prd` MAY add `## Out of Scope`, `## Dependencies`, and `## Clarifications`.
It carries no other section.

## Requirement form

A `prd` requirement states **an outcome**: what the product must achieve, for
whom, at what threshold. It does not state the trigger, the response, the
surface, or the error path — those are `spec` content.

- Write each requirement as one numbered declarative line.
- Do not use EARS clause order in a `prd`. `WHEN <trigger>, the <subject> MUST
  <response>` is `spec` notation, and a `prd` line written that way has moved
  into the `spec`'s territory.
- Do not use BCP 14 modals (`MUST`, `SHOULD`, `MAY`) in a `prd`. A `prd` states
  a wanted result, and a normative modal claims an obligation the `prd` cannot
  verify. The ISO requirement types (`brs`, `strs`, `syrs`, `srs`) keep their
  own notation and their stable identifiers; this rule governs `prd` alone.
- One requirement per line, one outcome per requirement.

Non-normative examples of the same content on both sides of the boundary:

| prd requirement (outcome) | spec behavior (contract) |
|---|---|
| Export finishes without the user waiting on the page. | `WHEN the user requests an export, the service MUST return a job ID within 200 ms.` |
| A failed delivery never loses the event. | `IF the subscriber returns 5xx, THEN the service MUST retry per the backoff schedule.` |

## Content-kind ownership

Each content kind below has **one** owning document. The composing skill MUST
write a content kind only into its owner.

| Content kind | Owner | Section |
|---|---|---|
| The concept and the opportunity it opens | `idea` | Idea, Value |
| The problem, its cost, and who carries it | `prd` | Problem Statement |
| The measured outcome the work targets | `prd` | Goals and Success Metrics |
| What the product owes, as an outcome | `prd` | Requirements |
| The interface, parts, states, and fields dependents see | `spec` | Surface |
| Behavior a consumer relies on | `spec` | Normative Behavior |
| Hard limits and conditions that always hold | `spec` | Constraints & Invariants |
| Error, edge, and degradation behavior | `spec` | Failure Behavior |
| What makes an implementation correct | `spec` | Conformance |
| The order of work, its phases and tasks | `plan` | Tasks |
| The check that the delivered change is complete | `plan` | Acceptance Criteria |
| Why one option was chosen over another | `adr` | Decision, Alternatives Considered |

Rules:

1. WHEN a document on the topic already owns a content kind, the composing skill
   MUST NOT restate that content in a second document.
2. WHEN a downstream gate produces the owner of a content kind the upstream
   draft carries, the composing skill MUST edit the upstream statement to keep
   only the outcome that document owns and to remove the detail that moved, in
   the same `update_document` call that closes the gate.
3. A document MAY name the outcome the linked document specifies. It MUST NOT
   reproduce that document's line.
4. The coverage category `Completion Signals`
   (`skills/_shared/coverage-taxonomy.md`) reaches three of the sections above —
   `prd` Goals and Success Metrics, `plan` Acceptance Criteria, `spec`
   Conformance. Coverage at one gate does not close the category at another, and
   copying a `prd` metric into a `plan` acceptance criterion breaks rule 1.

## Scope rule

One `prd` covers one unit of product decision — a whole product or a single
feature. Size never changes the type.

- A feature-scoped `prd` uses the same four sections, compressed to a target of
  40 lines or fewer. A product-level `prd` carries no line target.
- A product-level `prd` links each feature-scoped `prd` it covers through
  `implements` relations, added with `mcp__archcore__add_relation`.
- Routing stays content-kind-based, per the ownership table above, never
  size-based.
- A `prd` is not owed on every topic. WHEN the request is feature-scoped and an
  `idea`, `rnd`, or `adr` on the topic already records the problem and the
  goals, the track continues straight to the `spec` and links it to that
  upstream document. The `sdd.require` gate in `skills/_shared/tracks/sdd.md`
  carries this compression path as a `skip_when` condition.

Recorded in `no-frd-type-prd-scope-rule.adr`.

## Status

A `prd` is created with `status: draft`; the `closeout.accept` gate
(`skills/_shared/tracks/closeout.md`) performs the draft → accepted transition
after the user confirms it, per `document-status-transitions.adr`.

## Forbidden in the body

- A section enumerating other `.archcore/` documents → the relation graph
  carries those links, per `skills/_shared/precision-rules.md` Rule 5.
- A code block, unless the exact textual format is itself the requirement.

Content another type owns is not listed again here. The ownership table above is
the one place that assignment lives.

## Enforcement

The Archcore CLI checks the mechanical part of this contract in the post-tool-use
hook — the mandatory sections, the requirement form, the ownership headings, and
near-verbatim restatement across an `implements` or `extends` link — under the
advisory pattern in `skills/_shared/precision-rules.md`. Where the hook is
silent, the gate exit checks carry the contract alone.

Whether a document **paraphrases** the document it links to is not decidable
there at any version. That judgement stays with the executing skill at the gate
exit checks in `skills/_shared/tracks/sdd.md`.

## Rationale

The `prd` is the one type in the `sdd` track that had no content contract, so
the `prd`/`spec` boundary was stated only from the `spec` side. A gate can check
that a section is present; it cannot judge whether the section repeats the
document upstream of it. The ownership table gives every gate one objective
question — *which document owns this kind of statement* — and gives the
composing skill a place to move content to instead of a second copy.

`sdd.decompose` asks zero questions and composes from upstream drafts. Without
an ownership table, the only content that gate can produce is a restatement of
the `prd` and the `spec`.

## Examples

### Good (feature-scoped prd, compressed)

```markdown
## Vision
Catalog exports leave the product as a file the user receives by email, so a
large export no longer holds the browser tab open.

## Problem Statement
An export over 20 000 rows blocks the catalog page until it finishes; support
receives roughly 15 reports a month from operations staff who close the tab and
lose the work.

## Goals and Success Metrics
- Exports blocking the page: 0 (today: every export over 20 000 rows).
- Support reports about lost exports: under 2 a month by the end of Q3.

## Requirements
1. The user starts an export and continues working in the catalog.
2. The user receives the finished file without returning to the page.
3. An export that fails tells the user it failed, and why.
```

### Bad (crosses three boundaries)

```markdown
## Requirements
1. WHEN the user requests an export, the service MUST return a job ID within
   200 ms.
2. `POST /exports` accepts `{format, filters}` and returns `{jobId}`.
3. Phase 1 delivers the queue; phase 2 delivers the email sender.
4. We chose SQS over Redis because the team already operates it.
```

(Line 1 is `spec` Normative Behavior; line 2 is `spec` Surface; line 3 is `plan`
Tasks; line 4 is `adr` Decision. The outcome those four lines share belongs in
the `prd`: "The user starts an export and continues working in the catalog.")
