# Pixel-art runner on a CRT

A short side-scrolling "game" made in true low-res pixel art: a small hero runs, jumps over obstacles and reaches a goal or logo, all shown through a curved, scanlined CRT. Use it as an 18 s brand or launch spot, a game-studio promo or a playful explainer, in 16:9, 9:16 or 1:1. The format works when the pixel grid is honest (integer scale, stepped animation, small palette) and the CRT is applied last.

## How the pros do it
- **Draw at a tiny base resolution and scale only by whole numbers,** using nearest-neighbour ("Point"/"None") filtering. 2× and 3× are fine; 2.5× breaks the grid. Never downscale pixel art, and never mix more than two pixel resolutions (for example, the game layer plus a 2× UI layer). [13]
- **Work inside console limits for an authentic look.**
  - NES sprites use 4-colour palettes, 3 visible colours plus transparent. There are 4 sprite and 4 background palettes, taken from a 64-colour master palette. [15]
  - NES sprite tiles are 8×8 or 8×16, with at most 64 sprites on screen and 8 per scanline. [16]
  - PICO-8 is 128×128 with a fixed 16-colour palette and 8×8 sprites. [17][18]
  - The Game Boy look is 4 shades of green. [19]
- **Run cycles: few poses, honest timing.**
  - An 8-frame run shows each pose for 80 ms.
  - A 4-frame run shows each pose for 160 ms.
  - The famous 3-pose run with a repeated passing pose (a 4-frame loop) beats many longer cycles for energy.
  - Add a vertical bob for bounce. [14]
- **Experiment with playback speed; it changes the energy more than adding frames does.** Small teams reuse a 2-frame cycle for idles. [14]
- **Keep animation time stepped and separate from the frame rate.** PICO-8 games update at 30 fps by default, or 60 fps with `_update60`. Sprite poses still change only every few frames. [17]
- **Order: render low-res first → CRT shader last,** and give the CRT shader the low-resolution image, not an upscaled one. [3]
- **The CRT values most people use are the public-domain Lottes shader defaults** [10]:
  - hardScan −8 (sharp scanlines), hardPix −3
  - warpX 0.031, warpY 0.041 (barrel curvature)
  - shadowMask 3, with maskDark 0.5 and maskLight 1.5
  - bloomAmount 0.15
  - brightBoost 1.0
- **Simulate CRT gamma and the bezel in the crt-geom style** [11]:
  - CRT gamma 2.4 vs monitor gamma 2.2; a higher CRT gamma gives a darker, more saturated look.
  - Curvature radius R between 1.5 and 2.0; a higher R means a flatter tube, and 2.0 is a common preference.
  - Corner size 0.03 (0.10 looks toy-like).
  - Overscan 1.02 crops garbage edge lines.
- **Credit the shader community, not just "a filter."** Practitioners build on libretro/RetroArch shaders for CRT and ntsc-rs for the composite signal, and say so. [4][12]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `pixel-runner-crt.console-16` | 16-colour console on a consumer CRT, 16:9 | base 320×180 → ×6 = 1920×1080; PICO-8 16-colour palette; hero 16×16; 8-pose run at 80 ms; Lottes CRT defaults |
| `pixel-runner-crt.dmg-green` | 4-shade handheld green | base 320×180 ×6; palette #081820 #346856 #88c070 #e0f8d0; no shadow mask (maskDark 1, maskLight 1), scanlines hardScan −6, warp 0 |
| `pixel-runner-crt.nes-strict` | strict 8-bit sprite limits | sprites 3 colours + transparent each; ≤8 sprites per row; 3-pose + pass run at 133 ms (8 frames @ 60 fps); crt-geom R 2.0, CRT gamma 2.4 |
| `pixel-runner-crt.vertical` | 9:16 phone, runner climbs or runs on lower third | base 180×320 → ×6 = 1080×1920; ground at y = 70% of the frame; same palette and CRT |
| `pixel-runner-crt.square-128` | 1:1 fantasy-console | base 128×128 → ×8 = 1024 inside a 1080 frame (28 px bezel); PICO-8 palette; 30 fps update, poses at 4 frames (133 ms) |

## Timing and numbers
- **Output frame rate:** 60 fps, so the scroll is smooth. Sprite poses are held for whole frames:
  - At 60 fps: 5 frames ≈ 83 ms (close to the 80 ms rule).
  - At 50 fps: 4 frames = 80 ms exactly.
  - At 30 fps: 2 frames = 67 ms or 3 frames = 100 ms. [14]
- **Scroll speed:** 1 base px per output frame at 60 fps, which is 60 base px/s (360 px/s at 1080p). The "speed-up" beat uses 2 base px per frame. Always move in whole base pixels; anything else is sub-pixel shimmer, which breaks the grid rule. [13]
- **Parallax:** 3 layers at 0.25×, 0.5× and 1.0× of the ground speed, each rounded to whole base pixels per frame. Accumulate in floats and draw floored values.
- **Jump:** 0.5 s of airtime (30 frames at 60 fps) with a 24 base px apex, on a parabola. Hold a 1-frame squash pose on landing, then return to the run cycle.
- **Hero size:** 16×16 base px is 8.9% of a 180 px frame height. Keep the hero at 8–14% of frame height so it reads on a phone.
- **CRT power-on (convention):** 2 frames show a 1 px bright horizontal line; it then grows to full height over 8 frames, followed by a 6-frame overbright (brightBoost 1.3 → 1.0).
- **CRT power-off:** 6 frames vertical collapse to a 2 px line, then 6 frames horizontal shrink to a dot, then a 12-frame dot fade.
- **Beat structure (18.0 s, music at 120 BPM = 0.5 s per beat, 36 beats):**
  - 0.0–1.0 s: CRT power-on over a black field.
  - 1.0–3.0 s: title and "PRESS START" blinking at 2 Hz (0.25 s on, 0.25 s off). On "press", the blink rate jumps to 8 Hz for 0.5 s.
  - 3.0–5.0 s: the hero runs in from the left. The camera locks the hero at 33% of the frame width.
  - 5.0–11.0 s: three obstacles, one every 2 beats, with jumps landing on the downbeat. Coins add +100 to a score counter (top-left, 2× UI layer).
  - 11.0–13.0 s: speed-up (2 px per frame), poses at 4 frames each, music at double time.
  - 13.0–15.0 s: the big gap jump. A 2-frame hit-stop at the apex, then a 1 base px screen shake for 6 frames on landing.
  - 15.0–16.5 s: the goal, a flag or door that turns into the logo. "STAGE CLEAR" types in at 15 characters/s.
  - 16.5–18.0 s: hold the logo for 0.75 s, then CRT power-off.
- **Shot list:**
  1. Black screen and power-on line.
  2. Title card.
  3. Run-in.
  4. Obstacle run (one continuous scroll).
  5. Speed-up.
  6. Gap jump.
  7. Goal and logo.
  8. Power-off. Everything after the title card is one continuous scroll, so there are no cuts inside the game.
- **Type:** Press Start 2P (OFL-1.1) for the title and score, at 8 px base size (48 px at ×6). Silkscreen (OFL-1.1) for small UI. Text gets integer scaling only.
- **Sound:** keep the score to 4 voices, like PICO-8's 4 channels [17]. Use square/pulse leads and a noise-channel hat. Add jump and coin SFX on the frame of the action.

## Build it
1. **Pixel layer.** Use a `<canvas>` at the base size with `ctx.imageSmoothingEnabled = false`, scaled up by CSS `transform: scale(6)` and `image-rendering: pixelated`. Draw sprites from a sprite-sheet PNG. Every position is `Math.floor()`ed in base pixels.
2. **Stepped time.** Compute the pose index as `Math.floor(t / poseDuration) % poses` from the timeline time. The registry component `stop-motion-cadence` shows this law (`floor(t·fps)/fps`) and is seek-safe. Drive the scroll from `t` too (`x = floor(t·60·speed)`), so every frame can render independently.
3. **Level script:** an array of `{t, type}` events (obstacle, coin, gap, goal) on the 0.5 s beat grid. Jumps come from closed-form parabolas over `t − t_jump`, with no physics integration.
4. **CRT pass, last:** port the public-domain Lottes CRT shader (from libretro slang-shaders `crt/shaders/crt-lottes.slang`) to a WebGL full-screen pass on the low-res canvas texture [10]. A lighter option is the registry overlay `yt-screen-warp` (grid, scanlines, vignette, sheen, 3D warp), plus `vignette`. To show a physical TV in a room, wrap the result in `filmed-screen`.
5. **Optional composite softness** before the CRT, in the order composite → downscale → CRT: a light ntsc-rs pass on the base-res render [3], or `ordered-dither-pass` for a dithered fade-in.
6. **varg cards to pair:** `hyperframes-registry` (blocks above) and `fal-gamedev` (for generating sprite sheets, then hand-fix them to the palette).

## Mistakes that look amateur
- Non-integer scaling or bilinear upscaling, which blurs and smears pixels → integer scale with nearest-neighbour only. [13]
- Mixed pixel sizes (a 1× hero next to a 3× tree) → one game resolution plus at most one UI resolution. [13]
- Smooth, tweened sprite motion at 60 fps → step the poses (80–160 ms) and move in whole base pixels. [14]
- Too many colours, gradients or anti-aliasing → 4-colour sprites, a 16-colour scene, flat fills. [15][18]
- The CRT shader on the 1080p upscale, or before other effects → feed the shader the low-res frame and apply it last. [3]
- Over-curved, toy-like tubes (cornersize 0.1, big warp) → warp ≈ 0.03–0.04, corners 0.03. [10][11]
- A 30-frame run cycle "for smoothness" → 3–8 poses carry more energy. [14]

## Sources
[3] Finn McKenty (@thefinnmckenty) — https://x.com/thefinnmckenty/status/2078469612786847903 — NTSC → downscale → CRT order; the shader should get a low-res image
[4] Finn McKenty — https://x.com/thefinnmckenty/status/2079554243380572162 — ntsc-rs and RetroArch CRT shaders are best in class
[10] Timothy Lottes — public-domain CRT shader, libretro slang port, parameter defaults — https://raw.githubusercontent.com/libretro/slang-shaders/master/crt/shaders/crt-lottes.slang
[11] Hunter K. (libretro shader developer) — "Customizing cgwg's CRT pixel shader" (crt-geom) — https://filthypants.blogspot.com/2012/07/customizing-cgwgs-crt-pixel-shader.html — R, d, cornersize, gamma, overscan
[12] Pedro Medeiros (@saint11; pixel artist on Celeste and TowerFall, 6.4k-like tutorial thread) — https://x.com/saint11/status/1283130502195539968 — his pixel-art tutorial index
[13] Pedro Medeiros — "Scaling pixel art" — https://saint11.art/blog/scaling/ — integer scaling, nearest neighbour, never downscale, at most two resolutions
[14] Raymond Schlitter (Slynyrd) — "Pixelblog 8: Intro to Animation" — https://slynyrd.com/blog/2018/8/19/pixelblog-8-intro-to-animation — 8 poses at 80 ms, 4 at 160 ms, 3-pose run, bob
[15] NESdev Wiki — PPU palettes — https://www.nesdev.org/wiki/PPU_palettes — 4+4 palettes, 4 entries with 0 transparent, 64 master colours
[16] NESdev Wiki — PPU OAM — https://www.nesdev.org/wiki/PPU_OAM — 64 sprites, 8×8/8×16, 8 per scanline
[17] Lexaloffle — PICO-8 manual — https://www.lexaloffle.com/dl/docs/pico-8_manual.html — 128×128, 16 colours, 8×8 sprites, 30/60 fps, 4 sound channels
[18] Lospec — PICO-8 palette — https://lospec.com/palette-list/pico-8 — 16 hex values
[19] Lospec — Nintendo Game Boy (BGB) palette — https://lospec.com/palette-list/nintendo-gameboy-bgb — 4 hex values
