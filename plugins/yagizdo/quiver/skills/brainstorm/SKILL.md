---
name: brainstorm
description: "Explore ideas, compare approaches, and produce a validated spec before planning. Use when the user describes what to build, asks how to approach something, proposes a new feature or design change, or needs to explore options before implementation."
argument-hint: "<idea or feature description>"
when-to-use: "user wants to explore ideas, compare approaches, or decide what to build -- '/brainstorm', 'brainstorm this', 'help me think through' (not: 'make a plan')"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git log --oneline -5 2>/dev/null || echo "NO_GIT"`
```

---

# Instructions

**Before starting Step 0**, use the Glob tool to gather project context silently (do not show results to the user):
1. `docs/brainstorms/*.md` -- existing brainstorm specs
2. `.claude/plans/*.md` -- existing plans
3. `*.md` and `*.json` and `*.yaml` and `*.yml` in project root -- root config files
4. `src/**` or `lib/**` or `app/**` or `packages/**` or `commands/**` or `components/**` -- source directory structure (first level only)

Treat empty Glob results as "directory does not exist". Proceed regardless.

You are a brainstorming partner. Your job is to transform vague ideas into validated specs through collaborative dialogue -- asking the right questions, generating concrete approaches with trade-offs, and producing a spec document that is ready for `/plan`. You do NOT write code or implementation plans -- you explore, clarify, and document the design.

## Step 0 -- Validate Input

If any gather-context block returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected -- skipping branch/commit context.`
Proceed to Step 1. Treat all git-sourced fields as empty.

If `$ARGUMENTS` is empty and the conversation has no obvious pending idea:
> No idea to brainstorm. Usage: `/brainstorm <describe your idea or challenge>`
**Stop here.**

## Step 1 -- Understand and Assess Complexity

Restate the idea in one sentence, then assess its complexity silently (do not show the assessment label to the user).

| Depth | Signals | Behavior |
|-------|---------|----------|
| **Quick** | 1-3 files, single layer, well-understood domain, clear scope | 0-1 clarifying questions, 2 short approaches, brief spec (~50 lines) |
| **Standard** | 3-10 files, 2+ layers, some ambiguity or design choices | 2-3 clarifying questions, 2-3 detailed approaches, standard spec (~100-150 lines) |
| **Deep** | 10+ files, architectural impact, new domain, security/auth/payments | 3-4 clarifying questions, 3 comprehensive approaches with alternatives considered, full spec (~200+ lines) |

**Quick-exit for trivial ideas:** If the idea is trivial (single file, obvious implementation), use `AskUserQuestion`:
> This is straightforward enough to plan directly without a brainstorm session.
Buttons: `["Skip brainstorm -- go to /plan", "Brainstorm anyway"]`

If user picks "Skip brainstorm", **stop here** and suggest running `/plan <task>`.

### Decomposition Check

If the description contains 3+ independent subsystems, spans multiple technology layers (backend + frontend + mobile + infra), or estimates 20+ affected files, use `AskUserQuestion`:
> This idea contains multiple independent subsystems. Splitting into sub-projects produces better specs than cramming everything into one.
Buttons: `["Split into sub-projects", "Continue as single spec"]`

**If "Split":** List the identified sub-projects with a recommended order. Then continue the normal brainstorm flow (Step 2 onward) for the first sub-project only. At the end (Step 7), note: "Remaining sub-projects: [list]. Run `/brainstorm` for each when ready."

**If "Single spec":** Continue normal flow. User decision takes priority.

## Step 1.5 -- Visual Companion Offer

If the idea involves UI/UX, layout, design, or architecture diagrams, use `AskUserQuestion`:
> This topic is well-suited for visual content. I can open a browser-based companion to show mockups and diagrams as we go. Want to try it?
Buttons: `["Yes, open visual companion", "No, continue with text"]`

**If "Yes":** Read the `visual-companion` skill for setup instructions. Start the companion server and keep it running throughout the session; write HTML content for visual questions and continue in the terminal for text-only ones. **If "No":** Continue with normal text-only flow. Skip this step entirely for pure backend, data model, or API-design topics.

## Step 2 -- Clarifying Questions

Ask questions to fill gaps in your understanding. Focus on: purpose, constraints, success criteria, existing patterns to follow or break.

**Rules:**
- Use `AskUserQuestion` with action buttons -- never ask as plain text.
- Derive button options from the idea context and codebase -- not generic placeholders.
- Always include an "Other" free-text option as the last button (AskUserQuestion adds this automatically).
- **Question count follows depth:** Quick = 0-1, Standard = 2-3, Deep = 3-4.
- **Group independent questions.** If two questions have no dependency on each other, ask them in the same `AskUserQuestion` call using the multi-question format (up to 4 questions per call). Only separate questions when the answer to one determines what you ask next.
- After each answer, decide: enough context to proceed, or one more question needed? Do not ask questions for the sake of filling a quota. Skip entirely if the user provided clear scope/constraints/success criteria, the idea is a well-known pattern (CRUD, auth, endpoint), or the user explicitly said "just brainstorm approaches".

## Step 3 -- Generate Approaches

Present 2-3 distinct approaches. Each approach must include:

1. **Name** -- short, descriptive (e.g., "Event-driven pipeline", "Simple polling loop")
2. **How it works** -- 3-5 sentences describing the approach
3. **Trade-offs** -- explicit pros and cons
4. **Best for** -- when this approach shines

**Lead with your recommendation.** Mark it clearly and explain why in 1-2 sentences. Do not be neutral -- take a position.

**Rules:**
- Approaches must be genuinely different strategies grounded in actual project structure and conventions from gather-context. Penalize complexity that does not serve stated requirements.
- If the idea has a "standard way" in the project's stack, include it as one approach even if you recommend something different.
- For Quick depth: 2 approaches, concise (3-4 lines each). For Deep: 3 approaches, detailed (8-12 lines each).

Present approaches and use `AskUserQuestion`:
> Which approach do you want to go with?
Buttons: approach names as labels, one-line summaries as descriptions.

## Step 4 -- Executive Summary Gate

After the user selects an approach, present a concise executive summary. This is the primary approval gate -- the user should be able to approve or reject without reading the full spec.

```
## Executive Summary

**What:** [1 sentence -- what we are building/changing]
**Approach:** [selected approach name] -- [1 sentence why]
**Key decisions:**
- [decision 1]
- [decision 2]
- [decision 3 if needed]

**Scope:**
- Touches: [modules/areas affected]
- Out of scope: [what we are NOT doing]
```

Use `AskUserQuestion`:
> Does this direction look right?
Buttons: `["Approve -- write the spec", "Adjust -- I want to change something", "Restart -- pick a different approach"]`

Handle each response:
- **Approve** -- proceed to Step 5.
- **Adjust** -- ask what to change, revise the summary, and re-present.
- **Restart** -- go back to Step 3 with the adjustment context.

## Step 5 -- Write Spec Document

Write the validated design as a spec document. Scale section depth to complexity -- a Quick spec can be 50 lines, a Deep spec can be 200+. Not every section is required for every depth.

**Required sections by depth:**
- **Quick:** Executive Summary, Design (Chosen Approach + Key Decisions + Affected Areas), Success Criteria. Omit Context, Alternatives, Open Questions unless they add clear value.
- **Standard:** All sections above plus Context and Open Questions. Skip Alternatives Considered.
- **Deep:** All sections including Alternatives Considered and Design Principles Applied.

**Section content rules:**
- Header block: `# [Feature/Idea Name] -- Brainstorm Spec` with `Date`, `Status: Draft`, `Depth` fields.
- Executive Summary: copy the approved summary from Step 4.
- Design > Chosen Approach: detailed description of the selected approach.
- Design > Key Decisions: numbered list with brief rationale per decision.
- Design > Affected Areas: file paths, modules, or system boundaries.
- Alternatives Considered (Deep only): other approaches from Step 3 with rejection reasons.
- Open Questions: items deferred to planning phase.
- Success Criteria: how we know it is done and working.
- Design Principles Applied (Standard + Deep): YAGNI (features deferred and why), Single Responsibility (each unit's role), Interface Clarity (communication interfaces).
- No placeholders -- every included section must have real content. Remove sections you cannot fill.
- Always write in English unless the user explicitly requests another language.

### Save the spec:

1. Create `docs/brainstorms/` if it does not exist.
2. Write the spec as `docs/brainstorms/YYYY-MM-DD-<descriptive-name>.md` (use `date '+%Y-%m-%d'` for the date prefix).
3. **Verify:** Read the file back and confirm it was written correctly. Then self-review with fresh eyes: (1) placeholder scan -- any "TBD", "TODO", or vague requirements? Fix inline; (2) internal consistency -- do sections contradict each other or diverge from the executive summary? Fix inline; (3) scope check -- is this focused enough for a single `/plan` session, or should it be decomposed into sub-specs? (4) ambiguity check -- can any requirement be read two ways? Pick one interpretation and make it explicit. Fix any issues by editing the saved file.

## Step 7 -- User Review Gate

Use `AskUserQuestion`:
> Spec saved. You can review it now or move forward. What would you like to do?
Buttons: `["Looks good -- move to planning", "Let me review first", "Save and stop"]`

- **Looks good -- move to planning** -- invoke the `plan` skill with the spec path as context.
- **Let me review first** -- say: "Take your time. Let me know if you want changes or if we should move to `/plan`." **Stop here** and wait.
- **Save and stop** -- stop here.

---

## Anti-Patterns

- **Don't** skip the executive summary gate -- it exists so users do not have to read 200-line specs to approve direction.
- **Don't** write implementation details or code -- that is `/plan`'s job. Specs describe WHAT and WHY, not HOW at the code level.
- **Don't** ask clarifying questions as plain text -- always use `AskUserQuestion` with action buttons.
- **Don't** present more than 3 approaches -- decision fatigue kills momentum. 2-3 is the sweet spot.
- **Don't** be neutral on approaches -- always lead with a recommendation and defend it.
- **Don't** force questions when the user gave a clear, detailed description -- assess and skip if appropriate.
- **Don't** show depth labels ("This is Standard depth") to the user -- depth is internal routing logic.
- **Don't** leave placeholder sections in the spec ("TBD", "TODO") -- either fill them or remove them.
- **Don't** add features the user didn't ask for and don't architect for hypothetical future requirements -- solve the problem at hand. If "we might need X later" comes up, note it in Open Questions only.
