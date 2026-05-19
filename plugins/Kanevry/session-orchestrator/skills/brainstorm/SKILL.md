---
name: brainstorm
description: Use when you have a feature idea but the scope or UX is still ambiguous — runs a lightweight Socratic design dialogue (3-5 AUQ rounds) and writes a spec markdown file. Use BEFORE /plan feature when product intent needs validation; skip to /plan feature when scope is already clear. HARD-GATE prevents any code work until the design is user-approved.
model: inherit
color: cyan
tools: Read, Grep, Glob, Bash, Write
---

# Brainstorm Skill

> Lightweight Socratic design dialogue for per-feature exploration. Sibling to `/plan feature`, not a replacement. Produces `docs/specs/YYYY-MM-DD-<slug>-design.md` after the user approves an approach.

## Soul Reference

Read `soul.md` in this skill directory before anything else. It defines WHO you are — a Design Facilitator who shapes vague ideas into approved designs through Socratic questioning. Every interaction in this skill should reflect that identity.

## When to use

- A new feature is requested but the UX, product surface, or scope is still ambiguous
- The user wants design validation before committing to a full PRD
- Multiple plausible approaches exist and the trade-offs need to be surfaced first
- A "what should this look like?" question that would otherwise collapse into unfocused implementation work

## When NOT to use

- Scope is already clear → use `/plan feature` directly
- A full project kickoff is needed → use `/plan new`
- A spec or PRD already exists → use `/plan feature` to formalize it
- Pure bug fixes or regressions → use `/debug` (issue #37) once shipped

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If GATE_CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before returning here. If GATE_OPEN, continue.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY brainstorm regardless of perceived simplicity.

There is no bypass. There is no exception for urgent requests, demo features, or spike work.
The ONLY valid next action when the design is unapproved is presenting a design and waiting for user approval.
</HARD-GATE>

## Phase 1: Frame the Problem

Parse `$ARGUMENTS` for an optional topic or feature slug. The slug will be used in the spec filename. If absent, derive it from the user's Phase 1 answer.

Run a single AUQ to let the user characterize the problem in their own words:

```
AskUserQuestion({
  questions: [{
    question: "Describe the feature or problem you want to brainstorm. What's the core pain point it addresses, and what's still ambiguous to you?",
    header: "Feature Frame",
    options: [
      { label: "UX / user-facing surface is unclear", description: "You know what you want to build but not how it should work for the user." },
      { label: "Scope / boundaries are unclear", description: "You're not sure how much to build, or where one feature ends and another begins." },
      { label: "Multiple approaches exist — need to pick one", description: "You see 2-3 ways to solve this and aren't sure which is best." },
      { label: "Other / describe below", description: "Free-form: describe the ambiguity in the next prompt." }
    ],
    multiSelect: false
  }]
})
```

After the user responds, confirm your understanding with a 1-2 sentence summary before continuing.

## Phase 2: Socratic Dialogue (3-5 AUQ rounds)

Run 3 to 5 AUQ rounds. Each round asks ONE question. Stop when the design space is sufficiently constrained — fewer rounds is better. Do NOT run more than 5 rounds; if still ambiguous after 5, recommend switching to `/plan feature`.

**Round topics (select the most relevant; do not ask redundant questions):**

1. **User-facing surface** — who triggers this feature, what do they see, what action do they take?
2. **Data shape** — what data is created, read, updated, or deleted? Any persistence, sync, or external service involved?
3. **Integration points** — what existing systems, APIs, or modules does this touch? What must NOT change?
4. **Risk / reversibility** — what could go wrong? Is this easy to roll back if it doesn't work?
5. **Success criteria** — how will you know this feature is working correctly in production?

**AUQ format rules for every round:**
- Present 2-4 options; Option 1 is ALWAYS marked `(Recommended)`
- Each option has a `description` with a concrete pro/con (one sentence each)
- Include an `Other / describe below` option when free-form input makes sense
- `multiSelect: false` unless the question is genuinely multi-select (e.g., integration targets)

Example round (adapt to the actual feature):

```
AskUserQuestion({
  questions: [{
    question: "Who is the primary user of this feature, and how do they trigger it?",
    header: "User Surface — Round 2",
    options: [
      { label: "Authenticated user via UI action (Recommended)", description: "Pro: fits existing session model. Con: requires UI component work." },
      { label: "Automated trigger (webhook, cron, event)", description: "Pro: no manual user step. Con: harder to debug and test." },
      { label: "Admin-only operation", description: "Pro: simpler access control. Con: limits who can self-serve." },
      { label: "Other / describe below", description: "Describe the trigger mechanism." }
    ],
    multiSelect: false
  }]
})
```

After each round, record the answer in a running summary:

```
## Design Answers (Round N/M)
- User surface: [answer]
- Data shape: [answer]
- ...
```

Present this summary in plain text between rounds so the user can catch any misunderstanding.

## Phase 3: Synthesize Approaches

Once the dialogue has enough signal, synthesize 2-3 concrete implementation approaches and present them via AUQ:

```
AskUserQuestion({
  questions: [{
    question: "Based on your answers, here are the viable approaches. Which fits best?",
    header: "Design Approach",
    options: [
      { label: "Approach A — [1-sentence summary] (Recommended)", description: "Trade-offs: [key pro]. [key con]. Complexity: low/medium/high." },
      { label: "Approach B — [1-sentence summary]", description: "Trade-offs: [key pro]. [key con]. Complexity: low/medium/high." },
      { label: "Approach C — [1-sentence summary]", description: "Trade-offs: [key pro]. [key con]. Complexity: low/medium/high." }
    ],
    multiSelect: false
  }]
})
```

Mark the approach that best balances user value, reversibility, and smallest scope as `(Recommended)`. State your reasoning in one sentence before the AUQ call (plain text, not another question).

If the user selects "Other" or asks for modifications, incorporate the feedback and re-present before proceeding.

## Phase 4: Write Spec

Generate today's date via `date +%Y-%m-%d`. Derive `<slug>` from the feature name (lowercase, hyphens, no special characters). Ensure the target directory exists:

```bash
mkdir -p docs/specs
```

Write `docs/specs/YYYY-MM-DD-<slug>-design.md` with the following sections:

```markdown
# [Feature Name] — Design Spec

> Generated by /brainstorm on YYYY-MM-DD. Status: draft.

## Problem

[1-3 sentences: what pain point does this address, and for whom?]

## Chosen Approach

[Name of the selected approach from Phase 3. 2-4 sentences describing the design decision.]

## Trade-offs Accepted

| Trade-off | Rationale |
|-----------|-----------|
| [Pro accepted] | [Why this matters] |
| [Con accepted] | [Why it's tolerable] |

## Open Questions

- [Genuine unresolved question that needs more information or runtime data]
- [Another genuine open question, if any]

(If none: "No open questions — all design decisions were resolved in the dialogue.")

## Out of Scope

- [Explicitly excluded item 1 — prevents scope creep]
- [Explicitly excluded item 2]

## Hand-off

Recommended next step: `/plan feature` to formalize this design into a PRD with acceptance criteria and issue creation.
```

Do NOT leave any section with "TBD", "TODO", or placeholder text. Genuine open questions go in the Open Questions section. Unresolved items that are explicitly deferred go in Out of Scope.

## Phase 5: Self-Review Pass

Read the written spec back. Verify all of the following before proceeding:

1. **No placeholders** — no "TBD", "TODO", or empty bullet points remain
2. **Internal consistency** — the Chosen Approach matches the Design Answers from Phase 2
3. **Genuine open questions** — Open Questions contains only real unknowns, not items that were resolved in the dialogue
4. **Explicit scope boundary** — Out of Scope contains at least one item
5. **Slug accuracy** — the filename matches the feature name (lowercase, hyphens)

If any check fails, fix the spec before Phase 6.

## Phase 6: Hand-off

Present the spec path and summary to the user. Then ask via AUQ:

```
AskUserQuestion({
  questions: [{
    question: "The design spec has been written to docs/specs/YYYY-MM-DD-<slug>-design.md. How do you want to proceed?",
    header: "Design Hand-off",
    options: [
      { label: "Proceed to /plan feature (Recommended)", description: "Formalize this spec into a PRD with acceptance criteria and issue creation." },
      { label: "Proceed to /write-executable-plan", description: "Skip the formal PRD and go straight to an executable plan (issue #39, once shipped)." },
      { label: "Revise the spec", description: "I have feedback — describe what to change and I'll update the spec." },
      { label: "Done for now", description: "Keep the spec as a reference; no immediate next step." }
    ],
    multiSelect: false
  }]
})
```

If the user selects "Revise the spec", incorporate the feedback, update `docs/specs/YYYY-MM-DD-<slug>-design.md`, and re-present Phase 6.

If the user selects "Proceed to /plan feature", confirm the hand-off:

> "Design approved. Run `/plan feature` and reference `docs/specs/YYYY-MM-DD-<slug>-design.md` as the input PRD brief."

## Anti-Patterns

- **Brainstorming when scope is already clear** — if the user describes a fully-specified feature, stop and recommend `/plan feature` directly
- **Skipping the HARD-GATE** — never call Edit, Write (for code), or Bash (for implementation) during the dialogue; the only Write call allowed is the spec file in Phase 4
- **More than 5 AUQ rounds** — if you need more rounds, the ambiguity requires `/plan feature` depth
- **Writing the spec before Phase 3 approach selection** — Phase 3 approval is the gate for Phase 4
- **Neutral recommendations** — every AUQ must have one option marked `(Recommended)`; being non-committal undermines the dialogue
- **Open Questions that aren't open** — if the question was answered in the dialogue, it belongs in Chosen Approach, not Open Questions

## See Also

- `skills/brainstorm/soul.md` — Design Facilitator identity
- `skills/plan/SKILL.md` — primary hand-off target after design approval
- `skills/write-executable-plan/SKILL.md` — alternative hand-off for direct execution (issue #39)
- `.claude/rules/ask-via-tool.md` — AUQ-001..005 tool usage conventions
- `skills/_shared/bootstrap-gate.md` — bootstrap gate protocol
