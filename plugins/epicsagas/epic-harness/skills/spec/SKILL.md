---
name: spec
description: "Spec phase. Converts user requirements into a numbered Requirements + Acceptance Criteria document saved as SPEC-{timestamp}.md. Prompts /team suggestion when 3+ requirements are detected."
---

# Spec — Define What to Build

**CRITICAL**: Run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

## Process

1. **Understand the request**
   - Read any existing context (CLAUDE.md, README, codebase structure)
   - If the request is vague, ask focused questions (max 3 at a time)
   - Never assume — clarify ambiguity before proceeding

2. **Produce the spec**
   Write a concise spec covering:
   - **Goal**: One sentence — what does this achieve?
   - **Scope**: What's included and explicitly excluded
   - **Requirements**: Numbered list (`R1`, `R2`, ...) of concrete, testable behaviors
   - **Acceptance criteria**: Numbered list (`AC1`, `AC2`, ...) — observable outcomes that prove each requirement is met
   - **Technical notes**: Constraints, dependencies, edge cases

3. **Confirm with user**
   Show the spec in digestible chunks. Get explicit approval before proceeding.

## Output

Save the approved spec to `$HARNESS_DIR/specs/SPEC-{timestamp}.md` using this exact format:

```markdown
---
status: approved
created: {ISO-8601 timestamp}
goal_slug: {kebab-case-goal-summary}
---

# SPEC-{timestamp}: {Goal}

## Goal
{One sentence}

## Scope
- In: {what is included}
- Out: {what is explicitly excluded}

## Requirements
- R1: {concrete testable behavior}
- R2: {concrete testable behavior}

## Acceptance Criteria
- AC1 (R1): {observable outcome proving R1}
- AC2 (R2): {observable outcome proving R2}

## Technical Notes
{Constraints, dependencies, edge cases}
```

After saving:
1. Count the Requirements (R1, R2, ...). If 3 or more, check team status: `epic team status`.
   - If no team is linked: suggest **"This spec has N requirements. Consider running `/team` to set up a project-specific agent team before `/go`."**
   - If a team is already linked: skip this hint.
2. Tell the user: **"Spec saved. Run `/go` to start building."**

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "It's a small change, I'll just code it" | Small changes still have wrong assumptions | Write the spec — it takes 2 minutes |
| "I'll refine the spec after coding" | Spec after code is documentation, not planning | Spec first, code second |
| "The user didn't give me enough detail" | Then ask — don't invent requirements | Ask focused questions, max 3 at a time |

## Evidence Required

- [ ] Spec file exists at `$HARNESS_DIR/specs/SPEC-{timestamp}.md`
- [ ] Frontmatter has `status: approved`
- [ ] Every Requirement has at least one Acceptance Criterion
- [ ] ACs are observable (can be tested or verified)

## Red Flags

- Writing code before the spec is approved
- Assuming requirements that weren't stated
- Producing a 3-page spec for a 1-line change
- Acceptance criteria that cannot be verified by a test or observation
- Skipping this phase for non-trivial features
