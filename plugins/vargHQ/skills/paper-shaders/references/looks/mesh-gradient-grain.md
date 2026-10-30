# Mesh gradient with grain

Slow-blending spots of colour with a fine film grain: the default brand background behind titles, product cards, lower thirds and talking-head side panels. 16:9, 9:16 and 1:1; 6–10 s per shot, often the whole video.

## How the pros do it
- Use Paper's MeshGradient: up to 10 colour spots moving on separate trajectories; `distortion` = organic noise warp, `swirl` = vortex warp, `grainMixer` = grain on the shape edges, `grainOverlay` = black-and-white grain on top. [18][19]
- The overlay grain mixes toward pure black or white at 35% of its strength, so `grainOverlay` 0.1–0.2 is already visible; above 0.3 it dominates the colour. [19]
- Order the colours so complementary hues never touch: orange next to blue, or red next to green, blends to brown. Put the dark base between them. [20]
- Four colours are enough for the classic flowing web gradient (Stripe's hero uses #6ec3f4, #3a3aff, #ff61ab, #E63946). [32]
- Speed behind text: timeScale 0.2–0.4. The shader's internal clock is `0.5 × u_time`, so 0.3 gives a drift the eye notices only after a few seconds. Paper's Beach preset ships at 0.1. [19][20]
- Grain also hides banding in long, subtle gradients, but it is the first thing a platform encoder removes; render at the delivery resolution and export at high bitrate. [11][30]
- Paper Shaders are open source and free for commercial use. [1]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Indigo, navy, coral, blush | speed 0.3; colors #3A2BD9 #0B1026 #FF6A3D #F6C7B6; distortion 0.8, swirl 0.1, grainMixer 0.1, grainOverlay 0.15 |
| `dusk` | Plum to peach | speed 0.25; #1B1033 #6B2E8F #F07A5A #FFC79A; distortion 0.9, swirl 0.2, grainMixer 0.15, grainOverlay 0.2 |
| `lagoon` | Aqua and sand | speed 0.15; #BCECF6 #00AAFF #0A3D62 #FFD447; distortion 0.8, swirl 0.35, grainOverlay 0.12 |
| `studio` | Warm off-white for light brands | speed 0.2; #F4F1EC #D9D4CC #B8B2A7 #ECE7DF; distortion 0.6, swirl 0.05, grainOverlay 0.1 |
| `ink` | Black and white ink clouds | speed 0.3; rotation 90; #FFFFFF #000000; distortion 1, swirl 0.2, grainMixer 0.2, grainOverlay 0.2 |

## Timing and numbers
- 10 s background: timeScale 0.15–0.3; interstitial or music bed: 0.5–0.6 (Paper's Purple preset).
- `motion.frame` picks the start state: try 0, 20000 and 60000 ms and keep the still with dark space where the headline goes. Keep offsets under 100,000 ms. [20]
- Text: headline on the darkest quadrant; for `studio` use dark text (#1A1A1A). Run `npx hyperframes check` for WCAG AA. [20]
- Loops: the shader time is not periodic, so a seamless loop of length L needs a 1 s crossfade at the end into a copy whose `motion.frame` is `L × 1000 × timeScale` ms earlier than the main clip's (start the main clip at 60000 ms so the copy stays positive). [19][20]

## Build it
1. Copy the varg `brand-mesh` preset from `vargHQ/skills/paper-shaders`, replace params, or run `apply-brand.mjs` with the client palette (never invent brand colours). [20]
2. HyperFrames host + `paperFrameSource`; Remotion `<ShaderBackground>` with `--gl=angle`. [20]
3. Ready alternatives in the HyperFrames registry: `mesh-gradient` (WebGPU block) or `mesh-gradient-bg` (radial layers, render-safe), plus `grain-overlay`. [39]

## Mistakes that look amateur
- Blue and orange adjacent in `colors` → brown mud in the middle; insert the dark base between them. [20]
- grainOverlay 0.4+ → 0.1–0.2; grain should be felt, not seen. [19]
- Speed 1 behind a lower third → 0.2–0.4. [20]
- Six or more saturated colours → 3–4, one dark anchor. [32]
- Hard cut at the loop point → 1 s crossfade. [19]
- Draft rendered at a different pixel ratio from the final → grain changes size; keep `minPixelRatio` the same. [20]

## Sources
[1] Stephen Haney — Paper Shaders open source — https://x.com/stephenhaney/status/2072369858638233843
[11] Lucas Pope — compression of fine texture on YouTube — https://x.com/dukope/status/1300259933414330368
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt
[19] Paper — mesh-gradient.ts source — https://github.com/paper-design/shaders — `t = .5*(u_time+offset)`, overlay at `.35 * strength`
[20] vargHQ — paper-shaders skill — brand-mesh preset, Paper Beach/Ink/Purple values, complementary-hue rule
[30] Jimmy Chion — Grainy Gradients — https://css-tricks.com/grainy-gradients/
[32] Kevin Hufnagl — Stripe gradient effect — https://kevinhufnagl.com/how-to-stripe-website-gradient-effect/
[39] HeyGen HyperFrames registry — `mesh-gradient`, `mesh-gradient-bg`, `grain-overlay`
