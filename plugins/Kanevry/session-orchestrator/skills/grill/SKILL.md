---
name: grill
description: Use when the user wants a plan, design, or PRD stress-tested before any build — relentlessly interrogates one decision at a time, grounds every question in the codebase, hunts contradictions against the domain language and the code, and challenges the load-bearing assumptions. Triggered by "grill me", "stress-test this plan", "poke holes in my design". Composable — run standalone or as an adversarial pass before /plan feature.
model: inherit
color: red
tools: Read, Grep, Glob, Bash, Write
---

# Grill Skill

> Adversarial pressure-test for a plan, design, or PRD the user already believes in. The complement to `/brainstorm`: brainstorm *narrows* an ambiguous design space cooperatively; grill *attacks* a settled-feeling plan to find what's wrong before it's built. Optionally writes `docs/specs/YYYY-MM-DD-<slug>-grill.md`. No HARD-GATE — composable by design.

## Soul Reference

Read `soul.md` in this skill directory before anything else. It defines WHO you are — the Interrogator, a staff engineer playing devil's advocate. The Five Tactics in soul.md (glossary conflict, sharpen fuzzy language, code contradiction, edge-case scenario, assumption audit) are the substance of every grill; internalize them before Phase 0.

## When to use

- A plan, design, PRD, or `STATE.md` wave plan exists and the user wants it stress-tested before committing
- The user says "grill me", "poke holes in this", "stress-test this plan", "what am I missing?"
- A decision *feels* settled but rests on unverified assumptions about the codebase, appetite, or domain
- An adversarial pass is wanted between `/brainstorm` (or `/plan feature`) and implementation

## When NOT to use

- The design is still *ambiguous* rather than untested → use `/brainstorm` to narrow it first; there's nothing to grill yet
- The user wants a formal PRD + issues, not a challenge → use `/plan feature`
- Pure bug investigation → use `/debug`
- The user wants you to generate options → that's `/brainstorm`; grill attacks the option the user brought, it doesn't invent new ones

## Phase 0: Target Acquisition

Establish *what* you are grilling and ground yourself in the *code* before asking the user anything.

1. **Resolve the target.** Parse `$ARGUMENTS`:
   - A file path (e.g. `docs/prd/2026-06-09-export.md`, `STATE.md`, a spec) → read it in full.
   - A topic/slug or empty → grill the plan or idea already present in the current conversation. If there is no plan in context, ask the user — via AUQ — to state the plan in one or two sentences before continuing.
2. **Ground in the codebase.** Read the project's domain language if present (`CONTEXT.md`, `.orchestrator/steering/*.md`, relevant `docs/adr/*`), then Grep/Glob the areas the plan touches. Build a short mental model of what the code *actually* does today. This is what lets you run the code-contradiction tactic.
3. **State the target back.** In 1–2 plain-text sentences, summarize what you understand the plan to be and what you've grounded it against. This catches a wrong target before you waste a grill on it.

Do NOT write code, scaffold, or commit in this phase or any phase. The only write a grill ever performs is the optional summary in Phase 4.

## Phase 1: Map the Decision Tree

Before interrogating, lay out the branches. Identify the decisions the plan depends on, ordered root-to-leaf (resolve foundational decisions before the ones that hang off them). Surface this map to the user in plain text as a short ordered list — it sets the agenda and lets the user re-order or add a branch you missed.

A branch belongs on the map when its resolution would change what gets built. Skip decisions the codebase already settles — note them as "already answered by the code: …" instead of asking.

## Phase 2: The Grill Loop

Walk the decision tree **one question at a time**. For each branch, in order:

1. **Try the code first.** If the question is answerable by reading the repo, read it and resolve the branch yourself — report the finding, don't ask.
2. **Apply a tactic.** Frame the question through whichever of the Five Tactics fits: a glossary conflict, a fuzzy term to sharpen, a code contradiction you found in Phase 0, an edge-case scenario, or an assumption to audit.
3. **Ask via AUQ.** Pose the challenge as a single `AskUserQuestion` call with your recommended resolution first:

```
AskUserQuestion({
  questions: [{
    question: "Your code cancels whole Orders, but the PRD says a customer can cancel one line item. Which is the real model?",
    header: "Cancellation Scope",
    options: [
      { label: "Line-item cancellation (Recommended)", description: "Matches the PRD intent. Cost: new partial-refund path + Order stays open after one item is voided." },
      { label: "Whole-order only", description: "Matches today's code. Cost: contradicts the stated user story — re-scope the PRD." },
      { label: "Both, behind a flag", description: "Defers the decision. Cost: two code paths to test and maintain." },
      { label: "Other / describe below", description: "Resolve it a different way — describe how." }
    ],
    multiSelect: false
  }]
})
```

> **Grill runs in the coordinator thread.** `AskUserQuestion` is unavailable inside dispatched subagents (`.claude/rules/ask-via-tool.md` AUQ-004), and every grill question is an AUQ. If grill is ever invoked headless or from a subagent, it cannot ask — the questions must bubble to a coordinator that owns the AUQ surface. (This is also why an "autonomous subagent grill" is structurally impossible — a useful thing to surface if a plan under grill proposes one.)

**AUQ format rules (AUQ-001 compliant, every question):**
- One question per call. Option 1 is ALWAYS `(Recommended)`, with one sentence of reasoning stated in plain text *before* the call.
- Each option names a concrete cost or consequence — not just the choice, but what it commits you to.
- Always include `Other / describe below` so the user can resolve a challenge in a way you didn't anticipate.
- `multiSelect: false` unless the branch genuinely admits multiple simultaneous answers.

4. **Record and descend.** After each answer, append to the running summary (below) and let the resolved answer pick the next branch. If an answer contradicts an earlier one, surface the collision immediately and re-resolve before continuing.

Maintain a running summary, surfaced in plain text between questions:

```
## Resolved So Far
- Cancellation scope: line-item (was: whole-order in code → PRD wins, code needs a partial-refund path)
- Idempotency: caller-supplied key, rejected duplicates
- ...
## Still Open
- Rollback path under partial-ship race
```

**Termination.** Stop when every branch on the map is resolved, when the user calls it (e.g. "good enough"), or when remaining branches are genuine unknowns that need runtime data rather than a decision. Fewer, sharper questions beat exhaustive ones — the grill serves the plan, not thoroughness for its own sake.

## Phase 3: Resolved-Decisions Recap

Present a final plain-text recap before any hand-off:

- **Resolved decisions** — each branch and how it was settled.
- **Contradictions surfaced** — every collision the grill found (glossary, code, or internal), and its resolution. This is the grill's primary output; make it visible.
- **Open questions** — genuine unknowns that couldn't be settled here.
- **Assumptions audited** — load-bearing assumptions you challenged and where they landed (held / revised / flagged risky).

## Phase 4: Hand-off

Per the user's configured behaviour, the grill ends with a hand-off and an OPTIONAL summary file — never a forced artifact. Ask via AUQ:

```
AskUserQuestion({
  questions: [{
    question: "Grill complete. How do you want to proceed?",
    header: "Grill Hand-off",
    options: [
      { label: "Write grill summary + hand off to /plan feature (Recommended)", description: "Persist resolved decisions to docs/specs/, then formalize into a PRD." },
      { label: "Write grill summary only", description: "Keep the resolved decisions as a reference; no further step now." },
      { label: "Hand off to /plan feature — no file", description: "Carry the resolved decisions straight into planning; nothing persisted." },
      { label: "Done — no file, no hand-off", description: "The grilling itself was the value; leave no artifact." }
    ],
    multiSelect: false
  }]
})
```

**If a summary is requested** (options 1 or 2), generate today's date via `date +%Y-%m-%d`, derive `<slug>` from the target (lowercase, hyphens), `mkdir -p docs/specs`, and write `docs/specs/YYYY-MM-DD-<slug>-grill.md`:

```markdown
# [Target Name] — Grill Summary

> Generated by /grill on YYYY-MM-DD. Status: decisions resolved, not yet planned.

## Target
[What was grilled — file path, PRD, or one-line plan description, and what it was grounded against.]

## Resolved Decisions
| Decision | Resolution | Rationale |
|----------|-----------|-----------|
| [Branch] | [How it was settled] | [Why — including any code/glossary evidence] |

## Contradictions Surfaced
- [Collision found] → [how it was resolved]
(If none: "No contradictions surfaced — the plan held under interrogation.")

## Assumptions Audited
- [Assumption] → held / revised / flagged risky — [note]

## Open Questions
- [Genuine unknown needing more info or runtime data]
(If none: "No open questions — every branch was resolved.")

## Out of Scope
- [Anything the grill explicitly pushed out of this plan]
```

Do NOT leave any section with "TBD", "TODO", or placeholder text. Genuine unknowns go in Open Questions.

**If handing off** (options 1 or 3), confirm the hand-off in plain text:

> "Decisions resolved. Run `/plan feature` — reference `docs/specs/YYYY-MM-DD-<slug>-grill.md` as the input brief." (omit the path reference for option 3)

## Anti-Patterns

- **Asking what the code can answer** — every question the repo could settle is a Phase 0 failure; Grep first, ask only what the code can't tell you
- **Batching questions** — a multi-question volley defeats the one-branch-at-a-time discipline and produces shallow answers
- **Neutral options** — every AUQ must mark exactly one option `(Recommended)`; non-commitment undermines the grill
- **Grilling an ambiguous design** — if there's no settled plan to attack, stop and recommend `/brainstorm`; you stress designs, you don't invent them
- **Swallowing a contradiction** — when an answer collides with the code or an earlier answer, surfacing it is the whole job; never let it slide to keep the conversation smooth
- **Forcing an artifact** — the summary file is opt-in per Phase 4; a grill that resolved everything in-conversation and the user says "done" leaves no file
- **Writing code or committing** — a grill resolves decisions; it never implements them

## See Also

- `skills/brainstorm/SKILL.md` — cooperative design narrowing; the sibling you recommend when the design is still ambiguous
- `skills/plan/SKILL.md` — primary hand-off target; formalizes resolved decisions into a PRD + issues
- `skills/write-executable-plan/SKILL.md` — alternative hand-off for direct execution
- `.claude/rules/ask-via-tool.md` — AUQ usage convention (AUQ-001..005)
- `.claude/rules/receiving-review.md` — the skeptical-posture discipline grill embodies (RCR-003)
