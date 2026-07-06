# Operationalizing Ideas Into Self-Documenting Beads

> The fourth and fifth steps of the generate-winnow methodology
> (`ideation-mode.md`): turn a ranked portfolio of ideas into a comprehensive,
> granular, self-documenting set of `br` beads, then refine them 4-5x in "plan
> space" before any implementation begins.
>
> This is primarily a `/discovery` responsibility on the open-ended path, but it
> consumes ideation-mode output and uses the same `br`/`bv` discipline.
>
> **Tracking is `br` (beads).** This is AgentOps — use `br`/`bv`.

## Step 4 — Comprehensive bead creation

Take ALL of the ranked ideas (top 5 + next 10 = 15) and elaborate them into a
comprehensive, granular set of beads with tasks, subtasks, and a dependency
structure overlaid. The beads must be **self-documenting**: so detailed that the
original markdown plan never needs to be consulted again.

Each bead's description should answer, for our "future self":

1. **What** — What specifically needs to be done?
2. **Why** — Why it matters; how it serves the project's overarching goals.
3. **How** — Key implementation approach.
4. **Risks** — What could go wrong (carry the red-team findings forward).
5. **Success criteria** — How we know it's done.

Include relevant background, reasoning/justification, and considerations — the
goals, intentions, and thought process that produced the idea.

### Bead structure

```bash
br create "Epic: <Feature Name>" -p 1 -t epic --description "
## Background
[Why this feature matters; which ideation idea(s) it came from]

## Goals
- [Goal 1]
- [Goal 2]

## Non-Goals
- [What we are explicitly NOT doing]

## Considerations
[Technical constraints, user expectations, rubric scores, red-team findings]
"
```

### Subtask + dependency pattern

```bash
# Create the epic, then tasks under it
br create "Design <component> interface" -p 1 -t task --description "..."
br create "Implement <component> logic"  -p 2 -t task --description "..."
br create "Tests for <component>"         -p 2 -t task --description "..."

# Wire dependencies (child depends on parent)
br dep add <impl-id> <epic-id>      # impl depends on epic
br dep add <test-id> <impl-id>      # tests depend on implementation
```

### Explicit test tasks (mandatory, with detailed logging)

Every feature gets companion test beads — unit AND e2e — with detailed logging
so we can confirm everything works after implementation:

```bash
br create "Unit tests for <component>" -p 2 -t task --description "
## Coverage Requirements
- Core behavior
- Error handling for invalid input
- Edge cases (empty, unicode, concurrent)

## Logging
- Log inputs and outputs
- Log timing for performance tracking
"

br create "E2E tests for <component>" -p 2 -t task --description "
## Scenarios
- Happy path
- Error path
- Integration with existing surfaces

## Logging
- Full command and response capture
- Timing and resource usage
"
```

### Overlap check before creating

Compare against existing beads so ideas enhance rather than duplicate:

```bash
br list --json | jq '.issues[]?.title'
```

| Overlap type | Action |
|--------------|--------|
| Direct duplicate | Skip; reference the existing bead |
| Complementary | Merge into the existing bead |
| Conflicts | Note explicitly; flag an architectural decision in the bead body or handoff |

## Step 5 — Refine in plan space (4-5 passes)

It is far easier and faster to operate in **plan space** before implementing.
Run **4-5 refinement passes** over the bead set. Each pass:

1. **Re-read AGENTS.md / CLAUDE.md** so the project's rules are fresh (especially
   after any context compaction).
2. Check every bead carefully: Does it make sense? Is it optimal? Could anything
   change to make the system work better for users? Revise in place.
3. **DO NOT OVERSIMPLIFY.** Resist the urge to collapse complexity — complexity
   usually exists for a reason.
4. **DO NOT LOSE FEATURES OR FUNCTIONALITY.** Every capability in the portfolio
   must survive the refinement.
5. Ensure comprehensive unit tests AND e2e test scripts with detailed logging are
   part of the bead set.

Suggested per-pass focus:

| Pass | Focus |
|------|-------|
| 1 | Structural issues, missing tasks |
| 2 | Dependency sanity, cycle detection |
| 3 | Test coverage gaps |
| 4 | Comment quality, self-documentation completeness |
| 5 | Final optimization |

### Validation between passes

```bash
br dep cycles --json     # dependency cycles MUST be empty
br ready --json | jq 'length'   # confirm actionable work exists
br lint                  # hygiene: orphans, missing fields
```

> If `br` lacks a direct cycle-detection subcommand in your install, inspect the
> dependency graph with `br dep tree <id>` and `br blocked --json`. The
> invariant is the same: no cycles, every leaf actionable.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Single-pass beads | 4-5 passes — the first draft is never optimal |
| Beads that need the markdown plan | Self-documenting beads — what/why/how/risks/success |
| Omit tests | Explicit unit + e2e test beads with detailed logging |
| Oversimplify on refinement | Preserve complexity that exists for a reason |
| Lose features when refining | Every portfolio capability survives |
| `bd`/Dolt | `br`/`bv` — this is AgentOps |
