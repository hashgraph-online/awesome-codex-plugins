---
name: legibility-typeface-and-size
description: 'Apply typeface and size choices for legibility — picking the right typeface for the use case (display, body, code, UI) and sizing it appropriately for the rendering context. Use when designing a type system for a product, choosing a brand typeface, evaluating an existing typeface against rendering conditions, picking sizes for body, headings, captions, code, or UI elements. The two most fundamental legibility decisions; everything else (contrast, spacing) is layered on top.'
---

# Legibility — typeface and size

The two most fundamental legibility decisions: which typeface to use, and at what size. Everything else — contrast, spacing, weight, color — is calibrated against these choices. A typeface that's wrong for the use case can't be saved by any other adjustment; a size that's wrong for the rendering context produces text that no contrast or spacing tweak will fix.

## Choosing typefaces by use case

Different uses demand different typefaces. The major categories:

**Display typefaces** are designed for headlines, posters, and other large-size uses where the typeface is meant to make a visual statement. Often have high contrast between thick and thin strokes (Bodoni, Didot), unusual proportions (condensed, expanded), or expressive personality (script, modern serif). They look striking at large sizes and lose distinguishability at small sizes — many become unreadable below 18–24px.

Use display typefaces only at display sizes (typically 24px and up). Don't use them for body text, UI labels, or anything small.

**Body / text typefaces** are designed for sustained reading at body sizes (typically 14–18px on screens, 9–12pt in print). They have moderate stroke contrast, generous apertures, and proportions optimized for legibility in long-form prose. Examples: Garamond, Caslon, Georgia (serif); Helvetica, Inter, Source Sans (sans-serif).

Use body typefaces for body copy and most UI text.

**UI typefaces** are body typefaces with adjustments for screen UI use: even more generous spacing, slightly heavier weights, sometimes designed for specific rendering targets. Examples: SF Pro (Apple), Roboto (Google), Inter (open-source), Segoe UI (Microsoft).

UI typefaces and body typefaces overlap heavily. The distinction matters most when you're designing for a specific platform that has a strong native typeface.

**Monospace / code typefaces** have every character occupying the same width. Essential for code (column alignment) and useful for tabular data. The best ones (JetBrains Mono, Fira Code, Source Code Pro) have explicit attention to character disambiguation (0/O, 1/I/l).

Use monospace for code, terminal output, structured numeric data, and tabular layouts where alignment matters.

**Specialty typefaces** for specific functions: Atkinson Hyperlegible for accessibility-first contexts; Highway Gothic-style typefaces for distance signage; numbers-only typefaces optimized for spreadsheet display.

Most products need at most 2–3 typefaces: a body typeface for the bulk of text, a display typeface for headlines (sometimes the same as body, in heavier weight), and a monospace typeface for code if applicable.

## Sizing for the rendering context

The right size depends on:

**Viewing distance.** Closer viewing tolerates smaller text; further viewing requires larger. Mobile devices are held at ~25–35cm; desktop monitors at ~50–80cm; TVs at 2–3m; signage at variable distances.

**Display DPI.** Higher-DPI displays render small text more legibly because antialiasing has more pixels to work with. A 12px font that's legible on a Retina display may be illegible on a lower-DPI external monitor.

**Lighting and environment.** Bright sunlight, glare, low ambient light all reduce legibility. Outdoor and mobile contexts often need larger sizes than indoor desktop contexts.

**User population.** Older users, low-vision users, and users in unfamiliar languages need larger text. If your audience skews toward any of these, baseline sizes should scale up.

A practical baseline for modern UI:

- Body text: 14–16px
- Smaller UI text (helper, captions): 12–14px (don't go below 12 for primary content)
- Headings: scale based on hierarchy (24, 32, 48, 64+)
- Code: 13–15px for inline; 14–16px for blocks
- Hero text: 48–96px (or larger, depending on layout)

These are starting points. Specific products should test with their actual users in their actual conditions.

## A typographic scale

Most well-designed type systems use a scale rather than ad-hoc sizes. A typographic scale defines a small set of sizes (typically 5–8) related by a consistent ratio. Common ratios:

- **Major Second (1.125):** subtle progression, lots of size steps. Used for tight UI systems.
- **Minor Third (1.2):** moderate progression. The most common modern UI scale.
- **Major Third (1.25):** stronger progression, fewer steps. Used for products that emphasize hierarchy.
- **Perfect Fourth (1.333):** strong progression. Used for editorial or display-heavy designs.
- **Golden Ratio (1.618):** dramatic progression. Used for highly hierarchical layouts.

Pick a base size (often 16px) and a ratio. Each size in the scale is the previous one multiplied by the ratio (or divided, going down). The result is a small set of sizes that work harmoniously.

For example, with base 16px and Minor Third (1.2): 11, 13, 16, 19, 23, 28, 33, 40, 48 px. Round to nearest pixel for crisp rendering.

The scale should cover all your needs. If you find yourself wanting a size between two scale values, the right answer is usually to use one of the existing values (the constraint is helpful) rather than adding a new one.

## Choosing a system typeface

Some products use the platform-default system typeface (San Francisco on Apple, Roboto on Android, Segoe UI on Windows) for body and UI text. Pros:

- Free (no licensing cost).
- Optimized for the platform's rendering.
- Familiar to platform users.
- Performant (no font loading required).

Cons:

- Limited brand differentiation.
- Inconsistent across platforms (your product looks slightly different on each).

For most products that aren't building a strong brand identity through typography, system typefaces are a reasonable choice. They're free, performant, and well-tested.

For products with a stronger brand commitment, a custom or licensed typeface (Inter, IBM Plex, or a proprietary brand typeface) provides more consistency and personality, at some cost in licensing and performance.

## Worked examples

### A SaaS product's type system

**Typefaces:** Inter for UI and body. Inter Display for very large headings. JetBrains Mono for code.

**Scale (1.2 ratio, base 16px):** 11, 13, 16, 19, 23, 28, 33, 40 px.

**Usage:**
- Body text and UI labels: 16px Inter Regular.
- Helper text and captions: 13px Inter Regular.
- Section headings: 19px Inter Medium or 23px Inter Semibold.
- Page titles: 28–33px Inter Bold or Inter Display.
- Hero headlines: 40+px Inter Display.
- Code: 14px JetBrains Mono.

The system covers all needs with three typefaces and a single scale. New designers and engineers can reach for the system without creating new variants.

### A consumer product with brand display type

**Typefaces:** A custom display typeface for headlines, marketing surfaces, and some hero UI. Inter for body and UI text. JetBrains Mono for code.

**Usage:** the display typeface is reserved for moments where it shines (hero, marketing, occasional UI flourish). Body text uses Inter for legibility at small sizes. The display typeface would be illegible at body sizes.

The system honors brand identity through display typography while ensuring functional UI legibility through body typography.

### A code editor's type choice

**Typeface:** JetBrains Mono. Specifically chosen for character disambiguation (0 has a slash, l and 1 are clearly different, O and 0 are different) and programming ligatures.

**Size:** 14px default, with user adjustment up to 18px+ for those who prefer larger code.

**Why not Inter:** proportional fonts make code alignment ambiguous; column-based code reading depends on monospace.

### A landing page that picks the wrong type

A startup uses an elegant high-contrast modern serif (a Didot-style typeface) for both headlines and body copy. The headlines look beautiful. The body copy is hard to read: at 16px, the thin strokes of the typeface are nearly invisible on most displays, and the high contrast between thick and thin makes the text feel "broken."

The fix: use the modern serif only for display sizes (32px+). For body copy, switch to a humanist serif or sans-serif designed for sustained reading.

## Anti-patterns

**Display typefaces in body copy.** A typeface chosen for headlines used at body sizes loses its distinguishing features and becomes hard to read.

**Body typefaces in display use.** Less harmful but feels weak; the typeface doesn't have the visual presence that display sizes can support.

**Too many typefaces.** Three typefaces is plenty. Four or five starts to feel like a patchwork. Each additional typeface adds cognitive load and visual noise.

**Ad-hoc sizes.** Choosing 13.5px because it "looks right" instead of using a scale value. Over time, the type sizes spread across many arbitrary values and the system feels inconsistent.

**Sizes too small for the audience.** Designers often set body text smaller than is comfortable because the design canvas makes everything look bigger than production. Test on actual devices with actual users.

**Ignoring monospace for code.** Code in proportional fonts is hard to scan, hard to align, and ambiguous in some characters. Use monospace.

**Brand typefaces that don't render well at UI sizes.** A custom brand typeface designed for marketing materials but applied to UI may not have the legibility characteristics needed for small sizes. Either commission a UI variant of the brand typeface or use a separate UI typeface.

## Heuristic checklist

Before settling on type choices, ask: **Is each typeface chosen for its intended use (display, body, code, UI)?** Mismatches cost legibility. **Is the size appropriate for the rendering context?** Test on actual devices, not just your design canvas. **Does the scale provide all needed sizes without forcing ad-hoc values?** A complete scale prevents drift. **Are there too many typefaces?** Three is a good limit. **Have you tested with users from your actual audience?** Designer intuition about legibility is unreliable.

## Related sub-skills

- `legibility` — parent principle on visual character clarity.
- `legibility-contrast-and-spacing` — sibling skill on the rendering conditions.
- `readability` — for sustained reading of prose.
- `consistency-internal` — type systems are part of internal consistency.
- `signal-to-noise` — well-chosen type is signal; poorly chosen is noise.

## See also

- `references/typeface-selection.md` — practical guidance on choosing specific typefaces for specific use cases.
