---
name: plan
argument-hint: "[topic]"
description: "Plan future work, investigate before building, research a topic, or compare the alternatives for a choice. Takes optional free text. The skill reads the request, open drafts, accepted canon, branch, and code, then creates only the documents a later reader needs — none for a small fix. Use for 'plan the X redesign', 'create a roadmap', 'plan a new feature', 'plan the onboarding journey', 'investigate X before we plan', 'compare the alternatives for Y', 'REST or a queue? two teams disagree', 'I need market research before we plan', 'we are regulated — trace the requirements'. With no arguments it resumes an open planning draft or offers what to plan next. Not for recording a decision or documenting existing code — use /archcore:document. Not for checking docs against code — use /archcore:review."
---

# /archcore:plan

Plan future work from the project context. Context resolution
(`skills/_shared/gate-contract.md`, section Context resolution) records the
claims, unknowns, hazards, and authority; the conductor
(`skills/_shared/delta-routing.md`) selects the documents a later reader needs;
instruments produce them. Vision types are the primary output. Reads cover all three categories: vision supplies intent and
resumption targets, knowledge supplies constraints, experience supplies
precedent.

## When to use

- "Plan a new feature for CSV export" → typically one `spec` and one `plan`
- "Upgrade the HTTP client across three services with a coordinated rollout" → a `plan` alone
- "Plan the notifications platform" → a `prd`, one `spec` per capability, one `plan`
- "Fix the typo in the onboarding copy" → no document; implement directly
- "I need market research before we plan" → acquisition instrument
- "We must trace these requirements for the auditor" → only the requirement levels that obligation names
- "Investigate X before we plan" → `research`; "Compare the alternatives for Y" → `rnd`
- "REST or a queue for SAP? Two teams disagree", with the facts of both options recorded → `rfc`
- `research <topic>` as the first word → the type `research`

**Not plan:**

- Recording a decision → `/archcore:document`
- Documenting existing code → `/archcore:document`
- Codifying a team standard → `/archcore:document`
- Checking documents against code → `/archcore:review`

## Entry

Apply in this order:

| Signal | Action |
|---|---|
| No arguments, one draft with a state block this command resumes | Resume it at its earliest incomplete gate |
| No arguments, several such drafts | Resume rule 10 in `skills/_shared/gate-contract.md` |
| No arguments, a clear request in the session or one unfinished plan | Offer a start menu of at most four items, each with the evidence that names it, the recommended item first |
| No arguments and no reliable signal | Ask one question — what outcome to plan; a dirty branch alone is not a target |
| The first word is a type slug | The explicit type request per `explicit-type-request-wins.adr`; a leading `research` requests the type `research` |
| Any other request | Context resolution, then Selection per `skills/_shared/delta-routing.md` |
| A decision surfaces at a gate | Record the `adr` through the decision instrument (`skills/_shared/tracks/decision.md`), then return to the open gate |

Research boundary: discovery feeding an `mrd` → `brd` → `urd` requirements
chain belongs to acquisition. A request naming a pending decision or a set of
candidates to choose between produces `rnd` only when the evidence to choose
is missing; any other investigation produces `research`. WHEN the deciding facts
are already recorded and the open part is whose weights win — two owners
disagree, or the owner has not chosen — the decision instrument records an
`rfc`, and no `rnd` is created. A standalone external material is filed through
`/archcore:document`. A request proposing a specific target for team review
("let's adopt Y", "draft an RFC for Y") belongs to `/archcore:document`'s
decision instrument; a lone "should we switch to Y" with the evidence to choose
missing stays here as `rnd`.

## Execution

### 1. Ground

Complete this step before asking the user any question. The research
vocabulary probe (`skills/_shared/research-compatibility.md`) runs only under
its own condition 1 — a request or type naming `research` or `evidence`, a
selection engaging the research instrument, or a grounding result of either type.
Add `research` and `evidence` to the planning-moment filter below only when
the probe returns `yes`; a topic search without a type filter finds documents
of both types on every engine. If this skill has no shell tool, use the probe
result the host supplied; if none was supplied, report `needs-vocabulary-probe`
with the helper path and stop before the first MCP call that names either type.

The actor-subject probe (`skills/_shared/actor-subject-compatibility.md`) runs
under its own condition 1 — a request naming `scenario` or `journey`, a selection
engaging the illustrate instrument, or a grounding result of either type — and
adds both types to the filter below only when it returns `yes`. The same
no-shell rule applies: report `needs-vocabulary-probe` and stop before the first
MCP call that names either type.

1. Search `.archcore/` with `mcp__archcore__search_documents` and `mcp__archcore__list_documents` across all three categories. Pass a planning-moment type filter — for example `types=["idea", "prd", "plan", "spec", "rnd", "rfc", "adr", "rule", "task-type", "cpat"]` — and add `"scenario"`, `"journey"` when the actor-subject probe returned `yes` — instead of relying on the global type ranking. Do not exclude a category from reads.
2. WHEN a found document carries `implements`, `depends_on`, or `related` relations, pull the linked documents one hop via `mcp__archcore__list_relations` and `mcp__archcore__get_document`.
3. WHEN a found draft on the topic carries an `archcore:track` state block, resume it per the resume rules in `skills/_shared/gate-contract.md` and `skills/_shared/delta-routing.md` instead of opening a new track.
4. Read git state — current branch, recent commits, working tree — and the code areas the topic names. Record the concrete files and modules for Step 5, and note owner documents whose referenced paths changed after them — the staleness input to Selection.
5. IF `.archcore/` exists but contains no documents, THEN proceed on outer-context grounding (git state and the codebase) and report that zero documents were found.
6. IF `.archcore/` does not exist, THEN announce initialization in one line and call `mcp__archcore__init_project` without asking a question.

**Global sources.** If a `list_documents` / `search_documents` result has
`global: true` / `read_only: true` / `source_kind: "global"`, load
`skills/_shared/globals.md`. Also load it when a `search_documents` response's
`coverage` names a source other than `"local"` — even when `results` is empty:
the empty page is exactly where that file's retry ladder applies. Never modify
a global document and never target one with `add_relation`. Absent any global
match, proceed as usual.

### 2. Select

Build the context record per `skills/_shared/gate-contract.md`, section Context
resolution, then run Selection per `skills/_shared/delta-routing.md` and report
its selection line. Never ask the user to choose an instrument.

### 3. Budget

Interview mechanics, question form, and the ceiling of 5 questions per
invocation: `skills/_shared/elicitation-contract.md`.

### 4. Execute the selection

Invoke each selected instrument, in conductor order, per the instrument
registry and sequencing rules in `skills/_shared/delta-routing.md`. Run each
instrument's gates per `skills/_shared/gate-contract.md`: evaluate `skip_when`
first at every gate, keep track state only in the `archcore:track` block
inside the draft artifact (with the `claims:` field this command adds), persist each gate close in one `mcp__archcore__update_document` call,
and follow the resume rules on re-entry. Gate bodies, per-gate questions, and
relation wiring live in the track files — do not restate them.

Before delegating research or evidence work, pass the current vocabulary probe
result and absolute plugin root to the assistant. If the assistant returns
`needs-vocabulary-probe`, run the helper and resume the same task.
Before delegating any other document write or relation work, pass the absolute
plugin root to the assistant. The assistant reads
`skills/_shared/relation-authoring.md` under that root.

### 5. Map tasks to files

WHEN the selection produced a `plan` document:

1. Annotate each task in the plan's Tasks section with the concrete files or modules that grounding surfaced for it, using `@path/to/file` notation, in one `mcp__archcore__update_document` call.
2. WHEN grounding surfaced no file or module for a task, state that no target was found for that task. Do not guess a path.
3. Confirm the plan carries its `## Declared Delta` section per sequencing rule 9 of `skills/_shared/delta-routing.md`.

WHEN the selection produced no `plan` document, skip to Result — the exit gate
or the selection line names the follow-ups.

### 6. Implement fork

WHEN a blocking exit check stopped the selection, skip this step and go to Result.
Otherwise, offer exactly two exits and let the user choose:

- **Implement now** — start on the mapped task list, first phase first, against the files mapped in Step 5.
- **Stop here** — the draft documents and relations stay in `.archcore/`; a later `/archcore:plan` invocation resumes any draft that still carries a state block.

## Result

Report:

- The selection line, and the inferred scope when no argument set it.
- Produced documents grouped by category — vision, knowledge, experience — with each document's path and status.
- Relations created, plus candidate `mcp__archcore__add_relation` targets among existing documents, or a statement that none match.
- `retire` claims reported for closeout discharge, when any exist.
- Next actions, naming only v2 commands: `/archcore:plan` to continue the selection, `/archcore:document <subject>` to record a decision or document code touched during implementation, `/archcore:review` to check the implementation against the recorded plan and reconcile its Declared Delta.
- WHEN contract drafting remains open on a material user-owned choice, name the draft `spec`, the unanswered choice, and the behavior it changes. Do not offer implementation until that check passes. Name the three ways to continue — answer the choice, delegate it ("you decide"), or proceed anyway — and the resume command `/archcore:plan <spec title>`.
- Name instruments and stages in plain words; do not print a gate address of the form `<track>.<stage>`.
