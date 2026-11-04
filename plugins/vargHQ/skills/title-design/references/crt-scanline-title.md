# CRT scanline title

A name and role that crash onto a cathode-ray-tube screen — power-on flash, rolling noise, scanlines, RGB fringe —
then the tube clears away and clean type stays on a transparent frame. Retro tech, gaming, synth music, archive
segments. 16:9, 9:16, 1:1; about 6 s. Delivered with alpha (ProRes 4444 / WebM VP9 alpha) so it sits over footage.

## How the pros do it
- Model the signal, then the screen: a convincing CRT look comes from the composite signal path (luma/chroma
  separation, bandwidth limits, chroma delay, ghosting, noise) feeding a separate display stage (scanlines,
  phosphor mask, curvature, bezel) [36]. Do color bleed first, scanlines and mask last.
- Scanline gaps exist because a 240p picture on a TV built for 480 interlaced lines leaves every second line dark;
  emulators therefore double the image first and apply scanlines after scaling, never before [46]. Model the beam,
  not a hard black line: Lottes' shader uses a Gaussian beam (`hardScan −8`, `hardPix −3`) plus bloom `0.15` [21].
- Phosphor mask: dark/light mask levels 0.5 / 1.5 around 1.0, with aperture-grille, slot or shadow-mask patterns [21].
- Curvature is subtle: warp 0.031 horizontally, 0.041 vertically in Lottes' defaults [21].
- Pixel art and type were designed for the blur and bloom of the tube; the effect should soften edges, not just add
  black lines [21][36].
- The CRT phase is a transition, not the resting state: the information (name/role) must end clean and hold for two
  reads [14][13].
- RGB splitting in motion: keep it small and animate it (a 10%→15% split range is a typical subtle move in tools) [37].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `crt-scanline-title.consumer-tv` | Warm TV: slot mask, soft beam, chroma bleed, roll | scan period 4.5 px (240 lines @1080), dark 45%, mask 0.5/1.5, warp 0.031/0.041, bloom 0.15, chroma shift 2 px |
| `crt-scanline-title.arcade-monitor` | Sharp RGB monitor, aperture grille, little bleed | scan period 4 px, dark 55%, grille 3 px triads, no chroma shift, bloom 0.1 |
| `crt-scanline-title.terminal-green` | Monochrome phosphor terminal | #33FF66 on #031A0B, VT323 / IBM Plex Mono, phosphor persistence via `lagfun decay=0.9`, scan 4 px |

## Timing and numbers
- 6.0 s at 30 fps:
  - 0.00–0.20 s (6 f): power-on — a 2 px white line at center expands to full height (scaleY 0.002→1, `expo.out`), brightness 2.0→1.0.
  - 0.20–0.60 s (12 f): snow noise burst at 40% over the raster, vertical roll 0→−24 px then back, hum bars (2 soft dark bands) drift.
  - 0.60–1.20 s (18 f): name types or snaps in line by line; RGB offset decays 8 px → 1 px (`power3.out`); jitter ±2 px on random frames (seeded).
  - 1.20–3.40 s: CRT hold: scanlines, mask, bloom 0.15, 1 px chroma bleed; role line appears at 1.4 s.
  - 3.40–3.80 s (12 f): "clear" — scanline + mask layer opacity 1→0, curvature 1→0, bloom 0.15→0, background tube glass → transparent.
  - 3.80–6.00 s: clean type on alpha (≥ 2 × reading time for name + role) [6].
- Scanline geometry at 1080p: period = 1080 / 240 = 4.5 px (or 4 px / 6 px for integer lines); dark band 40–55% of the period;
  at 2160p double it. CSS: `repeating-linear-gradient(to bottom, rgba(0,0,0,.45) 0 2px, transparent 2px 4.5px)`.
- Mask: vertical RGB triads 3 px wide, multiply at 15–25% (maps maskDark 0.5 / maskLight 1.5 around white [21]).
- Chroma bleed: shift chroma ±1–2 px horizontally (not luma) before scanlines [36].
- Type: VT323 (OFL) 9% H for the name, IBM Plex Mono 500 3.2% H for the role; text #E9FFF1 with glow `0 0 6px` at 60% of the text color.
- Colors: tube black #050607, phosphor white #E9FFF1, warm TV tint #FFF3E0, terminal green #33FF66.

## Build it
- HyperFrames: start from `caption-glitch-rgb` (RGB aberration + CRT scanline overlay), `scan-band` (diagonal distortion
  band with red/cyan offsets), `scramble-reveal` (deterministic decode), `rgb-glitch-text`; `filmed-screen` when the whole
  scene should look shot off a screen. Use a canvas/WebGL pass for curvature + mask, or stacked CSS layers when flat is fine.
- Shader (WebGL/TypeGPU) for the CRT stage, Lottes-style uniforms: `hardScan=-8, hardPix=-3, warp=vec2(0.031,0.041),
  maskDark=0.5, maskLight=1.5, bloomAmount=0.15` [21]; animate a single `crt` uniform 1→0 for the clear.
- Drive everything from timeline time; noise and jitter seeded by frame index so renders repeat.
- ffmpeg on footage (no shader): `format=yuv444p, chromashift=crh=2:cbh=-2, noise=alls=14:allf=t,
  geq=lum='lum(X,Y)*(1-0.45*lt(mod(Y,4.5),2))':cb='cb(X,Y)':cr='cr(X,Y)', lagfun=decay=0.85,
  lenscorrection=k1=0.04:k2=0.02, gblur=sigma=0.6` [22]. Roll: `scroll=v=0.002` for a few frames via `enable`.

## Mistakes that look amateur
- Pure black 1 px lines every other pixel → 4–6 px period with a Gaussian beam profile, applied after scaling [21][46].
- Heavy fisheye curvature → warp ≤ 0.04 [21].
- RGB split on luma and chroma alike at 20 px → 1–2 px chroma bleed; big offsets only in the 0.4 s crash [36].
- CRT effect left on the whole time over information → clear to clean type and hold for two reads [14].
- Random noise that changes on every re-render → seed by frame [44].
- Scanline period that aliases into moiré after scaling → render at final resolution, integer or 4.5 px period at 1080p [21].

## Sources
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[13] Chris Salters — Sports lower thirds (School of Motion) (Motion designer writing for School of Motion) — https://schoolofmotion.com/blog/sports-lower-thirds — 3-6 s on screen, read twice, define purpose (identify vs context), flexible widths, ProRes 4444 alpha.
[14] Jason Boone — How to make lower third titles that don't suck (Frame.io Insider) (Editor and doc filmmaker (National Geographic, Current TV), Premiere/AE educator) — https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/ — Read every word twice, plates for separation, avoid mouth/edges, consistency, simple animation.
[21] Timothy Lottes — CRT styled scan-line shader (libretro crt-lottes) (Graphics engineer (creator of FXAA); public-domain shader) — https://github.com/libretro/glsl-shaders/blob/master/crt/shaders/crt-lottes.glsl — hardScan -8, hardPix -3, warp 0.031/0.041, mask 0.5/1.5, mask types, bloom 0.15.
[22] FFmpeg Filters Documentation (FFmpeg project) — https://ffmpeg.org/ffmpeg-filters.html — rgbashift, chromashift, noise, gblur, geq, tmix, lagfun options.
[36] @komm64 (Indie game developer (14k followers) explaining his NTSC/CRT shader) — https://x.com/komm64/status/2073558529097834584 — Signal path first (YIQ, chroma bleed, ghosting, noise), display stage second (scanlines, mask, curvature).
[37] @tranmautritam (Tran Mau Tri Tam) (Product designer, ex-UI8 design lead, 111k Dribbble followers) — https://x.com/tranmautritam/status/2079207566526259654 — Shader animation values incl. RGB split 10% -> 15%.
[44] @twoclipping (Creator of a code-only motion design prompt template (1.1M views)) — https://x.com/twoclipping/status/2103273003555402193 — Every style computed from time in seek(t); subframes blended with ffmpeg tmix for motion blur.
[46] Libretro forums — 240p LCD vs TV (Thread with libretro shader developers (hunterk, DariusG)) — https://forums.libretro.com/t/240p-lcd-vs-tv/44087 — 240p leaves every second line dark; double the image and apply scanlines after scaling.
