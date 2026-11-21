# Amber booth console

A retro amber-phosphor touchscreen, like the control panel of a cinema projection booth: it boots (self-test lines, a progress bar), loads "your show" (a playlist of reels/cues with durations), runs a countdown, and draws your end card in glowing amber vector lines. A cinematic opener or closer for film, creator and tool brands that want a warm analogue-tech mood. 16:9 native; 1:1 crops the panel; 9:16 stacks the panel vertically. Typical length 15–20 s.

## How the pros do it
- Ground the fiction in the real machine: decide what content flows through the screen (show playlist, cue list, lamp hours, reel status) before styling it, and research real systems; screen-graphics studios work this way. [42]
- Feel can beat literal clarity on a mood screen, but the one line that carries the story (the show title, the end card) must be readable. [42]
- Use the real phosphor color: amber monitors used P3 phosphor peaking at 602 nm, which converts to roughly #ffb700 (bright) to #fa9300 / #f67800 (deeper), depending on the conversion method; amber sat next to green (P1) and white (P4) on 1960s–80s monochrome screens. [39][40]
- Retro-terminal emulators tune the look with a few knobs; a good amber starting point is text #ff8100 on #000000, bloom 0.6, burn-in 0.3, flicker 0.1, jitter 0.2, static noise 0.1, screen curvature 0.2, glowing scan line 0.2. Copy the idea of the knobs, not the code (GPL). [41]
- Boot text streams like terminal output (bursts of lines every 40–80 ms), and readable lines hold by reading time (0.6 s + chars ÷ 15). [12][15]
- Typing on the console is human-paced: 12–16 cps with uneven gaps; system text prints faster. [10][62]
- Keep moves short and decelerating; the "touch" feedback is a 120–200 ms flash on the pressed control. [44][2]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `amber-booth-console.boot-load-endcard` | Full 19 s arc: boot → load show → countdown → vector end card | text #FFB000, dim #7A4A00, bg #0A0600, bloom 0.6, scanlines 3 px period 18% darkening, curvature barrel k1 0.06, flicker ±3% at 12 Hz noise |
| `amber-booth-console.clean-amber` | Same UI, no curvature, light glow (readable for product text) | glow 0 0 6px rgba(255,176,0,.55), scanlines 10%, no jitter |
| `amber-booth-console.footage-crt` | ffmpeg look to turn any footage into an amber CRT screen | see filter chain below |

## Timing and numbers
- 19 s arc (570 frames): 0–0.6 s power-on (a horizontal line expands to full height: scaleY 0.004 → 1, 0.35 s expo.out, then brightness overshoot 1.4 → 1 in 0.25 s); 0.6–4.5 s self-test lines (bursts every 60 ms, each check "OK" 0.2 s later); 4.5–6.0 s progress bar 0→100% (power1.inOut); 6.0–11.0 s "LOAD SHOW" — playlist rows type in (title 14 cps, durations snap), a cursor highlight steps row to row every 0.5 s; 11.0–13.5 s countdown 3-2-1 (each 0.8 s, number scale 1.08 → 1); 13.5–17.5 s end card drawn as vector strokes (stroke-dashoffset, 2.5 s power2.inOut, stagger 0.12 s per path); 17.5–19.0 s hold with gentle flicker. [12][15][44]
- Color: primary #FFB000 (between the 602 nm conversions #ffb700 and #fa9300), dim text at 45% (#7A4A00 on black), background #0A0600 not pure black, so bloom has room. [40]
- Glow: two text-shadows, 0 0 4px rgba(255,176,0,.8) + 0 0 18px rgba(255,140,0,.35). Burn-in/persistence: previous frame ghost at 25–30% decaying over 3 frames. [41]
- Scanlines: 1 dark line every 3 px at 1080p, 15–20% darker; shadow-mask off. Curvature: barrel distortion k1 0.04–0.08; vignette 0.35.
- Type: VT323 (OFL-1.1) for pixel-terminal text at ≥ 3.4% of frame height; IBM Plex Mono or Share Tech Mono (OFL-1.1) for cleaner panel labels. [49]
- Touch flash: the pressed button inverts (black text on amber) for 0.15 s.

## Build it
1. Start from HyperFrames `terminal-simulator` for the boot log, `code-terminal-run` for typed commands, `svg-stroke-trace` for the vector end card and `vignette` for the edges: `npx hyperframes add terminal-simulator svg-stroke-trace vignette`. The registry has no CRT block (checked): add a full-frame overlay div with `repeating-linear-gradient` scanlines. Skip `grain-overlay` (it uses CSS keyframes); drive grain from timeline time instead.
2. Build the console as one HTML panel (header strip, playlist table, status column, big action buttons), all amber on near-black.
3. Draw the end card as inline SVG paths (your logo outlines) in `svg-stroke-trace`, or animate `stroke-dashoffset` from path length → 0 on the timeline yourself; add the same glow as the text.
4. Curvature/bloom in the browser: render the panel into a WebGL plane with a small barrel-distortion + bloom shader (seek-safe: uniforms from timeline time), or keep it flat for the clean preset.
5. Footage version (ffmpeg, any clip → amber CRT):
   `ffmpeg -i in.mp4 -vf "format=gray,lutrgb=r='val*1.0':g='val*0.69':b='val*0.0',lenscorrection=k1=0.06:k2=0.02,tmix=frames=3:weights='1 0.45 0.2',gblur=sigma=1.2,noise=alls=6:allf=t,geq=r='r(X,Y)*(1-0.18*eq(mod(Y,3),0))':g='g(X,Y)*(1-0.18*eq(mod(Y,3),0))':b='b(X,Y)',vignette=PI/4.5" -c:v libx264 -crf 18 out.mp4`
   (grey → amber tint, barrel curve, phosphor persistence, soft bloom, grain, scanlines, vignette).

## Mistakes that look amateur
- Pure orange #FF8000 on pure black with no glow → warm #FFB000, near-black bg, two-layer glow. [40][41]
- Every effect at full strength (curvature, jitter, chroma shift) → small values; the show title must stay readable. [41][42]
- Boot text that is random gibberish → real-sounding booth checks (lamp, shutter, audio, playlist) decided before styling. [42]
- Boot lines all at once or all at one speed → bursts every 40–80 ms, checks resolving after a beat. [15]
- Wall-clock flicker (Math.random per render) → seeded noise from timeline time.
- Scanlines finer than 2 px at 1080p (they moiré after compression) → 3 px period.

## Sources
[2] Emil Kowalski (@emilkowalski) — https://x.com/emilkowalski/status/1970144111261868487
[10] Dhakal et al. CHI 2018 — https://www.eurekalert.org/news-releases/569762
[12] Netflix English Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[15] VHS best-practice skill — https://cdn.jsdelivr.net/npm/@marcfargas/skills@0.5.1/vhs/SKILL.md
[39] Wikipedia, Monochrome monitor — https://en.wikipedia.org/wiki/Monochrome_monitor
[40] Phosphor color notes (P3 602 nm conversions) — https://publish.obsidian.md/xybre/permalink/e397c38e-aa6f-45eb-831f-f02a3836abc4
[41] cool-retro-term "Default Amber" profile (GPL-3; parameter values only) — https://github.com/Swordfish90/cool-retro-term
[42] Pushing Pixels, David Sheldon-Hicks (Territory Studio) — https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html
[44] Emil Kowalski, Great animations — https://emilkowal.ski/ui/great-animations
[49] Google Fonts metadata (VT323, IBM Plex Mono, Share Tech Mono: OFL) — https://github.com/google/fonts
[62] HyperFrames notes-typing — https://github.com/heygen-com/hyperframes/tree/main/registry/components/notes-typing
