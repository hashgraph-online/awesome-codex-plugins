# Wave and heat distortion

Makes real footage ripple: fine rising heat haze over hot ground, a broad water wobble, a clean travelling sine wave, or the footage smearing itself along its own brightness. Use it for heat, dreams, underwater, psychedelic and transition beats. Works in 16:9, 9:16 and 1:1. Shots run 3–8 s (looks) or 0.5–1 s (transitions).

## How the pros do it
- **Displace with a moving noise map.** Offset the screen UVs by a scrolling normal or noise map, at a perturbation scale around 0.05 UV. Water used 0.075 and glass 0.2. Mask the effect so foreground objects do not leak into the refraction. [38]
- **Two layers for heat:** a coarse matte (Turbulent Displace amount 245, size 100, feathered 250 px) shapes where the heat is. A fine adjustment layer (amount 30, size 30) does the shimmer, with evolution at one full turn per 5 s and a small blur (Fast Blur 4) to hide stepping. [39]
- **Heat is mask-driven:** controlling intensity with a mask beats hand-tuning plain displacement and fractal noise. Use it subtly. [40]
- **Turbulence:** for fluid motion, add perpendicular sine waves over several iterations. More iterations add finer, more liquid detail. [5]
- **Self-driven distortion:** for "pushed around by its own colours", use the clip's own blurred luma as the displacement map, so bright areas shove pixels.
- **Remotion turbulentDisplace semantics:** amount in px (default 50), size = largest noise feature in px (100), complexity 1–10 noise layers, evolution in degrees with an optional loop, pinning to keep the edges fixed. Drive evolution from the frame number. [25]

## Presets
| Preset | Look | Key values (1080p, 30 fps) |
|---|---|---|
| `heat-haze` | Fine rising shimmer, strongest at the bottom | ±4 px x, ±2 px y; Perlin 3 octaves, persistence 0.5, xscale 4 / yscale 8; rises ≈ 97 px/s; evolution tscale 0.6; mask 0 above 35% of height → full below 75%; post-blur σ 0.7 |
| `water-ripple` | Slow broad wobble | ±12 px both axes; Perlin 2 octaves, scale 2/2; tscale 0.3; edge mirror |
| `self-smear` | Footage pushes itself, with trails | map = own luma blurred σ 24 (contrast 0.35 → ±40 px x; inverted, 0.2 for y); `lagfun` 0.9 trails |
| `sine-wave` | Clean travelling ripple | amplitude 10 px, wavelength 180 px, 0.5 cycles/s, rows shift horizontally |

## Timing and numbers
- Amplitude guide at 1080p: heat 2–6 px, water 8–16 px, dream 16–40 px. Scale with frame height.
- Heat rises: scroll the map upward at 60–120 px/s, while the noise itself evolves at a different rate, or it looks like a sliding texture.
- Evolution loop: one turn per 5 s (72°/s) for the fine layer. [39] For seamless loops set Remotion `cycleEvolution: true`.
- Transition use: ramp amplitude 0 → 40 px → 0 over 16 frames around the cut (`sine.inOut`), and crossfade at the peak.
- `displace` moves by whole pixels: add `gblur` σ 0.6–0.8 afterwards, or render at 2× and downscale, to remove stair-steps.

## Build it
**ffmpeg (heat-haze, tested):** seeded `perlin` sources make the X and Y maps (128 = no shift; `eq=contrast` sets the amplitude). They are scrolled upward, displaced in `gbrp` so all planes move together, and masked to the lower frame.
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)   # generated inputs are endless: always cap the output
ffmpeg -i in.mp4 \
 -f lavfi -i "perlin=s=480x270:r=30:octaves=3:persistence=0.5:xscale=4:yscale=8:tscale=0.6:random_mode=seed:seed=7,format=gray,scroll=vertical=0.003,scale=1920:1080:flags=bicubic,eq=contrast=0.06,format=gbrp" \
 -f lavfi -i "perlin=s=480x270:r=30:octaves=3:persistence=0.5:xscale=4:yscale=8:tscale=0.6:random_mode=seed:seed=11,format=gray,scroll=vertical=0.003,scale=1920:1080:flags=bicubic,eq=contrast=0.03,format=gbrp" \
 -f lavfi -i "color=c=black:s=1920x1080:r=30,format=gray,geq=lum='255*clip((Y/H-0.35)/0.4,0,1)',trim=end_frame=1,loop=-1:size=1,format=gbrp" \
 -filter_complex "[0:v]format=gbrp,split[o][s];[s][1:v][2:v]displace=edge=smear,gblur=sigma=0.7[d];[o][d][3:v]maskedmerge,format=yuv420p[v]" \
 -map "[v]" -map '0:a?' -t "$DUR" -c:v libx264 -crf 16 out.mp4
```
- Map amplitude: `eq=contrast=c` on a Perlin map gives about ±64·c px (contrast 1 measured 61–190 around 128).
- Always seed Perlin (`random_mode=seed:seed=N`). The default random seed changes on every render.
- Self-smear: `split`, then `format=gray,gblur=sigma=24,eq=contrast=0.35` makes the X map, and the `negate` version the Y map. Finish with `displace` and `lagfun=decay=0.9`.
- All chains are in `assets/presets/wave-distortion.json`.

**Remotion:** `turbulentDisplace({amount: 6, size: 40, complexity: 3, evolution: interpolate(frame,[0,150],[0,360]), pinning: 'all-locked'})` for heat, and `{displacement: 'turbulent-smoother', amount: 24, size: 220, complexity: 2}` for water. `wave({amplitude: 10, wavelength: 180, direction: 'vertical', phase})` for the sine. [25]

**HyperFrames:** the registry has `thermal-distortion` (heat-haze shader transition), `transitions-distortion`, `ripple-waves` and `ripples`. On footage, write a WebGL layer over the `<video>` texture with the turbulence loop (`p += sin(p.yx*freq + t)/freq`, rotated each iteration) and `t` from the timeline.

## Mistakes that look amateur
- Displacing YUV with gray maps: chroma does not move, so colour fringes appear → displace in `gbrp` with `gbrp` maps.
- A global offset because the map mean is not 128 (the whole picture drifts) → check `signalstats` YAVG ≈ 128 and convert gray → gbrp, not gray → yuv420p (range shift).
- Heat haze over the whole frame including the sky → mask it to the hot area, with ≥ 25% of frame height of feather.
- Stair-stepped edges → blur σ 0.6–0.8 after `displace`, or work at 2×.
- Noise that only slides (texture scroll) → evolve and scroll at different rates.
- Unseeded noise → seed every noise source.

## Sources
[5] Xor (@XorDev) — turbulence — https://x.com/XorDev/status/2008979114544509285
[10] FFmpeg Filters Documentation — https://ffmpeg.org/ffmpeg-filters.html
[25] Remotion — turbulentDisplace() — https://www.remotion.dev/docs/effects/turbulent-displace
[38] Tiago Sousa — GPU Gems 2 ch.19, Generic Refraction Simulation — https://developer.nvidia.com/gpugems/gpugems2/part-ii-shading-lighting-and-shadows/chapter-19-generic-refraction-simulation
[39] Caleb Ward (PremiumBeat) — How to create heat waves in After Effects — https://www.premiumbeat.com/blog/how-to-create-heat-waves-in-after-effects/
[40] Video Copilot — Heat Distortion plug-in — http://www.videocopilot.net/blog/2013/10/new-heat-distortion-plug-in-sneak-peak/
