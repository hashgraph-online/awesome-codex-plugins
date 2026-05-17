# Implementation Plan: [Title]

## WORKFLOW STATE
Status: In Progress
Current Phase: 1 (Research + Plan — approach approved in brainstorming, pending plan approval)
Phases remaining: 2, 3, 4
Research: docs/plans/NNNN__research__{slug}.md
Chronicle: TBD — decided in Phase 2
Verification: TBD

**Sections:** WORKFLOW STATE | Brainstorming Summary | Clarifications | Plan | Task Checklist | Implementation Log | Verification Results | Review Log

## Brainstorming Summary

**Task:** [One-sentence restatement]

**Understanding:**
- **WHAT:** [Key deliverables]
- **WHY:** [Business motivation]

**Approaches considered:**
1. **[Approach Name]** — [1-2 sentence description] | Complexity: [LOW/MEDIUM/HIGH] | Risk: [brief]
2. **[Approach Name]** — [1-2 sentence description] | Complexity: [LOW/MEDIUM/HIGH] | Risk: [brief]

**Recommended: [Name]**
[2-4 sentence description incorporating evaluation feedback]

**Evaluation verdict:** [PROCEED / PROCEED WITH CHANGES / RECONSIDER / STOP]
[1-sentence rationale]

**Complexity:** [LOW/MEDIUM/HIGH] | **Risk:** [brief]

**Key risks identified:**
- [Risk 1]
- [Risk 2]

## Plan

- **Assumptions** — [about codebase, requirements, environment]
- **Risks** — [what could go wrong, edge cases, side effects]
- **Unknowns** — [anything unclear — state explicitly, don't guess]
- **Verification strategy** — [how to prove it works]
- **Files to modify** — [specific files and planned changes]
- **File responsibilities** — [what each touched/new file owns]
- **Task decomposition** — [smallest buildable slices; each has a test/check]

### HOW-level locks (Phase 1 will fill these in)

| Dimension | Answer |
|---|---|
| Edge cases | [decision or N/A: reason] |
| Data shapes | [decision or N/A: reason] |
| Error semantics | [decision or N/A: reason] |
| Contract boundaries | [decision or N/A: reason] |
| Test scope | [decision or N/A: reason] |
| Rollback | [decision or N/A: reason] |

### Plan buildability checks

- [ ] No placeholders: no `TBD`, `TODO`, `later`, `similar to above`, or vague "add appropriate..." steps.
- [ ] Every task has exact file paths or an explicit discovery step that produces them.
- [ ] New/changed functions, types, fields, routes, and commands are named consistently across tasks.
- [ ] Tasks are vertical slices: one behavior/check -> minimal implementation -> verification -> next behavior.
- [ ] Every task has a verification command or manual evidence target.

## Implementation Steps

[Numbered, buildable steps for the recommended approach. Each step should include: target file(s), behavior changed, expected failing test/check when applicable, minimal implementation action, and verification command. Do not write placeholders.]
