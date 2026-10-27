---
name: document
argument-hint: "[subject]"
description: "Record a decision, document existing code, or file a supplied research material, in free text; no first word is a mode. Use for 'we decided', 'record this decision', 'document why we chose X', 'make it our standard', 'draft an RFC', 'should we switch to Y' proposals, 'resolve the RFC', 'we accepted the proposal', 'document the auth module', 'capture how the payment system works', reference material, how-to instructions, a repeated agent procedure, a user flow with examples over an existing spec, or a finished report or one external material already in hand. Name any document type inside the subject — journey, prd, idea, or cpat included — to get exactly that type. Planning a feature, an investigation not yet done, or an intended user journey the request asks to plan ('plan the onboarding journey') → /archcore:plan. Checking docs against code or docs health → /archcore:review."
---

# /archcore:document

Record the present state: a technical decision, existing code, or a supplied
research material. Context resolution (`skills/_shared/gate-contract.md`,
section Context resolution) classifies the request and finds the present owner;
a gate inside the selected track selects the document type. Write affinity: knowledge
types; a filed `research` and the decision cascade's `plan` belong to vision.
The standard cascade can add a `cpat` (experience). A type the user names
explicitly keeps its own category (Named type below).

Command tense: `/archcore:plan` declares a future canon delta, `/archcore:document`
records the present state — including work that shipped without a plan — and
`/archcore:review` reconciles a past declared delta. Claim vocabulary:
`skills/_shared/delta-routing.md`.

Load `skills/_shared/gate-contract.md` and `skills/_shared/elicitation-contract.md` before executing any gate.

## Tracks

| Classification | Track and entry | Types the entry gate selects |
|---|---|---|
| decision | `skills/_shared/tracks/decision.md`, `decision.classify` | `adr`, `rfc`; `rule` through the standard cascade; an existing `rfc` draft on the topic → `decision.resolve`, which records an `adr` on an accepted verdict |
| code-doc | `skills/_shared/tracks/describe.md`, `describe.read` | `spec`, `guide`, `task-type`, `scenario`, `doc` |
| research material | `skills/_shared/tracks/research.md`, `research.frame` | `research`, `rnd` by the closing test; one external material → `evidence` |

No first word is a mode. When the subject text names a type (`skills/_shared/gate-contract.md`,
Entry terms) that the selected track produces, the selecting gate treats that type as settled and asks no
type question: `record an rfc for gRPC` reaches the RFC branch; a leading type
slug takes the Named type path. No track produces a `journey`; a `journey` comes
from `/archcore:plan` or from the named-type path below.

### Named type

WHEN the first word of the subject is a kernel document type slug, or the subject writes a slug in
backticks, the named type wins over routing (`explicit-type-request-wins.adr`).
A slug elsewhere in plain topic text names no type here; inside a track the gate
contract's naming rule still applies. When two slugs qualify, the
first one wins.

1. IF a document track produces the named type as its own product, THEN enter that track with the type settled: `adr`, `rfc` → decision; `spec`, `doc`, `guide`, `scenario` → describe; `research`, `rnd`, `evidence` → research.
2. IF no document track produces it as its own product — `rule`, `journey`, `prd`, `idea`, `plan`, `cpat`, `task-type`, `mrd`, `brd`, `urd`, `brs`, `strs`, `syrs`, `srs` — THEN compose it directly per the steps below. A `rule` comes from the decision track only as a cascade member behind an `adr`; a named `rule` needs neither.
3. Apply the compatibility file for the type before the first MCP call that names it.
4. Search `.archcore/` for a local document of that type on the topic; when one exists, offer to update it instead.
5. Load `skills/_shared/<type>-contract.md` when that file exists, and `skills/_shared/precision-rules.md`.
6. WHEN no contract file exists, compose the sections of the `create_document` template for that type.
7. Create the document with `status: draft` through `create_document`.
8. Evaluate relations through `skills/_shared/relation-authoring.md`.
9. WHEN the type's routing condition fails, report it in one result line naming the better-fitting type; ask no question.

Examples of a failed routing condition: a `journey` where a covering `spec`
exists (`scenario` fits), a `plan` composed without the conductor (it
carries no Declared Delta), or a `rule` with no `adr` recording its reason.

## When to use

- "We decided to go with microservices" — settled decision
- "Record the decision to use PostgreSQL"
- "Document why we chose JWT over sessions"
- "Make this our team standard for error handling"
- "Draft an RFC for switching from REST to gRPC"
- "Should we switch to Kubernetes?" — open choice: one question offers an `adr`, an `rfc` (resolved into an `adr` later), or investigating first
- "We accepted the proposal — resolve the RFC" — proposal resolution
- "Document the auth module"
- "Capture how the payment system works"
- "Create reference docs for the config system" — reference material
- "Write a guide for the release process" — how-to instructions
- "Write down how the agent cuts a release" — a repeated agent procedure (`task-type`)
- "Scenario for checkout over the checkout spec" — a user flow with examples over an existing spec
- "File this benchmark report" — a ready investigation
- "File this vendor PDF as evidence" — one external material

**Not document:**

- Planning a feature, an initiative, or an intended user journey the request does not name as a `journey` → `/archcore:plan`
- Checking documents against code, reviewing branch changes, or a documentation audit → `/archcore:review`
- First-time setup → `/archcore:init`

## Routing table

| Signal | Route |
|---|---|
| No arguments, one draft with a state block this command resumes | → resume it |
| No arguments, branch changes or supplied material name a present fact | → a start menu of at most four owners, each with its evidence, the smallest owner first |
| No arguments and no reliable signal | → ask one question: what present fact or subject to record |
| The subject names a document type that no document track produces | → Named type, direct composition |
| Decision signals: "we decided", "record this decision", "document why we chose X", "make it our standard", "draft an RFC", a "should we switch to Y" question (the decision track asks which exit). A bare "compare X vs Y" with no proposed target belongs to `/archcore:plan`'s research track; a proposal to add a new capability with no named technical target ("should we add caching?") is feature framing → `/archcore:plan` | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.classify` |
| Resolution signals: "resolve the RFC", "we accepted the proposal", "reject the RFC" — an `rfc` draft exists on the topic | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.resolve` |
| Code-doc signals: "document the auth module", "capture how the payment system works", reference material (registry, glossary, lookup), how-to instructions, a repeated agent procedure, a user flow with examples over an existing `spec` | → describe track — `skills/_shared/tracks/describe.md`, entry at `describe.read` |
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
type filter below. On older engines, keep the legacy filter; a request to
describe code whose subject names `scenario` then reports the required version
and exits without a write.
When the probe returns `yes`, add `research` and `evidence` to the type filter
below. On older engines, keep the legacy filter.

Search `.archcore/` on the request topic across all three categories — vision,
knowledge, experience. Do not exclude a category from reads. Pass a type filter
matched to this command's moment (`adr`, `rfc`, `spec`, `doc`, `guide`, `rule`,
plus `rnd` as decision evidence, and `research` and `evidence` when the probe returned `yes`) instead of relying on the global type ranking. When a found document carries
`implements`, `depends_on`, or `related` relations, pull the linked documents one hop across
categories. Duplicate handling lives in the tracks' check-existing gates — do
not resolve duplicates here.

WHEN a found draft on the topic carries an `archcore:track` state block,
resume it per the resume rules in `skills/_shared/gate-contract.md` instead of
opening a new track; a block this command does not resume follows resume
rules 8 and 9 there.

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

### Step 2: Resolve context

Build the context record per `skills/_shared/gate-contract.md`, section Context
resolution. IF the subject names a type per Named type above, THEN apply Named
type first. IF accepted canon conflicts with the code the request describes,
THEN report the conflict before any write.

### Step 3: Classify

Classify the target as resolution, decision, code-doc, research material, or unclear:

- **Resolution** — the request names a verdict on an existing open proposal
  (resolution signals above) and an `rfc` draft on the topic exists → decision
  track at `decision.resolve`. Check this before Decision: wording that also
  reads as a settled-decision signal ("we accepted the proposal") routes here
  whenever a matching `rfc` draft exists.
- **Decision** — the request records a settled choice or an open proposal
  (decision signals above) → decision track at `decision.classify`, which
  selects `adr`, `rfc`, or the standard outcome. A type name in the subject
  (`adr`, `rfc`, `rule`) satisfies that gate's `skip_when`.
- **Code-doc** — the request describes existing code, reference material, a
  procedure, or a user flow over an existing `spec` (code-doc signals above) →
  describe track at `describe.read`. `describe.read` records
  `features/*.feature` files as evidence when present; a `scenario` with no
  covering `spec` routes to the earliest gate that produces the `spec` per
  `skills/_shared/gate-contract.md`.
- **Research material** — the request supplies a ready report or one external
  material to file (research-material signals above) → research track at
  `research.frame`;
  the supplied report satisfies frame inputs without an interview (investigation versus one external material:
  `skills/_shared/gate-contract.md`, Entry terms), and the closing test selects
  the type — a report that ends in a recommendation is an `rnd`, a report that
  covers a scope is a `research`. One external material with no investigation
  enters `research.gather` as standalone evidence, records the request in the
  evidence draft's Clarifications, and exits after gather. Follow the
  compatibility contract's no-write exit when the type is unsupported.
- **No material** — the request asks an unanswered question, including a bare
  "compare X and Y" with no proposed target, and supplies
  neither a report nor a material → write nothing and name `/archcore:plan
  <topic>` for a new investigation.
- **Unclear** — inspect git state and the working tree first: recent commits and
  changed files are evidence of what the user has been working on. If the
  evidence still supports both readings, ask one classifying question — "Is this
  a decision to record or existing code to document?" — with the recommendation
  drawn from the git evidence.

### Step 4: Execute the track

Run the selected track gate by gate per `skills/_shared/gate-contract.md`. The
track owns check-existing, per-gate elicitation, composition, and relation
wiring.

Question budget: the ceiling of 5 questions per invocation in
`skills/_shared/elicitation-contract.md`.

## Result

Report the produced documents grouped by category:

- **knowledge** — `adr`, `rfc`, `spec`, `doc`, `guide`, `rule`, `evidence`, `scenario`
- **vision** — `research` (scope-covering report), `rnd` (recommendation-closed report, or compatibility fallback), `plan` (architecture cascade)
- **experience** — `task-type` (repeated agent procedure), `cpat` (standard cascade opt-in)
- any category — a type composed on the Named type path, with its routing-condition line when one failed

List each document's path and relation edges. Name tracks and steps in plain
words; do not print a gate address of the form `<track>.<stage>`. Close with one
recommended next action naming only `/archcore:plan`, `/archcore:review`, or a
repeat `/archcore:document` invocation with its subject. WHEN a gate stopped on a
blocking exit check, the next action is the resume command for that draft.
WHEN the run created drafts other than an `rfc` and no `plan` covers them, the
next action is `/archcore:review`, which offers their acceptance. An `rfc`
resolves through `/archcore:document resolve the <rfc title> RFC`.
