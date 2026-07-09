# PRD Template — Feature (5 Sections)

> Template for `/plan feature` mode. Used by SKILL.md Phase 3 to generate feature PRDs.
> Fill each `{{placeholder}}` with data gathered during the Q&A waves.
> Delete this instruction block before saving the final PRD.

---

# Feature: {{feature-name}}

**Date:** {{YYYY-MM-DD}}
**Author:** {{user}} + Claude (AI-assisted planning)
**Status:** Draft
**Appetite:** {{1w|2w|6w}}
**Parent Project:** {{project-name or "standalone"}}

## 1. Problem & Motivation

### What
{{What we're building — clear, concise description}}

### Why
{{Business driver, user feedback, or technical necessity — from Wave 1 Q2}}

### Who
{{Target users — existing personas or new audience — from Wave 1 Q3}}

## 2. Solution & Scope

### In-Scope
- [ ] {{scope-item-1}}
- [ ] {{scope-item-2}}
- [ ] {{scope-item-3}}

### Out-of-Scope
- {{excluded-1 — why}}
- {{excluded-2 — why}}

## User Stories

> Optional intent layer — emitted only when the Wave-1 story toggle is "yes". Leave blank or delete this section if §3/§3.A acceptance criteria already capture the intent. Stories are the "who/why"; acceptance criteria are the "verify".

### US-1 (→ {{Feature Area}})
**Als** {{Persona}} **möchte ich** {{Capability}}, **damit** {{Nutzen}}.
- ↳ AC: {{§3 / §3.A reference to ≥1 acceptance criterion}}

### US-2 (→ {{Feature Area}})
**Als** {{Persona}} **möchte ich** {{Capability}}, **damit** {{Nutzen}}.
- ↳ AC: {{§3 / §3.A reference to ≥1 acceptance criterion}}

## 3. Acceptance Criteria

### {{Feature Area 1}}
```gherkin
Given {{precondition}}
When {{action}}
Then {{expected result}}
```

### {{Feature Area 2}}
```gherkin
Given {{precondition}}
When {{action}}
Then {{expected result}}
```

### {{Edge Case / Error Handling}}
```gherkin
Given {{error condition}}
When {{action}}
Then {{graceful handling}}
```

## 3.A Acceptance Criteria (EARS)

> Optional companion to Section 3 — translates each Feature Area's acceptance criteria into EARS-shaped statements for deterministic vitest stub generation by `/write-executable-plan`. Leave blank if Section 3's narrative Gherkin suffices.

### Feature Area 1 — {{name}}

**Ubiquitous** (always-true invariants — no trigger, no state):
- The {{system}} shall {{response}}.

**State-driven** (`While …`):
- While {{precondition}}, the {{system}} shall {{response}}.

**Event-driven** (`When …`):
- When {{trigger}}, the {{system}} shall {{response}}.

**Optional feature** (`Where …`):
- Where {{feature enabled}}, the {{system}} shall {{response}}.

**Unwanted behaviour** (`If … then …`):
- If {{unwanted condition}}, then the {{system}} shall {{response}}.

### Feature Area 2 — {{name}}

[repeat pattern]

### Edge Case / Error Handling

[repeat pattern, typically focused on Unwanted + Optional]

## 4. Technical Notes

### Affected Files
- `{{file-path-1}}` — {{what changes}}
- `{{file-path-2}}` — {{what changes}}

### Architecture
{{High-level approach — patterns to follow, components to modify}}

### Data Model Changes
{{New tables, columns, migrations — or "None"}}

### API Changes
{{New endpoints, modified contracts — or "None"}}

## 5. Risks & Dependencies

| Risk | Impact | Mitigation |
|------|--------|------------|
| {{risk-1}} | {{impact}} | {{mitigation}} |

### Dependencies
- {{dependency-1}}: {{status}}
- {{open-issue-ref}}: {{relationship}}
