# motion-formats preview

A 15.9 s HyperFrames film (1920x1080, 30 fps, silent) that plays four formats of the skill one after another. A small label in the bottom-left corner names the template and preset on screen.

| # | Time | Preset | Shows |
|---|---|---|---|
| 1 | 0.0–3.5 s | `vhs-bouncing-logo.pal-50` | an invented "NORTHWIND HOME VIDEO" logo (420x180) bouncing at 1000 px/s on each axis (45°) inside the 1500x900 free area. Its position is the preset's triangle wave, `x = L − |((v·t + x0) mod 2L) − L|`, so any frame renders on its own. The scene shows path time 1.5–5.0 s: the corner hit lands at 3.0 s and is held for 0.5 s. The colour hard-switches through the six preset colours on every wall hit. The corner flashes white for 2 f with a soft tracking glitch, and each wall hit kicks the chroma by 5 px for 1 f. "PLAY ▶" in VT323 sits at 6% of the frame height, inset 7%, for the first 1.5 s, and a 12-line tracking band rolls from bottom to top over the first 0.5 s |
| 2 | 3.5–8.0 s | `pixel-runner-crt.console-16` | a 320x180 pixel game in the PICO-8 16-colour palette (every pixel snapped to it), with an original cast on a dusk world. The hero is a small cyan robot, 16x16 in 3 colours plus transparent, with an 8-pose run and a 1 px bob. The obstacles are hazard pylons and spikes, and the pickups are pink gems. Three parallax layers move at 0.25x, 0.5x and 1.0x, in whole base pixels. The hero makes three jumps with 0.5 s of airtime and a 24 px apex (closed-form parabola), each landing on a 120 BPM downbeat with a 1-frame squash. Each gem adds +1 to a "◆ 09" counter, with "STAGE 01" on the right, and the text is Press Start 2P at 8 px base. A WebGL port of the public-domain Lottes CRT shader runs last, on the low-res texture, with the preset defaults: hardScan −8, hardPix −3, warp 0.031/0.041, shadowMask 3 at 0.5/1.5, bloom 0.15, plus 0.03 corners. Power-on is a 2 f line, an 8 f expand and a 6 f overbright from 1.3 to 1.0. Power-off is a 6 f collapse, 6 f to a dot and a 12 f dot fade |
| 3 | 8.0–10.5 s | `wave-wordmark.lift` | an invented "lumen labs" wordmark in Inter 800. One raised-cosine wave drives every glyph: `peak_i = t0 + i·0.1 s`, a falloff window of 2x the delay (0.4 s pulse) and a lift of 30% of the cap height. The crest is tinted #FFD400 from the same ease value. Glyph positions come from the kerned word, and the word ends on the exact rest pose |
| 4 | 10.5–15.9 s | `kinetic-lyric-video.word-punch` | an invented lyric, "say it soft, then say it loud", at 100 BPM (0.6 s a beat), one word per beat. Anton caps with −3% tracking: normal at 26% of the frame height, the whisper at 0.5x and the hook at 1.8x. Each word slides 160 px in 5 f (`expo.out`) from alternating sides, starting 2 f before its onset, and exits over 4 f on the next onset. The hook lands on the chorus downbeat with an inverted frame, a 1-frame-late #FF3D2E duplicate for a highlight edge, a 2-frame chromatic kick of 6 px, a 1.5 s hold and grain at 5% |

The values come from `assets/presets/*.json` and from the "Timing and numbers" section of each reference: geometry, speeds, hexes, frame counts, eases, sizes and shader parameters. Every time is computed from absolute time (t0 + n x beat), never by adding rounded frames.

## Render

```bash
cd motion-formats/examples/demo
npx --yes hyperframes@0.8.206 check
npx --yes hyperframes@0.8.206 snapshot --at 2.95,4.75,8.6,14.43
npx --yes hyperframes@0.8.206 render --fps 30 --crf 23 --output motion-formats.mp4
```

HyperFrames needs Node 22 and ffmpeg. The render takes about two minutes on a laptop, mostly for the per-frame tape pass, and writes a file of about 5 MB. The CRT pass needs WebGL, which HyperFrames' Chrome provides.

## Deviations and notes

- **30 fps everywhere.** The preview spec is 30 fps. The VHS preset renders at its 50 fps field rate and the pixel runner at 60 fps, so here the bounce moves 33.3 px per frame instead of 20, the runner scrolls 2 base px per frame instead of 1 (the same 60 base px/s), and run poses hold 2 frames (67 ms, the reference's 30 fps option) instead of 80 ms. For a real deliverable, render those two formats at `--fps 50` and `--fps 60`.
- **Tape pass in the browser.** The reference's first choice is ntsc-rs on the clean render. This demo runs a seeded, in-page stand-in on a 480-line YIQ signal, in the order the reference gives (tape, then downscale): luma blur 1.75 px and chroma blur 9 px with a 4 px delay (both scaled to 480 lines), halved vertical chroma, sharpen 0.25, edge wave 0.5, snow 0.025, chroma noise and an 8-line head-switching band, before the upscale. The "PLAY" OSD stays clean, because the VCR draws it after the tape. To get the full signal model, pass the clean render through ntsc-rs with the preset values.
- **VHS excerpt.** The scene shows only the last 3.5 s of the 5 s sting, so the corner hit lands inside a short card. The opening frame starts on the right wall rather than at `x0 = 0.25·L`.
- **Runner excerpt.** The reference describes an 18 s beat structure. The demo keeps the power-on, the run with jumps on the downbeat, the pickups and counter, and the power-off, and skips the title card, the speed-up, the gap jump and the goal. The reference's +100 coin score is shown as a gem counter (+1 per gem), and the cast, HUD and props are deliberately generic so they do not echo any existing game. The HUD sits on the base pixel grid rather than on a separate 2x UI layer, so the frame uses a single pixel resolution.
- **Wave lead-in.** The rest before the crest is 0.4 s instead of 0.2 s so that the cut into the scene reads, and the rest pose is then held for 1.0 s.
- **Lyric timings are illustrative.** There is no audio. The onsets are set by hand at 0.3 + n x 0.6 s. Each outgoing word fades its ink in 2 f while it slides out over the preset's 4 f, so that two words never sit on top of each other for long. The hook holds for 1.5 s, the reference's minimum.

## Credits

All imagery, sprites and logos are drawn in code, and the robot, pylons, gems and HUD are original designs. "Northwind" and "Lumen Labs" are invented brands, and the lyric is invented. No footage, music or real logos are used. The CRT pass is a port of Timothy Lottes' public-domain CRT shader (libretro slang-shaders `crt-lottes`), with corner rounding after cgwg's crt-geom. The palette is the PICO-8 16-colour palette (via Lospec). The fonts are all under the SIL Open Font License: Anton, VT323 and Press Start 2P are kept in `assets/fonts/`, and HyperFrames bundles Inter and JetBrains Mono.
