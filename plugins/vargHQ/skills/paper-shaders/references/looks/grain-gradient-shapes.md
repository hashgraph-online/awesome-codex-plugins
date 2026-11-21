# Grain gradient

Soft colour shapes (corner glows, waves, ripples, a blob, a sphere) rendered through heavy grain, like a riso print or grainy poster. A backdrop for a quote, a product cut-out or a speaker. 16:9, 9:16 and 1:1; 6–10 s.

## How the pros do it
- Use Paper's GrainGradient: up to 7 colours plus `colorBack`; `shape` is one of wave, dots, truchet, corners, ripple, blob, sphere; `softness` 0 = hard bands, 1 = smooth; `intensity` = distortion between bands; `noise` = grain amount. [18]
- The grain is computed from screen pixels (`gl_FragCoord`), so changing `scale` or `fit` does not change grain size; render at the delivery resolution and keep the same pixel ratio for drafts and finals. [19][20]
- Its internal clock is slow (`0.1 × (u_time + 7)`), so timeScale 0.3–0.5 suits a 10 s background and 1.0 is lively. [19]
- `blob` works as a product backdrop; move it off-centre with `offsetX` to clear room for a quote. [20]
- For a print look, use real riso ink colours instead of digital primaries: Fluorescent Pink #FF48B0, Blue #0078BF, Yellow #FFE800, Federal Blue #3D5588, Orange #FF6C2F, Sunflower #FFB511. Paper's print designers also warn that pure digital primaries look fake. [33][35]
- Two or three inks read as print; a fourth usually muddies it. [20]
- Heavy grain is where platform re-encodes hurt most; export 1080p at high bitrate and preview the uploaded result. [11]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Violet-to-pink corner glow on near-black | speed 0.5; back #0A0A12; #3B2BFF #FF6AC1 #FFD3A5; shape corners, softness 0.6, intensity 0.35, noise 0.4 |
| `riso` | Riso pink/blue/yellow waves on paper | speed 0.4; back #FBFAF4; #FF48B0 #0078BF #FFE800; shape wave, softness 0.3, intensity 0.5, noise 0.7 |
| `ember` | Burnt orange ripples | speed 0.4; scale 0.5; back #140A00; #6F2D00 #FF6C2F #FFB511; shape ripple, softness 0.5, intensity 0.5, noise 0.5 |
| `sage` | Muted sage blob (Paper's Blob) | speed 0.5; scale 1.3; back #0F0E18; #3E6172 #A49B74 #568C50; shape blob, softness 0, intensity 0.15, noise 0.5 |
| `night` | Navy sphere, pale rim | speed 0.3; back #02030A; #0E1A4F #3D5588 #9CC2FF; shape sphere, softness 0.8, intensity 0.25, noise 0.6 |

## Timing and numbers
- noise 0.25 = subtle (Paper's Default), 0.5 = clearly grainy, 0.7 = print. Above 0.8 the colour shapes stop reading.
- Text over `riso`: use #231F20 warm black at 600–800 weight; over dark presets use #F4EFE6 rather than pure white so it sits in the print world. [33]
- A product cut-out on `sage`/`blob`: blob centre 15–20% of frame width off the product's side so the glow frames it.

## Build it
1. Copy the varg `grain-blob` preset (or Paper's `paper-grain-gradient-*`) from `vargHQ/skills/paper-shaders`; paste the params; mount with `paperFrameSource`. [20]
2. Brand it with `apply-brand.mjs` through roles; keep `colorBack` as the base role. [20]
3. HyperFrames alternatives: `grain-field` component (dot field over a luminance gradient) and `warm-grain`. [39]

## Mistakes that look amateur
- Pure #FF00FF / #00FFFF / #FFFF00 for a "print" look → riso or warm CMYK inks. [33][35]
- noise 1.0 → 0.4–0.7.
- Rendering at 4K and downscaling to 1080p → grain shrinks to sub-pixel and turns into flat colour; render at delivery size. [19]
- Five or more colours → 3, plus `colorBack`. [20]
- Shape centred behind the text → offset it with `offsetX`/`offsetY`. [20]

## Sources
[11] Lucas Pope — capture of fine texture — https://x.com/dukope/status/1300259933414330368
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt
[19] Paper — grain-gradient.ts source — https://github.com/paper-design/shaders — grain from `gl_FragCoord`, `t = .1*(u_time+7)`
[20] vargHQ — paper-shaders skill — `grain-blob`, Paper Default/Blob/Ripple values, two-ink rule
[33] Ksenia Kondrashova and Agu Seguí — Retro print CMYK halftone (Paper blog) — https://paper.design/blog/retro-print-cmyk-halftone-shader
[35] risoinks colour table — https://rdrr.io/github/anfederico/risoinks/src/R/color.R
[39] HeyGen HyperFrames registry — `grain-field`, `warm-grain`
