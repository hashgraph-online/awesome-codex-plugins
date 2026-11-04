# Chromatic aberration

Splits real footage's red, green and blue channels into a fringe. Real lenses push the fringe outward from the centre. A digital split shifts the whole frame, and a psychedelic version pulses. Use it for lens character, impact frames, music videos and "something is wrong" beats. Works in 16:9, 9:16 and 1:1, for 2–8 s per shot (an accent, not a grade).

## How the pros do it
- **Pick the model first.** Real lateral CA comes from magnification that differs by wavelength. It is zero at the optical centre and grows with radius, and lens software corrects it by scaling R and B radially to match G. A flat RGB shift is a digital or glitch look, not a lens look. [16][11]
- **Radial lens look:** sample each channel at `mix(uv, centre, k)`, so separation is 0 at the centre and maximal at the corners. Keep the radial offset around 0.01 UV for the full effect. [11]
- **Natural version:** blend ~10 samples across the offset with per-sample channel weights (blue → green → red) and accumulate squared colour, then `sqrt`. It reads as a lens rainbow instead of three ghost images. [11]
- **Cheap edge-only hack:** `col.rgb += dFdx(col.rgb) * vec3(3,0,-3)` fringes only where the image has contrast. [1]
- CA is a coloured linear or zoom blur, where each sample gets its own colour weight. [2]
- **Chromatic motion:** feed R the current frame, G the previous frame's R and B the frame before that, so red leads motion and blue trails by ~2 frames. It looks best with steady camera moves. [11]
- **Use it with intent:** it signals urgency, damage or cinematic emphasis. Careless use distracts, and a game ships an off switch for it. In a video, keep the strong presets to accents of 0.5–3 s. [11]
- **Ranges that hold up:** HyperFrames' tested CRT recipe keeps channel separation at 0–0.12 and rejects large colour fringes. Its VHS recipe uses 0.08–0.22. [29]
- Remotion's built-in `chromaticAberration({amount: 8, angle: 0})` is a linear split in pixels. A radial lens look needs a custom shader. [27]

## Presets
| Preset | Look | Key values (1080p, 30 fps) |
|---|---|---|
| `lens-subtle` | Real-lens fringe, invisible on faces | radial: R ×1.004, G ×1.002, B ×1.0; corner R–B offset 4.4 px, mid-edge 3.8 px; static |
| `radial-strong` | Obvious rainbow toward the edges, clean centre | radial a = 0.006 → 13 px at the corners; keep the subject in the central 40% (< 5 px there) |
| `linear-split` | Flat horizontal red/blue offset, graphic | `rgbashift=rh=-6:bh=6`; Remotion `amount: 6, angle: 0` |
| `acid-trip` | Breathing split, trails, hue cycle | R scale 1.012 ± 0.012 and B 0.988 ∓ 0.012 on a 1.5 s sine (peak 53 px at the corners); `lagfun` decay 0.82; hue +72°/s; saturation 1.25; ≤ 4 s |

## Timing and numbers
- Offsets are in pixels at 1080p. Scale them with frame height: ×0.667 at 720p and ×2 at 2160p. In 9:16 (1080×1920) the corner radius is the same 1101 px, so the same values apply.
- Radial scale `a` gives a corner R–B offset of 2a × 1101 px: a 0.002 → 4.4 px, a 0.004 → 8.8 px, a 0.006 → 13 px.
- Accent hit: ramp `a` 0 → 0.006 over 3 frames, hold 4–8 frames, release over 6 frames (ease-out). Pair it with a 1.00 → 1.04 scale punch.
- Text and UI: keep a linear split ≤ 2 px over text under 40 px tall, or put text on its own untreated layer.

## Build it
**ffmpeg (radial lens, tested on FFmpeg 9.0.2):** scale the R and G planes slightly, crop all three planes back to the frame centre, then merge.
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)   # generated inputs are endless: always cap the output
ffmpeg -i in.mp4 -filter_complex "[0:v]format=gbrp,split=3[cr][cg][cb];\
[cr]extractplanes=r,scale=iw*1.0040:ih*1.0040:flags=bicubic,crop=1920:1080[R];\
[cg]extractplanes=g,scale=iw*1.0020:ih*1.0020:flags=bicubic,crop=1920:1080[G];\
[cb]extractplanes=b[B];[G][B][R]mergeplanes=0x001020:gbrp,format=yuv420p[v]" \
-map "[v]" -map '0:a?' -t "$DUR" -c:v libx264 -crf 16 -c:a copy out.mp4
```
- Linear: `format=gbrp,rgbashift=rh=-6:bh=6:edge=smear`. For YUV-only work, `chromashift=cbh=-4:crh=4` shifts chroma instead.
- Animated radial (`acid-trip`): give each plane its own `perspective=...:eval=frame` zoom whose scale is a function of the frame index `in`. The full chain is in `assets/presets/chromatic-aberration.json`.

**HyperFrames:** on the real `<video>`, set `data-color-grading='{"effects":{"chromaticAberration":0.06,"chromaticAngle":0}}'` (0–0.12). For transitions use the registry block `chromatic-radial-split`, for wipes `chromatic-aberration-wipe`, and for captions `caption-glitch-rgb`. For the radial lens look, write a WebGL layer that samples the video texture with the GM Shaders radial loop, with time from the timeline.

**Remotion:** `<Video src=… effects={[chromaticAberration({amount: 6, angle: 0})]}/>` from `@remotion/effects/chromatic-aberration` (v4.0.467+). Drive `amount` with `interpolate(frame, …)` for hits.

## Mistakes that look amateur
- A flat RGB shift used as "lens" CA, with the same fringe at the centre as at the edges → use the radial model.
- Fringes on the face or the logo in the centre → radial with the subject in the central 40%, or protect the subject with a mask.
- Three hard ghost copies → blend 8–10 weighted samples, or keep the split ≤ 6 px.
- Running `eq` or `vignette` after `format=gbrp` in ffmpeg: they treat the G plane as luma and tint the image green or magenta → grade in YUV, then convert.
- CA left on for a whole talking-head video → accent for 0.5–3 s, or the subtle preset only.
- Splitting text the viewer must read → keep text on an untreated layer above.

## Sources
[1] Xor (@XorDev) — chromatic aberration hack — https://x.com/XorDev/status/1831738521935360079
[2] Xor (@XorDev) — types of blur shaders — https://x.com/XorDev/status/1762944762787647954
[10] FFmpeg Filters Documentation — https://ffmpeg.org/ffmpeg-filters.html
[11] Xor — GM Shaders Mini: Chromatic Aberration — https://mini.gmshaders.com/p/gm-shaders-mini-chromatic-aberration
[16] Wikipedia — Chromatic aberration — https://en.wikipedia.org/wiki/Chromatic_aberration
[27] Remotion — chromaticAberration() — https://www.remotion.dev/docs/effects/chromatic-aberration
[29] HyperFrames — media-treatment recipes — https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/media-treatment-recipes.md
