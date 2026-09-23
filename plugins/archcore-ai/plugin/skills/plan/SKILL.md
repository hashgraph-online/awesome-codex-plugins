---
name: plan
argument-hint: "[sdd|sources|iso|research] [topic]"
description: "Plan a feature or initiative through a computed route: the conductor derives the canon delta and assembles the document package — from a zero-document null route for small fixes to an umbrella PRD with one spec per capability for large initiatives. Modes, named as the first word: sdd (full package), sources (MRD → BRD → URD) for market research, customer discovery, and business or user requirements, iso (BRS → StRS → SyRS → SRS) for ISO 29148 and regulated work, research for a technical investigation — never market research — that the research instrument closes either by scope coverage (a research document) or by a recommendation (an rnd). Explicit form: plan research <topic>. Use for 'plan the X redesign', 'create a roadmap', 'plan a new feature', 'I need market research before we plan', 'we're regulated — start the ISO requirements cascade', 'investigate X before we plan', 'compare the alternatives for Y' — a new investigation, not a finished report already in hand. Not for recording a decision or documenting existing code — use /archcore:document. Not for checking docs against code — use /archcore:review."
---

# /archcore:plan

Plan a feature or initiative through a computed route. The conductor
(`skills/_shared/delta-routing.md`) derives the canon delta Δ, the gap profile
Π, the zone maturity M, and the risk flags R, then assembles the document
package; instruments produce the documents. Vision types are the primary
output. Reads cover all three categories: vision supplies intent and
resumption targets, knowledge supplies constraints, experience supplies
precedent.

## When to use

- "Plan the auth redesign" → computed route — typically `capability`: one spec plus one plan
- "Create a roadmap for the API migration" → computed route
- "Plan a new feature for CSV export" → computed route
- "Plan the notifications platform" → computed route — typically `umbrella`: prd, one spec per capability, one plan
- "I need market research before we plan" → acquisition instrument (`sources` mode)
- "We're regulated — start the ISO requirements cascade" → iso links (`iso` mode)
- "Investigate X before we plan" → research instrument, `research`; "Compare the alternatives for Y" → research instrument, `rnd` — a named pending decision or candidate set selects `rnd`, otherwise `research`
- `plan research <topic>` → research instrument; the instrument selects `research` (closed by scope coverage) or `rnd` (closed by a recommendation) by its closing test

**Not plan:**

- Recording a decision → `/archcore:document`
- Documenting existing code → `/archcore:document`
- Codifying a team standard → `/archcore:document`
- Checking documents against code → `/archcore:review`

## Route computation

Apply in this order:

| Signal | Route |
|---|---|
| No arguments | Ground per step 1; WHEN a draft on the branch carries a state block, resume it; otherwise ask one question — what to plan — with a recommendation drawn from the branch changes |
| The first word is a mode (`sdd`, `sources`, `iso`, `research`) | The mapped instrument per the mode map in `skills/_shared/delta-routing.md`, without route computation |
| Any other request | Compute Δ, Π, M, and R per the Derivation section of `skills/_shared/delta-routing.md`; its route table decides the package |
| A decision surfaces at a gate | Record the `adr` through the decision instrument (`skills/_shared/tracks/decision.md`), then return to the open gate |

Research boundary: discovery feeding an `mrd` → `brd` → `urd` requirements
chain belongs to acquisition. A request naming a pending decision or a set of
candidates to choose between produces `rnd`; any other investigation produces
`research`. The path name `research` selects the instrument, not the type; the
same test applies. Neither `rnd` nor `evidence` is an entry on this command: an
`rnd` comes only from that test, the spike, or the compatibility fallback, and a
standalone material is filed through `/archcore:document research`. A request proposing a specific
target for team acceptance ("should we switch to Y", "let's adopt Y") belongs
to `/archcore:document`'s decision instrument.

## Execution

### 1. Ground

Complete this step before asking the user any question. The research
vocabulary probe (`skills/_shared/research-compatibility.md`) runs only under
its own condition 1 — a request or type naming `research` or `evidence`, a
route engaging the research instrument, or a grounding result of either type.
Add `research` and `evidence` to the planning-moment filter below only when
the probe returns `yes`; a topic search without a type filter finds documents
of both types on every engine. If this skill has no shell tool, use the probe
result the host supplied; if none was supplied, report `needs-vocabulary-probe`
with the helper path and stop before the first MCP call that names either type.

The actor-subject probe (`skills/_shared/actor-subject-compatibility.md`) runs
under its own condition 1 — a request naming `scenario` or `journey`, a route
engaging the illustrate instrument, or a grounding result of either type — and
adds both types to the filter below only when it returns `yes`. The same
no-shell rule applies: report `needs-vocabulary-probe` and stop before the first
MCP call that names either type.

1. Search `.archcore/` with `mcp__archcore__search_documents` and `mcp__archcore__list_documents` across all three categories. Pass a planning-moment type filter — for example `types=["idea", "prd", "plan", "spec", "rnd", "rfc", "adr", "rule", "task-type", "cpat"]` — and add `"scenario"`, `"journey"` when the actor-subject probe returned `yes` — instead of relying on the global type ranking. Do not exclude a category from reads.
2. WHEN a found document carries `implements`, `depends_on`, or `related` relations, pull the linked documents one hop via `mcp__archcore__list_relations` and `mcp__archcore__get_document`.
3. WHEN a found draft on the topic carries an `archcore:track` state block, resume it per the resume rules in `skills/_shared/gate-contract.md` and `skills/_shared/delta-routing.md` instead of opening a new track.
4. Read git state — current branch, recent commits, working tree — and the code areas the topic names. Record the concrete files and modules for Step 5, and note zone documents whose referenced paths changed after them — the staleness input to Derivation.
5. IF `.archcore/` exists but contains no documents, THEN proceed on outer-context grounding (git state and the codebase) and report that zero documents were found.
6. IF `.archcore/` does not exist, THEN announce initialization in one line and call `mcp__archcore__init_project` without asking a question.

**Global sources.** If a `list_documents` / `search_documents` result has
`global: true` / `read_only: true` / `source_kind: "global"`, load
`skills/_shared/globals.md`. Also load it when a `search_documents` response's
`coverage` names a source other than `"local"` — even when `results` is empty:
the empty page is exactly where that file's retry ladder applies. Never modify
a global document and never target one with `add_relation`. Absent any global
match, proceed as usual.

### 2. Route

Compute the route per the Derivation section of
`skills/_shared/delta-routing.md` and report the route announcement. WHEN the
first word is a mode, execute its mapped instrument without route computation.
A route name or a document type name as the first word is topic text; the
conductor computes the route. Never ask the user to choose a route or a size label.

### 3. Budget

Interview mechanics, question form, and ceilings:
`skills/_shared/elicitation-contract.md`. Auto mode draws every question from
the shared per-invocation ceiling; a mode entry raises per-gate
budgets to the maxima the track file declares.

### 4. Execute the package

Invoke each instrument the route names, in conductor order, per the instrument
registry and sequencing rules in `skills/_shared/delta-routing.md`. Run each
instrument's gates per `skills/_shared/gate-contract.md`: evaluate `skip_when`
first at every gate, keep track state only in the `archcore:track` block
inside the draft artifact (with the `route:` and `delta:` fields this command
adds), persist each gate close in one `mcp__archcore__update_document` call,
and follow the resume rules on re-entry. Gate bodies, per-gate questions, and
relation wiring live in the track files — do not restate them.

Before delegating research or evidence work, pass the current vocabulary probe
result and absolute plugin root to the assistant. If the assistant returns
`needs-vocabulary-probe`, run the helper and resume the same task.
Before delegating any other document write or relation work, pass the absolute
plugin root to the assistant. The assistant reads
`skills/_shared/relation-authoring.md` under that root.

### 5. Map tasks to files

WHEN the package produced a `plan` document:

1. Annotate each task in the plan's Tasks section with the concrete files or modules that grounding surfaced for it, using `@path/to/file` notation, in one `mcp__archcore__update_document` call.
2. WHEN grounding surfaced no file or module for a task, state that no target was found for that task. Do not guess a path.
3. Confirm the plan carries its `## Declared Delta` section per sequencing rule 9 of `skills/_shared/delta-routing.md`.

WHEN the package produced no `plan` document (the `null`, `decision`, and
`amendment` routes, the acquisition and research paths), skip to Result — the
exit gate or the announcement names the follow-ups.

### 6. Implement fork

Offer exactly two exits and let the user choose:

- **Implement now** — start on the mapped task list, first phase first, against the files mapped in Step 5.
- **Stop here** — the draft documents and relations stay in `.archcore/`; a later `/archcore:plan` invocation resumes any draft that still carries a state block.

## Result

Report:

- The route announcement — route, size label, and the Δ, Π, M, R values that produced them.
- Produced documents grouped by category — vision, knowledge, experience — with each document's path and status.
- Relations created, plus candidate `mcp__archcore__add_relation` targets among existing documents, or a statement that none match.
- `retires` entries reported for closeout discharge, when any exist.
- Next actions, naming only v2 commands: `/archcore:plan` to continue a package, `/archcore:document decision` to record a decision or `/archcore:document code` to document code touched during implementation, `/archcore:review closeout` to check the implementation against the recorded plan and reconcile the declared Δ.
- Name instruments and stages in plain words; do not print a gate address of the form `<track>.<stage>`.
