---
name: hierarchy-spatial
description: 'Use this skill when constructing visual hierarchy through layout, position, size, and whitespace — not type, not color. Trigger when laying out a page or section and deciding what gets the dominant region, where to place the focal element, how much breathing room to give it, and how secondary elements should arrange around it. Trigger when reviewing a layout that "feels cramped" or "feels lost," when a hero''s CTA is competing with surrounding content, or when a dashboard''s primary KPI is the same size as everything else. Sub-aspect of the broader `hierarchy` principle; read that first if you haven''t already.'
---

# Hierarchy through space

Spatial hierarchy uses three tools: **position**, **size** (relative to neighbors), and **whitespace** (isolation around an element). Together they can carry a complete hierarchy without depending on typography or color. Spatial hierarchy is what makes a magazine spread or a museum poster work even before you read a word.

## When this is the decisive sub-aspect

- You're laying out a hero, dashboard, gallery, or any composition where placement and size are doing more work than type.
- You're reviewing a screen where "everything has the same weight" — the typographic hierarchy is fine but the layout is flat.
- You need to elevate one element among many roughly equivalent ones (a featured project, a recommended plan, a primary metric).
- You're working in a constrained type system (one or two sizes) and need hierarchy from elsewhere.

## Core ideas

### Size relative to neighbors carries hierarchy

Absolute size matters less than *relative* size. A 200×200 card next to other 200×200 cards is neutral. The same card at 200×200 next to seven 100×100 cards is dominant. Scale operates *against the local norm*; design hierarchy by establishing a norm and then breaking it deliberately.

In CSS Grid, this is `grid-column: span N` and `grid-row: span N`:

```html
<section style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
  <article class="featured" style="grid-column: span 2; grid-row: span 2;">…primary…</article>
  <article>…secondary…</article>
  <article>…secondary…</article>
  <article>…secondary…</article>
  <article>…secondary…</article>
  <article>…secondary…</article>
  <article>…secondary…</article>
</section>
```

The featured article occupies four times the area of its neighbors. The eye lands there first.

### Position privileges (in left-to-right scripts)

The eye, given an unfamiliar uniform layout, falls back to the **Z-pattern** (Gutenberg Diagram): top-left → top-right → bottom-left → bottom-right. Use this:

- **Top-left** is the *primary optical area*. A logo, page title, or brand mark goes here naturally.
- **Top-right** is the *strong fallow*. Useful for a primary CTA or account chrome.
- **Bottom-right** is the *terminal area*. The eye exits here; place the conversion CTA in conversion-focused layouts.
- **Bottom-left** is the *weak fallow*. Recede secondary content here.

When hierarchy is *strong*, this default is overridden by the dominant element. When hierarchy is *weak*, the Z-pattern takes over by default.

In RTL scripts, mirror the pattern.

### Whitespace as a hierarchy signal

Whitespace around an element communicates importance. A primary heading with 4rem of margin above and below reads as more significant than the same heading with 0.5rem of margin. The element seems to *occupy* its space, not merely *fill* it.

The rough rule: *the more space around an element, the more important it appears* — up to a point where excess space starts to read as accident or empty page.

A worked example using a vertical rhythm:

```css
:root {
  --rhythm-tight: 0.25rem;   /* between label and input */
  --rhythm-base:  1rem;      /* between fields in a section */
  --rhythm-loose: 2rem;      /* between sections */
  --rhythm-major: 4rem;      /* between page regions */
  --rhythm-hero:  8rem;      /* hero/marketing surfaces */
}

.field-group   > * + * { margin-top: var(--rhythm-tight); }
.section       > * + * { margin-top: var(--rhythm-base); }
.page          > section + section { margin-top: var(--rhythm-loose); }
.page-region   { padding-block: var(--rhythm-major); }
.hero-section  { padding-block: var(--rhythm-hero); }
```

Five rhythm levels, each ~2x the previous. The eye reads the spacing as nesting: the things closest are most related; the things farthest are most separate (Proximity); the things with the most surrounding space are most important (Hierarchy).

### Aspect ratio and orientation

A wide element reads as expansive (banner, hero); a tall element reads as deep (sidebar, column); a square element reads as neutral (card, tile). Choose aspect ratio to match the role:

- **Hero / banner / page header** — wide (≥ 16:9 or 21:9). Establishes presence.
- **Card / tile** — square or 4:3 / 3:4. Neutral; designed to repeat.
- **Sidebar / column** — tall and narrow. Recedes laterally.
- **Modal / dialog** — typically 4:3 or 3:2 — wide enough for content, tall enough to feel deliberate.

Mismatching aspect to role makes hierarchy fight the layout.

### Centering and alignment as hierarchy signals

Center alignment is high-attention but inflexible (you can't add another centered thing without competition). Left alignment is lower-attention but extensible. Right alignment is rare and signals secondary action (e.g., toolbar overflow menu).

A useful rule: **center the one element you want the user to look at first; left-align everything else.**

```html
<section class="hero">
  <h1 style="text-align: center;">Run payroll in minutes</h1>      <!-- centered: the focal element -->
  <p   style="text-align: center;">Not hours. Not the next morning.</p>  <!-- centered: paired support -->
  <div style="text-align: center;"><button>Start free trial</button></div>
</section>

<section class="features" style="margin-top: 6rem;">
  <h2>What you get</h2>           <!-- left-aligned: secondary section -->
  <ul>
    <li>Automatic tax calculations</li>
    <li>Direct deposit to 50 states</li>
    <li>Year-end W-2 / 1099 generation</li>
  </ul>
</section>
```

The hero is centered; the rest is left-aligned. The eye registers the difference and treats the hero as the moment.

## Worked example: a marketing landing page

Combining all the spatial hierarchy tools:

```html
<main class="landing">
  <!-- Hero: centered, generous space, dominant -->
  <section style="padding: 8rem 1rem; text-align: center;">
    <h1 style="font-size: 4rem; max-width: 32ch; margin: 0 auto;">
      Run payroll in minutes, not hours
    </h1>
    <p style="font-size: 1.25rem; max-width: 50ch; margin: 1.5rem auto 0;">
      Built for small teams that don't have a dedicated finance person.
    </p>
    <div style="margin-top: 3rem;">
      <button class="primary">Start free trial</button>
    </div>
  </section>

  <!-- Features: 3-up grid, left-aligned, recessed -->
  <section style="padding: 4rem 1rem; max-width: 1100px; margin: 0 auto;">
    <h2>Designed for small teams</h2>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-top: 3rem;">
      <article><h3>Automatic taxes</h3><p>...</p></article>
      <article><h3>Direct deposit</h3><p>...</p></article>
      <article><h3>Year-end forms</h3><p>...</p></article>
    </div>
  </section>

  <!-- Featured customer: dominant within its section -->
  <section style="padding: 4rem 1rem; background: #f7f7f7;">
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 4rem; max-width: 1100px; margin: 0 auto;">
      <blockquote style="font-size: 1.5rem; line-height: 1.5;">
        "We went from spending two days on payroll each month to twenty minutes."
      </blockquote>
      <div>
        <p>Clara Mendoza</p>
        <p>COO, Bright Labs</p>
      </div>
    </div>
  </section>
</main>
```

Three spatial hierarchies: hero dominant via centering + space; features uniform via grid; testimonial dominant within its section via 2:1 split. The page reads top-to-bottom with clear focal moments.

## Anti-patterns

- **Equal-space everything.** Every section the same height, every gap the same size. The eye gets no rhythm; the whole page feels mechanical.
- **Centered everything.** Centering for emphasis works because most content is left-aligned. Center every paragraph and the emphasis collapses.
- **The fold panic.** Cramming the hero, three features, and a CTA "above the fold" because of an imagined scroll-aversion. Modern users scroll without resistance; let the hero breathe and the CTA earn its place.
- **The wall of cards.** A grid of identical cards with no featured tile is a "browsing" composition, not a "reading" composition. If the user is supposed to act, elevate one card.
- **Whitespace where attention should be.** Massive whitespace around a recessive element makes the eye land on emptiness. Whitespace amplifies attention; aim it at things that earn it.

## Heuristics

1. **Mass diagram.** Sketch the page as filled black blocks with no detail. The dominant block should be 2–4× any other. If all blocks are similar size, hierarchy is flat.
2. **The 30-foot test.** Stand back from your screen at distance until labels are unreadable. The composition should still tell you what's important.
3. **Trace the eye-path.** Draw the line your eye follows through the composition. It should land on the primary first, sweep through secondaries, and exit at a CTA or terminal. If your eye-path is chaotic or returns to the primary repeatedly, refine.

## Related principles

- **`hierarchy`** — parent skill. Read it for full framing.
- **`hierarchy-typographic`** — type-driven hierarchy; combines with spatial.
- **`proximity`** — spacing between elements (Gestalt grouping); compounds with spatial hierarchy.
- **`alignment`** — spatial hierarchy operates on a grid; misalignment fights it.
- **`gutenberg-diagram`** — the default eye-path when hierarchy is absent.
- **`horror-vacui`** — the impulse to fill empty space; resist it on important surfaces.
