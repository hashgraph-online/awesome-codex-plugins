# Perceivable: standards and edge cases

A reference complementing `accessibility-perceivable` SKILL.md with deeper detail on the WCAG 1.* criteria and harder cases.

## WCAG 1.* criteria summary

The Perceivable principle has four guidelines, each with measurable success criteria.

### 1.1 Text alternatives

- **1.1.1 Non-text Content (Level A)** — every non-text element has an equivalent text alternative.

### 1.2 Time-based media

- **1.2.1 Audio-only and Video-only (A)** — alternatives provided.
- **1.2.2 Captions (A)** — captions for prerecorded audio.
- **1.2.3 Audio Description or Media Alternative (A)** — audio description or text alternative for video.
- **1.2.4 Captions (Live) (AA)** — captions for live audio.
- **1.2.5 Audio Description (AA)** — audio description for prerecorded video.

### 1.3 Adaptable

- **1.3.1 Info and Relationships (A)** — information and structure conveyed in presentation must be programmatically determinable.
- **1.3.2 Meaningful Sequence (A)** — content order makes sense when linearized.
- **1.3.3 Sensory Characteristics (A)** — instructions don't rely solely on shape, color, position.
- **1.3.4 Orientation (AA)** — content works in both portrait and landscape.
- **1.3.5 Identify Input Purpose (AA)** — common form fields use autocomplete attributes.

### 1.4 Distinguishable

- **1.4.1 Use of Color (A)** — color is not the only visual means of conveying information.
- **1.4.2 Audio Control (A)** — auto-playing audio over 3 seconds has stop/pause.
- **1.4.3 Contrast (Minimum) (AA)** — 4.5:1 body, 3:1 large.
- **1.4.4 Resize Text (AA)** — text resizable to 200% without loss.
- **1.4.5 Images of Text (AA)** — avoid images of text where text would do.
- **1.4.10 Reflow (AA)** — content reflows to 320 px wide without horizontal scroll.
- **1.4.11 Non-text Contrast (AA)** — UI components and graphical objects have 3:1 contrast.
- **1.4.12 Text Spacing (AA)** — content adapts to user-set spacing.
- **1.4.13 Content on Hover or Focus (AA)** — hover/focus revealed content is dismissable, hoverable, persistent.

## Hard cases

### Charts and infographics

A chart is non-text content per 1.1.1, but a one-line alt won't convey the chart's data. Patterns:

- **Brief alt + linked long description.** "Quarterly sales chart, see description below." Then a `<figcaption>` or separate page detailing the data.
- **Data table alongside the chart.** The same data in `<table>` form for screen reader users; the chart for sighted users.
- **`<svg>` with native semantics.** SVG charts can include `<title>` and `<desc>` elements that screen readers may read.

For complex visualizations (interactive dashboards), text alternative is harder. Consider letting screen reader users access the underlying data directly rather than describing the visualization.

### Decorative vs. functional images

The line is sometimes blurry. Heuristics:

- If removing the image would lose information, it's informative — needs alt.
- If removing the image only loses style, it's decorative — `alt=""` and `aria-hidden="true"`.
- If the image *is* the link/button, alt describes the action.
- An image that adds *atmosphere* but no information (a hero photo behind a heading) is decorative.

### CAPTCHA

WCAG 1.1.1 requires text alternatives for non-text content, but CAPTCHA exists to defeat automated systems including assistive tech. The accommodation: provide alternative challenges (audio CAPTCHA, logic puzzles, reCAPTCHA's invisible methods). Single-modality visual CAPTCHA fails accessibility broadly.

### Dynamic visual content (videos, animations)

WCAG 1.2 series covers prerecorded media. For live or auto-generated visual content:

- Provide pause / stop controls.
- Don't auto-play with sound.
- Honor `prefers-reduced-motion`.
- For data visualizations that animate, give a static-state alternative.

## Color contrast: nuances

Contrast is calculated against the *visible* foreground and background. Some traps:

- **Text over images.** The contrast varies by pixel. Fix by adding a semi-opaque scrim, a text-shadow, or a solid background panel.
- **Text over gradients.** Same issue; pick the worst-case spot to measure.
- **Anti-aliased text.** The actual edges of glyphs sub-pixel render and may have lower contrast than the text body. Ensure baseline body color/background pair meets the ratio.
- **Disabled controls.** WCAG explicitly exempts disabled controls from contrast requirements — but the rationale is weak. Aim for at least 3:1 even on disabled, so users can read the disabled state.

## Reflow at 320 px

Test at the iPhone SE / smaller-Android width: 320 CSS pixels. At this width, no horizontal scroll for primary content. Tables and code blocks may scroll horizontally as exceptions.

Common reflow failures:

- Fixed-width containers (e.g., `width: 800px`).
- Columns that don't collapse on narrow screens.
- Tooltips that extend off-screen.
- Modals with fixed pixel widths larger than 320.

## Closing

Perceivable accessibility is the most "checklistable" sub-principle — many of its criteria are programmatically testable. But the gap between passing the checklist and being genuinely perceivable is wide; manual testing with assistive tech catches what automated tools miss.
