# Footage effects demo

The skill's preview video: four presets applied to real footage, 3.6 s each, 1920x1080 at 30 fps.

| # | Preset | Footage |
|---|---|---|
| 1 | `glow-bloom.film-halation` | Rooftops in low sun (Tears of Steel, 05:29) |
| 2 | `crt-screen.consumer-tv` | Close-up in the lab (06:38) |
| 3 | `digital-glitch.default` | Robot battle (07:49) |
| 4 | `halftone-footage.ink-on-paper` | Two people on a bridge (00:28) |

## Make it

```bash
# 1. Cut 16:9 clips from the 720p master (CC BY 3.0) and bring them to 1080p30
U=https://mirrors.dotsrc.org/blender/blender-demo/movies/ToS/tears_of_steel_720p.mov
i=0; for t in 329 398 469 28; do i=$((i+1))
  ffmpeg -ss $t -t 3.6 -i "$U" -vf "crop=ih*16/9:ih,scale=1920:1080:flags=lanczos,fps=30,format=yuv420p" -an -c:v libx264 -crf 12 c$i.mp4
done

# 2. Apply the presets exactly as the JSON gives them
node run-preset.mjs c1.mp4 glow-bloom film-halation fx1.mp4 3.6
node run-preset.mjs c2.mp4 crt-screen consumer-tv fx2.mp4 3.6
node run-preset.mjs c3.mp4 digital-glitch default fx3.mp4 3.6
node run-preset.mjs c4.mp4 halftone-footage ink-on-paper fx4.mp4 3.6

# 3. Join with hard cuts (the preview also burns a small label and the credit on each clip)
printf "file fx1.mp4\nfile fx2.mp4\nfile fx3.mp4\nfile fx4.mp4\n" > list.txt
ffmpeg -f concat -i list.txt -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart footage-effects.mp4
```

`run-preset.mjs` reads `assets/presets/<template>.json`, passes the preset's generated inputs and filter graph to
ffmpeg, and caps the output with `-t` (generated inputs never end). Any other preset runs the same way.

## Deviations

- The source is the 720p master, cropped from 2.39:1 to 16:9 and scaled to 1080p, so it is softer than a real 1080p
  camera file. The presets' pixel values assume 1080p, which is why the clips are scaled up first.
- The preview's final encode is CRF 27 to stay under 8 MB; for delivery use CRF 14-16 on anything with grain, dots or
  scanlines, as the skill says.

## Credits

Footage: Tears of Steel, (CC) Blender Foundation | mango.blender.org, licensed CC BY 3.0. Labels set in JetBrains Mono
(OFL-1.1).
