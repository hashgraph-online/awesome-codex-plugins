# Spec Content Contract

Plugin runtime asset. Loaded by skills creating specs: `document` (the describe
track and the decision track's architecture cascade), `plan` (the contract
instrument at `sdd.design`), and `init` (Phase E hotspot specs). Companion to
`skills/_shared/precision-rules.md`.

## What a spec is

The durable, normative description of **behavior others rely on right now** — one API,
interface, schema, protocol, feature, or subsystem whose externally-observable behavior
other code, teams, UI surfaces, or sibling modules depend on. A spec exists so anyone
touching the subject reads one authoritative account of how it must behave, instead of
re-deriving it from drifting code or from an ADR (which records only *why*). A spec may
be written **after** code (capture the behavior of what exists) or **before** it
(specify what to build). One subject per spec — and **one form**: the same six sections
regardless of subject.

**Routing gate:** if the document answers *"what should we build and why"* (user
stories, priorities, success metrics), it is a `prd` (or ISO `syrs`/`srs`) — not a spec.
If it answers *"what behavior can consumers rely on right now"*, it is a spec.

## When NOT to write a spec

- Requirements / what is needed and why → `prd` (or ISO `syrs` / `srs`)
- Task breakdown / execution order → `plan`
- Rationale / why a choice was made → `adr`
- Non-normative reference (tables, registries, glossaries) → `doc`
- Team-wide human practice ("always do X") → `rule`
- A trivial internal helper, or behavior nobody depends on → not a spec

## Mandatory sections

1. **Purpose & Scope** — the one subject this spec is normative for, and what it does
   not cover. MUST name the subject and who depends on it (external code, teams,
   users/UI, or sibling modules).
2. **Surface** — what dependents see of the subject: the externally-observable
   interface (inputs, outputs, signatures) and/or the parts, states, and data fields
   that drive behavior — each with its canonical identifier (`@path/to/file`). MUST
   reference, not reproduce, source definitions — copied signatures go stale against
   the code.
3. **Normative Behavior** — numbered behavioral requirements in the notation below,
   each numbered for traceability.
4. **Constraints & Invariants** — hard limits (each with a rationale) and conditions
   that MUST always hold, listed separately. Plain BCP 14 statements — EARS clauses
   are not required here (EARS fits triggered behavior poorly here).
5. **Failure Behavior** — error and edge conditions with the observable outcome of
   each: response and recovery semantics (retriable? idempotent? timeout behavior?)
   and degradation on bad, empty, or missing input or on dependency failure. Same
   notation as Normative Behavior.
6. **Conformance** — what makes an implementation correct: satisfies all MUST
   requirements, all invariants, and all failure rules. MAY close with ONE
   non-normative example block (≤ 5 lines, Given/When/Then) anchoring the most
   load-bearing behavior.

## Notation

Each numbered line in **Normative Behavior** and **Failure Behavior** follows EARS
clause order with a BCP 14 keyword (RFC 2119 + RFC 8174: MUST / SHOULD / MAY,
uppercase only) as the modal:

- Ubiquitous: `The <subject> MUST <response>.`
- Event-driven: `WHEN <trigger>, the <subject> MUST <response>.`
- State-driven: `WHILE <state>, the <subject> MUST <response>.`
- Unwanted behavior: `IF <undesired condition>, THEN the <subject> MUST <response>.`

Four rules keep each numbered line strict-EARS conformant:

1. **Active voice, obligated subject.** The grammatical subject is the component
   that bears the obligation — never a subjectless passive. "Tokens MUST be
   rotated" names no obligated component; write `the <component> MUST rotate the
   token`. A plain `The <subject> MUST <response>` line is valid only when
   `<subject>` is that component, not a passive object.
2. **One line, one requirement, one modal.** Each numbered line carries exactly
   one modal keyword (MUST NOT counts as one). Split `MUST X and MUST NOT Y`
   into two numbered lines.
3. **Explicit trigger for event responses.** When behavior answers a command,
   request, or state change, open with `WHEN <trigger>,` (or `WHILE <state>,`) —
   the event is the trigger, never the grammatical subject. Do not bury the
   trigger inside the subject ("The /remember command invalidates the cache" →
   `WHEN the user invokes /remember, the <component> MUST invalidate the cache`).
4. **One clause, 25 words or fewer.** Past that a clause has usually taken on a
   second obligation, or buried the actor behind subordinate clauses. Split it,
   or move the qualifier into Constraints & Invariants.

Grade with intent: MUST only where required for interoperation or to prevent harm
(RFC 2119 §6 — sparingly); SHOULD where deviation needs a weighed reason; MAY for
true options. Existing conformant plain `X MUST Y` lines need no migration; add
trigger/state clauses when writing or editing a line whose behavior is conditional.

## Body cap

**≤ 120 lines, one number for every path.** Six sections, each a handful of
numbered/bulleted points — the "reference, don't reproduce" rule (Forbidden section
below) is what keeps a spec inside the cap even for a complex subject.

The cap counts the whole body, headings and blank lines included; on the six-section
form those alone take about 19 lines, so the room for requirements is nearer 100. The
extra room over the former 80 goes to Normative Behavior / Constraints & Invariants,
never to reproducing source.

The separate flagship cap that `/archcore:init` hotspot synthesis carried is folded
into this default — a synthesized spec and an authored one are now measured alike, and
`skills/_shared/grounding/detect-hotspots.md` "Flagship specs" keeps only the
decomposition treatment it always governed. The Archcore CLI enforces the same 120 in
`@templates/precision.go` (`MaxSpecBodyLines`), so the contract and the hook agree.

### Over the cap — decompose, never compress

A subject that does not fit the cap is a routing signal, not a formatting problem.
WHEN a draft exceeds its body cap, the composing skill MUST apply the first remedy
below that the evidence supports.

1. The skill MUST replace pasted source, schemas, and inventories with
   `@path/to/file` citations (Forbidden section below).
2. The skill MUST route foreign content to its owning type — rationale to an `adr`,
   stories and metrics to a `prd`, reference material to a `doc`, steps to a `guide`.
3. WHEN the subject exposes two or more independently consumable sub-surfaces, the
   skill MUST compose one spec per sub-surface, each inside the default cap
   (`filename=<subject-slug>-<sub-surface-slug>`).
4. The skill MUST link sub-specs to each other with `related` via
   `mcp__archcore__add_relation`.
5. IF no sub-surface boundary is unambiguous, THEN the skill MUST keep the subject as
   one spec — a cohesive contract is not split to satisfy a line count.
6. WHEN a spec stays over the cap under rule 5, the skill MUST name the excess and its
   reason in the closing report.
7. The skill MUST NOT delete normative content to fit the cap.

Rule 7 is the point of the whole section: truncation loses the contract, decomposition
preserves it. Sizing a delta's capability list follows the same boundary — see
`skills/_shared/capability-granularity.md`, which routes an over-cap capability to a
split by the same sub-surface test.

## Status (init-synthesized specs)

A hotspot `spec` synthesized by `/archcore:init` (Tier-2) is created with
`status: draft` in every case — it is derived heuristically from source + tests,
not authored or reviewed, so the user confirms it before it becomes canon. Same
rationale, and same default, as a heuristic-derived cross-cutting `rule`
(`skills/_shared/rule-contract.md`). This status default is specific to init's
synthesis path; a spec authored via `/archcore:document`
follows that skill's own status convention. A spec authored **ahead of the
code** (`sdd.design`) also stays `status: draft` until the implementation is
verified — the closeout track's accept gate performs the draft → accepted
transition, so the status field is what distinguishes an intended contract
from a verified one.

## Forbidden in the body

- Decision rationale ("we chose JWT because…") → belongs in a linked `adr`.
- User stories, priorities, success metrics → belong in a `prd` (routing gate above).
- General reference material (glossaries of everything, inventories) → belongs in a `doc`.
- Sequential how-to steps ("first call X, then Y") → belongs in a `guide`.
- A section enumerating other `.archcore/` documents (`## Related Documents`,
  `## References` listing ADRs/specs/rules). Cross-document links live in the relation
  graph via `mcp__archcore__add_relation`. The body MAY cite source code
  (`@path/to/file`), schemas, and external authorities. See
  `skills/_shared/precision-rules.md` Rule 5.

## Enforcement

The Archcore CLI reports the mechanical part of this contract in the post-tool-use
hook: the mandatory sections, `SHALL` in place of a BCP 14 modal, two modals in
one numbered line, a subjectless passive, a condition placed after the obligation
it controls, and a clause past 25 words.

The hook applies the same 120-line cap this contract states, so a spec composed at
the cap no longer reports a finding it was never meant to trip. That agreement
replaced an earlier split — an 80-line hook against a 120-line flagship allowance —
in which one finding per flagship spec was expected and the composing skill was left
to decide the finding did not apply.

One limit remains, and no version removes it: whether the spec covers **one** subject,
and whether Surface references the source instead of reproducing it, is not decidable
in the hook. Both are judgments the composing skill owns. The hook can say how long a
body is and where its mass sits; it cannot say whether that mass is one contract.

## Rationale

One form, not profiles — one template, varying content: pre-code requirement
bundles stay in `prd`/`srs`, and `spec` holds the durable behavior contract.
The notation is a deliberate hybrid: EARS clause templates force the trigger or
state to be stated explicitly — exactly where LLM agents otherwise guess —
while BCP 14 keywords add the MUST/SHOULD/MAY grading that plain-`shall` EARS
cannot express. The "reference, don't reproduce" rule keeps the spec from
becoming a second, drifting copy of the code it describes — the spec states the
contract, the code remains the implementation.

## Examples

Two subjects, one form — a called boundary and a UI feature use the same six sections.

### Good (boundary subject)

```markdown
## Purpose & Scope
This spec defines the webhook **delivery** contract: payload format, delivery
guarantees, retry policy, and signature verification. Normative for the delivery
service (@internal/webhooks/deliver.go); consumed by external subscriber endpoints.
Out of scope: the webhook **management** API (separate spec).

## Surface
- `Deliver(event Event) (Receipt, error)` — see `@internal/webhooks/deliver.go`.
- Payload schema: `@internal/webhooks/schema.json` (referenced, not reproduced).

## Normative Behavior
1. The service MUST sign every payload with HMAC-SHA256 over the raw body.
2. WHEN a delivery attempt fails, the service MUST retry with exponential backoff,
   up to 5 attempts.
3. WHEN the subscriber returns 2xx, the service MUST treat the event as delivered.

## Constraints & Invariants
- Constraint: payload size MUST NOT exceed 256 KB (downstream gateway limit).
- Invariant: each event is delivered at-least-once; the receipt ID is stable across retries.

## Failure Behavior
1. IF the subscriber returns 5xx or times out, THEN the service MUST retry per the
   backoff schedule (idempotent by event ID).
2. WHEN retries are exhausted, the service MUST mark the event `failed` and emit
   `delivery.failed`; no further automatic attempts.

## Conformance
An implementation is conformant when it satisfies behaviors 1–3, preserves the
at-least-once invariant, and follows the failure rules above.
```

### Good (feature subject)

```markdown
## Purpose & Scope
This spec governs the **content card** — the unit rendering a catalog item across
feed, search, and detail views, which rely on which fields drive which blocks.
Normative for the card renderer (@ui/card/*). Out of scope: the catalog data source
(separate spec) and styling tokens.

## Surface
- Blocks: header, media, meta, actions — see `@ui/card/blocks/`.
- Field → block: `status` drives the badge; `episodes[]` drives progress; `price`
  drives actions (hidden when absent).
- States: `loading`, `ready`, `partial`, `unavailable`.

## Normative Behavior
1. WHEN `episodes[]` is non-empty, the card MUST render the progress block.
2. WHILE `status` is `completed`, the card MUST show the completed badge.
3. WHILE `status` is `completed`, the card MUST NOT show the subscribe action.
4. The card MUST reach `ready` only when header and media fields are both present.

## Constraints & Invariants
- Invariant: exactly one primary action is visible in the `ready` state.

## Failure Behavior
1. IF a meta field is missing, THEN the card MUST degrade to `partial` — never
   error out; other blocks render.
2. IF the data source fails, THEN the card MUST enter `unavailable` with a retry
   affordance; no blocks render.

## Conformance
An implementation is conformant when it satisfies behaviors 1–4, holds the
single-primary-action invariant, and degrades per the failure rules.
```

### Bad (scope)

```markdown
## Purpose
This spec covers the webhook system. We chose webhooks because polling was slow.
First, register an endpoint, then send events to it. See the table of all event types.
As a user, I want reliable webhooks so that I never miss an update.
```

(Mixes rationale + how-to + reference + a user story. Split by subject — one subject
per spec; move the "why" to an `adr`, the steps to a `guide`, the event table to a
`doc`, the story to a `prd`.)
