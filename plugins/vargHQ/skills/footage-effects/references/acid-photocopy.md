# Acid photocopy

Turns real footage into a stuttering photocopy: two spot inks (teal shadows, red mid-tones jumping out of register) or one black toner, on scanned cream paper with toner grain and drum streaks. Use it for flyer-style music promos, club and event ads, zine intros and lo-fi product drops. Works in 16:9, 9:16, 1:1 and 4:5. Shots run 2–8 s.

## How the pros do it
- **Kill the mid-tones:** copier contrast is binary. Threshold or crush the levels (for example black point 41, white point 214) before adding texture. A median of 1–2 px first removes fine detail that would turn into noise. [41][42]
- **Toner speckle:** grain or speckle at high intensity (98, contrast 11), heavy monochrome noise (162%) and a 1.7 px Gaussian, so speckles clump like toner. [41]
- **Striped or smudged copies:** a horizontal motion blur (distance 11, or 208 for a smear) plus a coarse halftone or mezzotint gives drum streaks and smudges. [41]
- **Real spot-ink colours, not RGB:** Riso Teal #00838A (Pantone 321 U), Riso Red #FF665E (Warm Red U), Bright Red #F15060 (185 U), Fluorescent Pink #FF48B0 (806 U), Blue #0078BF (3005 U), Yellow #FFE800. [43]
- **Two inks overprint by multiplying,** with a small registration offset. HyperFrames' two-ink treatment maps warm mid-tones to vermilion and cool shadows to teal, with separate screens and a subtle fixed registration offset on warm paper. It rejects results that read as "a red tint with dots". [29]
- **Grain is texture,** not damage, when it has the right character and amount. Keep toner grain temporal (it moves) and paper texture static (it does not). [8]
- **Dither or threshold** is a stylization tool. Ordered palette dither with an explicit dark-to-light palette (2–6 colours) is the HyperFrames equivalent. [4][29]

## Presets
| Preset | Look | Key values (1080p, 30 fps) |
|---|---|---|
| `stutter-flyer` | 8 fps two-ink copy | hold 8 fps; teal #00838A below the 25th luma percentile (≈ 70/255), red #FF665E below the 60th (≈ 140); paper #F2EAD3 with static noise 14; toner noise 28 temporal; contrast 1.5; red misregistration ±5 px x / ±2.5 px y re-rolled every held frame |
| `still-print` | Slow 2 fps poster print | hold 2 fps; same inks; toner 18; red fixed 6 px right and down; contrast 1.4 |
| `mono-toner` | One black toner, zine copy | hold 12 fps; ink #1A1A1A on #EDE8DC below the 45th percentile (≈ 110); toner 32; static 1 px vertical drum streaks, 0–18% darkening |

## Timing and numbers
- Stutter: hold 6–10 fps for a flyer, 2 fps for a print, 12 fps for a zine. Re-roll registration and toner on each held frame, not every output frame.
- Thresholds: measure luma with `signalstats` (YLOW, YAVG, YHIGH) and set T_teal = YLOW + 0.25·(YHIGH − YLOW), T_red = YLOW + 0.6·(YHIGH − YLOW). Fixed 70/140 suits well-exposed footage only.
- Misregistration: 3–6 px at 1080p. Beyond 10 px it reads as a bug, not print.
- Type over it: a heavy grotesk such as Archivo Black (OFL-1.1) in one of the two inks, or knocked out of the paper colour. Never use pure white text on the cream paper.
- Edit rhythm: cut on the held frames (every 4th output frame at 8 fps) so cuts never land mid-hold.

## Build it
**ffmpeg (stutter-flyer, tested):** hold the frames, threshold the luma twice, map each mask to a spot ink with `lutrgb`, offset the red plate by a per-hold hash, multiply the two plates, then multiply onto static paper.
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)   # generated inputs are endless: always cap the output
J='(sin(floor(t*8)*12.9898)*43758.5453-floor(sin(floor(t*8)*12.9898)*43758.5453))'
ffmpeg -i in.mp4 \
 -f lavfi -i "color=c=0xF2EAD3:s=1920x1080:r=30,format=gbrp,noise=alls=14:allf=u,gblur=sigma=0.8,trim=end_frame=1,loop=-1:size=1" \
 -filter_complex "[0:v]fps=8,fps=30,format=gray,eq=contrast=1.5:brightness=0.04,noise=alls=28:allf=t+u,gblur=sigma=1.2,split=2[k1][k2];\
[k1]lutyuv=y='if(lt(val,70),0,255)',format=gbrp,lutrgb=r='if(lt(val,128),0x00,255)':g='if(lt(val,128),0x83,255)':b='if(lt(val,128),0x8A,255)'[teal];\
[k2]lutyuv=y='if(lt(val,140),0,255)',format=gbrp,lutrgb=r='if(lt(val,128),0xFF,255)':g='if(lt(val,128),0x66,255)':b='if(lt(val,128),0x5E,255)',\
crop=w=iw-14:h=ih-14:x='7+10*($J-0.5)':y='7+5*($J-0.5)',pad=iw+14:ih+14:7:7:white[red];\
[red][teal]blend=all_mode=multiply:shortest=1[ink];[ink][1:v]blend=all_mode=multiply:shortest=1,format=yuv420p[v]" \
 -map "[v]" -map '0:a?' -t "$DUR" -c:v libx264 -crf 16 out.mp4
```
- The `t` flag in `noise` makes the toner move each frame; the paper noise has no `t` flag and is frozen with `loop`.
- Drum streaks (`mono-toner`): a 1920×1 noise row scaled to 1920×1080 with `flags=neighbor` makes vertical streaks. Lighten it with `curves` and multiply.
- All three chains are in `assets/presets/acid-photocopy.json`.

**HyperFrames:** pre-render the hold with `ffmpeg -vf fps=8,fps=30`, then on the `<video>` use Ordered Palette Dither with `{"effects":{"dither":1,"ditherSize":0.3},"palette":["#00838A","#FF665E","#F2EAD3"]}` (palette dark to light). Or use the fixed vermilion/teal Two-Ink Editorial Print (`twoInkPrint` 1, `twoInkPrintSize` 0.42). Do not stack it with `halftone`. [29] For a paper grain finish over the frame, the `paper-shaders` skill's `paper-finish` preset works on stills or exported frames.

**Remotion:** wrap the `<Video>` in `<Freeze frame={Math.floor(frame/4)*4}>` for an 8 fps hold at 30 fps. Layer two copies: `duotone({darkColor:'#00838A', lightColor:'#F2EAD3', threshold:0.3})`, and above it a red duotone with `mix-blend-mode: multiply`, offset by a frame-hashed 3–6 px.

## Mistakes that look amateur
- RGB red and cyan instead of spot inks → Riso hex values with Pantone references.
- Smooth gradients left in → threshold to 2–3 levels.
- Toner grain frozen, or paper texture swimming → toner temporal, paper static.
- Misregistration moving every output frame (vibration) → re-roll only on held frames, 3–6 px.
- Fixed thresholds on dark footage (a solid teal slab) → percentile thresholds from `signalstats`.
- Stutter on top of fast cuts (unreadable) → hold ≥ 3 held frames per shot, and cut on hold boundaries.

## Sources
[4] Xor (@XorDev) — dithering for stylization — https://x.com/XorDev/status/1883915548502995174
[8] Steve Yedlin (@steveyedlin) — grain and noise as texture — https://x.com/steveyedlin/status/1610040392296337409
[10] FFmpeg Filters Documentation — https://ffmpeg.org/ffmpeg-filters.html
[29] HyperFrames — media-treatment recipes — https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/media-treatment-recipes.md
[41] Monika Zagrobelna (Envato Tuts+) — How to create photocopy and xerox textures — https://design.tutsplus.com/tutorials/how-to-create-photocopy-and-xerox-textures--cms-109034
[42] Photoshop Roadmap — Colorful xerox photocopy effect — https://www.photoshoproadmap.com/create-a-colorful-xerox-photocopy-effect-in-photoshop/
[43] Matt DesLauriers — riso-colors (from stencil.wiki) — https://github.com/mattdesl/riso-colors
