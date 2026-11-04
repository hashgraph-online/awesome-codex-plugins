# Chrome echo melt

A single word in liquid chrome that melts into its own echoes: stepped copies trail off it, blur into a grainy halo,
and dissolve. Music releases, fashion and Y2K-style promos, logo-like title words. Four palettes: Ice, Chrome, Ember,
Toxic. 16:9, 9:16, 1:1; about 6 s.

## How the pros do it
- The classic chrome fill is a vertical gradient with a hard horizon in the middle: white → sky color → black at 50%,
  white at 51% → ground color → black (Steve Patterson's 80s chrome recipe, linear 90°) [26]. Chrome reads as chrome
  because of that hard center transition in the gradient map [27].
- Chrome type needs sharp alternating light/dark bands; add a small RGB split that fringes the band edges red/blue/cyan
  rather than a blurry overall gradient [38].
- Echoes, not motion blur: Spider-Verse replaced motion blur with "shifting" — the same image stepped across frames —
  which reads sharper [32]. Space echoes by whole frames or steps.
- Blur in layers: radial → Gaussian → RGB-split blur stacked gives a richer halo than one big blur [39].
- Halos and stylized glow sit on top as their own layer; keep the type core sharp underneath (glow bleeding over the
  type is the common Video Copilot-style pitfall viewers report) [24].
- Chrome type is a long-running look (Tron, MTV, Y2K/vaporwave revival); the current trend favors liquid, distorted
  metal and looping metallic swirls [28].
- Grain ties it together and hides banding in long blurs: scanned-film grain was layered over the Stranger Things title [29].
- Animate the RGB split amount rather than holding a large fixed offset (a 10%→15% move is typical) [37].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `chrome-echo-melt.ice` | Cold silver-blue chrome, blue halo | stops #FFFFFF 5% / #9FD8FF 25% / #05070A 50% / #FFFFFF 51% / #1A4CFF 75% / #020308 95%; halo #6FB8FF |
| `chrome-echo-melt.chrome` | Neutral mirror chrome | #FFFFFF / #E8ECF2 / #0A0A0C / #FFFFFF / #5A5F6B / #050506; halo #DDE3EA |
| `chrome-echo-melt.ember` | Hot gold-orange metal | #FFF6E5 / #FFC46B / #1A0700 / #FFF1D6 / #B3260F / #120300; halo #FF7A2F |
| `chrome-echo-melt.toxic` | Acid green-teal metal | #F4FFE0 / #D9FF4A / #031008 / #EFFFE8 / #0FA36B / #010805; halo #7DFF5A |

## Timing and numbers
- 6.0 s at 30 fps:
  - 0.0–1.2 s form: word resolves from blur 40 px → 0 (`expo.out`), 8 echoes collapse inward (offset 6 px → 0), RGB split 6 px → 1.5 px.
  - 1.2–3.0 s hold: a highlight band sweeps the chrome once (gradient offset −30% → +30% over 1.4 s, `cubic-bezier(0.2,0,0,1)` [10]); split 1–2 px on band edges [38].
  - 3.0–5.0 s melt: echoes peel off downward/outward on steps of 2 frames, each echo +8 px and opacity × 0.7 per step;
    core blur 0 → 18 px; halo radius 24 → 64 px; RGB split 1.5 → 8 px (`power2.in`).
  - 5.0–6.0 s dissolve: everything fades to grain; grain stays to the last frame.
- Echo stack: 6–10 copies, spacing 2 frames (stepped, no blur on the copies) [32], opacity 0.7^n, blend `screen` (lighten on dark bg).
- Halo: duplicate of the word, Gaussian blur σ = 24–48 px at 1080p, `screen` at 50–70%; then a radial blur 8–12% and a
  2–4 px RGB-split blur on top [39].
- Grain: monochrome, 8–12% opacity, changes every frame (or every 2 frames for a stepped feel).
- Type: Unbounded 900 or Archivo Black (OFL), 16–20% H, tracking −0.02em; single word, ≤ 8 letters.
- Background: #000000–#08080A; never mid-gray (chrome needs dark around it).

## Build it
- HyperFrames: `chrome-orb` / `liquid-metal` (WebGPU chrome material, MIT shaders) for a metal backdrop or orb; the varg
  `paper-shaders` skill preset `liquid-metal-sting` for a frame-exact metal sting; `grain-overlay`, `blur-in`,
  `focus-blur-resolve`, `yt-prism-title` (red/blue fringe that settles) for parts.
- Canvas/WebGL route: render the word to a texture; fragment shader maps `uv.y` (plus a small noise warp) through the
  6-stop gradient with a hard step at 0.5; sample three times with ±split offsets for R/G/B [38]. Echoes = the previous
  N rendered frames composited with offsets — but compute them from time (`t − k·2/fps`), never from a feedback buffer, so seeking works.
- CSS-only fallback: `background: linear-gradient(180deg, stops…)` with `background-clip: text`; echoes are N absolutely
  positioned clones whose `transform`/`opacity`/`filter: blur()` are functions of `t − k·step`.
- ffmpeg on footage or a rendered word with alpha: `split[a][b]; [b]gblur=sigma=36,colorchannelmixer=aa=0.6[halo];
  [a]tmix=frames=8:weights='1 0.7 0.49 0.34 0.24 0.17 0.12 0.08'[echo]; [echo][halo]blend=all_mode=screen,
  rgbashift=rh=-3:bh=3, noise=alls=12:allf=t` — or `lagfun=decay=0.93` for a trailing melt [22].

## Mistakes that look amateur
- Smooth gray gradient on the type → hard horizon at 50/51% with dark bands [26][27].
- Glow/halo applied to the type itself, washing out the letters → separate halo layer under/over a sharp core [24].
- Motion-blurred smear for the echo → stepped, sharp copies with decaying opacity [32].
- One giant Gaussian blur → stacked radial + Gaussian + RGB-split blur [39].
- Static 10 px RGB offset during the hold → 1–2 px at rest, grow only in the melt [37].
- Banding in the halo on dark backgrounds → 8–12% grain over everything [29].

## Sources
[10] Material Design 3 motion tokens (material-web) (Google Material Design system source tokens) — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — Emphasized decelerate/accelerate cubic-beziers and the 50-1000 ms duration scale.
[22] FFmpeg Filters Documentation (FFmpeg project) — https://ffmpeg.org/ffmpeg-filters.html — rgbashift, chromashift, noise, gblur, geq, tmix, lagfun options.
[24] Andrew Kramer — Colorful Glitch FX, 100% AE (Video Copilot) (Founder of Video Copilot, VFX artist) — https://www.videocopilot.net/tutorials/colorful_glitch_fx — Fractal noise -> displacement map; animate noise brightness; isolate glow and color passes.
[26] Steve Patterson — 80s retro text effect (Photoshop Essentials) (Photoshop educator, Photoshop Essentials) — https://www.photoshopessentials.com/?p=14254 — Chrome gradient stops with a hard black/white horizon at 50/51%, bevel and glow values.
[27] Texturelabs — Super rad 80s chrome in Photoshop (Photoshop Roadmap) (Texturelabs, texture and effects educator) — https://photoshoproadmap.com/how-to-create-super-rad-80s-chrome-in-photoshop — Gradient maps with a hard central transition make realistic chrome.
[28] Motion Array — The chrome effect in video and design (Motion Array blog (asset marketplace)) — https://blog.motionarray.com/?p=28891 — History of chrome type (Tron, MTV, Y2K) and the current liquid-metal trend.
[29] Art of the Title — Stranger Things (Imaginary Forces; Michelle Dougherty) (Emmy-winning main title; interview with creative director Michelle Dougherty) — https://www.artofthetitle.com/title/stranger-things/ — Typeface as actor, rejected snapping lock-in, fluid jitter-free drift, film grain, ~45 s sweet spot.
[32] CG Spectrum — Spider-Man: Into the Spider-Verse, how they got that look (Interviews with supervising animator Jeff Panko and lead lighting/comp artist Geeta Basantani) — https://cgspectrum.com/blog/spider-man-into-the-spider-verse-how-they-got-that-mind-blowing-look — Animate on ones then step to twos; no motion blur, stepped echoes; sims on ones.
[37] @tranmautritam (Tran Mau Tri Tam) (Product designer, ex-UI8 design lead, 111k Dribbble followers) — https://x.com/tranmautritam/status/2079207566526259654 — Shader animation values incl. RGB split 10% -> 15%.
[38] @tranmautritam (Tran Mau Tri Tam) — chromatic metal shader (Product designer, ex-UI8 design lead) — https://x.com/tranmautritam/status/2075885681147298085 — Chrome = sharp alternating bands + RGB split fringes; sample the ramp 3x for R/G/B.
[39] @TheMirzaBeig (Mirza Beig) (Technical artist / VFX (Unity, After Effects), 30k followers) — https://x.com/TheMirzaBeig/status/2104135691567243517 — Blur chain: radial -> Gaussian -> RGB-split blur.
