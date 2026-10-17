# Type-scale history and reference

A deeper reference on typographic hierarchy: where common type scales come from, why specific ratios feel right, and how typographic hierarchy is constructed in print and digital contexts beyond the modern web.

## Historical type scales

The "type-scale ratios" used in modern web design are not invented — they descend from centuries of typesetting practice.

### The traditional metal-type sizes

Before computers, typefaces were cast at fixed point sizes. The set of sizes a typesetter typically had to work with was:

```
6, 8, 9, 10, 11, 12, 14, 16, 18, 24, 30, 36, 42, 48, 60, 72
```

These aren't arbitrary; they evolved as a working compromise between geometric ratios and the practical economics of metal foundry production. The ratio between adjacent sizes is roughly 1.15–1.2, comfortable for body type. Display sizes (24+) jump in larger ratios because subtle differences are imperceptible at scale.

A modern type scale at ratio 1.2 (Minor Third) approximates this traditional scale closely.

### Renaissance proportions

Renaissance typesetters (Aldus Manutius, Claude Garamond) often worked from geometric proportions rooted in classical architecture: the golden ratio (1.618) for page layouts, simpler integer ratios (3:4, 2:3) for type scales.

Robert Bringhurst's *The Elements of Typographic Style* documents these traditions in detail. They're worth reading because the same proportional logic that worked for 15th-century books still produces calm, balanced layouts on screens.

### Modular scales for the web

In 2011, Tim Brown's "More Meaningful Typography" article introduced the modern web design community to *modular scales* — using a single mathematical ratio to generate a series of harmonious sizes from a base value. The popular ratios:

| Ratio | Name | Where it shines |
|---|---|---|
| 1.067 | Minor Second | Subtle UI; very tight ladder |
| 1.125 | Major Second | Dense application UI |
| 1.2 | Minor Third | General software UI (Tailwind default approximates) |
| 1.25 | Major Third | Web content sites |
| 1.333 | Perfect Fourth | Editorial layouts |
| 1.414 | Augmented Fourth | Print, classical |
| 1.5 | Perfect Fifth | Bold magazines |
| 1.618 | Golden Ratio | Hero/marketing scale |
| 1.778 | Major Seventh | Cinematic, oversized hero |

Some teams use *two* ratios — a tighter ratio for body-related sizes (caption, body, body-large) and a wider ratio for display sizes (h1, display). This produces a calm reading experience while still delivering dramatic display type.

## Cross-domain examples

### Newspaper typography

A newspaper front page often shows 5–6 distinct type sizes:

- Masthead (display, often custom typeface): 60–80 pt.
- Lead headline: 36–48 pt.
- Secondary headline: 18–24 pt.
- Section heading / kicker: 9–12 pt.
- Body: 8–10 pt.
- Caption: 7–8 pt.

Notice the *condensed* range at the body end (8, 9, 10) and the wider jumps at the display end. This is the two-ratio approach in practice.

### Apple's San Francisco type system

Apple's San Francisco (SF) typeface ships with a documented type scale and weight ladder spanning ~9 sizes (Caption 2 through Large Title) and ~9 weights (Ultralight through Black). The system encodes hierarchy decisions that designers don't have to re-derive every project.

### Google Material's type system

Material Design 3 documents a specific scale: Display Large, Display Medium, Display Small, Headline Large, Headline Medium, Headline Small, Title Large, Title Medium, Title Small, Body Large, Body Medium, Body Small, Label Large, Label Medium, Label Small. Fifteen tiers — overkill for most applications, but the structure is useful as a reference.

### Web fonts and font loading

A practical reality: web fonts add render-blocking work. Three patterns:

- **System font stack** — `font-family: -apple-system, BlinkMacSystemFont, ...` — uses OS-default. Zero load cost; varies by platform.
- **Variable fonts** — one file with weight and width axes. Allows continuous weight/size variation; cuts file count.
- **Subset and preload** — load only the glyphs you use; preload critical fonts.

For typographic hierarchy specifically: variable fonts are a quiet revolution. They let you fine-tune weight at every size — slightly thinner display, slightly heavier body — at no extra file cost.

## The leading question

Line-height (leading) interacts with type size and reading mode:

- **Display type at ~1.0–1.1 line-height** — tight, no excessive air between lines.
- **Headings at ~1.2–1.3** — distinct from body, but not so loose they break.
- **Body at 1.5–1.7** — the canonical reading range.
- **Captions and small labels at 1.4–1.5** — slightly tighter than body because text is smaller.

The reason: the optimal line-height varies inversely with size up to a point. Big type needs less leading because the visual gap between lines is already large in absolute terms; small type needs more because the gap collapses fast as size shrinks.

## Anti-patterns from print that recur on the web

- **Widows and orphans.** Single-word last lines or single-line first lines on a page. Print typesetters fixed these manually; CSS now offers `widows`, `orphans`, and `text-wrap: balance` for similar control.
- **Justified body without manual hyphenation.** Looks tidy in mockups; produces "rivers of white" in real text. Use ragged-right (`text-align: left`) for screen body; `hyphens: auto` if you must justify.
- **Mixed typefaces without intent.** Two body typefaces and one display, none related. Pick one or two families and use weight/style to differentiate.

## Resources for going further

- **Bringhurst, R.** *The Elements of Typographic Style* — comprehensive print-grounded reference.
- **Lupton, E.** *Thinking with Type* — accessible introduction.
- **Type-Scale.com** — interactive scale generator.
- **Modular Scale** (Tim Brown) — modularscale.com.
- **System Font Stack** — systemfontstack.com — for OS-default fallbacks.
- **Variable Fonts** — v-fonts.com — gallery of variable fonts.

## Closing thought

Typographic hierarchy is an intersection of math (the scale) and craft (the choices about which weights, leadings, and tracking values match the type at each size). The math gets you 80% of the way; the last 20% is taste developed by looking at lots of typeset pages.
