---
name: brainstorming
description: "Use when creating features, building components, adding functionality, modifying behavior, designing systems, choosing between approaches, or making architectural decisions."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Task, AskUserQuestion, Edit, Write, Skill
---

# Brainstorming — Conversational Design

<HARD-GATE>
No code, scaffold, or implementation action until design is presented AND user-approved. Every non-trivial task. A long prior artifact (audit, RFC, plan, ticket) is a *stronger* trigger, not an exemption. *"This is too simple"* / *"the audit already decided"* / *"this is just execution"* → STOP, display the design, gate. Process Rule D (`../../shared/iron-rules.md`): spirit beats letter.
</HARD-GATE>

Interview the user relentlessly about every aspect of the plan until you reach shared understanding. Walk down each branch of the design tree, resolving dependencies one-by-one. For each question, attach your reasoned guess. Optionally delegate web research. Write a plan to disk, gate before handing off to `core-dev`.

## YOUR TASK

**Task:** $ARGUMENTS

If `$ARGUMENTS` is empty: ask *"What would you like me to brainstorm?"* and STOP.

---

## STEP 0 — Hypothesis + Confidence

Before any question, declare your read of what the user wants:

```
HYPOTHESIS: <one-sentence read of the intent>
CONFIDENCE: <0-100>%
```

Calibration: *if you can't predict the user's reaction to the next 3 questions you would ask, the confidence number is wrong.* Honest 30% beats false 80%.

---

## STEP 1 — Codebase Scan

Lightweight: Glob + Grep + Read of entry points, similar features, related modules. Build a `CODEBASE_FINDINGS` mental note.

Do this **before** any technical question. Never ask the user something a 60-second look at the codebase would answer.

---

## STEP 2 — Q&A (Walk the Design Tree)

**Goal:** lock `WHY → scope → WHAT → quality bars → HOW`, parent decisions before children.

**Rules:**

1. **One topic at a time.** Resolve one branch before opening another.
2. **Q + GUESS per question.** Every question carries your reasoned hypothesis for the answer. *"The user reacts faster to a wrong guess than to generating an answer from scratch."* Format: `Q: <question> · GUESS: <hypothesis + reasoning> · CONFIDENCE: <0-100>%`. The number forces honesty.
3. **Multiple choice when possible**; open-ended only when no good options exist.
4. **Hard rule:** WHY / scope / priority / trade-off can never be derived from the codebase. Always ask if missing.
5. **95% stop test:** stop when you can predict the user's reaction to the next 3 questions you would ask. Or when the user says *"enough"* / *"just propose"*. Three rounds without confidence rising → step back and reframe.
6. **Anti-pattern:** do not infer or rationalize *"the user said X so probably means Y"*. When in doubt, ask.
7. **Want vs. should-want rescue.** When an answer pattern-matches buzzwords (*"scalable"*, *"modern"*, *"the standard approach"*, *"I should probably…"*), ask: *"If you didn't have to justify this to anyone, what would you actually want?"* Often surfaces more than the previous five questions.

Use `AskUserQuestion`. Up to 4 logically-related questions per call (answers don't reframe each other). Dependent questions in separate calls. Recommended answer = first option, label `"[option] (Recommended)"`.

End your turn. Wait for the user's reply.

---

## STEP 3 — Approach Sketch

Based on locked WHAT/WHY/scope, sketch **2-3 candidate approaches**:

- Each: 1-2 sentence description · complexity LOW/MEDIUM/HIGH · key trade-off.
- Lead with the recommended one.

**Interface / API / module design?** Optionally invoke `references/design-it-twice.md` — Ousterhout's technique: generate 2-3 radically different shapes with orthogonal constraints, compare, synthesize.

---

## STEP 4 — Optional Research

If approaches involve external best practices, official docs, or unfamiliar tech, delegate to the research subagent. Skip if internal-only, well-known, or the codebase already shows the pattern.

Pick `NNNN` = highest existing prefix in `docs/plans/` + 1 (or `0001`). Pick `SLUG` = kebab-case topic. Both reused in Step 7.

Dispatch via `Task`, `subagent_type: general-purpose`, `model: opus`. Read `../../shared/agents/research-agent.md`, fill `{TASK}`, `{RESEARCH_TARGETS}` (approaches to evaluate), `{CODEBASE_FINDINGS}`, `{EXISTING_RESEARCH_FILE}` (usually `"none"`), `{NNNN}`, `{SLUG}`. Pass as prompt.

The subagent writes `docs/plans/{NNNN}__research__{SLUG}.md` and returns `RESEARCH_PATH::<path>` + a 5-line digest.

After return, **Read** the research file. Pull the selected approach, anti-patterns, and reusable codebase patterns into your context.

---

## STEP 5 — Critical Evaluation (always performed)

Read `critical-analysis.md`. Run the Simplicity Audit (Iron Rules Pillar 1) for every approach. Score complexity (0-10). Apply MINIMAL (0-5) / MID (6-7) / FULL (8-10) framework. **No SKIP** — even score-0 gets a 2-line risk-and-mitigation.

Verdict: **PROCEED / PROCEED WITH CHANGES / RECONSIDER / STOP**. An approach that fails the Simplicity Audit is `RECONSIDER` regardless of other strengths. If `RECONSIDER` or `STOP`, surface the reason and re-enter Step 2 or end the flow.

---

## STEP 6 — Approach Selection

Present the candidates via `AskUserQuestion` — 1 question, options = approaches + `"Just analysis"` + `"Modify"`.

Wait for user reply.

- **Approach selected:** continue to Step 7.
- **"Modify":** ask what. Simple edit → re-present. Fundamental → re-enter Step 2.
- **"Just analysis":** if Step 4 ran, the research file is already saved. End without writing a plan.

---

## STEP 7 — Write Plan File

Read `../../shared/templates/plan-template.md` — the canonical schema. Write to:

`docs/plans/{NNNN}__YYYY-MM-DD__implementation_plan__{SLUG}.md`

Use the same `NNNN` and `SLUG` from Step 4. Set `Status: In Progress`, `Current Phase: 1 (Research + Plan)`. The WORKFLOW STATE section MUST reference the research file path (if Step 4 ran) and include a Brainstorming Summary block.

The plan file is the artifact Phase 1 will pick up and extend with HOW-level locks.

---

## STEP 8 — Hard Gate + Route

**MANDATORY before invoking `core-dev`. No exceptions.**

Display the gate summary in chat. Two parts: the canonical **6-line restate** (the kernel — keeps misalignment surfaced) AND the **detailed implementation outline** (plan-mode style — gives the user enough concrete detail to approve with confidence without opening the plan file). Both required. The plan file path is announced at the top so the user can open it for full detail.

### Restate (canonical 6 lines)

```
- Outcome:      <one line>
- User:         <one line — who benefits>
- Why now:      <one line — what changed>
- Success:      <one line — how we know it worked>
- Constraint:   <one line — the binding limit>
- Out of scope: <one line — what we're explicitly NOT doing>
```

*"Out of scope" is non-negotiable* — half of misalignment is silent disagreement about what is NOT being built.

### Implementation outline (plan-mode style)

Render the outline in chat as a structured markdown plan — closer to what Claude writes in plan mode than to the 6-line restate. Pull directly from the plan file you wrote in Step 7. The user should be able to approve with confidence from this alone, without opening the plan file; the file path is announced so they can open it for full detail.

Template (fill every section; omit a section ONLY if it's genuinely empty, never omit silently):

```markdown
**Plan file:** `docs/plans/{NNNN}__YYYY-MM-DD__implementation_plan__{SLUG}.md`

#### Recommended approach: [name]

[2-4 sentences explaining WHY this approach over the alternatives. Reference each alternative by name and the trade-off that pushed the decision. Anchor in the codebase scan + research findings.]

#### Alternatives considered (rejected)

- **[Alternative A name]** — [1 sentence on what it was] · Rejected because: [1 sentence on the dealbreaker].
- **[Alternative B name]** — [...]. Rejected because: [...].

#### Files to modify

- `path/to/file.ext` — [what changes, 1-2 lines; name the function / section / behavior changed]
- `path/to/another.ext` — [...]
- *(New)* `path/to/new-file.ext` — [purpose]
- *(Delete)* `path/to/obsolete.ext` — [why obsolete]

#### Implementation tasks (vertical slices)

Each task leaves the project in a working state. Order matters — earlier tasks lay groundwork for later ones; flag any ordering constraint explicitly.

1. **[Task 1 name]** — [1 sentence describing the task]
   - Files: `path/...`, `path/...`
   - Verification: `<command>` (or `<assertion>` if not command-driven)
   - Risk: [one line or `none`]
2. **[Task 2 name]** — [...]
   - Files: `path/...`
   - Verification: `<command>`
   - Risk: [...]
3. ...

#### Verification strategy

[2-3 sentences. What evidence proves it works end-to-end? Tests / lint / manual smoke? Coverage target if applicable? Regression baseline if applicable? Each task's local verification ladders up to this overall strategy.]

#### Key risks (highest-leverage)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| [risk] | CRITICAL/HIGH/MEDIUM | [mitigation, one line] |
| [risk] | ... | [...] |
| [risk] | ... | [...] |

#### Out of scope (explicit)

- [item NOT being built or changed in this task]
- [item]
- [item]

#### Open questions (if any)

- [unknown that may surface during implementation] — [how it will be resolved if it surfaces]
- *(or `none`)*
```

**Anti-pattern guard.** Do not dump the full plan body into chat. If the outline naturally exceeds 60 lines of markdown, condense by:
1. Show the first 5-7 tasks + a final line `...N more tasks in the plan file`.
2. Show top 3 risks only.
3. Keep Approach / Verification strategy / Out of scope at full detail (load-bearing).

Never truncate silently. Never replace any of {Approach, Files, Tasks, Verification, Risks, Out of scope} with a hand-wave — those are the load-bearing fields. *"...details in the plan file"* is acceptable as an explicit terminator on a section that ran long, never as a substitute for a section the user hasn't seen.

### Gate

Then ask via `AskUserQuestion`: *"Approve the design and proceed to implementation?"* — options: `"Approve and proceed (Recommended)"`, `"Modify"`.

**Non-yes detection (especially Codex fallback):** these are NOT yes:

- *"Sounds good"* → ambiguous. Ask: *"Anything you'd refine?"*
- *"Whatever you think"* → delegation, not decision. Re-present options.
- *"Sure, let's go"* → polite exit. Ask: *"Approve, or skip this?"*
- Silence then *"okay let's start"* → gave up, not converged. Reframe.

**Spirit beats letter** (Process Rule D). A skipped gate, a hedged confirmation, an inferred "yes" — each violates it.

If user picks `"Modify"`: ask what, edit the plan file, re-restate, re-gate.

On approval, append to the plan file:

```markdown
## Approach Decision

**Selected:** [name]
**User modifications:** [None / changes]
**Confirmed:** [YYYY-MM-DD]
```

Announce: *"Approach confirmed: [name]. Routing to core-dev."*

Invoke `development-skills:core-dev` via the Skill tool, no arguments. `core-dev`'s Step 1 detects `Status: In Progress` and proceeds without re-triggering brainstorming.
