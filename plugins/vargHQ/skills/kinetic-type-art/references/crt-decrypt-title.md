# CRT decrypt title

Two rows of glowing amber type decrypt on a curved CRT seen from a three-quarter side angle, surrounded by dim interface labels. A 2-4 s title hit for tech, sci-fi, game and anime-flavoured edits. 16:9, 9:16, 1:1.

## How the pros do it
- Decrypt is a scramble that locks the target string in order: set the scramble alphabet (`chars`), refresh rate (`speed`, default 1, lower is slower), and a `revealDelay` so the noise shows before letters lock; `rightToLeft` and `delimiter` change the order [20].
- A CSS-only scramble: slide a vertical strip of letters with `steps(11)` over 0.25 s and stagger by letter [2]; many variants exist with CSS alone or JS [12].
- Per-letter flips through `_` and two random glyphs in 0.2 s, 0.05 s stagger, give the glitchier decode [3].
- CRT finish from a real shader's defaults: scanline weight 6.0 (inverse: higher = thinner lines), gap brightness 0.12, mask brightness 0.70, bloom factor 1.5, curvature 0.10 x / 0.15 y, input gamma 2.4, output 2.2; darker gaps raise moire [36].
- Interface labels stay quiet; the decrypting title is the message [55]. Keep labels in one system [54].
- Anime screens pair a compressed heavy serif with all-caps grotesque labels [52].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `crt-decrypt-title.amber` | Orange phosphor on black, side-angle monitor | type #FF8A1F, glow #FF5A00, bg #050403, VT323 or JetBrains Mono 700, rotateY 28deg |
| `crt-decrypt-title.green` | Green phosphor, flat-on | #33FF8A on #020604, Share Tech Mono, rotateY 0 |
| `crt-decrypt-title.serif` | Compressed Mincho title decrypts, mono labels | Shippori Mincho 800 scaleX 0.65, #FF8A1F, labels JetBrains Mono 12-14 px at 35% |

## Timing and numbers (3 s = 90 f)
- 0-6 f: screen powers on (white line to full height, `expo.out`).
- 6-48 f: row 1 decrypts: scramble shows for 6 f (`revealDelay` 0.2 s), then letters lock left to right over 24-30 f (`speed` 0.6-1) [20]; row 2 starts 8-10 f after row 1.
- Glyph refresh: every 2 f (15 Hz) reads as computer noise; every frame reads as static.
- Character sets: hex `0123456789ABCDEF`; block `█▓▒░▄▀■`; katakana-style half-width set; binary `01` for minimal. Keep one set per piece.
- 48-80 f: hold with 2-3% brightness flicker (seeded per frame) and a slow scan bar (12% opacity, 1 pass per 1.5 s).
- 80-90 f: optional 1-frame RGB split 4-6 px, then cut.
- Monitor angle: rotateY 22-32deg, perspective 1200 px; type cap height 9-12% of frame height per row.
- Bloom: blur radius 8-14 px at 60-80% opacity under the type (text-shadow stack or a filter pass).

## Build it
1. HyperFrames `scramble-reveal` (deterministic glyph rows locking left to right) for the rows; `caption-glitch-rgb` for scanline + RGB; `oscilloscope-trace` shows the phosphor-decay approach [41].
2. If using GSAP ScrambleText, seed its randomness or replace with your own per-frame glyph table, so renders are identical (glyph = table[(frame*7 + i*13 + seed) % n]).
3. Scanlines: `repeating-linear-gradient(to bottom, rgba(0,0,0,.88) 0 1px, transparent 1px 3px)` over the screen, or a fragment shader with the crt-pi parameters [36].
4. Curvature: apply only to the screen plane (barrel distortion) and keep labels outside it flat.
5. ffmpeg for footage of real screens: `curves=preset=increase_contrast,gblur=sigma=4:steps=2` blended back over the original for bloom, `vignette=angle=PI/4` [33].

## Mistakes that look amateur
- Unseeded random scramble → different every render; seed by frame and index.
- All letters lock at once → decrypt must sweep in order.
- Noise glyphs from a different font width than the target → line jitters; use a monospace or fixed-width cell.
- Scanlines so dark that type loses half its brightness → gap brightness ~0.12, not 0 [36].
- Labels as bright as the title → dim them to 30-40%.
- Copying a show's real interface labels or logos → invent labels.

## Sources
[2] @jh3yy, CSS scramble — https://x.com/jh3yy/status/1852465034481598662 — steps(11), 0.25 s
[3] @jh3yy, glitch flip — https://x.com/jh3yy/status/1762979019446698310
[12] @jh3yy, scramble ways — https://x.com/jh3yy/status/1867330835415707959
[20] GSAP ScrambleText — https://gsap.com/docs/v3/Plugins/ScrambleTextPlugin/
[33] FFmpeg filters — https://ffmpeg.org/ffmpeg-filters.html
[36] crt-pi shader — https://raw.githubusercontent.com/libretro/glsl-shaders/master/crt/shaders/crt-pi.glsl
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — scramble-reveal, caption-glitch-rgb, oscilloscope-trace
[52] Fonts In Use, Evangelion — https://fontsinuse.com/uses/28760/neon-genesis-evangelion
[54] Territory Studio interview — https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html
[55] John LePore interview — https://pushing-pixels.org/?p=12751
