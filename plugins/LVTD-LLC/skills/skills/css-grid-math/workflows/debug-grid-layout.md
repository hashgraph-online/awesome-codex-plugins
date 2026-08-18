# Debug Grid Layout Workflow

Step-by-step process for applying css grid math to front-end code.

## When to Use

- A layout, color, or UI value needs a formula instead of a magic number.
- A computed browser value differs from the expected design value.
- You need to explain or review the math behind a UI decision.

## Prerequisites

- Know the target browser/UI state.
- Have the relevant CSS, JavaScript, or design token values.

**Reference**: `../references/grid-layout/rules.md`

## Workflow Steps

### Step 1: Name the Unknown

**Goal**: Make the calculation explicit.

- [ ] State the exact value being solved.
- [ ] List known inputs and units.
- [ ] Identify the source of each input.

**Reference**: `../references/grid-layout/knowledge.md`

### Step 2: Pick the Formula Pattern

**Goal**: Choose the smallest math model that explains the behavior.

- [ ] Check whether a pattern in `../references/grid-layout/patterns.md` matches.
- [ ] Prefer a bounded formula over a magic number.
- [ ] Decide whether CSS or JavaScript owns the calculation.

**Reference**: `../references/grid-layout/patterns.md`

### Step 3: Apply the Rules

**Goal**: Convert the formula into maintainable code.

- [ ] Follow the relevant rules in `../references/grid-layout/rules.md`.
- [ ] Use named tokens, variables, or intermediate values.
- [ ] Keep units valid and readable.

### Step 4: Verify Extremes

**Goal**: Catch boundary failures.

- [ ] Count grid lines, not just visible cells.
- [ ] Subtract gap space from the container before solving track sizes.
- [ ] Check whether content minimums are constraining flexible tracks.
- [ ] Decide whether empty auto-repeat tracks should collapse.

## Common Mistakes

| Mistake | Why It's Bad | Do Instead |
|---------|--------------|------------|
| fr columns are not equal | It hides the real calculation problem. | Check fixed tracks, gaps, min-content constraints, and max constraints. |
| Item is one column off | It hides the real calculation problem. | Recount grid lines and inspect start/end line values. |
| auto-fill leaves empty columns | It hides the real calculation problem. | Use auto-fit if empty tracks should collapse. |

## Exit Criteria

Task is complete when:

- [ ] The formula is explainable from named inputs.
- [ ] The implementation works at boundary and representative states.
- [ ] Any CSS/JavaScript ownership boundary is documented in code or tokens.
