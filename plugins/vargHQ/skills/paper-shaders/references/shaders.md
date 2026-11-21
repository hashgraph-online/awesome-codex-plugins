# Shader catalog for video

Paper Shaders 0.0.82 ships 30 shaders. This page sorts them by the job they do in a video. Every shader's page is `https://shaders.paper.design/<slug>`. Exact props, ranges and enum values are in `assets/paper-shaders.params.json` (generated from `https://shaders.paper.design/llms.txt`); the validator reads that file.

"Static" means the shader ignores time: changing `frame` does nothing, so animate it with the timeline (scale, opacity, `paramsAt`) instead of `timeScale`.

## Backgrounds and textures (animated)

| Shader | Slug | Colors | Use in a video |
|---|---|---|---|
| MeshGradient | `mesh-gradient` | up to 10 | The default brand background. timeScale 0.2–0.4 behind text. |
| GrainGradient | `grain-gradient` | up to 7 + colorBack | Grainy print-like gradients in 7 shapes (`wave`, `dots`, `truchet`, `corners`, `ripple`, `blob`, `sphere`). `blob` works as a product backdrop. |
| Warp | `warp` | up to 10 | Marbled fields over `checks`, `stripes` or `edge`. A high timeScale (1.5+) makes a transition. |
| Swirl | `swirl` | up to 10 + colorBack | Spiral bands for intros and hypnotic loops. |
| SimplexNoise | `simplex-noise` | up to 10 | Soft drifting color fields. |
| PerlinNoise | `perlin-noise` | front + back | Organic two-color noise; ink and topography looks. |
| NeuroNoise | `neuro-noise` | front, mid, back | A glowing web of lines for tech backgrounds. |
| Voronoi | `voronoi` | up to 5 + glow + gap | Cells for organic or technical looks. |
| Metaballs | `metaballs` | up to 8 | Merging blobs; playful product launches. |
| DotOrbit | `dot-orbit` | up to 10 | Animated dot fields. |
| ColorPanels | `color-panels` | up to 7 | Translucent 3D panels turning around an axis; premium tech look. |
| Spiral | `spiral` | front + back | Single-color spiral for retro and op-art. |
| Dithering | `dithering` | front + back | Two-ink dithered patterns (`simplex`, `warp`, `dots`, `wave`, `ripple`, `swirl`, `sphere`; type `random`, `2x2`, `4x4`, `8x8`). Mount at `minPixelRatio: 1`. |

## Static backgrounds

| Shader | Slug | Colors | Use in a video |
|---|---|---|---|
| StaticMeshGradient | `static-mesh-gradient` | up to 10 | A still mesh gradient; move it with GSAP or animate its params with `paramsAt`. |
| StaticRadialGradient | `static-radial-gradient` | up to 10 + colorBack | Radial gradient with a movable focal point. |
| Waves | `waves` | front + back | Line-wave pattern. |
| DotGrid | `dot-grid` | fill, stroke, back | Dot grid in `circle`, `diamond`, `square` or `triangle`. Mount at `minPixelRatio: 1`. |

## Light, loaders and frames

| Shader | Slug | Colors | Use in a video |
|---|---|---|---|
| GodRays | `god-rays` | up to 5 + bloom + back | Rays from a point behind a logo or product. Ramp `intensity` and `midIntensity` from 0 with `paramsAt` for a reveal. Alpha in `colors` layers the rays. |
| SmokeRing | `smoke-ring` | up to 10 + back | A smoky ring around a countdown, a loader or a small mark. |
| PulsingBorder | `pulsing-border` | up to 5 + back | A glowing animated border; frames a call to action or an end card. |

## Logo stings (the image is a mask)

These read the logo's alpha, so the logo needs a transparent background. Preprocessing runs once in `ready`.

| Shader | Slug | Colors | Use in a video |
|---|---|---|---|
| LiquidMetal | `liquid-metal` | tint + back | The logo turns to liquid chrome. Without an image it fills `shape` (`none`, `circle`, `daisy`, `diamond`, `metaballs`). A white `colorTint` reads as chrome; a brand tint burns into it. |
| GemSmoke | `gem-smoke` | up to 6 + inner + back | Smoke swirling inside a gem-cut logo or shape. |
| Heatmap | `heatmap` | up to 10 | A heat-map glow traced from the logo. Its preprocessor treats light pixels as background: pass a dark logo on transparent, or the frame stays black. |

## Image filters for stills

They take an image (`HTMLImageElement` or URL), never a `<video>`. Use them on posters, product shots, title cards and photos the user has rights to.

| Shader | Slug | Animated | Use in a video |
|---|---|---|---|
| HalftoneDots | `halftone-dots` | no | Halftone print in two inks or the image's colors; dot `type` `classic`, `gooey`, `holes`, `soft` on a `square` or `hex` grid. |
| HalftoneCmyk | `halftone-cmyk` | no | Four-ink CMYK print (`dots`, `ink`, `sharp`). |
| ImageDithering | `image-dithering` | no | Dithered image in 2–3 inks. Mount at `minPixelRatio: 1`. |
| PaperTexture | `paper-texture` | no | Grain, fibers, folds, wrinkles and drops over an image, or paper alone. |
| FlutedGlass | `fluted-glass` | no | Reeded glass distortion over an image. |
| LensDistortion | `lens-distortion` | no | Chromatic aberration with barrel or pincushion warp. |
| Water | `water` | yes | Caustics over an image, or alone. |

### Footage

Paper's image filters cannot sample video. For real footage in HyperFrames, grade it and add film grain with HyperFrames media treatments (`npx hyperframes media-treatment --capabilities`); for warps of an existing layer use HyperFrames `data-vfx-chain`. Paper shaders belong to the designed layers: backgrounds, stings, textures over graphics and stills.

## Paper's own presets

`assets/presets/paper/` holds all 124 presets Paper ships in `@paper-design/shaders-react` 0.0.82, converted to this skill's format with `origin: "paper"`: 4–6 per shader, named `paper-<slug>-<preset>` (Default, then Paper's names such as Beach, Ink, Passion, Noir, Newspaper). `motion.timeScale` is Paper's `speed`, so motion matches the site. They carry no `roles`; to brand one, copy it and add roles. Image presets expect a still (filters) or a logo (Heatmap); LiquidMetal and GemSmoke fall back to their built-in shapes.

## The nine varg presets

| Preset | Shader | timeScale | Image | Job |
|---|---|---|---|---|
| `brand-mesh` | MeshGradient | 0.3 | none | Background behind titles, cards and lower thirds |
| `grain-blob` | GrainGradient | 0.5 | none | Soft blob backdrop behind a quote or a product |
| `retro-dither` | Dithering | 0.6 | none | Two-ink texture for interstitials and end cards |
| `warp-transition` | Warp | 1.5 | none | 0.5–1 s full-frame interstitial |
| `god-rays-reveal` | GodRays | 0.6 | none | Rays behind a logo as it appears |
| `liquid-metal-sting` | LiquidMetal | 1 | logo, optional | 1–2 s chrome logo sting |
| `smoke-ring-loader` | SmokeRing | 0.5 | none | Ring around a countdown or loader |
| `halftone-overlay` | HalftoneDots | 0 (static) | still, required | Print look for a still |
| `paper-finish` | PaperTexture | 0 (static) | still, optional | Paper finish over a still or title card |

## Writing a new preset

1. Pick the shader from the tables above, then read its props in `assets/paper-shaders.params.json` or on its page.
2. Copy the preset with the closest shader, or start from Paper's defaults, and set **every** param, including the nine sizing params (`fit`, `scale`, `rotation`, `offsetX`, `offsetY`, `originX`, `originY`, `worldWidth`, `worldHeight`). `paper-preset.js` refuses a preset that leaves a uniform unset.
3. Set `motion.timeScale` (the number Paper's editor calls `speed`) and `motion.frame` (the shader time at the scene's first frame, in ms). Static shaders take `timeScale: 0`.
4. Map each color param to a role in `roles` (see `brand-mapping.md`).
5. Run `node scripts/validate-presets.mjs`, check stills with `npx hyperframes snapshot`, then `node scripts/build-manifest.mjs`.
