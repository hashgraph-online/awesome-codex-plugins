---
name: perception-router
description: 'Use this skill whenever a design task involves visual perception, layout, hierarchy, grouping, scanning order, attention, color organization, or composition — regardless of framework, design system, or platform. Trigger when the user is laying out a screen, page, slide, poster, dashboard, mobile view, or print piece; choosing what to emphasize; deciding how things should group; picking type sizes, spacing, or color roles; reviewing why something "looks busy" or "feels empty"; or asking "where should the eye land first." Routes the model to the right perception principle in this plugin and surfaces the most-decisive ones for the surface in question. Framework-agnostic: applies to web, mobile, print, physical product, slide design, and information graphics alike.'
---

# Perception & hierarchy — router

This plugin holds the principles that govern how the eye organizes a composition: what gets seen first, what groups with what, what reads as noise, what reads as quality. They are framework-agnostic; the same principle applies to a shadcn/ui card, a Material chip, a Figma slide, a poster, or a printed report.

## How to route

Read the task and identify the principles that decide it. Most non-trivial perception tasks are dominated by 3–6 principles. Read those principles' skills in full; treat the rest as background.

## Principles in this plugin

The list below is the full inventory of perception-related principles from *Universal Principles of Design* covered by this plugin. Each principle has its own skill (and where useful, sub-aspect skills) under `skills/`. Principles marked **[full]** have reference-grade skill files; the others are planned and will be added in subsequent passes.

### Visual hierarchy and emphasis

- **`hierarchy`** *[full]* — the ranking of importance among visible elements; size, weight, color, position.
  - Sub-skills: `hierarchy-typographic`, `hierarchy-spatial`, `hierarchy-color-and-tone`.
- **`alignment`** — elements share an invisible axis; misalignment reads as disorder.
- **`area-alignment`** — alignment by visual mass rather than bounding box.
- **`signal-to-noise-ratio`** *[full]* — the ratio of meaningful information to decoration.
  - Sub-skills: `snr-densification`, `snr-decoration-removal`, `snr-emphasis-economy`.
- **`highlighting`** — emphasis works only when sparing.
- **`von-restorff-effect`** — the item that differs is remembered and noticed first.
- **`red-effect`** — red attracts disproportionate attention; reserve for genuine urgency.
- **`horror-vacui`** — the impulse to fill empty space; whitespace is a feature.
- **`layering`** — distinct visual planes (z, elevation) reduce noise.
- **`gutenberg-diagram`** — Z-pattern reading on uniform layouts.

### Gestalt grouping

- **`proximity`** *[full]* — nearby items are perceived as a group.
  - Sub-skills: `proximity-form-fields`, `proximity-data-tables`, `proximity-navigation`.
- **`similarity`** — items that look alike are perceived as related.
- **`closure`** — the eye completes incomplete shapes.
- **`common-fate`** — elements moving together are perceived as related.
- **`figure-ground-relationship`** — every composition has a focused figure and a recessive ground.
- **`good-continuation`** — aligned edges read as connected.
- **`uniform-connectedness`** — a shared region binds elements more strongly than proximity alone.
- **`law-of-pragnanz`** — the eye prefers the simplest valid interpretation.
- **`contour-bias`** — sharp angles feel hostile; rounded corners feel friendly.

### Proportion, rhythm, and depth

- **`golden-ratio`** — 1:1.618; useful as a starting proportion for hero compositions.
- **`fibonacci-sequence`** — successive Fibonacci ratios produce natural-feeling spacing scales.
- **`rule-of-thirds`** — split a composition into thirds; place focal points on intersections.
- **`symmetry`** — bilateral, radial, or translational; stable but can feel static.
- **`self-similarity`** — fractal repetition at multiple scales creates coherence.
- **`cathedral-effect`** — high "ceilings" (whitespace) invite expansive thinking; low ones invite focus.
- **`three-dimensional-projection`** — subtle depth cues (shadow, scale) clarify layering.

### Typography and color

- **`legibility`** — character distinctness; a property of typeface and rendering.
- **`readability`** — sustained reading speed; a property of layout (length, leading, contrast).
- **`color`** — hue, saturation, value; cultural meaning; accessibility.
- **`gloss-bias`** — glossy surfaces read as desirable.
- **`top-down-lighting-bias`** — humans assume light from above; shadows below = raised, shadows above = recessed.

### Attention quirks

- **`inattentional-blindness`** — focused users don't see unexpected elements.
- **`threat-detection`** — sharp angles, snake-like shapes, angry faces detected fast.
- **`orientation-sensitivity`** — vertical and horizontal lines processed faster than oblique.

## Heuristic for which to read first

- **Designing a page or screen layout** → `hierarchy`, `alignment`, `proximity`, `signal-to-noise-ratio`.
- **Reviewing a "busy" or "noisy" UI** → `signal-to-noise-ratio`, `highlighting`, `horror-vacui`.
- **Form layout** → `proximity`, `alignment`, `good-continuation`, `gutenberg-diagram`.
- **Data table or dashboard** → `hierarchy`, `signal-to-noise-ratio`, `legibility`, `gestalt similarity`.
- **Marketing / hero surface** → `hierarchy`, `golden-ratio` or `rule-of-thirds`, `gloss-bias`, `cathedral-effect`.
- **Empty / loading / error states** → `hierarchy`, `horror-vacui`, `figure-ground-relationship`.
- **Brand / visual-identity decisions** → `contour-bias`, `color`, `symmetry`, `self-similarity`.
- **Choosing color tokens** → `color`, `red-effect`, `top-down-lighting-bias`, plus accessibility checks (see `process-and-robustness-principles`).

## Working method

1. **Name the surface** in concrete terms: "B2B SaaS settings page with three sections," not "settings page."
2. **Pick 3–6 decisive principles** from the list above. Most surfaces are dominated by Hierarchy, Proximity, Alignment, and Signal-to-Noise.
3. **Read those skills.** Each principle skill includes a definition, when-to-apply guidance, anti-patterns, and worked examples.
4. **Make the decision and name the trade-off.** Most principles trade against another.

## Cross-plugin pointers

- For *learnability* (mental models, complexity, defaults, recognition), see `cognition-and-learnability-principles`.
- For *behavior* (affordance, feedback, errors, control), see `interaction-and-control-principles`.
- For *brand and tone*, see `aesthetics-and-emotion-principles`.
- For *accessibility and edge cases*, see `process-and-robustness-principles`.
