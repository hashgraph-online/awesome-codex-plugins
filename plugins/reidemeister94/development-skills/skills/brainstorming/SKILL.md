---
name: brainstorming
description: "Use when creating features, building components, adding functionality, modifying behavior, designing systems, choosing between approaches, or making architectural decisions."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Task, AskUserQuestion, Edit, Write, Skill
---

# Brainstorming — Conversational Design

**Task:** $ARGUMENTS — if empty, ask *"What would you like me to brainstorm?"* and STOP.

Interview the user relentlessly about every aspect of the plan until you reach a shared understanding and remove all the ambiguity. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer. Then sketch approaches, evaluate, write a plan, gate, hand off to `core-dev`.

## 0 — Hypothesis

Before any question, declare your read:

```
HYPOTHESIS: <one-sentence read of the intent>
CONFIDENCE: <0-100>%
```

If you can't predict the user's reaction to the next 3 questions you'd ask, the number is wrong. Honest 30% beats false 80%.

## 1 — Codebase scan

Glob + Grep + Read of entry points, similar features, related modules → `CODEBASE_FINDINGS`. Do this before any technical question.

## 2 — Q&A

Lock `WHY → scope → WHAT → quality bars → HOW → definition of done`. One topic at a time, resolve one branch before opening another.

- **Definition of done is a hard lock.** Before you finish, BOTH the problem/specs AND the 0-ambiguity verification procedure (the check that definitively says DONE/NOT-DONE) must be explicit — ask the user; if either is unclear, reach it via more Q&A + analysis of reality (codebase, docs, live database/logs). [`../../shared/definition-of-done.md`](../../shared/definition-of-done.md). It becomes the gate's **Success** line and the plan's **Verification strategy**.
- **Q + GUESS per question.** Every question carries your reasoned hypothesis — the user reacts faster to a wrong guess than to generating an answer cold. Format: `Q: <question> · GUESS: <hypothesis + reasoning> · CONFIDENCE: <0-100>%`. The number forces honesty.
- **WHY / scope / priority / trade-off can never be derived from the codebase** — always ask if missing.
- **95% stop test:** stop when you can predict the user's reaction to the next 3 questions you'd ask, or on *"enough"* / *"just propose"*. Three rounds without confidence rising → reframe.
- **Want vs. should-want rescue.** When an answer pattern-matches buzzwords (*"scalable"*, *"modern"*, *"the standard approach"*, *"I should probably…"*), ask: *"If you didn't have to justify this to anyone, what would you actually want?"* Often surfaces more than the previous five questions.

Use `AskUserQuestion`, up to 4 logically-related questions per call (dependent questions in separate calls). Recommended answer = first option, label `"[option] (Recommended)"`. End turn, wait.

## 3 — Approach sketch

Sketch 2-3 candidates, recommended first: each 1-2 sentence description · complexity LOW/MEDIUM/HIGH · key trade-off.

- **UI-surface task?** Give each approach a visual/UX dimension (the design-level trade-offs like modal vs inline belong in approach selection), and when the project ships a design system prefer composing its components — build-on-vs-hand-roll is itself an approach dimension.
- **Interface / API / module design?** Optionally invoke `references/design-it-twice.md`.

## 4 — Optional research

If approaches need external best practices, official docs, or unfamiliar tech, delegate to the research subagent. Skip if internal-only, well-known, or the codebase already shows the pattern.

Pick `NNNN` = highest existing prefix in `docs/plans/` + 1 (or `0001`); `SLUG` = kebab-case topic. Both reused in Step 7.

Dispatch via `Task`, `subagent_type: general-purpose`, `model: opus`. Read `../../shared/agents/research-agent.md`, fill `{TASK}`, `{RESEARCH_TARGETS}`, `{CODEBASE_FINDINGS}`, `{EXISTING_RESEARCH_FILE}` (usually `"none"`), `{NNNN}`, `{SLUG}`. The subagent writes `docs/plans/{NNNN}__research__{SLUG}.md` and returns `RESEARCH_PATH::<path>` + digest. **Read** the file after; pull the selected approach, anti-patterns, reusable patterns into context.

## 5 — Critical evaluation (always)

Read `critical-analysis.md` and apply it to every approach. Verdict per approach: **PROCEED / PROCEED WITH CHANGES / RECONSIDER / STOP**. If `RECONSIDER` or `STOP`, surface the reason and re-enter Step 2 or end.

## 6 — Approach selection

`AskUserQuestion`, 1 question, options = approaches + `"Just analysis"` + `"Modify"`. Wait.

- **Selected** → Step 7.
- **"Modify"** → ask what; simple edit re-present, fundamental re-enter Step 2.
- **"Just analysis"** → research file (if Step 4 ran) is already saved; end without a plan.

## 7 — Write plan file

Read `../../shared/templates/plan-template.md` (canonical schema). Write to `docs/plans/{NNNN}__YYYY-MM-DD__implementation_plan__{SLUG}.md` with the `NNNN`/`SLUG` from Step 4. Set `Status: In Progress`, `Current Phase: 1 (Research + Plan)`. WORKFLOW STATE MUST reference the research file path (if any) and include a Brainstorming Summary block. Phase 1 picks this file up.

## 8 — Gate + route

HARD-GATE: no code or scaffold until the design is presented AND user-approved — a long prior artifact is a stronger trigger, never an exemption (iron-rules P2). Display in chat first:

1. The canonical **6-line restate** — the misalignment kernel:

```
- Outcome:      <one line>
- User:         <one line — who benefits>
- Why now:      <one line — what changed>
- Success:      <one line — the 0-ambiguity verification procedure that says DONE>
- Constraint:   <one line — the binding limit>
- Out of scope: <one line — what we're explicitly NOT doing>
```

*"Out of scope" is non-negotiable* — half of misalignment is silent disagreement about what is NOT being built.

2. A plan-mode-style outline pulled from the plan file (announce its path): recommended approach + why-over-alternatives, files to modify, vertical-slice tasks with verification, key risks, out of scope. Enough for confident approval without opening the file; condense long sections with an explicit `...N more in the plan file`, never silently.

Gate via `AskUserQuestion` (always selectable — never ask the user to type approval): *"Approve the design and proceed to implementation?"* — `"Approve (Recommended)"`, `"Edit"`, `"Chat about"`. (`AskUserQuestion` auto-adds an "Other" free-text choice.)

**Non-yes detection (especially Codex):** *"Sounds good"*, *"Whatever you think"*, *"Sure let's go"*, silence-then-*"okay"* are NOT approval — they are ambiguity, delegation, or giving up. Ask what they'd refine, or reframe. Spirit beats letter.

- **Approve** → invoke `development-skills:core-dev` via Skill (no args) — its Step 1 detects `Status: In Progress` and proceeds without re-triggering brainstorming.
- **Edit** → ask what to change, edit the plan, re-restate, re-gate.
- **Chat about** → discuss without deciding (re-enter Step 2 as needed), then re-restate and re-gate.
