# Finish accepted footage without another generation

Use the project's available FFmpeg or compositor. These are adjustable command patterns, not a claim of platform acceptance or a new Magic Hour tool. Keep the clean master and write derivatives to new files. Do not install a renderer just to apply one effect.

## Inspect and choose the edit

```bash
ffprobe -v error -show_entries format=duration:stream=index,codec_type,codec_name,width,height,sample_aspect_ratio,r_frame_rate,sample_rate,channel_layout -of json master.mp4
```

Choose intervals from actual playback and speech boundaries. Inspect rotation and sample aspect ratio before using the square-pixel examples below. The example canvas is 1080×1920 at 30 fps; replace it with the real deliverable's dimensions and frame rate. Do not assume every placement is vertical.

- **Crop** only when the subject, gestures, product and required context stay visible throughout the whole interval. A center crop is not tracking.
- **Contain** when retaining the full picture is acceptable. Scale proportionally, pad the remaining canvas, and keep exact copy in a separate layer. A contained version does not fulfill a requested full-bleed version without agreement.

```bash
# Decode and re-encode a chosen five-second interval; retain audio when present.
ffmpeg -ss 2 -i master.mp4 -t 5 -map 0:v:0 -map '0:a:0?' -c:v libx264 -pix_fmt yuv420p -c:a aac -movflags +faststart trimmed.mp4
# Contain a square-pixel source; inspect the actual output for crop and copy space.
ffmpeg -i trimmed.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1" -map 0:v:0 -map '0:a:0?' -c:v libx264 -pix_fmt yuv420p -c:a aac -movflags +faststart contained.mp4
```

Stream-copy trims can begin at a nearby keyframe; use decoding when a word or action needs an exact cut. Never choose a duration merely to make a command run.

## Join clips with deliberate audio

Check both inputs first. Concatenation needs compatible picture properties and a consistent audio plan. This example assumes **both clips have audio** and square pixels. It normalizes the canvas, frame rate, timebase, pixel format, sample rate and channel layout rather than stretching the picture.

```bash
ffmpeg -i opener.mp4 -i body.mp4 -filter_complex "[0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,settb=AVTB,format=yuv420p,setpts=PTS-STARTPTS[v0];[1:v]fps=30,scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,settb=AVTB,format=yuv420p,setpts=PTS-STARTPTS[v1];[0:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a0];[1:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map '[v]' -map '[a]' -c:v libx264 -pix_fmt yuv420p -c:a aac -movflags +faststart joined.mp4
```

If an input has no audio, do not reference its absent audio stream. For an intentionally silent export, use video-only concatenation (`concat=n=2:v=1:a=0`) with the normalized video streams. If speech must survive, supply silence for only the silent interval using its measured duration, then join it with the other audio. Do not discard the speaking clip's audio to make the streams match.

Review the seam for clipped consonants, unwanted silence, abrupt ambience and mismatched crop. Concat can pad a shorter audio segment with silence; inspect that duration instead of assuming the join is seamless. An audio fade can soften a click but cannot repair a cut inside a word. Avoid `-shortest` when it would remove the last word or action.

## Put licensed music under speech

Use only the requested, authorized music. The source below must have speech audio. The music loops while the speech remains the first, duration-controlling mix input; no picture trim is implied.

```bash
ffmpeg -i master.mp4 -stream_loop -1 -i licensed-music.wav -filter_complex "[0:a]asplit=2[voice][key];[1:a]volume=0.2[music];[music][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[ducked];[voice][ducked]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v:0 -map '[a]' -c:v copy -c:a aac -movflags +faststart mixed.mp4
```

Treat those levels as a starting point. Listen for intelligibility, pumping, clipping and the ending. A shorter speech track may leave a deliberate picture tail; decide its soundtrack rather than trimming automatically. For a silent source, choose an explicit soundtrack instead of using the speech-ducking recipe.

## Caption the final cut

Use actual speech timestamps or an authorized transcript aligned to the final audio. Do not estimate word timings from text length. Correct proper names, numbers and the last word before styling. Choose one readable treatment:

| Treatment | Use | Keep readable |
| --- | --- | --- |
| Outlined phrase | General speech and product demos | Short phrases, one or two lines, clear outline; avoid covering the product or mouth |
| Dark phrase plate | Busy or bright footage | Light text on a quiet dark plate, stable position and enough reading time |
| Active-word emphasis | A short hook when word timings exist | Keep the phrase visible; highlight the current word without moving every word; also retain a plain phrase version |

Set font, size, placement and line breaks against the actual canvas and current destination template. There is no universal safe box. Use a font licensed for the export. Never add a new caption engine merely to obtain an animation style.

With an available libass-enabled FFmpeg, an approved ASS file can carry the chosen style and canvas coordinates:

```bash
ffmpeg -i joined.mp4 -vf ass=approved-captions.ass -map 0:v:0 -map '0:a:0?' -c:v libx264 -pix_fmt yuv420p -c:a aac -movflags +faststart captioned.mp4
```

Keep supplied copy in subtitle/text files rather than interpolating it into shell commands or filter strings. Deliver a plain SRT/VTT alongside the styled render when the source timings and available tooling support it. Magic Hour's subtitle endpoint may return only burned-in video; do not claim it produced an editable subtitle file.

Reopen the exported file, inspect the entire motion path and all joins, and listen through the ending. Verify actual dimensions, frame rate, duration, streams, readable text and unclipped speech. Save the clean master, final render and editable subtitle/layout sources separately. These recipes require validation on the actual files; a successful encode is not visual or listening acceptance.

Adapted from Varg's MIT-licensed [FFmpeg cookbook](https://github.com/vargHQ/skills/blob/04cd89af3dfa6ba1c0a8dc6470107d02579b198b/short-form-ffmpeg-cookbook/SKILL.md) and [caption styles](https://github.com/vargHQ/skills/blob/04cd89af3dfa6ba1c0a8dc6470107d02579b198b/caption-styles/SKILL.md). Copyright (c) 2026 vargai Inc.; see this skill's [MIT license](../LICENSE). Varg's executions are not Magic Hour validation evidence.
