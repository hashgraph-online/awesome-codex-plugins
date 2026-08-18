# Debug Flex Distribution Workflow

Step-by-step process for applying flexbox math to front-end code.

## When to Use

- A layout, color, or UI value needs a formula instead of a magic number.
- A computed browser value differs from the expected design value.
- You need to explain or review the math behind a UI decision.

## Prerequisites

- Know the target browser/UI state.
- Have the relevant CSS, JavaScript, or design token values.

**Reference**: `../references/flex-distribution/rules.md`

## Workflow Steps

### Step 1: Name the Unknown

**Goal**: Make the calculation explicit.

- [ ] State the exact value being solved.
- [ ] List known inputs and units.
- [ ] Identify the source of each input.

**Reference**: `../references/flex-distribution/knowledge.md`

### Step 2: Pick the Formula Pattern

**Goal**: Choose the smallest math model that explains the behavior.

- [ ] Check whether a pattern in `../references/flex-distribution/patterns.md` matches.
- [ ] Prefer a bounded formula over a magic number.
- [ ] Decide whether CSS or JavaScript owns the calculation.

**Reference**: `../references/flex-distribution/patterns.md`

### Step 3: Apply the Rules

**Goal**: Convert the formula into maintainable code.

- [ ] Follow the relevant rules in `../references/flex-distribution/rules.md`.
- [ ] Use named tokens, variables, or intermediate values.
- [ ] Keep units valid and readable.

### Step 4: Verify Extremes

**Goal**: Catch boundary failures.

- [ ] Identify the main axis.
- [ ] Record each item flex-basis and gap.
- [ ] Determine whether free space is positive or negative.
- [ ] Apply grow or shrink distribution.

## Common Mistakes

| Mistake | Why It's Bad | Do Instead |
|---------|--------------|------------|
| Equal flex values produce unequal widths | It hides the real calculation problem. | Check flex-basis and intrinsic content. |
| Long text breaks the row | It hides the real calculation problem. | Add min-width: 0 and explicit overflow behavior. |
| One item stops shrinking | It hides the real calculation problem. | Check min-width, min-content, and frozen constraint behavior. |

## Exit Criteria

Task is complete when:

- [ ] The formula is explainable from named inputs.
- [ ] The implementation works at boundary and representative states.
- [ ] Any CSS/JavaScript ownership boundary is documented in code or tokens.
