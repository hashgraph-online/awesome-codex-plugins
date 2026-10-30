# CRT screen

Shows real footage on a curved CRT: low-line picture, scanlines, phosphor mask, bloom, rounded dark corners and optional afterglow. A monochrome terminal variant suits chat and UI scenes. Use it for retro, archive, gaming and "watching it on TV" beats. Works best in 16:9 or 4:3 (1:1 is fine). Shots run 3–8 s.

## How the pros do it
- **Two stages:** first the signal (YIQ, limited chroma bandwidth, imperfect luma/chroma separation, ghosting, noise), then the display (scanlines, mask, curvature, bezel). Colour bleed should come from the signal stage, not be painted on. [6]
- **Scanline beam width grows with brightness:** bright lines get fatter and fill the gaps, so dark lines show only in darker areas. In crt-geom the scanline weight defaults to 0.3, and its beam profile tightens to a Gaussian at width 2. [17][19]
- **Mask types:** aperture grille (vertical RGB stripes, sharpest, easiest to emulate at 1080p), slot mask (consumer TVs) and shadow/dot mask (monitors). crt-lottes uses maskDark 0.5 / maskLight 1.5 with shadowMask 1 = TV, 2 = aperture grille, 3/4 = VGA. [18][19]
- **Geometry:** crt-geom projects onto a sphere (radius 2.0, distance 1.6) and rounds the corners (corner size 0.03). crt-lottes warps with warpX 0.031 and warpY 0.041. Aperture-grille tubes curve less. [17][18]
- **Halation:** a glow around bright areas from light passing through the tube glass, strongest on dark backgrounds. Phosphor persistence (afterglow) leaves trails. Convergence errors grow toward the edges. Vignette. [19]
- **Gamma:** emulate the tube at 2.4 (CRTgamma) and output at 2.2. Otherwise the mask and scanlines darken the picture too much. [17]
- **Restraint on ordinary footage:** HyperFrames' tested recipe uses curvature 0.08–0.28, scanlines 0.18–0.45 and channel separation 0–0.12. It rejects heavy black corners, unreadable UI and large fringes. [29]

## Presets
| Preset | Look | Key values (1080p) |
|---|---|---|
| `consumer-tv` | 360-line picture, soft TV | source 640×360 → 1080; scanline period 3 px (dark row 0.47); RGB stripe mask, off-phosphor 0.6; k1 0.10 k2 0.04; bloom σ 12 at 0.5; corner feather 14 px; vignette π/5 |
| `arcade-grille` | 270-line arcade, heavy lines | source 480×270; period 4 px (dark 0.35); grille 0.55; k1 0.06 k2 0.02; bloom σ 10 at 0.65; Lottes equivalent hardScan −8, hardPix −3, maskDark 0.5, maskLight 1.5, shadowMask 2 |
| `green-terminal` | P1 green mono, for chat/UI | phosphor #33FF66; no colour mask; period 3; afterglow `lagfun` 0.85; k1 0.12; bloom σ 14 at 0.7; text ≥ 36 px tall |
| `amber-terminal` | Amber mono monitor | phosphor #FFB000; afterglow 0.80; k1 0.10 k2 0.03; bloom σ 12 at 0.6 |

## Timing and numbers
- Source line count sets the period: 1080 / 360 = 3 px and 1080 / 270 = 4 px. Use integer periods only, or the lines beat into moiré.
- Brightness compensation: the mask plus scanlines remove about 35% of the light, so boost with `colorlevels` imax 0.82 (about +22%) before the bloom.
- Bloom: σ 10–14 px at 0.5–0.7. Afterglow: decay 0.8–0.88 (about 0.2–0.3 s trail at 30 fps).
- Power-on (optional): over 10 frames, scale Y 0.01 → 1 with brightness 2 → 1, then a 4-frame white flash on a centre line.
- Monochrome text in the terminal variant: VT323 (OFL-1.1), ≥ 36 px at 1080p, line height 1.2.

## Build it
**ffmpeg (consumer-tv, tested):** downscale and upscale (line count), grade in YUV, then in `gbrp` multiply by a pre-rendered mask texture, add bloom, multiply a corner mask, curve the tube and vignette.
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)   # generated inputs are endless: always cap the output
ffmpeg -i in.mp4 \
 -f lavfi -i "color=c=white:s=1920x1080:r=30,format=gbrp,geq=r='if(lt(mod(Y,3),2),255,120)*if(eq(mod(X,3),0),1,0.6)':g='if(lt(mod(Y,3),2),255,120)*if(eq(mod(X,3),1),1,0.6)':b='if(lt(mod(Y,3),2),255,120)*if(eq(mod(X,3),2),1,0.6)',trim=end_frame=1,loop=-1:size=1" \
 -f lavfi -i "color=c=black:s=1920x1080:r=30,format=gray,geq=lum='255*clip(min(min(X,W-1-X),min(Y,H-1-Y))/14,0,1)',trim=end_frame=1,loop=-1:size=1,format=gbrp" \
 -filter_complex "[0:v]scale=640:360:flags=area,scale=1920:1080:flags=bicubic,eq=contrast=1.1:saturation=1.15,format=gbrp[lo];\
[lo][1:v]blend=all_mode=multiply:shortest=1,colorlevels=rimax=0.82:gimax=0.82:bimax=0.82[m];[m]split[m1][m2];\
[m2]gblur=sigma=12,colorchannelmixer=rr=0.5:gg=0.5:bb=0.5[bl];[m1][bl]blend=all_mode=screen:shortest=1[lit];\
[lit][2:v]blend=all_mode=multiply:shortest=1,lenscorrection=k1=0.10:k2=0.04:i=bilinear:fc=black,format=yuv420p,vignette=angle=PI/5[v]" \
 -map "[v]" -map '0:a?' -t "$DUR" -c:v libx264 -crf 16 out.mp4
```
- Positive `k1` in `lenscorrection` gives the CRT pillow shape (picture pulled in, black curved borders).
- Generate the mask and corner textures once (`trim=end_frame=1,loop=-1`) instead of evaluating `geq` every frame.
- All four chains are in `assets/presets/crt-screen.json`.

**HyperFrames:** on the real `<video>`, use the CRT Display payload `{"intensity":1,"effects":{"crtCurvature":0.2,"scanlines":0.35,"scanlineCount":0.17,"scanlineSoftness":1,"chromaticAberration":0.08,"chromaticAngle":0}}`. [29] For a screen filmed from the room, use the registry component `filmed-screen` (perspective, depth of field, LED sub-pixels). For chat on a terminal, build the chat as DOM, then apply the treatment, or render it through the ffmpeg green-terminal chain.

**Remotion:** `@remotion/effects` ships `barrelDistortion({amount})` (default 0.25), `scanlines({amount: 0.15, spacing: 4, thickness: 1, offset})` and `glow()`. Stack them on `<Video>`: barrel 0.15–0.2, scanlines amount 0.35 with spacing 3, glow radius 12 at threshold 0.5.

## Mistakes that look amateur
- Non-integer scanline period after scaling (uneven lines, moiré) → integer periods of 3 or 4 px at the delivery size, and render at the final resolution.
- Mask and scanlines with no brightness compensation (murky picture) → about +22% gain, gamma 2.4 → 2.2, bloom.
- Using `eq` or `vignette` while frames are in `gbrp` (green or magenta cast) → grade in YUV before `format=gbrp` and vignette after converting back.
- Fish-eye curvature with huge black corners → k1 ≤ 0.12, curvature ≤ 0.28 in HyperFrames terms.
- A colour shadow mask on a monochrome terminal → no colour mask on mono tubes; scanlines and afterglow only.
- Small UI text under scanlines → ≥ 36 px text, or keep the UI sharp and add only a light scanline overlay.

## Sources
[6] komm64 (@komm64) — CRT shader signal path — https://x.com/komm64/status/2073558529097834584
[10] FFmpeg Filters Documentation — https://ffmpeg.org/ffmpeg-filters.html
[17] libretro — crt-geom.glsl — https://raw.githubusercontent.com/libretro/glsl-shaders/master/crt/shaders/crt-geom.glsl
[18] libretro — crt-lottes.glsl — https://raw.githubusercontent.com/libretro/glsl-shaders/master/crt/shaders/crt-lottes.glsl
[19] libretro forums — CRT effects list — https://forums.libretro.com/t/crt-effects-list/49051
[29] HyperFrames — media-treatment recipes — https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/media-treatment-recipes.md
