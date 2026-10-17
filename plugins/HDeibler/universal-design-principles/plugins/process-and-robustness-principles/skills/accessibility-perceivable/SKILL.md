---
name: accessibility-perceivable
description: 'Use this skill when the question is whether users can *perceive* the content — see it, hear it, or feel it — regardless of impairment. Trigger when designing color systems, picking text sizes, building image-heavy surfaces, working with video/audio, designing for low-vision users, or running an accessibility audit. Covers WCAG Principle 1 (Perceivable). Sub-aspect of `accessibility`; read that first if you haven''t already.'
---

# Accessibility — Perceivable

WCAG Principle 1: information and user-interface components must be presentable to users in ways they can perceive.

The four sub-criteria, simplified:

1. **Text alternatives** for non-text content.
2. **Time-based media** (audio/video) has alternatives.
3. **Adaptable** content can be presented in different ways without losing structure.
4. **Distinguishable** — color contrast, audio control, text resizing.

This skill covers each in practical detail.

## 1. Text alternatives

### Images

Every image gets alternative text describing what's relevant about it. The right alt text depends on the image's role:

```html
<!-- Informative: describe what the user needs to know -->
<img src="/dashboard-screenshot.png"
     alt="Dashboard showing $48,200 monthly revenue, up 12% from last month." />

<!-- Functional (image as link / button): describe the action -->
<a href="/profile">
  <img src="/avatar.png" alt="Open your profile" />
</a>

<!-- Decorative: empty alt so screen readers skip -->
<img src="/decorative-pattern.svg" alt="" aria-hidden="true" />

<!-- Complex (chart, infographic): brief alt + linked long description -->
<figure>
  <img src="/sales-chart.png"
       alt="Quarterly sales chart, see description below."
       aria-describedby="chart-desc" />
  <figcaption id="chart-desc">
    Sales rose from $12k in Q1 to $58k in Q4, with a dip to $31k in Q3 caused
    by a supply chain interruption.
  </figcaption>
</figure>
```

**Common mistakes:**
- `alt="image"` or `alt="photo of woman"` — describes the file type, not the meaning.
- Decorative images with non-empty alt — screen reader users hear "decorative-pattern-3-svg" announced as content.
- Long alt text on simple images — alt should be ≤ 125 characters; longer goes in `<figcaption>` or linked description.

### Icons

Icon-only buttons need an accessible name. Two patterns:

```html
<!-- Pattern A: aria-label on the button -->
<button aria-label="Close">
  <svg aria-hidden="true">...</svg>
</button>

<!-- Pattern B: visually-hidden text -->
<button>
  <svg aria-hidden="true">...</svg>
  <span class="sr-only">Close</span>
</button>
```

Either is fine; pattern B can be more reliable across screen readers. The `sr-only` class:

```css
.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
  border: 0;
}
```

### Decorative SVG

```html
<svg aria-hidden="true" focusable="false">...</svg>
```

`aria-hidden` removes from accessibility tree; `focusable="false"` prevents keyboard focus on the SVG (some browsers focus SVGs by default).

## 2. Time-based media

### Video

- **Captions** for all spoken content. Auto-generated captions are a starting point; review for accuracy.
- **Audio descriptions** for visual content not conveyed by audio (a chart appearing on screen, a character action shown but not narrated).
- **Transcripts** as text alternatives for anyone who can't watch.

### Audio

- **Transcripts** for podcasts, interviews, voicemails.
- **Captions or transcripts** for any audio-only message in the UI.

### Auto-playing media

Don't autoplay video or audio with sound. WCAG 1.4.2 requires that audio playing for more than 3 seconds either:

- Has a pause/stop control, or
- Has a volume control independent of system volume.

Better: don't autoplay sound at all. It's hostile to users with hearing aids, in public spaces, or sharing audio output.

## 3. Adaptable

### Semantic structure

Use HTML elements for what they're for. Heading order matters; landmarks matter; lists matter.

```html
<!-- Right -->
<main>
  <h1>Dashboard</h1>
  <section aria-labelledby="kpi-heading">
    <h2 id="kpi-heading">This month</h2>
    <ul>
      <li>Revenue: $48k</li>
      <li>Users: 12,481</li>
    </ul>
  </section>
</main>

<!-- Wrong: divs everywhere, no structure -->
<div>
  <div>Dashboard</div>
  <div>This month</div>
  <div>Revenue: $48k</div>
  <div>Users: 12,481</div>
</div>
```

Screen readers navigate by headings (`H` key in NVDA), landmarks (`R` key), lists, links. Without semantic structure, navigation falls apart.

### Heading order

Don't skip heading levels. Page structure:

```
<h1>Page title (one per page)
  <h2>Section
    <h3>Subsection
      <h4>Sub-subsection
```

Going from `<h1>` to `<h3>` confuses assistive tech. If the visual size you want for an `<h2>` is too large, restyle the `<h2>` — don't reach for `<h3>` to get smaller text.

### Reading order

Source order in HTML should match visual reading order. CSS Grid and Flexbox can rearrange visually, but screen readers follow source order.

```html
<!-- Source order matches visual order: title, then summary, then details -->
<article>
  <h2>Article title</h2>
  <p class="summary">Brief summary.</p>
  <p>Detailed body...</p>
</article>

<!-- Wrong: visually rearranged but source order is now confusing -->
<article style="display: flex; flex-direction: column-reverse;">
  <p>Detailed body...</p>
  <p>Summary.</p>
  <h2>Title</h2>
</article>
```

### Programmatic relationships

Use `<label for>`, `aria-labelledby`, `aria-describedby` to expose visual relationships to assistive tech.

```html
<div>
  <label for="email">Email</label>
  <input id="email" aria-describedby="email-help" />
  <p id="email-help">We'll never share this.</p>
</div>
```

The label is associated; the help text is associated. A screen reader announces all three together.

## 4. Distinguishable

### Color contrast

WCAG ratios:

| Content | Level AA | Level AAA |
|---|---|---|
| Body text (< 18pt regular or < 14pt bold) | 4.5:1 | 7:1 |
| Large text (≥ 18pt regular or ≥ 14pt bold) | 3:1 | 4.5:1 |
| UI components and graphical objects | 3:1 | (no AAA) |
| Disabled / inactive elements | (exempt) | (exempt) |

Test every text-on-background combination. Common failures:

- Light grey body text (`#999` on white = 2.85:1, fails AA).
- Brand-color body links (`#1e90ff` on white = 3.4:1, fails AA for body text).
- Placeholder text in inputs (often muted to look "less important," ends up unreadable).

Tools: WebAIM Contrast Checker, Stark plugin, Chrome DevTools' contrast inspector.

### Color not the only signal

WCAG 1.4.1: don't use color alone to convey information. Pair with icon, text, pattern, or position.

```html
<!-- Wrong: red border = error, but if red isn't perceivable, no signal -->
<input style="border: 2px solid red" />

<!-- Right: red border + icon + descriptive text -->
<div class="field" data-state="error">
  <label for="email">Email</label>
  <input id="email" aria-invalid="true" aria-describedby="email-error" />
  <p id="email-error">
    <AlertIcon aria-hidden="true" /> Please enter a valid email.
  </p>
</div>
```

### Text resize

WCAG 1.4.4: text must be resizable up to 200% without loss of content or functionality. Test:

- Browser zoom at 200% — does content reflow without horizontal scroll?
- Text size only at 200% (Firefox supports text-only zoom) — does the layout survive?

Use relative units (`rem`, `em`, `%`) for type sizes; avoid `px` for body text. Use `vw`/`vh` cautiously — they don't scale with text size.

### Reflow

WCAG 1.4.10 (Level AA): content reflows to a 320 CSS-pixel-wide viewport without requiring horizontal scrolling. Equivalent to 400% zoom on a 1280px viewport.

Practical test: open the design in DevTools at 320px wide and 1280px wide. Anything that requires sideways scroll for primary content fails.

### Images of text

Avoid embedding text in images (which can't be resized, restyled, or read by screen readers). Render text as text wherever possible. SVG with `<text>` elements is OK because it scales and can be read; raster images of text aren't.

### Non-color content

Patterns, textures, position, shape — non-color signals carry meaning for color-blind users:

```html
<!-- Chart series with color + pattern -->
<svg>
  <rect fill="url(#solid-blue)" />     <!-- Series A: solid blue -->
  <rect fill="url(#striped-blue)" />   <!-- Series B: striped blue -->
  <rect fill="url(#dotted-blue)" />    <!-- Series C: dotted blue -->
</svg>
```

Even users who can perceive color benefit from redundant signals.

## Worked example: an accessible status badge system

```html
<style>
  .badge { display: inline-flex; align-items: center; gap: 4px;
           padding: 2px 8px; border-radius: 9999px;
           font-size: 12px; font-weight: 500; }
  .badge--success { background: hsl(142 70% 95%); color: hsl(142 70% 22%); }
  .badge--warning { background: hsl(38 95% 95%); color: hsl(38 90% 25%); }
  .badge--error   { background: hsl(0 80% 95%); color: hsl(0 75% 32%); }
</style>

<span class="badge badge--success">
  <CheckIcon aria-hidden="true" /> Paid
</span>
<span class="badge badge--warning">
  <ClockIcon aria-hidden="true" /> Pending
</span>
<span class="badge badge--error">
  <AlertIcon aria-hidden="true" /> Overdue
</span>
```

What's working:

- Color + icon + text — three signals.
- Contrast ratios above 7:1 for both color combinations (verified in a contrast checker).
- Icons have `aria-hidden` since the text already conveys meaning.
- Background color tinted, foreground darkened, both relative to a hue rather than using full saturation (preserves AA contrast).

## Anti-patterns

- **`alt="image"` or `alt=""` on informative images.** Screen reader users get nothing.
- **Color-only error states.** A red border with no text or icon. Color-blind users perceive no error.
- **Pale-grey body text for elegance.** Below 4.5:1 contrast — looks polished, fails AA, exhausts users with low vision.
- **Auto-playing video with sound.** Hostile to users in shared spaces, with hearing aids, on subway commutes.
- **Heading shenanigans.** Using `<h2>` for "I want this size" rather than for structural meaning. Leaves `<h1>` missing or `<h2>` skipped.

## Heuristics

1. **The contrast checker pass.** Every text-on-background pair, every UI-element-against-background pair. Body must clear 4.5:1; large text and UI 3:1.
2. **The grayscale pass.** Take a screenshot, convert to grayscale. Do all status indicators still parse?
3. **The 200% zoom test.** Browser zoom to 200%. Layout survives? Buttons still hittable? No content lost?
4. **The screen-reader pass.** With VoiceOver / NVDA / TalkBack, walk a critical flow. Listen for unlabeled controls, announced as "blank," missing state.
5. **The image audit.** Every `<img>`. Alt text describes what the user needs to know. Decorative images have empty alt.

## Related skills

- **`accessibility`** (parent).
- **`accessibility-operable`** — keyboard reach and target size.
- **`accessibility-understandable`** — labels, copy, predictability.
- **`accessibility-robust`** — semantic markup and ARIA.
- **`color`** and **`hierarchy-color-and-tone`** (perception) — color decisions that respect contrast.
- **`legibility`** and **`readability`** (perception) — type decisions that aid perception.
