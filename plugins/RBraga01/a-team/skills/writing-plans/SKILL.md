---
name: writing-plans
description: Create a detailed, phased implementation plan from an approved spec. Use after brainstorming produces an approved spec. Produces a plan file that executing-plans or subagent-driven-development can consume.
---

# Writing Plans

Create implementation plans from approved specs. The output is consumed by
`executing-plans` or `subagent-driven-development`.

## Process

### Step 1: Read the Spec
- Read the approved spec in `docs/specs/`
- Identify: requirements, architecture changes, success criteria
- Note any open questions before planning

### Step 2: Break Down Into Phases

Each phase must be:
- **Independently deliverable** — it can be merged on its own
- **Incrementally testable** — tests can verify it at the end of the phase
- **Scope-bounded** — clear start and end

Phase structure:
- Phase 1: Minimum viable (smallest slice with value)
- Phase 2: Core experience (complete happy path)
- Phase 3: Edge cases (error handling, polish)
- Phase 4: Optimization (performance, monitoring) — if needed

### Step 3: Write Each Step

Each step must include:
- **File:** exact path
- **Action:** specific change to make
- **Why:** rationale
- **Dependencies:** which steps must precede this
- **Risk:** Low / Medium / High

### Step 4: Add Testing Strategy

For each phase, specify:
- Unit tests: which functions/components
- Integration tests: which flows
- E2E tests: which user journeys

### Step 5: Write Plan File

Save to `docs/plans/YYYY-MM-DD-<feature>.md`

```markdown
# Implementation Plan: [Feature Name]

## Overview
[2-3 sentences]

## Requirements
- [Requirement 1]

## Architecture Changes
- [file path]: [description]

## Implementation Steps

### Phase 1: [Name] — Minimum Viable
1. **[Step]** (File: path/to/file.ts)
   - Action: ...
   - Why: ...
   - Dependencies: None
   - Risk: Low

## Testing Strategy
- Unit: [files]
- Integration: [flows]
- E2E: [journeys]

## Success Criteria
- [ ] Criterion 1
```

### Step 6: Confirm Plan with Human

Present the plan and confirm before execution begins.

## Quality Checks

- [ ] Every step has an exact file path
- [ ] Every step has a specific action
- [ ] Phases are independently mergeable
- [ ] Testing strategy covers all new code paths
- [ ] No step is larger than 50 lines of code
