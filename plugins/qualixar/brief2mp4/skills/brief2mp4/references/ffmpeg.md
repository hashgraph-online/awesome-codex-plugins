# ffmpeg: finishing, joining, sound, checks

Every path ends here. The renderers make pictures; ffmpeg makes a file that plays everywhere and meets the delivery spec.

## The finish step

```bash
scripts/finish.sh --in render.mp4 --out final.mp4 --seconds 12               # silent track added
scripts/finish.sh --in render.mp4 --out final.mp4 --seconds 12 --audio bed.wav
scripts/finish.sh --in frames/   --out final.mp4 --seconds 8                 # a PNG sequence
scripts/finish.sh --in render.mp4 --out final.mp4 --seconds 12 --keep-audio  # keep the render's own sound
```

It fits the picture to the frame without stretching, forces the frame rate, holds the last frame if the render is short, cuts to the exact duration, encodes H.264 (CRF 18, yuv420p, `+faststart` for web playback) and AAC 48 kHz stereo, and normalises the sound to -14 LUFS with true peak at -1.5 dBTP. Options: `--size 1080x1920`, `--fps 60`, `--lufs -16`, `--crf 16`.

## Check it

```bash
scripts/check_delivery.sh final.mp4 --seconds 12            # PASS/WARN/FAIL per item
scripts/contact_sheet.sh final.mp4 --at 0.5,3,6,9.5,11.5    # stills at exact moments
ffprobe -v error -show_streams -show_format final.mp4       # everything, raw
```

## Recipes

**Join clips that share size, rate and codec (no re-encode):**
```bash
printf "file '%s'\n" a.mp4 b.mp4 c.mp4 > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy joined.mp4
```

**Join with a crossfade (re-encodes):**
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5,format=yuv420p[v]" \
  -map "[v]" -an ab.mp4      # offset = length of a.mp4 minus the fade
```

**Put a transparent overlay (MOV with alpha, or PNG) on top of a shot:**
```bash
ffmpeg -i shot.mp4 -i title.mov -filter_complex "[0:v][1:v]overlay=0:0:shortest=1" -c:a copy out.mp4
```

**Lay a soundtrack under a silent render** (or use `finish.sh --audio`):
```bash
ffmpeg -i render.mp4 -i music.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4
```

**A placeholder soundtrack when you have no music:** `scripts/sound_bed.sh bed.wav --seconds 12 --hits 9.0` makes a quiet original pad with a pulse and a low accent at each `--hits` time (put one on the hero moment). Replace it with real music when you have some.

**Measure loudness:**
```bash
ffmpeg -nostats -i final.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12
```

**Find black or frozen stretches:**
```bash
ffmpeg -i final.mp4 -vf blackdetect=d=0.5:pic_th=0.98 -an -f null - 2>&1 | grep black_start
ffmpeg -i final.mp4 -vf freezedetect=n=0.001:d=1.5 -an -f null - 2>&1 | grep freeze_start
```

**A GIF preview for a README or a pull request:**
```bash
ffmpeg -i final.mp4 -vf "fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" preview.gif
```

**Speed up heavy encodes on Apple Silicon** (for intermediates only; keep x264 for the final): `-c:v h264_videotoolbox -b:v 12M`.

## Platform targets

| Where | Frame | Rate | Loudness |
|---|---|---|---|
| YouTube, landscape | 1920x1080 or 3840x2160 | 24, 30 or 60 | about -14 LUFS |
| Shorts, Reels, TikTok | 1080x1920 | 30 or 60 | about -14 LUFS |
| Slides, websites | 1920x1080 | 30 | quieter is fine, or silent |
