---
name: short-form-ffmpeg-cookbook
description: >-
  Short-form FFmpeg cookbook: copyable commands for Reels. Turns raw footage into a 1080×1920 9:16 MP4 for Reels, TikTok and Shorts with
  burned-in captions (SRT or ASS), trims and joins clips, and lays music under the voice with ducking. Every command was run
  on test media. Free and local; works in Claude Code, Codex and Grok, or on the varg ffmpeg tool (credits) when the agent has
  no shell. Use when the user wants to crop to vertical, burn subtitles, cut or join clips, or add background music with
  FFmpeg. NOT for animated word-by-word captions (use Remotion or HyperFrames caption skills) or for choosing an editing
  service (use varg-video-editing).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - ffmpeg
    homepage: https://github.com/vargHQ/skills/tree/main/short-form-ffmpeg-cookbook
compatibility: >-
  Any OS with ffmpeg and ffprobe. Burning captions needs an FFmpeg built with libass (`ffmpeg -filters | grep subtitles`);
  if it prints nothing, use `brew install ffmpeg-full`, a static build or `npx ffmpeg-static`.
allowed-tools: Bash(ffmpeg:*) Bash(ffprobe:*) Read
---

# Short-form FFmpeg cookbook: copyable commands for Reels

Input: a video (any size), optionally an SRT file and a music track. Output: a 1080×1920 9:16 MP4 ready for Reels, TikTok and Shorts. Probe first, run one recipe at a time, check the result with ffprobe and a frame grab before the next step.

```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate -show_entries format=duration -of compact=p=0 input.mp4
```

## 1. Crop to 9:16 vertical

```bash
# center crop, full height
ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 20 -c:a copy vertical.mp4
# subject off-center: add the x offset in px
ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih:200:0,scale=1080:1920,setsar=1" -c:v libx264 -crf 20 -c:a copy vertical.mp4
# keep the whole frame over a blurred copy
ffmpeg -i input.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1" -c:v libx264 -crf 20 -c:a copy vertical-blur.mp4
```

## 2. Burn in captions

```bash
ffmpeg -i vertical.mp4 -vf "subtitles=subs.srt:force_style='FontName=Arial,FontSize=14,Bold=1,Outline=2,Alignment=2,MarginV=60'" -c:v libx264 -crf 20 -c:a copy captioned.mp4
# styled or karaoke captions: convert, edit the .ass, burn
ffmpeg -i subs.srt subs.ass
ffmpeg -i vertical.mp4 -vf "ass=subs.ass" -c:v libx264 -crf 20 -c:a copy captioned.mp4
# soft subtitles (switchable, no re-encode)
ffmpeg -i input.mp4 -i subs.srt -map 0 -map 1 -c copy -c:s mov_text -metadata:s:s:0 language=eng soft.mp4
```

Keep captions out of the bottom 14% and the right edge of a 9:16 frame, where the platform buttons sit. Check a frame: `ffmpeg -ss 2 -i captioned.mp4 -frames:v 1 frame.png`, then read it.

## 3. Trim and join

```bash
# frame-accurate trim (re-encodes)
ffmpeg -ss 00:00:05 -to 00:00:12 -i input.mp4 -c:v libx264 -crf 18 -c:a aac clip.mp4
# instant lossless trim (cuts on keyframes, may start a few seconds off)
ffmpeg -ss 00:00:05 -to 00:00:12 -i input.mp4 -c copy clip.mp4
# join clips with the same codec, size and frame rate
printf "file 'clip1.mp4'\nfile 'clip2.mp4'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy joined.mp4
# join clips that differ: scale and pad each to 1080x1920, then concat
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -c:a aac joined.mp4
```

Every clip in the concat filter needs an audio track; give a silent one `-f lavfi -i anullsrc=r=48000:cl=stereo -shortest`.

## 4. Music under the voice

```bash
# duck the music while people talk
ffmpeg -i input.mp4 -i music.mp3 -filter_complex "[0:a]asplit=2[voice][key];[1:a]volume=0.4[m];[m][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[ducked];[voice][ducked]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac output.mp4
# flat music bed
ffmpeg -i input.mp4 -i music.mp3 -filter_complex "[1:a]volume=0.25[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac output.mp4
# replace the sound, loop the track, fade out (20 s video)
ffmpeg -i input.mp4 -stream_loop -1 -i music.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest -af "afade=t=out:st=18:d=2" output.mp4
# loudness check (platforms normalize to about -14 LUFS)
ffmpeg -i output.mp4 -af ebur128 -f null -
```

Use music you made or licensed for the platform. `normalize=0` needs FFmpeg 4.4 or later.

## No shell

Send the same command to the varg `ffmpeg` tool (MCP `call_tool`, or `POST https://api.varg.ai/v2/ffmpeg`), or use its `resize`, `trim` and `slice` tools, with URLs in and out. Priced in credits, with an estimate before it runs. Tutorials: https://skills.varg.ai/burn-captions-with-ffmpeg/, https://skills.varg.ai/crop-a-video-to-vertical-with-ffmpeg/, https://skills.varg.ai/trim-and-join-video-clips-with-ffmpeg/, https://skills.varg.ai/add-music-to-a-video-with-ffmpeg/.
