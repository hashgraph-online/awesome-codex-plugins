# Technical Writing

Use this reference for coding plans, implementation plans, technical proposals,
technical documentation, design docs, and product specs.

## Coding Plan

Frame:
- Goal, current codebase context, constraints, risk, test expectations

Plan shape:
- Goal
- Architecture
- File map
- Task sequence
- Tests and verification
- Rollout or migration notes

Critique focus:
- Scope control
- File ownership
- Testability
- Sequencing
- Missing edge cases
- Ambiguous handoffs

Reusable preferences:
- Preferred planning granularity
- TDD strictness
- Risk tolerance
- Commit and review cadence

## Technical Documentation

Frame:
- User role, task, prerequisites, expected outcome

Plan shape:
- What this is for
- Minimal working path
- Step-by-step instructions
- Examples
- Troubleshooting
- Reference details

Critique focus:
- Correctness
- Completeness
- User path clarity
- Example quality
- Hidden assumptions

Reusable preferences:
- Example-first or concept-first
- Concision level
- Troubleshooting depth

## Design Doc Or Product Spec

Frame:
- Problem, users, goals, non-goals, constraints, success metrics

Plan shape:
- Context
- Goals and non-goals
- Proposed design
- Alternatives
- Risks
- Open questions
- Rollout and validation

Critique focus:
- Problem clarity
- Constraint coverage
- Alternatives
- Failure modes
- Measurable success

Reusable preferences:
- Decision record depth
- Preference for diagrams or prose
- Risk documentation style

## Technical Critique Rubric

- Can the target reader execute or review the work without hidden context?
- Are files, interfaces, tests, commands, examples, or success metrics concrete?
- Does each task or section have one clear responsibility?
- Are risky migrations, shared contracts, or irreversible decisions isolated?
- Is verification proportional to risk?
- Are placeholders and vague steps removed or explicitly marked as unknown?

Specific critique example:
> "Tasks 3 and 5 both modify `session.ts` without assigning ownership — one
> team will block the other. Assign one task to own the interface change."

Generic critique to avoid:
> "Are file boundaries clear?"
