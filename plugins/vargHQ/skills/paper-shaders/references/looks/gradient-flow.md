# Gradient flow

Saturated colour that blooms and folds through a flowing gradient: an energetic opener, a music bed, a product hero backdrop or a 0.5–1 s transition. 16:9, 9:16 and 1:1; 8–11 s as a background.

## How the pros do it
- Use Paper's Warp with `softness: 1` for smooth folds: colours (up to 10) over a base `checks`, `stripes` or `edge` pattern, bent by `distortion` and `swirl` × `swirlIterations`. Paper's co-founder introduced it as the shader for flowing colour fields. [3][18]
- Warp's internal clock is `0.0625 × (u_time + offset)`: timeScale 0.8–1.2 is a slow background, 1.5+ makes a transition, Paper's Nectar ships at 4.2. [19][20]
- `edge` + `offsetY 0.6` + `scale 2` makes colour rise from the bottom like heat (Paper's Nectar structure). [20]
- Order colours so complementary hues are separated by a third colour (violet between cyan and yellow, the dark base between orange and blue), or the mixes go brown. [20]
- Four colours are the classic web flowing gradient (Stripe uses #6ec3f4, #3a3aff, #ff61ab, #E63946). [32]
- If you need palette cycling in custom code, IQ's cosine palette `a + b·cos(2π(c·t + d))` with integer c cycles seamlessly. [24]
- Paper time is not periodic. For a seamless loop of length L, crossfade frame(t) with frame(t − L) over the last 1 s. [19]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Violet, hot pink, apricot on indigo | Warp, speed 1.0; #1A0B3D #5B2BFF #FF4FA3 #FFB36B; proportion 0.45, softness 1, distortion 0.25, swirl 0.8, iterations 10, checks, shapeScale 0.1 |
| `chroma` | Full-saturation bands, separated by violet | speed 1.2; #00E0FF #7A00FF #FF00A8 #7A00FF #FFE600; proportion 0.5, softness 1, distortion 0.2, swirl 0.7, iterations 8, stripes, shapeScale 0.35 |
| `ember` | Molten reds rising from the bottom | speed 2.0; scale 2, offsetY 0.6; #1A0500 #B3260E #FF6C2F #FFC85C; proportion 0.3, softness 1, distortion 0.21, swirl 0.57, iterations 10, edge, shapeScale 0.75 |
| `aurora` | Teal and violet curtains, slow | speed 0.8; rotation 90; #020814 #0B3D3A #2BFFB0 #020814 #7A5CFF; proportion 0.4, softness 1, distortion 0.3, swirl 0.6, iterations 6, stripes, shapeScale 0.2 |
| `mono` | Black and white liquid folds | speed 0.8; #0A0A0A #F2F2F2; proportion 0.5, softness 1, distortion 0.25, swirl 0.8, iterations 10, checks, shapeScale 0.1 |

## Timing and numbers
- Background: timeScale 0.8–1.2 for 8–11 s. Transition: 0.5–1 s at 1.5–3 (the varg `warp-transition` runs 1.5). [20]
- Loop: 1 s crossfade (30 frames at 30 fps) at the end.
- Text: the flow is busy; place type on a 50–60% dark scrim band or in a solid card; check WCAG AA. [20]

## Build it
1. Start from `warp-transition` or Paper's `paper-warp-default` / `paper-warp-nectar` in `vargHQ/skills/paper-shaders`; paste params; mount via `paperFrameSource`. [20]
2. For a loop of length L: give the main clip `motion.frame = 60000`; over its last 1 s crossfade to a copy whose `motion.frame = 60000 − L × 1000 × timeScale`. At t = L the copy shows exactly the main clip's first frame. [20]
3. HyperFrames ready blocks: `flowing-gradient` (orange and violet bands), `aurora`, `aurora-drift`. [39]

## Mistakes that look amateur
- Cyan next to yellow next to magenta with nothing between → separate with violet or the base. [20]
- Warp at 0.3 → near-static; Warp needs 0.8+. [19]
- Hard cut at the loop point → 1 s crossfade. [19]
- 8–10 colours → 4–5. [32]
- White text directly on the flow → scrim or card. [20]

## Sources
[3] Stephen Haney — Warp shader — https://x.com/stephenhaney/status/1882113262092976634
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt
[19] Paper — warp.ts source — https://github.com/paper-design/shaders
[20] vargHQ — paper-shaders skill — `warp-transition`, Paper Default/Nectar values, complementary-hue rule
[24] Inigo Quilez — Palettes — https://iquilezles.org/articles/palettes/
[32] Kevin Hufnagl — Stripe gradient effect — https://kevinhufnagl.com/how-to-stripe-website-gradient-effect/
[39] HeyGen HyperFrames registry — `flowing-gradient`, `aurora`, `aurora-drift`
