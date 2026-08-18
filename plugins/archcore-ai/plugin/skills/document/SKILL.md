---
name: document
argument-hint: "[module, topic, or decision] [adr|rfc|spec|doc|guide|rule]"
description: "Record a decision or document existing code. Use for 'we decided', 'record this decision', 'document why we chose X', 'make it our standard', 'draft an RFC', 'should we switch to Y' proposals, 'resolve the RFC', 'we accepted the proposal', 'document the auth module', 'capture how the payment system works', reference material, or how-to instructions. Planning a feature → /archcore:plan. Checking docs against code or docs health → /archcore:review."
---

# /archcore:document

Record a technical decision or document existing code. The skill classifies the
request, then executes one gated track: the decision track for ADRs and RFCs, or
the describe track for specs, docs, and guides. Write affinity: knowledge types;
the decision cascade can add a `plan` (vision) or `cpat` (experience).

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

**Not document:**

- Planning a feature or initiative → `/archcore:plan`
- Checking documents against code, reviewing branch changes, or docs health → `/archcore:review`
- First-time setup → `/archcore:init`

## Routing table

| Signal | Route |
|---|---|
| The invocation names a type — `adr`, `rfc`, `spec`, `doc`, `guide`, `rule` | → expert form, no routing (Step 2) |
| Decision signals: "we decided", "record this decision", "document why we chose X", "make it our standard", "draft an RFC", a "should we switch to Y" proposal. A bare "compare X vs Y" with no proposed target belongs to `/archcore:plan`'s research track; a proposal to add a new capability with no named technical target ("should we add caching?") is feature framing → `/archcore:plan`, sdd track | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.classify` |
| Resolution signals: "resolve the RFC", "we accepted the proposal", "reject the RFC" — an `rfc` draft exists on the topic | → decision track — `skills/_shared/tracks/decision.md`, entry at `decision.resolve` |
| Code-doc signals: "document the auth module", "capture how the payment system works", reference material (registry, glossary, lookup), how-to instructions | → describe track — `skills/_shared/tracks/describe.md`, entry at `describe.read` |
| Unclear | → git investigation, then one classifying question (Step 3) |

## Execution

### Step 1: Ground

Search `.archcore/` on the request topic across all three categories — vision,
knowledge, experience. Do not exclude a category from reads. Pass a type filter
matched to this command's moment (`adr`, `rfc`, `spec`, `doc`, `guide`, `rule`,
plus `rnd` as decision evidence) instead of relying on the global type ranking. When a found document carries
`implements` or `related` relations, pull the linked documents one hop across
categories. Duplicate handling lives in the tracks' check-existing gates — do
not resolve duplicates here.

If `.archcore/` does not exist, announce initialization in one line and call
`mcp__archcore__init_project` without asking a question. If `.archcore/` exists
but contains no documents, proceed on outer-context grounding and report that
zero documents were found.

**Global sources.** If a `mcp__archcore__list_documents` /
`mcp__archcore__search_documents` result has `global: true` / `read_only: true` /
`source_kind: "global"`, load `skills/_shared/globals.md`. Never modify a global
document and never target one with `add_relation`. Absent any global match,
proceed as usual.

### Step 2: Expert form

If the invocation names a type, execute the named path without routing:

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

- **knowledge** — `adr`, `rfc`, `spec`, `doc`, `guide`, `rule`
- **vision** — `plan` (architecture cascade)
- **experience** — `cpat` (standard cascade opt-in)

List each document's path and relation edges. Close with one recommended next
action naming only `/archcore:plan`, `/archcore:review`, or a repeat
`/archcore:document` invocation.
