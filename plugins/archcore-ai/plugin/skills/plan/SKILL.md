---
name: plan
argument-hint: "[topic] [sdd | sources | iso | research]"
description: "Plan a feature or initiative over gated tracks: sdd (idea → PRD → spec → plan) by default, sources mode (MRD → BRD → URD) for market research and discovery, iso mode (BRS → StRS → SyRS → SRS) for ISO 29148 and regulated work, research track (RND) for technical research. Use for 'plan the X redesign', 'create a roadmap', 'plan a new feature', 'I need market research before we plan', 'we're regulated — start the ISO requirements cascade', 'investigate X before we plan', 'compare the alternatives for Y'. Not for recording a decision or documenting existing code — use /archcore:document. Not for checking docs against code — use /archcore:review."
---

# /archcore:plan

Plan a feature or initiative through one gated track. Vision types are the
primary output. Reads cover all three categories: vision supplies intent and
resumption targets, knowledge supplies constraints, experience supplies
precedent.

## When to use

- "Plan the auth redesign" → `sdd` track
- "Create a roadmap for the API migration" → `sdd` track
- "Plan a new feature for CSV export" → `sdd` track
- "Just a plan, skip the idea and PRD" → `sdd` track; gates an existing document covers close via `skip_when`, the rest run question-free
- "I need market research before we plan" → `requirements-cascade` track, sources mode
- "We're regulated — start the ISO requirements cascade" → `requirements-cascade` track, iso mode
- "Investigate X before we plan" / "Compare the alternatives for Y" → `research` track

**Not plan:**

- Recording a decision → `/archcore:document`
- Documenting existing code → `/archcore:document`
- Codifying a team standard → `/archcore:document`
- Checking documents against code → `/archcore:review`

## Routing table

| Signal | Route |
|---|---|
| Default — feature, initiative, refactor, roadmap | `sdd` track — `skills/_shared/tracks/sdd.md`, entry `sdd.frame` |
| Market research, discovery, competitive or opportunity analysis, stakeholder alignment — when it opens a requirements cascade (`mrd` → `brd` → `urd`); standalone market research as evidence routes to the `research` row below | `requirements-cascade` track, sources mode — `skills/_shared/tracks/requirements-cascade.md`, entry `requirements-cascade.mrd` |
| Regulated system, ISO 29148, audits, formal or traceable requirements | `requirements-cascade` track, iso mode — `skills/_shared/tracks/requirements-cascade.md`, entry `requirements-cascade.brs` |
| Technical research: investigate an unknown, compare alternatives, gather evidence before planning or deciding — "investigate X", "research the options for Y". Market and business discovery stays on the sources row above; a request that already proposes a specific target for team acceptance ("should we switch to Y", "let's adopt Y") belongs to `/archcore:document`'s decision track — research is pre-decision evidence gathering with no proposed verdict | `research` track — `skills/_shared/tracks/research.md`, entry `research.frame` |
| The user names a track or mode (`sdd`, `sources`, `iso`, `research`) in the invocation | The named path, with no routing |
| "Just a plan" or "only the plan document" | `sdd` track — gates whose topic an existing document already covers close through `skip_when`; otherwise upstream gates run question-free when the request text satisfies their entry conditions |
| A decision surfaces at a gate | Record the `adr` through the decision track (`skills/_shared/tracks/decision.md`), then return to the open gate |

Finer mode selection inside `requirements-cascade` — document-graph state, a
named cascade document type — belongs to that track's Mode selection section.

## Execution

### 1. Ground

Complete this step before asking the user any question.

1. Search `.archcore/` with `mcp__archcore__search_documents` and `mcp__archcore__list_documents` across all three categories. Pass a planning-moment type filter — for example `types=["idea", "prd", "plan", "spec", "rnd", "rfc", "adr", "rule", "task-type", "cpat"]` — instead of relying on the global type ranking. Do not exclude a category from reads.
2. WHEN a found document carries `implements` or `related` relations, pull the linked documents one hop via `mcp__archcore__list_relations` and `mcp__archcore__get_document`.
3. WHEN a found draft on the topic carries an `archcore:track` state block, resume it per the resume rules in `skills/_shared/gate-contract.md` instead of opening a new track.
4. Read git state — current branch, recent commits, working tree — and the code areas the topic names. Record the concrete files and modules for Step 5.
5. IF `.archcore/` exists but contains no documents, THEN proceed on outer-context grounding (git state and the codebase) and report that zero documents were found.
6. IF `.archcore/` does not exist, THEN announce initialization in one line and call `mcp__archcore__init_project` without asking a question.

**Global sources.** If a `list_documents` / `search_documents` result has
`global: true` / `read_only: true` / `source_kind: "global"`, load
`skills/_shared/globals.md`. Never modify a global document and never target
one with `add_relation`. Absent any global match, proceed as usual.

### 2. Route

Apply the routing table to the request text and the grounding results. WHEN
the user names a track or mode in the invocation, execute that path with no
routing — this is the expert invocation.

### 3. Budget

Interview mechanics, question form, and ceilings:
`skills/_shared/elicitation-contract.md`. Auto mode draws every question from
the shared per-invocation ceiling; an expert invocation raises per-gate
budgets to the maxima the track file declares.

### 4. Execute the track

Run the routed track's gates per `skills/_shared/gate-contract.md`: evaluate
`skip_when` first at every gate, keep track state only in the
`archcore:track` block inside the draft artifact, persist each gate close in
one `mcp__archcore__update_document` call, and follow the resume rules on
re-entry. Gate bodies, per-gate questions, and relation wiring live in the
track files — do not restate them.

### 5. Map tasks to files

WHEN the track has exited and a `plan` document exists:

1. Annotate each task in the plan's Tasks section with the concrete files or modules that grounding surfaced for it, using `@path/to/file` notation, in one `mcp__archcore__update_document` call.
2. WHEN grounding surfaced no file or module for a task, state that no target was found for that task. Do not guess a path.

WHEN the track produced no `plan` document (sources and iso modes, and the
`research` track), skip to Result — the track's exit gate names its
follow-ups.

### 6. Implement fork

Offer exactly two exits and let the user choose:

- **Implement now** — start on the mapped task list, first phase first, against the files mapped in Step 5.
- **Stop here** — the draft documents and relations stay in `.archcore/`; a later `/archcore:plan` invocation resumes any draft that still carries a state block.

## Result

Report:

- Produced documents grouped by category — vision, knowledge, experience — with each document's path and status.
- Relations created, plus candidate `mcp__archcore__add_relation` targets among existing documents, or a statement that none match.
- Next actions, naming only v2 commands: `/archcore:plan` to continue a cascade (for example a `prd` through the `sdd` track after sources mode), `/archcore:document` to record a decision or document code touched during implementation, `/archcore:review` to check the implementation against the recorded plan.
