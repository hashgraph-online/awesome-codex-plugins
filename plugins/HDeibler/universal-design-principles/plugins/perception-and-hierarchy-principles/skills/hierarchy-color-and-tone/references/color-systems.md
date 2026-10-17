# Color systems and contrast research

A reference on color hierarchy beyond the practical patterns: the perceptual research underneath, common color-system architectures, and cross-domain examples.

## Perceptual research underpinning

### Why tone (value) is the universal signal

The retina has roughly 120 million rod cells (sensitive to brightness only) and 6 million cone cells (sensitive to color). Brightness perception is faster, more peripheral, and operates in low-light conditions where color perception fails. This is why grayscale photography reads as readily as color, and why a tone-driven hierarchy survives nearly any viewing condition.

WCAG contrast ratios are calibrated against luminance (a photometric measure of brightness), not hue. A hierarchy that works in luminance works in monochrome, in color blindness, and in glare.

### Color blindness statistics

Approximate prevalence in populations of European descent:

- Red-green color blindness (deuteranopia or protanopia): ~8% of men, ~0.5% of women.
- Blue-yellow color blindness (tritanopia): ~0.01% of all populations.
- Total color blindness (achromatopsia): ~0.003%.

Other populations have different rates — generally lower red-green prevalence in some Asian and African populations.

The takeaway: color hierarchy choices must work for ~10% of male viewers who can't distinguish red and green at typical saturations. Pair color with shape, position, or text always.

### Color and emotion

Color perception is partly innate (red attracts attention; blue calms) and partly learned (color associations vary by culture). For software targeting global audiences, lean on the innate effects (warm = energetic, cool = calm) and treat the learned effects as preferences your local audience may have.

## Color system architectures

### The HSL ramp

Modern design systems often define color as **a brand hue plus a neutral ramp**, with semantic variants (success/warning/error) drawn from fixed hues. The HSL color model makes this tractable:

```
neutral-100  hsl(var(--brand-hue), 6%, 96%)
neutral-200  hsl(var(--brand-hue), 6%, 92%)
neutral-300  hsl(var(--brand-hue), 6%, 85%)
…
neutral-900  hsl(var(--brand-hue), 6%, 9%)
```

Tinting neutrals slightly toward the brand hue (here, 6% saturation) makes the whole UI feel cohesive without anyone consciously noticing.

### The OKLCH movement

CSS Color 4 introduces the OKLCH color space, which is *perceptually uniform* — equal numerical jumps correspond to equal perceived jumps. This solves a real HSL problem: at the same lightness value, blues look darker than yellows because human luminance perception varies by hue. Tone ramps in HSL drift unpredictably; OKLCH ramps stay perceptually consistent.

Worth using when your design system needs precise tonal control across hues.

### Material Design's tonal palettes

Material 3 generates 13-stop tonal palettes per color role (primary, secondary, tertiary, error, neutral, neutral-variant). Each palette spans tone 0 to tone 100 with controlled chroma. The system ensures that any role can produce a WCAG-compliant text/background pair.

The architecture is overkill for many products but useful as a reference: it shows what a fully thought-through tone system looks like.

### Apple's semantic colors

Apple's HIG defines colors by *semantic role* (label, secondaryLabel, tertiaryLabel, link, fill, separator, etc.) rather than by name. The OS adjusts the actual values for light/dark mode, accessibility settings, and contrast preferences. Designers don't pick "grey #888"; they pick "secondaryLabel."

This semantic-naming approach is a strong pattern for any product that ships across modes.

## Cross-domain examples

### Wayfinding color codes

The London Underground uses a fixed palette of line colors, applied consistently across maps, station signage, and trains. Each line has a unique hue. Color carries the categorical signal (which line); position and text carry the rest.

This works because the system is **closed and small** (~12 lines). A color system with 50 categories couldn't sustain this.

### Topographic maps

Maps use color to encode altitude (greens for low, browns for high, white for snow). The choice isn't arbitrary — it tracks intuitive associations (vegetation, soil, ice). And the *value* progression (light to dark, or dark to light) carries the magnitude signal even for color-blind viewers.

### Status lights

Traffic-light red/yellow/green is the canonical Western status code. Software status badges inherit it. But: in some Asian contexts, red signals luck/celebration, not stop. A globally-shipped product should pair color status with icon/text.

## Tools

- **Realtime Colors** (realtimecolors.com) — preview a palette across real UI.
- **Stark** (Figma plugin) — contrast checking, color blindness simulation.
- **Coolors** (coolors.co) — palette generation.
- **Adobe Color** — palettes derived from harmony rules; useful for non-monochrome systems.
- **Sim Daltonism** (macOS) and **Color Oracle** (cross-platform) — color blindness simulators.

## Closing

Color is the loudest single dimension a designer commands. Spending it deliberately — and only on things that earn the volume — is what separates polished UIs from noisy ones.
