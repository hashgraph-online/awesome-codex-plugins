# PRD Template — Full (8 Sections)

> Template for `/plan new` mode. Used by SKILL.md Phase 3 to generate project PRDs.
> Fill each `{{placeholder}}` with data gathered during the Q&A waves.
> Delete this instruction block before saving the final PRD.

---

# {{project-name}} — Product Requirements Document

**Date:** {{YYYY-MM-DD}}
**Author:** {{user}} + Claude (AI-assisted planning)
**Status:** Draft
**Appetite:** {{1w|2w|6w}}

## 1. Executive Summary

{{2-3 paragraph synthesis of the project: what it is, who it's for, and why it matters. Written in active voice.}}

## 2. Problem & Context

### Problem Statement
{{Core problem being solved — from Wave 1 Q4}}

### Context
{{Market context, user feedback, technical necessity — from Wave 1 Q3 + research}}

### Current State
{{How users currently solve this problem. Pain points.}}

## 3. Target Audience & Personas

| Persona | Description | Primary Need | Usage Frequency |
|---------|-------------|--------------|-----------------|
| {{persona-1}} | {{description}} | {{need}} | {{daily/weekly/monthly}} |
| {{persona-2}} | {{description}} | {{need}} | {{daily/weekly/monthly}} |

{{1-2 paragraphs elaborating on primary persona}}

## 4. Solution & Scope

### In-Scope (MVP)
- [ ] {{feature-1 — must-have for launch}}
- [ ] {{feature-2}}
- [ ] {{feature-3}}

### Explicitly Out-of-Scope
- {{excluded-1 — and why it's excluded}}
- {{excluded-2}}

### Future Phases
- Phase 2: {{what comes after MVP}}
- Phase 3: {{long-term vision}}

## 5. Success Criteria

| Metric | Target | Measurement Method | Deadline |
|--------|--------|--------------------|----------|
| {{metric-1}} | {{specific target}} | {{how to measure}} | {{date}} |
| {{metric-2}} | {{specific target}} | {{how to measure}} | {{date}} |
| {{metric-3}} | {{specific target}} | {{how to measure}} | {{date}} |

## 5.A Acceptance Criteria (EARS)

> Optional companion to Section 5 — translates each Feature Area's acceptance criteria into EARS-shaped statements for deterministic vitest stub generation by `/write-executable-plan`. Leave blank if Section 5's success metrics suffice.

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

## 6. Technical Architecture

### Archetype
{{archetype from Wave 1 Q1}} (from projects-baseline)

### Tech Stack
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | {{tech}} | {{why}} |
| Backend | {{tech}} | {{why}} |
| Database | {{tech}} | {{why}} |
| Auth | {{tech}} | {{why}} |
| Hosting | {{tech}} | {{why}} |

### Integrations
- {{integration-1}}: {{purpose}}
- {{integration-2}}: {{purpose}}

### Schema Sketch
{{High-level data model — key entities and relationships}}

## 7. Risks & Dependencies

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| {{risk-1}} | High/Medium/Low | High/Medium/Low | {{mitigation}} |
| {{risk-2}} | High/Medium/Low | High/Medium/Low | {{mitigation}} |

### Dependencies
- {{dependency-1}}: {{status and impact if unavailable}}
- {{dependency-2}}: {{status and impact if unavailable}}

## 8. Post-Launch Plan

### Monitoring
- {{what to monitor and how}}

### Rollback Strategy
- {{how to rollback if issues arise}}

### Feedback Channels
- {{how users report issues / provide feedback}}

### First Week Checklist
- [ ] Deploy to production
- [ ] Verify monitoring dashboards
- [ ] Announce to target audience
- [ ] Collect initial feedback
