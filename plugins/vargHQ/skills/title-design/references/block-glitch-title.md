# Block glitch title

A title that snaps in through a heavy digital block glitch — sliced bands jump sideways, RGB channels tear apart,
the frame "crashes" for a beat — and then settles into clean type. Tech launches, gaming, music, trailers. Two
variants: on black, or on a transparent frame over footage. 16:9, 9:16, 1:1; about 6 s.

## How the pros do it
- Build the glitch procedurally: a noise field (Fractal Noise) drives a displacement map, and you animate the noise
  brightness to turn the glitch on and off; isolate color passes with channel tools and glow them separately [24].
- Glitch events are synchronized: Video Copilot's Twitch plug-in is built around synchronizing its random operators,
  so every distortion fires on the same frames and reads as one event rather than noise [25].
- Real codec damage is blocky because video is coded in 16×16 macroblocks with 8×8 or 4×4 transform blocks [23] — so
  block heights and slice offsets in multiples of 8/16 px read as "digital", random sizes read as fake.
- The tool vocabulary is consistent: block shift, RGB split, channel scale, pixel sort, transform glitch, flicker,
  analog sync distortion [25]. Pick 2–3, not all.
- Step the glitch: posterized time (e.g. 12 fps) makes a pop glitch read as anime-style animation [40]; the same trick
  plus noise/blur/threshold builds photocopy textures [45].
- Animate the RGB split amount instead of holding a big offset; small values (10%→15% of the control) already read [37].
- End clean: the information is the title; hold the settled type ≥ 2 × reading time [6][14].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `block-glitch-title.black` | Hard glitch on #000, white title | bursts 2–4 f on / 3–8 f off; 3–7 slices of 16/32/64 px, x-shift 24–160 px; RGB split 6–14 px; crash 2 f invert; settle 12 f |
| `block-glitch-title.transparent` | Same over footage, alpha output | same timing; slices only inside the type's bounding box + 15%; no full-frame invert; RGB 4–10 px |
| `block-glitch-title.stepped` | Anime-style stepped glitch | same as black, glitch layer quantized to 12 fps [40], clean type on ones |

## Timing and numbers
- 6.0 s at 30 fps (black):
  - 0.00–0.40 s: empty frame with 2 single-frame flickers (frames 4 and 9) of 1–2 slices — anticipation.
  - 0.40–1.30 s: heavy section: the title is visible but sliced; bursts of 2–4 frames on, 3–8 off; per burst 3–7
    horizontal slices, heights 16/32/48/64 px, x-shift ±24–160 px; RGB split rh −6…−14 px / bh +6…+14 px; 1-frame
    full-width block of noise (8×8 px cells) once.
  - 1.30–1.37 s (2 f): crash — invert or white flash, slices at maximum.
  - 1.37–1.77 s (12 f): settle — RGB split 6 px → 0 with `expo.out`, 1–2 residual 1-frame slices at 1.5 s and 1.63 s.
  - 1.77–5.50 s: clean hold; optional micro-glitch (1 frame, 1 slice, 2 px split) once at 3.5 s.
  - 5.50–6.00 s: exit with a final 3-frame burst and cut to black/alpha.
- Randomness: seeded by frame index (`mulberry32(seed + frame)`) — identical on every render and on scrub [44].
- Synchronize: slices, RGB split, flicker and audio clicks all key off the same burst schedule [25].
- Type: Space Grotesk 700 or JetBrains Mono 800 (OFL), 10–13% H, caps +0.04em [7]; colors #F5F5F5 on #000;
  glitch accents pure channels #FF0040 / #00E5FF.
- Transparent variant: keep slices within the text bounding box + 15% padding, never tear the footage itself.

## Build it
- HyperFrames: `rgb-glitch-text` (RGB-offset copies jitter in a controlled window), `glitch` (shader transition with digital
  artifacts), `chromatic-aberration-wipe` (channel split on peak frames), `grid-pixelate-wipe`, `scramble-reveal`,
  `caption-glitch-rgb`.
- DOM approach: 3 stacked copies (R, G, B via `mix-blend-mode: screen` on black, or `filter` color matrices) + N slice copies
  with `clip-path: inset(top 0 bottom 0)` and `translateX`; a precomputed burst table `[{frame, slices:[{y,h,dx}], split}]`
  drives a single `onUpdate` that sets styles from the current frame. No per-slice tweens.
- WebGL: one fragment shader with uniforms `burst`, `split`, `seed`; slice = `floor(uv.y * H / 16.)`, offset =
  `step(0.7, hash(slice, seed)) * dx`; sample R/G/B with ±split.
- Stepped variant: quantize only the glitch layer's time `floor(t * 12) / 12`; keep the clean type on full frame rate [40].
- ffmpeg on footage (bursts via `enable`): `rgbashift=rh=-10:bh=10:enable='lt(mod(n,9),3)*between(t,0.4,1.3)',
  noise=alls=40:allf=t:enable='eq(n,39)', negate=enable='between(n,39,40)'`; block slices: `split` the input, `crop`
  64 px bands, `overlay` them back shifted by 48–120 px with the same `enable` window [22].

## Mistakes that look amateur
- Random slice heights like 13 or 27 px → multiples of 8/16 px [23].
- Glitch frames scattered evenly through the whole clip → clustered bursts with gaps, synchronized across effects [25].
- RGB split at 30 px held for seconds → 6–14 px in bursts, decaying to 0 at settle [37].
- Every effect at once (pixel sort + VHS + datamosh + split) → 2–3 effects [25].
- Glitch never resolves → clean type holds ≥ 2 reads [14][6].
- Non-deterministic noise that changes between preview and render → seeded by frame [44].

## Sources
[6] Clevercast — BBC Subtitling Guidelines (summary) (Video platform company summarizing the BBC subtitle guidelines) — https://clevercast.com/bbc-subtitling-guidelines — 160-180 wpm = 0.33-0.375 s per word; line max 68% of a 16:9 frame.
[7] Matthew Butterick — Practical Typography: Letterspacing (Typographer and author of Practical Typography) — https://practicaltypography.com/letterspacing.html — Caps +5-12% letterspacing (0.05-0.12em); no letterspacing on lowercase.
[14] Jason Boone — How to make lower third titles that don't suck (Frame.io Insider) (Editor and doc filmmaker (National Geographic, Current TV), Premiere/AE educator) — https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/ — Read every word twice, plates for separation, avoid mouth/edges, consistency, simple animation.
[22] FFmpeg Filters Documentation (FFmpeg project) — https://ffmpeg.org/ffmpeg-filters.html — rgbashift, chromashift, noise, gblur, geq, tmix, lagfun options.
[23] Wikipedia — Macroblock (Encyclopedia article on video coding) — https://en.wikipedia.org/wiki/Macroblock — 16x16 macroblocks, 8x8/4x4 transform blocks -> block sizes for digital glitches.
[24] Andrew Kramer — Colorful Glitch FX, 100% AE (Video Copilot) (Founder of Video Copilot, VFX artist) — https://www.videocopilot.net/tutorials/colorful_glitch_fx — Fractal noise -> displacement map; animate noise brightness; isolate glow and color passes.
[25] Rich Young — Glitches in After Effects (ProVideo Coalition) (ProVideo Coalition writer on AE tools) — https://www.provideocoalition.com/glitches-in-after-effects/ — Glitch vocabulary (block shift, RGB split, pixel sort, sync distortion); Twitch syncs random operators.
[37] @tranmautritam (Tran Mau Tri Tam) (Product designer, ex-UI8 design lead, 111k Dribbble followers) — https://x.com/tranmautritam/status/2079207566526259654 — Shader animation values incl. RGB split 10% -> 15%.
[40] @ohey_official (OHEY | Top Effects) (After Effects effects/template creator) — https://x.com/ohey_official/status/1846868254595469793 — Pop glitch text + posterize time for an anime feel.
[44] @twoclipping (Creator of a code-only motion design prompt template (1.1M views)) — https://x.com/twoclipping/status/2103273003555402193 — Every style computed from time in seek(t); subframes blended with ffmpeg tmix for motion blur.
[45] @niqteh (niqte) (Motion designer posting AE tutorials) — https://x.com/niqteh/status/2079011658467266574 — Photocopy texture chain: noise, blur, threshold, tint, posterize time.
