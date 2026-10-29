---
name: ecommerce-video-edit
description: >-
  Turn raw product footage into a TikTok ad with FFmpeg. Recuts creator, UGC or product footage into
  a 9:16 ecommerce ad for TikTok, TikTok Shop, Reels and Meta: the best moment moved to second 0, a
  text hook inside the safe zone, dead air cut, captions, a CTA end card, loudness at -14 LUFS, and
  one MP4 per hook for testing (plus a 4:5 feed cut and a cover frame). Every command was run on test
  media. Free and local; on the varg ffmpeg tool (credits) when the agent has no shell. Use when
  someone has footage of a product (a creator video, an unboxing, a demo, a winning ad) and wants it
  edited into an ad, wants new hooks on an existing ad, or wants it TikTok-ready. NOT for generating
  new footage (use product-photo-to-video or ai-ugc-ad-video), animated word-by-word captions (use a
  Remotion or HyperFrames caption skill), or generic crops and subtitles (use
  short-form-ffmpeg-cookbook).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - ffmpeg
    homepage: https://github.com/vargHQ/skills/tree/main/ecommerce-video-edit
compatibility: >-
  Any OS with ffmpeg and ffprobe. Text hooks and burned captions need an FFmpeg built with
  libfreetype and libass (`ffmpeg -filters | grep -E "drawtext|subtitles"`). If that prints
  nothing, use `npx ffmpeg-static`, a static build or `brew install ffmpeg-full`.
allowed-tools: Bash(ffmpeg:*) Bash(ffprobe:*) Bash(bash:*) Read Write
---

# Turn raw product footage into a TikTok ad with FFmpeg

Input: footage of a product (a creator clip, an unboxing, a demo, last month's winning ad). Output: a 1080×1920 MP4 that opens on the product and the payoff, says the hook in text inside the safe zone, has no dead air, ends on one CTA, and plays at the loudness the apps expect. You also get one file per hook for testing, a 4:5 feed cut and a cover frame.

All commands were run on test media (FFmpeg 6.0 static and 8.1). Run one step at a time and look at a frame before going on.

## 0. Ask before cutting

1. **What is the one thing the viewer must see?** The product doing its job, or the result. It goes in the first 1–2 seconds.
2. **Where does it run?** TikTok Shop and organic content: 15–45 s. Paid TikTok and Meta: 15–30 s for cold traffic, up to 60 s for a story that holds. One video, many hooks, beats one video per idea.
3. **What claims are allowed?** Only what the brand can prove. Edit out "cures", "guaranteed", fake prices and before/after shots on health or weight products.
4. **Sound:** the creator's voice, licensed music (TikTok Commercial Music Library for ads), or both with ducking. Trending sounds from organic posts are not cleared for ads.

## 1. Probe

```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate -show_entries format=duration -of compact=p=0 input.mp4
```

Horizontal footage? Fit it to 9:16 over a blurred copy, so the whole product stays in the frame:

```bash
ffmpeg -i raw.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1" -c:v libx264 -crf 20 -c:a copy vertical.mp4
```

For a centre crop instead, see `short-form-ffmpeg-cookbook`.

## 2. Find the hook moment and move it to second 0

Watch for the strongest 2–4 s: the product working, the reveal, the reaction, the before→after. If there is a transcript, the hook is often a line said 10–20 s in ("I stopped buying razors after this"). Move it to the front and keep the rest in order (here 12–15 s moves to the front):

```bash
ffmpeg -i input.mp4 -filter_complex "[0:v]trim=12:15,setpts=PTS-STARTPTS[v0];[0:a]atrim=12:15,asetpts=PTS-STARTPTS[a0];[0:v]trim=0:12,setpts=PTS-STARTPTS[v1];[0:a]atrim=0:12,asetpts=PTS-STARTPTS[a1];[0:v]trim=start=15,setpts=PTS-STARTPTS[v2];[0:a]atrim=start=15,asetpts=PTS-STARTPTS[a2];[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -c:a aac -b:a 192k recut.mp4
```

Then cut what came before the product shows up: "Hey guys", logos, slow intros. Nobody waits for them.

## 3. Cut dead air

`scripts/cut-dead-air.sh` finds pauses with `silencedetect`, keeps 0.12 s of air on each side, and joins the rest:

```bash
bash scripts/cut-dead-air.sh recut.mp4 tight.mp4 -35 0.5 0.12   # noise floor dB, min pause s, padding s
# Tested: "kept 4 segments: 16.28s of 20.00s"
```

Raise the noise floor (-30) for noisy rooms and lower it (-40) for quiet voices. Listen to the cuts: a breath cut mid-word means the padding is too small.

Pacing that still drags? Speed the body up a little (1.1–1.2× keeps the voice natural):

```bash
ffmpeg -i tight.mp4 -filter_complex "[0:v]setpts=PTS/1.15[v];[0:a]atempo=1.15[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 20 -c:a aac fast.mp4
```

## 4. Text hook in the first 3 seconds

Most people watch muted at first. Put the hook in words on screen, inside the safe zone: out of the top 14%, the bottom 35% and 6% at each side (the TikTok and Reels buttons, caption and username sit there). Keep it to two lines of at most about 24 characters each at 64 px:

```bash
printf 'I stopped buying razors\nafter I found this' > hook.txt
ffmpeg -i tight.mp4 -vf "drawtext=fontfile='/System/Library/Fonts/Supplemental/Arial Bold.ttf':textfile=hook.txt:fontcolor=white:fontsize=64:line_spacing=12:box=1:boxcolor=black@0.6:boxborderw=28:x=(w-text_w)/2:y=h*0.20:enable='between(t,0,3)'" -c:v libx264 -crf 20 -c:a copy texthook.mp4
```

Always pass `fontfile` (on Linux, e.g. `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`). Without it, static builds print a fontconfig error. Multi-line drawtext aligns lines to the left. For centred or animated type, render the hook as a PNG or in HyperFrames/Remotion and overlay it.

Captions for the rest of the video: burn an SRT or ASS file (see `short-form-ffmpeg-cookbook` §2) and keep them in the same safe band.

## 5. One CTA at the end

One action, said and shown: "Tap the orange cart" (TikTok Shop), "Shop now", or "Link in bio" (organic). Show it over the last 3 seconds:

```bash
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 texthook.mp4)
ffmpeg -i texthook.mp4 -vf "drawtext=fontfile='/System/Library/Fonts/Supplemental/Arial Bold.ttf':text='Tap the orange cart':fontcolor=black:fontsize=72:box=1:boxcolor=white@0.92:boxborderw=30:x=(w-text_w)/2:y=h*0.45:enable='gte(t,$D-3)'" -c:v libx264 -crf 20 -c:a copy cta.mp4
```

Don't add a price, a discount or "only today" unless the offer is real and live.

## 6. Many hooks, one body (the test set)

A hook is the first 2–3 s. Make 3–10 openers (new footage, a new line, a new text hook, a different first frame) and put each in front of the same body. `scripts/hook-variants.sh` scales every input to 1080×1920 at 30 fps and 48 kHz stereo, so clips from different sources join cleanly:

```bash
# hooks/h01-question.mp4, hooks/h02-pov.mp4, ...   body.mp4 = the ad without its old hook
bash scripts/hook-variants.sh body.mp4 hooks variants 2   # last arg: seconds to drop from the body's start (its old hook)
# → variants/h01-question__body.mp4, variants/h02-pov__body.mp4
```

Name files so the results can be read back later: `<product>_<angle>_<hook-id>_<creator>_<length>_v<N>.mp4`, e.g. `serum_dryskin_h03-pov_maya_22s_v1.mp4`. Change one thing per variant (the hook) so the test says which one won.

## 7. Loudness, export, check

Two-pass loudnorm to -14 LUFS integrated and -1 dBTP:

```bash
J=$(ffmpeg -hide_banner -i cta.mp4 -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
v() { echo "$J" | grep "\"$1\"" | cut -d'"' -f4; }
ffmpeg -i cta.mp4 -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=$(v input_i):measured_TP=$(v input_tp):measured_LRA=$(v input_lra):measured_thresh=$(v input_thresh):offset=$(v target_offset):linear=true,aresample=48000" -c:v copy -c:a aac -b:a 192k loud.mp4
ffmpeg -hide_banner -i loud.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1   # Tested: I: -14.0 and -13.9 LUFS on two inputs
```

Export (H.264 High, yuv420p, 30 fps, AAC 48 kHz, faststart), a 4:5 feed cut and a cover:

```bash
ffmpeg -i loud.mp4 -c:v libx264 -profile:v high -pix_fmt yuv420p -r 30 -b:v 8M -maxrate 10M -bufsize 16M -c:a aac -b:a 192k -ar 48000 -movflags +faststart final_9x16.mp4
ffmpeg -i final_9x16.mp4 -vf "crop=iw:iw*5/4:0:(ih-iw*5/4)*0.4,scale=1080:1350,setsar=1" -c:v libx264 -crf 20 -c:a copy final_4x5.mp4
ffmpeg -ss 0.5 -i final_9x16.mp4 -frames:v 1 -q:v 2 cover.jpg
```

Check the safe zone on a frame before delivering: the red bands must hold no text, no product and no face.

```bash
ffmpeg -ss 1 -i final_9x16.mp4 -frames:v 1 -vf "drawbox=x=0:y=0:w=iw:h=ih*0.14:color=red@0.35:t=fill,drawbox=x=0:y=ih*0.65:w=iw:h=ih*0.35:color=red@0.35:t=fill,drawbox=x=0:y=0:w=iw*0.06:h=ih:color=red@0.35:t=fill,drawbox=x=iw*0.94:y=0:w=iw*0.06:h=ih:color=red@0.35:t=fill" safezone.png
```

## Edit checklist

- [ ] The product or the result shows by second 2; no logo or greeting opens the video
- [ ] The text hook is readable muted, two short lines, inside the safe zone
- [ ] No pause longer than half a second; the pacing drops off nowhere
- [ ] The claims are provable; no fake urgency; AI people or voices are labelled where the platform requires it
- [ ] One CTA, said and shown
- [ ] Integrated loudness -14 LUFS, peaks at -1 dBTP or lower
- [ ] 1080×1920, 30 fps, H.264 yuv420p, faststart; a 4:5 cut for feed placements
- [ ] Every hook variant in its own named file, the body unchanged

## No shell? Run it on varg

Send the same command to the varg `ffmpeg` tool (MCP `call_tool`, or `POST https://api.varg.ai/v2/ffmpeg`). Inputs and outputs are URLs. It is priced in credits, with an estimate before anything runs.

## Related skills

- `ecommerce-video-ads`: the whole process, from angle to hooks, formats and testing
- `product-video-hooks`: what to say and show in the first 3 seconds
- `ad-creative-testing`: how many variants to make, what to change, when to kill an ad
- `short-form-ffmpeg-cookbook`: crop, captions, trim and join, music ducking
- `varg-video-edit-library`: 206 named edits (cuts, transitions, titles, end cards) for FFmpeg, HyperFrames, Remotion and CapCut
