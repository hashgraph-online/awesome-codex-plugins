---
title: Real Screenshots
impact: HIGH
tags: comparison, tokens, screenshots, mockups, validation
---

**Rule**: Compare visual options on the real product. Change the tokens temporarily, capture the real screens, decide, then restore. Never judge a palette or type change from an invented mockup alone.

**Evidence**: A palette that looks right on a sample swatch often fails next to real content: long names, busy data, photos, maps, system UI, and dark mode. Designers have long tested colours in context for this reason (Albers, *Interaction of Color*, 1963: the same colour reads differently against different neighbours).

### When Building

- **Option A versus option B means two builds of the same screens.** Change only the token values (colour, font, radius) and capture each option with the same data.
- **Capture the hard cases**: the busiest screen, the longest strings, system content the app cannot restyle (maps, photos, keyboards, share sheets), and both light and dark mode.
- **Use the platform's tools to capture**: the iOS Simulator or Xcode Previews, an Android emulator or Compose previews, a browser at phone and desktop widths, or Storybook.
- **Restore the tokens afterwards** unless the user picked that option. Never leave a trial palette in the code.
- **Label anything drawn by hand as a sketch.** HTML or canvas mockups are fine for structure (layout, new screens), but say so. People mistake polished mockups for screenshots, then are surprised by the real build.
- **Coordinate shared tools.** Simulators and devices may be used by other sessions or people, so check before taking one over.

### When Auditing

- A palette or font chosen from a moodboard or swatch, never shown on real screens
- Mockups presented as if they were the built app
- Trial token values left behind in the code
- Dark mode never captured
- Screens checked only with placeholder data

### Incorrect

```text
Proposed new accent: orange (see swatch). Approve to apply.
```

### Correct

```text
Captured Home, Detail and Settings in light and dark with an orange
accent (A) and a blue accent (B), using the busiest test data.
A collides with the orange "overdue" status on Detail; B does not.
Tokens restored to current values.
```

### Why This Matters

Swatches and mockups hide the interactions that make a palette fail: a selected state that looks like an error, an accent that disappears on a photo, a font that wraps a long name. Real captures catch these before anyone has committed to a direction.

### Alternatives

For a brand-new product with no code yet, mockups are the only option. Build the first screen in code as soon as the direction is chosen, and check against that. For quick single-colour tweaks inside an established system, a live preview (Xcode Previews, Compose previews, a hot-reloading browser) counts as a real capture.
