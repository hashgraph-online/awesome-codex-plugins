# Debug CSS Calculation Workflow

Step-by-step process for applying css math units to front-end code.

## When to Use

- A layout, color, or UI value needs a formula instead of a magic number.
- A computed browser value differs from the expected design value.
- You need to explain or review the math behind a UI decision.

## Prerequisites

- Know the target browser/UI state.
- Have the relevant CSS, JavaScript, or design token values.

**Reference**: `../references/css-calculations/rules.md`

## Workflow Steps

### Step 1: Name the Unknown

**Goal**: Make the calculation explicit.

- [ ] State the exact value being solved.
- [ ] List known inputs and units.
- [ ] Identify the source of each input.

**Reference**: `../references/css-calculations/knowledge.md`

### Step 2: Pick the Formula Pattern

**Goal**: Choose the smallest math model that explains the behavior.

- [ ] Check whether a pattern in `../references/css-calculations/patterns.md` matches.
- [ ] Prefer a bounded formula over a magic number.
- [ ] Decide whether CSS or JavaScript owns the calculation.

**Reference**: `../references/css-calculations/patterns.md`

### Step 3: Apply the Rules

**Goal**: Convert the formula into maintainable code.

- [ ] Follow the relevant rules in `../references/css-calculations/rules.md`.
- [ ] Use named tokens, variables, or intermediate values.
- [ ] Keep units valid and readable.

### Step 4: Verify Extremes

**Goal**: Catch boundary failures.

- [ ] Identify whether each unit is absolute or relative.
- [ ] Find the parent/root/reference value for each relative unit.
- [ ] Resolve custom properties into the final expression.
- [ ] Check box-sizing before calculating final dimensions.

## Common Mistakes

| Mistake | Why It's Bad | Do Instead |
|---------|--------------|------------|
| Font sizes grow unexpectedly | It hides the real calculation problem. | Look for nested em multiplication. |
| Box is wider than declared width | It hides the real calculation problem. | Check content-box padding and border. |
| calc() is invalid | It hides the real calculation problem. | Check missing spaces around operators or incompatible units. |

## Exit Criteria

Task is complete when:

- [ ] The formula is explainable from named inputs.
- [ ] The implementation works at boundary and representative states.
- [ ] Any CSS/JavaScript ownership boundary is documented in code or tokens.
