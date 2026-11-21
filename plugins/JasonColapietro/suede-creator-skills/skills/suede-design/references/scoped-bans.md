# Scoped Bans And Exceptions

Art-direction prompts for authorized new design work. These suggestions are
not defects by themselves and do not authorize changing an intentional brand,
approved copy or a surface outside scope. Content-integrity rules remain firm.

## Scoped Bans And Exceptions

Keep a pattern when it serves the task or belongs to the confirmed brand or
platform. An audit need not justify an exception to a reviewer's taste. Apply
standards, documented project conventions and optional suggestions distinctly.

When exploring new art direction, consider whether these familiar defaults
serve the subject. Rewrite only inside an authorized design scope:

### Scaffolding And Typography Devices

**Tiny uppercase tracked eyebrow above every section.**
BEFORE: a small all-caps kicker ("ABOUT" · "PROCESS" · "PRICING") sitting above every section heading, page after page.
AFTER: vary the cadence, or drop the kicker and let the heading carry weight. One deliberate kicker as a named brand device is voice; one on every section is AI grammar.

**Numbered section markers as default scaffolding (01 / 02 / 03).**
BEFORE: `01 · About` / `02 · Process` / `03 · Pricing` stamped above every section regardless of content.
AFTER: reserve numbering for a real ordered sequence (an actual 3-step flow, a timeline) where the order carries information. Elsewhere, drop it.

**Identical icon-card grids as main page structure.**
BEFORE: 3×2 grid of cards each with icon + title + one-line description
AFTER: A task-driven layout where each row or section maps to a specific user action, not a product category

**Punctuation repeated as a style reflex.**
Follow the established voice. Punctuation alone is not a review finding; do not
rewrite approved sales copy or claims for personal preference.

### Surface And Color Treatments

**Gradient text.**
BEFORE: `-webkit-background-clip: text` rainbow or metallic effect on headlines
AFTER: A single high-contrast headline at full weight with an accent word in a solid color, or a single-hue gradient at low chroma (essentially a slight lightness shift)

**Decorative glass panels (blur + translucent background).**
BEFORE: `backdrop-filter: blur(20px)` card floating over a gradient background
AFTER: An opaque surface at the correct elevation token, with a 1px border for definition

**Colored side-stripe borders on cards, alerts, or list items.**
BEFORE: A card with a 4px left border in `--color-warning` indicating status
AFTER: An icon + label in the semantic color inside the card; or a top-of-card banner strip that spans the full width and carries text

**The ghost-card pattern (thin border plus soft wide shadow, stacked).**
BEFORE: `border: 1px solid` combined with `box-shadow: 0 16px+ blur` on the same card or button as decoration.
AFTER: pick one: a defined border at the brand color, or a shadow no wider than 8px blur at the correct elevation token. Never both as ornament.

**Over-rounded corners.**
BEFORE: `border-radius: 32px` or higher on cards, sections, or inputs.
AFTER: cap cards and inputs at 12-16px radius. Full-pill radius is fine for tags and buttons only.

**Repeating-linear-gradient stripe backgrounds.**
BEFORE: diagonal stripe patterns in a section or body background via `repeating-linear-gradient`.
AFTER: a real art-direction choice: solid surface, noise texture, or a concrete product artifact.

**Decorative orbs, bokeh blobs, generic gradient backgrounds.**
BEFORE: Three radial gradients at 30% opacity behind the hero
AFTER: A concrete art-direction choice: a noise texture, a geometric system, a real product screenshot, an illustrated scene, or a typographic lock-up that IS the background

**Cream, sand, or beige as the default body background.**
BEFORE: a near-white warm-tinted background (OKLCH lightness 0.84-0.97, chroma below 0.06, hue 40-100) used as the safe default for "warm" or "editorial" briefs, under a name like `--paper`, `--cream`, `--sand`, `--linen`, or `--ivory`.
AFTER: pick a saturated brand color as the body, a true off-white at chroma 0 (or tinted toward the brand's own hue, not toward warmth by default), or a darker tinted neutral that reads as this brand's own. Carry "warmth" through accent color, typography, and imagery instead. Same chroma-tinting discipline as the Color Strategy Axis above, applied to the one background choice teams default on without thinking.

### Content Integrity And Structure

**The hero-metric template (big number, tiny label, support stats, gradient accent).**
BEFORE: `$2.4M` in 80px weight-900 with "Revenue generated" in 12px below it
AFTER: A metric placed inside a real workflow context. E.g., the royalty total shown inside the rights ledger column it belongs to, not isolated as a hero number.

**Modal as the first answer to every interaction.**
BEFORE: Every "view details" → opens modal
AFTER: Inline expansion, side panel, or dedicated route; modal reserved for destructive confirmation or focused isolated actions

**Centered hero copy over a stock-feeling gradient with no real Suede artifact.**
BEFORE: "Own Your Music" centered on dark purple, no visual content below
AFTER: A hero that contains a real product artifact (a partial rights registry UI, an animated waveform ledger, a claim receipt) with copy anchored to it.

**Fake metrics, fake testimonials, fake partner claims.**
No exception. Remove and replace with either: (a) a real stat with a source note, (b) a placeholder with a `[NEEDS REAL DATA]` flag, or (c) a structural element that doesn't depend on a specific number.

**Hand-drawn or sketchy SVG illustrations.**
BEFORE: crude wavy-line doodles, `feTurbulence`/`feDisplacementMap` "paper grain" filters, or a 5-30 path sketch standing in for a real subject.
AFTER: ship a real asset (photo, product screenshot, a properly illustrated scene) or ship no illustration at all.
