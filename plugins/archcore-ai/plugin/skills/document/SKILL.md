---
name: document
argument-hint: "[module, topic, or decision] [adr|rfc|spec|doc|guide|rule|research|evidence]"
description: "Record a decision or document existing code. Use for 'we decided', 'record this decision', 'document why we chose X', 'make it our standard', 'draft an RFC', 'should we switch to Y' proposals, 'resolve the RFC', 'we accepted the proposal', 'document the auth module', 'capture how the payment system works', reference material, or how-to instructions. Use document research to file an existing investigation report, or document evidence to file one external material. Planning a feature → /archcore:plan. Checking docs against code or docs health → /archcore:review."
---

# /archcore:document

Record a technical decision or document existing code. The skill classifies the
request, then executes a gated track: decision, describe, or research for an
explicit report or material. Write affinity: knowledge types; a filed `research`
and the decision cascade's `plan` belong to vision. The standard cascade can
add a `cpat` (experience).

Command tense: `/archcore:plan` declares a future canon delta, `/archcore:document`
records the present state — including work that shipped without a plan — and
`/archcore:review` reconciles a past declared delta. Δ vocabulary:
`skills/_shared/delta-routing.md`.

Load `skills/_shared/gate-contract.md` and `skills/_shared/elicitation-contract.md` before executing any gate.

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
- `document research <report>` — file a ready investigation
- `document evidence <material>` — file one external material

**Not document:**

- Planning a feature or initiative → `/archcore:plan`
- Checking documents against code, reviewing branch changes, or docs health → `/archcore:review`
- First-time setup → `/archcore:init`

## Routing table

| Signal | Route |
|---|---|
| The invocation names a type — `adr`, `rfc`, `spec`, `doc`, `guide`, `rule`, `research`, `evidence` | → expert form, no routing (Step 2) |
| Decision signals: "we decided", "record this decision", "document why we chose X", "make it our standard", "draft an RFC", a "should we switch to Y" proposal. A bare "compare X vs Y" with no proposed target belongs to `/archcore:plan`'s research track; a proposal to add a new capability with no named technical target ("should we add caching?") is feature framing → `/archcore:plan`, sdd track | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.classify` |
| Resolution signals: "resolve the RFC", "we accepted the proposal", "reject the RFC" — an `rfc` draft exists on the topic | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.resolve` |
| Code-doc signals: "document the auth module", "capture how the payment system works", reference material (registry, glossary, lookup), how-to instructions | → describe track — `skills/_shared/tracks/describe.md`, entry at `describe.read` |
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
When the probe returns `yes`, add `research` and `evidence` to the type filter
below. On older engines, keep the legacy filter.

Search `.archcore/` on the request topic across all three categories — vision,
knowledge, experience. Do not exclude a category from reads. Pass a type filter
matched to this command's moment (`adr`, `rfc`, `spec`, `doc`, `guide`, `rule`,
plus `rnd` as decision evidence, and `research` and `evidence` when the probe returned `yes`) instead of relying on the global type ranking. When a found document carries
`implements` or `related` relations, pull the linked documents one hop across
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

### Step 2: Expert form

If the invocation names a type, execute the named path without routing:

- `research` → research track at `research.frame`; the track selects `research`
  or `rnd` by its closing test — a report that ends in a recommendation is an
  `rnd`, a report that covers a scope is a `research`; the supplied report satisfies frame inputs without an interview.
- `evidence` → research track at `research.gather`, standalone material;
  the request satisfies frame, recorded in the evidence draft's Clarifications.
  This entry needs no parent investigation and exits after gather. Follow the
  compatibility contract's no-write exit when the type is unsupported.
- `adr` → decision track at `decision.adr`
- `rfc` → decision track at `decision.rfc`
- `spec`, `doc`, `guide` → describe track at `describe.read`; the named type
  settles `describe.draft`'s type question, so its elicitation trigger does not
  fire. `describe.read`'s own skip_when fast-paths a request that already
  carries the evidence.
- `rule` → decision track, creation at `decision.cascade`; a missing upstream
  document routes per `skills/_shared/gate-contract.md`

Then go to Step 4.

### Step 3: Classify

Classify the target as resolution, decision, code-doc, or unclear:

- **Resolution** — the request names a verdict on an existing open proposal
  (resolution signals above) and an `rfc` draft on the topic exists → decision
  track at `decision.resolve`. Check this before Decision: wording that also
  reads as a settled-decision signal ("we accepted the proposal") routes here
  whenever a matching `rfc` draft exists.
- **Decision** — the request records a settled choice or an open proposal
  (decision signals above) → decision track at `decision.classify`.
- **Code-doc** — the request describes existing code, reference material, or a
  procedure (code-doc signals above) → describe track at `describe.read`.
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
from the shared per-invocation ceiling; expert invocation raises to the track's
per-gate maxima.

## Result

Report the produced documents grouped by category:

- **knowledge** — `adr`, `rfc`, `spec`, `doc`, `guide`, `rule`, `evidence`
- **vision** — `research` (scope-covering report), `rnd` (recommendation-closed report, or compatibility fallback), `plan` (architecture cascade)
- **experience** — `cpat` (standard cascade opt-in)

List each document's path and relation edges. Close with one recommended next
action naming only `/archcore:plan`, `/archcore:review`, or a repeat
`/archcore:document` invocation.
