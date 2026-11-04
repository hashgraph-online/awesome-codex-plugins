# Bitten word title

A word eaten letter by letter: each bite takes a scalloped mouthful out of the type, crumbs fly, and the bitten edge shows the fruit's colour, until the word is gone or one letter is left. Playful food, drink, kids, summer promos. Variants by fruit colour (lemon, orange, lime, strawberry). 16:9, 9:16, 1:1; 3-5 s.

## How the pros do it
- Every bite has anticipation: the letter leans or squeezes slightly away before the bite lands [39].
- Squash and stretch keep volume: when the bitten letter recoils, it squashes in one axis and stretches in the other by the same ratio [39].
- Loose bits (crumbs, juice drops) keep moving after the bite and move slower than the main shape (drag) [39].
- Hold a beat between bites so each one reads; a moving hold of 8-16 frames [39].
- Put bites on the beat; a bite is a hit, like a cut [38].
- Use a heavy, round-shouldered display face so a bite reads as a bite (lots of filled area): Rubik Mono One, Dela Gothic One, Bungee, Alfa Slab One [27].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `bitten-word-title.lemon` | Yellow word on white, pale inner flesh at the bite | word #FFE800 [30], bite rim #FFF6A8, bg #FFFFFF, Rubik Mono One |
| `bitten-word-title.orange` | Orange on cream | word #FF6C2F [30], rim #FFC58F, bg #FFF7EC |
| `bitten-word-title.lime` | Green on near-white | word #67B346 [30], rim #D9F0B8, bg #F7FBF2 |
| `bitten-word-title.strawberry` | Red with seed dots, pink flesh | word #F65058 [30], rim #FFD1D6, seeds #FFE900 2-3 px dots, bg #FFF5F5 |

## Timing and numbers (4 s = 120 f at 120 BPM, 15 f/beat)
- Word lands: 0-10 f, scale 0.92 to 1, `back.out(1.4)`.
- One bite per beat starting beat 2: anticipation 3 f (letter rotates -3deg, scale 0.97 x / 1.03 y), bite 1 f (mask applied), recoil 6-8 f (squash 1.08 x / 0.93 y back to 1, `elastic.out(1, 0.5)`).
- Bite shape: 3-5 overlapping circles of radius 16-22% of cap height along an arc, centre on the letter's top or side edge; reveals 25-45% of the letter per bite.
- Crumbs: 6-12 particles per bite, radius 2-6 px, initial speed 300-600 px/s, gravity 1800 px/s^2, life 12-18 f, seeded.
- Last bite on the final letter or leave one letter standing; hold 15-20 f.
- Cap height 30-40% of frame height (16:9), word centred, 8% side margin.

## Build it
1. Render the word as SVG text (or paths) with an SVG `<mask>` per letter: white rect minus bite circles (black). Each bite adds circles at a precomputed time.
2. Bite rim: draw the same circles slightly larger (+3 px) in the rim colour, clipped to the letter, under the mask edge, so the bitten edge shows flesh.
3. Timeline: per beat, a `set` for the mask circles (instant), tweens for anticipation and squash on the letter's `transform`.
4. Crumbs: positions as a closed-form function of time since the bite (`x0 + vx·t`, `y0 + vy·t + 0.5·g·t²`), seeded PRNG for velocities.
5. Optional crunch SFX on each bite frame.

## Mistakes that look amateur
- Bite as a straight cut or one perfect circle → use 3-5 overlapping circles so it reads as teeth.
- Letter does not react → add anticipation and recoil [39].
- Squash that changes volume (both axes shrink) → keep x·y ≈ 1 [39].
- Bites on random frames → lock to beats.
- Thin or light font → bites erase it instantly; use heavy faces.
- Crumbs from wall-clock random → seeded and time-based.

## Sources
[27] google/fonts METADATA — https://github.com/google/fonts — Rubik Mono One, Dela Gothic One, Bungee, Alfa Slab One are OFL
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — yellow, orange, kelly green, scarlet hexes
[38] Silverman Sound BPM calculator — https://www.silvermansound.com/bpm-to-fps-calculator
[39] Netguru, 12 principles — https://www.netguru.com/blog/illustrators-eye-12-principles-of-animation — anticipation, squash with constant volume, drag, moving hold
Gap: no practitioner write-up on bite-mask type was found; the bite geometry and crumb physics are our starting values.
