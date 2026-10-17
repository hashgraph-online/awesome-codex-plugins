# Color theory, perception, and modern color systems

A reference complementing the `color` SKILL.md with deeper grounding in color science and modern color-system architectures.

## A short history of color theory

- **Newton** (1672) — first systematic color wheel; demonstrated white light decomposes into a spectrum.
- **Goethe** (1810) — *Theory of Colours*; emphasized perceptual and psychological dimensions over physical optics. Influential in art and design even where the physics was wrong.
- **Helmholtz, Maxwell, Hering** (mid-late 19th century) — trichromacy and opponent-process theories of color perception, both partly correct and now combined in modern accounts.
- **Itten and Albers** (Bauhaus, mid-20th century) — color theory for designers, focused on perceptual relationships, simultaneous contrast, and color interaction.
- **CIE color spaces** (1931 onward) — mathematical models of color perception that underlie modern color management.
- **OKLCH and modern perceptual color spaces** (2020s) — the CSS Color 4 spec brought perceptually-uniform color spaces into web design tools.

## Color perception basics

The human retina has three types of cone photoreceptors, sensitive to overlapping ranges of long, medium, and short wavelengths (roughly red, green, blue). The brain combines these signals into perceived colors.

Key perceptual phenomena:

- **Simultaneous contrast** — a color appears different against different backgrounds. Albers's *Interaction of Color* documented this exhaustively.
- **Color constancy** — the brain maintains stable color perception across changing illumination. Why a white shirt still "looks white" in tungsten and daylight.
- **Adaptation** — prolonged exposure to a color shifts perception of subsequent colors (the "afterimage" effect).
- **Brightness vs. luminance** — perceived brightness is not linearly related to physical luminance; this is why pure yellow looks bright and pure blue looks dark at the same measured luminance.

These matter because color systems built on physical metrics (RGB, HSL) often produce visually uneven results across hues. OKLCH addresses this by being perceptually uniform.

## RGB, HSL, OKLCH

### RGB / Hex

The lowest-level web color model. Each channel 0–255 (or 0–FF). Easy to implement; hard to think in.

```css
color: rgb(220, 38, 127);
color: #DC267F;
```

### HSL

Hue (0–360°), Saturation (0–100%), Lightness (0–100%). Easier for designers; perceptually problematic — equal lightness values across hues don't look equally light.

```css
color: hsl(335 75% 50%);
```

### OKLCH

Perceptually uniform. L (lightness), C (chroma), H (hue). Equal L values across hues look equally light. Available in modern browsers via CSS Color 4.

```css
color: oklch(60% 0.18 350);
```

For new systems where you control the spec, OKLCH is the future. For existing systems, HSL is fine as long as you tune lightness per hue (don't assume `hsl(220 90% 50%)` and `hsl(40 90% 50%)` are equally light — they aren't).

## Color-system architectures

### Material Design's tonal palettes

Material 3 generates 13-stop tonal palettes per role (primary, secondary, tertiary, error, neutral). Each palette spans tone 0 to tone 100 with controlled chroma. Ensures WCAG contrast can be hit between any two stops at known tone differences.

### Apple's semantic colors

Apple's HIG defines colors by semantic role (`label`, `secondaryLabel`, `tertiaryLabel`, `link`, `fill`, `separator`). The OS adjusts actual values per appearance mode and accessibility setting.

### Tailwind's neutral and color scales

Tailwind ships 11-stop color scales (50–950) for neutrals and many hues. Each step is approximately 10% lightness apart. Wide adoption has made these stops a de facto convention.

### Design-token systems

The W3C Design Tokens Community Group is standardizing token formats (color, spacing, typography). Tools like Style Dictionary translate JSON tokens to per-platform format (CSS variables, iOS, Android).

## Cultural and contextual color

Color symbolism varies by culture. A few well-documented variations:

| Color | Western | East Asian | South Asian | African (varies) |
|---|---|---|---|---|
| Red | Stop, danger, urgent | Luck, prosperity, celebration | Marriage, purity | Mourning (some) |
| White | Purity, weddings | Mourning, funerals | Mourning | Varies |
| Black | Authority, formality | Knowledge, formality | Mourning | Maturity, wisdom |
| Green | Go, nature, money | Infidelity (Chinese) | Faith (Muslim) | Health |
| Yellow | Caution, warmth | Sacred, royalty (some) | Sacred | Mourning (some) |

For products serving global audiences, don't lean on color symbolism alone. Pair with icon and text.

## Resources

- **Albers, J.** *Interaction of Color* (1963). Required reading.
- **Itten, J.** *The Art of Color* (1961).
- **Stone, M.** *A Field Guide to Digital Color* (2003). Practical color science for screens.
- **W3C CSS Color Module Level 4** — modern color-space spec.
- **WebAIM Contrast Checker** — most-used contrast tool.
- **OKLCH color picker** (oklch.com) — for working in OKLCH.

## Closing

Color rewards study. The principles in this plugin set are the operational layer; deeper investment in Albers, modern color science, and design-system color architecture pays off across every product you ship.
