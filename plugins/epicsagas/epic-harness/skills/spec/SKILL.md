---
name: spec
description: "Spec phase. Converts user requirements into a numbered Requirements + Acceptance Criteria document saved as SPEC-{timestamp}.md. Prompts /team suggestion when 3+ requirements are detected."
---

# Spec — Define What to Build

**CRITICAL**: Run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

## Process

1. **Understand the request**
   - Read any existing context (CLAUDE.md, README, codebase structure)
   - If `.epic/team.md` (or `.epic/team.local.md`) has a `## spec` section, each of its bullets is required spec content, not advice. Missing one is a `GAP:` in the readiness gate.
   - If the request is vague, ask focused questions (max 3 at a time)
   - Never assume — clarify ambiguity before proceeding

2. **Produce the spec**
   Write a concise spec covering:
   - **Goal**: One sentence — what does this achieve?
   - **Scope**: What's included and explicitly excluded
   - **Requirements**: Numbered list (`R1`, `R2`, ...) of concrete, testable behaviors
   - **Acceptance criteria**: Numbered list (`AC1`, `AC2`, ...) — observable outcomes that prove each requirement is met
   - **Technical notes**: Constraints, dependencies, edge cases
   - **Right-size**: for a one-shot change (1–2 requirements) keep Scope and Technical Notes to one line each. Never skip the file, the gate, or the two record sections below; a small change with no record is how decisions get invented twice.

3. **Readiness gate** (adversarial, one pass, before approval)
   Ask one question of the draft: *could a different engineer implement this spec without inventing a decision that nothing records?*
   - Walk every R and AC. For each, name the decision an implementer would have to make that the spec does not settle (data shape, error path, boundary, ordering, naming, which existing module to extend).
   - Each gap is written as `GAP: R{n} — {missing decision}`. A gap is located, not vague: it points at one R or AC.
   - Zero gaps → proceed to step 4. One or more gaps → resolve each with the user (max 3 questions at a time), fold the answer into the spec, re-run the gate once.
   - The gate fails the spec, not the user. A thin spec fails here, where it costs one conversation, instead of in `/audit`, where it costs a rebuild.

4. **Confirm with user**
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

## Readiness Gate
{One line per gap found in step 3, each with how it was settled, or `none`:}
- GAP: R{n} — {decision the spec did not settle} → settled: {answer, and who decided: user | assumption}

## Implementation Notes
<!-- Agent-owned. Append-only during /go: decisions the spec left open, files touched beyond the plan, surprises. Empty at approval. Sections above this line are frozen after approval. -->
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
- [ ] Readiness gate run once; every gap and its resolution is recorded under `## Readiness Gate` (or `none`)
- [ ] `## Implementation Notes` present and empty
- [ ] ACs are observable (can be tested or verified)

## Red Flags

- Writing code before the spec is approved
- Assuming requirements that weren't stated
- Producing a 3-page spec for a 1-line change
- Acceptance criteria that cannot be verified by a test or observation
- Approving a spec with an open `GAP:` line ("the implementer will figure it out" is the gate failing)
- Skipping this phase for non-trivial features
