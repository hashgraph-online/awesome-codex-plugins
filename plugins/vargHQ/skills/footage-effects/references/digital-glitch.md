# Digital glitch

Glitches real footage in short deterministic bursts: RGB channel splits, torn and sheared rows, swapped blocks, frame stutter with jitter, and posterized macroblock corruption. Use it for tech, gaming, music and hacker beats, for transitions, and to sell "signal lost". Works in 16:9, 9:16 and 1:1. Use bursts of 2–6 frames across 1–8 s; the strong presets stay ≤ 1.5 s.

## How the pros do it
- **Separate controls for size, rate and duration.** Pro block-glitch tools expose block size, breakup and displacement amounts, glitch rate (how often) and glitch duration (how long) as separate controls. Tune rate and duration first, then size. [35]
- **Small and wide glitches are different layers,** each with its own maximum, plus a global size, a displacement amount and a random seed to vary layers. RGB split examples run from 15 to −60, and negative values flip the direction. [34]
- **Compression as a glitch ingredient:** subtle up to 50%, heavy above. Applying it last blends the glitches into the footage. [34]
- **Datamosh:** a share of macroblocks (intensity 0.7) locks and smears along motion (drift 0.35), with 48 px blocks. Churn 0.4 controls how often each block re-rolls, and low churn lets corrupted regions persist. [36]
- **Procedural, not stock:** build glitches from noise-driven displacement and a colour glow, so they can be timed to the edit. [9][37]
- **Restraint for real footage:** HyperFrames' VHS recipe allows only rare horizontal row tears (digitalGlitch 0.2–0.4, line tear 0.04–0.1), with colour split, block displacement and pixelation at zero. It rejects hard edge tearing and face smearing. [29]

## Presets
| Preset | Look | Key values (1080p, 30 fps) |
|---|---|---|
| `subtle` | Rare thin row tears, small split | 2-frame windows, hit probability 0.12 (~1.8 hits/s); RGB split 8 px; row tear 8–40 px tall, shift 20 px |
| `default` | Readable bursts | p 0.30; split 24 px; sheared band 32–128 px, shift ±40; one swapped 240×48 block |
| `intense` | Half the frames hit | p 0.55; split 48 px; bands 64–256 px, shift ±120; block 320×64; temporal noise 10; ≤ 1.5 s |
| `jittery` | 12 fps stutter, frame jumps | `fps=12` hold; whole-frame jitter ±16 px on 1-frame windows, p 0.5; split 12 px |
| `corrupt` | Codec corruption | 3-frame windows, p 0.4; a 384×96 region of 32 px macroblocks posterized to 4 levels; split 32; block 256×64 |

## Timing and numbers
- Hits live on windows of 2 frames (66 ms) at 30 fps. One-frame flashes read as dropped frames, and windows longer than 4 frames read as broken footage.
- Gate: `hash(floor(n/2)) < p`, with hash = fract(sin(k·12.9898)·43758.5453). The same frame always gives the same glitch, so renders are seekable and parallel-safe.
- On cuts, force a hit on the 2 frames before and after the cut (p = 1 inside that window) for a glitch transition.
- Sync with audio: put hits on snare or hat transients. Leave ≥ 8 clean frames between bursts in `subtle` and `default`.
- Faces and logos: keep split ≤ 12 px across a face in close-up, and never cover a logo with a swapped block for more than 2 frames.

## Build it
**ffmpeg (default, tested):** split R and B by per-frame `crop` x expressions (G stays put), then `swaprect` a full-width band with a sideways-shifted copy of itself (a shear) and swap one random block. Every value is a function of `n`, with no `random()` calls.
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)   # generated inputs are endless: always cap the output
H='(sin(floor(n/2)*12.9898)*43758.5453-floor(sin(floor(n/2)*12.9898)*43758.5453))'
H2='(sin(floor(n/2)*78.233)*43758.5453-floor(sin(floor(n/2)*78.233)*43758.5453))'
G="lt($H,0.3)"
ffmpeg -i in.mp4 -filter_complex "[0:v]format=gbrp,split=3[a][b][c];\
[a]extractplanes=r,crop=w=iw-48:h=ih:x='24+if($G,24*(2*$H2-1),0)':y=0,pad=iw+48:ih:24:0,fillborders=left=24:right=24:mode=smear[R];\
[b]extractplanes=g[Gp];\
[c]extractplanes=b,crop=w=iw-48:h=ih:x='24-if($G,24*(2*$H2-1),0)':y=0,pad=iw+48:ih:24:0,fillborders=left=24:right=24:mode=smear[B];\
[Gp][B][R]mergeplanes=0x001020:gbrp,\
swaprect=w='w-80':h='if($G,32+floor(96*$H2),2)':x1=40:y1='floor($H*(h-140))':x2='if($G,40+floor(80*($H-0.5)),40)':y2='floor($H*(h-140))+2',\
swaprect=w='if($G,240,2)':h='if($G,48,2)':x1='floor($H2*(w-240))':y1='floor($H*(h-48))':x2='floor($H*(w-240))':y2='floor($H2*(h-48))',\
format=yuv420p[v]" -map "[v]" -map '0:a?' -t "$DUR" -c:v libx264 -crf 16 out.mp4
```
- In `swaprect`, `w` and `h` are the frame size (lowercase). When a hit is off, the rectangles collapse to 2 px.
- Jitter: `fps=12,fps=30` for the stutter, then a per-frame `crop` with x and y from the hash, then `scale` back to 1920×1080.
- Corruption: `pixelize=w=32:h=32` and `lutrgb='floor(val/64)*64'` on a copy, then `crop` a hashed region and `overlay` it with `enable='gate'`.
- All five chains are in `assets/presets/digital-glitch.json`.

**HyperFrames:** use the registry block `glitch` (shader transition) between shots, `rgb-glitch-text` or `caption-glitch-rgb` for type, and the `scan-band` component for a branded sweep. On footage, use the `digitalGlitch*` treatment keys (`digitalGlitch`, `digitalGlitchColorSplit`, `digitalGlitchLineTear`, `digitalGlitchBlockAmount`, `digitalGlitchBlockDisplacement`, `digitalGlitchPixelate`, `digitalGlitchSpeed`). Start from the VHS recipe values and raise the split and blocks for the louder presets. [29]

**Remotion:** `chromaticAberration({amount: 24 * gate})` on `<Video>`, with `gate` computed from `frame` by the same hash. `@remotion/effects` also exports `tear`, `pixelate` and `white-noise`; check their docs pages for params.

## Mistakes that look amateur
- Constant glitching for the whole shot → bursts on 2-frame windows with p ≤ 0.3, except as a ≤ 1.5 s transition.
- `random()` or wall-clock noise (different on every render, breaks parallel rendering) → hash the frame number.
- Glitch frames that ignore the music → hits on transients.
- Splitting a face by 40+ px in close-up → ≤ 12 px across faces.
- Every layer the same size → mix small (8–40 px) tears with a few wide bands.
- Glitch bursts landing on the logo or call to action → keep the end card and the logo clean for the last 1 s.

## Sources
[9] Andrew Kramer (@videocopilot) — Colorful Glitch FX — https://x.com/videocopilot/status/970977859568201732
[10] FFmpeg Filters Documentation — https://ffmpeg.org/ffmpeg-filters.html
[29] HyperFrames — media-treatment recipes — https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/media-treatment-recipes.md
[34] Maxon — Red Giant Universe Glitch Transition — https://help.maxon.net/rg/en-us/Content/html/glitch-transition.html
[35] Notch — Block Glitch — https://manual.notch.one/1.0/en/docs/reference/nodes/post-fx/stylisation/block-glitch
[36] shaders.com — DataMosh — https://shaders.com/docs/components/datamosh
[37] Video Copilot blog — Colorful Glitch FX — http://www.videocopilot.net/blog/2018/03/new-tutorial-colorful-glitch-fx-100-ae/
