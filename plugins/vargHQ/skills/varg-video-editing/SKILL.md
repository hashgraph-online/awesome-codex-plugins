---
name: varg-video-editing
description: >-
  Which service to edit an existing video with, and how to edit it without breaking it. A routing
  guide for ten editing jobs: cut, trim, resize and join (FFmpeg, the varg ffmpeg tool, Rendi),
  talking-head cleanup (silence and filler cuts from word timestamps: auto-editor, Descript,
  ElevenLabs Scribe, Groq Whisper), long video to Shorts (OpusClip, or transcript + Gemini +
  FFmpeg), captions and subtitles (ASS through FFmpeg, Remotion, HyperFrames, Submagic, ZapCap),
  assembling from a timeline or template (HyperFrames, Remotion, Shotstack, Creatomate), AI edits
  that restyle, swap people, relight or extend (varg Recast/Relight/ID-V2V, Runway Aleph, Luma Ray,
  Wan VACE), dubbing and lip sync (HeyGen, ElevenLabs Dubbing, Sync Labs), upscaling, slow motion
  and background removal (Topaz, SeedVR, Bria), finding moments and QA (Gemini, varg
  video-analyze, Twelve Labs, VideoDB), and handing the cut to DaVinci Resolve, Premiere or Final
  Cut. Use when someone asks to edit, cut, trim, shorten, clip, reframe, caption, subtitle,
  translate, dub, lip-sync, upscale, restyle or clean up footage they already have, or asks which
  tool or API to edit video with. Not for making a video from a brief (varg-ai and the format
  skills).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - ffmpeg
        - curl
    homepage: https://skills.varg.ai/browse/skills/edit-services/
compatibility: >-
  The guide itself needs nothing. Local edits need ffmpeg and ffprobe. Paid edits run on the varg
  MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY, or on the service's own key.
allowed-tools: Bash(ffmpeg:*) Bash(ffprobe:*) Bash(curl:*) Read
---

# Video editing: which service, and how

Editing starts from footage that already exists, so the first rule is not to damage it. Work in this order, and pick the service for each step from the table below.

1. **Probe.** Run `ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate -of json in.mp4`. Note the frame rate, whether it is variable, the sample rate and the duration.
2. **Transcribe once** if anyone speaks: word-level timestamps, saved as JSON next to the source. Every text decision reads from this file: silences, filler words, highlights, captions.
3. **Write the edit decision list** as data: source, in and out points, track, effect, the service for each step and its cost. Show it to the person and wait for a yes before any paid call. On varg, run `estimate_cost` first.
4. **Render deterministically** wherever you can (FFmpeg, HyperFrames, Remotion). Use a generative model only on the shortest span whose pixels must change. Cut that span out, edit it, and stitch it back.
5. **Verify.** ffprobe the output, grab stills at every cut point (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 cut-<t>.jpg`) and look at them. Compare the duration with the edit list.

## Which service for which edit

The first service in each row is the default pick. Switch only for the reason given. The full table, with access, pricing and links, is in [references/services.md](references/services.md).

| Job | Pick | Switch to |
|---|---|---|
| Cut, trim, resize, join | **FFmpeg** on the agent's machine | **varg `ffmpeg` / `trim` / `slice` / `resize`** when there is no shell or the clips already live on varg. **Rendi** for hosted FFmpeg on its own key |
| Talking-head cleanup | **Word timestamps + FFmpeg** (varg `transcription`, ElevenLabs Scribe or Groq Whisper) | **auto-editor** for a quick local silence pass. **Descript** when a person will review the edit in an app |
| Long video to Shorts | **OpusClip** for finished, scored and captioned clips | **Transcript + Gemini + FFmpeg** with a tracking crop when you need control. **Vizard** for cheap bulk clipping |
| Captions & subtitles | **ASS from your word timestamps, burned in with FFmpeg** | **Remotion / HyperFrames** for animated styles. **Submagic / ZapCap** for their templates |
| Assemble from a timeline | **HyperFrames or Remotion** when the agent writes the video | **Shotstack / Creatomate** for hundreds of template variants rendered in the cloud |
| AI edits: restyle, swap, relight | **varg**: `minimax_h3_max_recast` (swap people), `minimax_h3_max_relight`, `id_v2v` (restyle, keep identity), `minimax_h3_max_extend` / `_insert`, prompt edits on `kling_v4` and `omni_flash_1_1` | **Runway Aleph** for prompt and keyframe edits. **Luma Ray** for motion-preserving restyle and reframe. **Wan VACE** for masked inpainting |
| Dubbing & lip sync | **HeyGen Video Translate** (translation, voice and lips in one call) | **ElevenLabs Dubbing** for the best voice, then **Sync Labs** (varg `sync_v3`, `sync_v2_pro`) for the lips |
| Upscale, slow-mo, cut-outs | **Topaz** (varg `topaz_video`) on the final export | **SeedVR / ByteDance / Sima** upscalers for price. **Bria** for background removal |
| Find moments & QA | **Gemini** video understanding (timecodes, QA questions) | **varg `video-analyze`** for a quick JSON report. **Twelve Labs / VideoDB** to search a library |
| Hand off to an editing app | **A timeline file**: OTIO, FCPXML or Premiere XML | **DaVinci Resolve Studio MCP** to drive the app live (the only official one). Premiere has only community bridges, and CapCut has no API |

## Rules that save a re-render

- **Frame-accurate cuts need a re-encode.** `-c copy` snaps to the nearest keyframe and can leave black frames or audio drift. Re-encode the cut (`-c:v libx264 -crf 18 -c:a aac`), or use varg `trim` with `precise: true`.
- **One frame rate before joining.** Convert mixed sources first (`-vf fps=30 -r 30`, `-ar 48000`). Then use the concat filter, not the concat demuxer, unless every input has identical codecs and settings.
- **Cut audio with the video.** Use the same timestamps for both. Pad each spoken cut by 50–150 ms and add a ~30 ms `afade` at each joint so the cuts do not click. Check that the output duration matches the edit list.
- **Never overwrite the source.** Write to new files, and use low-resolution proxies for analysis and previews. Apply the final cut to the full-resolution source, and upscale only the final export.
- **Generative windows are short.** Most video-to-video models take 5–30 s per pass. Split at a calm moment, edit each piece, and cross-fade the seams. Check faces and identity on frame grabs before you deliver.
- **Hosted APIs are jobs.** Store the job id, poll or take a webhook, back off on 429, and download the result straight away (some links expire within hours). Pass public URLs between steps. On varg, upload once with `/v2/files`.
- **Reframe with tracking.** For 9:16, follow the face or subject rather than cropping the center. Keep captions inside the safe zones: the top ~12% and bottom ~20% are covered by platform UI.
- **Spend only after a yes.** Show the edit list and the estimate first. Cache transcripts and generations. Never re-run a paid model just to move a cut.

## On varg

One key covers the deterministic and the generative steps: `ffmpeg`, `trim`, `slice`, `resize` and `render` for the cut, `transcription` for word timestamps, `video-analyze` for QA, and the video edit, lip-sync and upscale models above. Each model's inputs are in its spec at `https://varg.ai/models/<model>.md`. Prices are in credits from `estimate_cost`; never quote them in money. For generating new footage, use the varg-ai skill.

The full table, with access, pricing, gotchas and links: [references/services.md](references/services.md). Online: https://skills.varg.ai/browse/skills/edit-services.md

How the best editing agents cut footage (transcript first, edit decision list, word-boundary padding, 30 ms audio fades, proxies, self-checks with a retry cap, timeline hand-off): [references/practices.md](references/practices.md), 21 practices with sources. For the named edits themselves (cuts, transitions, titles, UI, cursors, devices, numbers), use the varg-video-edit-library skill.
