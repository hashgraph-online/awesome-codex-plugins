---
name: document
argument-hint: "[decision|code|research] [subject]"
description: "Record a decision, document existing code, or file a supplied research material. Modes: document decision (ADR, RFC, or rule), document code (spec, doc, guide, or scenario for existing behavior), document research (only when a finished report or one external material is already in hand). Use for 'we decided', 'record this decision', 'document why we chose X', 'make it our standard', 'draft an RFC', 'should we switch to Y' proposals, 'resolve the RFC', 'we accepted the proposal', 'document the auth module', 'capture how the payment system works', reference material, how-to instructions, or a user flow with examples over an existing spec. Name the type inside the subject to skip the type question. Planning a feature or an intended user journey → /archcore:plan. Checking docs against code or docs health → /archcore:review."
---

# /archcore:document

Record the present state: a technical decision, existing code, or a supplied
research material. The first word of the arguments selects the mode; a gate
inside the mode's track selects the document type. Write affinity: knowledge
types; a filed `research` and the decision cascade's `plan` belong to vision.
The standard cascade can add a `cpat` (experience).

Command tense: `/archcore:plan` declares a future canon delta, `/archcore:document`
records the present state — including work that shipped without a plan — and
`/archcore:review` reconciles a past declared delta. Δ vocabulary:
`skills/_shared/delta-routing.md`.

Load `skills/_shared/gate-contract.md` and `skills/_shared/elicitation-contract.md` before executing any gate.

## Modes

| Mode | Track and entry | Types the entry gate selects |
|---|---|---|
| `decision` | `skills/_shared/tracks/decision.md`, `decision.classify` | `adr`, `rfc`; `rule` through the standard cascade; an existing `rfc` draft on the topic → `decision.resolve`, which records an `adr` on an accepted verdict |
| `code` | `skills/_shared/tracks/describe.md`, `describe.read` | `spec`, `doc`, `guide`, `scenario` |
| `research` | `skills/_shared/tracks/research.md`, `research.frame` | `research`, `rnd` by the closing test; one external material → `evidence` |

A document type name is not a mode. When the subject text names a type (`skills/_shared/gate-contract.md`,
Entry terms) that the mode's track produces, the selecting gate treats that type as settled and asks no
type question: `document decision rfc for gRPC` reaches the RFC branch. A leading
word that is not a mode is topic text and goes through classification (Step 3).
No mode produces a `journey`; an intended user path belongs to `/archcore:plan`.

## When to use

- "We decided to go with microservices" — settled decision
- "Record the decision to use PostgreSQL"
- "Document why we chose JWT over sessions"
- "Make this our team standard for error handling"
- "Draft an RFC for switching from REST to gRPC"
- "Should we switch to Kubernetes?" — open proposal
- "We accepted the proposal — resolve the RFC" — proposal resolution
- "Document the auth module"
- "Capture how the payment system works"
- "Create reference docs for the config system" — reference material
- "Write a guide for the release process" — how-to instructions
- `document code scenario for checkout` — a user flow with examples over an existing spec
- `document research <report>` — file a ready investigation
- `document research <material>` — file one external material as evidence

**Not document:**

- Planning a feature, an initiative, or an intended user journey → `/archcore:plan`
- Checking documents against code, reviewing branch changes, or docs health → `/archcore:review`
- First-time setup → `/archcore:init`

## Routing table

| Signal | Route |
|---|---|
| No arguments | → git investigation of the branch changes, then one classifying question (Step 3, Unclear) |
| The first word is a mode — `decision`, `code`, `research` | → mode entry, no routing (Step 2) |
| Decision signals: "we decided", "record this decision", "document why we chose X", "make it our standard", "draft an RFC", a "should we switch to Y" proposal. A bare "compare X vs Y" with no proposed target belongs to `/archcore:plan`'s research track; a proposal to add a new capability with no named technical target ("should we add caching?") is feature framing → `/archcore:plan`, sdd track | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.classify` |
| Resolution signals: "resolve the RFC", "we accepted the proposal", "reject the RFC" — an `rfc` draft exists on the topic | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.resolve` |
| Code-doc signals: "document the auth module", "capture how the payment system works", reference material (registry, glossary, lookup), how-to instructions, a user flow with examples over an existing `spec` | → describe track — `skills/_shared/tracks/describe.md`, entry at `describe.read` |
| Research-material signals: a supplied investigation report, benchmark, transcript, or vendor document to file as is | → research track — `skills/_shared/tracks/research.md`, entry at `research.frame` |
| Unclear | → git investigation, then one classifying question (Step 3) |

## Execution

### Step 1: Ground

Apply `skills/_shared/research-compatibility.md` under its condition 1 — a
request or type naming `research` or `evidence`, the research track, or a
grounding result of either type. If this skill has no shell tool and no probe
result was supplied, report `needs-vocabulary-probe` with the helper path and
stop before the first MCP call that names either type.
Before delegating research or evidence work, pass the current vocabulary probe
result and absolute plugin root to the assistant. If the assistant returns
`needs-vocabulary-probe`, run the helper and resume the same task.
Before delegating any other document write or relation work, pass the absolute
plugin root to the assistant. The assistant reads
`skills/_shared/relation-authoring.md` under that root.
Apply `skills/_shared/actor-subject-compatibility.md` under its own condition 1 —
a request whose subject names `scenario` or `journey`, or a grounding result of
either type. When that probe returns `yes`, add `scenario` and `journey` to the
type filter below. On older engines, keep the legacy filter; a `code` request
whose subject names `scenario` then reports the required version and exits
without a write.
When the probe returns `yes`, add `research` and `evidence` to the type filter
below. On older engines, keep the legacy filter.

Search `.archcore/` on the request topic across all three categories — vision,
knowledge, experience. Do not exclude a category from reads. Pass a type filter
matched to this command's moment (`adr`, `rfc`, `spec`, `doc`, `guide`, `rule`,
plus `rnd` as decision evidence, and `research` and `evidence` when the probe returned `yes`) instead of relying on the global type ranking. When a found document carries
`implements`, `depends_on`, or `related` relations, pull the linked documents one hop across
categories. Duplicate handling lives in the tracks' check-existing gates — do
not resolve duplicates here.

If `.archcore/` does not exist, announce initialization in one line and call
`mcp__archcore__init_project` without asking a question. If `.archcore/` exists
but contains no documents, proceed on outer-context grounding and report that
zero documents were found.

**Global sources.** If a `mcp__archcore__list_documents` /
`mcp__archcore__search_documents` result has `global: true` / `read_only: true` /
`source_kind: "global"`, load `skills/_shared/globals.md`. Also load it when a
`search_documents` response's `coverage` names a source other than `"local"` —
even when `results` is empty: the empty page is exactly where that file's retry
ladder applies. Never modify a global document and never target one with
`add_relation`. Absent any global match, proceed as usual.

### Step 2: Mode entry

If the first word is a mode, execute the mapped entry without routing:

- `decision` → decision track. An `rfc` draft on the topic plus resolution
  wording enters `decision.resolve`; any other request enters
  `decision.classify`, which selects `adr`, `rfc`, or the standard outcome. A
  type name in the subject (`adr`, `rfc`, `rule`) satisfies that gate's
  `skip_when`.
- `code` → describe track at `describe.read`. `describe.draft` selects `spec`,
  `doc`, `guide`, or `scenario`; a type name in the subject settles its type
  question. `describe.read` records `features/*.feature` files as evidence when
  present; a `scenario` with no covering `spec` routes to the earliest gate that
  produces the `spec` per `skills/_shared/gate-contract.md`.
- `research` → research track at `research.frame`; the supplied report satisfies frame inputs without an interview (investigation versus one external material: `skills/_shared/gate-contract.md`, Entry terms), and the closing test selects the type — a
  report that ends in a recommendation is an `rnd`, a report that covers a scope
  is a `research`. One external material with no investigation enters
  `research.gather` as standalone evidence, records the request in the evidence
  draft's Clarifications, and exits after gather. Follow the compatibility
  contract's no-write exit when the type is unsupported.

Then go to Step 4.

### Step 3: Classify

Classify the target as resolution, decision, code-doc, research material, or unclear:

- **Resolution** — the request names a verdict on an existing open proposal
  (resolution signals above) and an `rfc` draft on the topic exists → decision
  track at `decision.resolve`. Check this before Decision: wording that also
  reads as a settled-decision signal ("we accepted the proposal") routes here
  whenever a matching `rfc` draft exists.
- **Decision** — the request records a settled choice or an open proposal
  (decision signals above) → decision track at `decision.classify`.
- **Code-doc** — the request describes existing code, reference material, a
  procedure, or a user flow over an existing `spec` (code-doc signals above) →
  describe track at `describe.read`.
- **Research material** — the request supplies a ready report or one external
  material to file (research-material signals above) → research track at
  `research.frame`.
- **Unclear** — inspect git state and the working tree first: recent commits and
  changed files are evidence of what the user has been working on. If the
  evidence still supports both readings, ask one classifying question — "Is this
  a decision to record or existing code to document?" — with the recommendation
  drawn from the git evidence.

### Step 4: Execute the track

Run the selected track gate by gate per `skills/_shared/gate-contract.md`. The
track owns check-existing, per-gate elicitation, composition, and relation
wiring.

Question budget: per `skills/_shared/elicitation-contract.md` — auto mode draws
from the shared per-invocation ceiling; a mode entry raises to the track's
per-gate maxima.

## Result

Report the produced documents grouped by category:

- **knowledge** — `adr`, `rfc`, `spec`, `doc`, `guide`, `rule`, `evidence`, `scenario`
- **vision** — `research` (scope-covering report), `rnd` (recommendation-closed report, or compatibility fallback), `plan` (architecture cascade)
- **experience** — `cpat` (standard cascade opt-in)

List each document's path and relation edges. Name tracks and steps in plain
words; do not print a gate address of the form `<track>.<stage>`. Close with one
recommended next action naming only `/archcore:plan`, `/archcore:review`, or a
repeat `/archcore:document` invocation with its mode.
