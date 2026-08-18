# Choose Math Approach Workflow

Step-by-step process for applying frontend math foundations to front-end code.

## When to Use

- A layout, color, or UI value needs a formula instead of a magic number.
- A computed browser value differs from the expected design value.
- You need to explain or review the math behind a UI decision.

## Prerequisites

- Know the target browser/UI state.
- Have the relevant CSS, JavaScript, or design token values.

**Reference**: `../references/math-foundations/rules.md`

## Workflow Steps

### Step 1: Name the Unknown

**Goal**: Make the calculation explicit.

- [ ] State the exact value being solved.
- [ ] List known inputs and units.
- [ ] Identify the source of each input.

**Reference**: `../references/math-foundations/knowledge.md`

### Step 2: Pick the Formula Pattern

**Goal**: Choose the smallest math model that explains the behavior.

- [ ] Check whether a pattern in `../references/math-foundations/patterns.md` matches.
- [ ] Prefer a bounded formula over a magic number.
- [ ] Decide whether CSS or JavaScript owns the calculation.

**Reference**: `../references/math-foundations/patterns.md`

### Step 3: Apply the Rules

**Goal**: Convert the formula into maintainable code.

- [ ] Follow the relevant rules in `../references/math-foundations/rules.md`.
- [ ] Use named tokens, variables, or intermediate values.
- [ ] Keep units valid and readable.

### Step 4: Verify Extremes

**Goal**: Catch boundary failures.

- [ ] Write down the value being solved.
- [ ] List inputs and units.
- [ ] Choose arithmetic, ratio, linear equation, inequality, geometry, or coordinates.
- [ ] Decide whether CSS or JavaScript owns the calculation.

## Common Mistakes

| Mistake | Why It's Bad | Do Instead |
|---------|--------------|------------|
| Formula works only for one viewport | It hides the real calculation problem. | Look for fixed values where ratios or linear equations belong. |
| CSS and JS duplicate the same calculation | It hides the real calculation problem. | Pick one owner and expose tokens or measured values across the boundary. |
| Layout math is hard to explain | It hides the real calculation problem. | Name intermediate values and preserve units. |

## Exit Criteria

Task is complete when:

- [ ] The formula is explainable from named inputs.
- [ ] The implementation works at boundary and representative states.
- [ ] Any CSS/JavaScript ownership boundary is documented in code or tokens.
