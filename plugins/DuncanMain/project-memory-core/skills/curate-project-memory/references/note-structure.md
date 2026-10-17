# Note structure

Use ordinary Markdown, YAML frontmatter, and Obsidian links. Do not require community plugins.

## Minimal project layout

```text
Project.md
Project Home.md
Current State.md
Decisions/
Inbox/Promotion Inbox.md
Handoff.md
Coverage.md
Dashboards/
```

Add `Plans`, `Investigations`, `Reference`, or workstream folders only when useful. Preserve existing folders and link them from `Project.md`.

## Note types

### Project landing page

Copy `assets/project-home.md` for the polished human-facing front door. Copy `assets/project-note.md` as the compact compatibility index used by existing workflows. Replace tokens with verified information and remove unknown rows rather than leaving raw placeholders.

### Current state

Copy `assets/current-state.md`. Keep it concise and current; move lasting rationale into decisions.

### Decision

Copy `assets/decision.md`. Use existing ADR numbering when present; otherwise use a descriptive filename.

### Constraints, discoveries, procedures, and debugging lessons

Use `assets/constraint.md`, `assets/discovery.md`, `assets/procedure.md`, or `assets/debugging-lesson.md`. Create one focused note only when the information is durable and useful; do not create empty category folders during setup.

### Promotion inbox

Copy `assets/promotion-inbox.md`. Candidates in this file are proposals, not durable facts. Keep a stable candidate ID. Review states are `pending`, `approved`, `rejected`, and `deferred`; application states are `applying`, `applied`, `conflict`, and `failed`. Follow `references/obsidian-companion.md` for guarded transitions and outcome metadata.

### Handoff brief

Copy `assets/handoff.md`. Regenerate it from canonical notes; do not place unique decisions only in the handoff.

### Coverage map

Copy `assets/coverage.md`. Generate it from declared project `coverage_areas` and tagged notes. Treat it as a derived navigation view, not canonical knowledge.

### Dashboards

Copy the `.base` files from `assets/bases/` into `Dashboards/`. They are optional Obsidian views over ordinary Markdown properties. The Markdown notes remain portable when Bases is unavailable.

## Common properties

Use only properties that add retrieval or review value:

```yaml
type: decision
project_id: example-project
knowledge_id: adr-example-001
status: accepted
confidence: confirmed
owner: optional-name
reviewers: []
review_status: approved
last_reviewed_by:
last_reviewed_at:
updated: 2026-08-05
review_after: 2026-11-05
workstreams:
  - authentication
tags:
  - project-memory
supersedes: []
superseded_by:
implementation_status: merged
applies_to_branch:
applies_to_revision:
code_paths: []
```

Use ISO dates. Allowed knowledge status values are `proposed`, `accepted`, `rejected`, `deprecated`, and `superseded`. Allowed confidence values are `confirmed`, `inferred`, and `tentative`. Allowed implementation states are `observed`, `proposed`, `implemented`, `merged`, `released`, `reverted`, and `unverified`.

### Session summary

Copy `assets/session-summary.md` only when session summaries are enabled or explicitly requested. Store it outside the vault.

### Automatic orientation

Copy the managed block from `assets/agents-project-memory.md` into the primary code repository's `AGENTS.md` only after the user opts in. Preserve unrelated instructions and store no absolute paths.

## Code references

Use logical repository IDs and relative paths:

```yaml
code_references:
  - repository: service-api
    path: src/auth/service.ts
    revision: optional-git-commit
```

Never persist an absolute source-code path in durable notes.
