# Brand mapping

Every preset names the job of each color in a `roles` map, so a brand palette can replace the varg colors without hand-editing hex values.

## Roles

| Role | Meaning | varg default |
|---|---|---|
| `base` | The ground color: the darkest color of a dark brand, the lightest of a light one | `#070708` |
| `ink` | Text and line color on `base` | `#ffffff` (dark brands), `#070708` on paper |
| `accent` | The main brand color | `#ff5315` |
| `accent-light` | A lighter tint of the accent, or the second brand color | `#ff9a5c` |
| `deep` | A dark secondary that adds depth | `#24124f` |
| `paper` | A warm light neutral for print looks | `#f4efe6` |
| `shadow` | The color of paper grain, folds and fibers | `#9c8a70` |
| `highlight` | Speculars and chrome; usually white | `#ffffff` |

`accent@0.48` means the accent at 48% alpha. Paper colors accept `#rrggbbaa`; GodRays uses alpha to layer its rays.

## Applying a palette

Ask for the brand's colors, or read them from a brand kit the user provides (a varg Studio brand kit, a design file, a style guide). Do not invent a palette: an unknown color stays the preset's.

```json
{ "base": "#0b0b0f", "ink": "#ffffff", "accent": "#3b5bfd", "accent-light": "#8ea2ff", "deep": "#1b1446" }
```

```bash
node scripts/apply-brand.mjs assets/presets/brand-mesh.json palette.json --out presets/brand-mesh.json
node scripts/validate-presets.mjs presets/brand-mesh.json
```

The script lists the roles the palette did not cover; those keep the preset's colors. Pass `--id` to save the branded copy under a new name.

## Rules that keep it on brand

1. **Text stays readable.** Put headlines over the `base`-heavy part of the frame, or move the shader with `offsetX`/`offsetY`/`scale` (the preset reel moves `grain-blob` right to clear room for a quote). `npx hyperframes check` measures WCAG AA contrast for every text element; fix what it flags.
2. **Keep complementary hues apart.** Orange next to blue, or red next to green, blends to brown in MeshGradient and Warp. Put `base` or `deep` between them in the `colors` order, or lower `distortion`.
3. **Two inks for print looks.** Halftone, dithering and two-color noise read as print with `ink` on `paper` or `accent` on `base`. A third ink usually muddies them.
4. **Mind the color limits.** MeshGradient, Warp, Swirl, SimplexNoise, SmokeRing, DotOrbit, Heatmap and the static gradients take up to 10 colors; GrainGradient and ColorPanels 7; Metaballs 8; GemSmoke 6; GodRays, Voronoi and PulsingBorder 5.
5. **Light brands invert the roles.** For a light brand, `base` becomes the paper tone and `ink` the dark color. Keep `deep` dark so the shader keeps its depth.
6. **Chrome stays neutral.** LiquidMetal reads as metal with a white `colorTint`; a strong brand tint turns it into colored plastic. Put the brand in the background or the wordmark instead.
