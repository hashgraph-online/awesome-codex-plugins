# Anime command screen title

A title framed by a fictional command-centre screen in the style of 1990s mecha anime: a compressed heavy serif title card, warning blocks, ticking counters, glow and scanlines. For trailers, game reveals, tech launches with drama. 16:9, 9:16, 1:1; 5-7 s.

## How the pros do it
- The message is the priority; everything else is supporting texture. Make the title huge enough for the back row [55].
- Avoid generic "boxes and windows all tinted blue"; every element should look like it does something [55].
- Make the screens believable rather than accurate, and keep one consistent "operating system" across every panel [54].
- Give the glass a physical layer: scratches, haze, overlays [54].
- The anime title-card look is a heavy Mincho serif mechanically compressed (squeezed horizontally) into interlocking blocks, black and white; interfaces pair it with all-caps grotesque, sometimes condensed [52].
- Counters and readouts change on story beats, in sync with what happens [55].
- CRT finish from a real shader's defaults: scanline weight 6.0, gap brightness 0.12, mask 0.70, bloom 1.5 [36].
- Decode labels with a scramble (chars set, speed, reveal delay) rather than a typewriter [20].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `anime-command-screen.alert` | Orange-red alert screen, black title card, hazard stripes | bg #0A0605, warn #FF3B1F, amber #FF8A1F, title Shippori Mincho 800 scaleX 0.62 |
| `anime-command-screen.monitor` | Green-on-black monitor grid, white title | bg #020604, line #2BE38A at 60%, title Zen Old Mincho 900 scaleX 0.7, labels Archivo wdth 62 |
| `anime-command-screen.card` | Pure black/white title card only, no UI | #000000 / #FFFFFF, Mincho compressed to 0.55-0.75, interlocking L layout |

## Timing and numbers (6 s = 180 f)
- 0-12 f: screen power-on (brightness 0 to 1, horizontal line expands to full height, `expo.out`).
- 12-60 f: panels draw on: borders 6-10 f each, staggered 2 f; labels scramble in 8-12 f each (`speed: 1`, `revealDelay` 0.1 s) [20].
- 60-90 f: title card slams in: hard cut, 2-frame white flash (opacity 0.6) before it.
- Counters: integer values tick every 2 f; percent bars fill linearly; one counter hits a threshold on a beat and turns warn colour.
- 150-180 f: hold; a 1-frame glitch on the last beat (rgb split 6 px).
- Title: compressed Mincho, cap height 18-24% of frame height, scaleX 0.55-0.75, letter-spacing -0.02em, set in two or three interlocking lines (one line short, one long).
- Labels: Archivo wdth 62-75 or Inter caps 14-18 px, +0.1em; JetBrains Mono for numbers.
- Scanlines: 2-3 px period at 1080p, gap darkness 12% brightness [36]; bloom radius 6-12 px on warn colours.

## Build it
1. HyperFrames: `telemetry-hud` (corner brackets, label:value cues), `scramble-reveal` (deterministic glyph rows), `caption-glitch-rgb` (RGB + scanline overlay), `camcorder-hud` for timeline-driven counters [41].
2. Title card: text in a Mincho font with `transform: scaleX(0.62)` on an inline-block (compression is mechanical, not a condensed cut [52]); compose interlocking lines with absolute positioning.
3. Scanlines and mask: CSS repeating-linear-gradient overlay or a small fragment shader using the crt-pi values [36]; curvature 0.10/0.15 only if the whole frame is a monitor.
4. Counters: value = f(frame) (e.g. `Math.floor(lerp(a,b,progress))`), never incremented in callbacks.
5. Hazard stripes: repeating-linear-gradient 45deg, 24 px bands, scrolling linearly.

## Mistakes that look amateur
- Blue boxes everywhere with nothing functional → give each panel a job [55].
- Using a condensed font instead of compressing the serif → loses the stretched-ink character [52].
- Tiny title buried in UI → the message is the priority [55].
- Counters that change randomly off the beat → tie changes to beats [55].
- Heavy curvature + strong scanlines on everything → moire and mush; dark gaps raise moire [36].
- Copying a specific show's logos, organisation names or kanji text → invent your own labels.

## Sources
[10] @HudsandGuis — https://x.com/HudsandGuis/status/1427767264720285701 — FUI archive and talks
[20] GSAP ScrambleText — https://gsap.com/docs/v3/Plugins/ScrambleTextPlugin/
[36] crt-pi shader — https://raw.githubusercontent.com/libretro/glsl-shaders/master/crt/shaders/crt-pi.glsl — CRT defaults
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — telemetry-hud, scramble-reveal, caption-glitch-rgb, camcorder-hud
[52] Fonts In Use, Neon Genesis Evangelion (Peiran Tan) — https://fontsinuse.com/uses/28760/neon-genesis-evangelion — compressed Mincho title cards, grotesque on HUDs
[54] Territory Studio interview — https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html
[55] John LePore interview — https://pushing-pixels.org/?p=12751
