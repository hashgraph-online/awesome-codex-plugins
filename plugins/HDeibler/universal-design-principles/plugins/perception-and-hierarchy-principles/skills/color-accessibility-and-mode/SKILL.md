---
name: color-accessibility-and-mode
description: 'Use this skill when designing color systems that must satisfy accessibility requirements, work in both light and dark modes, support high-contrast preferences, and remain meaningful for users with color blindness or low vision. Trigger when picking text colors, designing for global compliance (WCAG, EAA, ADA), supporting dark mode, or auditing an existing palette for accessibility. Sub-aspect of `color`; read that first.'
---

# Color: accessibility and mode support

Accessibility-aware color isn't a polish layer; it's a constraint that shapes the palette from the start. Adding accessibility late is much more expensive than building it in. The core constraints: WCAG contrast ratios, color-blindness compatibility, high-contrast mode support, and dark-mode parity.

## WCAG contrast in practice

Required ratios (relative luminance):

| Content | Level AA | Level AAA |
|---|---|---|
| Body text (< 18pt regular or < 14pt bold) | 4.5:1 | 7:1 |
| Large text (≥ 18pt regular or ≥ 14pt bold) | 3:1 | 4.5:1 |
| UI components and graphical objects | 3:1 | (no AAA) |

To check a color pair: any contrast tool (WebAIM, Stark, Chrome DevTools' contrast inspector). If you're picking from a designer's mockup, run every text/background pair through. Common failures:

- Light grey body text on white (`#999` or `#aaa`).
- Brand-color body links on white when the brand is mid-tone.
- Placeholder text in inputs (often unreadable).
- White text on light brand backgrounds.

**Practical rule**: pick body text colors at neutral-700 or darker on light backgrounds; never use anything lighter than neutral-500 for content the user must read.

## Color blindness

Approximate prevalence in populations of European descent:

- **Deuteranopia / deuteranomaly** (red-green): ~6% of men, ~0.4% of women.
- **Protanopia / protanomaly** (red-green, slightly different): ~2% of men.
- **Tritanopia / tritanomaly** (blue-yellow): ~0.01%.
- **Achromatopsia** (full color blindness): ~0.003%.

Other populations have different rates — generally lower red-green prevalence in some Asian populations.

Practical implications:

- Don't rely on red-green distinction alone for status. Use icon, text, or pattern alongside.
- Avoid red-on-green or green-on-red combinations for important text.
- Test with simulators: Chrome DevTools → Rendering → Emulate vision deficiencies. Or Stark, Sim Daltonism, Color Oracle.

## Dark mode

Dark mode is no longer optional for new products. Macs, iPhones, and Androids all default to dark in some contexts; users expect it.

Common pitfalls:

### Pure inversion is wrong

Inverting a light palette doesn't produce a good dark palette. Saturation perception is different on dark backgrounds; very-saturated colors that read fine on white look glaring on black. Build dark-mode tokens deliberately.

### Tinted neutrals work better than pure black

Pure white text on pure black is high-contrast but hard on the eyes and produces strong "halation" (blur) on OLED screens. Most well-tuned dark modes use:

- A near-black background (not pure black): `hsl(220 10% 8%)`.
- Off-white text: `hsl(0 0% 90%)` or so.
- Tinted neutrals keeping the same hue cast as light mode.

### Adjust saturation downward

Saturated colors that work on white backgrounds need toning down for dark. A primary brand at `hsl(220 90% 50%)` may need to be `hsl(220 70% 60%)` in dark mode to feel comfortable.

### Test contrast in both modes

A pair that passes AA in light mode may fail in dark mode. The luminance values differ; recheck.

## High-contrast mode

Many operating systems offer a high-contrast mode for low-vision users. Web equivalents:

- **Windows High Contrast Mode** (now "contrast themes")
- **`prefers-contrast: more`** CSS media query

In these modes, the user has explicitly requested maximum contrast. Designs should:

- Avoid relying on subtle color distinctions.
- Ensure all text/background pairs hit AAA contrast.
- Avoid background images or gradients that might obscure text.
- Use strong, defined borders.

```css
@media (prefers-contrast: more) {
  :root {
    --neutral-700: hsl(0 0% 0%);
    --background: hsl(0 0% 100%);
    --border: hsl(0 0% 0%);
    /* ...etc... */
  }
}
```

## Forced colors mode

Some users (particularly with low vision or migraine sensitivity) override page colors entirely with system colors via Windows' Forced Colors Mode. The browser maps your colors to a small set of system tokens (`Canvas`, `CanvasText`, `LinkText`, `ButtonText`, `ButtonFace`, etc.).

In this mode:

- Background images may be hidden.
- Custom colors are overridden.
- The page should still be usable.

Design implications:

- Use `<button>` for buttons; the system colors map correctly.
- Don't rely on background images for critical info.
- Test in Forced Colors Mode (Edge: Settings → Accessibility → "High contrast").

## Color and motion / animation

Color transitions can trigger photosensitive epilepsy if they flash rapidly (3+ Hz, especially with red). WCAG 2.3.1: no content flashes more than 3 times per second.

Design implications:

- No strobing animations.
- Loading spinners should rotate, not flash colors.
- Auto-playing animations should respect `prefers-reduced-motion`.

## Worked example: a fully accessibility-aware palette

```css
:root {
  /* Light mode */
  --bg: hsl(0 0% 100%);
  --fg: hsl(220 6% 12%);          /* near-black; contrast 17:1 on white */
  --fg-muted: hsl(220 6% 40%);    /* 7.4:1 — passes AA body, AAA large */
  --primary: hsl(220 90% 45%);    /* 5:1 on white — AA body */
  --destructive: hsl(0 75% 40%);  /* 5.5:1 on white — AA body */
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: hsl(220 10% 9%);
    --fg: hsl(220 6% 92%);          /* 12:1 on dark */
    --fg-muted: hsl(220 6% 65%);    /* 5.5:1 — AA body */
    --primary: hsl(220 80% 65%);    /* tuned brighter for dark mode */
    --destructive: hsl(0 70% 60%);  /* tuned brighter for dark mode */
  }
}

@media (prefers-contrast: more) {
  :root {
    --fg: hsl(0 0% 0%);
    --bg: hsl(0 0% 100%);
    --fg-muted: hsl(0 0% 20%);
    /* etc. */
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Anti-patterns

- **Color-only signals.** Red asterisks for required fields with no `*` or "required." Color-blind users miss it.
- **Light grey body text** that looks "elegant" in mockups but fails AA in production.
- **Dark mode by inversion.** Pure inversion produces glare and saturation issues.
- **Ignoring `prefers-contrast` and `forced-colors`.** Your design works for typical users but fails for users with explicit accessibility needs.
- **Status that depends on hue alone.** Color-blind users can't distinguish red from green; pair with icon and text.

## Heuristics

1. **Run a contrast checker.** Every text/background pair, every UI/background pair. AA at minimum.
2. **Simulate color blindness.** Chrome DevTools or a dedicated tool. Status systems that lean on red/green collapse here.
3. **Test in dark mode.** Toggle the OS preference; check every page.
4. **Test with forced colors.** Edge in High Contrast mode reveals what depends on color.
5. **The grayscale test.** If the design works in grayscale, color is enhancement; if not, color is load-bearing and must satisfy accessibility constraints.

## Related sub-skills

- **`color`** (parent).
- **`color-semantic-systems`** — building the semantic layer this skill makes accessible.
- **`hierarchy-color-and-tone`** — using tone (not just hue) for hierarchy.
- **`accessibility-perceivable`** (process) — covers color contrast and other perceivable concerns.
