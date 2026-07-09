# Design Fluid Layout Workflow

Step-by-step process for applying responsive layout math to front-end code.

## When to Use

- A layout, color, or UI value needs a formula instead of a magic number.
- A computed browser value differs from the expected design value.
- You need to explain or review the math behind a UI decision.

## Prerequisites

- Know the target browser/UI state.
- Have the relevant CSS, JavaScript, or design token values.

**Reference**: `../references/fluid-layouts/rules.md`

## Workflow Steps

### Step 1: Name the Unknown

**Goal**: Make the calculation explicit.

- [ ] State the exact value being solved.
- [ ] List known inputs and units.
- [ ] Identify the source of each input.

**Reference**: `../references/fluid-layouts/knowledge.md`

### Step 2: Pick the Formula Pattern

**Goal**: Choose the smallest math model that explains the behavior.

- [ ] Check whether a pattern in `../references/fluid-layouts/patterns.md` matches.
- [ ] Prefer a bounded formula over a magic number.
- [ ] Decide whether CSS or JavaScript owns the calculation.

**Reference**: `../references/fluid-layouts/patterns.md`

### Step 3: Apply the Rules

**Goal**: Convert the formula into maintainable code.

- [ ] Follow the relevant rules in `../references/fluid-layouts/rules.md`.
- [ ] Use named tokens, variables, or intermediate values.
- [ ] Keep units valid and readable.

### Step 4: Verify Extremes

**Goal**: Catch boundary failures.

- [ ] Identify the parent box for every percentage.
- [ ] Define minimum and maximum acceptable sizes before writing clamp().
- [ ] Use structural breakpoints only where the layout actually changes.
- [ ] Check classic and modern viewport units for mobile full-height regions.

## Common Mistakes

| Mistake | Why It's Bad | Do Instead |
|---------|--------------|------------|
| Layout jumps too abruptly | It hides the real calculation problem. | Use clamp() or proportional sizing before adding more breakpoints. |
| 100vh section cuts off on mobile | It hides the real calculation problem. | Evaluate svh, lvh, dvh, or min-height instead. |
| Nested columns are unexpectedly narrow | It hides the real calculation problem. | Trace percentage calculations through parent boxes. |

## Exit Criteria

Task is complete when:

- [ ] The formula is explainable from named inputs.
- [ ] The implementation works at boundary and representative states.
- [ ] Any CSS/JavaScript ownership boundary is documented in code or tokens.
