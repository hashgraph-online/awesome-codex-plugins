# Dot-burst particle title

A typed title sequence where a few dots drift together into one point, then burst into a field of coloured particles that settles into (or behind) the next title. For intros, chapter openers, generative-art brand pieces. Variants: meadow, evening, monochrome, electric. 16:9, 9:16, 1:1; 10-15 s.

## How the pros do it
- Sample target positions from the rendered text bitmap once at mount, keep particles in a table, and paint them in one update function with no per-particle tweens [41].
- For thousands of points use the GPU: points scatter through space and fly to the exact glyph pixels [41].
- Seed the field so every render is identical [41].
- Type rebuilt from discrete cells is a recognisable motion idea in its own right; keep the cell grid visible for a moment before it resolves [11].
- Type the title with a human cadence (chunked, uneven) behind a deterministic caret, not an even tick [41].
- Build tension, then release: the gather (anticipation) should be slower than the burst [39].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `particle-burst-title.meadow` | Greens, yellows, pinks on cream | bg #F4F1EA, particles #67B346 #FFE800 #FF48B0 #00A95C [30] |
| `particle-burst-title.evening` | Warm oranges and violets on deep blue | bg #1B1E3A, #FF6C2F #FFB511 #9D7AD2 #F984CA [30] |
| `particle-burst-title.monochrome` | Black dots on paper | bg #F2EFE8, #111111 at 3 opacities |
| `particle-burst-title.electric` | Saturated cyan, magenta, lime on black | bg #050505, #5EC8E5 #FF48B0 #E3ED55 [30], additive blend |

## Timing and numbers (15 s = 450 f)
- 0-90 f: title 1 types in (JetBrains Mono or Inter, 2-4 characters per chunk, chunks every 3-6 f), hold.
- 90-150 f: 5-9 dots drift from the frame edges toward one point (`power2.inOut`, 60 f).
- 150-156 f: merge into one dot, scale 1 to 1.6 (anticipation squeeze to 0.8 first, 3 f).
- 156 f: burst. Particles launch radially, speed 600-1400 px/s, drag 2.5-4 per s (exponential), small curl/noise offset.
- 156-240 f: field settles into a slow drift (10-30 px/s).
- 240-330 f: particles fly to sampled glyph positions of title 2 (`power3.inOut`, staggered by distance, 45-60 f total).
- 330-450 f: hold title 2; particles jitter ±0.5 px (breathing).
- Counts (starting values): Canvas 2D 1,500-4,000 particles at 1080p; WebGL points 20,000-80,000. Sample step 3-6 px across the glyph bitmap; dot radius 1.5-3 px.
- Burst on a downbeat; settle by the next bar.

## Build it
1. HyperFrames: `particle-text-dissolve` (assemble from / dissolve into a seeded cloud, density cap), `code-particle-assemble` (GPU points to glyph pixels), `caption-particle-burst` (bursts on keywords), `typed-prompt` (human-cadence typing) [41].
2. Sampling: draw the title on an offscreen canvas at the final size, read alpha, keep pixels on a grid step, shuffle with a seeded PRNG.
3. Motion as closed-form functions of time: burst `p = p0 + v·(1 - e^(-k·t))/k`, homing `p = lerp(p_field, p_target, ease(clamp((t - t_i)/d)))`.
4. Colour: assign palette colours by index modulo palette length, or by the target glyph.
5. Remotion: same maths inside a canvas drawn in a `useEffect` keyed on `frame`.

## Mistakes that look amateur
- Per-particle GSAP tweens → slow and non-deterministic at scale; use one painter [41].
- Uniform random burst with no drag → particles leave the frame; add exponential drag.
- Every particle arrives at once → stagger by distance or index.
- Too few particles for big type → title reads as dots; reduce sample step.
- Rainbow palette → 3-4 colours max per variant.
- Particle field fighting the typed title for attention → dim field to 40-60% while text holds.

## Sources
[11] @yiannifive, voxelized type — https://x.com/yiannifive/status/2023883254978531704 — type built from cells
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — palette hexes
[39] Netguru, 12 principles — https://www.netguru.com/blog/illustrators-eye-12-principles-of-animation — anticipation
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — particle-text-dissolve, code-particle-assemble, caption-particle-burst, typed-prompt
Gap: particle counts and burst physics are our starting values; no expert write-up with numbers was found.
