---
name: plan
argument-hint: "[topic] [sdd | sources | iso | research]"
description: "Plan a feature or initiative through a computed route: the conductor derives the canon delta and assembles the document package — from a zero-document null route for small fixes to an umbrella PRD with one spec per capability for large initiatives. Expert paths: sdd (full package), sources mode (MRD → BRD → URD) for market research and discovery, iso mode (BRS → StRS → SyRS → SRS) for ISO 29148 and regulated work, research track (RND) for technical research. Use for 'plan the X redesign', 'create a roadmap', 'plan a new feature', 'I need market research before we plan', 'we're regulated — start the ISO requirements cascade', 'investigate X before we plan', 'compare the alternatives for Y'. Not for recording a decision or documenting existing code — use /archcore:document. Not for checking docs against code — use /archcore:review."
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
- "I need market research before we plan" → acquisition instrument (`sources` expert path)
- "We're regulated — start the ISO requirements cascade" → iso links (`iso` expert path)
- "Investigate X before we plan" / "Compare the alternatives for Y" → research instrument

**Not plan:**

- Recording a decision → `/archcore:document`
- Documenting existing code → `/archcore:document`
- Codifying a team standard → `/archcore:document`
- Checking documents against code → `/archcore:review`

## Route computation

Apply in this order:

| Signal | Route |
|---|---|
| The user names an expert path — an alias (`sdd`, `sources`, `iso`, `research`), a route name, or a registry document type | The named path per the expert invocation map in `skills/_shared/delta-routing.md`, with no computation |
| Any other request | Compute Δ, Π, M, and R per the Derivation section of `skills/_shared/delta-routing.md`; its route table decides the package |
| A decision surfaces at a gate | Record the `adr` through the decision instrument (`skills/_shared/tracks/decision.md`), then return to the open gate |

Technical-research boundary: market and business discovery belongs to the
acquisition instrument; a request that already proposes a specific target for
team acceptance ("should we switch to Y", "let's adopt Y") belongs to
`/archcore:document`'s decision instrument — research is pre-decision evidence
gathering with no proposed verdict.

## Execution

### 1. Ground

Complete this step before asking the user any question.

1. Search `.archcore/` with `mcp__archcore__search_documents` and `mcp__archcore__list_documents` across all three categories. Pass a planning-moment type filter — for example `types=["idea", "prd", "plan", "spec", "rnd", "rfc", "adr", "rule", "task-type", "cpat"]` — instead of relying on the global type ranking. Do not exclude a category from reads.
2. WHEN a found document carries `implements` or `related` relations, pull the linked documents one hop via `mcp__archcore__list_relations` and `mcp__archcore__get_document`.
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
user names an expert path, execute it with no computation — this is the expert
invocation. Never ask the user to choose a route or a size label.

### 3. Budget

Interview mechanics, question form, and ceilings:
`skills/_shared/elicitation-contract.md`. Auto mode draws every question from
the shared per-invocation ceiling; an expert invocation raises per-gate
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
- Next actions, naming only v2 commands: `/archcore:plan` to continue a package, `/archcore:document` to record a decision or document code touched during implementation, `/archcore:review` to check the implementation against the recorded plan and reconcile the declared Δ.
