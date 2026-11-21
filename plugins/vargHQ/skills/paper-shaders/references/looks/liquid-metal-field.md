# Liquid metal field

Flowing chrome that fills the whole frame: a premium backdrop behind a product name, a launch title or an end card, or a 1–2 s sting when a logo is used as the mask. 16:9, 9:16 and 1:1; 6–10 s as a background, 1–2 s as a sting.

## How the pros do it
- Fill the frame with LiquidMetal at `shape: "none"` and `scale: 1`; this keeps the effect inside the canvas and makes it responsive to any aspect ratio. Paper's shader developer gives this exact tip for full-canvas use. [7][18]
- Start from a predefined shape or a transparent logo, then polish with the sliders; for a logo sting the image needs a transparent background because LiquidMetal reads its alpha as the mask. [6][18][20]
- Keep the chrome neutral: `colorTint` is applied with colour-burn blending, so `#FFFFFF` reads as polished metal and a strong brand tint turns it into coloured plastic. Put the brand colour in the background or the wordmark instead. [18][20]
- `shiftRed` / `shiftBlue` are per-channel dispersion: 0.3 / 0.3 gives a thin rainbow fringe on the stripe edges (Paper's default); 0 / 0 gives clean noir graphite. Stay at or below 0.3 for a premium look. [18][20]
- `repetition` sets stripe density: 1.5 gives wide liquid bands (Paper's Backdrop), 2 gives the classic chrome reflection (Paper's Default). Above 4 the bands read as a pattern, not a material. [18][20]
- `softness` 0.05–0.1 gives hard mirror edges; 0.45 gives a soft satin (Paper's Noir). `distortion` 0.07–0.1 adds organic wobble; `contour` 0.4 bends the stripes at the shape edges. [18][20]
- Paper ships every LiquidMetal preset at speed 1. Behind text, slow it to 0.4–0.7 so the eye reads the words, not the metal; the varg skill keeps backgrounds behind text at the low end of the speed range. [20]
- Mount at speed 0 and drive `frame` from the timeline (`frame = seconds × 1000 × timeScale`), never Paper's own animation loop, or renders flicker and differ between workers. [20]
- Paper Shaders are open source and free for any commercial use, including in client videos. [1]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Bright silver chrome, thin RGB fringe | speed 0.5; back #AAAAAC, tint #FFFFFF; repetition 2, softness 0.1, shiftR/B 0.3/0.3, distortion 0.07, contour 0.4, angle 70 |
| `chrome` | Wide liquid bands | speed 0.7; back #AAAAAC, tint #FFFFFF; repetition 1.5, softness 0.05, shift 0.3/0.3, distortion 0.1, contour 0.4, angle 90 |
| `noir` | Graphite on black, no fringe | speed 0.4; back #000000, tint #606060; repetition 1.5, softness 0.45, shift 0/0, distortion 0, contour 0, angle 90 |
| `gold` | Gold burned into chrome on near-black | speed 0.5; back #1A1206, tint #D9A441; repetition 2, softness 0.15, shiftR 0.15, shiftB -0.15, distortion 0.08, contour 0.3, angle 60 |

All presets: `shape: "none"`, `scale: 1`, `fit: "contain"`, offsets 0.

## Timing and numbers
- Background: 6–10 s, timeScale 0.4–0.7 (Paper's editor `speed`). Sting: 1–2 s at timeScale 1.0–1.5, logo as the mask.
- `angle` is the direction the pattern moves relative to the shape: 70–90° gives a diagonal-to-vertical flow that reads well in 9:16.
- Text over chrome: average luminance sits near mid-grey, so white or black type both fail contrast. Put a 40–60% black gradient scrim under the text block, or use `noir`; then run `npx hyperframes check` for WCAG AA. [20]
- Keep under about 12 shader hosts per composition; Chrome drops WebGL contexts past 16. [20]

## Build it
1. Start from the varg `liquid-metal-sting` preset or Paper's `paper-liquid-metal-backdrop` in `vargHQ/skills/paper-shaders`; copy the params above into a preset JSON with every sizing param set. [20]
2. HyperFrames: a host `div.clip` with `data-no-timeline`, then `registerFrameSource(paperFrameSource(PS, host, preset))` from `paper-preset.js`. [20]
3. Remotion: `<ShaderBackground preset={...} />` from the skill's template, render with `--gl=angle`. [20]
4. Optional intro: `paramsAt: t => ({ distortion: 0.07 + 0.2 * (1 - easeOutCubic(min(t / 1.5, 1))) })` so the metal settles in the first 1.5 s (pure function of time).
5. Alternative block: HyperFrames registry `liquid-metal` (a chrome sphere on black, WebGPU) when a single orb is wanted instead of a field. [39]

## Mistakes that look amateur
- Brand-coloured tint on the chrome → keep tint white or #606060, move the colour to the background or type. [20]
- Speed 1+ behind a headline → 0.4–0.7; the metal should drift, not boil. [20]
- Shape left at `diamond` for a full-frame background → `shape: "none"`, `scale: 1`. [7]
- Heavy RGB dispersion (shift above 0.5) → 0.3 or less; strong fringes look like a chromatic-aberration filter, not metal. [18]
- Logo with a white background as the mask → export a transparent PNG/SVG first. [18]
- Paper's own animation loop running during render → speed 0, frame from timeline. [20]

## Sources
[1] Stephen Haney (Paper co-founder) — Paper Shaders open source and free — https://x.com/stephenhaney/status/2072369858638233843 — licence for commercial use
[6] Ksenia Kondrashova (Paper shader developer) — liquid metal workflow — https://x.com/uuuuuulala/status/2003848893965193406 — shape or image first, then sliders
[7] Ksenia Kondrashova — LiquidMetal pro tip — https://x.com/uuuuuulala/status/2044099750241415655 — `shape: none`, `scale: 1` for a contained, responsive fill
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt — param names and ranges; colour-burn tint
[20] vargHQ — paper-shaders skill — https://github.com/vargHQ/skills/tree/main/paper-shaders — Paper's Default/Backdrop/Noir values, determinism, chrome-stays-neutral rule
[39] HeyGen HyperFrames registry — `liquid-metal` block — https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/blocks/liquid-metal/registry-item.json
