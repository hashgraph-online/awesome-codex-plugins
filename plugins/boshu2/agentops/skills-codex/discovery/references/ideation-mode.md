# Ideation Mode — Generate-Winnow Methodology

> Open-ended idea generation for "improve the project"-style goals.
> Distinct from the four-phase goal-clarification flow, which sharpens ONE
> specific goal. Ideation mode generates MANY candidate improvements, winnows
> ruthlessly, and operationalizes the survivors.

## When to use which mode

| Signal | Mode | Why |
|--------|------|-----|
| Goal names ONE specific capability ("add JWT auth", "fix the login bug") | Goal-clarification (Phases 1-4) | The WHAT is known; explore HOW. |
| Goal is open-ended ("improve the project", "what should we build next", "make X more robust") | **Ideation mode** | The WHAT is unknown; generate a portfolio and select. |
| `--ideate` flag is passed | **Ideation mode** | Explicit operator override. |
| Phase 1 clarity assessment returns `exploring` AND no single goal emerges after follow-up | **Ideation mode** | The user has a direction, not a target. |

The two modes share the same evaluation rubric (`idea-rubric.md`) and the same
adversarial discipline (`red-team-checklist.md`). Ideation mode is **additive**:
it does not replace the goal-clarification flow. A session may start in ideation
mode, select one idea, and hand that single idea to the goal-clarification flow
for HOW-exploration.

## The methodology: generate → winnow → expand → operationalize → refine

Five steps, each with an explicit artifact. The discipline is "generate many,
keep few, document everything."

### Step 1 — Ground in reality (research context)

Before generating, read the project's current state so ideas align with reality
and don't duplicate existing work.

```bash
cat AGENTS.md                # or CLAUDE.md — project rules + constraints
ao beads exec list --json              # open work — avoid duplicating
ao beads exec list --status closed --json   # closed work — lessons learned, don't re-propose
ao beads exec ready --json             # what is actionable right now
```

Checklist before generating:

- [ ] Read AGENTS.md / CLAUDE.md completely (constraints, non-goals, conventions)
- [ ] Reviewed open beads (don't propose what's already tracked)
- [ ] Reviewed closed beads (don't re-propose what was tried and cut)
- [ ] Understand the current architecture and where the project is headed

### Step 2 — Generate 30, winnow to 5 (ranked, with rationale)

Generate **30** candidate ideas for improving the project. The criteria are the
rubric dimensions: more robust, reliable, performant, intuitive, user-friendly,
ergonomic, useful, compelling — while staying **obviously accretive and
pragmatic**.

For each of the 30, think it through carefully:

1. **How it would work** — the mechanism, concretely.
2. **How users would perceive it** — first impression, learning curve, delight.
3. **How we would implement it** — rough approach, surfaces touched, scope.

Then **winnow ruthlessly to the VERY best 5**. Apply the winnowing rounds in
`idea-rubric.md` (hard cuts → threshold → weighted ranking → synergy).

Present the 5 **ranked best-to-worst**, each with full, detailed rationale: how
and why it makes the project obviously better, and why you are confident in that
assessment. Score each survivor against the rubric (see `idea-rubric.md`).

> The 30→5 funnel is the core discipline. Generating many before filtering
> prevents premature commitment to a mediocre first idea; the ruthless cut
> forces quality. Do NOT stop at the first 5 you think of — generate the full 30.

### Step 3 — Expand with the next 10 (→ 15 total)

The #6-15 ideas frequently have unique strengths that complement the top 5.
Generate the **next best 10**, each with its rationale, for a ranked portfolio
of **15**. Together the 15 form a more complete improvement package than the top
5 alone.

### Step 4 — Operationalize into self-documenting beads

This step belongs to `/discovery` on the open-ended path (see
`bead-operationalization.md`), but ideation mode produces its input: a ranked,
rationale-bearing list of 15 ideas with how/perceive/implement notes and rubric
scores. Hand that forward — do not lose the rationale.

### Step 5 — Refine in plan space (4-5 passes)

Also a `/discovery` responsibility (see `bead-operationalization.md`): re-read
AGENTS.md each pass, check every bead for sense and optimality, and resist
oversimplification. "It's a lot easier and faster to operate in plan space
before we start implementing."

## Output of ideation mode

When run standalone (`brainstorm --ideate`), ideation mode writes its portfolio
to `.agentsbrainstorm/YYYY-MM-DD-<slug>-ideation.md` with:

```markdown
---
id: brainstorm-YYYY-MM-DD-<slug>-ideation
type: brainstorm-ideation
date: YYYY-MM-DD
---
# Ideation: <Open-Ended Goal>
## Grounding (AGENTS.md + open/closed beads reviewed)
## Top 5 (ranked best-to-worst, with rationale + rubric scores)
## Next 10 (ranked, with rationale) — portfolio of 15
## Synergies and dependencies
## Next Step: /discovery --ideate (operationalize into beads)
```

When invoked BY `/discovery` on the open-ended path, ideation mode returns the
ranked portfolio inline for the operationalize step rather than writing a
standalone file.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Skip grounding | Read AGENTS.md + beads first — prevents duplicates |
| Generate 5 and stop | Generate the full 30, then winnow |
| Keep all 30 | Winnow ruthlessly to 5; quality over quantity |
| Stop at 5 | Expand to 15 — #6-15 are often complementary |
| Present unranked | Rank best-to-worst with full rationale |
| Drop rationale on handoff | Carry how/perceive/implement + rubric scores into operationalize |
| Use `bd`/Dolt | This is AgentOps — use `br` for tracking and `bv` for graph triage |
