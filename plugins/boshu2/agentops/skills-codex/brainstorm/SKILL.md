---
name: brainstorm
description: "Run brainstorm."
---
# $brainstorm — Clarify Goals Before Planning

> **Purpose:** Separate WHAT from HOW. Explore the problem space before committing to a solution.

## Two modes

`$brainstorm` runs in one of two modes (complementary, not exclusive):

| Mode | Use when | Shape |
|------|----------|-------|
| **Goal-clarification** (default; the four phases below) | The goal names ONE specific capability (`"add JWT auth"`, `"fix the login bug"`) | Sharpen the WHAT, explore the HOW for that single goal. |
| **Ideation** (open-ended; see below) | The goal is open-ended (`"improve the project"`, `"what should we build next"`) OR Phase 1 returns `exploring` with no single goal OR `--ideate` is passed | Generate MANY candidate improvements, winnow ruthlessly, operationalize the survivors. |

Four phases (goal-clarification mode):
1. **Assess clarity** — Is the goal specific enough?
2. **Understand idea** — What problem, who benefits, what exists?
3. **Explore approaches** — Generate options, compare tradeoffs
4. **Capture design** — Write structured output for `$plan`

---

## Quick Start

```bash
$brainstorm "add user authentication"     # full 4-phase process
$brainstorm                                # prompts for goal
```

---

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), ensure startup context
before ideation:

```bash
ao codex ensure-start 2>/dev/null || true
```

`ao codex ensure-start` is the single startup guard for Codex skills. It records
startup once per thread and skips duplicate startup automatically. Leave
`ao codex ensure-stop` to closeout skills; `$brainstorm` is a start-path skill.

---

## Execution Steps

### Phase 1: Assess Clarity

If the user provided a goal string, evaluate it. Otherwise prompt for one.

Ask the user with options to gauge clarity:

- **clear** — Goal is specific and actionable (e.g., "add JWT auth to the API")
- **vague** — Goal exists but needs narrowing (e.g., "improve security")
- **exploring** — No firm goal yet, just a direction (e.g., "something with auth")

If **vague** or **exploring**, ask follow-up questions to sharpen the goal before proceeding. Do NOT move to Phase 2 until you have a concrete problem statement (one sentence, testable).

### Phase 2: Understand the Idea

Answer these questions (use codebase exploration as needed):

1. **What problem does this solve?** — State the pain point in concrete terms.
2. **Who benefits?** — End users, developers, operators, CI pipeline?
3. **What exists today?** — Current state, prior art in the codebase, adjacent systems.
4. **What constraints matter?** — Performance, compatibility, security, timeline.

Summarize findings before moving on. If anything is unclear, ask the user.

### Phase 3: Explore Approaches

Generate **2-3 distinct approaches**. For each:

- **Name** — Short label (e.g., "JWT middleware", "OAuth proxy", "Session cookies")
- **How it works** — 2-3 sentences
- **Pros** — What it gets right
- **Cons** — What it gets wrong or defers
- **Effort** — Rough scope (small / medium / large)

#### Phase 3b: Adversarial Critique

Before asking the user to choose, stress-test each approach:

For each approach, answer these **red team questions** (read `references/red-team-checklist.md`):

1. **What breaks first?** — Under load, edge cases, or adversarial input
2. **What's the hidden cost?** — Maintenance burden, technical debt, learning curve
3. **What assumption is wrong?** — The unstated belief that makes this approach seem good
4. **Who disagrees?** — What would a senior engineer with the opposite preference say?

Mark any approach that fails 2+ red team questions as **HIGH RISK** in the comparison.

If all approaches fail 2+ questions, generate a 4th "hybrid" approach addressing the weaknesses.

Present the comparison and ask the user to pick an approach or request a hybrid.

### Phase 4: Capture Design

Generate a date slug: `YYYY-MM-DD-<goal-slug>` (lowercase, hyphens, no spaces).

Write the output file to `.agents/brainstorm/YYYY-MM-DD-<slug>.md`:

```markdown
---
id: brainstorm-YYYY-MM-DD-<goal-slug>
type: brainstorm
date: YYYY-MM-DD
---
# Brainstorm: <Goal>
## Problem Statement
## Approaches Considered
## Selected Approach
## Open Questions
## Next Step: $plan
```

All five sections must be populated. The "Next Step" section should contain a concrete `$plan` invocation suggestion with the selected approach as context.

Create the `.agents/brainstorm/` directory if it does not exist.

---

## Ideation Mode (open-ended generate-winnow)

> **Additive to the four-phase flow above — it does not replace it.** Ideation mode is for "improve the project"-style goals where the WHAT is unknown and you must generate a portfolio and select, rather than clarify ONE known goal.

**Trigger:** the `exploring` clarity path (Phase 1) when no single goal emerges, OR an explicit `--ideate` flag, OR an open-ended goal string.

The methodology is **generate → winnow → expand → operationalize → refine**. Steps 1-3 belong to `$brainstorm`; steps 4-5 are handed to `$discovery` on its open-ended path.

### Step 1 — Ground in reality

```bash
cat AGENTS.md                      # or CLAUDE.md — rules, constraints, non-goals
bd list --json                     # open work — don't duplicate
bd list --status closed --json     # closed work — don't re-propose cut ideas
bd ready --json                    # what is actionable now
```

### Step 2 — Generate 30, winnow to 5 (ranked, with rationale)

Generate **30** candidate improvements (criteria = the rubric dimensions: robust, reliable, performant, intuitive, user-friendly, ergonomic, useful, compelling, while staying obviously **accretive** and **pragmatic**). Think each one through: **how it works**, **how users perceive it**, **how we implement it**. Then **winnow ruthlessly to the VERY best 5**, presented **ranked best-to-worst** with full rationale and rubric scores. Stress-test survivors with the red team questions (Phase 3b). Do NOT stop at the first 5 — generate the full 30 first.

### Step 3 — Expand with the next 10 (→ 15)

Generate the **next best 10** (each with rationale) for a ranked portfolio of **15** — #6-15 are often complementary to the top 5.

### Steps 4-5 — Operationalize + refine (handed to `$discovery`)

Carry the ranked 15 (with how/perceive/implement notes + rubric scores + red-team findings) forward. `$discovery` operationalizes them into self-documenting `bd` beads (deps + explicit test tasks) and refines 4-5x in plan space.

### Output

Standalone (`$brainstorm --ideate`): write the ranked portfolio to `.agents/brainstorm/YYYY-MM-DD-<slug>-ideation.md`. Invoked by `$discovery`: return the ranked portfolio inline for the operationalize step.

> **Tracking is `bd`, never `br`/`bv`** — this is AgentOps.

---

## Termination

Phase 4 output written = done. No further phases, no loops.

## Validation

After writing the output file, verify:
1. File exists at the expected path
2. All 5 sections (`Problem Statement`, `Approaches Considered`, `Selected Approach`, `Open Questions`, `Next Step: $plan`) are present and non-empty

Report the file path to the user.

---

## Examples

**Example 1: Specific goal**
```
User: $brainstorm "add rate limiting to the API"

Phase 1: Goal is clear — add rate limiting to the API.
Phase 2: Problem is uncontrolled request volume causing timeouts.
         Benefits operators and end users. No rate limiting exists today.
Phase 3: Three approaches — token bucket middleware, API gateway,
         per-route decorators. User picks token bucket.
Phase 4: Writes .agents/brainstorm/2026-02-17-rate-limiting.md
```

**Example 2: Vague goal**
```
User: $brainstorm "improve performance"

Phase 1: Goal is vague. Asks: "Which part? API response times,
         build speed, database queries, or something else?"
         User says: "API response times on the search endpoint."
Phase 2: Investigates search endpoint, finds N+1 queries.
Phase 3: Approaches — query optimization, caching layer, pagination.
Phase 4: Writes .agents/brainstorm/2026-02-17-search-performance.md
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Brainstorm loops in Phase 1 without advancing | Goal remains too vague after follow-up questions | Provide a concrete, testable problem statement (e.g., "reduce API search latency below 200ms" instead of "improve performance"). |
| Output file missing one or more required sections | Phase 4 was interrupted or the skill terminated early | Re-run `$brainstorm` with the same goal; verify all 5 sections (`Problem Statement`, `Approaches Considered`, `Selected Approach`, `Open Questions`, `Next Step: $plan`) are present in the output. |
| `.agents/brainstorm/` directory not created | The skill could not create the directory (permissions or path issue) | Manually create it with `mkdir -p .agents/brainstorm` and re-run. |
| `$plan` invocation in "Next Step" section is generic or incomplete | The selected approach was not specific enough to generate a concrete plan command | Edit the output file to refine the selected approach, then craft a `$plan` invocation that includes the approach name and key constraints. |
| Brainstorm produces only one approach in Phase 3 | The problem space is narrow or the goal is overly constrained | Widen the goal slightly or explicitly ask for alternative approaches (e.g., "consider a caching approach and a query optimization approach"). |

---

## See Also

- [../plan/SKILL.md](../plan/SKILL.md) — Decompose the selected approach into actionable issues

## Reference Documents

- [references/red-team-checklist.md](references/red-team-checklist.md) — Adversarial critique template for Phase 3b

## Local Resources

### scripts/

- `scripts/validate.sh`
