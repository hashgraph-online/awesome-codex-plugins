# Liquid artwork reveal

An artwork (painting, poster, product key art) appears through a liquid distortion that ripples and settles until the image is still and sharp, with a title resolving last. For art shows, music covers, city or festival posters. 16:9, 9:16, 1:1; 4-6 s.

## How the pros do it
- Displacement maps move each pixel by a noise field: P'(x,y) = P(x + scale·(R-0.5), y + scale·(G-0.5)); a fractal/turbulence noise with baseFrequency ~0.05 and 2 octaves at scale 50 is the reference starting point [34].
- Settle by animating `scale` down to 0; the image is untouched when scale is 0 [34].
- Use frame-exact shaders, not wall-clock ones: Paper Shaders Warp (marbled fields; timeScale 1.5+ reads as a transition), Water (caustics over an image), FlutedGlass (reeded glass) and LiquidMetal (chrome logo sting), all mounted at speed 0 and driven by the timeline [42].
- Keep fewer than ~12 shader hosts per composition [42].
- Liquid backgrounds with HTML on top: registry `vfx-liquid-background`, `vfx-liquid-glass` [41].
- Grain and paper finish on stills keep a painted artwork from looking like a flat JPEG [42].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `liquid-art-reveal.ripple` | Strong ripple that calms, then a title | feTurbulence fractalNoise baseFrequency 0.012-0.02, numOctaves 2, scale 140 → 0 over 2.4 s |
| `liquid-art-reveal.marble` | Marbled warp from brand colours resolves into the artwork | Paper Warp `checks`, timeScale 1.6, crossfade to image at 1.2 s |
| `liquid-art-reveal.glass` | Reeded glass slides off the artwork | Paper FlutedGlass over image, distortion 1 → 0, 1.6 s |

## Timing and numbers (5 s = 150 f)
- 0-12 f: artwork fades from bg under full distortion (scale at max).
- 12-84 f: distortion scale eases to 0 (`power3.out`, 72 f); noise drifts (baseFrequency offset or seed time) slowly, 0.2-0.5 cycles over the move.
- 84-108 f: title resolves (mask wipe or tracking-in, 18-24 f, `expo.out`).
- 108-150 f: hold; optional micro-ripple scale 2-4 px.
- Max displacement: 6-10% of frame width at 1080p (scale 110-190 px); more breaks the image into noise.
- Type: Didone or editorial serif for art contexts (Bodoni Moda, Instrument Serif); title 8-12% of frame height; grotesque label 16-20 px caps +0.1em [22].

## Build it
1. SVG route (simple, seekable): `<filter><feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="2" seed="7" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="140" xChannelSelector="R" yChannelSelector="G"/></filter>` on the artwork; tween `scale` attribute on the timeline [34].
2. Shader route: paper-shaders `warp-transition` preset into the image, or Water/FlutedGlass over the still; mount through `paper-preset.js` at speed 0 [42].
3. Registry: `vfx-liquid-background` for a fluid plane behind HTML content [41].
4. Title: `tracking-in` or a mask wipe [41].
5. ffmpeg for footage: `displace` filter with a noise map as the second and third inputs (edge mode smear/mirror) [33].

## Mistakes that look amateur
- Distortion that never fully settles → the artwork looks broken; end at scale 0.
- Very high baseFrequency → fine noise looks like a cheap glass filter; 0.01-0.03 for liquid.
- Animating from the wall clock (shader default) → flicker in render; drive time from the timeline [42].
- Title on top while the image still ripples hard → wait until scale < 15%.
- Upscaled low-res artwork → displacement exaggerates pixelation; use 2x source.
- Using an artist's work without rights → only your own or licensed artwork; describe styles, never copy a named artist's piece.

## Sources
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html
[33] FFmpeg filters — https://ffmpeg.org/ffmpeg-filters.html — displace
[34] MDN, feDisplacementMap — https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDisplacementMap — formula, example values
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — vfx-liquid-background, vfx-liquid-glass, tracking-in
[42] varg paper-shaders — https://github.com/vargHQ/skills/tree/main/paper-shaders — Warp, Water, FlutedGlass, determinism
Gap: no practitioner on X with a written liquid-reveal recipe was found; values beyond the MDN example are our starting points.
