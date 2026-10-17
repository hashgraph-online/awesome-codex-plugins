---
name: hierarchy-typographic
description: 'Use this skill when the question is specifically about how to construct visual hierarchy through typography — picking a type scale, ladders of weight, line-height steps, and the relationships between display, heading, body, and caption type. Trigger when designing type systems, choosing fonts, picking heading sizes, defining a design system''s typographic tokens, fixing a "no clear focal point in the headline area" issue, or reviewing why a long-form page feels like a wall of text. Sub-aspect of the broader `hierarchy` principle; read that first if you haven''t already.'
---

# Hierarchy through typography

Typography alone can carry a complete hierarchy without color, color alone, or layout tricks. A well-constructed type system gives you 4–6 distinct ranks of importance using nothing but size, weight, and (sometimes) tracking and tone. This skill covers how to build that system.

## When this is the decisive sub-aspect

- You're picking the type tokens for a new design system (display, h1, h2, h3, h4, body-lg, body, body-sm, caption, micro).
- You're working in a constrained color palette (monochrome, a single brand color) and need hierarchy without leaning on hue.
- The page is text-heavy (docs, articles, settings descriptions, emails) and feels like a wall.
- You're reviewing a layout where headings, sub-heads, and body text don't read as distinct ranks.

## Core ideas

### Pick a type scale, not arbitrary sizes

A *type scale* is a multiplicative ratio applied to a base size to generate a series of harmonious sizes. Common scales:

- **1.125** (Major Second) — very subtle. Good for dense application UI where step changes between sizes shouldn't shout.
- **1.2** (Minor Third) — gentle, common in software UI.
- **1.25** (Major Third) — a solid default for general web; what Tailwind's default scale approximates.
- **1.333** (Perfect Fourth) — feels editorial; good for content sites.
- **1.414** (Augmented Fourth, √2) — common in print.
- **1.5** (Perfect Fifth) — bold, feels like a magazine layout.
- **1.618** (Golden Ratio) — dramatic, marketing/hero scale.

Pick *one* ratio per project. Mixing ratios across sizes destroys the rhythm.

A worked scale at base 16px and ratio 1.25:

```
caption  10.24 px   (16 / 1.25 / 1.25)
body-sm  12.80 px   (16 / 1.25)
body     16.00 px   (base)
body-lg  20.00 px   (16 * 1.25)
h4       25.00 px   (16 * 1.25^2)
h3       31.25 px   (16 * 1.25^3)
h2       39.06 px   (16 * 1.25^4)
h1       48.83 px   (16 * 1.25^5)
display  61.04 px   (16 * 1.25^6)
```

Rounded to friendly numbers (10, 13, 16, 20, 25, 31, 39, 49, 61), this gives you a 9-step ladder with consistent visual jumps between any two adjacent steps.

### Use weight as a second axis

Size alone is enough for hierarchy in body-vs.-heading contexts but is a blunt tool when you need fine distinctions. Weight gives you a second axis. A useful weight ladder:

```
hairline / thin    100   — display only, never body
light              300   — large display sizes; never small
regular            400   — body
medium             500   — UI labels, buttons
semibold           600   — headings, emphasis
bold               700   — strong emphasis, heavy display
black              900   — display only
```

Most software UIs need only three weights: regular (400), medium (500), and semibold (600). Reach for bolder weights only at display sizes; bold at body size is hard to read.

### Combine size and weight, don't trade them

A common mistake is treating size *or* weight as the hierarchy signal. They compound:

- A 24px-semibold heading reads as much higher in the hierarchy than a 24px-regular heading, even though the size is identical.
- A 16px-regular body paragraph and a 16px-medium label are perceived as different ranks despite identical size.

When constructing a step in your hierarchy, *both* dial up: bigger headings should also be bolder. The exception is display type (very large), which often *decreases* in weight at the largest sizes (light or regular at 60px+ reads as elegant; black at 60px+ reads as shouting).

### Line height (leading) is part of the system

Tighter leading (1.1–1.25) suits display and headings. Looser leading (1.5–1.75) suits body. Mismatch a heading with body leading (1.5) and the heading feels droopy; mismatch a body with display leading (1.2) and reading becomes hard.

A workable mapping:

```
display, h1, h2:   line-height 1.1–1.25
h3, h4:            line-height 1.25–1.4
body, body-lg:     line-height 1.5–1.75
body-sm, caption:  line-height 1.4–1.6
```

### Line length (measure)

For sustained reading, constrain body text to roughly 45–75 characters per line (≈ 65ch is a common default). Longer lines fatigue eye-tracking; shorter lines fragment thought. Headings can be wider; captions and labels can be tighter.

```css
.body-text { max-width: 65ch; }
```

### Tracking (letter-spacing)

Generally leave tracking alone. Two cases where it earns adjustment:

- **All-caps labels and small caps:** add ~0.04–0.08em of tracking; they read tightly otherwise.
- **Very large display type:** subtract a small amount (-0.01 to -0.02em); large type looks loose without it.

## Worked example: a complete typographic hierarchy in CSS

```css
:root {
  /* Type scale at ratio 1.25, base 16px */
  --text-caption: 0.64rem;   /* 10.24 */
  --text-sm:      0.80rem;   /* 12.80 */
  --text-base:    1.00rem;   /* 16.00 */
  --text-lg:      1.25rem;   /* 20.00 */
  --text-xl:      1.563rem;  /* 25.00 */
  --text-2xl:     1.953rem;  /* 31.25 */
  --text-3xl:     2.441rem;  /* 39.06 */
  --text-4xl:     3.052rem;  /* 48.83 */
  --text-display: 3.815rem;  /* 61.04 */

  /* Weight ladder */
  --weight-body:     400;
  --weight-label:    500;
  --weight-emphasis: 600;
  --weight-display:  700;

  /* Leading */
  --leading-display: 1.1;
  --leading-heading: 1.25;
  --leading-body:    1.6;
  --leading-tight:   1.4;
}

.display {
  font-size: var(--text-display);
  font-weight: 400;          /* display gets lighter weight, paradoxically */
  line-height: var(--leading-display);
  letter-spacing: -0.02em;
}
h1 {
  font-size: var(--text-3xl);
  font-weight: var(--weight-emphasis);
  line-height: var(--leading-heading);
  letter-spacing: -0.01em;
}
h2 {
  font-size: var(--text-2xl);
  font-weight: var(--weight-emphasis);
  line-height: var(--leading-heading);
}
h3 {
  font-size: var(--text-xl);
  font-weight: var(--weight-emphasis);
  line-height: var(--leading-heading);
}
h4 {
  font-size: var(--text-lg);
  font-weight: var(--weight-label);
  line-height: var(--leading-heading);
}
body, p {
  font-size: var(--text-base);
  font-weight: var(--weight-body);
  line-height: var(--leading-body);
  max-width: 65ch;
}
.label, button, .ui-control {
  font-size: var(--text-sm);
  font-weight: var(--weight-label);
  line-height: var(--leading-tight);
}
.caption, small, .micro {
  font-size: var(--text-caption);
  font-weight: var(--weight-body);
  line-height: var(--leading-tight);
  color: rgb(0 0 0 / 0.55);   /* tone reduction adds tertiary recession */
}
```

Eight clear ranks, all derived from one ratio, three weights, three leading values, and one tone reduction at the very bottom. This is enough hierarchy to handle any UI or content surface.

## Anti-patterns

- **Random sizing.** "Make this 18px" / "this 19px" / "this 22px" — close-but-not-equal sizes look like accidents. If two things should be the same rank, give them the same size; if different ranks, make the difference clear.
- **Bold everything.** When every label, every heading, and every value is bold, none of them read as emphasized. Reserve bold for one or two roles.
- **Gigantic body type.** Body text larger than ~18–20px starts to feel like a slide deck. Reserve large type for headings; keep body in the 14–18px range.
- **Tiny captions.** Below 11px, anti-aliasing destroys legibility. If you find yourself reaching for 9px or 10px, you have too much content for the space — cut content rather than shrink type.
- **Inconsistent weight per role.** "Card titles are semibold here, medium there." Decide once per role.

## Heuristics

1. **Print-test.** Print the page in grayscale on regular paper. Hierarchy that survives this test is robust. Hierarchy that requires color or screen brightness is fragile.
2. **Three-rank squint.** Squint until detail blurs. You should still see a primary tier, a secondary tier, and a recessive tier. If everything is one tone of grey, hierarchy is too flat.
3. **The body-only test.** Hide all headings; the body should still feel like prose, not a wall. If it feels like a wall, your `max-width` or leading is wrong.

## Related principles

- **`hierarchy`** — the parent skill. Read it for the full framing.
- **`hierarchy-spatial`** — when type alone isn't enough, spatial hierarchy carries the rest.
- **`hierarchy-color-and-tone`** — color and tone as a third axis on top of size+weight.
- **`legibility`** and **`readability`** — the typeface- and layout-side of typography that hierarchy depends on.
- **`signal-to-noise-ratio`** — too many active ranks reduces SNR; restraint multiplies the effect of each rank.
