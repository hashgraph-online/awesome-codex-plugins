# Color accessibility and mode support: deeper reference

A reference complementing `color-accessibility-and-mode` with WCAG details and mode-support patterns.

## WCAG color-relevant criteria

- **1.4.1 Use of Color (A)** — color is not the only visual signal.
- **1.4.3 Contrast (Minimum) (AA)** — body 4.5:1, large/UI 3:1.
- **1.4.6 Contrast (Enhanced) (AAA)** — body 7:1, large/UI 4.5:1.
- **1.4.11 Non-text Contrast (AA)** — UI components and graphical objects need 3:1.
- **1.4.13 Content on Hover or Focus (AA)** — hover-revealed content must be dismissable, hoverable, persistent.

The non-text contrast requirement (1.4.11, added in WCAG 2.1) is often missed. Form-field borders, icon buttons, focus rings, and chart elements all need 3:1 against their immediate background.

## Common contrast failures

- **Light grey body text on white.** `#999` on white = 2.85:1. Fails AA. Common in "minimalist" designs.
- **Brand-color body links on white.** Many brand blues fall in the 3.5–4:1 range — passes for large/UI, fails for body.
- **Placeholder text** in inputs is frequently below 3:1; the field's accessible name needs to clear contrast.
- **White text on light brand backgrounds.** A brand at 50% lightness with white text often misses 4.5:1.
- **Disabled controls.** Often under 3:1; WCAG exempts them but users can't read them anyway.

## Tools

- **WebAIM Contrast Checker** — webaim.org/resources/contrastchecker.
- **Chrome DevTools** — Elements panel, contrast inspector for any element.
- **Stark** — Figma plugin and browser extension.
- **OKLCH color picker** (oklch.com) — interactive contrast checking in OKLCH space.

## Color-blindness simulation

Tools:

- **Chrome DevTools** → Rendering → Emulate vision deficiencies.
- **Sim Daltonism** (macOS).
- **Color Oracle** (cross-platform).
- **Stark** — built-in color-blindness simulation.

Test status systems particularly. Red/green distinction collapses in deuteranopia simulation; if your "Active" and "Failed" states only differ in hue, they look identical to ~6% of male users.

## Dark mode patterns

### Pure inversion is wrong

Inverting a light palette doesn't produce a good dark palette. A few reasons:

- Saturated colors that work on white look glaring on dark.
- Pure white text on pure black causes "halation" (perceived blur) on OLED screens.
- Brand colors often need adjustment to retain identity in dark mode.

### Tinted backgrounds

Most well-tuned dark modes use:

- A near-black (not pure black) background: `hsl(220 10% 8%)` rather than `#000`.
- Off-white text: `hsl(0 0% 90%)` rather than `#fff`.
- Tinted neutrals matching the light-mode hue cast.

### Adjust saturation

Saturated brand colors that work on white need toning down for dark:

```css
:root {
  --primary: hsl(220 90% 50%);
}

@media (prefers-color-scheme: dark) {
  :root {
    --primary: hsl(220 70% 60%);  /* less saturated, slightly lighter */
  }
}
```

### Test contrast in both modes

WCAG ratios apply to whatever's actually rendered. A pair that passes in light may fail in dark.

## High-contrast / forced-colors mode

Two related but distinct preferences:

- `prefers-contrast: more` — user requests more contrast; respect by tightening color differences.
- Forced Colors Mode (Windows) — user has overridden page colors entirely with system colors.

In forced colors mode, the browser maps your colors to system tokens (`Canvas`, `CanvasText`, `LinkText`, `ButtonText`, `ButtonFace`, etc.). Backgrounds may be hidden entirely. Design implications:

- Don't rely on background images for critical info.
- Use `<button>` for buttons; the system maps them correctly.
- Test in Microsoft Edge with High Contrast mode toggled.

## Reduced motion

WCAG 2.3.3 — respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

For motion that's *meaningful* (state change indicator), allow a brief, subtle version even in reduced-motion mode.

## Resources

- **W3C WCAG** — w3.org/WAI/WCAG22.
- **WebAIM** — webaim.org. Practitioner-focused; includes the contrast checker.
- **MDN: prefers-color-scheme, prefers-contrast, prefers-reduced-motion** — current browser support.
- **Inclusive Components** (Heydon Pickering) — accessible color patterns.
