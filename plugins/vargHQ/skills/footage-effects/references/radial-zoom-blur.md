# Radial zoom blur

Pulls real footage into a zoom blur toward a centre point. It can be a constant soft pull, a 0.4 s punch on a beat or cut, a burst with colour fringes fanning outward, or light streaks that shoot only out of highlights. Use it for drops, impacts, speed and transitions. Works in 16:9, 9:16 and 1:1; hits last 6–24 frames and looks last up to 8 s.

## How the pros do it
- **Sample outward along the ray to the focal point and average.** This is a special case of linear blur and is cheap. [2] Remotion's `zoomBlur` does this with `amount` in px (default 40) and 24 samples (max 64). [24]
- **Zoom vs spin:** in Zoom mode, Amount is the blur length radiating from the centre. Spin blurs in arcs. Draft quality shows grainy steps. [21]
- **Symmetric blur or one-sided smear,** with a falloff on the smear. Animate the mix from the original to bring the effect in. [22]
- **Brightest mode** keeps the brightest sample along each ray, which suits light streaks. [23] The light-streak version samples toward the light with Density, Weight and Decay (0–1), then scales by Exposure. [20]
- **Coloured fringe fanning outward:** give each sample its own colour weight (red first, then green, then blue), or scale R and B radially after the blur. [2][11]
- **Steps must be invisible:** with too few samples the streak breaks into ghost copies. Keep the gap between samples ≤ 6 px at the frame corner, either with more samples or two passes (8 × 8 = 64 effective samples). (Our test: 8 samples at a 10% zoom left 14 px steps; two passes removed them.)

## Presets
| Preset | Look | Key values (1080p, 30 fps) |
|---|---|---|
| `soft-pull` | Gentle constant pull, sharp centre | scale amount 0.04 (≈ 44 px streak at the corner); centre (0.5, 0.5); 30% of the half-diagonal sharp, full blur from 70% |
| `punch-in` | Spike on a beat or cut | amount `0.14·exp(-((in − C)/6)²)` (peak ≈ 154 px at frame C, σ 6 frames); centre (0.5, 0.45); pair with a 1.00 → 1.06 scale punch |
| `fringe-burst` | Blur with red/blue fanning out | amount `0.10·exp(-((in − C)/8)²)`; radial CA a 0.006 (13 px at the corners) |
| `light-streak` | Rays out of lamps and windows only | highlights knee 0.70–0.95; amount 0.25; streak gain R 1.6 G 1.5 B 1.3; screen; centre = the light |

## Timing and numbers
- Streak length at the corner ≈ amount × 1101 px (1080p 16:9 half-diagonal). For 9:16 1080×1920 it is the same 1101 px.
- Hit envelope: Gaussian with σ 6 frames (0.2 s), so it is visible for about 24 frames (0.8 s) and peaks on the cut frame. For a whip transition, put the peak exactly on the cut so both shots blur at it.
- Centre: on the subject's eyes or the product, not always at frame centre (for faces, about (0.5, 0.42)).
- Samples: ≥ 32 effective for amounts up to 60 px, and 64 (two passes of 8) above that.
- Cost in ffmpeg: two passes of 8 `perspective` copies ran at about 0.25× real time at 1080p.

## Build it
**ffmpeg (tested):** each copy is the frame zoomed by `1 + A·i/(N−1)` around the centre with `perspective` (expressions evaluated per frame through the frame index `in`). Then `mix` averages the copies, and a second pass with A/8 fills the gaps. Generator:
```python
def zoom_pass(inp, out, n, A, cx, cy, tag):
    g = f"[{inp}]split={n}" + "".join(f"[{tag}{i}]" for i in range(n)) + ";"
    for i in range(n):
        s = f"(1+({A})*{i/(n-1):.4f})"; X, Y = f"W*{cx}", f"H*{cy}"
        g += (f"[{tag}{i}]perspective=x0='{X}-{X}/{s}':y0='{Y}-{Y}/{s}':x1='{X}+(W-{X})/{s}':y1='{Y}-{Y}/{s}'"
              f":x2='{X}-{X}/{s}':y2='{Y}+(H-{Y})/{s}':x3='{X}+(W-{X})/{s}':y3='{Y}+(H-{Y})/{s}':eval=frame[{tag}z{i}];")
    return g + "".join(f"[{tag}z{i}]" for i in range(n)) + f"mix=inputs={n}[{out}]"
A = "0.14*exp(-pow((in-45)/6,2))"          # punch peaking at frame 45
fc = "[0:v]format=gbrp[s];" + zoom_pass("s","p1",8,A,0.5,0.45,"a") + ";" + zoom_pass("p1","zb",8,f"({A})/8",0.5,0.45,"b") + ";[zb]format=yuv420p[v]"
```
- Sharp core: `maskedmerge` of the original and the blurred clip, with a radial `geq` mask (0 inside 30% of the half-diagonal, 255 beyond 70%). The mask is a generated lavfi input that never ends, so cap the output with `-t <clip duration>`.
- Light streak: threshold the highlights with `curves`, zoom-blur only that copy, then `blend=all_mode=screen:shortest=1` it over the original.
- The full chains for all four presets are in `assets/presets/radial-zoom-blur.json`.

**Remotion:** `<Video effects={[zoomBlur({amount: interpolate(frame,[C-12,C,C+12],[0,154,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}), center:[0.5,0.45], samples:48})]}/>` (`@remotion/effects/zoom-blur`, v4.0.480+). [24]

**HyperFrames:** use the registry's `zoom-through-transition` and `cinematic-zoom` for transitions. For a blur on footage, write a WebGL layer over the `<video>` texture with the 24–64 sample loop `uv_i = mix(uv, centre, amount·i/N)`, and set `amount` from the GSAP timeline (no wall clock).

## Mistakes that look amateur
- Visible stair-step ghost copies → more samples, or two passes (8 × 8).
- Blurring the subject's face at its peak for more than 6 frames → keep the sharp core mask, or put the peak on the cut.
- Centre at frame centre while the subject sits off-centre → centre on the subject.
- Constant heavy zoom blur over a whole shot (nausea) → strong amounts only as 0.2–0.8 s hits; soft-pull ≤ 50 px for looks.
- Streaks from dark areas (mud) → use the light-streak version with the highlight threshold.
- Linear easing on the hit → Gaussian or `expo.out`, peaking on the beat.

## Sources
[2] Xor (@XorDev) — types of blur shaders — https://x.com/XorDev/status/1762944762787647954
[10] FFmpeg Filters Documentation — https://ffmpeg.org/ffmpeg-filters.html
[11] Xor — GM Shaders Mini: Chromatic Aberration — https://mini.gmshaders.com/p/gm-shaders-mini-chromatic-aberration
[20] Kenny Mitchell — GPU Gems 3 ch.13 — https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process
[21] Adobe After Effects CS3 User Guide — Radial Blur — https://www.manualsdir.com/manuals/753848/adobe-after-effects-cs3.html?page=384
[22] Boris FX — BCC Radial Blur — https://borisfx.com/documentation/continuum/bcc-radial-blur/
[23] Plate docs — Point Blur — https://plate-docs.pages.dev/effects/blur/point/
[24] Remotion — zoomBlur() — https://www.remotion.dev/docs/effects/zoom-blur
