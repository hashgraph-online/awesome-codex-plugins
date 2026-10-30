# Glow and bloom

Makes the bright parts of real footage glow: a neutral soft bloom, a thin red film halation, coloured halos (sci-fi cyan, sunset amber, ominous red) or long anamorphic streaks. Use it on night exteriors, neon, practical lights, product hero shots and dream or flashback beats. Works in 16:9, 9:16 and 1:1, for whole shots of 3–10 s.

## How the pros do it
- **Threshold, blur, add.** Bloom takes the brightest pixels, blurs them and adds them back on top. Blooming the whole image looks "washed out and hazy", so only selected pixels may contribute. [12][13]
- **Soft threshold, never a hard cut:** `smoothstep(0.6, 0.8, luma)`, so a luma of 0.7 contributes 50%. Sapphire Glow's default threshold is 0.5. [12][14]
- **Blur at several scales and sum them:** a tight core plus wider halos (Kawase-style progressive blur). A single Gaussian holds too much energy in the middle and loses the fine core. [3][12][2]
- **Spread colour channels differently** for a natural halo: Sapphire's defaults are width R 1.0, G 1.2, B 1.4, and its combine mode is Screen. [14]
- **Add bloom before tone mapping** (HDR, then `1 - exp(-hdr·exposure)`), so added light compresses instead of clipping. On 8-bit footage, use Screen rather than Add for the same effect. [13]
- **Halation is not bloom.** It is red-orange, because light reflects off the film base back into the red-sensitive layer, and it hugs bright points and edges. [15] It erodes edges only in some circumstances, so keep it local to hard, bright edges. [7]
- **Use texture to take the clinical edge off**, not a blunt diffusion over the whole frame. [8]

## Presets
| Preset | Look | Key values (1080p) |
|---|---|---|
| `soft-default` | Neutral multi-scale bloom | knee 0.55–0.85; σ 6 / 24 / 72 px; gain 0.6; screen |
| `film-halation` | Thin red-orange rim on hard highlights | knee 0.70–0.95; σ 4 / 14 px; tint #E6401A (mix rr .9 gg .25 bb .06); stays within ~20 px of the edge |
| `scifi-cyan` | Cool cyan halo on screens and neon | knee 0.50–0.80; σ 8 / 32 / 96 px; tint #33BFFF |
| `sunset-warm` | Wide amber golden-hour lift | knee 0.45–0.80; σ 10 / 40 / 120 px; tint #FF8C33 |
| `anamorphic-streaks` | Long horizontal blue streaks plus a small core | knee 0.60–0.90; streak σH 140 / σV 1.5 px; core σ 10; tint #5A99FF |
| `ominous-red` | Darkened base, deep red bleed | base curve 0/0 0.5/0.35 1/0.9; knee 0.35–0.70; σ 20 / 80 px; tint #E6140D |

## Timing and numbers
- Sigma scales with frame height: ×0.667 at 720p, ×2 at 4K. Keep the ratios between scales near 1 : 4 : 12.
- Halation radius: σ ≤ 14 px at 1080p. Larger reads as bloom, not film.
- Animate gain, not threshold: a 0 → 1 fade over 12–18 frames with ease-out (`power2.out`). Moving the threshold makes highlights pop in and out.
- Keep text legible: no bloom behind captions. Put captions on an untreated layer, or keep glow gain ≤ 0.4 in the caption safe zone.
- Cost: three large Gaussians at 1080p ran at ~0.4× real time on an M-series laptop (FFmpeg 9.0.2). Use `steps=3` for σ ≥ 16.

## Build it
**ffmpeg (soft-default, tested):**
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)   # generated inputs are endless: always cap the output
ffmpeg -i in.mp4 -filter_complex "[0:v]format=gbrp,split=2[base][hi];\
[hi]curves=all='0/0 0.55/0 0.85/1 1/1',split=3[h0][h1][h2];\
[h0]gblur=sigma=6[g0];[h1]gblur=sigma=24:steps=3[g1];[h2]gblur=sigma=72:steps=3[g2];\
[g0][g1]blend=all_mode=addition:shortest=1[a];[a][g2]blend=all_mode=addition:shortest=1,colorchannelmixer=rr=0.6:gg=0.6:bb=0.6[glow];\
[base][glow]blend=all_mode=screen:shortest=1,format=yuv420p[v]" -map "[v]" -map '0:a?' -t "$DUR" -c:v libx264 -crf 16 out.mp4
```
- The curve thresholds per channel, so a red neon sign glows red. Tint the glow with `colorchannelmixer` before the screen blend.
- Streaks: `gblur=sigma=140:sigmaV=1.5` is an anamorphic horizontal blur in one filter.
- Work in `gbrp` for blending. `blend=addition` on YUV chroma planes shifts colour.
- Every preset's full chain is in `assets/presets/glow-bloom.json`.

**HyperFrames:** on the real `<video>`, animate `--hf-color-grading-bloom` (0–3) on the composition's paused GSAP timeline: put the first value inline and use a finite `tl.to(el, {"--hf-color-grading-bloom": 1.2, duration: 0.5})`. Bloom is a multipass effect, so avoid more than two full-frame bloom layers at once. [30] For coloured multi-scale glow or halation, render a WebGL layer (threshold pass, then three separable Gaussians, then a screen composite) driven by timeline time.

**Remotion:** stack `glow()` passes for multi-scale: `[glow({radius: 8, threshold: 0.6, intensity: 0.5}), glow({radius: 32, threshold: 0.6, intensity: 0.4}), glow({radius: 96, threshold: 0.6, intensity: 0.3})]` (`@remotion/effects/glow`; radius in px, threshold 0–1, colour). [26] For streaks, `lightTrail({direction: 0, distance: 220, threshold: 0.7})` plus the mirrored direction 180.

## Mistakes that look amateur
- Global glow with threshold 0 (haze over everything, milky blacks) → knee ≥ 0.45, and keep shadows untouched.
- One huge Gaussian (blob with no core) → 2–3 scales, from 1 : 4 to 1 : 12.
- Halation as a big red cloud → σ ≤ 14 px, threshold ≥ 0.7, red-orange only at hard highlight edges.
- Hard threshold, so highlights flicker on and off between frames → use a smooth knee 0.25–0.3 wide.
- Clipped white cores after adding → use screen (8-bit) or add before tone mapping (HDR).
- Glow behind small captions → captions on an untreated layer above.

## Sources
[2] Xor (@XorDev) — types of blur shaders — https://x.com/XorDev/status/1762944762787647954
[3] Xor (@XorDev) — bloom at multiple scales — https://x.com/XorDev/status/1883916173231759858
[7] Steve Yedlin (@steveyedlin) — halation and edge erosion — https://x.com/steveyedlin/status/1515462800629542912
[8] Steve Yedlin (@steveyedlin) — texture vs blunt diffusion — https://x.com/steveyedlin/status/1610039110445727745
[12] Xor — GM Shaders Mini: Bloom — https://mini.gmshaders.com/p/gm-shaders-mini-bloom
[13] LearnOpenGL — Bloom — https://learnopengl.com/Advanced-Lighting/Bloom
[14] Boris FX — Sapphire S_Glow — https://borisfx.com/documentation/sapphire/ae/glow/
[15] Analog.Cafe — Halation in film photography — https://www.analog.cafe/r/halation-in-film-photography-i3q4
[26] Remotion — glow() — https://www.remotion.dev/docs/effects/glow
[30] HyperFrames — grading reference — https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/grading.md
