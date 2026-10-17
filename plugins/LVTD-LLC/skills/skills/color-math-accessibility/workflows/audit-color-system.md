# Audit Color System Workflow

Step-by-step process for applying color math accessibility to front-end code.

## When to Use

- A layout, color, or UI value needs a formula instead of a magic number.
- A computed browser value differs from the expected design value.
- You need to explain or review the math behind a UI decision.

## Prerequisites

- Know the target browser/UI state.
- Have the relevant CSS, JavaScript, or design token values.

**Reference**: `../references/color-systems/rules.md`

## Workflow Steps

### Step 1: Name the Unknown

**Goal**: Make the calculation explicit.

- [ ] State the exact value being solved.
- [ ] List known inputs and units.
- [ ] Identify the source of each input.

**Reference**: `../references/color-systems/knowledge.md`

### Step 2: Pick the Formula Pattern

**Goal**: Choose the smallest math model that explains the behavior.

- [ ] Check whether a pattern in `../references/color-systems/patterns.md` matches.
- [ ] Prefer a bounded formula over a magic number.
- [ ] Decide whether CSS or JavaScript owns the calculation.

**Reference**: `../references/color-systems/patterns.md`

### Step 3: Apply the Rules

**Goal**: Convert the formula into maintainable code.

- [ ] Follow the relevant rules in `../references/color-systems/rules.md`.
- [ ] Use named tokens, variables, or intermediate values.
- [ ] Keep units valid and readable.

### Step 4: Verify Extremes

**Goal**: Catch boundary failures.

- [ ] List semantic color roles before picking values.
- [ ] Calculate contrast for text, icons, borders, and disabled states.
- [ ] Validate hover, focus, selected, and error states.
- [ ] Check light and dark mode independently.

## Common Mistakes

| Mistake | Why It's Bad | Do Instead |
|---------|--------------|------------|
| Palette looks balanced but text fails contrast | It hides the real calculation problem. | Run luminance and contrast calculations, not hue harmony checks. |
| Dark mode feels muddy | It hides the real calculation problem. | Adjust perceptual lightness and chroma rather than inverting RGB. |
| Overlay text changes by page section | It hides the real calculation problem. | Composite foreground colors against each actual background. |

## Exit Criteria

Task is complete when:

- [ ] The formula is explainable from named inputs.
- [ ] The implementation works at boundary and representative states.
- [ ] Any CSS/JavaScript ownership boundary is documented in code or tokens.
