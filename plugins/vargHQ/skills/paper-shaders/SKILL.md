---
name: paper-shaders
description: >-
  Turns Paper Shaders (30 WebGL shaders: mesh and grain gradients, god rays, liquid metal,
  smoke ring, dithering, halftone, paper texture and more) into frame-exact backgrounds,
  textures and logo stings for HyperFrames or Remotion videos, in brand colors, with nine
  tested presets and 11 researched looks (liquid metal field, god rays, mesh and grain
  gradients, dithered gradient, marbled ink, paper, contour lines, hand-drawn burst, gradient flow,
  datamosh rain) with numbers from Inigo Quilez, Paper's designers and Lucas Pope. Every frame is drawn from timeline time, so renders are seekable, parallel
  and repeatable, and spend no varg credits. Use when a video needs an animated shader
  background, a grain, dither, halftone or paper look on graphics or stills, or a logo reveal
  or sting. NOT for generating footage (use varg-ai), grading or film grain on real footage
  (HyperFrames media treatments), warping existing layers (HyperFrames data-vfx-chain),
  3D scenes (a Three.js skill) or shaders for websites.
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes, which brings Chrome; needs Node 22 and ffmpeg) or
  Remotion 4 rendered with --gl=angle. Paper Shaders 0.0.82 from npm or jsDelivr.
  Scripts run on Node 22 or Bun. No API key.
allowed-tools: Bash(node:*) Bash(bun:*) Bash(npx:*) Bash(ffmpeg:*) Read Write Edit
metadata:
  author: vargHQ
  version: "0.2.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "about 1 s of render per second of 1080p video on an M1 Pro"
  varg.models: "none"
  varg.refs.manifest: "assets/refs.manifest.json"
  varg.outputs: "mp4, webm, mov, gif or png sequence from HyperFrames or Remotion"
  paper-shaders.version: "0.0.82"
  hyperframes.version: "0.8.206"
---

# Paper Shaders for video

Paper Shaders draws designer-tuned WebGL shaders into a canvas. Left alone it animates from the wall clock, which flickers and drifts in a video render. This skill mounts every shader at speed 0 and draws each frame from the timeline, so the same frame always gives the same picture.

## Gates

1. **Pin `@paper-design/shaders@0.0.82`.** Use that exact version everywhere. Never use 0.0.47–0.0.76: they are PolyForm Shield, not open source. Bumping the version follows `references/licensing.md`.
2. **Speed 0, time from the timeline.** Mount shaders only through `templates/paper-preset.js`. Never set `speed` above 0, and never let scene code read `Date.now()`, `performance.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
3. **No credits here.** Shader layers render locally for free. If the video also needs generated footage, voice or music, that is the varg-ai skill: call `estimate_cost` and wait for the user's approval before any generation.
4. **Rights.** Logos and stills fed to image presets must be the user's own or licensed. Do not apply a shader to another company's logo.
5. **Stills, not footage.** Paper's image filters take images only. Grade and add grain to footage with HyperFrames media treatments instead.

## Workflow

A person approves at each checkpoint (looks, stills, motion) before the next step. Commands run from the skill folder; `HF` stands for the pinned CLI, `npx --yes hyperframes@0.8.206`.

1. **Pick the look.** Match the request to a preset below or to a shader in `references/shaders.md`. Say which one and why in one line; that is checkpoint 1.
2. **Scaffold, or add to a project.**
   ```bash
   node scripts/new-project.mjs ./video                 # new HyperFrames project from the template
   node scripts/new-project.mjs ./existing --add        # paper-preset.js and presets/ only
   ```
3. **Brand it.** Get the palette from the user or their brand kit. Never invent colors. Write the branded preset into the project, then import it in `index.html`. Image presets take `{ image: "assets/logo.png" }`; serve images from the project.
   ```bash
   node scripts/apply-brand.mjs assets/presets/brand-mesh.json palette.json --out ./video/presets/brand-mesh.json
   node scripts/validate-presets.mjs ./video/presets/brand-mesh.json
   ```
4. **Stills (checkpoint 2).** `$HF snapshot ./video --at 0.5,2,4` writes PNGs and a contact sheet. Show them; change one param at a time until approved.
5. **Motion (checkpoint 3).** `(cd ./video && $HF render --quality draft --output draft.mp4)`. Tune `motion.timeScale` for pace.
6. **Final.**
   ```bash
   node scripts/check-determinism.mjs ./video                        # must print "deterministic"
   (cd ./video && $HF check && $HF render --output final.mp4)        # or: npm run check, npm run render
   ```

## A shader layer in HyperFrames

The host is a timed clip with its own composition id and no GSAP timeline. HyperFrames calls `render(seconds)` for every frame it captures, in any order.

```html
<div id="bg" class="clip" data-composition-id="bg" data-start="0" data-duration="6"
     data-track-index="0" data-no-timeline data-layout-allow-overflow></div>

<script type="module">
  import * as PS from "https://cdn.jsdelivr.net/npm/@paper-design/shaders@0.0.82/dist/index.js";
  import { paperFrameSource } from "./paper-preset.js";
  import preset from "./presets/god-rays-reveal.json" with { type: "json" };

  const ramp = (t) => 1 - Math.pow(1 - Math.min(t / 1.2, 1), 3);
  window.__hyperframes.registerFrameSource(
    paperFrameSource(PS, document.getElementById("bg"), preset, {
      paramsAt: (t) => ({ intensity: 0.8 * ramp(t), bloom: 0.4 * ramp(t) }), // a reveal, as a pure function of time
    }),
  );
</script>
```

- Register at the top level of a module script, before any `await`; HyperFrames boots on `DOMContentLoaded`.
- Each shader scene needs its own host. Keep a composition under about 12 shader hosts; Chrome drops WebGL contexts past 16. For more looks in a row, use `paperSequenceSource`: one host, one context, any number of presets (see `examples/paper-gallery`).
- Text, logos and other DOM elements go on higher tracks and animate with the GSAP timeline as usual.
- `templates/hyperframes/shader-background.html` is a complete composition to start from.

## A shader layer in Remotion

```bash
npm i @paper-design/shaders@0.0.82
# copy templates/paper-preset.js, templates/paper-preset.d.ts, templates/remotion/ShaderBackground.tsx and the presets
```

```tsx
<ShaderBackground preset={brandMesh}>
  <h1>Headline</h1>
</ShaderBackground>
<ShaderBackground preset={liquidMetal} image={staticFile("logo.svg")} />
```

Render with `npx remotion render <id> out.mp4 --gl=angle`. Do not use Paper's React components for renders; see `references/determinism.md`.

## Presets

Two sets ship. Nine varg presets in `assets/presets/`, in varg colors with brand roles. And all 124 of Paper's own presets in `assets/presets/paper/` (`paper-<shader>-<name>`, for example `paper-mesh-gradient-beach`, `paper-warp-passion`), with the colors and speeds shown on shaders.paper.design. When the user wants "the look from Paper's site", start from those. All are validated against Paper's documented ranges; five of Paper's own go past the editor's slider ranges and stay as Paper ships them.

| Varg preset | Shader | Use |
|---|---|---|
| `brand-mesh` | MeshGradient | Background behind titles, product cards and lower thirds |
| `grain-blob` | GrainGradient | Soft grainy blob behind a quote, a product or a speaker |
| `retro-dither` | Dithering | Two-ink texture for interstitials and end cards |
| `warp-transition` | Warp | 0.5–1 s full-frame interstitial between scenes |
| `god-rays-reveal` | GodRays | Rays behind a logo as it appears (ramp with `paramsAt`) |
| `liquid-metal-sting` | LiquidMetal | 1–2 s chrome logo sting; needs a transparent logo |
| `smoke-ring-loader` | SmokeRing | Ring around a countdown, a loader or a mark |
| `halftone-overlay` | HalftoneDots | Print look for a still (needs the still) |
| `paper-finish` | PaperTexture | Paper grain and folds over a still or title card |

A preset is JSON: `shader`, `motion` (`timeScale`, `frame`), optional `mount` and `image` notes, `roles` for brand mapping, and every param. `paper-preset.js` refuses a preset that leaves a uniform unset rather than render a wrong frame.

## Looks: 11 researched backgrounds

Eleven background looks researched from the people who build these shaders, each with 4-5 presets in exact Paper params (checked with `validate-presets.mjs`) or, where Paper has no shader for it, a custom GLSL skeleton with its numbers. Each look has a reference (how the pros do it, presets, timing, build steps, mistakes, sources) in `references/looks/` and its presets in `assets/looks/` (50 presets). The look files use their own schema: a preset's `params.paper` block is what goes into a varg preset JSON, with `params.motion` as its `motion`.

| Look | Shader | Presets | Files |
|---|---|---|---|
| **Contour lines** | custom-glsl | Signature, Survey, Night, Blueprint | [`contour-lines.md`](references/looks/contour-lines.md) · [`json`](assets/looks/contour-lines.json) |
| **Datamosh rain** | custom-glsl | Signature, Datamosh, Phosphor, Ember, Ice | [`datamosh-rain.md`](references/looks/datamosh-rain.md) · [`json`](assets/looks/datamosh-rain.json) |
| **Dithered gradient** | Dithering | Signature, Newsprint, Riso, Phosphor | [`dithered-gradient.md`](references/looks/dithered-gradient.md) · [`json`](assets/looks/dithered-gradient.json) |
| **God-ray light field** | GodRays | Overhead, Off-center, Streaks, Photograph, Bright core | [`god-ray-light-field.md`](references/looks/god-ray-light-field.md) · [`json`](assets/looks/god-ray-light-field.json) |
| **Gradient flow** | Warp | Signature, Chroma, Ember, Aurora, Mono | [`gradient-flow.md`](references/looks/gradient-flow.md) · [`json`](assets/looks/gradient-flow.json) |
| **Grain gradient** | GrainGradient | Signature, Riso, Ember, Sage, Night | [`grain-gradient-shapes.md`](references/looks/grain-gradient-shapes.md) · [`json`](assets/looks/grain-gradient-shapes.json) |
| **Hand-drawn radial burst** | custom-glsl | Signature, Print, Negative, Riso | [`hand-drawn-radial-burst.md`](references/looks/hand-drawn-radial-burst.md) · [`json`](assets/looks/hand-drawn-radial-burst.json) |
| **Liquid metal field** | LiquidMetal | Signature, Chrome, Noir, Gold | [`liquid-metal-field.md`](references/looks/liquid-metal-field.md) · [`json`](assets/looks/liquid-metal-field.json) |
| **Marbled ink** | Warp | Signature, Ink, Ember, Sage | [`marbled-ink.md`](references/looks/marbled-ink.md) · [`json`](assets/looks/marbled-ink.json) |
| **Mesh gradient with grain** | MeshGradient | Signature, Dusk, Lagoon, Studio, Ink | [`mesh-gradient-grain.md`](references/looks/mesh-gradient-grain.md) · [`json`](assets/looks/mesh-gradient-grain.json) |
| **Paper texture** | PaperTexture | Signature, Kraft, Newsprint, Poster, Print | [`paper-texture.md`](references/looks/paper-texture.md) · [`json`](assets/looks/paper-texture.json) |

Rules for every look:

1. Mount every shader at speed 0 and compute the frame from timeline seconds; custom shaders get `u_t = seconds` only.
2. Speed is shader-specific (internal clocks differ: Mesh 0.5x, GodRays 0.2x, Grain 0.1x, Warp 0.0625x). Behind text: Mesh 0.15–0.3, GodRays 0.25–0.6, Grain 0.3–0.5, Warp 0.8–1.5, LiquidMetal 0.4–0.7.
3. Paper time is not periodic: loop with a 1 s crossfade into a copy offset by L × 1000 × timeScale ms.
4. Grain and dither are what platform encoders destroy: render at delivery resolution, ≥3–4 px dither cells and ≥8 px blocks at 1080p, high bitrate.
5. Never move or scale a dither grid; animate the source under a screen-fixed grid.
6. Keep complementary hues apart in colour order (dark base between); 3–4 colours plus one dark anchor.
7. Print looks: two inks, riso or warm CMYK hex (#FF48B0, #0078BF, #FFE800, #231F20 on #FBFAF4), 2–4 px misregistration with multiply.
8. Hand-drawn or glitch feel comes from stepped time: boil at 8–12.5 fps, re-roll glitch blocks at 12.5 fps, keep the main motion smooth.
9. Constant-width procedural lines need distance estimation (|f|/|∇f| via fwidth), not raw thresholds.
10. Domain-warped fBM (gain 0.5, 5 octaves, 0.5 rad octave rotation, IQ offsets) is the base of marble, terrain and organic flow.

Built from: Inigo Quilez; Paper's Ksenia Kondrashova (@uuuuuulala) and Stephen Haney (@stephenhaney); Lucas Pope (@dukope); Surma (Ditherpunk); Patricio Gonzalez Vivo & Jen Lowe (The Book of Shaders); Mirza Beig (@TheMirzaBeig); Rune Skovbo Johansen (@runevision); Xor; Kenny Mitchell. Sources with links: [`references/looks/sources.md`](references/looks/sources.md).

## Read this when

| When | Read |
|---|---|
| Choosing a shader, writing a new preset, working with footage | `references/shaders.md` |
| Frames flicker, go black or differ between workers; offline, 4K or Docker renders; Remotion details | `references/determinism.md` |
| Applying a palette, text contrast over a shader | `references/brand-mapping.md` |
| A named look (liquid metal field, god rays, marbled ink, contour lines, datamosh rain …) or its expert numbers | `references/looks/<look>.md` and `assets/looks/<look>.json` |
| Bumping the Paper Shaders version, vendoring it, credits, client work | `references/licensing.md` |

## Scripts

All run with `node` or `bun`, make no network calls of their own, and touch only the paths you give them.

| Script | Does |
|---|---|
| `new-project.mjs <dir> [--example preset-reel\|paper-gallery] [--add]` | Scaffolds a HyperFrames project, or adds `paper-preset.js` and `presets/` to one |
| `validate-presets.mjs [files]` | Checks presets against the documented params, ranges, enums and color limits |
| `apply-brand.mjs <preset> <palette>` | Maps a palette onto a preset through its `roles` |
| `check-determinism.mjs <project> [--at …] [--software]` | Snapshots forwards and backwards in two runs and compares pixels (uses `npx hyperframes`) |
| `build-manifest.mjs` | Rewrites `assets/refs.manifest.json` after a preset changes |
| `refresh-params.mjs <llms.txt> <version>` | Rebuilds `assets/paper-shaders.params.json` when the pinned version changes |

## Output contract

- **Project:** `index.html`, `paper-preset.js`, `presets/*.json` (the branded presets actually used), `package.json` and `hyperframes.json` with the HyperFrames version pinned.
- **Stills:** the snapshot folder with its `contact-sheet.jpg`, shown at checkpoint 2.
- **Video:** `renders/<name>.mp4` or the `--output` path; 1920×1080 at 30 fps unless asked otherwise.
- **Report:** the video path, duration and size; which presets ran with which changed params; and the `check-determinism.mjs` result.

## Examples

`examples/paper-gallery/` plays all 124 of Paper's presets, 2 s each, full frame, through one host (`--example paper-gallery`, about 4 minutes of video).

`examples/preset-reel/` shows all nine varg presets, 2.5 s each, at 1920×1080 and 30 fps, with a frame counter that is itself a frame source. Posters and the logo are drawn in code, so it needs no outside media. A contact sheet is in `assets/previews/preset-reel.webp`.

```bash
node scripts/new-project.mjs ./preset-reel --example preset-reel
cd preset-reel && npm run render -- --output preset-reel.mp4   # pinned HyperFrames; about 22 s on an M1 Pro
```

`hyperframes check` passes; lint's structure warnings come from keeping the reel in one file to read.
